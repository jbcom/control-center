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

// ============================================
// Default Configuration
// ============================================

/**
 * Default organization configurations
 * Can be extended via environment variables or config file
 */
const DEFAULT_ORGANIZATIONS: Record<string, OrganizationConfig> = {
  "FlipsideCrypto": {
    name: "FlipsideCrypto",
    tokenEnvVar: "GITHUB_FSC_TOKEN",
    defaultBranch: "main",
    isEnterprise: true,
  },
  "jbcom": {
    name: "jbcom",
    tokenEnvVar: "GITHUB_JBCOM_TOKEN",
    defaultBranch: "main",
    isEnterprise: false,
  },
};

/**
 * Default token configuration
 */
const DEFAULT_CONFIG: TokenConfig = {
  organizations: DEFAULT_ORGANIZATIONS,
  defaultTokenEnvVar: "GITHUB_TOKEN",
  prReviewTokenEnvVar: "GITHUB_JBCOM_TOKEN",
};

// ============================================
// Configuration State
// ============================================

let currentConfig: TokenConfig = { ...DEFAULT_CONFIG };

/**
 * Load additional organization configs from environment
 * Format: AGENTIC_ORG_<NAME>_TOKEN=ENV_VAR_NAME
 */
function loadEnvConfig(): void {
  const orgPattern = /^AGENTIC_ORG_([A-Z0-9_]+)_TOKEN$/;
  
  for (const [key, value] of Object.entries(process.env)) {
    const match = key.match(orgPattern);
    if (match && value) {
      const orgName = match[1].replace(/_/g, "-");
      if (!currentConfig.organizations[orgName]) {
        currentConfig.organizations[orgName] = {
          name: orgName,
          tokenEnvVar: value,
        };
      }
    }
  }

  // Override PR review token if specified
  if (process.env.AGENTIC_PR_REVIEW_TOKEN) {
    currentConfig.prReviewTokenEnvVar = process.env.AGENTIC_PR_REVIEW_TOKEN;
  }

  // Override default token if specified
  if (process.env.AGENTIC_DEFAULT_TOKEN) {
    currentConfig.defaultTokenEnvVar = process.env.AGENTIC_DEFAULT_TOKEN;
  }
}

// Load env config on module initialization
loadEnvConfig();

// ============================================
// Public API
// ============================================

/**
 * Get the current token configuration
 */
export function getTokenConfig(): TokenConfig {
  return { ...currentConfig };
}

/**
 * Update the token configuration
 */
export function setTokenConfig(config: Partial<TokenConfig>): void {
  currentConfig = {
    ...currentConfig,
    ...config,
    organizations: {
      ...currentConfig.organizations,
      ...config.organizations,
    },
  };
}

/**
 * Add or update an organization configuration
 */
export function addOrganization(org: OrganizationConfig): void {
  currentConfig.organizations[org.name] = org;
}

/**
 * Extract organization name from a repository URL or full name
 * 
 * @example
 * extractOrg("https://github.com/FlipsideCrypto/terraform-modules") // "FlipsideCrypto"
 * extractOrg("jbcom/jbcom-control-center") // "jbcom"
 * extractOrg("FlipsideCrypto/fsc-control-center.git") // "FlipsideCrypto"
 */
export function extractOrg(repoUrl: string): string | null {
  // Handle full GitHub URLs
  const urlMatch = repoUrl.match(/github\.com[/:]([^/]+)/);
  if (urlMatch) {
    return urlMatch[1];
  }

  // Handle owner/repo format
  const shortMatch = repoUrl.match(/^([^/]+)\//);
  if (shortMatch) {
    return shortMatch[1];
  }

  return null;
}

/**
 * Get the token environment variable name for a given organization
 * 
 * @param org - Organization name (e.g., "FlipsideCrypto", "jbcom")
 * @returns Environment variable name for the token
 */
export function getTokenEnvVar(org: string): string {
  const config = currentConfig.organizations[org];
  return config?.tokenEnvVar ?? currentConfig.defaultTokenEnvVar;
}

/**
 * Get the actual token value for an organization
 * 
 * @param org - Organization name
 * @returns Token value or undefined if not set
 */
export function getTokenForOrg(org: string): string | undefined {
  const envVar = getTokenEnvVar(org);
  return process.env[envVar];
}

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
export function getTokenForRepo(repoUrl: string): string | undefined {
  const org = extractOrg(repoUrl);
  if (!org) {
    return process.env[currentConfig.defaultTokenEnvVar];
  }
  return getTokenForOrg(org);
}

/**
 * Get the token that should ALWAYS be used for PR reviews
 * This ensures a consistent identity across all PR interactions
 * 
 * @returns Token value or undefined if not set
 */
export function getPRReviewToken(): string | undefined {
  return process.env[currentConfig.prReviewTokenEnvVar];
}

/**
 * Get the PR review token environment variable name
 */
export function getPRReviewTokenEnvVar(): string {
  return currentConfig.prReviewTokenEnvVar;
}

/**
 * Validate that required tokens are available
 * 
 * @param orgs - Organization names to validate (optional, validates all if not specified)
 * @returns Validation result with any missing tokens
 */
export function validateTokens(orgs?: string[]): Result<string[]> {
  const missing: string[] = [];
  const orgsToCheck = orgs ?? Object.keys(currentConfig.organizations);

  for (const org of orgsToCheck) {
    const token = getTokenForOrg(org);
    if (!token) {
      const envVar = getTokenEnvVar(org);
      missing.push(`${org}: ${envVar} not set`);
    }
  }

  // Always check PR review token
  if (!getPRReviewToken()) {
    missing.push(`PR Review: ${currentConfig.prReviewTokenEnvVar} not set`);
  }

  return {
    success: missing.length === 0,
    data: missing,
    error: missing.length > 0 
      ? `Missing tokens: ${missing.join(", ")}` 
      : undefined,
  };
}

/**
 * Get organization configuration
 */
export function getOrgConfig(org: string): OrganizationConfig | undefined {
  return currentConfig.organizations[org];
}

/**
 * Get all configured organizations
 */
export function getConfiguredOrgs(): string[] {
  return Object.keys(currentConfig.organizations);
}

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
export function getEnvForRepo(repoUrl: string): Record<string, string> {
  const token = getTokenForRepo(repoUrl);
  if (!token) {
    return {};
  }
  return {
    GH_TOKEN: token,
    GITHUB_TOKEN: token,
  };
}

/**
 * Create environment variables for PR review operations
 * Always uses the consistent PR review identity
 * 
 * @returns Object with GH_TOKEN set for PR review
 */
export function getEnvForPRReview(): Record<string, string> {
  const token = getPRReviewToken();
  if (!token) {
    return {};
  }
  return {
    GH_TOKEN: token,
    GITHUB_TOKEN: token,
  };
}

// ============================================
// Convenience Wrappers
// ============================================

/**
 * Check if we have a valid token for an organization
 */
export function hasTokenForOrg(org: string): boolean {
  return !!getTokenForOrg(org);
}

/**
 * Check if we have a valid token for a repository
 */
export function hasTokenForRepo(repoUrl: string): boolean {
  return !!getTokenForRepo(repoUrl);
}

/**
 * Get a summary of token availability
 */
export function getTokenSummary(): Record<string, { envVar: string; available: boolean }> {
  const summary: Record<string, { envVar: string; available: boolean }> = {};
  
  for (const org of getConfiguredOrgs()) {
    const envVar = getTokenEnvVar(org);
    summary[org] = {
      envVar,
      available: !!process.env[envVar],
    };
  }

  summary["PR Review"] = {
    envVar: currentConfig.prReviewTokenEnvVar,
    available: !!getPRReviewToken(),
  };

  return summary;
}
