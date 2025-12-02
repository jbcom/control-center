/**
 * Fleet management module for agentic-control
 * 
 * Provides Cursor Background Agent fleet management with:
 * - Agent lifecycle management (list, spawn, monitor)
 * - Communication (followup, broadcast)
 * - Coordination patterns (diamond, bidirectional)
 * - Token-aware GitHub integration
 * - Retry logic for transient failures
 * - Actionable error messages
 */

export { Fleet, type FleetConfig, type CoordinationConfig, type SpawnContext, type SpawnResult } from "./fleet.js";
export { CursorAPI, type CursorAPIOptions, type SpawnErrorCategory } from "./cursor-api.js";
