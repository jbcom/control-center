import { generateObject, generateText } from "ai";
import { anthropic } from "@ai-sdk/anthropic";
import { z } from "zod";
import type { FeedbackItem, Blocker, TriageResult, PRStatus } from "./types.js";
import type { GitHubClient } from "./github.js";

export class Analyzer {
  private model = anthropic("claude-sonnet-4-20250514");

  async analyzePR(
    github: GitHubClient,
    prNumber: number
  ): Promise<TriageResult> {
    // Gather all data
    const [pr, ci, feedback] = await Promise.all([
      github.getPR(prNumber),
      github.getCIStatus(prNumber),
      github.collectFeedback(prNumber),
    ]);

    // Analyze feedback for unaddressed items
    const analyzedFeedback = await this.analyzeFeedback(feedback);
    const unaddressedFeedback = analyzedFeedback.filter(
      (f) => f.status === "unaddressed"
    );

    // Identify blockers
    const blockers = await this.identifyBlockers(pr, ci, unaddressedFeedback);

    // Determine status
    const status = this.determineStatus(pr, ci, blockers, unaddressedFeedback);

    // Generate next actions
    const nextActions = await this.generateNextActions(
      status,
      blockers,
      unaddressedFeedback
    );

    // Generate summary
    const summary = await this.generateSummary(
      pr,
      ci,
      blockers,
      unaddressedFeedback
    );

    return {
      prNumber,
      prUrl: pr.html_url,
      prTitle: pr.title,
      status,
      ci,
      feedback: {
        total: feedback.length,
        unaddressed: unaddressedFeedback.length,
        items: analyzedFeedback,
      },
      blockers,
      nextActions,
      summary,
      timestamp: new Date().toISOString(),
    };
  }

  private async analyzeFeedback(
    feedback: FeedbackItem[]
  ): Promise<FeedbackItem[]> {
    if (feedback.length === 0) return [];

    // Use AI to analyze which feedback items are truly unaddressed
    const { object } = await generateObject({
      model: this.model,
      schema: z.object({
        items: z.array(
          z.object({
            id: z.string(),
            status: z.enum(["unaddressed", "addressed", "dismissed", "wont_fix"]),
            isAutoResolvable: z.boolean(),
            suggestedAction: z.string().nullable(),
          })
        ),
      }),
      prompt: `Analyze these PR feedback items and determine their status.

Feedback items:
${feedback.map((f) => `
ID: ${f.id}
Author: ${f.author}
Severity: ${f.severity}
Path: ${f.path ?? "general"}
Body: ${f.body}
---`).join("\n")}

For each item:
1. Determine if it's addressed (has been fixed/responded to), unaddressed (needs action), dismissed (explicitly dismissed with reason), or wont_fix
2. Determine if it can be auto-resolved (has suggestion block, is simple fix, etc.)
3. Suggest the action needed if unaddressed

Return analysis for each item by ID.`,
    });

    // Merge AI analysis back into feedback items
    return feedback.map((item) => {
      const analysis = object.items.find((a) => a.id === item.id);
      if (analysis) {
        return {
          ...item,
          status: analysis.status,
          isAutoResolvable: analysis.isAutoResolvable,
          suggestedAction: analysis.suggestedAction,
        };
      }
      return item;
    });
  }

  private async identifyBlockers(
    pr: Awaited<ReturnType<GitHubClient["getPR"]>>,
    ci: Awaited<ReturnType<GitHubClient["getCIStatus"]>>,
    unaddressedFeedback: FeedbackItem[]
  ): Promise<Blocker[]> {
    const blockers: Blocker[] = [];

    // CI failures
    for (const failure of ci.failures) {
      blockers.push({
        type: "ci_failure",
        description: `CI check "${failure.name}" failed`,
        isAutoResolvable: true, // We'll try to fix CI failures
        suggestedFix: `Analyze failure logs at ${failure.url} and fix the issue`,
        url: failure.url,
        resolved: false,
      });
    }

    // Unaddressed critical/high feedback
    const criticalFeedback = unaddressedFeedback.filter(
      (f) => f.severity === "critical" || f.severity === "high"
    );
    if (criticalFeedback.length > 0) {
      blockers.push({
        type: "review_feedback",
        description: `${criticalFeedback.length} critical/high severity feedback items unaddressed`,
        isAutoResolvable: criticalFeedback.some((f) => f.isAutoResolvable),
        suggestedFix: "Address each feedback item with a fix or justified response",
        url: null,
        resolved: false,
      });
    }

    // Merge conflicts
    if (pr.mergeable === false && pr.mergeable_state === "dirty") {
      blockers.push({
        type: "merge_conflict",
        description: "PR has merge conflicts that must be resolved",
        isAutoResolvable: false, // Conflicts usually need human judgment
        suggestedFix: "Rebase or merge main branch and resolve conflicts",
        url: null,
        resolved: false,
      });
    }

    // Missing approvals
    if (pr.mergeable_state === "blocked") {
      blockers.push({
        type: "branch_protection",
        description: "Branch protection rules prevent merge",
        isAutoResolvable: false,
        suggestedFix: "Ensure all required checks pass and approvals are obtained",
        url: null,
        resolved: false,
      });
    }

    return blockers;
  }

  private determineStatus(
    pr: Awaited<ReturnType<GitHubClient["getPR"]>>,
    ci: Awaited<ReturnType<GitHubClient["getCIStatus"]>>,
    blockers: Blocker[],
    unaddressedFeedback: FeedbackItem[]
  ): PRStatus {
    if (pr.merged) return "merged";
    if (pr.state === "closed") return "closed";

    // Check for non-auto-resolvable blockers
    const hardBlockers = blockers.filter((b) => !b.isAutoResolvable);
    if (hardBlockers.length > 0) return "blocked";

    // CI pending
    if (ci.anyPending) return "needs_ci";

    // CI failures or unaddressed feedback
    if (ci.failures.length > 0 || unaddressedFeedback.length > 0) {
      return "needs_work";
    }

    // All good
    if (ci.allPassing && unaddressedFeedback.length === 0) {
      return "ready_to_merge";
    }

    return "needs_review";
  }

  private async generateNextActions(
    status: PRStatus,
    blockers: Blocker[],
    unaddressedFeedback: FeedbackItem[]
  ) {
    const actions: TriageResult["nextActions"] = [];

    // Based on status, generate prioritized actions
    if (status === "needs_work") {
      // Handle CI failures first
      const ciBlockers = blockers.filter((b) => b.type === "ci_failure");
      for (const blocker of ciBlockers) {
        actions.push({
          action: `Fix CI failure: ${blocker.description}`,
          priority: "critical",
          automated: true,
          reason: "CI must pass before merge",
        });
      }

      // Then handle feedback
      for (const feedback of unaddressedFeedback) {
        actions.push({
          action: feedback.isAutoResolvable
            ? `Auto-fix: ${feedback.suggestedAction ?? feedback.body.slice(0, 100)}`
            : `Address feedback from ${feedback.author}: ${feedback.body.slice(0, 100)}`,
          priority: feedback.severity,
          automated: feedback.isAutoResolvable,
          reason: `${feedback.severity} severity feedback requires resolution`,
        });
      }
    }

    if (status === "needs_review") {
      actions.push({
        action: "Request AI reviews: /gemini review, /q review",
        priority: "high",
        automated: true,
        reason: "AI review required before merge",
      });
    }

    if (status === "ready_to_merge") {
      actions.push({
        action: "Merge PR",
        priority: "high",
        automated: false, // Merge should be explicit
        reason: "All checks pass and feedback addressed",
      });
    }

    return actions;
  }

  private async generateSummary(
    pr: Awaited<ReturnType<GitHubClient["getPR"]>>,
    ci: Awaited<ReturnType<GitHubClient["getCIStatus"]>>,
    blockers: Blocker[],
    unaddressedFeedback: FeedbackItem[]
  ): Promise<string> {
    const { text } = await generateText({
      model: this.model,
      prompt: `Generate a concise summary of this PR's triage status.

PR: ${pr.title}
CI: ${ci.allPassing ? "✅ All passing" : ci.anyPending ? "⏳ Pending" : `❌ ${ci.failures.length} failures`}
Blockers: ${blockers.length > 0 ? blockers.map((b) => b.description).join(", ") : "None"}
Unaddressed feedback: ${unaddressedFeedback.length} items

Write 2-3 sentences summarizing the current state and what needs to happen next.`,
    });

    return text;
  }

  // ==========================================================================
  // Response Generation
  // ==========================================================================

  async generateFeedbackResponse(
    feedback: FeedbackItem,
    context: { prTitle: string; files: string[] }
  ): Promise<{ type: "fix" | "justification"; content: string }> {
    const { object } = await generateObject({
      model: this.model,
      schema: z.object({
        type: z.enum(["fix", "justification"]),
        content: z.string(),
        reasoning: z.string(),
      }),
      prompt: `Determine how to address this PR feedback.

PR: ${context.prTitle}
Files changed: ${context.files.join(", ")}

Feedback from ${feedback.author}:
${feedback.body}

${feedback.path ? `File: ${feedback.path}` : ""}
${feedback.line ? `Line: ${feedback.line}` : ""}

Options:
1. "fix" - Generate code/text to fix the issue
2. "justification" - Explain why this feedback should not be implemented

Choose "fix" if:
- There's a clear suggestion to implement
- The issue is valid and should be fixed
- It's a straightforward change

Choose "justification" if:
- The feedback is a false positive
- It conflicts with project conventions
- It's out of scope for this PR

Provide the content (code fix or justification text) and your reasoning.`,
    });

    return {
      type: object.type,
      content: object.content,
    };
  }
}
