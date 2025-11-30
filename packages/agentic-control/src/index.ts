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

// Core exports
export * from "./core/index.js";

// Fleet management
export { Fleet, type FleetConfig, type CoordinationConfig } from "./fleet/index.js";
export { CursorAPI, type CursorAPIOptions } from "./fleet/index.js";

// AI Triage
export { AIAnalyzer, type AIAnalyzerOptions } from "./triage/index.js";

// GitHub operations
export { GitHubClient, ghForRepo, ghForPRReview, cloneRepo } from "./github/index.js";

// Handoff protocols
export { HandoffManager, type TakeoverOptions } from "./handoff/index.js";

// Version
export const VERSION = "0.1.0";
