/**
 * CursorAPI - Direct HTTP client for Cursor Background Agent API
 *
 * Bypasses MCP for direct API access with better performance and reliability.
 * Adapted from cursor-fleet with enhanced error handling.
 */
/** Default API base URL - configurable for testing/staging */
const DEFAULT_BASE_URL = "https://api.cursor.com/v0";
/** Validation regex for agent IDs (alphanumeric with hyphens) */
const AGENT_ID_PATTERN = /^[a-zA-Z0-9-]+$/;
/** Maximum prompt text length */
const MAX_PROMPT_LENGTH = 100000;
/** Maximum repository name length */
const MAX_REPO_LENGTH = 200;
/**
 * Validates an agent ID to prevent injection attacks
 */
function validateAgentId(agentId) {
    if (!agentId || typeof agentId !== "string") {
        throw new Error("Agent ID is required and must be a string");
    }
    if (agentId.length > 100) {
        throw new Error("Agent ID exceeds maximum length (100 characters)");
    }
    if (!AGENT_ID_PATTERN.test(agentId)) {
        throw new Error("Agent ID contains invalid characters (only alphanumeric and hyphens allowed)");
    }
}
/**
 * Validates prompt text
 */
function validatePromptText(text) {
    if (!text || typeof text !== "string") {
        throw new Error("Prompt text is required and must be a string");
    }
    if (text.trim().length === 0) {
        throw new Error("Prompt text cannot be empty");
    }
    if (text.length > MAX_PROMPT_LENGTH) {
        throw new Error(`Prompt text exceeds maximum length (${MAX_PROMPT_LENGTH} characters)`);
    }
}
/**
 * Validates repository name
 */
function validateRepository(repository) {
    if (!repository || typeof repository !== "string") {
        throw new Error("Repository is required and must be a string");
    }
    if (repository.length > MAX_REPO_LENGTH) {
        throw new Error(`Repository name exceeds maximum length (${MAX_REPO_LENGTH} characters)`);
    }
    // Basic format check: owner/repo or URL
    if (!repository.includes("/")) {
        throw new Error("Repository must be in format 'owner/repo' or a valid URL");
    }
}
/**
 * Sanitizes error messages to prevent sensitive data leakage
 */
function sanitizeError(error) {
    const message = error instanceof Error ? error.message : String(error);
    // Remove potential API keys, tokens, or sensitive patterns
    return message
        .replace(/Bearer\s+[a-zA-Z0-9._-]+/gi, "Bearer [REDACTED]")
        .replace(/api[_-]?key[=:]\s*["']?[a-zA-Z0-9._-]+["']?/gi, "api_key=[REDACTED]")
        .replace(/token[=:]\s*["']?[a-zA-Z0-9._-]+["']?/gi, "token=[REDACTED]");
}
export class CursorAPI {
    apiKey;
    timeout;
    baseUrl;
    constructor(options = {}) {
        // Check for API key in order: options, CURSOR_API_KEY
        this.apiKey = options.apiKey ?? process.env.CURSOR_API_KEY ?? "";
        this.timeout = options.timeout ?? 60000;
        this.baseUrl = options.baseUrl ?? process.env.CURSOR_API_BASE_URL ?? DEFAULT_BASE_URL;
        if (!this.apiKey) {
            throw new Error("CURSOR_API_KEY is required. Set it in environment or pass to constructor.");
        }
    }
    /**
     * Check if API key is available
     */
    static isAvailable() {
        return !!process.env.CURSOR_API_KEY;
    }
    async request(endpoint, method = "GET", body) {
        const url = `${this.baseUrl}${endpoint}`;
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);
        try {
            const response = await fetch(url, {
                method,
                headers: {
                    "Authorization": `Bearer ${this.apiKey}`,
                    "Content-Type": "application/json",
                },
                body: body ? JSON.stringify(body) : undefined,
                signal: controller.signal,
            });
            if (!response.ok) {
                const errorText = await response.text();
                let details;
                try {
                    const parsed = JSON.parse(errorText);
                    details = parsed.message || parsed.error || "Unknown API error";
                }
                catch {
                    details = sanitizeError(errorText);
                }
                return {
                    success: false,
                    error: `API Error ${response.status}: ${details}`,
                };
            }
            // Handle empty responses (e.g., 204 No Content)
            const contentType = response.headers.get("content-type");
            if (!contentType || !contentType.includes("application/json")) {
                return { success: true, data: {} };
            }
            const text = await response.text();
            if (!text || text.trim() === "") {
                return { success: true, data: {} };
            }
            try {
                const data = JSON.parse(text);
                return { success: true, data };
            }
            catch {
                return {
                    success: false,
                    error: "Invalid JSON response from API"
                };
            }
        }
        catch (error) {
            if (error instanceof Error && error.name === "AbortError") {
                return { success: false, error: `Request timeout after ${this.timeout}ms` };
            }
            return { success: false, error: sanitizeError(error) };
        }
        finally {
            clearTimeout(timeoutId);
        }
    }
    /**
     * List all agents
     */
    async listAgents() {
        const result = await this.request("/agents");
        if (!result.success)
            return { success: false, error: result.error };
        return { success: true, data: result.data?.agents ?? [] };
    }
    /**
     * Get status of a specific agent
     */
    async getAgentStatus(agentId) {
        validateAgentId(agentId);
        const encodedId = encodeURIComponent(agentId);
        return this.request(`/agents/${encodedId}`);
    }
    /**
     * Get conversation history for an agent
     */
    async getAgentConversation(agentId) {
        validateAgentId(agentId);
        const encodedId = encodeURIComponent(agentId);
        return this.request(`/agents/${encodedId}/conversation`);
    }
    /**
     * Launch a new agent
     */
    async launchAgent(options) {
        validatePromptText(options.prompt.text);
        validateRepository(options.source.repository);
        if (options.source.ref !== undefined) {
            if (typeof options.source.ref !== "string" || options.source.ref.length > 200) {
                throw new Error("Invalid ref: must be a string under 200 characters");
            }
        }
        return this.request("/agents", "POST", options);
    }
    /**
     * Send a follow-up message to an agent
     */
    async addFollowup(agentId, prompt) {
        validateAgentId(agentId);
        validatePromptText(prompt.text);
        const encodedId = encodeURIComponent(agentId);
        return this.request(`/agents/${encodedId}/followup`, "POST", { prompt });
    }
    /**
     * List available repositories
     */
    async listRepositories() {
        const result = await this.request("/repositories");
        if (!result.success)
            return { success: false, error: result.error };
        return { success: true, data: result.data?.repositories ?? [] };
    }
}
//# sourceMappingURL=cursor-api.js.map