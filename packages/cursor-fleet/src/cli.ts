#!/usr/bin/env node
/**
 * cursor-fleet CLI
 * 
 * Unified command-line interface for Cursor Background Agent fleet management.
 * Used by both FSC and jbcom control centers.
 */

import { Command } from "commander";
import { Fleet, type TaskAnalysis } from "./fleet.js";
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
    fleet.close();
  });

// ============================================
// replay
// ============================================
program
  .command("replay")
  .description("Replay agent conversation chronologically and analyze tasks")
  .argument("<agent-id>", "Agent ID")
  .option("-o, --output <dir>", "Output directory")
  .option("-v, --verbose", "Verbose output")
  .option("--json", "Output analysis as JSON")
  .option("--print", "Print full conversation to stdout")
  .option("--limit <n>", "Limit messages when printing", "50")
  .option("--filter <type>", "Filter messages: user, assistant, all", "all")
  .action(async (agentId, opts) => {
    const fleet = new Fleet({ timeout: 120000 }); // 2 min timeout for large conversations
    
    console.log(`\n🔄 Replaying agent ${agentId}...\n`);
    
    const result = await fleet.replay(agentId, {
      outputDir: opts.output,
      verbose: opts.verbose ?? true,
    });

    if (!result.success) {
      console.error(`❌ ${result.error}`);
      fleet.close();
      process.exit(1);
    }

    const { agent, conversation, archivePath, analysis } = result.data!;

    if (opts.json) {
      output(analysis, true);
    } else if (opts.print) {
      fleet.printReplay(conversation, {
        limit: parseInt(opts.limit, 10),
        filter: opts.filter as "user" | "assistant" | "all",
      });
    } else {
      printAnalysis(agent, analysis, archivePath);
    }

    fleet.close();
  });

// ============================================
// load-replay
// ============================================
program
  .command("load-replay")
  .description("Load a previously archived replay from disk")
  .argument("<archive-dir>", "Path to archive directory")
  .option("--json", "Output analysis as JSON")
  .option("--print", "Print full conversation to stdout")
  .option("--limit <n>", "Limit messages when printing", "50")
  .action(async (archiveDir, opts) => {
    const fleet = new Fleet();
    
    const result = await fleet.loadReplay(archiveDir);

    if (!result.success) {
      console.error(`❌ ${result.error}`);
      process.exit(1);
    }

    const { agent, conversation, archivePath, analysis } = result.data!;

    if (opts.json) {
      output(analysis, true);
    } else if (opts.print) {
      fleet.printReplay(conversation, {
        limit: parseInt(opts.limit, 10),
      });
    } else {
      printAnalysis(agent, analysis, archivePath);
    }
  });

/**
 * Print analysis results in a readable format
 */
function printAnalysis(agent: Agent, analysis: TaskAnalysis, archivePath: string): void {
  console.log(`\n${"═".repeat(70)}`);
  console.log(`  AGENT REPLAY ANALYSIS`);
  console.log(`${"═".repeat(70)}\n`);

  console.log(`📋 Agent: ${agent.name ?? "Unknown"}`);
  console.log(`🆔 ID: ${agent.id}`);
  console.log(`📊 Status: ${agent.status}`);
  console.log(`🕐 Duration: ${analysis.duration}`);
  console.log(`💬 Messages: ${analysis.messageCount}`);
  console.log(`📁 Archive: ${archivePath}`);
  
  console.log(`\n${"─".repeat(70)}`);
  console.log(`  SESSION SUMMARY`);
  console.log(`${"─".repeat(70)}\n`);
  console.log(analysis.sessionSummary);

  console.log(`\n${"─".repeat(70)}`);
  console.log(`  PRs (${analysis.prsCreated.length} created, ${analysis.prsMerged.length} merged)`);
  console.log(`${"─".repeat(70)}\n`);
  
  if (analysis.prsCreated.length > 0) {
    for (const pr of analysis.prsCreated) {
      const icon = pr.status === "merged" ? "✅" : pr.status === "closed" ? "❌" : "⏳";
      console.log(`  ${icon} #${pr.number}: ${pr.title}`);
    }
  } else {
    console.log("  (No PRs detected)");
  }

  console.log(`\n${"─".repeat(70)}`);
  console.log(`  COMPLETED TASKS (${analysis.completed.length})`);
  console.log(`${"─".repeat(70)}\n`);
  
  if (analysis.completed.length > 0) {
    for (const task of analysis.completed) {
      console.log(`  ✅ ${task.description}`);
    }
  } else {
    console.log("  (No explicitly marked completed tasks)");
  }

  console.log(`\n${"─".repeat(70)}`);
  console.log(`  OUTSTANDING TASKS (${analysis.outstanding.length})`);
  console.log(`${"─".repeat(70)}\n`);
  
  if (analysis.outstanding.length > 0) {
    for (const task of analysis.outstanding) {
      console.log(`  ⏳ ${task.description}`);
    }
  } else {
    console.log("  (No explicitly marked outstanding tasks)");
  }

  if (analysis.blockers.length > 0) {
    console.log(`\n${"─".repeat(70)}`);
    console.log(`  BLOCKERS (${analysis.blockers.length})`);
    console.log(`${"─".repeat(70)}\n`);
    for (const blocker of analysis.blockers) {
      console.log(`  ❌ ${blocker}`);
    }
  }

  if (analysis.keyDecisions.length > 0) {
    console.log(`\n${"─".repeat(70)}`);
    console.log(`  KEY DECISIONS (${analysis.keyDecisions.length})`);
    console.log(`${"─".repeat(70)}\n`);
    for (const decision of analysis.keyDecisions) {
      console.log(`  📌 ${decision}`);
    }
  }

  console.log(`\n${"═".repeat(70)}`);
  console.log(`  Files saved to: ${archivePath}`);
  console.log(`  - conversation.json`);
  console.log(`  - agent.json`);
  console.log(`  - analysis.json`);
  console.log(`  - REPLAY_SUMMARY.md`);
  console.log(`${"═".repeat(70)}\n`);
}

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

program.parse();
