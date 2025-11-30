/**
 * agentic-control
 *
 * Unified AI agent fleet management, triage, and orchestration toolkit
 * for control centers managing multi-organization GitHub workflows.
 *
 * Features:
 * - Intelligent token switching (auto-selects org-appropriate tokens)
 * - Fleet management (spawn, monitor, coordinate agents)
 * - AI-powered triage (conversation analysis, code review)
 * - Station-to-station handoff (agent continuity)
 * - Token-aware GitHub operations
 *
 * @packageDocumentation
 */
export * from "./core/index.js";
export { Fleet, type FleetConfig, type CoordinationConfig } from "./fleet/index.js";
export { CursorAPI, type CursorAPIOptions } from "./fleet/index.js";
export { AIAnalyzer, type AIAnalyzerOptions } from "./triage/index.js";
export { GitHubClient, ghForRepo, ghForPRReview, cloneRepo } from "./github/index.js";
export { HandoffManager, type TakeoverOptions } from "./handoff/index.js";
export declare const VERSION = "0.1.0";
//# sourceMappingURL=index.d.ts.map