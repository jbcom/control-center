/**
 * Fleet - High-level API for Cursor Background Agent management
 *
 * Provides a clean interface for:
 * - Listing and monitoring agents
 * - Spawning new agents with context and model specification
 * - Sending follow-up messages
 * - Archiving conversations
 * - Diamond pattern orchestration
 * - Token-aware GitHub coordination
 */
import { type CursorAPIOptions } from "./cursor-api.js";
import type { Agent, AgentStatus, Conversation, Repository, Result, SpawnOptions, DiamondConfig, PRComment } from "../core/types.js";
export interface FleetConfig extends CursorAPIOptions {
    /** Path to archive conversations */
    archivePath?: string;
}
export interface CoordinationConfig {
    /** PR number for coordination channel */
    coordinationPr: number;
    /** Repository in owner/repo format */
    repo: string;
    /** Outbound poll interval (ms) - check agents */
    outboundInterval?: number;
    /** Inbound poll interval (ms) - check PR comments */
    inboundInterval?: number;
    /** Agent IDs to monitor */
    agentIds?: string[];
}
export interface SpawnContext {
    controlManagerId?: string;
    controlCenter?: string;
    relatedAgents?: string[];
    metadata?: Record<string, unknown>;
}
export declare class Fleet {
    private api;
    private archivePath;
    private useDirectApi;
    constructor(config?: FleetConfig);
    /**
     * Check if direct API is available
     */
    isApiAvailable(): boolean;
    /**
     * List all agents
     */
    list(): Promise<Result<Agent[]>>;
    /**
     * List agents filtered by status
     */
    listByStatus(status: AgentStatus): Promise<Result<Agent[]>>;
    /**
     * Get running agents only
     */
    running(): Promise<Result<Agent[]>>;
    /**
     * Find agent by ID
     */
    find(agentId: string): Promise<Result<Agent | undefined>>;
    /**
     * Get agent status
     */
    status(agentId: string): Promise<Result<Agent>>;
    /**
     * Spawn a new agent with model specification
     *
     * @param options - Spawn options including repository, task, ref, context, and model
     */
    spawn(options: SpawnOptions & {
        context?: SpawnContext;
    }): Promise<Result<Agent>>;
    /**
     * Build task string with coordination context
     */
    private buildTaskWithContext;
    /**
     * Send a follow-up message to an agent
     */
    followup(agentId: string, message: string): Promise<Result<void>>;
    /**
     * Broadcast message to multiple agents
     */
    broadcast(agentIds: string[], message: string): Promise<Map<string, Result<void>>>;
    /**
     * Get agent conversation
     */
    conversation(agentId: string): Promise<Result<Conversation>>;
    /**
     * Archive agent conversation to disk
     */
    archive(agentId: string, outputPath?: string): Promise<Result<string>>;
    /**
     * List available repositories
     */
    repositories(): Promise<Result<Repository[]>>;
    /**
     * Create a diamond pattern orchestration
     */
    createDiamond(config: DiamondConfig): Promise<Result<{
        targetAgents: Agent[];
        counterpartyAgent: Agent;
    }>>;
    /**
     * Get fleet summary
     */
    summary(): Promise<Result<{
        total: number;
        running: number;
        completed: number;
        failed: number;
        agents: Agent[];
    }>>;
    /**
     * Wait for agent to complete
     */
    waitFor(agentId: string, options?: {
        timeout?: number;
        pollInterval?: number;
    }): Promise<Result<Agent>>;
    /**
     * Monitor specific agents until all complete
     */
    monitorAgents(agentIds: string[], options?: {
        pollInterval?: number;
        onProgress?: (status: Map<string, AgentStatus>) => void;
    }): Promise<Map<string, Agent>>;
    /**
     * Run bidirectional coordination loop with intelligent token switching
     */
    coordinate(config: CoordinationConfig): Promise<void>;
    private outboundLoop;
    private inboundLoop;
    private processCoordinationComment;
    /**
     * Fetch comments from a GitHub PR using appropriate token for the repo
     */
    fetchPRComments(repo: string, prNumber: number): PRComment[];
    /**
     * Post a comment to a GitHub PR
     * ALWAYS uses PR review token for consistent identity
     */
    postPRComment(repo: string, prNumber: number, body: string): void;
}
//# sourceMappingURL=fleet.d.ts.map