/**
 * Unified MCP Client Integration
 * 
 * Connects to MCP servers for a complete AI-powered development environment:
 * - Cursor Agent MCP: Manage background agents, spawn tasks, get conversations
 * - GitHub MCP: PR management, issues, code search, repository operations
 * - Context7 MCP: Up-to-date library documentation
 */

import { experimental_createMCPClient as createMCPClient } from "@ai-sdk/mcp";
import { Experimental_StdioMCPTransport as StdioMCPTransport } from "@ai-sdk/mcp/mcp-stdio";
import type { ToolSet } from "ai";
import env from "env-var";

// ─────────────────────────────────────────────────────────────────
// Environment Configuration
// ─────────────────────────────────────────────────────────────────

/** 
 * MCP environment variable definitions.
 * Each entry defines the canonical name and its fallback sources.
 */
export const MCP_ENV_VARS = {
  cursor: {
    name: "CURSOR_API_KEY",
    sources: ["COPILOT_MCP_CURSOR_API_KEY", "CURSOR_API_KEY"],
  },
  github: {
    name: "GITHUB_TOKEN",
    sources: ["COPILOT_MCP_GITHUB_TOKEN", "GITHUB_JBCOM_TOKEN", "GITHUB_TOKEN"],
  },
  context7: {
    name: "CONTEXT7_API_KEY",
    sources: ["COPILOT_MCP_CONTEXT7_API_KEY", "CONTEXT7_API_KEY"],
    optional: true,
  },
} as const;

/** Normalized environment with fallbacks resolved */
const mcpEnv = env.from({
  ...process.env,
  CURSOR_API_KEY: MCP_ENV_VARS.cursor.sources.map(k => process.env[k]).find(Boolean),
  GITHUB_TOKEN: MCP_ENV_VARS.github.sources.map(k => process.env[k]).find(Boolean),
  CONTEXT7_API_KEY: MCP_ENV_VARS.context7.sources.map(k => process.env[k]).find(Boolean),
});

/** Resolved MCP credentials - use this throughout the codebase */
export const mcpCredentials = {
  cursorApiKey: mcpEnv.get("CURSOR_API_KEY").asString(),
  githubToken: mcpEnv.get("GITHUB_TOKEN").asString(),
  context7ApiKey: mcpEnv.get("CONTEXT7_API_KEY").asString(),
};

export interface MCPClientConfig {
  /** Cursor Background Agent MCP configuration */
  cursor?: {
    /** Cursor API key (defaults to CURSOR_API_KEY env) */
    apiKey?: string;
    /** Use stdio (local) or HTTP proxy mode */
    mode?: "stdio" | "proxy";
    /** Proxy URL if using proxy mode */
    proxyUrl?: string;
  };
  /** GitHub MCP configuration */
  github?: {
    /** GitHub Personal Access Token (defaults to GITHUB_TOKEN env) */
    token?: string;
    /** Use remote server (api.githubcopilot.com) or local */
    remote?: boolean;
    /** Custom host for GitHub Enterprise */
    host?: string;
  };
  /** Context7 MCP configuration */
  context7?: {
    /** Context7 API key for higher rate limits */
    apiKey?: string;
  };
}

export interface MCPClients {
  cursor?: Awaited<ReturnType<typeof createMCPClient>>;
  github?: Awaited<ReturnType<typeof createMCPClient>>;
  context7?: Awaited<ReturnType<typeof createMCPClient>>;
}

/**
 * Initialize all MCP clients
 */
export async function initializeMCPClients(
  config: MCPClientConfig = {}
): Promise<MCPClients> {
  const clients: MCPClients = {};

  // ─────────────────────────────────────────────────────────────────
  // 1. Cursor Background Agent MCP
  // ─────────────────────────────────────────────────────────────────
  const cursorApiKey = config.cursor?.apiKey || mcpCredentials.cursorApiKey;
  
  if (cursorApiKey) {
    try {
      const mode = config.cursor?.mode ?? "stdio";
      
      if (mode === "proxy") {
        // HTTP proxy mode (when mcp-proxy is running)
        const proxyUrl = config.cursor?.proxyUrl || process.env.MCP_PROXY_CURSOR_AGENTS_URL || "http://localhost:3011";
        clients.cursor = await createMCPClient({
          transport: {
            type: "http",
            url: `${proxyUrl}/mcp`,
          },
          name: "cursor-agents-mcp",
        });
      } else {
        // Direct stdio mode - spawns cursor-background-agent-mcp-server
        clients.cursor = await createMCPClient({
          transport: new StdioMCPTransport({
            command: "npx",
            args: ["-y", "cursor-background-agent-mcp-server"],
            env: {
              ...process.env,
              CURSOR_API_KEY: cursorApiKey,
            },
          }),
          name: "cursor-agents-mcp",
        });
      }
      
      console.log("✅ Cursor Agent MCP client initialized");
    } catch (error) {
      console.warn("⚠️ Failed to initialize Cursor MCP client:", error instanceof Error ? error.message : error);
    }
  }

  // ─────────────────────────────────────────────────────────────────
  // 2. GitHub MCP Server (Official)
  // ─────────────────────────────────────────────────────────────────
  // Check for GitHub token: config, COPILOT_MCP_GITHUB_TOKEN (testing), GITHUB_JBCOM_TOKEN, GITHUB_TOKEN
  const githubToken = config.github?.token || mcpCredentials.githubToken;
  
  if (githubToken || config.github !== undefined) {
    try {
      const useRemote = config.github?.remote !== false;
      
      if (useRemote) {
        // Remote GitHub MCP server (hosted by GitHub)
        const baseUrl = config.github?.host 
          ? `https://copilot-api.${config.github.host}/mcp`
          : "https://api.githubcopilot.com/mcp/";
          
        clients.github = await createMCPClient({
          transport: {
            type: "http",
            url: baseUrl,
            headers: githubToken ? {
              Authorization: `Bearer ${githubToken}`,
            } : undefined,
          },
          name: "github-mcp",
        });
      } else {
        // Local GitHub MCP server via Docker
        clients.github = await createMCPClient({
          transport: new StdioMCPTransport({
            command: "docker",
            args: [
              "run", "-i", "--rm",
              "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
              "ghcr.io/github/github-mcp-server",
            ],
            env: {
              // Create clean env object with defined values only
              ...Object.fromEntries(
                Object.entries(process.env).filter((entry): entry is [string, string] => entry[1] !== undefined)
              ),
              GITHUB_PERSONAL_ACCESS_TOKEN: githubToken ?? "",
            },
          }),
          name: "github-mcp",
        });
      }
      
      console.log("✅ GitHub MCP client initialized");
    } catch (error) {
      console.warn("⚠️ Failed to initialize GitHub MCP client:", error instanceof Error ? error.message : error);
    }
  }

  // ─────────────────────────────────────────────────────────────────
  // 3. Context7 MCP Server (Documentation)
  // ─────────────────────────────────────────────────────────────────
  const context7ApiKey = config.context7?.apiKey || mcpCredentials.context7ApiKey;
  
  if (context7ApiKey || config.context7 !== undefined) {
    try {
      clients.context7 = await createMCPClient({
        transport: {
          type: "http",
          url: "https://mcp.context7.com/mcp",
          headers: context7ApiKey ? {
            "CONTEXT7_API_KEY": context7ApiKey,
          } : undefined,
        },
        name: "context7-mcp",
      });
      
      console.log("✅ Context7 MCP client initialized");
    } catch (error) {
      console.warn("⚠️ Failed to initialize Context7 MCP client:", error instanceof Error ? error.message : error);
    }
  }

  return clients;
}

/**
 * Get all tools from initialized MCP clients
 * Returns a unified ToolSet that can be passed to Vercel AI SDK
 */
export async function getMCPTools(clients: MCPClients): Promise<ToolSet> {
  const allTools: ToolSet = {};
  const toolCounts: Record<string, number> = {};

  // Get Cursor Agent tools
  if (clients.cursor) {
    try {
      const cursorTools = await clients.cursor.tools();
      Object.assign(allTools, cursorTools);
      toolCounts.cursor = Object.keys(cursorTools).length;
    } catch (error) {
      console.warn("⚠️ Failed to get Cursor MCP tools:", error instanceof Error ? error.message : error);
    }
  }

  // Get GitHub tools
  if (clients.github) {
    try {
      const githubTools = await clients.github.tools();
      Object.assign(allTools, githubTools);
      toolCounts.github = Object.keys(githubTools).length;
    } catch (error) {
      console.warn("⚠️ Failed to get GitHub MCP tools:", error instanceof Error ? error.message : error);
    }
  }

  // Get Context7 tools
  if (clients.context7) {
    try {
      const context7Tools = await clients.context7.tools();
      Object.assign(allTools, context7Tools);
      toolCounts.context7 = Object.keys(context7Tools).length;
    } catch (error) {
      console.warn("⚠️ Failed to get Context7 MCP tools:", error instanceof Error ? error.message : error);
    }
  }

  // Log summary
  const total = Object.values(toolCounts).reduce((a, b) => a + b, 0);
  console.log(`📦 Loaded ${total} MCP tools:`, toolCounts);

  return allTools;
}

/**
 * Close all MCP clients gracefully
 */
export async function closeMCPClients(clients: MCPClients): Promise<void> {
  const closePromises: Promise<void>[] = [];

  if (clients.cursor) closePromises.push(clients.cursor.close());
  if (clients.github) closePromises.push(clients.github.close());
  if (clients.context7) closePromises.push(clients.context7.close());

  await Promise.allSettled(closePromises);
  console.log("🔌 All MCP clients closed");
}

/**
 * List available prompts from MCP servers that support them
 */
export async function listMCPPrompts(clients: MCPClients): Promise<{
  cursor?: unknown[];
  github?: unknown[];
  context7?: unknown[];
}> {
  const prompts: Record<string, unknown[]> = {};

  for (const [name, client] of Object.entries(clients)) {
    if (client) {
      try {
        const result = await client.listPrompts();
        if (result.prompts?.length) {
          prompts[name] = result.prompts;
        }
      } catch {
        // Prompts not supported by this server
      }
    }
  }

  return prompts;
}

/**
 * List available resources from MCP servers
 */
export async function listMCPResources(clients: MCPClients): Promise<{
  cursor?: unknown[];
  github?: unknown[];
  context7?: unknown[];
}> {
  const resources: Record<string, unknown[]> = {};

  for (const [name, client] of Object.entries(clients)) {
    if (client) {
      try {
        const result = await client.listResources();
        if (result.resources?.length) {
          resources[name] = result.resources;
        }
      } catch {
        // Resources not supported by this server
      }
    }
  }

  return resources;
}
