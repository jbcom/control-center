/**
 * CursorAPI - Direct HTTP client for Cursor Background Agent API
 *
 * Bypasses MCP for direct API access with better performance and reliability.
 * Adapted from cursor-fleet with enhanced error handling.
 */
import type { Agent, Conversation, Repository, Result } from "../core/types.js";
export interface CursorAPIOptions {
    /** API key (defaults to CURSOR_API_KEY env var) */
    apiKey?: string;
    /** Request timeout in milliseconds (default: 60000) */
    timeout?: number;
    /** API base URL (default: https://api.cursor.com/v0) */
    baseUrl?: string;
}
export declare class CursorAPI {
    private readonly apiKey;
    private readonly timeout;
    private readonly baseUrl;
    constructor(options?: CursorAPIOptions);
    /**
     * Check if API key is available
     */
    static isAvailable(): boolean;
    private request;
    /**
     * List all agents
     */
    listAgents(): Promise<Result<Agent[]>>;
    /**
     * Get status of a specific agent
     */
    getAgentStatus(agentId: string): Promise<Result<Agent>>;
    /**
     * Get conversation history for an agent
     */
    getAgentConversation(agentId: string): Promise<Result<Conversation>>;
    /**
     * Launch a new agent
     */
    launchAgent(options: {
        prompt: {
            text: string;
        };
        source: {
            repository: string;
            ref?: string;
        };
        model?: string;
    }): Promise<Result<Agent>>;
    /**
     * Send a follow-up message to an agent
     */
    addFollowup(agentId: string, prompt: {
        text: string;
    }): Promise<Result<void>>;
    /**
     * List available repositories
     */
    listRepositories(): Promise<Result<Repository[]>>;
}
//# sourceMappingURL=cursor-api.d.ts.map