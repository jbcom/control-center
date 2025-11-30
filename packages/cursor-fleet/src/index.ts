/**
 * @jbcom/cursor-fleet
 * 
 * Unified Cursor Background Agent fleet management for control centers.
 * 
 * @example
 * ```typescript
 * import { Fleet } from "@jbcom/cursor-fleet";
 * 
 * const fleet = new Fleet();
 * 
 * // List running agents
 * const running = await fleet.running();
 * 
 * // Spawn a new agent
 * const agent = await fleet.spawn({
 *   repository: "https://github.com/org/repo",
 *   task: "Fix the bug in auth module",
 *   context: {
 *     controlCenter: "FSC Control Center",
 *     controlManagerId: "bc-xxx",
 *   },
 * });
 * 
 * // Send follow-up
 * await fleet.followup(agent.data.id, "Also check the tests");
 * 
 * // Diamond pattern orchestration
 * const diamond = await fleet.createDiamond({
 *   targetRepos: [
 *     { repository: "https://github.com/org/repo1", task: "Update deps" },
 *     { repository: "https://github.com/org/repo2", task: "Update deps" },
 *   ],
 *   counterparty: {
 *     repository: "https://github.com/jbcom/jbcom-control-center",
 *     task: "Coordinate package updates",
 *   },
 *   controlCenter: "FSC Control Center",
 * });
 * ```
 */

export { Fleet } from "./fleet.js";
export { MCPClient } from "./mcp-client.js";
export { CursorAPI, type CursorAPIOptions } from "./cursor-api.js";
export { 
  splitConversation, 
  quickSplit, 
  type SplitOptions, 
  type SplitResult 
} from "./conversation-splitter.js";
export {
  AIAnalyzer,
  analyzeAndReport,
  type TaskAnalysis,
  type CodeReview,
  type AnalyzerOptions,
} from "./ai-analyzer.js";
export type {
  Agent,
  AgentStatus,
  AgentSource,
  AgentTarget,
  Conversation,
  Message,
  Repository,
  LaunchOptions,
  SpawnContext,
  FleetConfig,
  FleetResult,
} from "./types.js";
