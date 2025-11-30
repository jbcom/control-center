#!/usr/bin/env node
/**
 * cursor-fleet CLI
 * 
 * Unified command-line interface for Cursor Background Agent fleet management.
 * Used by both FSC and jbcom control centers.
 */

import { Command } from "commander";
import { writeFileSync } from "node:fs";
import { Fleet } from "./fleet.js";
import { AIAnalyzer } from "./ai-analyzer.js";
import { HandoffManager } from "./handoff.js";
import type { Agent } from "./types.js";

const program = new Command();

program
  .name("cursor-fleet")
  .description("Cursor Background Agent fleet management")
  .version("0.1.0");

// Helper for JSON output
function output(data: unknown, json: boolean): void {
  if (json) {
    console.log(JSON.stringify(data, null, 2));
  } else if (typeof data === "string") {
    console.log(data);
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
// list
// ============================================
program
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

// ============================================
// spawn
// ============================================
program
  .command("spawn")
  .description("Spawn a new agent")
  .argument("<repo>", "Repository URL (https://github.com/org/repo)")
  .argument("<task>", "Task description")
  .option("--ref <ref>", "Git ref", "main")
  .option("--context <json>", "Spawn context as JSON")
  .option("--json", "Output as JSON")
  .action(async (repo, task, opts) => {
    const fleet = new Fleet();
    
    let context;
    if (opts.context) {
      try {
        context = JSON.parse(opts.context);
      } catch {
        console.error("❌ Invalid JSON in --context");
        process.exit(1);
      }
    }

    const result = await fleet.spawn({
      repository: repo,
      task,
      ref: opts.ref,
      context,
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
      console.log(`Branch: ${result.data?.target?.branchName ?? "pending"}`);
      console.log(`URL:    ${result.data?.target?.url ?? "pending"}`);
    }
  });

// ============================================
// status
// ============================================
program
  .command("status")
  .description("Get agent status")
  .argument("<agent-id>", "Agent ID")
  .option("--json", "Output as JSON")
  .action(async (agentId, opts) => {
    const fleet = new Fleet();
    const result = await fleet.status(agentId);

    if (!result.success) {
      console.error(`❌ ${result.error}`);
      process.exit(1);
    }

    output(result.data, opts.json);
  });

// ============================================
// followup
// ============================================
program
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

// ============================================
// broadcast
// ============================================
program
  .command("broadcast")
  .description("Send message to multiple agents")
  .argument("<message>", "Message to send")
  .option("--agents <ids>", "Comma-separated agent IDs")
  .option("--running", "Send to all running agents")
  .action(async (message, opts) => {
    const fleet = new Fleet();
    
    let agentIds: string[];
    if (opts.running) {
      const running = await fleet.running();
      agentIds = running.data?.map(a => a.id) ?? [];
    } else if (opts.agents) {
      agentIds = opts.agents.split(",").map((s: string) => s.trim());
    } else {
      console.error("❌ Specify --agents or --running");
      process.exit(1);
    }

    if (agentIds.length === 0) {
      console.log("No agents to broadcast to");
      return;
    }

    const results = await fleet.broadcast(agentIds, message);
    
    for (const [id, result] of results) {
      const status = result.success ? "✅" : "❌";
      console.log(`${status} ${id}`);
    }
  });

// ============================================
// conversation
// ============================================
program
  .command("conversation")
  .description("Get agent conversation")
  .argument("<agent-id>", "Agent ID")
  .option("--json", "Output as JSON")
  .option("--last <n>", "Show last N messages", "20")
  .action(async (agentId, opts) => {
    const fleet = new Fleet();
    const result = await fleet.conversation(agentId);

    if (!result.success) {
      console.error(`❌ ${result.error}`);
      process.exit(1);
    }

    if (opts.json) {
      output(result.data, true);
    } else {
      const messages = result.data?.messages ?? [];
      const last = parseInt(opts.last, 10);
      const shown = messages.slice(-last);
      
      console.log(`=== Conversation: ${agentId} (${messages.length} messages) ===\n`);
      
      for (const msg of shown) {
        const role = msg.type === "user_message" ? "USER" : "ASST";
        const text = msg.text.slice(0, 200).replace(/\n/g, " ");
        console.log(`[${role}] ${text}${msg.text.length > 200 ? "..." : ""}\n`);
      }
    }
  });

// ============================================
// archive
// ============================================
program
  .command("archive")
  .description("Archive agent conversation to disk")
  .argument("<agent-id>", "Agent ID")
  .option("-o, --output <path>", "Output file path")
  .action(async (agentId, opts) => {
    const fleet = new Fleet();
    const result = await fleet.archive(agentId, opts.output);

    if (!result.success) {
      console.error(`❌ ${result.error}`);
      process.exit(1);
    }

    console.log(`✅ Archived to ${result.data}`);
  });

// ============================================
// split
// ============================================
program
  .command("split")
  .description("Split conversation into readable files")
  .argument("<agent-id>", "Agent ID")
  .option("-o, --output <dir>", "Output directory")
  .action(async (agentId, opts) => {
    const fleet = new Fleet();
    const result = await fleet.split(agentId, opts.output);

    if (!result.success) {
      console.error(`❌ ${result.error}`);
      process.exit(1);
    }

    console.log(`✅ Split conversation for ${agentId}`);
    console.log(`   Messages: ${result.data?.totalMessages}`);
    console.log(`   Batches: ${result.data?.batchFiles}`);
    console.log(`   Output: ${result.data?.outputDir}`);
  });

// ============================================
// repos
// ============================================
program
  .command("repos")
  .description("List available repositories")
  .option("--json", "Output as JSON")
  .action(async (opts) => {
    const fleet = new Fleet();
    const result = await fleet.repositories();

    if (!result.success) {
      console.error(`❌ ${result.error}`);
      process.exit(1);
    }

    if (opts.json) {
      output(result.data, true);
    } else {
      console.log("=== Available Repositories ===\n");
      for (const repo of (result.data ?? []).slice(0, 50)) {
        console.log(`  ${repo.owner}/${repo.name}`);
      }
      if ((result.data?.length ?? 0) > 50) {
        console.log(`\n  ... and ${(result.data?.length ?? 0) - 50} more`);
      }
    }
  });

// ============================================
// summary
// ============================================
program
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

// ============================================
// diamond
// ============================================
program
  .command("diamond")
  .description("Create diamond pattern orchestration")
  .requiredOption("--targets <json>", "Target repos as JSON array [{repository, task, ref?}]")
  .requiredOption("--counterparty <json>", "Counterparty as JSON {repository, task, ref?}")
  .requiredOption("--control-center <name>", "Control center name")
  .option("--json", "Output as JSON")
  .action(async (opts) => {
    let targets, counterparty;
    try {
      targets = JSON.parse(opts.targets);
      counterparty = JSON.parse(opts.counterparty);
    } catch {
      console.error("❌ Invalid JSON in --targets or --counterparty");
      process.exit(1);
    }

    const fleet = new Fleet();
    const result = await fleet.createDiamond({
      targetRepos: targets,
      counterparty,
      controlCenter: opts.controlCenter,
    });

    if (!result.success) {
      console.error(`❌ ${result.error}`);
      process.exit(1);
    }

    if (opts.json) {
      output(result.data, true);
    } else {
      console.log("=== Diamond Pattern Created ===\n");
      console.log("Target Agents:");
      for (const agent of result.data?.targetAgents ?? []) {
        console.log(`  ${agent.id} → ${agent.source.repository}`);
      }
      console.log(`\nCounterparty Agent:`);
      console.log(`  ${result.data?.counterpartyAgent.id} → ${result.data?.counterpartyAgent.source.repository}`);
    }
  });

// ============================================
// wait
// ============================================
program
  .command("wait")
  .description("Wait for agent to complete")
  .argument("<agent-id>", "Agent ID")
  .option("--timeout <ms>", "Timeout in milliseconds", "300000")
  .option("--poll <ms>", "Poll interval in milliseconds", "10000")
  .action(async (agentId, opts) => {
    const fleet = new Fleet();
    
    console.log(`Waiting for ${agentId}...`);
    
    const result = await fleet.waitFor(agentId, {
      timeout: parseInt(opts.timeout, 10),
      pollInterval: parseInt(opts.poll, 10),
    });

    if (!result.success) {
      console.error(`❌ ${result.error}`);
      process.exit(1);
    }

    console.log(`✅ Agent finished with status: ${result.data?.status}`);
  });

// ============================================
// watch
// ============================================
program
  .command("watch")
  .description("Watch fleet and report status changes")
  .option("--poll <ms>", "Poll interval in milliseconds", "30000")
  .option("--iterations <n>", "Max iterations (default: infinite)", "0")
  .option("--stall <ms>", "Stall threshold in milliseconds", "600000")
  .action(async (opts) => {
    const fleet = new Fleet();
    const pollInterval = parseInt(opts.poll, 10);
    const maxIterations = parseInt(opts.iterations, 10) || Infinity;
    const stallThreshold = parseInt(opts.stall, 10);

    console.log("=== Fleet Watch Started ===");
    console.log(`Poll interval: ${pollInterval}ms`);
    console.log(`Stall threshold: ${stallThreshold}ms`);
    console.log("");

    await fleet.watch({
      pollInterval,
      maxIterations,
      stallThreshold,
      onAgentFinished: async (agent) => {
        console.log(`\n✅ FINISHED: ${agent.id}`);
        console.log(`   Name: ${agent.name}`);
        console.log(`   Summary: ${agent.summary?.slice(0, 200) ?? 'No summary available'}`);
        console.log("");
      },
      onAgentFailed: async (agent) => {
        console.log(`\n❌ FAILED: ${agent.id}`);
        console.log(`   Name: ${agent.name}`);
        console.log("");
      },
      onAgentStalled: async (agent, runtime) => {
        const mins = Math.floor(runtime / 60000);
        console.log(`\n⚠️  STALLED: ${agent.id} (running ${mins}m)`);
        console.log(`   Name: ${agent.name}`);
        console.log("");
      },
    });
  });

// ============================================
// monitor
// ============================================
program
  .command("monitor")
  .description("Monitor specific agents until completion")
  .argument("<agent-ids...>", "Agent IDs to monitor")
  .option("--poll <ms>", "Poll interval in milliseconds", "15000")
  .action(async (agentIds, opts) => {
    const fleet = new Fleet();
    const pollInterval = parseInt(opts.poll, 10);

    console.log(`=== Monitoring ${agentIds.length} agents ===\n`);

    const results = await fleet.monitorAgents(agentIds, {
      pollInterval,
      onProgress: (status) => {
        const line = Array.from(status.entries())
          .map(([id, s]) => `${id.slice(0, 8)}: ${s}`)
          .join(" | ");
        process.stdout.write(`\r${line}    `);
      },
    });

    console.log("\n\n=== Results ===\n");
    for (const [id, agent] of results) {
      // Both FINISHED and COMPLETED are successful terminal states
      const status = (agent.status === "FINISHED" || agent.status === "COMPLETED") ? "✅" : "❌";
      console.log(`${status} ${id}: ${agent.status}`);
    }
  });

// ============================================
// coordinate
// ============================================
program
  .command("coordinate")
  .description("Run the bidirectional fleet coordinator")
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
// analyze - AI-powered conversation analysis
// ============================================
program
  .command("analyze")
  .description("AI-powered analysis of agent conversation")
  .argument("<agent-id>", "Agent ID to analyze")
  .option("-o, --output <path>", "Output report path")
  .option("--create-issues", "Create GitHub issues from outstanding tasks")
  .option("--dry-run", "Show what issues would be created without creating them")
  .option("--no-copilot", "Don't add copilot label to issues")
  .option("--model <model>", "Claude model to use", "claude-sonnet-4-20250514")
  .action(async (agentId, opts) => {
    const fleet = new Fleet();
    const analyzer = new AIAnalyzer({ model: opts.model });

    console.log(`🔍 Fetching conversation for ${agentId}...`);
    const conv = await fleet.conversation(agentId);
    
    if (!conv.success || !conv.data) {
      console.error(`❌ ${conv.error}`);
      process.exit(1);
    }

    console.log(`📊 Analyzing ${conv.data.messages?.length ?? 0} messages with Claude ${opts.model}...`);
    
    try {
      const analysis = await analyzer.analyzeConversation(conv.data);
      
      console.log("\n=== Analysis Summary ===\n");
      console.log(analysis.summary);
      
      console.log(`\n✅ Completed Tasks: ${analysis.completedTasks.length}`);
      for (const task of analysis.completedTasks) {
        console.log(`   - ${task.title}`);
      }
      
      console.log(`\n📋 Outstanding Tasks: ${analysis.outstandingTasks.length}`);
      for (const task of analysis.outstandingTasks) {
        console.log(`   [${task.priority.toUpperCase()}] ${task.title}`);
      }
      
      console.log(`\n⚠️  Blockers: ${analysis.blockers.length}`);
      for (const blocker of analysis.blockers) {
        console.log(`   [${blocker.severity}] ${blocker.issue}`);
      }

      // Generate full report
      const report = await analyzer.generateReport(conv.data);
      
      if (opts.output) {
        writeFileSync(opts.output, report);
        console.log(`\n📝 Report saved to ${opts.output}`);
      }

      // Create issues if requested
      if (opts.createIssues || opts.dryRun) {
        console.log("\n🎫 Creating GitHub Issues...");
        if (opts.copilot !== false) {
          console.log("   (Adding 'copilot' label for automatic PR creation)");
        }
        const issues = await analyzer.createIssuesFromAnalysis(analysis, { 
          dryRun: opts.dryRun,
          assignCopilot: opts.copilot !== false,
        });
        console.log(`Created ${issues.length} issues`);
      }
    } catch (err) {
      console.error("❌ Analysis failed:", err);
      process.exit(1);
    }
  });

// ============================================
// triage - Quick AI triage of input
// ============================================
program
  .command("triage")
  .description("Quick AI triage of text input")
  .argument("<input>", "Text to triage (or - for stdin)")
  .option("--model <model>", "Claude model to use", "claude-sonnet-4-20250514")
  .action(async (input, opts) => {
    let text = input;
    if (input === "-") {
      // Read from stdin
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
      console.log(`Priority:  ${result.priority.toUpperCase()}`);
      console.log(`Category:  ${result.category}`);
      console.log(`Summary:   ${result.summary}`);
      console.log(`Action:    ${result.suggestedAction}`);
    } catch (err) {
      console.error("❌ Triage failed:", err);
      process.exit(1);
    }
  });

// ============================================
// review - AI code review
// ============================================
program
  .command("review")
  .description("AI-powered code review of git diff")
  .option("--base <ref>", "Base ref for diff", "main")
  .option("--head <ref>", "Head ref for diff", "HEAD")
  .option("--model <model>", "Claude model to use", "claude-sonnet-4-20250514")
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
        if (issue.suggestedFix) {
          console.log(`      💡 ${issue.suggestedFix}`);
        }
      }
      
      console.log(`\n💡 Improvements (${review.improvements.length}):`);
      for (const imp of review.improvements) {
        console.log(`   [${imp.effort}] ${imp.area}: ${imp.suggestion}`);
      }
      
      console.log("\n📝 Overall Assessment:");
      console.log(`   ${review.overallAssessment}`);
    } catch (err) {
      console.error("❌ Review failed:", err);
      process.exit(1);
    }
  });

// ============================================
// handoff - Station-to-station handoff
// ============================================
const handoffCmd = program
  .command("handoff")
  .description("Station-to-station agent handoff commands");

handoffCmd
  .command("initiate")
  .description("Initiate handoff to successor agent")
  .argument("<predecessor-id>", "Your agent ID (predecessor)")
  .requiredOption("--pr <number>", "Your current PR number")
  .requiredOption("--branch <name>", "Your current branch name")
  .option("--repo <url>", "Repository URL for successor", "https://github.com/jbcom/jbcom-control-center")
  .option("--ref <ref>", "Git ref for successor", "main")
  .option("--tasks <tasks>", "Comma-separated tasks for successor", "")
  .option("--timeout <ms>", "Health check timeout", "300000")
  .action(async (predecessorId, opts) => {
    const manager = new HandoffManager();
    
    console.log("🤝 Initiating station-to-station handoff...\n");
    
    const result = await manager.initiateHandoff(predecessorId, {
      repository: opts.repo,
      ref: opts.ref,
      currentPr: parseInt(opts.pr, 10),
      currentBranch: opts.branch,
      tasks: opts.tasks ? opts.tasks.split(",").map((t: string) => t.trim()) : [],
      healthCheckTimeout: parseInt(opts.timeout, 10),
    });

    if (!result.success) {
      console.error(`❌ Handoff failed: ${result.error}`);
      process.exit(1);
    }

    console.log(`\n✅ Handoff initiated`);
    console.log(`   Successor: ${result.successorId}`);
    console.log(`   Healthy: ${result.successorHealthy ? "Yes" : "Pending confirmation"}`);
  });

handoffCmd
  .command("confirm")
  .description("Confirm health as successor agent")
  .argument("<predecessor-id>", "Predecessor agent ID to confirm to")
  .action(async (predecessorId) => {
    const manager = new HandoffManager();
    
    // Get our own agent ID from environment or infer
    const successorId = process.env.CURSOR_AGENT_ID || "successor-agent";
    
    console.log(`🤝 Confirming health to predecessor ${predecessorId}...`);
    await manager.confirmHealthAndBegin(successorId, predecessorId);
    console.log("✅ Health confirmation sent");
    console.log("\nNext steps:");
    console.log("  1. Review .cursor/handoff/${predecessorId}/ for context");
    console.log("  2. Run: cursor-fleet handoff takeover <predecessor-id> <pr-number> <new-branch>");
  });

handoffCmd
  .command("takeover")
  .description("Merge predecessor PR and take over")
  .argument("<predecessor-id>", "Predecessor agent ID")
  .argument("<pr-number>", "Predecessor PR number to merge")
  .argument("<new-branch>", "Your new branch name")
  .action(async (predecessorId, prNumber, newBranch) => {
    const manager = new HandoffManager();
    
    console.log("🔄 Taking over from predecessor...\n");
    
    const result = await manager.takeover(
      predecessorId,
      parseInt(prNumber, 10),
      newBranch
    );

    if (!result.success) {
      console.error(`❌ Takeover failed: ${result.error}`);
      process.exit(1);
    }

    console.log("✅ Takeover complete!");
    console.log("\nYou are now the active agent.");
    console.log("Next steps:");
    console.log("  1. Create your hold-open PR");
    console.log("  2. Review outstanding tasks");
    console.log("  3. Continue the work");
  });

handoffCmd
  .command("status")
  .description("Check handoff status")
  .argument("<agent-id>", "Agent ID to check")
  .action(async (agentId) => {
    const { existsSync, readFileSync } = await import("node:fs");
    const { join } = await import("node:path");
    
    const handoffDir = join(".cursor", "handoff", agentId);
    const contextPath = join(handoffDir, "context.json");
    
    if (!existsSync(contextPath)) {
      console.log(`No handoff context found for ${agentId}`);
      return;
    }

    const context = JSON.parse(readFileSync(contextPath, "utf-8"));
    
    console.log("=== Handoff Context ===\n");
    console.log(`Predecessor: ${context.predecessorId}`);
    console.log(`PR: #${context.predecessorPr}`);
    console.log(`Branch: ${context.predecessorBranch}`);
    console.log(`Time: ${context.handoffTime}`);
    console.log(`\nCompleted Work: ${context.completedWork.length} items`);
    console.log(`Outstanding Tasks: ${context.outstandingTasks.length} items`);
    console.log(`Decisions: ${context.decisions.length} items`);
  });

program.parse();
