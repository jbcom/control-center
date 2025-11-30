/**
 * Token-Aware GitHub Client
 *
 * Provides GitHub API operations with intelligent token switching:
 * - Automatically selects the correct token based on organization
 * - Uses consistent identity for PR reviews
 * - Wraps @octokit/rest with multi-org support
 */
import { Octokit } from "@octokit/rest";
import type { Result, Repository, PullRequest, PRComment } from "../core/types.js";
export declare class GitHubClient {
    /**
     * Get an Octokit instance for a repository
     * Automatically selects the correct token based on org
     */
    static forRepo(repoUrl: string): Octokit | null;
    /**
     * Get an Octokit instance for PR review operations
     * Always uses the consistent PR review identity
     */
    static forPRReview(): Octokit | null;
    /**
     * Get repository information
     */
    static getRepo(owner: string, repo: string): Promise<Result<Repository>>;
    /**
     * List repositories for an organization
     */
    static listOrgRepos(org: string, options?: {
        type?: "all" | "public" | "private" | "forks" | "sources" | "member";
        perPage?: number;
    }): Promise<Result<Repository[]>>;
    /**
     * Get pull request information
     */
    static getPR(owner: string, repo: string, prNumber: number): Promise<Result<PullRequest>>;
    /**
     * List PR comments
     */
    static listPRComments(owner: string, repo: string, prNumber: number): Promise<Result<PRComment[]>>;
    /**
     * Post a PR comment (ALWAYS uses PR review identity)
     */
    static postPRComment(owner: string, repo: string, prNumber: number, body: string): Promise<Result<PRComment>>;
    /**
     * Request a review on a PR (ALWAYS uses PR review identity)
     */
    static requestReview(owner: string, repo: string, prNumber: number, reviewers: string[]): Promise<Result<void>>;
    /**
     * Create a pull request
     */
    static createPR(owner: string, repo: string, options: {
        title: string;
        body?: string;
        head: string;
        base: string;
        draft?: boolean;
    }): Promise<Result<PullRequest>>;
    /**
     * Merge a pull request (uses repo-appropriate token)
     */
    static mergePR(owner: string, repo: string, prNumber: number, options?: {
        mergeMethod?: "merge" | "squash" | "rebase";
        commitTitle?: string;
        commitMessage?: string;
    }): Promise<Result<void>>;
}
/**
 * Execute a gh CLI command with appropriate token for the repo
 */
export declare function ghForRepo(command: string, repoUrl: string): string;
/**
 * Execute a gh CLI command with PR review token
 */
export declare function ghForPRReview(command: string): string;
/**
 * Clone a repository with appropriate token
 */
export declare function cloneRepo(repoUrl: string, destPath: string): void;
//# sourceMappingURL=client.d.ts.map