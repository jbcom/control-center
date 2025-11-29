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
import { execSync } from "node:child_process";
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
  /** GitHub token (defaults to GITHUB_JBCOM_TOKEN env var) */
  githubToken?: string;
}

export interface PRComment {
  id: string;
  body: string;
  author: string;
  createdAt: string;
}

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

  // ============================================
  // Fleet Monitoring / Watch
  // ============================================

  /**
   * Watch fleet and trigger callbacks on state changes
   */
  async watch(options: {
    pollInterval?: number;
    onAgentFinished?: (agent: Agent) => Promise<void>;
    onAgentFailed?: (agent: Agent) => Promise<void>;
    onAgentStalled?: (agent: Agent, runtime: number) => Promise<void>;
    stallThreshold?: number; // ms before considering agent stalled
    maxIterations?: number; // for non-daemon mode
  }): Promise<void> {
    const pollInterval = options.pollInterval ?? 30000; // 30 seconds
    const stallThreshold = options.stallThreshold ?? 600000; // 10 minutes
    const maxIterations = options.maxIterations ?? Infinity;
    
    const agentStates = new Map<string, { status: AgentStatus; lastSeen: number }>();
    let iterations = 0;

    while (iterations < maxIterations) {
      iterations++;
      
      const result = await this.list();
      if (!result.success) {
        console.error(`Watch error: ${result.error}`);
        await new Promise(r => setTimeout(r, pollInterval));
        continue;
      }

      const now = Date.now();
      
      for (const agent of result.data ?? []) {
        const prev = agentStates.get(agent.id);
        
        // New agent or status changed
        if (!prev || prev.status !== agent.status) {
          agentStates.set(agent.id, { status: agent.status, lastSeen: now });
          
          // Trigger callbacks
          if (agent.status === "FINISHED" && prev?.status === "RUNNING") {
            await options.onAgentFinished?.(agent);
          } else if (agent.status === "FAILED" && prev?.status === "RUNNING") {
            await options.onAgentFailed?.(agent);
          }
        }
        
        // Check for stalled agents
        if (agent.status === "RUNNING" && prev) {
          const runtime = now - new Date(agent.createdAt ?? now).getTime();
          if (runtime > stallThreshold) {
            await options.onAgentStalled?.(agent, runtime);
          }
        }
      }

      await new Promise(r => setTimeout(r, pollInterval));
    }
  }

  /**
   * Monitor specific agents until all complete
   */
  async monitorAgents(agentIds: string[], options?: {
    pollInterval?: number;
    onProgress?: (status: Map<string, AgentStatus>) => void;
  }): Promise<Map<string, Agent>> {
    const pollInterval = options?.pollInterval ?? 15000;
    const results = new Map<string, Agent>();
    const pending = new Set(agentIds);

    while (pending.size > 0) {
      const statusMap = new Map<string, AgentStatus>();
      
      for (const id of pending) {
        const result = await this.status(id);
        if (result.success && result.data) {
          statusMap.set(id, result.data.status);
          
          if (result.data.status !== "RUNNING") {
            results.set(id, result.data);
            pending.delete(id);
          }
        }
      }

      options?.onProgress?.(statusMap);
      
      if (pending.size > 0) {
        await new Promise(r => setTimeout(r, pollInterval));
      }
    }

    return results;
  }

  // ============================================
  // Fleet Coordination (Bidirectional)
  // ============================================

  /**
   * Run bidirectional coordination loop
   * 
   * OUTBOUND: Periodically check sub-agents and send status requests
   * INBOUND: Poll coordination PR for @cursor mentions and process
   */
  async coordinate(config: CoordinationConfig): Promise<void> {
    const outboundInterval = config.outboundInterval ?? 60000;
    const inboundInterval = config.inboundInterval ?? 15000;
    const agentIds = new Set(config.agentIds ?? []);
    const processedCommentIds = new Set<string>();
    const githubToken = config.githubToken ?? process.env.GITHUB_JBCOM_TOKEN;

    console.log("=== Fleet Coordinator Started ===");
    console.log(`Coordination PR: #${config.coordinationPr}`);
    console.log(`Monitoring ${agentIds.size} agents`);
    console.log(`Outbound interval: ${outboundInterval}ms`);
    console.log(`Inbound interval: ${inboundInterval}ms`);
    console.log("");

    // Run both loops concurrently
    await Promise.all([
      this.outboundLoop(config, agentIds, outboundInterval),
      this.inboundLoop(config, agentIds, processedCommentIds, inboundInterval, githubToken),
    ]);
  }

  /**
   * OUTBOUND: Fan-out status checks to sub-agents
   */
  private async outboundLoop(
    config: CoordinationConfig,
    agentIds: Set<string>,
    interval: number
  ): Promise<void> {
    while (true) {
      try {
        const now = new Date();
        console.log(`\n[OUTBOUND ${now.toISOString()}] Checking ${agentIds.size} agents...`);

        for (const agentId of agentIds) {
          const result = await this.status(agentId);

          if (!result.success || !result.data) {
            console.log(`  ⚠️ ${agentId.slice(0, 12)}: Unable to fetch status`);
            continue;
          }

          const agent = result.data;
          const emoji = this.statusEmoji(agent.status);
          console.log(`  ${emoji} ${agentId.slice(0, 12)}: ${agent.status}`);

          // If still running, send periodic check-in request
          if (agent.status === "RUNNING") {
            const message = [
              "📊 STATUS CHECK from Fleet Coordinator",
              "",
              "Report progress by commenting on the coordination PR:",
              `https://github.com/${config.repo}/pull/${config.coordinationPr}`,
              "",
              "Formats:",
              `- @cursor ✅ DONE: ${agentId.slice(0, 12)} [summary]`,
              `- @cursor ⚠️ BLOCKED: ${agentId.slice(0, 12)} [issue]`,
              `- @cursor 📊 STATUS: ${agentId.slice(0, 12)} [update]`,
            ].join("\n");

            await this.followup(agentId, message);
          } else {
            // Agent finished - remove from monitoring
            agentIds.delete(agentId);
          }
        }
      } catch (err) {
        console.error("[OUTBOUND ERROR]", err);
      }

      await new Promise(r => setTimeout(r, interval));
    }
  }

  /**
   * INBOUND: Poll coordination PR for new comments
   */
  private async inboundLoop(
    config: CoordinationConfig,
    agentIds: Set<string>,
    processedIds: Set<string>,
    interval: number,
    githubToken?: string
  ): Promise<void> {
    while (true) {
      try {
        const comments = this.fetchPRComments(config.repo, config.coordinationPr, githubToken);

        for (const comment of comments) {
          if (processedIds.has(comment.id)) continue;

          // Check for @cursor mentions
          if (comment.body.includes("@cursor")) {
            console.log(`\n[INBOUND] New @cursor mention from ${comment.author}`);
            await this.processCoordinationComment(config, agentIds, comment, githubToken);
          }

          processedIds.add(comment.id);
        }
      } catch (err) {
        console.error("[INBOUND ERROR]", err);
      }

      await new Promise(r => setTimeout(r, interval));
    }
  }

  /**
   * Process an incoming @cursor comment
   */
  private async processCoordinationComment(
    config: CoordinationConfig,
    agentIds: Set<string>,
    comment: PRComment,
    githubToken?: string
  ): Promise<void> {
    const body = comment.body;

    if (body.includes("✅ DONE:")) {
      const match = body.match(/✅ DONE:\s*(bc-[\w-]+)\s*(.*)/);
      if (match) {
        const [, agentId, summary] = match;
        console.log(`  ✅ Agent ${agentId} completed: ${summary}`);
        agentIds.delete(agentId);
        this.postPRComment(
          config.repo, 
          config.coordinationPr, 
          `✅ Acknowledged completion from ${agentId.slice(0, 12)}. Summary: ${summary}`,
          githubToken
        );
      }
    } else if (body.includes("⚠️ BLOCKED:")) {
      const match = body.match(/⚠️ BLOCKED:\s*(bc-[\w-]+)\s*(.*)/);
      if (match) {
        const [, agentId, issue] = match;
        console.log(`  ⚠️ Agent ${agentId} blocked: ${issue}`);
        this.postPRComment(
          config.repo,
          config.coordinationPr,
          `⚠️ Agent ${agentId.slice(0, 12)} blocked: ${issue}\n\n@jbcom - Manual intervention may be required.`,
          githubToken
        );
      }
    } else if (body.includes("📊 STATUS:")) {
      const match = body.match(/📊 STATUS:\s*(bc-[\w-]+)\s*(.*)/);
      if (match) {
        const [, agentId, update] = match;
        console.log(`  📊 Agent ${agentId} update: ${update}`);
      }
    } else if (body.includes("🔄 HANDOFF:")) {
      const match = body.match(/🔄 HANDOFF:\s*(bc-[\w-]+)\s*(.*)/);
      if (match) {
        const [, agentId, info] = match;
        console.log(`  🔄 Agent ${agentId} handoff: ${info}`);
        this.postPRComment(
          config.repo,
          config.coordinationPr,
          `🔄 Handoff acknowledged from ${agentId.slice(0, 12)}: ${info}`,
          githubToken
        );
      }
    }
  }

  /**
   * Fetch comments from a GitHub PR
   */
  fetchPRComments(repo: string, prNumber: number, githubToken?: string): PRComment[] {
    try {
      const token = githubToken ?? process.env.GITHUB_JBCOM_TOKEN ?? "";
      const output = execSync(
        `GH_TOKEN="${token}" gh api repos/${repo}/issues/${prNumber}/comments --jq '.[] | {id: .id, body: .body, author: .user.login, createdAt: .created_at}'`,
        { encoding: "utf-8", stdio: ["pipe", "pipe", "pipe"] }
      );

      // Parse JSONL output
      return output
        .trim()
        .split("\n")
        .filter(Boolean)
        .map(line => JSON.parse(line) as PRComment);
    } catch {
      return [];
    }
  }

  /**
   * Post a comment to a GitHub PR
   */
  postPRComment(repo: string, prNumber: number, body: string, githubToken?: string): void {
    try {
      const token = githubToken ?? process.env.GITHUB_JBCOM_TOKEN ?? "";
      const escapedBody = body.replace(/"/g, '\\"').replace(/\n/g, '\\n');
      execSync(
        `GH_TOKEN="${token}" gh pr comment ${prNumber} --repo ${repo} --body "${escapedBody}"`,
        { stdio: ["pipe", "pipe", "pipe"] }
      );
    } catch (err) {
      console.error("Failed to post PR comment:", err);
    }
  }

  /**
   * Get emoji for agent status
   */
  private statusEmoji(status: AgentStatus): string {
    switch (status) {
      case "RUNNING": return "🔄";
      case "FINISHED":
      case "COMPLETED": return "✅";
      case "FAILED": return "❌";
      case "EXPIRED": return "⏰";
      default: return "❓";
    }
  }
}
