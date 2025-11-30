/**
 * MCP Client Integration
 * 
 * Connects to MCP servers for enhanced AI capabilities:
 * - GitHub MCP: PR management, issues, code search, repository operations
 * - Context7 MCP: Up-to-date library documentation
 */

import { experimental_createMCPClient as createMCPClient } from "@ai-sdk/mcp";
import type { ToolSet } from "ai";

export interface MCPClientConfig {
  github?: {
    /** GitHub Personal Access Token or use OAuth */
    token?: string;
    /** Use remote server (api.githubcopilot.com) or local */
    remote?: boolean;
    /** Custom host for GitHub Enterprise */
    host?: string;
  };
  context7?: {
    /** Context7 API key for higher rate limits */
    apiKey?: string;
  };
}

export interface MCPClients {
  github?: Awaited<ReturnType<typeof createMCPClient>>;
  context7?: Awaited<ReturnType<typeof createMCPClient>>;
}

/**
 * Initialize MCP clients for GitHub and Context7
 */
export async function initializeMCPClients(
  config: MCPClientConfig = {}
): Promise<MCPClients> {
  const clients: MCPClients = {};

  // Initialize GitHub MCP client
  if (config.github !== undefined || process.env.GITHUB_TOKEN || process.env.GITHUB_JBCOM_TOKEN) {
    const githubToken = config.github?.token || process.env.GITHUB_JBCOM_TOKEN || process.env.GITHUB_TOKEN;
    
    try {
      // Use remote GitHub MCP server (recommended)
      const useRemote = config.github?.remote !== false;
      
      if (useRemote) {
        clients.github = await createMCPClient({
          transport: {
            type: "http",
            url: config.github?.host 
              ? `https://copilot-api.${config.github.host}/mcp`
              : "https://api.githubcopilot.com/mcp/",
            headers: githubToken ? {
              Authorization: `Bearer ${githubToken}`,
            } : undefined,
          },
          name: "github-mcp",
        });
      }
      
      console.log("✅ GitHub MCP client initialized");
    } catch (error) {
      console.warn("⚠️ Failed to initialize GitHub MCP client:", error instanceof Error ? error.message : error);
    }
  }

  // Initialize Context7 MCP client
  if (config.context7 !== undefined || process.env.CONTEXT7_API_KEY) {
    const context7ApiKey = config.context7?.apiKey || process.env.CONTEXT7_API_KEY;
    
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
 * Get tools from all initialized MCP clients
 */
export async function getMCPTools(clients: MCPClients): Promise<ToolSet> {
  const allTools: ToolSet = {};

  if (clients.github) {
    try {
      const githubTools = await clients.github.tools();
      Object.assign(allTools, githubTools);
      console.log(`📦 Loaded ${Object.keys(githubTools).length} GitHub MCP tools`);
    } catch (error) {
      console.warn("⚠️ Failed to get GitHub MCP tools:", error instanceof Error ? error.message : error);
    }
  }

  if (clients.context7) {
    try {
      const context7Tools = await clients.context7.tools();
      Object.assign(allTools, context7Tools);
      console.log(`📦 Loaded ${Object.keys(context7Tools).length} Context7 MCP tools`);
    } catch (error) {
      console.warn("⚠️ Failed to get Context7 MCP tools:", error instanceof Error ? error.message : error);
    }
  }

  return allTools;
}

/**
 * Close all MCP clients
 */
export async function closeMCPClients(clients: MCPClients): Promise<void> {
  const closePromises: Promise<void>[] = [];

  if (clients.github) {
    closePromises.push(clients.github.close());
  }

  if (clients.context7) {
    closePromises.push(clients.context7.close());
  }

  await Promise.all(closePromises);
}

/**
 * List available resources from MCP servers
 */
export async function listMCPResources(clients: MCPClients): Promise<{
  github?: unknown[];
  context7?: unknown[];
}> {
  const resources: { github?: unknown[]; context7?: unknown[] } = {};

  if (clients.github) {
    try {
      const result = await clients.github.listResources();
      resources.github = result.resources;
    } catch {
      // Resources not supported or error
    }
  }

  if (clients.context7) {
    try {
      const result = await clients.context7.listResources();
      resources.context7 = result.resources;
    } catch {
      // Resources not supported or error
    }
  }

  return resources;
}
