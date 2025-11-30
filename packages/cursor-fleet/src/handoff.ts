/**
 * Station-to-Station Handoff Protocol
 * 
 * Enables seamless agent continuity:
 * 1. Current agent completes SOW
 * 2. Spawns successor agent (not sub-agent - its own master)
 * 3. Successor confirms health via fleet tooling
 * 4. Successor retrieves predecessor's conversation
 * 5. Successor merges predecessor's PR, closes them out
 * 6. Successor opens own PR and continues work
 */

import { execSync } from "node:child_process";
import { writeFileSync, mkdirSync, existsSync } from "node:fs";
import { join } from "node:path";
import { CursorAPI } from "./cursor-api.js";
import { AIAnalyzer } from "./ai-analyzer.js";
import { splitConversation } from "./conversation-splitter.js";
import type { Conversation, Agent, FleetResult } from "./types.js";

export interface HandoffContext {
  /** Predecessor agent ID */
  predecessorId: string;
  /** Predecessor's PR number (to merge) */
  predecessorPr: number;
  /** Repository */
  repo: string;
  /** Branch the predecessor was on */
  predecessorBranch: string;
  /** Summary of completed work */
  completedWork: string[];
  /** Outstanding tasks to continue */
  outstandingTasks: string[];
  /** Key decisions made */
  decisions: string[];
  /** Timestamp of handoff */
  handoffTime: string;
}

export interface HandoffOptions {
  /** Repository URL for successor */
  repository: string;
  /** Git ref for successor */
  ref?: string;
  /** PR number of current agent (to be merged by successor) */
  currentPr: number;
  /** Current branch name */
  currentBranch: string;
  /** Tasks for successor to continue */
  tasks: string[];
  /** Health check timeout (ms) */
  healthCheckTimeout?: number;
  /** Health check interval (ms) */
  healthCheckInterval?: number;
}

export interface HandoffResult {
  success: boolean;
  successorId?: string;
  successorHealthy?: boolean;
  handoffContext?: HandoffContext;
  error?: string;
}

/**
 * Manages station-to-station handoff between agents
 */
export class HandoffManager {
  private api: CursorAPI;
  private analyzer: AIAnalyzer;
  private githubToken: string;
  private repo: string;

  constructor(options?: { 
    apiKey?: string; 
    anthropicKey?: string;
    githubToken?: string;
    repo?: string;
  }) {
    this.api = new CursorAPI({ apiKey: options?.apiKey });
    this.analyzer = new AIAnalyzer({ apiKey: options?.anthropicKey });
    this.githubToken = options?.githubToken ?? process.env.GITHUB_JBCOM_TOKEN ?? "";
    this.repo = options?.repo ?? "jbcom/jbcom-control-center";
  }

  /**
   * Initiate handoff to successor agent
   * 
   * This is called by the predecessor when they're ready to hand off
   */
  async initiateHandoff(
    predecessorId: string,
    options: HandoffOptions
  ): Promise<HandoffResult> {
    console.log("=== Station-to-Station Handoff Initiated ===\n");

    // 1. Analyze predecessor's conversation to extract context
    console.log("📊 Analyzing predecessor conversation...");
    const convResult = await this.api.getAgentConversation(predecessorId);
    if (!convResult.success || !convResult.data) {
      return { success: false, error: `Failed to get conversation: ${convResult.error}` };
    }

    const analysis = await this.analyzer.analyzeConversation(convResult.data);
    
    // 2. Build handoff context
    const handoffContext: HandoffContext = {
      predecessorId,
      predecessorPr: options.currentPr,
      repo: this.repo,
      predecessorBranch: options.currentBranch,
      completedWork: analysis.completedTasks.map(t => t.title),
      outstandingTasks: [
        ...analysis.outstandingTasks.map(t => `[${t.priority}] ${t.title}`),
        ...options.tasks,
      ],
      decisions: analysis.decisions.map(d => d.decision),
      handoffTime: new Date().toISOString(),
    };

    // 3. Save handoff context to file for successor
    const handoffDir = join(".cursor", "handoff", predecessorId);
    if (!existsSync(handoffDir)) {
      mkdirSync(handoffDir, { recursive: true });
    }
    writeFileSync(
      join(handoffDir, "context.json"),
      JSON.stringify(handoffContext, null, 2)
    );

    // 4. Split and save conversation for successor replay
    console.log("📝 Archiving conversation for successor...");
    await splitConversation(convResult.data, {
      outputDir: join(handoffDir, "conversation"),
    });

    // 5. Build successor task prompt
    const successorPrompt = this.buildSuccessorPrompt(handoffContext);

    // 6. Spawn successor agent
    console.log("🚀 Spawning successor agent...");
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
    console.log(`✅ Successor spawned: ${successorId}`);

    // 7. Wait for health check from successor
    console.log("\n⏳ Waiting for successor health confirmation...");
    const healthCheckResult = await this.waitForHealthCheck(
      successorId,
      options.healthCheckTimeout ?? 300000, // 5 minutes default
      options.healthCheckInterval ?? 15000   // 15 seconds
    );

    if (!healthCheckResult.healthy) {
      console.log("⚠️ Successor did not confirm health in time");
      console.log("   Manual intervention may be required");
      return {
        success: true, // Handoff initiated, but health unconfirmed
        successorId,
        successorHealthy: false,
        handoffContext,
      };
    }

    console.log("✅ Successor confirmed healthy!");
    console.log("\n=== Handoff Complete ===");
    console.log(`Predecessor: ${predecessorId}`);
    console.log(`Successor:   ${successorId}`);
    console.log(`PR to merge: #${options.currentPr}`);
    console.log("\nSuccessor will now:");
    console.log("  1. Review predecessor's conversation");
    console.log("  2. Merge predecessor's PR");
    console.log("  3. Open own PR against main");
    console.log("  4. Continue outstanding work");

    return {
      success: true,
      successorId,
      successorHealthy: true,
      handoffContext,
    };
  }

  /**
   * Called by successor to confirm health and begin work
   */
  async confirmHealthAndBegin(
    successorId: string,
    predecessorId: string
  ): Promise<void> {
    // Send health confirmation to predecessor
    await this.api.addFollowup(predecessorId, {
      text: `🤝 HANDOFF CONFIRMED

Successor agent ${successorId} is healthy and beginning work.

I will now:
1. Review your conversation history
2. Merge your PR
3. Open my own PR
4. Continue the outstanding tasks

You can safely conclude your session.
Thank you for your work!

@cursor 🤝 HANDOFF: ${successorId} confirmed healthy, beginning work`,
    });
  }

  /**
   * Called by successor to merge predecessor and take over
   */
  async takeover(
    predecessorId: string,
    predecessorPr: number,
    newBranchName: string
  ): Promise<{ success: boolean; error?: string }> {
    console.log("=== Successor Takeover ===\n");

    // 1. Merge predecessor's PR
    console.log(`📥 Merging predecessor PR #${predecessorPr}...`);
    try {
      execSync(
        `gh pr merge ${predecessorPr} --squash --delete-branch --repo ${this.repo}`,
        { 
          encoding: "utf-8",
          env: { ...process.env, GH_TOKEN: this.githubToken },
        }
      );
      console.log("✅ Predecessor PR merged");
    } catch (err) {
      return { success: false, error: `Failed to merge PR: ${err}` };
    }

    // 2. Pull latest main
    console.log("📥 Pulling latest main...");
    try {
      execSync("git checkout main && git pull", { encoding: "utf-8" });
    } catch (err) {
      return { success: false, error: `Failed to pull main: ${err}` };
    }

    // 3. Create own branch
    console.log(`🌿 Creating branch: ${newBranchName}...`);
    try {
      execSync(`git checkout -b ${newBranchName}`, { encoding: "utf-8" });
    } catch (err) {
      return { success: false, error: `Failed to create branch: ${err}` };
    }

    // 4. Notify predecessor they're closed out
    await this.api.addFollowup(predecessorId, {
      text: `✅ TAKEOVER COMPLETE

I have:
1. Merged your PR #${predecessorPr}
2. Created my own branch: ${newBranchName}
3. Loaded your context into my memory

Your session is now complete. Thank you!

@cursor ✅ DONE: ${predecessorId} successfully handed off to successor`,
    });

    console.log("✅ Takeover complete");
    return { success: true };
  }

  /**
   * Build the prompt for successor agent
   */
  private buildSuccessorPrompt(context: HandoffContext): string {
    return `# STATION-TO-STATION HANDOFF

You are a SUCCESSOR AGENT taking over from predecessor ${context.predecessorId}.

## CRITICAL FIRST STEPS

1. **IMMEDIATELY** send health confirmation:
   \`\`\`
   cursor-fleet handoff confirm ${context.predecessorId}
   \`\`\`

2. **LOAD** predecessor context from:
   \`.cursor/handoff/${context.predecessorId}/\`
   - \`context.json\` - Handoff metadata
   - \`conversation/\` - Full conversation history

3. **REVIEW** the conversation history to understand:
   - What was completed
   - What remains to be done
   - Key decisions made

4. **TAKEOVER** from predecessor:
   \`\`\`
   cursor-fleet handoff takeover ${context.predecessorId} ${context.predecessorPr} successor/continue-work-$(date +%Y%m%d)
   \`\`\`
   This will merge their PR and create your own branch.

5. **CREATE YOUR OWN HOLD-OPEN PR** and continue work.

## PREDECESSOR SUMMARY

### Completed Work
${context.completedWork.map(w => `- ${w}`).join("\n")}

### Outstanding Tasks (YOUR WORK)
${context.outstandingTasks.map(t => `- ${t}`).join("\n")}

### Key Decisions Made
${context.decisions.map(d => `- ${d}`).join("\n")}

## YOUR RESPONSIBILITIES

1. Complete the outstanding tasks
2. Create your own GitHub issues for planning
3. Use \`cursor-fleet analyze\` to track progress
4. When YOU are done, initiate handoff to YOUR successor

## IMPORTANT

- You are NOT a sub-agent - you are an independent master agent
- Predecessor PR #${context.predecessorPr} on branch \`${context.predecessorBranch}\`
- Repository: ${context.repo}
- Handoff time: ${context.handoffTime}

BEGIN by sending health confirmation NOW.
`;
  }

  /**
   * Wait for health check from successor
   */
  private async waitForHealthCheck(
    successorId: string,
    timeout: number,
    interval: number
  ): Promise<{ healthy: boolean }> {
    const start = Date.now();

    while (Date.now() - start < timeout) {
      const status = await this.api.getAgentStatus(successorId);
      
      if (status.success && status.data) {
        // Check if still running (healthy)
        if (status.data.status === "RUNNING") {
          // Check conversation for health confirmation
          const conv = await this.api.getAgentConversation(successorId);
          if (conv.success && conv.data) {
            const messages = conv.data.messages || [];
            for (const msg of messages) {
              if (msg.text?.includes("HANDOFF CONFIRMED") || 
                  msg.text?.includes("cursor-fleet handoff confirm")) {
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

/**
 * Convenience function for CLI
 */
export async function initiateHandoff(
  options: HandoffOptions & { predecessorId: string }
): Promise<HandoffResult> {
  const manager = new HandoffManager();
  return manager.initiateHandoff(options.predecessorId, options);
}
