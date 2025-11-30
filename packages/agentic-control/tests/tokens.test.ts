/**
 * Tests for token management system
 */

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import {
  extractOrg,
  getTokenEnvVar,
  getTokenForRepo,
  getTokenForOrg,
  validateTokens,
  getConfiguredOrgs,
  setTokenConfig,
  getTokenConfig,
  hasTokenForOrg,
  hasTokenForRepo,
  getEnvForRepo,
  getEnvForPRReview,
} from "../src/core/tokens.js";

describe("Token Management", () => {
  // Save original env
  const originalEnv = { ...process.env };

  beforeEach(() => {
    // Reset env for each test
    process.env = { ...originalEnv };
  });

  afterEach(() => {
    // Restore original env
    process.env = originalEnv;
  });

  describe("extractOrg", () => {
    it("extracts org from full GitHub URL", () => {
      expect(extractOrg("https://github.com/FlipsideCrypto/terraform-modules")).toBe("FlipsideCrypto");
      expect(extractOrg("https://github.com/jbcom/jbcom-control-center")).toBe("jbcom");
    });

    it("extracts org from owner/repo format", () => {
      expect(extractOrg("FlipsideCrypto/terraform-modules")).toBe("FlipsideCrypto");
      expect(extractOrg("jbcom/extended-data-types")).toBe("jbcom");
    });

    it("handles git clone URLs", () => {
      expect(extractOrg("https://github.com/FlipsideCrypto/repo.git")).toBe("FlipsideCrypto");
    });

    it("returns null for invalid input", () => {
      expect(extractOrg("invalid")).toBeNull();
      expect(extractOrg("")).toBeNull();
    });
  });

  describe("getTokenEnvVar", () => {
    it("returns correct env var for known orgs", () => {
      expect(getTokenEnvVar("FlipsideCrypto")).toBe("GITHUB_FSC_TOKEN");
      expect(getTokenEnvVar("jbcom")).toBe("GITHUB_JBCOM_TOKEN");
    });

    it("returns default env var for unknown orgs", () => {
      expect(getTokenEnvVar("unknown-org")).toBe("GITHUB_TOKEN");
    });
  });

  describe("getTokenForOrg", () => {
    it("returns token value when env var is set", () => {
      process.env.GITHUB_FSC_TOKEN = "test-fsc-token";
      expect(getTokenForOrg("FlipsideCrypto")).toBe("test-fsc-token");
    });

    it("returns undefined when env var is not set", () => {
      delete process.env.GITHUB_FSC_TOKEN;
      expect(getTokenForOrg("FlipsideCrypto")).toBeUndefined();
    });
  });

  describe("getTokenForRepo", () => {
    it("returns correct token for repo URL", () => {
      process.env.GITHUB_FSC_TOKEN = "fsc-token";
      process.env.GITHUB_JBCOM_TOKEN = "jbcom-token";

      expect(getTokenForRepo("https://github.com/FlipsideCrypto/repo")).toBe("fsc-token");
      expect(getTokenForRepo("jbcom/repo")).toBe("jbcom-token");
    });

    it("returns default token for unknown org", () => {
      process.env.GITHUB_TOKEN = "default-token";
      expect(getTokenForRepo("unknown/repo")).toBe("default-token");
    });
  });

  describe("validateTokens", () => {
    it("returns success when all tokens available", () => {
      process.env.GITHUB_FSC_TOKEN = "fsc";
      process.env.GITHUB_JBCOM_TOKEN = "jbcom";

      const result = validateTokens(["FlipsideCrypto", "jbcom"]);
      expect(result.success).toBe(true);
    });

    it("returns error when tokens missing", () => {
      delete process.env.GITHUB_FSC_TOKEN;
      process.env.GITHUB_JBCOM_TOKEN = "jbcom";

      const result = validateTokens(["FlipsideCrypto"]);
      expect(result.success).toBe(false);
      expect(result.data).toContain("FlipsideCrypto: GITHUB_FSC_TOKEN not set");
    });
  });

  describe("getConfiguredOrgs", () => {
    it("returns default configured orgs", () => {
      const orgs = getConfiguredOrgs();
      expect(orgs).toContain("FlipsideCrypto");
      expect(orgs).toContain("jbcom");
    });
  });

  describe("hasTokenForOrg", () => {
    it("returns true when token is set", () => {
      process.env.GITHUB_FSC_TOKEN = "token";
      expect(hasTokenForOrg("FlipsideCrypto")).toBe(true);
    });

    it("returns false when token is not set", () => {
      delete process.env.GITHUB_FSC_TOKEN;
      expect(hasTokenForOrg("FlipsideCrypto")).toBe(false);
    });
  });

  describe("hasTokenForRepo", () => {
    it("returns true when repo token is available", () => {
      process.env.GITHUB_JBCOM_TOKEN = "token";
      expect(hasTokenForRepo("jbcom/repo")).toBe(true);
    });
  });

  describe("getEnvForRepo", () => {
    it("returns env object with GH_TOKEN", () => {
      process.env.GITHUB_FSC_TOKEN = "my-token";
      const env = getEnvForRepo("FlipsideCrypto/repo");
      expect(env.GH_TOKEN).toBe("my-token");
      expect(env.GITHUB_TOKEN).toBe("my-token");
    });

    it("returns empty object when no token", () => {
      delete process.env.GITHUB_FSC_TOKEN;
      const env = getEnvForRepo("FlipsideCrypto/repo");
      expect(env).toEqual({});
    });
  });

  describe("getEnvForPRReview", () => {
    it("returns env with PR review token", () => {
      process.env.GITHUB_JBCOM_TOKEN = "review-token";
      const env = getEnvForPRReview();
      expect(env.GH_TOKEN).toBe("review-token");
    });
  });
});
