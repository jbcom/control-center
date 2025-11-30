import { Octokit } from "@octokit/rest";
import type { CICheck, CIStatus, FeedbackItem, FeedbackSeverity, FeedbackStatus } from "./types.js";

export interface GitHubConfig {
  token: string;
  owner: string;
  repo: string;
}

export class GitHubClient {
  private octokit: Octokit;
  private owner: string;
  private repo: string;

  constructor(config: GitHubConfig) {
    this.octokit = new Octokit({ auth: config.token });
    this.owner = config.owner;
    this.repo = config.repo;
  }

  // ==========================================================================
  // PR Information
  // ==========================================================================

  async getPR(prNumber: number) {
    const { data } = await this.octokit.pulls.get({
      owner: this.owner,
      repo: this.repo,
      pull_number: prNumber,
    });
    return data;
  }

  async getPRFiles(prNumber: number) {
    const { data } = await this.octokit.pulls.listFiles({
      owner: this.owner,
      repo: this.repo,
      pull_number: prNumber,
    });
    return data;
  }

  // ==========================================================================
  // Reviews and Comments
  // ==========================================================================

  async getReviews(prNumber: number) {
    const { data } = await this.octokit.pulls.listReviews({
      owner: this.owner,
      repo: this.repo,
      pull_number: prNumber,
    });
    return data;
  }

  async getReviewComments(prNumber: number) {
    const { data } = await this.octokit.pulls.listReviewComments({
      owner: this.owner,
      repo: this.repo,
      pull_number: prNumber,
    });
    return data;
  }

  async getIssueComments(prNumber: number) {
    const { data } = await this.octokit.issues.listComments({
      owner: this.owner,
      repo: this.repo,
      issue_number: prNumber,
    });
    return data;
  }

  // ==========================================================================
  // CI Status
  // ==========================================================================

  async getCIStatus(prNumber: number): Promise<CIStatus> {
    const pr = await this.getPR(prNumber);
    const ref = pr.head.sha;

    const { data: checkRuns } = await this.octokit.checks.listForRef({
      owner: this.owner,
      repo: this.repo,
      ref,
    });

    const checks: CICheck[] = checkRuns.check_runs.map((run) => ({
      name: run.name,
      status: this.mapCheckStatus(run.status, run.conclusion),
      conclusion: run.conclusion,
      url: run.html_url ?? "",
      startedAt: run.started_at,
      completedAt: run.completed_at,
    }));

    const failures = checks.filter((c) => c.status === "failure");
    const pending = checks.filter((c) => c.status === "pending" || c.status === "in_progress");

    return {
      allPassing: failures.length === 0 && pending.length === 0,
      anyPending: pending.length > 0,
      checks,
      failures,
    };
  }

  private mapCheckStatus(
    status: string,
    conclusion: string | null
  ): CICheck["status"] {
    if (status === "queued" || status === "pending") return "pending";
    if (status === "in_progress") return "in_progress";
    if (conclusion === "success") return "success";
    if (conclusion === "failure" || conclusion === "timed_out") return "failure";
    if (conclusion === "skipped" || conclusion === "cancelled") return "skipped";
    return "pending";
  }

  // ==========================================================================
  // Feedback Collection
  // ==========================================================================

  async collectFeedback(prNumber: number): Promise<FeedbackItem[]> {
    const [reviewComments, reviews] = await Promise.all([
      this.getReviewComments(prNumber),
      this.getReviews(prNumber),
    ]);

    const feedbackItems: FeedbackItem[] = [];

    // Process inline review comments
    for (const comment of reviewComments) {
      const severity = this.inferSeverity(comment.body);
      feedbackItems.push({
        id: `comment-${comment.id}`,
        author: comment.user?.login ?? "unknown",
        body: comment.body,
        path: comment.path,
        line: comment.line ?? comment.original_line ?? null,
        severity,
        status: this.inferStatus(comment),
        createdAt: comment.created_at,
        url: comment.html_url,
        isAutoResolvable: this.isAutoResolvable(comment.body, severity),
        suggestedAction: this.extractSuggestion(comment.body),
        resolution: null,
      });
    }

    // Process review bodies (summary comments)
    for (const review of reviews) {
      if (!review.body || review.body.trim() === "") continue;
      
      const severity = this.inferSeverity(review.body);
      feedbackItems.push({
        id: `review-${review.id}`,
        author: review.user?.login ?? "unknown",
        body: review.body,
        path: null,
        line: null,
        severity,
        status: "addressed", // Review summaries are informational
        createdAt: review.submitted_at ?? new Date().toISOString(),
        url: review.html_url,
        isAutoResolvable: false,
        suggestedAction: null,
        resolution: null,
      });
    }

    return feedbackItems;
  }

  private inferSeverity(body: string): FeedbackSeverity {
    const lower = body.toLowerCase();
    
    // Check for explicit severity indicators
    if (body.includes("🛑") || body.includes(":stop_sign:") || lower.includes("critical")) {
      return "critical";
    }
    if (body.includes("medium-priority") || lower.includes("high severity")) {
      return "high";
    }
    if (body.includes("medium") || lower.includes("should")) {
      return "medium";
    }
    if (body.includes("nitpick") || body.includes("nit:") || lower.includes("consider")) {
      return "low";
    }
    if (body.includes("info") || body.includes("note:")) {
      return "info";
    }
    
    // Default based on content
    if (lower.includes("error") || lower.includes("bug") || lower.includes("fix")) {
      return "high";
    }
    
    return "medium";
  }

  private inferStatus(comment: { body: string; in_reply_to_id?: number }): FeedbackStatus {
    // If it's a reply, it might be addressing previous feedback
    if (comment.in_reply_to_id) {
      return "addressed";
    }
    return "unaddressed";
  }

  private isAutoResolvable(body: string, severity: FeedbackSeverity): boolean {
    // Can auto-resolve if there's a suggestion block
    if (body.includes("```suggestion")) return true;
    
    // Low severity items with clear fixes
    if (severity === "low" || severity === "info") return true;
    
    // Simple formatting/style issues
    const lower = body.toLowerCase();
    if (lower.includes("formatting") || lower.includes("typo") || lower.includes("spelling")) {
      return true;
    }
    
    return false;
  }

  private extractSuggestion(body: string): string | null {
    const suggestionMatch = body.match(/```suggestion\n([\s\S]*?)```/);
    if (suggestionMatch) {
      return suggestionMatch[1].trim();
    }
    return null;
  }

  // ==========================================================================
  // Actions
  // ==========================================================================

  async postComment(prNumber: number, body: string) {
    const { data } = await this.octokit.issues.createComment({
      owner: this.owner,
      repo: this.repo,
      issue_number: prNumber,
      body,
    });
    return data;
  }

  async replyToComment(prNumber: number, commentId: number, body: string) {
    const { data } = await this.octokit.pulls.createReplyForReviewComment({
      owner: this.owner,
      repo: this.repo,
      pull_number: prNumber,
      comment_id: commentId,
      body,
    });
    return data;
  }

  async requestReview(prNumber: number, reviewCommands: string[]) {
    // Post review request commands as comments
    for (const command of reviewCommands) {
      await this.postComment(prNumber, command);
    }
  }

  async mergePR(prNumber: number, method: "merge" | "squash" | "rebase" = "squash") {
    const { data } = await this.octokit.pulls.merge({
      owner: this.owner,
      repo: this.repo,
      pull_number: prNumber,
      merge_method: method,
    });
    return data;
  }
}
