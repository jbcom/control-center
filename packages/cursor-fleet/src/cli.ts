#!/usr/bin/env node
/**
 * cursor-fleet CLI
 * 
 * Unified command-line interface for Cursor Background Agent fleet management.
 * Uses direct Cursor API calls.
 */

import { Command } from "commander";
import { Fleet, type TaskAnalysis, type SplitResult } from "./fleet.js";
import type { Agent } from "./types.js";

const program = new Command();

program
  .name("cursor-fleet")
  .description("Cursor Background Agent fleet management")
  .version("0.2.0");

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
// replay - THE MAIN RECOVERY COMMAND
// ============================================
program
  .command("replay")
  .description("Replay agent conversation - fetch, archive, split, and analyze")
  .argument("<agent-id>", "Agent ID")
  .option("-o, --output <dir>", "Output directory")
  .option("-b, --batch-size <n>", "Messages per batch", "10")
  .option("-v, --verbose", "Verbose output")
  .option("--json", "Output analysis as JSON")
  .option("--print", "Print full conversation to stdout")
  .option("--limit <n>", "Limit messages when printing", "50")
  .action(async (agentId, opts) => {
    const fleet = new Fleet({ timeout: 180000 }); // 3 min timeout for large conversations
    
    console.log(`\n🔄 Replaying agent ${agentId}...\n`);
    
    const result = await fleet.replay(agentId, {
      outputDir: opts.output,
      verbose: opts.verbose ?? true,
      batchSize: parseInt(opts.batchSize, 10),
    });

    if (!result.success) {
      console.error(`❌ ${result.error}`);
      process.exit(1);
    }

    const { agent, conversation, archivePath, analysis, split } = result.data!;

    if (opts.json) {
      output(analysis, true);
    } else if (opts.print) {
      fleet.printReplay(conversation, { limit: parseInt(opts.limit, 10) });
    } else {
      printAnalysis(agent, analysis, archivePath, split);
    }
  });

// ============================================
// split - Split existing conversation JSON
// ============================================
program
  .command("split")
  .description("Split an existing conversation.json into readable chunks")
  .argument("<conversation-json>", "Path to conversation.json file")
  .option("-o, --output <dir>", "Output directory (defaults to same dir as input)")
  .option("-b, --batch-size <n>", "Messages per batch", "10")
  .action(async (conversationPath, opts) => {
    const fleet = new Fleet();
    
    console.log(`\n📂 Splitting ${conversationPath}...\n`);
    
    const result = await fleet.splitExisting(
      conversationPath,
      opts.output,
      parseInt(opts.batchSize, 10)
    );

    if (!result.success) {
      console.error(`❌ ${result.error}`);
      process.exit(1);
    }

    const split = result.data!;
    console.log(`✅ Split complete!`);
    console.log(`   📁 Output: ${split.outputDir}`);
    console.log(`   💬 Messages: ${split.messageCount}`);
    console.log(`   📦 Batches: ${split.batchCount}`);
    console.log(`   📄 Index: ${split.files.index}`);
  });

// ============================================
// load-replay - Load archived replay
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

    const { agent, conversation, archivePath, analysis, split } = result.data!;

    if (opts.json) {
      output(analysis, true);
    } else if (opts.print) {
      fleet.printReplay(conversation, { limit: parseInt(opts.limit, 10) });
    } else {
      printAnalysis(agent, analysis, archivePath, split);
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
  .option("--json", "Output as JSON")
  .action(async (repo, task, opts) => {
    const fleet = new Fleet();
    
    const result = await fleet.spawn({
      repository: repo,
      task,
      ref: opts.ref,
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
    }
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
// Helper: Print analysis
// ============================================
function printAnalysis(agent: Agent, analysis: TaskAnalysis, archivePath: string, split: SplitResult): void {
  console.log(`\n${"═".repeat(70)}`);
  console.log(`  AGENT REPLAY ANALYSIS`);
  console.log(`${"═".repeat(70)}\n`);

  console.log(`📋 Agent: ${agent.name ?? "Unknown"}`);
  console.log(`🆔 ID: ${agent.id}`);
  console.log(`📊 Status: ${agent.status}`);
  console.log(`🕐 Duration: ${analysis.duration}`);
  console.log(`💬 Messages: ${analysis.messageCount}`);
  console.log(`📦 Batches: ${split.batchCount}`);
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

  console.log(`\n${"═".repeat(70)}`);
  console.log(`  HOW TO READ THE CONVERSATION`);
  console.log(`${"═".repeat(70)}\n`);
  console.log(`  1. Index:      ${archivePath}/INDEX.md`);
  console.log(`  2. Batches:    ${archivePath}/batches/batch-*.md`);
  console.log(`  3. Individual: ${archivePath}/messages/####-*.md`);
  console.log(`  4. Summary:    ${archivePath}/REPLAY_SUMMARY.md`);
  console.log(`\n${"═".repeat(70)}\n`);
}

program.parse();
