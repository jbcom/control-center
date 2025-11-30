/**
 * Token-Aware GitHub Client
 *
 * Provides GitHub API operations with intelligent token switching:
 * - Automatically selects the correct token based on organization
 * - Uses consistent identity for PR reviews
 * - Wraps @octokit/rest with multi-org support
 */
import { Octokit } from "@octokit/rest";
import { execSync } from "node:child_process";
import { getTokenForRepo, getPRReviewToken, getEnvForRepo, getEnvForPRReview, extractOrg, } from "../core/tokens.js";
import { log } from "../core/config.js";
// ============================================
// Octokit Cache (one per token)
// ============================================
const octokitCache = new Map();
/**
 * Get or create an Octokit instance for a specific token
 */
function getOctokit(token) {
    let octokit = octokitCache.get(token);
    if (!octokit) {
        octokit = new Octokit({ auth: token });
        octokitCache.set(token, octokit);
    }
    return octokit;
}
// ============================================
// GitHub Client Class
// ============================================
export class GitHubClient {
    /**
     * Get an Octokit instance for a repository
     * Automatically selects the correct token based on org
     */
    static forRepo(repoUrl) {
        const token = getTokenForRepo(repoUrl);
        if (!token) {
            log.warn(`No token available for repo: ${repoUrl}`);
            return null;
        }
        return getOctokit(token);
    }
    /**
     * Get an Octokit instance for PR review operations
     * Always uses the consistent PR review identity
     */
    static forPRReview() {
        const token = getPRReviewToken();
        if (!token) {
            log.warn("No PR review token available");
            return null;
        }
        return getOctokit(token);
    }
    /**
     * Get repository information
     */
    static async getRepo(owner, repo) {
        const octokit = this.forRepo(`${owner}/${repo}`);
        if (!octokit) {
            return { success: false, error: "No token available for this repository" };
        }
        try {
            const { data } = await octokit.repos.get({ owner, repo });
            return {
                success: true,
                data: {
                    owner: data.owner.login,
                    name: data.name,
                    fullName: data.full_name,
                    defaultBranch: data.default_branch,
                    isPrivate: data.private,
                    url: data.html_url,
                },
            };
        }
        catch (error) {
            return { success: false, error: String(error) };
        }
    }
    /**
     * List repositories for an organization
     */
    static async listOrgRepos(org, options) {
        const octokit = this.forRepo(`${org}/any`);
        if (!octokit) {
            return { success: false, error: `No token available for org: ${org}` };
        }
        try {
            const { data } = await octokit.repos.listForOrg({
                org,
                type: options?.type ?? "all",
                per_page: options?.perPage ?? 100,
            });
            return {
                success: true,
                data: data.map(r => ({
                    owner: r.owner.login,
                    name: r.name,
                    fullName: r.full_name,
                    defaultBranch: r.default_branch ?? "main",
                    isPrivate: r.private,
                    url: r.html_url,
                })),
            };
        }
        catch (error) {
            return { success: false, error: String(error) };
        }
    }
    /**
     * Get pull request information
     */
    static async getPR(owner, repo, prNumber) {
        const octokit = this.forRepo(`${owner}/${repo}`);
        if (!octokit) {
            return { success: false, error: "No token available for this repository" };
        }
        try {
            const { data } = await octokit.pulls.get({ owner, repo, pull_number: prNumber });
            return {
                success: true,
                data: {
                    number: data.number,
                    title: data.title,
                    body: data.body ?? undefined,
                    state: data.state,
                    draft: data.draft ?? false,
                    url: data.html_url,
                    headBranch: data.head.ref,
                    baseBranch: data.base.ref,
                    author: data.user?.login ?? "unknown",
                },
            };
        }
        catch (error) {
            return { success: false, error: String(error) };
        }
    }
    /**
     * List PR comments
     */
    static async listPRComments(owner, repo, prNumber) {
        const octokit = this.forRepo(`${owner}/${repo}`);
        if (!octokit) {
            return { success: false, error: "No token available for this repository" };
        }
        try {
            const { data } = await octokit.issues.listComments({
                owner,
                repo,
                issue_number: prNumber,
                per_page: 100,
            });
            return {
                success: true,
                data: data.map(c => ({
                    id: c.id,
                    body: c.body ?? "",
                    author: c.user?.login ?? "unknown",
                    createdAt: c.created_at,
                    updatedAt: c.updated_at,
                })),
            };
        }
        catch (error) {
            return { success: false, error: String(error) };
        }
    }
    /**
     * Post a PR comment (ALWAYS uses PR review identity)
     */
    static async postPRComment(owner, repo, prNumber, body) {
        // ALWAYS use PR review token for commenting
        const octokit = this.forPRReview();
        if (!octokit) {
            return { success: false, error: "No PR review token available" };
        }
        try {
            const { data } = await octokit.issues.createComment({
                owner,
                repo,
                issue_number: prNumber,
                body,
            });
            return {
                success: true,
                data: {
                    id: data.id,
                    body: data.body ?? "",
                    author: data.user?.login ?? "unknown",
                    createdAt: data.created_at,
                    updatedAt: data.updated_at,
                },
            };
        }
        catch (error) {
            return { success: false, error: String(error) };
        }
    }
    /**
     * Request a review on a PR (ALWAYS uses PR review identity)
     */
    static async requestReview(owner, repo, prNumber, reviewers) {
        // ALWAYS use PR review token for review requests
        const octokit = this.forPRReview();
        if (!octokit) {
            return { success: false, error: "No PR review token available" };
        }
        try {
            await octokit.pulls.requestReviewers({
                owner,
                repo,
                pull_number: prNumber,
                reviewers,
            });
            return { success: true };
        }
        catch (error) {
            return { success: false, error: String(error) };
        }
    }
    /**
     * Create a pull request
     */
    static async createPR(owner, repo, options) {
        const octokit = this.forRepo(`${owner}/${repo}`);
        if (!octokit) {
            return { success: false, error: "No token available for this repository" };
        }
        try {
            const { data } = await octokit.pulls.create({
                owner,
                repo,
                title: options.title,
                body: options.body,
                head: options.head,
                base: options.base,
                draft: options.draft,
            });
            return {
                success: true,
                data: {
                    number: data.number,
                    title: data.title,
                    body: data.body ?? undefined,
                    state: data.state,
                    draft: data.draft ?? false,
                    url: data.html_url,
                    headBranch: data.head.ref,
                    baseBranch: data.base.ref,
                    author: data.user?.login ?? "unknown",
                },
            };
        }
        catch (error) {
            return { success: false, error: String(error) };
        }
    }
    /**
     * Merge a pull request (uses repo-appropriate token)
     */
    static async mergePR(owner, repo, prNumber, options) {
        const octokit = this.forRepo(`${owner}/${repo}`);
        if (!octokit) {
            return { success: false, error: "No token available for this repository" };
        }
        try {
            await octokit.pulls.merge({
                owner,
                repo,
                pull_number: prNumber,
                merge_method: options?.mergeMethod ?? "squash",
                commit_title: options?.commitTitle,
                commit_message: options?.commitMessage,
            });
            return { success: true };
        }
        catch (error) {
            return { success: false, error: String(error) };
        }
    }
}
// ============================================
// CLI-based Operations (for operations not in Octokit)
// ============================================
/**
 * Execute a gh CLI command with appropriate token for the repo
 */
export function ghForRepo(command, repoUrl) {
    const env = { ...process.env, ...getEnvForRepo(repoUrl) };
    return execSync(`gh ${command}`, { encoding: "utf-8", env });
}
/**
 * Execute a gh CLI command with PR review token
 */
export function ghForPRReview(command) {
    const env = { ...process.env, ...getEnvForPRReview() };
    return execSync(`gh ${command}`, { encoding: "utf-8", env });
}
/**
 * Clone a repository with appropriate token
 */
export function cloneRepo(repoUrl, destPath) {
    const token = getTokenForRepo(repoUrl);
    if (!token) {
        throw new Error(`No token available for repo: ${repoUrl}`);
    }
    // Extract the repo URL and inject token
    let cloneUrl = repoUrl;
    if (cloneUrl.startsWith("https://github.com/")) {
        cloneUrl = cloneUrl.replace("https://github.com/", `https://oauth2:${token}@github.com/`);
    }
    else if (!cloneUrl.includes("@")) {
        // Handle owner/repo format
        const org = extractOrg(repoUrl);
        const repoName = repoUrl.replace(`${org}/`, "");
        cloneUrl = `https://oauth2:${token}@github.com/${org}/${repoName}.git`;
    }
    execSync(`git clone "${cloneUrl}" "${destPath}"`, { stdio: "inherit" });
}
//# sourceMappingURL=client.js.map