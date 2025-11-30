#!/usr/bin/env node

import { Command } from "commander";
import { Triage } from "./triage.js";

const program = new Command();

function getConfig() {
  const token = process.env.GITHUB_JBCOM_TOKEN || process.env.GITHUB_TOKEN || process.env.GH_TOKEN;
  if (!token) {
    console.error("Error: No GitHub token found. Set GITHUB_JBCOM_TOKEN, GITHUB_TOKEN, or GH_TOKEN");
    process.exit(1);
  }

  const repo = process.env.GITHUB_REPOSITORY || "jbcom/jbcom-control-center";
  const [owner, repoName] = repo.split("/");

  return {
    github: {
      token,
      owner,
      repo: repoName,
    },
    resolver: {
      workingDirectory: process.cwd(),
      dryRun: false,
    },
  };
}

program
  .name("ai-triage")
  .description("AI-powered PR and issue triage with automated resolution")
  .version("0.1.0");

// =============================================================================
// analyze command
// =============================================================================

program
  .command("analyze <pr-number>")
  .description("Analyze a PR and report its triage status")
  .option("-j, --json", "Output as JSON")
  .action(async (prNumber: string, options: { json?: boolean }) => {
    const config = getConfig();
    const triage = new Triage(config);

    console.error(`Analyzing PR #${prNumber}...`);

    const result = await triage.analyze(parseInt(prNumber));

    if (options.json) {
      console.log(JSON.stringify(result, null, 2));
    } else {
      console.log(triage.formatTriageReport(result));
    }
  });

// =============================================================================
// plan command
// =============================================================================

program
  .command("plan <pr-number>")
  .description("Generate a resolution plan without executing")
  .option("-j, --json", "Output as JSON")
  .action(async (prNumber: string, options: { json?: boolean }) => {
    const config = getConfig();
    const triage = new Triage(config);

    console.error(`Planning resolution for PR #${prNumber}...`);

    const plan = await triage.plan(parseInt(prNumber));

    if (options.json) {
      console.log(JSON.stringify(plan, null, 2));
    } else {
      console.log(`# Resolution Plan for PR #${plan.prNumber}`);
      console.log("");
      console.log(`Estimated duration: ${plan.estimatedTotalDuration}`);
      console.log(`Requires human intervention: ${plan.requiresHumanIntervention ? "Yes" : "No"}`);
      if (plan.humanInterventionReason) {
        console.log(`Reason: ${plan.humanInterventionReason}`);
      }
      console.log("");
      console.log("## Steps:");
      for (const step of plan.steps) {
        const icon = step.automated ? "🤖" : "👤";
        const deps = step.dependencies.length > 0 
          ? ` (after: ${step.dependencies.join(", ")})` 
          : "";
        console.log(`${step.order}. ${icon} ${step.action}${deps}`);
        console.log(`   ${step.description}`);
        console.log(`   Duration: ${step.estimatedDuration}`);
      }
    }
  });

// =============================================================================
// resolve command
// =============================================================================

program
  .command("resolve <pr-number>")
  .description("Resolve all auto-resolvable blockers and feedback")
  .option("--dry-run", "Show what would be done without making changes")
  .action(async (prNumber: string, options: { dryRun?: boolean }) => {
    const config = getConfig();
    if (options.dryRun) {
      config.resolver.dryRun = true;
    }
    const triage = new Triage(config);

    console.error(`Resolving issues for PR #${prNumber}...`);

    const { triage: result, actions } = await triage.resolve(parseInt(prNumber));

    console.log("# Resolution Results");
    console.log("");
    console.log("## Actions Taken:");
    for (const action of actions) {
      const icon = action.success ? "✅" : "❌";
      console.log(`${icon} ${action.action}: ${action.description}`);
      if (action.error) {
        console.log(`   Error: ${action.error}`);
      }
    }
    console.log("");
    console.log("## Updated Status:");
    console.log(`Status: ${result.status}`);
    console.log(`Unaddressed feedback: ${result.feedback.unaddressed}`);
    console.log(`Blockers: ${result.blockers.length}`);
  });

// =============================================================================
// run command
// =============================================================================

program
  .command("run <pr-number>")
  .description("Run the full triage workflow until PR is ready to merge")
  .option("--max-iterations <n>", "Maximum resolution iterations", "10")
  .action(async (prNumber: string, options: { maxIterations: string }) => {
    const config = getConfig();
    const triage = new Triage(config);

    console.error(`Running triage workflow for PR #${prNumber}...`);

    const result = await triage.runUntilReady(parseInt(prNumber), {
      maxIterations: parseInt(options.maxIterations),
      onProgress: (t, iteration) => {
        console.error(`[Iteration ${iteration}] Status: ${t.status}, Unaddressed: ${t.feedback.unaddressed}, Blockers: ${t.blockers.length}`);
      },
    });

    console.log("");
    console.log(`# Workflow Complete`);
    console.log("");
    console.log(`Success: ${result.success}`);
    console.log(`Iterations: ${result.iterations}`);
    console.log(`Final Status: ${result.finalTriage.status}`);
    console.log("");
    console.log("## Actions Summary:");
    const successful = result.allActions.filter((a) => a.success).length;
    const failed = result.allActions.filter((a) => !a.success).length;
    console.log(`Successful: ${successful}`);
    console.log(`Failed: ${failed}`);
  });

// =============================================================================
// request-review command
// =============================================================================

program
  .command("request-review <pr-number>")
  .description("Request AI reviews on a PR")
  .action(async (prNumber: string) => {
    const config = getConfig();
    const triage = new Triage(config);

    console.error(`Requesting reviews for PR #${prNumber}...`);

    await triage.requestReviews(parseInt(prNumber));

    console.log("Review requests posted: /gemini review, /q review");
  });

// =============================================================================
// status command
// =============================================================================

program
  .command("status <pr-number>")
  .description("Quick status check for a PR")
  .action(async (prNumber: string) => {
    const config = getConfig();
    const triage = new Triage(config);

    const result = await triage.analyze(parseInt(prNumber));

    const statusEmoji: Record<string, string> = {
      needs_work: "🔧",
      needs_review: "👀",
      needs_ci: "⏳",
      ready_to_merge: "✅",
      blocked: "🚫",
      merged: "🎉",
      closed: "🔒",
    };

    console.log(`${statusEmoji[result.status] || "❓"} PR #${result.prNumber}: ${result.status}`);
    console.log(`   CI: ${result.ci.allPassing ? "✅" : result.ci.anyPending ? "⏳" : "❌"}`);
    console.log(`   Feedback: ${result.feedback.unaddressed} unaddressed`);
    console.log(`   Blockers: ${result.blockers.length}`);
  });

program.parse();
