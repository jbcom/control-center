/**
 * Fleet - High-level API for Cursor Background Agent management
 * 
 * Uses direct Cursor API calls (no MCP overhead).
 * Includes conversation splitting for large conversations.
 */

import { writeFile, mkdir, readFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { execSync } from "node:child_process";
import { CursorAPI } from "./cursor-api.js";
import { splitConversation, type SplitResult } from "./conversation-splitter.js";
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
  split: SplitResult;
  analysis: TaskAnalysis;
}

export interface TaskAnalysis {
  completed: TaskItem[];
  outstanding: TaskItem[];
  prsCreated: PRInfo[];
  prsMerged: PRInfo[];
  keyDecisions: string[];
  blockers: string[];
  sessionSummary: string;
  messageCount: number;
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
  coordinationPr: number;
  repo: string;
  outboundInterval?: number;
  inboundInterval?: number;
  agentIds?: string[];
  githubToken?: string;
}

export interface PRComment {
  id: string;
  body: string;
  author: string;
  createdAt: string;
}

export class Fleet {
  private api: CursorAPI;
  private archivePath: string;

  constructor(config: FleetConfig = {}) {
    this.api = new CursorAPI(config.apiKey, config.timeout ?? 120000);
    this.archivePath = config.archivePath ?? "./.cursor/recovery";
  }

  // ============================================
  // Agent Discovery
  // ============================================

  async list(): Promise<FleetResult<Agent[]>> {
    return this.api.listAgents();
  }

  async listByStatus(status: AgentStatus): Promise<FleetResult<Agent[]>> {
    const result = await this.list();
    if (!result.success) return result;
    return { success: true, data: result.data?.filter(a => a.status === status) ?? [] };
  }

  async running(): Promise<FleetResult<Agent[]>> {
    return this.listByStatus("RUNNING");
  }

  async find(agentId: string): Promise<FleetResult<Agent | undefined>> {
    const result = await this.list();
    if (!result.success) return { success: false, error: result.error };
    return { success: true, data: result.data?.find(a => a.id === agentId) };
  }

  async status(agentId: string): Promise<FleetResult<Agent>> {
    return this.api.getAgentStatus(agentId);
  }

  // ============================================
  // Agent Spawning
  // ============================================

  async spawn(options: LaunchOptions): Promise<FleetResult<Agent>> {
    const task = this.buildTaskWithContext(options.task, options.context);
    return this.api.launchAgent({
      prompt: { text: task },
      source: {
        repository: options.repository,
        ref: options.ref ?? "main",
      },
    });
  }

  private buildTaskWithContext(task: string, context?: SpawnContext): string {
    if (!context) return task;
    const lines = [task, "", "--- COORDINATION CONTEXT ---"];
    if (context.controlManagerId) lines.push(`Control Manager Agent: ${context.controlManagerId}`);
    if (context.controlCenter) lines.push(`Control Center: ${context.controlCenter}`);
    if (context.relatedAgents?.length) lines.push(`Related Agents: ${context.relatedAgents.join(", ")}`);
    if (context.metadata) lines.push(`Metadata: ${JSON.stringify(context.metadata)}`);
    lines.push("Report progress via PR comments and addFollowup.");
    lines.push("--- END CONTEXT ---");
    return lines.join("\n");
  }

  // ============================================
  // Agent Communication
  // ============================================

  async followup(agentId: string, message: string): Promise<FleetResult<void>> {
    return this.api.addFollowup(agentId, { text: message });
  }

  async broadcast(agentIds: string[], message: string): Promise<Map<string, FleetResult<void>>> {
    const results = new Map<string, FleetResult<void>>();
    await Promise.all(agentIds.map(async (id) => {
      results.set(id, await this.followup(id, message));
    }));
    return results;
  }

  // ============================================
  // Conversations & Recovery
  // ============================================

  async conversation(agentId: string): Promise<FleetResult<Conversation>> {
    return this.api.getAgentConversation(agentId);
  }

  /**
   * Replay an agent's conversation - fetches, archives, splits, and analyzes
   */
  async replay(agentId: string, options?: {
    outputDir?: string;
    verbose?: boolean;
    batchSize?: number;
  }): Promise<FleetResult<ReplayResult>> {
    const outputDir = options?.outputDir ?? join(this.archivePath, agentId);
    const verbose = options?.verbose ?? false;
    const batchSize = options?.batchSize ?? 10;

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
      
      // Save full conversation
      const convPath = join(outputDir, "conversation.json");
      await writeFile(convPath, JSON.stringify(conversation, null, 2));
      
      // Save agent status
      const statusPath = join(outputDir, "agent.json");
      await writeFile(statusPath, JSON.stringify(agent, null, 2));
    } catch (error) {
      return { success: false, error: `Failed to archive: ${error}` };
    }

    // 4. Split conversation into readable chunks
    if (verbose) console.log(`📂 Splitting ${conversation.messages.length} messages into batches of ${batchSize}...`);
    const convPath = join(outputDir, "conversation.json");
    const splitResult = await splitConversation(convPath, outputDir, {
      batchSize,
      individualFiles: true,
      markdown: true,
      createIndex: true,
    });

    // 5. Analyze conversation
    if (verbose) console.log(`🔍 Analyzing conversation...`);
    const analysis = this.analyzeConversation(agent, conversation);

    // 6. Save analysis
    const analysisPath = join(outputDir, "analysis.json");
    await writeFile(analysisPath, JSON.stringify(analysis, null, 2));

    // 7. Generate summary
    const summaryPath = join(outputDir, "REPLAY_SUMMARY.md");
    const summary = this.generateReplaySummary(agent, conversation, analysis, splitResult);
    await writeFile(summaryPath, summary);

    if (verbose) {
      console.log(`\n✅ Replay complete!`);
      console.log(`   📁 Output: ${outputDir}`);
      console.log(`   💬 Messages: ${conversation.messages.length}`);
      console.log(`   📦 Batches: ${splitResult.batchCount}`);
      console.log(`   📄 Index: ${splitResult.files.index}`);
    }

    return {
      success: true,
      data: {
        agent,
        conversation,
        archivePath: outputDir,
        split: splitResult,
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
      const metaPath = join(archiveDir, "metadata.json");

      const agent = JSON.parse(await readFile(agentPath, "utf-8")) as Agent;
      const conversation = JSON.parse(await readFile(convPath, "utf-8")) as Conversation;
      const analysis = JSON.parse(await readFile(analysisPath, "utf-8")) as TaskAnalysis;
      
      let metadata: any = {};
      try {
        metadata = JSON.parse(await readFile(metaPath, "utf-8"));
      } catch { /* no metadata */ }

      return {
        success: true,
        data: {
          agent,
          conversation,
          archivePath: archiveDir,
          split: {
            outputDir: archiveDir,
            messageCount: metadata.messageCount ?? conversation.messages.length,
            batchCount: metadata.batchCount ?? Math.ceil(conversation.messages.length / 10),
            files: {
              messages: [],
              batches: [],
              index: join(archiveDir, "INDEX.md"),
              fullConversation: convPath,
            },
          },
          analysis,
        },
      };
    } catch (error) {
      return { success: false, error: `Failed to load replay: ${error}` };
    }
  }

  /**
   * Split an existing conversation file
   */
  async splitExisting(conversationPath: string, outputDir?: string, batchSize: number = 10): Promise<FleetResult<SplitResult>> {
    try {
      const outDir = outputDir ?? dirname(conversationPath);
      const result = await splitConversation(conversationPath, outDir, {
        batchSize,
        individualFiles: true,
        markdown: true,
        createIndex: true,
      });
      return { success: true, data: result };
    } catch (error) {
      return { success: false, error: `Failed to split: ${error}` };
    }
  }

  // ============================================
  // Analysis
  // ============================================

  private analyzeConversation(agent: Agent, conversation: Conversation): TaskAnalysis {
    const messages = conversation.messages;
    const completed: TaskItem[] = [];
    const outstanding: TaskItem[] = [];
    const prsCreated: PRInfo[] = [];
    const prsMerged: PRInfo[] = [];
    const keyDecisions: string[] = [];
    const blockers: string[] = [];

    const prCreatePattern = /(?:created|opened|create)\s+(?:PR|pull request)\s*#?(\d+)/gi;
    const prMergePattern = /(?:merged|merge)\s+(?:PR|pull request)\s*#?(\d+)/gi;
    const prUrlPattern = /https:\/\/github\.com\/[\w-]+\/[\w-]+\/pull\/(\d+)/g;
    const todoPattern = /(?:TODO|REMAINING|OUTSTANDING|PENDING|IN PROGRESS):\s*(.+)/gi;
    const completedPattern = /(?:✅|DONE|COMPLETED|FINISHED):\s*(.+)/gi;
    const blockerPattern = /(?:❌|BLOCKED|BLOCKER|ERROR|FAILED):\s*(.+)/gi;

    const seenPRs = new Set<number>();

    for (const msg of messages) {
      const text = msg.text;
      let match;

      while ((match = prCreatePattern.exec(text)) !== null) {
        const prNum = parseInt(match[1], 10);
        if (!seenPRs.has(prNum)) {
          seenPRs.add(prNum);
          prsCreated.push({ number: prNum, title: `PR #${prNum}`, status: "open" });
        }
      }

      while ((match = prMergePattern.exec(text)) !== null) {
        const prNum = parseInt(match[1], 10);
        const existing = prsCreated.find(p => p.number === prNum);
        if (existing) {
          existing.status = "merged";
          if (!prsMerged.includes(existing)) prsMerged.push(existing);
        } else if (!seenPRs.has(prNum)) {
          seenPRs.add(prNum);
          prsMerged.push({ number: prNum, title: `PR #${prNum}`, status: "merged" });
        }
      }

      while ((match = prUrlPattern.exec(text)) !== null) {
        const prNum = parseInt(match[1], 10);
        const existing = prsCreated.find(p => p.number === prNum);
        if (existing) existing.url = match[0];
      }

      while ((match = todoPattern.exec(text)) !== null) {
        const desc = match[1].trim();
        if (desc.length > 10 && !outstanding.some(t => t.description.includes(desc.slice(0, 30)))) {
          outstanding.push({ description: desc, status: "pending" });
        }
      }

      while ((match = completedPattern.exec(text)) !== null) {
        const desc = match[1].trim();
        if (desc.length > 10 && !completed.some(t => t.description.includes(desc.slice(0, 30)))) {
          completed.push({ description: desc, status: "completed" });
        }
      }

      while ((match = blockerPattern.exec(text)) !== null) {
        const desc = match[1].trim();
        if (desc.length > 10 && !blockers.includes(desc)) {
          blockers.push(desc);
        }
      }
    }

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

  private generateReplaySummary(agent: Agent, conversation: Conversation, analysis: TaskAnalysis, split: SplitResult): string {
    return `# Agent Replay Summary

**Agent ID**: \`${agent.id}\`
**Name**: ${agent.name ?? "Unknown"}
**Status**: ${agent.status}
**Repository**: ${agent.source.repository}
**Branch**: ${agent.target?.branchName ?? "N/A"}
**Created**: ${agent.createdAt ?? "Unknown"}
**Duration**: ${analysis.duration}

---

## Session Summary

${analysis.sessionSummary}

---

## Statistics

- **Total Messages**: ${analysis.messageCount}
- **Batches**: ${split.batchCount} (${split.files.batches.length} files)
- **PRs Created**: ${analysis.prsCreated.length}
- **PRs Merged**: ${analysis.prsMerged.length}

---

## How to Read This Conversation

1. **Index**: Start with [INDEX.md](INDEX.md) for an overview
2. **Batches**: Read \`batches/batch-001.md\` through \`batch-${String(split.batchCount).padStart(3, "0")}.md\`
3. **Individual**: For specific messages, check \`messages/0001-*.md\`

---

## PRs

${analysis.prsCreated.length > 0 
  ? analysis.prsCreated.map(pr => `- **#${pr.number}**: ${pr.title} [${pr.status.toUpperCase()}]${pr.url ? ` - ${pr.url}` : ""}`).join("\n")
  : "_No PRs detected_"}

---

## Completed Tasks

${analysis.completed.length > 0
  ? analysis.completed.map(t => `- ✅ ${t.description}`).join("\n")
  : "_No explicitly marked completed tasks_"}

---

## Outstanding Tasks

${analysis.outstanding.length > 0
  ? analysis.outstanding.map(t => `- ⏳ ${t.description}`).join("\n")
  : "_No explicitly marked outstanding tasks_"}

${analysis.blockers.length > 0 ? `
---

## Blockers

${analysis.blockers.map(b => `- ❌ ${b}`).join("\n")}
` : ""}

---

_Generated by cursor-fleet at ${new Date().toISOString()}_
`;
  }

  // ============================================
  // Repositories
  // ============================================

  async repositories(): Promise<FleetResult<Repository[]>> {
    return this.api.listRepositories();
  }

  // ============================================
  // Fleet Summary
  // ============================================

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
        completed: agents.filter(a => a.status === "COMPLETED" || a.status === "FINISHED").length,
        failed: agents.filter(a => a.status === "FAILED").length,
        agents,
      },
    };
  }

  // ============================================
  // Print helpers
  // ============================================

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
  }

  // ============================================
  // GitHub PR Helpers (for coordination)
  // ============================================

  fetchPRComments(repo: string, prNumber: number): PRComment[] {
    try {
      const output = execSync(
        `gh api repos/${repo}/issues/${prNumber}/comments --jq '.[] | {id: .id, body: .body, author: .user.login, createdAt: .created_at}'`,
        { encoding: "utf-8", stdio: ["pipe", "pipe", "pipe"] }
      );
      return output.trim().split("\n").filter(Boolean).map(line => JSON.parse(line) as PRComment);
    } catch {
      return [];
    }
  }

  postPRComment(repo: string, prNumber: number, body: string): void {
    try {
      execSync(`gh pr comment ${prNumber} --repo ${repo} --body-file -`, { input: body, stdio: ["pipe", "pipe", "pipe"] });
    } catch (err) {
      console.error("Failed to post PR comment:", err);
    }
  }
}

// Re-export splitter
export type { SplitResult } from "./conversation-splitter.js";
