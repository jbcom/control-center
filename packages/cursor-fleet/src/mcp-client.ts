/**
 * MCP Client - Handles communication with cursor-background-agent-mcp-server
 * 
 * Supports two modes:
 * 1. HTTP proxy mode (when mcp-proxy is running)
 * 2. Direct stdio mode (spawns npx cursor-background-agent-mcp-server)
 */

import { spawn, ChildProcess } from "node:child_process";
import type { FleetConfig, FleetResult, MCPRequest, MCPResponse } from "./types.js";

const DEFAULT_PROXY_URL = "http://localhost:3011";
const DEFAULT_TIMEOUT = 60000; // Increased to 60s for conversation retrieval
const MCP_PROTOCOL_VERSION = "2024-11-05";

export class MCPClient {
  private apiKey: string;
  private proxyUrl: string;
  private timeout: number;
  private proxyAvailable: boolean | null = null;
  private child: ChildProcess | null = null;
  private initialized: boolean = false;
  private pendingRequests: Map<number, {
    resolve: (value: FleetResult<unknown>) => void;
    timeout: NodeJS.Timeout;
  }> = new Map();
  private nextId: number = 1;
  private buffer: string = "";

  constructor(config: FleetConfig = {}) {
    this.apiKey = config.apiKey ?? process.env.CURSOR_API_KEY ?? "";
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
   * Ensure the MCP server child process is running and initialized
   */
  private async ensureChild(): Promise<void> {
    if (this.child && this.initialized) {
      return;
    }

    return new Promise((resolve, reject) => {
      this.child = spawn("npx", ["-y", "cursor-background-agent-mcp-server"], {
        stdio: ["pipe", "pipe", "pipe"],
        env: { ...process.env, CURSOR_API_KEY: this.apiKey },
      });

      let stderr = "";

      this.child.stderr?.on("data", (data) => {
        stderr += data.toString();
      });

      this.child.stdout?.on("data", (data) => {
        this.buffer += data.toString();
        this.processBuffer();
      });

      this.child.on("close", (code) => {
        if (!this.initialized) {
          reject(new Error(`MCP server exited with code ${code}: ${stderr}`));
        }
        this.child = null;
        this.initialized = false;
        // Reject all pending requests
        for (const [id, { resolve, timeout }] of this.pendingRequests) {
          clearTimeout(timeout);
          resolve({ success: false, error: "MCP server closed" });
        }
        this.pendingRequests.clear();
      });

      this.child.on("error", (error) => {
        reject(error);
      });

      // Send initialize message
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

      // Wait for initialize response
      const initTimeout = setTimeout(() => {
        reject(new Error("Initialize timeout"));
      }, 10000);

      const checkInit = () => {
        // Look for id:0 response in buffer
        const lines = this.buffer.split("\n");
        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const msg = JSON.parse(line) as MCPResponse;
            if (msg.id === 0 && msg.result) {
              clearTimeout(initTimeout);
              this.initialized = true;
              // Remove processed lines from buffer
              const idx = this.buffer.indexOf(line);
              if (idx !== -1) {
                this.buffer = this.buffer.slice(idx + line.length + 1);
              }
              resolve();
              return;
            }
          } catch {
            // Not valid JSON, skip
          }
        }
        // Check again after a delay
        setTimeout(checkInit, 100);
      };

      this.child.stdin?.write(JSON.stringify(initMessage) + "\n");
      checkInit();
    });
  }

  /**
   * Process buffered data looking for complete JSON messages
   */
  private processBuffer(): void {
    const lines = this.buffer.split("\n");
    const unprocessed: string[] = [];

    for (const line of lines) {
      if (!line.trim()) continue;
      try {
        const msg = JSON.parse(line) as MCPResponse;
        if (typeof msg.id === "number" && msg.id > 0) {
          const pending = this.pendingRequests.get(msg.id);
          if (pending) {
            clearTimeout(pending.timeout);
            this.pendingRequests.delete(msg.id);
            pending.resolve(this.parseResponse(msg));
          }
        }
      } catch {
        // Incomplete JSON, keep for later
        unprocessed.push(line);
      }
    }

    this.buffer = unprocessed.join("\n");
  }

  /**
   * Call MCP tool directly via stdio with persistent connection
   */
  private async callDirect<T>(tool: string, args: Record<string, unknown>): Promise<FleetResult<T>> {
    try {
      await this.ensureChild();
    } catch (error) {
      return { success: false, error: `Failed to initialize MCP server: ${error}` };
    }

    return new Promise((resolve) => {
      const id = this.nextId++;
      
      const timeout = setTimeout(() => {
        this.pendingRequests.delete(id);
        resolve({ success: false, error: `MCP call timed out after ${this.timeout}ms` });
      }, this.timeout);

      this.pendingRequests.set(id, { 
        resolve: resolve as (value: FleetResult<unknown>) => void, 
        timeout 
      });

      const request: MCPRequest = {
        jsonrpc: "2.0",
        id,
        method: "tools/call",
        params: { name: tool, arguments: args },
      };

      this.child?.stdin?.write(JSON.stringify(request) + "\n");
    });
  }

  /**
   * Close the MCP server connection
   */
  close(): void {
    if (this.child) {
      this.child.stdin?.end();
      this.child.kill();
      this.child = null;
      this.initialized = false;
    }
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
