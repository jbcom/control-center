/**
 * MCP Client - Handles communication with cursor-background-agent-mcp-server
 * 
 * Supports two modes:
 * 1. HTTP proxy mode (when mcp-proxy is running)
 * 2. Direct stdio mode (spawns npx cursor-background-agent-mcp-server)
 */

import { spawn } from "node:child_process";
import type { FleetConfig, FleetResult, MCPRequest, MCPResponse } from "./types.js";

const DEFAULT_PROXY_URL = "http://localhost:3011";
const DEFAULT_TIMEOUT = 30000;
const MCP_PROTOCOL_VERSION = "2024-11-05";

export class MCPClient {
  private apiKey: string;
  private proxyUrl: string;
  private timeout: number;
  private proxyAvailable: boolean | null = null;

  constructor(config: FleetConfig = {}) {
    // Prioritize COPILOT_MCP_CURSOR_API_KEY for testing, then fall back to CURSOR_API_KEY
    this.apiKey = config.apiKey ?? process.env.COPILOT_MCP_CURSOR_API_KEY ?? process.env.CURSOR_API_KEY ?? "";
    this.proxyUrl = config.proxyUrl ?? process.env.MCP_PROXY_CURSOR_AGENTS_URL ?? DEFAULT_PROXY_URL;
    this.timeout = config.timeout ?? DEFAULT_TIMEOUT;

    if (!this.apiKey) {
      throw new Error("CURSOR_API_KEY is required. Set it in config or environment.");
    }
  }

  /**
   * Check if MCP proxy is available
   */
  async checkProxy(): Promise<boolean> {
    if (this.proxyAvailable !== null) {
      return this.proxyAvailable;
    }

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2000);
      
      const response = await fetch(`${this.proxyUrl}/mcp`, {
        method: "GET",
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);
      this.proxyAvailable = response.ok;
    } catch {
      this.proxyAvailable = false;
    }

    return this.proxyAvailable;
  }

  /**
   * Call an MCP tool
   */
  async call<T>(tool: string, args: Record<string, unknown> = {}): Promise<FleetResult<T>> {
    const useProxy = await this.checkProxy();
    
    if (useProxy) {
      return this.callViaProxy<T>(tool, args);
    }
    
    return this.callDirect<T>(tool, args);
  }

  /**
   * Call MCP tool via HTTP proxy
   */
  private async callViaProxy<T>(tool: string, args: Record<string, unknown>): Promise<FleetResult<T>> {
    const request: MCPRequest = {
      jsonrpc: "2.0",
      id: 1,
      method: "tools/call",
      params: { name: tool, arguments: args },
    };

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);

      const response = await fetch(`${this.proxyUrl}/mcp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(request),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        return { success: false, error: `HTTP ${response.status}: ${response.statusText}` };
      }

      const result = await response.json() as MCPResponse;
      return this.parseResponse<T>(result);
    } catch (error) {
      return { success: false, error: String(error) };
    }
  }

  /**
   * Call MCP tool directly via stdio
   */
  private async callDirect<T>(tool: string, args: Record<string, unknown>): Promise<FleetResult<T>> {
    return new Promise((resolve) => {
      const initMessage: MCPRequest = {
        jsonrpc: "2.0",
        id: 0,
        method: "initialize",
        params: {
          protocolVersion: MCP_PROTOCOL_VERSION,
          capabilities: {},
          clientInfo: { name: "cursor-fleet", version: "1.0" },
        },
      };

      const callMessage: MCPRequest = {
        jsonrpc: "2.0",
        id: 1,
        method: "tools/call",
        params: { name: tool, arguments: args },
      };

      const child = spawn("npx", ["-y", "cursor-background-agent-mcp-server"], {
        stdio: ["pipe", "pipe", "pipe"],
        env: { ...process.env, CURSOR_API_KEY: this.apiKey },
      });

      let stdout = "";
      let resolved = false;

      const timeout = setTimeout(() => {
        if (!resolved) {
          resolved = true;
          child.kill();
          resolve({ success: false, error: "MCP call timed out" });
        }
      }, this.timeout);

      child.stdout.on("data", (data) => {
        stdout += data.toString();
      });

      child.on("close", () => {
        if (resolved) return;
        clearTimeout(timeout);
        resolved = true;

        // Parse output looking for response to our call (id: 1)
        for (const line of stdout.split("\n")) {
          if (!line.trim()) continue;
          try {
            const msg = JSON.parse(line) as MCPResponse;
            if (msg.id === 1) {
              resolve(this.parseResponse<T>(msg));
              return;
            }
          } catch {
            // Not JSON, skip
          }
        }

        resolve({ success: false, error: "No valid response from MCP server" });
      });

      child.on("error", (error) => {
        if (!resolved) {
          resolved = true;
          clearTimeout(timeout);
          resolve({ success: false, error: String(error) });
        }
      });

      // Send messages with delays for protocol handshake
      child.stdin.write(JSON.stringify(initMessage) + "\n");
      
      setTimeout(() => {
        child.stdin.write(JSON.stringify(callMessage) + "\n");
        
        // Give time for response then close stdin
        setTimeout(() => {
          child.stdin.end();
        }, 5000);
      }, 2000);
    });
  }

  /**
   * Parse MCP response
   */
  private parseResponse<T>(response: MCPResponse): FleetResult<T> {
    if (response.error) {
      return { success: false, error: response.error.message };
    }

    const content = response.result?.content?.[0]?.text;
    if (!content) {
      return { success: false, error: "Empty response from MCP server" };
    }

    try {
      const data = JSON.parse(content) as T;
      return { success: true, data };
    } catch {
      return { success: false, error: `Invalid JSON in response: ${content.slice(0, 200)}` };
    }
  }
}
