/**
 * Core types for Cursor Fleet management
 */

export type AgentStatus = 
  | "RUNNING" 
  | "COMPLETED" 
  | "FINISHED"
  | "FAILED" 
  | "CANCELLED"
  | "PENDING"
  | "EXPIRED"
  | "CREATING";

export interface AgentSource {
  repository: string;
  ref: string;
}

export interface AgentTarget {
  branchName?: string;
  url?: string;
}

export interface Agent {
  id: string;
  name?: string;
  status: AgentStatus;
  source: AgentSource;
  target?: AgentTarget;
  createdAt?: string;
  finishedAt?: string;
  summary?: string;
}

export interface Message {
  type: "user_message" | "assistant_message";
  text: string;
  timestamp?: string;
}

export interface Conversation {
  agentId: string;
  messages: Message[];
}

export interface Repository {
  owner: string;
  name: string;
  url: string;
}

export interface LaunchOptions {
  repository: string;
  ref?: string;
  task: string;
  /** Context about the spawning agent/control center */
  context?: SpawnContext;
}

export interface SpawnContext {
  /** ID of the control manager agent */
  controlManagerId?: string;
  /** Name of the control center (e.g., "FSC Control Center") */
  controlCenter?: string;
  /** Related agent IDs for diamond pattern communication */
  relatedAgents?: string[];
  /** Additional metadata */
  metadata?: Record<string, unknown>;
}

export interface FleetConfig {
  /** Cursor API key (defaults to CURSOR_API_KEY env var) */
  apiKey?: string;
  /** MCP proxy URL if running (defaults to http://localhost:3011) */
  proxyUrl?: string;
  /** Timeout for MCP operations in ms (default: 30000) */
  timeout?: number;
  /** Path to archive conversations */
  archivePath?: string;
}

export interface MCPRequest {
  jsonrpc: "2.0";
  id: number;
  method: string;
  params: Record<string, unknown>;
}

export interface MCPResponse<T = unknown> {
  jsonrpc: "2.0";
  id: number;
  result?: {
    content: Array<{ type: string; text: string }>;
  };
  error?: {
    code: number;
    message: string;
  };
}

export interface FleetResult<T> {
  success: boolean;
  data?: T;
  error?: string;
}
