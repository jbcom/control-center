/**
 * AI Analyzer - Uses Claude Haiku for fast triage and assessment
 * 
 * Automatically analyzes:
 * - Conversation history for completed/outstanding tasks
 * - Code changes for issues and improvements
 * - Creates GitHub issues from analysis
 */

import { createAnthropic } from "@ai-sdk/anthropic";
import { generateText, generateObject } from "ai";
import { z } from "zod";
import { execSync } from "node:child_process";
import type { Conversation, Message } from "./types.js";

// Schemas for structured output
// Note: Using .nullable().optional() to handle AI returning null instead of omitting fields
const TaskAnalysisSchema = z.object({
  completedTasks: z.array(z.object({
    title: z.string(),
    description: z.string(),
    evidence: z.string(),
    prNumber: z.number().nullable().optional(),
  })),
  outstandingTasks: z.array(z.object({
    title: z.string(),
    description: z.string(),
    priority: z.enum(["critical", "high", "medium", "low"]),
    blockedBy: z.string().nullable().optional(),
    suggestedLabels: z.array(z.string()),
  })),
  blockers: z.array(z.object({
    issue: z.string(),
    severity: z.enum(["critical", "high", "medium"]),
    suggestedResolution: z.string(),
  })),
  decisions: z.array(z.object({
    decision: z.string(),
    rationale: z.string(),
    alternatives: z.array(z.string()).nullable().optional(),
  })),
  summary: z.string(),
});

const CodeReviewSchema = z.object({
  issues: z.array(z.object({
    file: z.string(),
    line: z.number().optional(),
    severity: z.enum(["critical", "high", "medium", "low", "info"]),
    category: z.enum(["security", "bug", "performance", "style", "documentation"]),
    description: z.string(),
    suggestedFix: z.string().optional(),
  })),
  improvements: z.array(z.object({
    area: z.string(),
    suggestion: z.string(),
    effort: z.enum(["trivial", "small", "medium", "large"]),
  })),
  overallAssessment: z.string(),
  readyToMerge: z.boolean(),
  mergeBlockers: z.array(z.string()),
});

export type TaskAnalysis = z.infer<typeof TaskAnalysisSchema>;
export type CodeReview = z.infer<typeof CodeReviewSchema>;

export interface AnalyzerOptions {
  /** Anthropic API key (defaults to ANTHROPIC_API_KEY env var) */
  apiKey?: string;
  /** Model to use (default: claude-sonnet-4-20250514 for balance of speed/quality) */
  model?: string;
  /** GitHub token for issue creation */
  githubToken?: string;
  /** Repository for GitHub operations */
  repo?: string;
}

export class AIAnalyzer {
  private anthropic: ReturnType<typeof createAnthropic>;
  private model: string;
  private githubToken?: string;
  private repo?: string;

  constructor(options: AnalyzerOptions = {}) {
    const apiKey = options.apiKey ?? process.env.ANTHROPIC_API_KEY;
    if (!apiKey) {
      throw new Error("ANTHROPIC_API_KEY is required");
    }

    this.anthropic = createAnthropic({ apiKey });
    // Use claude-sonnet-4-20250514 for good balance of speed and quality
    this.model = options.model ?? "claude-sonnet-4-20250514";
    this.githubToken = options.githubToken ?? process.env.GITHUB_JBCOM_TOKEN;
    this.repo = options.repo ?? "jbcom/jbcom-control-center";
  }

  /**
   * Analyze a conversation to extract completed/outstanding tasks
   */
  async analyzeConversation(conversation: Conversation): Promise<TaskAnalysis> {
    const messages = conversation.messages || [];
    
    // Prepare conversation text (truncate if too long)
    const conversationText = this.prepareConversationText(messages);

    const { object } = await generateObject({
      model: this.anthropic(this.model),
      schema: TaskAnalysisSchema,
      prompt: `Analyze this agent conversation and extract:
1. COMPLETED TASKS - What was actually finished and merged/deployed
2. OUTSTANDING TASKS - What remains to be done
3. BLOCKERS - Any issues preventing progress
4. DECISIONS - Key decisions made during the session
5. SUMMARY - Brief overall assessment

Be thorough and specific. Reference PR numbers, file paths, and specific changes where possible.

CONVERSATION:
${conversationText}`,
    });

    return object;
  }

  /**
   * Review code changes and identify issues
   */
  async reviewCode(diff: string, context?: string): Promise<CodeReview> {
    const { object } = await generateObject({
      model: this.anthropic(this.model),
      schema: CodeReviewSchema,
      prompt: `Review this code diff and identify:
1. ISSUES - Security, bugs, performance problems
2. IMPROVEMENTS - Suggestions for better code
3. OVERALL ASSESSMENT - Is this ready to merge?

Be specific about file paths and line numbers.
Focus on real issues, not style nitpicks.

${context ? `CONTEXT:\n${context}\n\n` : ""}DIFF:
${diff}`,
    });

    return object;
  }

  /**
   * Quick triage - fast assessment of what needs attention
   */
  async quickTriage(input: string): Promise<{
    priority: "critical" | "high" | "medium" | "low";
    category: string;
    summary: string;
    suggestedAction: string;
  }> {
    const { object } = await generateObject({
      model: this.anthropic(this.model),
      schema: z.object({
        priority: z.enum(["critical", "high", "medium", "low"]),
        category: z.string(),
        summary: z.string(),
        suggestedAction: z.string(),
      }),
      prompt: `Quickly triage this input and determine:
1. Priority level (critical/high/medium/low)
2. Category (bug, feature, documentation, infrastructure, etc.)
3. Brief summary
4. Suggested immediate action

INPUT:
${input}`,
    });

    return object;
  }

  /**
   * Create GitHub issues from analysis
   * Issues are formatted to work with GitHub Copilot for automatic PR creation
   */
  async createIssuesFromAnalysis(
    analysis: TaskAnalysis,
    options?: { 
      dryRun?: boolean; 
      labels?: string[];
      assignCopilot?: boolean;  // Add copilot label for auto-pickup
    }
  ): Promise<string[]> {
    const createdIssues: string[] = [];

    for (const task of analysis.outstandingTasks) {
      // Build labels - include copilot for auto-pickup if requested
      const labels = [
        ...(task.suggestedLabels || []), 
        ...(options?.labels || []),
      ];
      
      // Add copilot label for automatic PR creation
      if (options?.assignCopilot !== false) {
        labels.push("copilot");
      }
      
      // Add priority label
      if (task.priority === "critical" || task.priority === "high") {
        labels.push(`priority:${task.priority}`);
      }

      const labelsArg = labels.length > 0 ? `--label "${labels.join(",")}"` : "";
      
      // Format body for Copilot comprehension
      // Include clear acceptance criteria and context
      const body = `## Summary
${task.description}

## Priority
\`${task.priority.toUpperCase()}\`

${task.blockedBy ? `## Blocked By\n${task.blockedBy}\n` : ""}

## Acceptance Criteria
- [ ] Implementation complete
- [ ] Tests added/updated
- [ ] Documentation updated if needed
- [ ] CI passes

## Context for AI Agents
This issue was auto-generated from agent session analysis.
- Follow the guidelines in \`.ruler/AGENTS.md\`
- Use CalVer versioning (automatic)
- Run \`cursor-fleet review\` before pushing

---
*Generated by AI Analyzer • Copilot-ready*`;

      if (options?.dryRun) {
        console.log(`[DRY RUN] Would create issue: ${task.title}`);
        console.log(`  Priority: ${task.priority}`);
        console.log(`  Labels: ${labels.join(", ")}`);
        createdIssues.push(`[DRY RUN] ${task.title}`);
        continue;
      }

      try {
        const result = execSync(
          `gh issue create --repo ${this.repo} --title "${task.title.replace(/"/g, '\\"')}" --body-file - ${labelsArg}`,
          { 
            input: body, 
            encoding: "utf-8",
            env: { ...process.env, GH_TOKEN: this.githubToken },
          }
        );
        createdIssues.push(result.trim());
        console.log(`✅ Created issue: ${result.trim()}`);
      } catch (err) {
        console.error(`❌ Failed to create issue: ${task.title}`, err);
      }
    }

    return createdIssues;
  }

  /**
   * Generate a comprehensive assessment report
   */
  async generateReport(conversation: Conversation): Promise<string> {
    const analysis = await this.analyzeConversation(conversation);
    
    const report = `# Agent Session Assessment Report

## Summary
${analysis.summary}

## Completed Tasks (${analysis.completedTasks.length})
${analysis.completedTasks.map(t => `
### ✅ ${t.title}
${t.description}
${t.prNumber ? `**PR**: #${t.prNumber}` : ""}
${t.evidence ? `**Evidence**: ${t.evidence}` : ""}
`).join("\n")}

## Outstanding Tasks (${analysis.outstandingTasks.length})
${analysis.outstandingTasks.map(t => `
### 📋 ${t.title}
**Priority**: ${t.priority}
${t.description}
${t.blockedBy ? `**Blocked By**: ${t.blockedBy}` : ""}
**Suggested Labels**: ${t.suggestedLabels.join(", ")}
`).join("\n")}

## Blockers (${analysis.blockers.length})
${analysis.blockers.map(b => `
### ⚠️ ${b.issue}
**Severity**: ${b.severity}
**Suggested Resolution**: ${b.suggestedResolution}
`).join("\n")}

## Key Decisions (${analysis.decisions.length})
${analysis.decisions.map(d => `
### 💡 ${d.decision}
${d.rationale}
${d.alternatives?.length ? `**Alternatives Considered**: ${d.alternatives.join(", ")}` : ""}
`).join("\n")}

---
*Generated by AI Analyzer using Claude ${this.model}*
*Timestamp: ${new Date().toISOString()}*
`;

    return report;
  }

  /**
   * Prepare conversation text for analysis (handle large conversations)
   */
  private prepareConversationText(messages: Message[], maxTokens = 100000): string {
    // Estimate ~4 chars per token
    const maxChars = maxTokens * 4;
    
    let text = messages
      .map((m, i) => {
        const role = m.type === "user_message" ? "USER" : "ASSISTANT";
        return `[${i + 1}] ${role}:\n${m.text}\n`;
      })
      .join("\n---\n");

    // If too long, prioritize recent messages but keep some context
    if (text.length > maxChars) {
      const firstPart = text.slice(0, maxChars * 0.2);
      const lastPart = text.slice(-(maxChars * 0.8));
      text = `${firstPart}\n\n[... ${messages.length - 20} messages truncated ...]\n\n${lastPart}`;
    }

    return text;
  }
}

/**
 * Quick helper to analyze and report
 */
export async function analyzeAndReport(
  conversation: Conversation,
  options?: AnalyzerOptions
): Promise<{ analysis: TaskAnalysis; report: string }> {
  const analyzer = new AIAnalyzer(options);
  const analysis = await analyzer.analyzeConversation(conversation);
  const report = await analyzer.generateReport(conversation);
  return { analysis, report };
}
