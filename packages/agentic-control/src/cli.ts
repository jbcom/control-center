#!/usr/bin/env node
/**
 * agentic-control CLI
 * 
 * Unified command-line interface for AI agent fleet management,
 * triage, and orchestration across multiple GitHub organizations.
 */

import { Command } from "commander";
import { writeFileSync } from "node:fs";
import { Fleet } from "./fleet/index.js";
import { AIAnalyzer } from "./triage/index.js";
import { HandoffManager } from "./handoff/index.js";
import {
  getTokenSummary,
  validateTokens,
  getConfiguredOrgs,
  extractOrg,
} from "./core/tokens.js";
import { initConfig, getDefaultModel } from "./core/config.js";
import type { Agent } from "./core/types.js";
import { VERSION } from "./index.js";

const program = new Command();

program
  .name("agentic")
  .description("Unified AI agent fleet management, triage, and orchestration")
  .version(VERSION);

// ============================================
// Helper Functions
// ============================================

function output(data: unknown, json: boolean): void {
  if (json) {
    console.log(JSON.stringify(data, null, 2));
  } else {
    console.log(data);
  }
}

function formatAgent(agent: Agent): string {
  const status = agent.status.padEnd(10);
  const id = agent.id.padEnd(40);
  const repo = (agent.source?.repository?.split("/").pop() ?? "?").padEnd(25);
  const name = (agent.name ?? "").slice(0, 40);
  return `${status} ${id} ${repo} ${name}`;
}

// ============================================
// Token Commands
// ============================================

const tokensCmd = program
  .command("tokens")
  .description("Manage GitHub tokens for multi-org access");

tokensCmd
  .command("status")
  .description("Show token availability status")
  .option("--json", "Output as JSON")
  .action((opts) => {
    const summary = getTokenSummary();
    
    if (opts.json) {
      output(summary, true);
    } else {
      console.log("=== Token Status ===\n");
      for (const [org, info] of Object.entries(summary)) {
        const status = info.available ? "✅" : "❌";
        console.log(`${status} ${org.padEnd(15)} ${info.envVar}`);
      }
    }
  });

tokensCmd
  .command("validate")
  .description("Validate required tokens are available")
  .option("--orgs <orgs>", "Comma-separated org names to validate")
  .action((opts) => {
    const orgs = opts.orgs?.split(",").map((s: string) => s.trim());
    const result = validateTokens(orgs);
    
    if (result.success) {
      console.log("✅ All required tokens are available");
    } else {
      console.error("❌ Missing tokens:");
      for (const missing of result.data ?? []) {
        console.error(`   - ${missing}`);
      }
      process.exit(1);
    }
  });

tokensCmd
  .command("for-repo")
  .description("Show which token would be used for a repository")
  .argument("<repo>", "Repository URL or owner/repo")
  .action((repo) => {
    const org = extractOrg(repo);
    const summary = getTokenSummary();
    const config = org ? summary[org] : null;
    
    console.log(`Repository: ${repo}`);
    console.log(`Organization: ${org ?? "unknown"}`);
    if (config) {
      console.log(`Token Env Var: ${config.envVar}`);
      console.log(`Available: ${config.available ? "✅ Yes" : "❌ No"}`);
    } else {
      console.log("Using default token (GITHUB_TOKEN)");
    }
  });

// ============================================
// Fleet Commands
// ============================================

const fleetCmd = program
  .command("fleet")
  .description("Cursor Background Agent fleet management");

fleetCmd
  .command("list")
  .description("List all agents")
  .option("--running", "Show only running agents")
  .option("--json", "Output as JSON")
  .action(async (opts) => {
    const fleet = new Fleet();
    const result = opts.running ? await fleet.running() : await fleet.list();
    
    if (!result.success) {
      console.error(`❌ ${result.error}`);
      process.exit(1);
    }

    if (opts.json) {
      output(result.data, true);
    } else {
      console.log("=== Fleet Status ===\n");
      console.log(`${"STATUS".padEnd(10)} ${"ID".padEnd(40)} ${"REPO".padEnd(25)} NAME`);
      console.log("-".repeat(100));
      for (const agent of result.data ?? []) {
        console.log(formatAgent(agent));
      }
      console.log(`\nTotal: ${result.data?.length ?? 0} agents`);
    }
  });

fleetCmd
  .command("spawn")
  .description("Spawn a new agent")
  .argument("<repo>", "Repository URL (https://github.com/org/repo)")
  .argument("<task>", "Task description")
  .option("--ref <ref>", "Git ref", "main")
  .option("--model <model>", "AI model to use", getDefaultModel())
  .option("--json", "Output as JSON")
  .action(async (repo, task, opts) => {
    const fleet = new Fleet();
    
    const result = await fleet.spawn({
      repository: repo,
      task,
      ref: opts.ref,
      model: opts.model,
    });

    if (!result.success) {
      console.error(`❌ ${result.error}`);
      process.exit(1);
    }

    if (opts.json) {
      output(result.data, true);
    } else {
      console.log("=== Agent Spawned ===\n");
      console.log(`ID:     ${result.data?.id}`);
      console.log(`Status: ${result.data?.status}`);
      console.log(`Model:  ${opts.model}`);
    }
  });

fleetCmd
  .command("followup")
  .description("Send follow-up message to agent")
  .argument("<agent-id>", "Agent ID")
  .argument("<message>", "Message to send")
  .action(async (agentId, message) => {
    const fleet = new Fleet();
    const result = await fleet.followup(agentId, message);

    if (!result.success) {
      console.error(`❌ ${result.error}`);
      process.exit(1);
    }

    console.log(`✅ Follow-up sent to ${agentId}`);
  });

fleetCmd
  .command("summary")
  .description("Get fleet summary")
  .option("--json", "Output as JSON")
  .action(async (opts) => {
    const fleet = new Fleet();
    const result = await fleet.summary();

    if (!result.success) {
      console.error(`❌ ${result.error}`);
      process.exit(1);
    }

    if (opts.json) {
      output(result.data, true);
    } else {
      const s = result.data!;
      console.log("=== Fleet Summary ===\n");
      console.log(`Total:     ${s.total}`);
      console.log(`Running:   ${s.running}`);
      console.log(`Completed: ${s.completed}`);
      console.log(`Failed:    ${s.failed}`);
    }
  });

fleetCmd
  .command("coordinate")
  .description("Run bidirectional fleet coordinator")
  .requiredOption("--pr <number>", "Coordination PR number")
  .option("--repo <owner/name>", "Repository", "jbcom/jbcom-control-center")
  .option("--outbound <ms>", "Outbound poll interval (ms)", "60000")
  .option("--inbound <ms>", "Inbound poll interval (ms)", "15000")
  .option("--agents <ids>", "Comma-separated agent IDs to monitor", "")
  .action(async (opts) => {
    const fleet = new Fleet();
    
    await fleet.coordinate({
      coordinationPr: parseInt(opts.pr, 10),
      repo: opts.repo,
      outboundInterval: parseInt(opts.outbound, 10),
      inboundInterval: parseInt(opts.inbound, 10),
      agentIds: opts.agents ? opts.agents.split(",").filter(Boolean) : [],
    });
  });

// ============================================
// Triage Commands
// ============================================

const triageCmd = program
  .command("triage")
  .description("AI-powered triage and analysis");

triageCmd
  .command("quick")
  .description("Quick AI triage of text input")
  .argument("<input>", "Text to triage (or - for stdin)")
  .option("--model <model>", "Claude model to use", getDefaultModel())
  .action(async (input, opts) => {
    let text = input;
    if (input === "-") {
      text = "";
      process.stdin.setEncoding("utf8");
      for await (const chunk of process.stdin) {
        text += chunk;
      }
    }

    const analyzer = new AIAnalyzer({ model: opts.model });
    
    try {
      const result = await analyzer.quickTriage(text);
      
      console.log("\n=== Triage Result ===\n");
      console.log(`Priority:   ${result.priority.toUpperCase()}`);
      console.log(`Category:   ${result.category}`);
      console.log(`Summary:    ${result.summary}`);
      console.log(`Action:     ${result.suggestedAction}`);
      console.log(`Confidence: ${(result.confidence * 100).toFixed(0)}%`);
    } catch (err) {
      console.error("❌ Triage failed:", err);
      process.exit(1);
    }
  });

triageCmd
  .command("review")
  .description("AI-powered code review of git diff")
  .option("--base <ref>", "Base ref for diff", "main")
  .option("--head <ref>", "Head ref for diff", "HEAD")
  .option("--model <model>", "Claude model to use", getDefaultModel())
  .action(async (opts) => {
    const { execSync } = await import("node:child_process");
    
    const diff = execSync(`git diff ${opts.base}...${opts.head}`, { encoding: "utf-8" });
    
    if (!diff.trim()) {
      console.log("No changes to review");
      return;
    }

    const analyzer = new AIAnalyzer({ model: opts.model });
    
    console.log(`🔍 Reviewing diff ${opts.base}...${opts.head}...`);
    
    try {
      const review = await analyzer.reviewCode(diff);
      
      console.log("\n=== Code Review ===\n");
      console.log(`Ready to merge: ${review.readyToMerge ? "✅ YES" : "❌ NO"}`);
      
      if (review.mergeBlockers.length > 0) {
        console.log("\n🚫 Merge Blockers:");
        for (const blocker of review.mergeBlockers) {
          console.log(`   - ${blocker}`);
        }
      }
      
      console.log(`\n📋 Issues (${review.issues.length}):`);
      for (const issue of review.issues) {
        const icon = issue.severity === "critical" ? "🔴" : 
                     issue.severity === "high" ? "🟠" :
                     issue.severity === "medium" ? "🟡" : "⚪";
        console.log(`   ${icon} [${issue.category}] ${issue.file}${issue.line ? `:${issue.line}` : ""}`);
        console.log(`      ${issue.description}`);
      }
      
      console.log("\n📝 Overall Assessment:");
      console.log(`   ${review.overallAssessment}`);
    } catch (err) {
      console.error("❌ Review failed:", err);
      process.exit(1);
    }
  });

triageCmd
  .command("analyze")
  .description("Analyze agent conversation")
  .argument("<agent-id>", "Agent ID to analyze")
  .option("-o, --output <path>", "Output report path")
  .option("--create-issues", "Create GitHub issues from outstanding tasks")
  .option("--dry-run", "Show what issues would be created")
  .option("--model <model>", "Claude model to use", getDefaultModel())
  .action(async (agentId, opts) => {
    const fleet = new Fleet();
    const analyzer = new AIAnalyzer({ model: opts.model });

    console.log(`🔍 Fetching conversation for ${agentId}...`);
    const conv = await fleet.conversation(agentId);
    
    if (!conv.success || !conv.data) {
      console.error(`❌ ${conv.error}`);
      process.exit(1);
    }

    console.log(`📊 Analyzing ${conv.data.messages?.length ?? 0} messages...`);
    
    try {
      const analysis = await analyzer.analyzeConversation(conv.data);
      
      console.log("\n=== Analysis Summary ===\n");
      console.log(analysis.summary);
      
      console.log(`\n✅ Completed: ${analysis.completedTasks.length}`);
      console.log(`📋 Outstanding: ${analysis.outstandingTasks.length}`);
      console.log(`⚠️ Blockers: ${analysis.blockers.length}`);

      if (opts.output) {
        const report = await analyzer.generateReport(conv.data);
        writeFileSync(opts.output, report);
        console.log(`\n📝 Report saved to ${opts.output}`);
      }

      if (opts.createIssues || opts.dryRun) {
        console.log("\n🎫 Creating GitHub Issues...");
        const issues = await analyzer.createIssuesFromAnalysis(analysis, { 
          dryRun: opts.dryRun,
        });
        console.log(`Created ${issues.length} issues`);
      }
    } catch (err) {
      console.error("❌ Analysis failed:", err);
      process.exit(1);
    }
  });

// ============================================
// Handoff Commands
// ============================================

const handoffCmd = program
  .command("handoff")
  .description("Station-to-station agent handoff");

handoffCmd
  .command("initiate")
  .description("Initiate handoff to successor agent")
  .argument("<predecessor-id>", "Your agent ID (predecessor)")
  .requiredOption("--pr <number>", "Your current PR number")
  .requiredOption("--branch <name>", "Your current branch name")
  .option("--repo <url>", "Repository URL for successor", "https://github.com/jbcom/jbcom-control-center")
  .option("--ref <ref>", "Git ref for successor", "main")
  .option("--tasks <tasks>", "Comma-separated tasks for successor", "")
  .action(async (predecessorId, opts) => {
    const manager = new HandoffManager();
    
    console.log("🤝 Initiating station-to-station handoff...\n");
    
    const result = await manager.initiateHandoff(predecessorId, {
      repository: opts.repo,
      ref: opts.ref,
      currentPr: parseInt(opts.pr, 10),
      currentBranch: opts.branch,
      tasks: opts.tasks ? opts.tasks.split(",").map((t: string) => t.trim()) : [],
    });

    if (!result.success) {
      console.error(`❌ Handoff failed: ${result.error}`);
      process.exit(1);
    }

    console.log(`\n✅ Handoff initiated`);
    console.log(`   Successor: ${result.successorId}`);
    console.log(`   Healthy: ${result.successorHealthy ? "Yes" : "Pending"}`);
  });

handoffCmd
  .command("confirm")
  .description("Confirm health as successor agent")
  .argument("<predecessor-id>", "Predecessor agent ID")
  .action(async (predecessorId) => {
    const manager = new HandoffManager();
    const successorId = process.env.CURSOR_AGENT_ID || "successor-agent";
    
    console.log(`🤝 Confirming health to predecessor ${predecessorId}...`);
    await manager.confirmHealthAndBegin(successorId, predecessorId);
    console.log("✅ Health confirmation sent");
  });

handoffCmd
  .command("takeover")
  .description("Merge predecessor PR and take over")
  .argument("<predecessor-id>", "Predecessor agent ID")
  .argument("<pr-number>", "Predecessor PR number")
  .argument("<new-branch>", "Your new branch name")
  .option("--admin", "Use admin privileges")
  .option("--auto", "Enable auto-merge")
  .option("--merge-method <method>", "Merge method (merge|squash|rebase)", "squash")
  .action(async (predecessorId, prNumber, newBranch, opts) => {
    const manager = new HandoffManager();
    
    console.log("🔄 Taking over from predecessor...\n");
    
    const result = await manager.takeover(
      predecessorId,
      parseInt(prNumber, 10),
      newBranch,
      {
        admin: opts.admin,
        auto: opts.auto,
        mergeMethod: opts.mergeMethod as "merge" | "squash" | "rebase",
        deleteBranch: true,
      }
    );

    if (!result.success) {
      console.error(`❌ Takeover failed: ${result.error}`);
      process.exit(1);
    }

    console.log("✅ Takeover complete!");
  });

// ============================================
// Config Commands
// ============================================

program
  .command("config")
  .description("Show current configuration")
  .option("--json", "Output as JSON")
  .action((opts) => {
    const config = {
      defaultModel: getDefaultModel(),
      configuredOrgs: getConfiguredOrgs(),
      tokens: getTokenSummary(),
    };
    
    if (opts.json) {
      output(config, true);
    } else {
      console.log("=== Configuration ===\n");
      console.log(`Default Model: ${config.defaultModel}`);
      console.log(`Configured Orgs: ${config.configuredOrgs.join(", ")}`);
      console.log("\nToken Status:");
      for (const [org, info] of Object.entries(config.tokens)) {
        const status = info.available ? "✅" : "❌";
        console.log(`  ${status} ${org}: ${info.envVar}`);
      }
    }
  });

// ============================================
// Parse and Run
// ============================================

// Initialize config
initConfig();

// Parse CLI
program.parse();
