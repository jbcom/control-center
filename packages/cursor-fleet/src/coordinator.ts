#!/usr/bin/env npx ts-node
/**
 * Fleet Coordinator - Bidirectional event loop
 * 
 * OUTBOUND: Periodically check sub-agents and send status requests
 * INBOUND: Poll coordination PR for @cursor mentions and process
 */

import { Fleet } from "./fleet";
import { execSync } from "child_process";

interface CoordinatorConfig {
  /** PR number for coordination channel */
  coordinationPr: number;
  /** Repository in owner/repo format */
  repo: string;
  /** Outbound poll interval (ms) */
  outboundInterval: number;
  /** Inbound poll interval (ms) */
  inboundInterval: number;
  /** Agent IDs to monitor */
  agentIds: string[];
}

interface PRComment {
  id: string;
  body: string;
  author: string;
  createdAt: string;
}

class FleetCoordinator {
  private fleet: Fleet;
  private config: CoordinatorConfig;
  private processedCommentIds: Set<string> = new Set();
  private lastOutboundCheck: Date = new Date(0);

  constructor(config: CoordinatorConfig) {
    this.fleet = new Fleet();
    this.config = config;
  }

  /**
   * Main coordination loop
   */
  async run(): Promise<void> {
    console.log("=== Fleet Coordinator Started ===");
    console.log(`Coordination PR: #${this.config.coordinationPr}`);
    console.log(`Monitoring ${this.config.agentIds.length} agents`);
    console.log("");

    // Run both loops concurrently
    await Promise.all([
      this.outboundLoop(),
      this.inboundLoop(),
    ]);
  }

  /**
   * OUTBOUND: Fan-out status checks to sub-agents
   */
  private async outboundLoop(): Promise<void> {
    while (true) {
      try {
        const now = new Date();
        const elapsed = now.getTime() - this.lastOutboundCheck.getTime();
        
        if (elapsed >= this.config.outboundInterval) {
          console.log(`\n[OUTBOUND ${now.toISOString()}] Checking agents...`);
          
          for (const agentId of this.config.agentIds) {
            await this.checkAgent(agentId);
          }
          
          this.lastOutboundCheck = now;
        }
      } catch (err) {
        console.error("[OUTBOUND ERROR]", err);
      }
      
      await this.sleep(5000); // Check every 5s if interval elapsed
    }
  }

  /**
   * Check a single agent and send follow-up if needed
   */
  private async checkAgent(agentId: string): Promise<void> {
    const result = await this.fleet.getAgent(agentId);
    
    if (!result.success || !result.data) {
      console.log(`  ⚠️ ${agentId.slice(0, 8)}: Unable to fetch status`);
      return;
    }

    const agent = result.data;
    const status = agent.status;
    
    console.log(`  ${this.statusEmoji(status)} ${agentId.slice(0, 8)}: ${status}`);

    // If still running, send periodic check-in request
    if (status === "RUNNING") {
      const message = [
        "📊 STATUS CHECK from Control Manager",
        "",
        "Please report your progress by commenting on the coordination PR:",
        `https://github.com/${this.config.repo}/pull/${this.config.coordinationPr}`,
        "",
        "Use format: @cursor 📊 STATUS: [your-agent-id] [brief update]",
        "",
        "If blocked, use: @cursor ⚠️ BLOCKED: [your-agent-id] [issue]",
        "If done, use: @cursor ✅ DONE: [your-agent-id] [summary]",
      ].join("\n");

      await this.fleet.sendFollowup(agentId, message);
    }
  }

  /**
   * INBOUND: Poll coordination PR for new comments
   */
  private async inboundLoop(): Promise<void> {
    while (true) {
      try {
        const comments = await this.fetchPRComments();
        
        for (const comment of comments) {
          if (this.processedCommentIds.has(comment.id)) continue;
          
          // Check for @cursor mentions
          if (comment.body.includes("@cursor")) {
            console.log(`\n[INBOUND] New @cursor mention from ${comment.author}`);
            await this.processComment(comment);
          }
          
          this.processedCommentIds.add(comment.id);
        }
      } catch (err) {
        console.error("[INBOUND ERROR]", err);
      }
      
      await this.sleep(this.config.inboundInterval);
    }
  }

  /**
   * Fetch comments from coordination PR
   */
  private async fetchPRComments(): Promise<PRComment[]> {
    try {
      const output = execSync(
        `GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh api repos/${this.config.repo}/issues/${this.config.coordinationPr}/comments --jq '.[] | {id: .id, body: .body, author: .user.login, createdAt: .created_at}'`,
        { encoding: "utf-8", stdio: ["pipe", "pipe", "pipe"] }
      );

      // Parse JSONL output
      return output
        .trim()
        .split("\n")
        .filter(Boolean)
        .map(line => JSON.parse(line));
    } catch {
      return [];
    }
  }

  /**
   * Process an incoming @cursor comment
   */
  private async processComment(comment: PRComment): Promise<void> {
    const body = comment.body;

    // Parse message type
    if (body.includes("✅ DONE:")) {
      const match = body.match(/✅ DONE:\s*(bc-[\w-]+)\s*(.*)/);
      if (match) {
        const [, agentId, summary] = match;
        console.log(`  ✅ Agent ${agentId} completed: ${summary}`);
        await this.handleAgentDone(agentId, summary);
      }
    } else if (body.includes("⚠️ BLOCKED:")) {
      const match = body.match(/⚠️ BLOCKED:\s*(bc-[\w-]+)\s*(.*)/);
      if (match) {
        const [, agentId, issue] = match;
        console.log(`  ⚠️ Agent ${agentId} blocked: ${issue}`);
        await this.handleAgentBlocked(agentId, issue);
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
        await this.handleHandoff(agentId, info);
      }
    }
  }

  /**
   * Handle agent completion
   */
  private async handleAgentDone(agentId: string, summary: string): Promise<void> {
    // Remove from active monitoring
    const idx = this.config.agentIds.indexOf(agentId);
    if (idx >= 0) {
      this.config.agentIds.splice(idx, 1);
    }

    // Post acknowledgment
    await this.postComment(`✅ Acknowledged completion from ${agentId.slice(0, 12)}. Summary: ${summary}`);
  }

  /**
   * Handle blocked agent
   */
  private async handleAgentBlocked(agentId: string, issue: string): Promise<void> {
    // Post acknowledgment and escalation
    await this.postComment(
      `⚠️ Agent ${agentId.slice(0, 12)} is blocked: ${issue}\n\n` +
      `@jbcom - Manual intervention may be required.`
    );
  }

  /**
   * Handle handoff request
   */
  private async handleHandoff(agentId: string, info: string): Promise<void> {
    // Check if this triggers spawning a new agent
    if (info.includes("spawn")) {
      console.log(`  → Would spawn new agent for handoff`);
      // TODO: Parse and spawn
    }

    await this.postComment(`🔄 Handoff acknowledged from ${agentId.slice(0, 12)}: ${info}`);
  }

  /**
   * Post a comment to coordination PR
   */
  private async postComment(body: string): Promise<void> {
    try {
      execSync(
        `GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr comment ${this.config.coordinationPr} --repo ${this.config.repo} --body "${body.replace(/"/g, '\\"')}"`,
        { stdio: ["pipe", "pipe", "pipe"] }
      );
    } catch (err) {
      console.error("Failed to post comment:", err);
    }
  }

  private statusEmoji(status: string): string {
    switch (status) {
      case "RUNNING": return "🔄";
      case "FINISHED":
      case "COMPLETED": return "✅";
      case "FAILED": return "❌";
      case "EXPIRED": return "⏰";
      default: return "❓";
    }
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Main entry point
async function main() {
  const coordinator = new FleetCoordinator({
    coordinationPr: parseInt(process.env.COORDINATION_PR || "251", 10),
    repo: process.env.REPO || "jbcom/jbcom-control-center",
    outboundInterval: parseInt(process.env.OUTBOUND_INTERVAL || "60000", 10),
    inboundInterval: parseInt(process.env.INBOUND_INTERVAL || "15000", 10),
    agentIds: (process.env.AGENT_IDS || "").split(",").filter(Boolean),
  });

  await coordinator.run();
}

main().catch(console.error);
