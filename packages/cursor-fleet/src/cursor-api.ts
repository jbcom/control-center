/**
 * CursorAPI - Direct HTTP client for Cursor Background Agent API
 * 
 * Bypasses MCP for direct API access with better performance and reliability.
 */

import type { Agent, Conversation, Repository, FleetResult } from "./types.js";

const BASE_URL = "https://api.cursor.com/v0";

export class CursorAPI {
  private apiKey: string;
  private timeout: number;

  constructor(apiKey?: string, timeout: number = 60000) {
    this.apiKey = apiKey ?? process.env.CURSOR_API_KEY ?? "";
    this.timeout = timeout;
    
    if (!this.apiKey) {
      throw new Error("CURSOR_API_KEY is required. Set it in environment or pass to constructor.");
    }
  }

  private async request<T>(endpoint: string, method: string = "GET", body?: object): Promise<FleetResult<T>> {
    const url = `${BASE_URL}${endpoint}`;
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

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorText = await response.text();
        let details: string;
        try {
          const parsed = JSON.parse(errorText);
          details = parsed.message || parsed.error || errorText;
        } catch {
          details = errorText;
        }
        
        return {
          success: false,
          error: `API Error ${response.status}: ${details}`,
        };
      }

      const data = await response.json() as T;
      return { success: true, data };
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error && error.name === "AbortError") {
        return { success: false, error: `Request timeout after ${this.timeout}ms` };
      }
      return { success: false, error: String(error) };
    }
  }

  /**
   * List all background agents
   */
  async listAgents(): Promise<FleetResult<Agent[]>> {
    return this.request<Agent[]>("/background-agents");
  }

  /**
   * Get status of a specific agent
   */
  async getAgentStatus(agentId: string): Promise<FleetResult<Agent>> {
    return this.request<Agent>(`/background-agents/${agentId}`);
  }

  /**
   * Get conversation history for an agent
   */
  async getAgentConversation(agentId: string): Promise<FleetResult<Conversation>> {
    return this.request<Conversation>(`/background-agents/${agentId}/conversation`);
  }

  /**
   * Launch a new background agent
   */
  async launchAgent(options: {
    prompt: { text: string };
    source: { repository: string; ref?: string };
  }): Promise<FleetResult<Agent>> {
    return this.request<Agent>("/background-agents", "POST", options);
  }

  /**
   * Send a follow-up message to an agent
   */
  async addFollowup(agentId: string, prompt: { text: string }): Promise<FleetResult<void>> {
    return this.request<void>(`/background-agents/${agentId}/followup`, "POST", { prompt });
  }

  /**
   * List available repositories
   */
  async listRepositories(): Promise<FleetResult<Repository[]>> {
    return this.request<Repository[]>("/repositories");
  }
}
