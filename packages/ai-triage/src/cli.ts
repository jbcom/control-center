#!/usr/bin/env node
/**
 * AI Triage CLI
 * 
 * Command-line interface for AI-powered PR and issue triage.
 * Integrates MCP servers (Cursor, GitHub, Context7) with Vercel AI SDK.
 */

import { Command } from "commander";
import { PRTriageAgent } from "./pr-triage-agent.js";
import { UnifiedAgent, runTask } from "./unified-agent.js";
import { initializeMCPClients, getMCPTools, closeMCPClients } from "./mcp-clients.js";

const program = new Command();

program
  .name("ai-triage")
  .description("AI-powered PR and issue triage with MCP integration")
  .version("0.1.0");

// ─────────────────────────────────────────────────────────────────
// PR Commands
// ─────────────────────────────────────────────────────────────────

const pr = program.command("pr").description("PR triage commands");

pr.command("analyze <pr-number>")
  .description("Analyze a PR and show detailed status")
  .option("-r, --repo <repo>", "Repository (owner/repo)", process.env.GITHUB_REPOSITORY)
  .option("-v, --verbose", "Verbose output")
  .action(async (prNumber: string, options) => {
    const repo = options.repo;
    if (!repo) {
      console.error("❌ Repository required. Use --repo or set GITHUB_REPOSITORY");
      process.exit(1);
    }

    console.log(`🔍 Analyzing PR #${prNumber} in ${repo}...\n`);

    const agent = new PRTriageAgent({
      repository: repo,
      verbose: options.verbose,
    });

    try {
      const analysis = await agent.analyze(parseInt(prNumber, 10));
      
      console.log(`\n📊 Analysis Results\n${"─".repeat(50)}`);
      console.log(`Status: ${analysis.status}`);
      console.log(`CI: ${analysis.ci.status}`);
      console.log(`Feedback: ${analysis.feedback.unaddressed}/${analysis.feedback.total} unaddressed`);
      console.log(`Blockers: ${analysis.blockers.length}`);
      
      console.log(`\n📋 Summary\n${analysis.summary}`);
      
      if (analysis.nextActions.length > 0) {
        console.log(`\n📌 Next Actions:`);
        for (const action of analysis.nextActions) {
          const icon = action.automated ? "🤖" : "👤";
          console.log(`  ${icon} [${action.priority}] ${action.action}`);
        }
      }
    } catch (error) {
      console.error("❌ Analysis failed:", error instanceof Error ? error.message : error);
      process.exit(1);
    } finally {
      await agent.close();
    }
  });

pr.command("report <pr-number>")
  .description("Generate a full triage report for a PR")
  .option("-r, --repo <repo>", "Repository (owner/repo)", process.env.GITHUB_REPOSITORY)
  .option("-o, --output <file>", "Output file (default: stdout)")
  .action(async (prNumber: string, options) => {
    const repo = options.repo;
    if (!repo) {
      console.error("❌ Repository required. Use --repo or set GITHUB_REPOSITORY");
      process.exit(1);
    }

    const agent = new PRTriageAgent({ repository: repo });

    try {
      const report = await agent.generateReport(parseInt(prNumber, 10));
      
      if (options.output) {
        const { writeFileSync } = await import("fs");
        writeFileSync(options.output, report);
        console.log(`✅ Report saved to ${options.output}`);
      } else {
        console.log(report);
      }
    } catch (error) {
      console.error("❌ Report generation failed:", error instanceof Error ? error.message : error);
      process.exit(1);
    } finally {
      await agent.close();
    }
  });

pr.command("resolve <pr-number>")
  .description("Automatically resolve issues in a PR")
  .option("-r, --repo <repo>", "Repository (owner/repo)", process.env.GITHUB_REPOSITORY)
  .option("-v, --verbose", "Verbose output")
  .action(async (prNumber: string, options) => {
    const repo = options.repo;
    if (!repo) {
      console.error("❌ Repository required. Use --repo or set GITHUB_REPOSITORY");
      process.exit(1);
    }

    console.log(`🔧 Resolving issues in PR #${prNumber}...\n`);

    const agent = new PRTriageAgent({
      repository: repo,
      verbose: options.verbose,
    });

    try {
      const result = await agent.resolve(parseInt(prNumber, 10));
      
      if (result.success) {
        console.log(`\n✅ Resolution complete`);
        console.log(result.result);
      } else {
        console.error(`\n❌ Resolution failed: ${result.result}`);
      }

      if (result.steps.length > 0) {
        console.log(`\n📝 Steps taken: ${result.steps.length}`);
        if (options.verbose) {
          for (const step of result.steps) {
            console.log(`  - ${step.toolName}`);
          }
        }
      }
    } catch (error) {
      console.error("❌ Resolution failed:", error instanceof Error ? error.message : error);
      process.exit(1);
    } finally {
      await agent.close();
    }
  });

pr.command("run <pr-number>")
  .description("Run full triage workflow until PR is ready")
  .option("-r, --repo <repo>", "Repository (owner/repo)", process.env.GITHUB_REPOSITORY)
  .option("-i, --iterations <n>", "Max iterations", "5")
  .option("--request-reviews", "Request reviews when ready")
  .option("--auto-merge", "Auto-merge when ready")
  .option("-v, --verbose", "Verbose output")
  .action(async (prNumber: string, options) => {
    const repo = options.repo;
    if (!repo) {
      console.error("❌ Repository required. Use --repo or set GITHUB_REPOSITORY");
      process.exit(1);
    }

    console.log(`🚀 Running triage workflow for PR #${prNumber}...\n`);

    const agent = new PRTriageAgent({
      repository: repo,
      verbose: options.verbose,
    });

    try {
      const result = await agent.runUntilReady(parseInt(prNumber, 10), {
        maxIterations: parseInt(options.iterations, 10),
        requestReviews: options.requestReviews,
        autoMerge: options.autoMerge,
      });

      console.log(`\n${"═".repeat(60)}`);
      console.log(result.report);
      console.log(`${"═".repeat(60)}`);

      if (result.success) {
        console.log(`\n✅ PR is ready! (${result.iterations} iterations)`);
      } else {
        console.log(`\n⚠️ Could not make PR ready after ${result.iterations} iterations`);
        console.log(`   Final status: ${result.finalStatus}`);
      }
    } catch (error) {
      console.error("❌ Workflow failed:", error instanceof Error ? error.message : error);
      process.exit(1);
    } finally {
      await agent.close();
    }
  });

// ─────────────────────────────────────────────────────────────────
// Agent Commands
// ─────────────────────────────────────────────────────────────────

const agent = program.command("agent").description("AI agent commands");

agent.command("run <task>")
  .description("Run a task with the unified AI agent")
  .option("-d, --dir <directory>", "Working directory", process.cwd())
  .option("-s, --steps <n>", "Max steps", "25")
  .option("-v, --verbose", "Verbose output")
  .action(async (task: string, options) => {
    console.log(`🤖 Running task: ${task.slice(0, 100)}${task.length > 100 ? '...' : ''}\n`);

    try {
      const result = await runTask(task, {
        workingDirectory: options.dir,
        maxSteps: parseInt(options.steps, 10),
        verbose: options.verbose,
      });

      if (result.success) {
        console.log(`\n✅ Task completed\n`);
        console.log(result.result);
      } else {
        console.error(`\n❌ Task failed: ${result.result}`);
      }

      if (result.usage) {
        console.log(`\n📊 Usage: ${result.usage.totalTokens} tokens`);
      }
    } catch (error) {
      console.error("❌ Task failed:", error instanceof Error ? error.message : error);
      process.exit(1);
    }
  });

agent.command("stream <task>")
  .description("Run a task with streaming output")
  .option("-d, --dir <directory>", "Working directory", process.cwd())
  .option("-s, --steps <n>", "Max steps", "25")
  .action(async (task: string, options) => {
    const unified = new UnifiedAgent({
      workingDirectory: options.dir,
      maxSteps: parseInt(options.steps, 10),
    });

    try {
      for await (const chunk of unified.stream(task)) {
        process.stdout.write(chunk);
      }
      console.log();
    } catch (error) {
      console.error("\n❌ Task failed:", error instanceof Error ? error.message : error);
      process.exit(1);
    } finally {
      await unified.close();
    }
  });

// ─────────────────────────────────────────────────────────────────
// MCP Commands
// ─────────────────────────────────────────────────────────────────

const mcp = program.command("mcp").description("MCP server management");

mcp.command("list-tools")
  .description("List all available MCP tools")
  .option("--cursor", "Initialize Cursor MCP")
  .option("--github", "Initialize GitHub MCP")
  .option("--context7", "Initialize Context7 MCP")
  .action(async (options) => {
    console.log("🔌 Connecting to MCP servers...\n");

    const config: Record<string, Record<string, boolean>> = {};
    if (options.cursor) config.cursor = {};
    if (options.github) config.github = {};
    if (options.context7) config.context7 = {};

    // Default to all if none specified
    if (Object.keys(config).length === 0) {
      config.cursor = {};
      config.github = {};
      config.context7 = {};
    }

    const clients = await initializeMCPClients(config);

    try {
      const tools = await getMCPTools(clients);
      const toolNames = Object.keys(tools);

      console.log(`\n📦 Available Tools (${toolNames.length} total):\n`);
      
      for (const name of toolNames.sort()) {
        const t = tools[name] as { description?: string };
        console.log(`  • ${name}`);
        if (t.description) {
          console.log(`    ${t.description.slice(0, 80)}${t.description.length > 80 ? '...' : ''}`);
        }
      }
    } catch (error) {
      console.error("❌ Failed to list tools:", error instanceof Error ? error.message : error);
    } finally {
      await closeMCPClients(clients);
    }
  });

mcp.command("status")
  .description("Check MCP server connectivity")
  .action(async () => {
    console.log("🔍 Checking MCP servers...\n");

    const checks = [
      { name: "Cursor Agent MCP", env: "CURSOR_API_KEY" },
      { name: "GitHub MCP", env: "GITHUB_TOKEN or GITHUB_JBCOM_TOKEN" },
      { name: "Context7 MCP", env: "CONTEXT7_API_KEY (optional)" },
    ];

    for (const check of checks) {
      const hasEnv = check.env.split(" or ").some(e => process.env[e]);
      const status = hasEnv ? "✅" : "⚠️";
      console.log(`${status} ${check.name}`);
      console.log(`   Environment: ${check.env} ${hasEnv ? "(set)" : "(not set)"}`);
    }

    console.log("\n🔌 Testing connections...\n");

    try {
      const clients = await initializeMCPClients({
        cursor: process.env.CURSOR_API_KEY ? {} : undefined,
        github: process.env.GITHUB_TOKEN || process.env.GITHUB_JBCOM_TOKEN ? {} : undefined,
        context7: {},  // Context7 works without API key
      });

      const tools = await getMCPTools(clients);
      console.log(`\n✅ Connected! ${Object.keys(tools).length} tools available`);

      await closeMCPClients(clients);
    } catch (error) {
      console.error("❌ Connection failed:", error instanceof Error ? error.message : error);
    }
  });

// ─────────────────────────────────────────────────────────────────
// Quick Commands
// ─────────────────────────────────────────────────────────────────

program.command("fix <description>")
  .description("Quick fix: describe what needs fixing and let AI handle it")
  .option("-d, --dir <directory>", "Working directory", process.cwd())
  .action(async (description: string, options) => {
    console.log(`🔧 Fixing: ${description}\n`);

    const result = await runTask(
      `Fix the following issue: ${description}

Steps:
1. Understand the issue
2. Find the relevant code
3. Make the fix
4. Verify the fix works
5. Commit the changes with a descriptive message`,
      { workingDirectory: options.dir, verbose: true }
    );

    if (result.success) {
      console.log(`\n✅ Fix applied!\n${result.result}`);
    } else {
      console.error(`\n❌ Fix failed: ${result.result}`);
      process.exit(1);
    }
  });

program.command("review")
  .description("Review current changes and suggest improvements")
  .option("-d, --dir <directory>", "Working directory", process.cwd())
  .action(async (options) => {
    console.log("👀 Reviewing changes...\n");

    const result = await runTask(
      `Review the current git changes:
1. Run git status to see what's changed
2. Run git diff to see the actual changes
3. Analyze the changes for:
   - Potential bugs
   - Code style issues
   - Missing error handling
   - Security concerns
   - Performance issues
4. Provide a summary with specific suggestions`,
      { workingDirectory: options.dir }
    );

    console.log(result.result);
  });

program.command("docs <query>")
  .description("Look up documentation for a library or API")
  .action(async (query: string) => {
    console.log(`📚 Looking up: ${query}\n`);

    const clients = await initializeMCPClients({ context7: {} });

    try {
      const tools = await getMCPTools(clients);
      
      // Check if Context7 tools are available
      const c7Tools = Object.keys(tools).filter(t => t.includes("context7") || t.includes("resolve") || t.includes("get"));
      
      if (c7Tools.length === 0) {
        console.log("⚠️ Context7 MCP tools not available. Using general search...");
      }

      const result = await runTask(
        `Look up documentation for: ${query}

Use the Context7 MCP tools if available to get up-to-date documentation.
Provide a clear, concise summary of the relevant documentation.`,
        { mcp: { context7: {} } }
      );

      console.log(result.result);
    } finally {
      await closeMCPClients(clients);
    }
  });

// Parse and run
program.parse();
