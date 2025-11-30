/**
 * Station-to-Station Handoff Protocol
 * 
 * Enables seamless agent continuity:
 * 1. Current agent completes scope of work
 * 2. Spawns successor agent (not sub-agent - its own master)
 * 3. Successor confirms health via fleet tooling
 * 4. Successor retrieves predecessor's conversation
 * 5. Successor merges predecessor's PR
 * 6. Successor opens own PR and continues work
 */

import { execSync } from "node:child_process";
import { writeFileSync, mkdirSync, existsSync } from "node:fs";
import { join } from "node:path";
import { CursorAPI } from "../fleet/cursor-api.js";
import { AIAnalyzer } from "../triage/analyzer.js";
import { getEnvForRepo } from "../core/tokens.js";
import { log } from "../core/config.js";
import type { 
  HandoffContext, 
  HandoffOptions, 
  HandoffResult,
  Result,
} from "../core/types.js";

// ============================================
// Types
// ============================================

export type MergeMethod = "merge" | "squash" | "rebase";

export interface TakeoverOptions {
  admin?: boolean;
  auto?: boolean;
  mergeMethod?: MergeMethod;
  deleteBranch?: boolean;
}

// ============================================
// Handoff Manager
// ============================================

export class HandoffManager {
  private api: CursorAPI | null;
  private analyzer: AIAnalyzer | null;
  private repo: string;

  constructor(options?: { 
    cursorApiKey?: string; 
    anthropicKey?: string;
    repo?: string;
  }) {
    // Initialize Cursor API if available
    try {
      this.api = new CursorAPI({ apiKey: options?.cursorApiKey });
    } catch {
      this.api = null;
      log.warn("Cursor API not available for handoff operations");
    }

    // Initialize AI Analyzer if available
    try {
      this.analyzer = new AIAnalyzer({ apiKey: options?.anthropicKey });
    } catch {
      this.analyzer = null;
      log.warn("AI Analyzer not available for handoff analysis");
    }

    this.repo = options?.repo ?? "jbcom/jbcom-control-center";
  }

  /**
   * Initiate handoff to successor agent
   */
  async initiateHandoff(
    predecessorId: string,
    options: HandoffOptions
  ): Promise<HandoffResult> {
    log.info("=== Station-to-Station Handoff Initiated ===");

    if (!this.api) {
      return { success: false, error: "Cursor API not available" };
    }

    // 1. Analyze predecessor's conversation
    log.info("📊 Analyzing predecessor conversation...");
    const convResult = await this.api.getAgentConversation(predecessorId);
    if (!convResult.success || !convResult.data) {
      return { success: false, error: `Failed to get conversation: ${convResult.error}` };
    }

    let completedWork: string[] = [];
    let outstandingTasks: string[] = options.tasks ?? [];
    let decisions: string[] = [];

    // Use AI analysis if available
    if (this.analyzer) {
      try {
        const analysis = await this.analyzer.analyzeConversation(convResult.data);
        completedWork = analysis.completedTasks.map(t => t.title);
        outstandingTasks = [
          ...analysis.outstandingTasks.map(t => `[${t.priority}] ${t.title}`),
          ...outstandingTasks,
        ];
        decisions = analysis.recommendations;
      } catch (err) {
        log.warn("AI analysis failed, using minimal context:", err);
      }
    }

    // 2. Build handoff context
    const handoffContext: HandoffContext = {
      predecessorId,
      predecessorPr: options.currentPr,
      predecessorBranch: options.currentBranch,
      handoffTime: new Date().toISOString(),
      completedWork: completedWork.map(w => ({ id: `completed-${Date.now()}`, title: w, description: w, priority: "medium" as const, category: "other" as const, status: "completed" as const })),
      outstandingTasks: outstandingTasks.map(t => ({ id: `task-${Date.now()}`, title: t, description: t, priority: "medium" as const, category: "other" as const, status: "pending" as const })),
      decisions,
    };

    // 3. Save handoff context
    const handoffDir = join(".cursor", "handoff", predecessorId);
    if (!existsSync(handoffDir)) {
      mkdirSync(handoffDir, { recursive: true });
    }
    writeFileSync(
      join(handoffDir, "context.json"),
      JSON.stringify(handoffContext, null, 2)
    );

    // 4. Build successor prompt
    const successorPrompt = this.buildSuccessorPrompt(handoffContext, options);

    // 5. Spawn successor agent
    log.info("🚀 Spawning successor agent...");
    const spawnResult = await this.api.launchAgent({
      prompt: { text: successorPrompt },
      source: {
        repository: options.repository,
        ref: options.ref ?? "main",
      },
    });

    if (!spawnResult.success || !spawnResult.data) {
      return { success: false, error: `Failed to spawn successor: ${spawnResult.error}` };
    }

    const successorId = spawnResult.data.id;
    log.info(`✅ Successor spawned: ${successorId}`);

    // 6. Wait for health check
    log.info("⏳ Waiting for successor health confirmation...");
    const healthCheckResult = await this.waitForHealthCheck(
      successorId,
      options.healthCheckTimeout ?? 300000
    );

    return {
      success: true,
      successorId,
      successorHealthy: healthCheckResult.healthy,
    };
  }

  /**
   * Called by successor to confirm health
   */
  async confirmHealthAndBegin(
    successorId: string,
    predecessorId: string
  ): Promise<void> {
    if (!this.api) {
      throw new Error("Cursor API not available");
    }

    await this.api.addFollowup(predecessorId, {
      text: `🤝 HANDOFF CONFIRMED

Successor agent ${successorId} is healthy and beginning work.

I will now:
1. Review your conversation history
2. Merge your PR
3. Open my own PR
4. Continue the outstanding tasks

You can safely conclude your session.

@cursor 🤝 HANDOFF: ${successorId} confirmed healthy`,
    });
  }

  /**
   * Called by successor to merge predecessor and take over
   */
  async takeover(
    predecessorId: string,
    predecessorPr: number,
    newBranchName: string,
    options?: TakeoverOptions
  ): Promise<Result<void>> {
    log.info("=== Successor Takeover ===");

    if (options?.admin && options?.auto) {
      return { success: false, error: "Cannot use --admin and --auto simultaneously" };
    }

    // Use appropriate token for the repo
    const env = { ...process.env, ...getEnvForRepo(this.repo) };

    // 1. Merge predecessor's PR
    log.info(`📥 Merging predecessor PR #${predecessorPr}...`);
    try {
      const mergeMethod = options?.mergeMethod ?? "squash";
      const deleteBranch = options?.deleteBranch !== false;
      const mergeArgs = [
        `gh pr merge ${predecessorPr}`,
        `--${mergeMethod}`,
        "--repo",
        this.repo,
      ];

      if (deleteBranch) {
        mergeArgs.splice(2, 0, "--delete-branch");
      }

      if (options?.admin) {
        mergeArgs.push("--admin");
      } else if (options?.auto) {
        mergeArgs.push("--auto");
      }

      execSync(mergeArgs.join(" "), { encoding: "utf-8", env });
      log.info("✅ Predecessor PR merged");
    } catch (err) {
      return { success: false, error: `Failed to merge PR: ${err}` };
    }

    // 2. Pull latest main
    log.info("📥 Pulling latest main...");
    try {
      execSync("git checkout main && git pull", { encoding: "utf-8" });
    } catch (err) {
      return { success: false, error: `Failed to pull main: ${err}` };
    }

    // 3. Create own branch
    log.info(`🌿 Creating branch: ${newBranchName}...`);
    try {
      execSync(`git checkout -b ${newBranchName}`, { encoding: "utf-8" });
    } catch (err) {
      return { success: false, error: `Failed to create branch: ${err}` };
    }

    // 4. Notify predecessor
    if (this.api) {
      await this.api.addFollowup(predecessorId, {
        text: `✅ TAKEOVER COMPLETE

I have:
1. Merged your PR #${predecessorPr}
2. Created my own branch: ${newBranchName}
3. Loaded your context

Your session is now complete. Thank you!

@cursor ✅ DONE: ${predecessorId} successfully handed off`,
      });
    }

    log.info("✅ Takeover complete");
    return { success: true };
  }

  /**
   * Build successor prompt
   */
  private buildSuccessorPrompt(context: HandoffContext, options: HandoffOptions): string {
    return `# STATION-TO-STATION HANDOFF

You are a SUCCESSOR AGENT taking over from predecessor ${context.predecessorId}.

## CRITICAL FIRST STEPS

1. **IMMEDIATELY** send health confirmation:
   \`\`\`
   agentic handoff confirm ${context.predecessorId}
   \`\`\`

2. **LOAD** predecessor context from:
   \`.cursor/handoff/${context.predecessorId}/\`

3. **TAKEOVER** from predecessor:
   \`\`\`
   agentic handoff takeover ${context.predecessorId} ${context.predecessorPr} successor/continue-work-$(date +%Y%m%d)
   \`\`\`

4. **CREATE YOUR OWN HOLD-OPEN PR** and continue work.

## PREDECESSOR SUMMARY

### Completed Work
${context.completedWork.map(t => `- ${t.title}`).join("\n")}

### Outstanding Tasks (YOUR WORK)
${context.outstandingTasks.map(t => `- ${t.title}`).join("\n")}

### Recommendations
${context.decisions.map(d => `- ${d}`).join("\n")}

## IMPORTANT

- You are NOT a sub-agent - you are an independent master agent
- Predecessor PR #${context.predecessorPr} on branch \`${context.predecessorBranch}\`
- Repository: ${options.repository}
- Handoff time: ${context.handoffTime}

BEGIN by sending health confirmation NOW.
`;
  }

  /**
   * Wait for health check from successor
   */
  private async waitForHealthCheck(
    successorId: string,
    timeout: number
  ): Promise<{ healthy: boolean }> {
    if (!this.api) {
      return { healthy: false };
    }

    const start = Date.now();
    const interval = 15000;

    while (Date.now() - start < timeout) {
      const status = await this.api.getAgentStatus(successorId);
      
      if (status.success && status.data) {
        if (status.data.status === "RUNNING") {
          const conv = await this.api.getAgentConversation(successorId);
          if (conv.success && conv.data) {
            const messages = conv.data.messages || [];
            for (const msg of messages) {
              if (msg.text?.includes("HANDOFF CONFIRMED")) {
                return { healthy: true };
              }
            }
          }
        } else if (status.data.status === "FAILED") {
          return { healthy: false };
        }
      }

      await new Promise(r => setTimeout(r, interval));
    }

    return { healthy: false };
  }
}
