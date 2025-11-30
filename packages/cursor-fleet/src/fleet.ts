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

import { writeFile, mkdir, readFile } from "node:fs/promises";
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
  Message,
  Repository,
  SpawnContext,
} from "./types.js";

export interface ReplayResult {
  agent: Agent;
  conversation: Conversation;
  archivePath: string;
  analysis: TaskAnalysis;
}

export interface TaskAnalysis {
  /** Tasks that were completed based on conversation */
  completed: TaskItem[];
  /** Tasks that remain outstanding/in progress */
  outstanding: TaskItem[];
  /** PRs created during this session */
  prsCreated: PRInfo[];
  /** PRs merged during this session */
  prsMerged: PRInfo[];
  /** Key decisions made */
  keyDecisions: string[];
  /** Blockers encountered */
  blockers: string[];
  /** Summary of the session */
  sessionSummary: string;
  /** Total messages in conversation */
  messageCount: number;
  /** Session duration */
  duration: string;
}

export interface TaskItem {
  description: string;
  status: "completed" | "in_progress" | "blocked" | "pending";
  context?: string;
}

export interface PRInfo {
  number: number;
  title: string;
  url?: string;
  status: "open" | "merged" | "closed";
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
          
          // Trigger callbacks - both FINISHED and COMPLETED are successful terminal states
          if ((agent.status === "FINISHED" || agent.status === "COMPLETED") && prev?.status === "RUNNING") {
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

    // Non-terminal states - agents still working
    const nonTerminalStates = new Set<AgentStatus>(["RUNNING", "CREATING", "PENDING"]);

    while (pending.size > 0) {
      const statusMap = new Map<string, AgentStatus>();
      
      for (const id of pending) {
        const result = await this.status(id);
        if (result.success && result.data) {
          statusMap.set(id, result.data.status);
          
          // Check if agent has reached a terminal state
          if (!nonTerminalStates.has(result.data.status)) {
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

        // Iterate over a copy to avoid race conditions with inbound loop modifications
        for (const agentId of [...agentIds]) {
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
   * GH_TOKEN is read from environment by gh CLI automatically
   */
  fetchPRComments(repo: string, prNumber: number, _githubToken?: string): PRComment[] {
    try {
      // gh CLI reads GH_TOKEN from environment automatically
      const output = execSync(
        `gh api repos/${repo}/issues/${prNumber}/comments --jq '.[] | {id: .id, body: .body, author: .user.login, createdAt: .created_at}'`,
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
   * Uses --body-file - to safely pass body via stdin, avoiding shell injection
   */
  postPRComment(repo: string, prNumber: number, body: string, _githubToken?: string): void {
    try {
      // GH_TOKEN is read from environment by gh CLI automatically
      execSync(
        `gh pr comment ${prNumber} --repo ${repo} --body-file -`,
        { input: body, stdio: ["pipe", "pipe", "pipe"] }
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

  // ============================================
  // Replay & Analysis
  // ============================================

  /**
   * Replay an agent's conversation chronologically and analyze tasks
   * 
   * This is the core recovery function - retrieves the full conversation,
   * archives it to disk, and performs comprehensive task analysis.
   */
  async replay(agentId: string, options?: {
    outputDir?: string;
    verbose?: boolean;
  }): Promise<FleetResult<ReplayResult>> {
    const outputDir = options?.outputDir ?? join(this.archivePath, agentId);
    const verbose = options?.verbose ?? false;

    // 1. Get agent status
    if (verbose) console.log(`📡 Fetching agent status for ${agentId}...`);
    const statusResult = await this.status(agentId);
    if (!statusResult.success || !statusResult.data) {
      return { success: false, error: `Failed to get agent status: ${statusResult.error}` };
    }
    const agent = statusResult.data;

    // 2. Get conversation
    if (verbose) console.log(`💬 Fetching conversation (this may take a moment)...`);
    const convResult = await this.conversation(agentId);
    if (!convResult.success || !convResult.data) {
      return { success: false, error: `Failed to get conversation: ${convResult.error}` };
    }
    const conversation = convResult.data;

    // 3. Archive to disk
    if (verbose) console.log(`💾 Archiving to ${outputDir}...`);
    try {
      await mkdir(outputDir, { recursive: true });
      
      // Save raw conversation
      const convPath = join(outputDir, "conversation.json");
      await writeFile(convPath, JSON.stringify(conversation, null, 2));
      
      // Save agent status
      const statusPath = join(outputDir, "agent.json");
      await writeFile(statusPath, JSON.stringify(agent, null, 2));
      
    } catch (error) {
      return { success: false, error: `Failed to archive: ${error}` };
    }

    // 4. Analyze conversation
    if (verbose) console.log(`🔍 Analyzing ${conversation.messages.length} messages...`);
    const analysis = this.analyzeConversation(agent, conversation);

    // 5. Save analysis
    const analysisPath = join(outputDir, "analysis.json");
    await writeFile(analysisPath, JSON.stringify(analysis, null, 2));

    // 6. Generate markdown summary
    const summaryPath = join(outputDir, "REPLAY_SUMMARY.md");
    const summary = this.generateReplaySummary(agent, conversation, analysis);
    await writeFile(summaryPath, summary);

    return {
      success: true,
      data: {
        agent,
        conversation,
        archivePath: outputDir,
        analysis,
      },
    };
  }

  /**
   * Load a previously archived replay
   */
  async loadReplay(archiveDir: string): Promise<FleetResult<ReplayResult>> {
    try {
      const agentPath = join(archiveDir, "agent.json");
      const convPath = join(archiveDir, "conversation.json");
      const analysisPath = join(archiveDir, "analysis.json");

      const agent = JSON.parse(await readFile(agentPath, "utf-8")) as Agent;
      const conversation = JSON.parse(await readFile(convPath, "utf-8")) as Conversation;
      const analysis = JSON.parse(await readFile(analysisPath, "utf-8")) as TaskAnalysis;

      return {
        success: true,
        data: {
          agent,
          conversation,
          archivePath: archiveDir,
          analysis,
        },
      };
    } catch (error) {
      return { success: false, error: `Failed to load replay: ${error}` };
    }
  }

  /**
   * Analyze a conversation to extract tasks, PRs, and status
   */
  private analyzeConversation(agent: Agent, conversation: Conversation): TaskAnalysis {
    const messages = conversation.messages;
    const completed: TaskItem[] = [];
    const outstanding: TaskItem[] = [];
    const prsCreated: PRInfo[] = [];
    const prsMerged: PRInfo[] = [];
    const keyDecisions: string[] = [];
    const blockers: string[] = [];

    // Patterns to match
    const prCreatePattern = /(?:created|opened)\s+(?:PR|pull request)\s*#?(\d+)/gi;
    const prMergePattern = /(?:merged|merge)\s+(?:PR|pull request)\s*#?(\d+)/gi;
    const prUrlPattern = /https:\/\/github\.com\/[\w-]+\/[\w-]+\/pull\/(\d+)/g;
    const todoPattern = /(?:TODO|REMAINING|OUTSTANDING|PENDING):\s*(.+)/gi;
    const completedPattern = /(?:✅|DONE|COMPLETED|FINISHED):\s*(.+)/gi;
    const blockerPattern = /(?:❌|BLOCKED|BLOCKER|ERROR):\s*(.+)/gi;
    const decisionPattern = /(?:DECISION|DECIDED|CHOOSING|CHOSE):\s*(.+)/gi;

    // Track seen PRs to avoid duplicates
    const seenPRs = new Set<number>();

    for (const msg of messages) {
      const text = msg.text;

      // Extract PRs created
      let match;
      while ((match = prCreatePattern.exec(text)) !== null) {
        const prNum = parseInt(match[1], 10);
        if (!seenPRs.has(prNum)) {
          seenPRs.add(prNum);
          prsCreated.push({
            number: prNum,
            title: this.extractPRTitle(text, prNum),
            status: "open",
          });
        }
      }

      // Extract PRs merged
      while ((match = prMergePattern.exec(text)) !== null) {
        const prNum = parseInt(match[1], 10);
        const existing = prsCreated.find(p => p.number === prNum);
        if (existing) {
          existing.status = "merged";
          prsMerged.push(existing);
        } else if (!seenPRs.has(prNum)) {
          seenPRs.add(prNum);
          prsMerged.push({
            number: prNum,
            title: this.extractPRTitle(text, prNum),
            status: "merged",
          });
        }
      }

      // Extract PR URLs
      while ((match = prUrlPattern.exec(text)) !== null) {
        const prNum = parseInt(match[1], 10);
        const existing = prsCreated.find(p => p.number === prNum);
        if (existing) {
          existing.url = match[0];
        }
      }

      // Extract TODOs/outstanding items
      while ((match = todoPattern.exec(text)) !== null) {
        const desc = match[1].trim();
        if (desc.length > 10 && !outstanding.some(t => t.description.includes(desc.slice(0, 30)))) {
          outstanding.push({ description: desc, status: "pending" });
        }
      }

      // Extract completed items
      while ((match = completedPattern.exec(text)) !== null) {
        const desc = match[1].trim();
        if (desc.length > 10 && !completed.some(t => t.description.includes(desc.slice(0, 30)))) {
          completed.push({ description: desc, status: "completed" });
        }
      }

      // Extract blockers
      while ((match = blockerPattern.exec(text)) !== null) {
        const desc = match[1].trim();
        if (desc.length > 10 && !blockers.includes(desc)) {
          blockers.push(desc);
        }
      }

      // Extract key decisions
      while ((match = decisionPattern.exec(text)) !== null) {
        const desc = match[1].trim();
        if (desc.length > 10 && !keyDecisions.includes(desc)) {
          keyDecisions.push(desc);
        }
      }
    }

    // Calculate session duration
    const startTime = agent.createdAt ? new Date(agent.createdAt).getTime() : Date.now();
    const endTime = agent.finishedAt ? new Date(agent.finishedAt).getTime() : Date.now();
    const durationMs = endTime - startTime;
    const hours = Math.floor(durationMs / 3600000);
    const minutes = Math.floor((durationMs % 3600000) / 60000);
    const duration = hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`;

    return {
      completed,
      outstanding,
      prsCreated,
      prsMerged,
      keyDecisions,
      blockers,
      sessionSummary: agent.summary ?? "No summary available",
      messageCount: messages.length,
      duration,
    };
  }

  /**
   * Extract PR title from context
   */
  private extractPRTitle(text: string, prNum: number): string {
    // Try to find title near PR number
    const patterns = [
      new RegExp(`#${prNum}[:\\s]+["']?([^"'\\n]{10,80})["']?`, "i"),
      new RegExp(`PR\\s*#?${prNum}[:\\s]+(.{10,80})`, "i"),
      new RegExp(`title[:\\s]+["']([^"'\\n]{10,80})["']`, "i"),
    ];

    for (const pattern of patterns) {
      const match = pattern.exec(text);
      if (match) {
        return match[1].trim();
      }
    }

    return `PR #${prNum}`;
  }

  /**
   * Generate markdown summary of the replay
   */
  private generateReplaySummary(agent: Agent, conversation: Conversation, analysis: TaskAnalysis): string {
    const lines: string[] = [
      `# Agent Replay Summary: ${agent.id}`,
      "",
      `**Name**: ${agent.name ?? "Unknown"}`,
      `**Status**: ${agent.status}`,
      `**Repository**: ${agent.source.repository}`,
      `**Branch**: ${agent.target?.branchName ?? "N/A"}`,
      `**Created**: ${agent.createdAt ?? "Unknown"}`,
      `**Duration**: ${analysis.duration}`,
      `**Messages**: ${analysis.messageCount}`,
      "",
      "---",
      "",
      "## Session Summary",
      "",
      analysis.sessionSummary,
      "",
      "---",
      "",
      "## PRs Created",
      "",
    ];

    if (analysis.prsCreated.length > 0) {
      for (const pr of analysis.prsCreated) {
        const status = pr.status === "merged" ? "✅ MERGED" : pr.status === "closed" ? "❌ CLOSED" : "⏳ OPEN";
        lines.push(`- **#${pr.number}**: ${pr.title} [${status}]`);
        if (pr.url) lines.push(`  - ${pr.url}`);
      }
    } else {
      lines.push("_No PRs detected_");
    }

    lines.push("", "## Completed Tasks", "");

    if (analysis.completed.length > 0) {
      for (const task of analysis.completed) {
        lines.push(`- ✅ ${task.description}`);
      }
    } else {
      lines.push("_No explicitly marked completed tasks detected_");
    }

    lines.push("", "## Outstanding Tasks", "");

    if (analysis.outstanding.length > 0) {
      for (const task of analysis.outstanding) {
        lines.push(`- ⏳ ${task.description}`);
      }
    } else {
      lines.push("_No explicitly marked outstanding tasks detected_");
    }

    if (analysis.blockers.length > 0) {
      lines.push("", "## Blockers Encountered", "");
      for (const blocker of analysis.blockers) {
        lines.push(`- ❌ ${blocker}`);
      }
    }

    if (analysis.keyDecisions.length > 0) {
      lines.push("", "## Key Decisions", "");
      for (const decision of analysis.keyDecisions) {
        lines.push(`- 📌 ${decision}`);
      }
    }

    lines.push(
      "",
      "---",
      "",
      "## Conversation Chronology",
      "",
      "| # | Type | Preview |",
      "|---|------|---------|",
    );

    // Show first 20 and last 10 messages
    const messages = conversation.messages;
    const toShow = messages.length <= 30 
      ? messages 
      : [...messages.slice(0, 20), ...messages.slice(-10)];

    let idx = 0;
    for (const msg of toShow) {
      if (idx === 20 && messages.length > 30) {
        lines.push(`| ... | ... | _${messages.length - 30} messages omitted_ |`);
      }
      const role = msg.type === "user_message" ? "👤 USER" : "🤖 ASST";
      const preview = msg.text
        .replace(/\n/g, " ")
        .replace(/\|/g, "\\|")
        .slice(0, 100);
      const actualIdx = idx < 20 ? idx + 1 : messages.length - (toShow.length - idx) + 1;
      lines.push(`| ${actualIdx} | ${role} | ${preview}${msg.text.length > 100 ? "..." : ""} |`);
      idx++;
    }

    lines.push(
      "",
      "---",
      "",
      `_Generated by cursor-fleet replay at ${new Date().toISOString()}_`,
    );

    return lines.join("\n");
  }

  /**
   * Print a chronological replay to console
   */
  printReplay(conversation: Conversation, options?: {
    limit?: number;
    filter?: "user" | "assistant" | "all";
  }): void {
    const limit = options?.limit ?? conversation.messages.length;
    const filter = options?.filter ?? "all";

    const messages = conversation.messages
      .filter(m => filter === "all" || 
        (filter === "user" && m.type === "user_message") ||
        (filter === "assistant" && m.type === "assistant_message"))
      .slice(0, limit);

    console.log(`\n${"=".repeat(80)}`);
    console.log(`CONVERSATION REPLAY (${messages.length}/${conversation.messages.length} messages)`);
    console.log(`${"=".repeat(80)}\n`);

    for (let i = 0; i < messages.length; i++) {
      const msg = messages[i];
      const role = msg.type === "user_message" ? "👤 USER" : "🤖 ASSISTANT";
      const divider = msg.type === "user_message" ? "─" : "━";
      
      console.log(`${divider.repeat(60)}`);
      console.log(`[${i + 1}/${messages.length}] ${role}`);
      console.log(`${divider.repeat(60)}`);
      console.log(msg.text);
      console.log("");
    }

    console.log(`${"=".repeat(80)}`);
    console.log(`END OF REPLAY`);
    console.log(`${"=".repeat(80)}\n`);
  }

  /**
   * Close the MCP client connection
   */
  close(): void {
    this.client.close();
  }
}
