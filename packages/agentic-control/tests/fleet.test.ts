/**
 * Tests for Fleet and CursorAPI reliability improvements
 * 
 * These tests verify:
 * - Input validation returns Result instead of throwing
 * - Retry logic for transient failures
 * - Error categorization
 * - Actionable error messages
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";

// Mock fetch before imports
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Import after mocking
import { CursorAPI } from "../src/fleet/cursor-api.js";
import { Fleet } from "../src/fleet/fleet.js";

describe("CursorAPI", () => {
  const originalEnv = { ...process.env };

  beforeEach(() => {
    process.env.CURSOR_API_KEY = "test-api-key";
    mockFetch.mockReset();
  });

  afterEach(() => {
    process.env = { ...originalEnv };
  });

  describe("constructor", () => {
    it("throws when API key is not provided", () => {
      delete process.env.CURSOR_API_KEY;
      expect(() => new CursorAPI()).toThrow("CURSOR_API_KEY is required");
    });

    it("accepts API key from constructor options", () => {
      delete process.env.CURSOR_API_KEY;
      expect(() => new CursorAPI({ apiKey: "custom-key" })).not.toThrow();
    });

    it("static isAvailable returns false when no API key", () => {
      delete process.env.CURSOR_API_KEY;
      expect(CursorAPI.isAvailable()).toBe(false);
    });

    it("static isAvailable returns true when API key is set", () => {
      expect(CursorAPI.isAvailable()).toBe(true);
    });
  });

  describe("launchAgent validation", () => {
    let api: CursorAPI;

    beforeEach(() => {
      api = new CursorAPI();
    });

    it("returns validation error for empty prompt text", async () => {
      const result = await api.launchAgent({
        prompt: { text: "   " }, // Whitespace-only text
        source: { repository: "owner/repo" },
      });

      expect(result.success).toBe(false);
      expect(result.error).toContain("Prompt text cannot be empty");
      expect((result as { category?: string }).category).toBe("validation");
      expect((result as { retryable?: boolean }).retryable).toBe(false);
    });

    it("returns validation error for missing repository slash", async () => {
      const result = await api.launchAgent({
        prompt: { text: "Test task" },
        source: { repository: "invalid-repo" },
      });

      expect(result.success).toBe(false);
      expect(result.error).toContain("Repository must be in format");
      expect((result as { category?: string }).category).toBe("validation");
    });

    it("returns validation error for prompt exceeding max length", async () => {
      const longPrompt = "x".repeat(100001);
      const result = await api.launchAgent({
        prompt: { text: longPrompt },
        source: { repository: "owner/repo" },
      });

      expect(result.success).toBe(false);
      expect(result.error).toContain("exceeds maximum length");
      expect((result as { category?: string }).category).toBe("validation");
    });

    it("returns validation error for invalid ref", async () => {
      const longRef = "x".repeat(201);
      const result = await api.launchAgent({
        prompt: { text: "Test task" },
        source: { repository: "owner/repo", ref: longRef },
      });

      expect(result.success).toBe(false);
      expect(result.error).toContain("Invalid ref");
    });
  });

  describe("error categorization", () => {
    let api: CursorAPI;

    beforeEach(() => {
      api = new CursorAPI({ maxRetries: 0 }); // Disable retries for these tests
    });

    it("categorizes 401 as authentication error", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        text: async () => JSON.stringify({ error: "Unauthorized" }),
      });

      const result = await api.launchAgent({
        prompt: { text: "Test" },
        source: { repository: "owner/repo" },
      });

      expect(result.success).toBe(false);
      expect((result as { category?: string }).category).toBe("authentication");
    });

    it("categorizes 403 as authorization error", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 403,
        text: async () => JSON.stringify({ error: "Forbidden" }),
      });

      const result = await api.launchAgent({
        prompt: { text: "Test" },
        source: { repository: "owner/repo" },
      });

      expect(result.success).toBe(false);
      expect((result as { category?: string }).category).toBe("authorization");
    });

    it("categorizes 429 as rate_limit error and marks as retryable", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 429,
        text: async () => JSON.stringify({ error: "Too Many Requests" }),
      });

      const result = await api.launchAgent({
        prompt: { text: "Test" },
        source: { repository: "owner/repo" },
      });

      expect(result.success).toBe(false);
      expect((result as { category?: string }).category).toBe("rate_limit");
      expect((result as { retryable?: boolean }).retryable).toBe(true);
    });

    it("categorizes 500 as server error and marks as retryable", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        text: async () => JSON.stringify({ error: "Internal Server Error" }),
      });

      const result = await api.launchAgent({
        prompt: { text: "Test" },
        source: { repository: "owner/repo" },
      });

      expect(result.success).toBe(false);
      expect((result as { category?: string }).category).toBe("server");
      expect((result as { retryable?: boolean }).retryable).toBe(true);
    });
  });

  describe("retry logic", () => {
    it("retries on 503 Service Unavailable", async () => {
      const api = new CursorAPI({ maxRetries: 2, retryDelay: 10 });

      // First two calls fail, third succeeds
      mockFetch
        .mockResolvedValueOnce({
          ok: false,
          status: 503,
          text: async () => "Service Unavailable",
        })
        .mockResolvedValueOnce({
          ok: false,
          status: 503,
          text: async () => "Service Unavailable",
        })
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          headers: new Map([["content-type", "application/json"]]),
          text: async () => JSON.stringify({ id: "agent-123", status: "RUNNING" }),
        });

      const result = await api.launchAgent({
        prompt: { text: "Test task" },
        source: { repository: "owner/repo" },
      });

      expect(mockFetch).toHaveBeenCalledTimes(3);
      expect(result.success).toBe(true);
      expect(result.data?.id).toBe("agent-123");
    });

    it("stops retrying after max retries exceeded", async () => {
      const api = new CursorAPI({ maxRetries: 1, retryDelay: 10 });

      // All calls fail
      mockFetch.mockResolvedValue({
        ok: false,
        status: 503,
        text: async () => "Service Unavailable",
      });

      const result = await api.launchAgent({
        prompt: { text: "Test task" },
        source: { repository: "owner/repo" },
      });

      expect(mockFetch).toHaveBeenCalledTimes(2); // Initial + 1 retry
      expect(result.success).toBe(false);
    });

    it("does not retry on 400 Bad Request", async () => {
      const api = new CursorAPI({ maxRetries: 2, retryDelay: 10 });

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        text: async () => JSON.stringify({ error: "Bad Request" }),
      });

      const result = await api.launchAgent({
        prompt: { text: "Test task" },
        source: { repository: "owner/repo" },
      });

      expect(mockFetch).toHaveBeenCalledTimes(1);
      expect(result.success).toBe(false);
    });
  });

  describe("successful responses", () => {
    let api: CursorAPI;

    beforeEach(() => {
      api = new CursorAPI();
    });

    it("parses successful agent response", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Map([["content-type", "application/json"]]),
        text: async () => JSON.stringify({
          id: "agent-abc123",
          status: "RUNNING",
          source: { repository: "owner/repo" },
        }),
      });

      const result = await api.launchAgent({
        prompt: { text: "Test task" },
        source: { repository: "owner/repo" },
      });

      expect(result.success).toBe(true);
      expect(result.data?.id).toBe("agent-abc123");
      expect(result.data?.status).toBe("RUNNING");
    });
  });
});

describe("Fleet", () => {
  const originalEnv = { ...process.env };

  beforeEach(() => {
    process.env.CURSOR_API_KEY = "test-api-key";
    mockFetch.mockReset();
  });

  afterEach(() => {
    process.env = { ...originalEnv };
  });

  describe("initialization", () => {
    it("creates Fleet when API key is available", () => {
      const fleet = new Fleet();
      expect(fleet.isApiAvailable()).toBe(true);
      expect(fleet.getInitError()).toBeNull();
    });

    it("creates Fleet without API when key is missing", () => {
      delete process.env.CURSOR_API_KEY;
      const fleet = new Fleet();
      expect(fleet.isApiAvailable()).toBe(false);
      expect(fleet.getInitError()).toContain("CURSOR_API_KEY");
    });
  });

  describe("spawn", () => {
    it("returns actionable error when API is not available", async () => {
      delete process.env.CURSOR_API_KEY;
      const fleet = new Fleet();

      const result = await fleet.spawn({
        repository: "owner/repo",
        task: "Test task",
      });

      expect(result.success).toBe(false);
      expect(result.error).toContain("CURSOR_API_KEY");
      expect(result.category).toBe("authentication");
      expect(result.retryable).toBe(false);
    });

    it("spawns agent successfully", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Map([["content-type", "application/json"]]),
        text: async () => JSON.stringify({
          id: "agent-xyz",
          status: "RUNNING",
          source: { repository: "owner/repo" },
        }),
      });

      const fleet = new Fleet();
      const result = await fleet.spawn({
        repository: "owner/repo",
        task: "Test task",
      });

      expect(result.success).toBe(true);
      expect(result.data?.id).toBe("agent-xyz");
    });

    it("includes context in task when provided", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Map([["content-type", "application/json"]]),
        text: async () => JSON.stringify({
          id: "agent-xyz",
          status: "RUNNING",
        }),
      });

      const fleet = new Fleet();
      await fleet.spawn({
        repository: "owner/repo",
        task: "Test task",
        context: {
          controlManagerId: "manager-1",
          relatedAgents: ["agent-a", "agent-b"],
        },
      });

      // Check that fetch was called with the right body
      expect(mockFetch).toHaveBeenCalledTimes(1);
      const callArgs = mockFetch.mock.calls[0];
      const body = JSON.parse(callArgs[1].body);
      expect(body.prompt.text).toContain("Test task");
      expect(body.prompt.text).toContain("Control Manager Agent: manager-1");
      expect(body.prompt.text).toContain("agent-a, agent-b");
    });

    it("enhances error messages with actionable guidance", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        text: async () => JSON.stringify({ error: "Invalid API key" }),
      });

      const fleet = new Fleet();
      const result = await fleet.spawn({
        repository: "owner/repo",
        task: "Test task",
      });

      expect(result.success).toBe(false);
      expect(result.error).toContain("Action:");
      expect(result.error).toContain("CURSOR_API_KEY");
      expect(result.category).toBe("authentication");
    });
  });
});
