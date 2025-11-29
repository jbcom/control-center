/**
 * Fleet - High-level API for Cursor Background Agent management
 * 
 * Provides a clean interface for:
 * - Listing and monitoring agents
 * - Spawning new agents with context
 * - Sending follow-up messages
 * - Archiving conversations
 * - Diamond pattern orchestration
 */

import { writeFile, mkdir } from "node:fs/promises";
import { dirname, join } from "node:path";
import { MCPClient } from "./mcp-client.js";
import type {
  Agent,
  AgentStatus,
  Conversation,
  FleetConfig,
  FleetResult,
  LaunchOptions,
  Repository,
  SpawnContext,
} from "./types.js";

export class Fleet {
  private client: MCPClient;
  private archivePath: string;

  constructor(config: FleetConfig = {}) {
    this.client = new MCPClient(config);
    this.archivePath = config.archivePath ?? "./memory-bank/recovery";
  }

  // ============================================
  // Agent Discovery
  // ============================================

  /**
   * List all agents
   */
  async list(): Promise<FleetResult<Agent[]>> {
    const result = await this.client.call<{ agents: Agent[] }>("listAgents", {});
    if (!result.success) return { success: false, error: result.error };
    return { success: true, data: result.data?.agents ?? [] };
  }

  /**
   * List agents filtered by status
   */
  async listByStatus(status: AgentStatus): Promise<FleetResult<Agent[]>> {
    const result = await this.list();
    if (!result.success) return result;
    return { 
      success: true, 
      data: result.data?.filter(a => a.status === status) ?? [] 
    };
  }

  /**
   * Get running agents only
   */
  async running(): Promise<FleetResult<Agent[]>> {
    return this.listByStatus("RUNNING");
  }

  /**
   * Find agent by ID
   */
  async find(agentId: string): Promise<FleetResult<Agent | undefined>> {
    const result = await this.list();
    if (!result.success) return { success: false, error: result.error };
    return { success: true, data: result.data?.find(a => a.id === agentId) };
  }

  /**
   * Get agent status
   */
  async status(agentId: string): Promise<FleetResult<Agent>> {
    return this.client.call<Agent>("getAgentStatus", { agentId });
  }

  // ============================================
  // Agent Spawning
  // ============================================

  /**
   * Spawn a new agent
   */
  async spawn(options: LaunchOptions): Promise<FleetResult<Agent>> {
    const task = this.buildTaskWithContext(options.task, options.context);

    const result = await this.client.call<Agent>("launchAgent", {
      prompt: { text: task },
      source: {
        repository: options.repository,
        ref: options.ref ?? "main",
      },
    });

    return result;
  }

  /**
   * Build task string with coordination context
   */
  private buildTaskWithContext(task: string, context?: SpawnContext): string {
    if (!context) return task;

    const lines = [task, "", "--- COORDINATION CONTEXT ---"];
    
    if (context.controlManagerId) {
      lines.push(`Control Manager Agent: ${context.controlManagerId}`);
    }
    if (context.controlCenter) {
      lines.push(`Control Center: ${context.controlCenter}`);
    }
    if (context.relatedAgents?.length) {
      lines.push(`Related Agents: ${context.relatedAgents.join(", ")}`);
    }
    if (context.metadata) {
      lines.push(`Metadata: ${JSON.stringify(context.metadata)}`);
    }
    lines.push("Report progress via PR comments and addFollowup.");
    lines.push("--- END CONTEXT ---");

    return lines.join("\n");
  }

  // ============================================
  // Agent Communication
  // ============================================

  /**
   * Send a follow-up message to an agent
   */
  async followup(agentId: string, message: string): Promise<FleetResult<void>> {
    const result = await this.client.call<void>("addFollowup", {
      agentId,
      prompt: { text: message },
    });
    return result;
  }

  /**
   * Broadcast message to multiple agents
   */
  async broadcast(agentIds: string[], message: string): Promise<Map<string, FleetResult<void>>> {
    const results = new Map<string, FleetResult<void>>();
    
    await Promise.all(
      agentIds.map(async (id) => {
        results.set(id, await this.followup(id, message));
      })
    );

    return results;
  }

  // ============================================
  // Conversations
  // ============================================

  /**
   * Get agent conversation
   */
  async conversation(agentId: string): Promise<FleetResult<Conversation>> {
    return this.client.call<Conversation>("getAgentConversation", { agentId });
  }

  /**
   * Archive agent conversation to disk
   */
  async archive(agentId: string, outputPath?: string): Promise<FleetResult<string>> {
    const conv = await this.conversation(agentId);
    if (!conv.success) return { success: false, error: conv.error };

    const path = outputPath ?? join(this.archivePath, `conversation-${agentId}.json`);
    
    try {
      await mkdir(dirname(path), { recursive: true });
      await writeFile(path, JSON.stringify(conv.data, null, 2));
      return { success: true, data: path };
    } catch (error) {
      return { success: false, error: String(error) };
    }
  }

  // ============================================
  // Repositories
  // ============================================

  /**
   * List available repositories
   */
  async repositories(): Promise<FleetResult<Repository[]>> {
    const result = await this.client.call<{ repositories: Repository[] }>("listRepositories", {});
    if (!result.success) return { success: false, error: result.error };
    return { success: true, data: result.data?.repositories ?? [] };
  }

  // ============================================
  // Diamond Pattern Orchestration
  // ============================================

  /**
   * Create a diamond pattern orchestration
   * 
   * Control Manager spawns agents in target repos, then spawns counterparty
   * agent which can communicate back to the target agents.
   */
  async createDiamond(options: {
    targetRepos: Array<{ repository: string; task: string; ref?: string }>;
    counterparty: { repository: string; task: string; ref?: string };
    controlCenter: string;
  }): Promise<FleetResult<{
    targetAgents: Agent[];
    counterpartyAgent: Agent;
  }>> {
    // Get my agent ID for context
    const runningResult = await this.running();
    const myId = runningResult.data?.[0]?.id ?? "control-manager";

    // Spawn target agents
    const targetAgents: Agent[] = [];
    for (const target of options.targetRepos) {
      const result = await this.spawn({
        ...target,
        context: {
          controlManagerId: myId,
          controlCenter: options.controlCenter,
        },
      });
      if (result.success && result.data) {
        targetAgents.push(result.data);
      }
    }

    // Spawn counterparty with knowledge of target agents
    const counterpartyResult = await this.spawn({
      ...options.counterparty,
      context: {
        controlManagerId: myId,
        controlCenter: options.controlCenter,
        relatedAgents: targetAgents.map(a => a.id),
        metadata: {
          pattern: "diamond",
          targetRepos: options.targetRepos.map(t => t.repository),
        },
      },
    });

    if (!counterpartyResult.success || !counterpartyResult.data) {
      return { 
        success: false, 
        error: counterpartyResult.error ?? "Failed to spawn counterparty" 
      };
    }

    // Notify target agents about counterparty
    for (const agent of targetAgents) {
      await this.followup(agent.id, 
        `Counterparty agent spawned: ${counterpartyResult.data.id}\n` +
        `You may receive direct communication from this agent for coordination.`
      );
    }

    return {
      success: true,
      data: {
        targetAgents,
        counterpartyAgent: counterpartyResult.data,
      },
    };
  }

  // ============================================
  // Fleet Monitoring
  // ============================================

  /**
   * Get fleet summary
   */
  async summary(): Promise<FleetResult<{
    total: number;
    running: number;
    completed: number;
    failed: number;
    agents: Agent[];
  }>> {
    const result = await this.list();
    if (!result.success) return { success: false, error: result.error };

    const agents = result.data ?? [];
    return {
      success: true,
      data: {
        total: agents.length,
        running: agents.filter(a => a.status === "RUNNING").length,
        completed: agents.filter(a => a.status === "COMPLETED").length,
        failed: agents.filter(a => a.status === "FAILED").length,
        agents,
      },
    };
  }

  /**
   * Wait for agent to complete
   */
  async waitFor(agentId: string, options?: {
    timeout?: number;
    pollInterval?: number;
  }): Promise<FleetResult<Agent>> {
    const timeout = options?.timeout ?? 300000; // 5 minutes default
    const pollInterval = options?.pollInterval ?? 10000; // 10 seconds
    const start = Date.now();

    while (Date.now() - start < timeout) {
      const result = await this.status(agentId);
      if (!result.success) return result;

      if (result.data?.status !== "RUNNING") {
        return result;
      }

      await new Promise(r => setTimeout(r, pollInterval));
    }

    return { success: false, error: `Timeout waiting for agent ${agentId}` };
  }
}
