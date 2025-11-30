/**
 * AI Triage - AI-powered PR and issue triage with MCP integration
 * 
 * This package provides:
 * - UnifiedAgent: Complete AI agent with Anthropic tools + MCP
 * - PRTriageAgent: Specialized PR analysis and resolution
 * - MCP Clients: Integration with Cursor, GitHub, and Context7 MCP servers
 * 
 * @example
 * ```typescript
 * import { PRTriageAgent, runTask } from "@jbcom/ai-triage";
 * 
 * // Quick task execution
 * const result = await runTask("Fix the linting errors in src/utils.ts");
 * 
 * // PR triage workflow
 * const agent = new PRTriageAgent({ repository: "owner/repo" });
 * const analysis = await agent.analyze(123);
 * await agent.close();
 * ```
 */

// Unified Agent
export { 
  UnifiedAgent, 
  runTask,
  type UnifiedAgentConfig,
  type AgentResult,
  type AgentStep,
} from "./unified-agent.js";

// PR Triage Agent
export {
  PRTriageAgent,
  triagePR,
  type PRTriageConfig,
  type PRAnalysis,
  type FeedbackItem,
} from "./pr-triage-agent.js";

// MCP Clients
export {
  initializeMCPClients,
  getMCPTools,
  closeMCPClients,
  listMCPPrompts,
  listMCPResources,
  type MCPClientConfig,
  type MCPClients,
} from "./mcp-clients.js";

// Code Agent (Anthropic tools only)
export {
  CodeAgent,
  type CodeAgentConfig,
} from "./code-agent.js";

// Legacy exports for backwards compatibility
export * from "./types.js";
export * from "./github.js";
export * from "./analyzer.js";
export * from "./resolver.js";
export * from "./triage.js";
