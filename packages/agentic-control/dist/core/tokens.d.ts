/**
 * Intelligent Token Management for Multi-Organization GitHub Access
 *
 * This module provides automatic token switching based on the target organization.
 * It ensures:
 * - FlipsideCrypto repos use GITHUB_FSC_TOKEN
 * - jbcom repos use GITHUB_JBCOM_TOKEN
 * - PR reviews ALWAYS use a consistent identity (GITHUB_JBCOM_TOKEN by default)
 */
import type { TokenConfig, OrganizationConfig, Result } from "./types.js";
/**
 * Get the current token configuration
 */
export declare function getTokenConfig(): TokenConfig;
/**
 * Update the token configuration
 */
export declare function setTokenConfig(config: Partial<TokenConfig>): void;
/**
 * Add or update an organization configuration
 */
export declare function addOrganization(org: OrganizationConfig): void;
/**
 * Extract organization name from a repository URL or full name
 *
 * @example
 * extractOrg("https://github.com/FlipsideCrypto/terraform-modules") // "FlipsideCrypto"
 * extractOrg("jbcom/jbcom-control-center") // "jbcom"
 * extractOrg("FlipsideCrypto/fsc-control-center.git") // "FlipsideCrypto"
 */
export declare function extractOrg(repoUrl: string): string | null;
/**
 * Get the token environment variable name for a given organization
 *
 * @param org - Organization name (e.g., "FlipsideCrypto", "jbcom")
 * @returns Environment variable name for the token
 */
export declare function getTokenEnvVar(org: string): string;
/**
 * Get the actual token value for an organization
 *
 * @param org - Organization name
 * @returns Token value or undefined if not set
 */
export declare function getTokenForOrg(org: string): string | undefined;
/**
 * Get the token for a repository URL
 * Automatically extracts the organization and returns the appropriate token
 *
 * @param repoUrl - Repository URL or owner/repo format
 * @returns Token value or undefined if not set
 *
 * @example
 * getTokenForRepo("https://github.com/FlipsideCrypto/terraform-modules")
 * // Returns value of GITHUB_FSC_TOKEN
 *
 * getTokenForRepo("jbcom/jbcom-control-center")
 * // Returns value of GITHUB_JBCOM_TOKEN
 */
export declare function getTokenForRepo(repoUrl: string): string | undefined;
/**
 * Get the token that should ALWAYS be used for PR reviews
 * This ensures a consistent identity across all PR interactions
 *
 * @returns Token value or undefined if not set
 */
export declare function getPRReviewToken(): string | undefined;
/**
 * Get the PR review token environment variable name
 */
export declare function getPRReviewTokenEnvVar(): string;
/**
 * Validate that required tokens are available
 *
 * @param orgs - Organization names to validate (optional, validates all if not specified)
 * @returns Validation result with any missing tokens
 */
export declare function validateTokens(orgs?: string[]): Result<string[]>;
/**
 * Get organization configuration
 */
export declare function getOrgConfig(org: string): OrganizationConfig | undefined;
/**
 * Get all configured organizations
 */
export declare function getConfiguredOrgs(): string[];
/**
 * Create environment variables object for a subprocess targeting a specific org
 * Useful when spawning child processes that need the correct GitHub token
 *
 * @param repoUrl - Repository URL to get token for
 * @returns Object with GH_TOKEN set to the appropriate value
 *
 * @example
 * execSync('gh pr list', { env: { ...process.env, ...getEnvForRepo(repoUrl) } })
 */
export declare function getEnvForRepo(repoUrl: string): Record<string, string>;
/**
 * Create environment variables for PR review operations
 * Always uses the consistent PR review identity
 *
 * @returns Object with GH_TOKEN set for PR review
 */
export declare function getEnvForPRReview(): Record<string, string>;
/**
 * Check if we have a valid token for an organization
 */
export declare function hasTokenForOrg(org: string): boolean;
/**
 * Check if we have a valid token for a repository
 */
export declare function hasTokenForRepo(repoUrl: string): boolean;
/**
 * Get a summary of token availability
 */
export declare function getTokenSummary(): Record<string, {
    envVar: string;
    available: boolean;
}>;
//# sourceMappingURL=tokens.d.ts.map