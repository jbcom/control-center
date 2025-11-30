/**
 * AI Analyzer - Uses Claude for fast triage and assessment
 *
 * Automatically analyzes:
 * - Conversation history for completed/outstanding tasks
 * - Code changes for issues and improvements
 * - Creates GitHub issues from analysis
 */
import { createAnthropic } from "@ai-sdk/anthropic";
import { generateObject } from "ai";
import { z } from "zod";
import { getDefaultModel, log } from "../core/config.js";
import { getEnvForPRReview } from "../core/tokens.js";
import { execSync } from "node:child_process";
// ============================================
// Schemas for Structured AI Output
// ============================================
const TaskAnalysisSchema = z.object({
    completedTasks: z.array(z.object({
        id: z.string(),
        title: z.string(),
        description: z.string().optional(),
        priority: z.enum(["critical", "high", "medium", "low", "info"]),
        category: z.enum(["bug", "feature", "security", "performance", "documentation", "infrastructure", "dependency", "ci", "other"]),
        status: z.literal("completed"),
        evidence: z.string().optional(),
        prNumber: z.number().nullable().optional(),
    })),
    outstandingTasks: z.array(z.object({
        id: z.string(),
        title: z.string(),
        description: z.string().optional(),
        priority: z.enum(["critical", "high", "medium", "low", "info"]),
        category: z.enum(["bug", "feature", "security", "performance", "documentation", "infrastructure", "dependency", "ci", "other"]),
        status: z.enum(["pending", "in_progress", "blocked"]),
        blockers: z.array(z.string()).optional(),
        suggestedLabels: z.array(z.string()).optional(),
    })),
    blockers: z.array(z.object({
        issue: z.string(),
        severity: z.enum(["critical", "high", "medium", "low", "info"]),
        suggestedResolution: z.string().optional(),
    })),
    summary: z.string(),
    recommendations: z.array(z.string()),
});
const CodeReviewSchema = z.object({
    issues: z.array(z.object({
        file: z.string(),
        line: z.number().optional(),
        severity: z.enum(["critical", "high", "medium", "low", "info"]),
        category: z.enum(["bug", "security", "performance", "style", "logic", "documentation", "test", "other"]),
        description: z.string(),
        suggestedFix: z.string().optional(),
    })),
    improvements: z.array(z.object({
        area: z.string(),
        suggestion: z.string(),
        effort: z.enum(["low", "medium", "high"]),
    })),
    overallAssessment: z.string(),
    readyToMerge: z.boolean(),
    mergeBlockers: z.array(z.string()),
});
const TriageSchema = z.object({
    priority: z.enum(["critical", "high", "medium", "low", "info"]),
    category: z.enum(["bug", "feature", "security", "performance", "documentation", "infrastructure", "dependency", "ci", "other"]),
    summary: z.string(),
    suggestedAction: z.string(),
    confidence: z.number().min(0).max(1),
});
// ============================================
// AI Analyzer Class
// ============================================
export class AIAnalyzer {
    anthropic;
    model;
    repo;
    constructor(options = {}) {
        const apiKey = options.apiKey ?? process.env.ANTHROPIC_API_KEY;
        if (!apiKey) {
            throw new Error("ANTHROPIC_API_KEY is required for AI analysis");
        }
        this.anthropic = createAnthropic({ apiKey });
        this.model = options.model ?? getDefaultModel();
        this.repo = options.repo ?? "jbcom/jbcom-control-center";
    }
    /**
     * Analyze a conversation to extract completed/outstanding tasks
     */
    async analyzeConversation(conversation) {
        const messages = conversation.messages || [];
        const conversationText = this.prepareConversationText(messages);
        const { object } = await generateObject({
            model: this.anthropic(this.model),
            schema: TaskAnalysisSchema,
            prompt: `Analyze this agent conversation and extract:
1. COMPLETED TASKS - What was actually finished and merged/deployed
2. OUTSTANDING TASKS - What remains to be done
3. BLOCKERS - Any issues preventing progress
4. SUMMARY - Brief overall assessment
5. RECOMMENDATIONS - What should be done next

Be thorough and specific. Reference PR numbers, file paths, and specific changes where possible.
Generate unique IDs for tasks (e.g., task-001, task-002).

CONVERSATION:
${conversationText}`,
        });
        // Map to our types
        const completedTasks = object.completedTasks.map(t => ({
            id: t.id,
            title: t.title,
            description: t.description,
            priority: t.priority,
            category: t.category,
            status: "completed",
        }));
        const outstandingTasks = object.outstandingTasks.map(t => ({
            id: t.id,
            title: t.title,
            description: t.description,
            priority: t.priority,
            category: t.category,
            status: t.status === "blocked" ? "blocked" : "pending",
            blockers: t.blockers,
        }));
        const blockers = object.blockers.map(b => ({
            issue: b.issue,
            severity: b.severity,
            suggestedResolution: b.suggestedResolution,
        }));
        return {
            summary: object.summary,
            completedTasks,
            outstandingTasks,
            blockers,
            recommendations: object.recommendations,
        };
    }
    /**
     * Review code changes and identify issues
     */
    async reviewCode(diff, context) {
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
        const issues = object.issues.map(i => ({
            file: i.file,
            line: i.line,
            severity: i.severity,
            category: i.category,
            description: i.description,
            suggestedFix: i.suggestedFix,
        }));
        const improvements = object.improvements.map(i => ({
            area: i.area,
            suggestion: i.suggestion,
            effort: i.effort,
        }));
        return {
            readyToMerge: object.readyToMerge,
            mergeBlockers: object.mergeBlockers,
            issues,
            improvements,
            overallAssessment: object.overallAssessment,
        };
    }
    /**
     * Quick triage - fast assessment of what needs attention
     */
    async quickTriage(input) {
        const { object } = await generateObject({
            model: this.anthropic(this.model),
            schema: TriageSchema,
            prompt: `Quickly triage this input and determine:
1. Priority level (critical/high/medium/low/info)
2. Category (bug, feature, documentation, infrastructure, etc.)
3. Brief summary
4. Suggested immediate action
5. Confidence level (0-1)

INPUT:
${input}`,
        });
        return {
            priority: object.priority,
            category: object.category,
            summary: object.summary,
            suggestedAction: object.suggestedAction,
            confidence: object.confidence,
        };
    }
    /**
     * Create GitHub issues from analysis
     * Always uses PR review token for consistent identity
     */
    async createIssuesFromAnalysis(analysis, options) {
        const createdIssues = [];
        const env = { ...process.env, ...getEnvForPRReview() };
        for (const task of analysis.outstandingTasks) {
            const labels = [
                ...(options?.labels || []),
            ];
            if (options?.assignCopilot !== false) {
                labels.push("copilot");
            }
            if (task.priority === "critical" || task.priority === "high") {
                labels.push(`priority:${task.priority}`);
            }
            const labelsArg = labels.length > 0 ? `--label "${labels.join(",")}"` : "";
            const body = `## Summary
${task.description || task.title}

## Priority
\`${task.priority.toUpperCase()}\`

${task.blockers?.length ? `## Blocked By\n${task.blockers.join("\n")}\n` : ""}

## Acceptance Criteria
- [ ] Implementation complete
- [ ] Tests added/updated
- [ ] Documentation updated if needed
- [ ] CI passes

## Context for AI Agents
This issue was auto-generated from agent session analysis.
- Follow the guidelines in \`.ruler/AGENTS.md\`
- Versioning is managed by python-semantic-release (SemVer) — never bump manually

---
*Generated by agentic-control AI Analyzer*`;
            if (options?.dryRun) {
                log.info(`[DRY RUN] Would create issue: ${task.title}`);
                createdIssues.push(`[DRY RUN] ${task.title}`);
                continue;
            }
            try {
                const result = execSync(`gh issue create --repo ${this.repo} --title "${task.title.replace(/"/g, '\\"')}" --body-file - ${labelsArg}`, { input: body, encoding: "utf-8", env });
                createdIssues.push(result.trim());
                log.info(`✅ Created issue: ${result.trim()}`);
            }
            catch (err) {
                log.error(`❌ Failed to create issue: ${task.title}`, err);
            }
        }
        return createdIssues;
    }
    /**
     * Generate a comprehensive assessment report
     */
    async generateReport(conversation) {
        const analysis = await this.analyzeConversation(conversation);
        return `# Agent Session Assessment Report

## Summary
${analysis.summary}

## Completed Tasks (${analysis.completedTasks.length})
${analysis.completedTasks.map(t => `
### ✅ ${t.title}
${t.description || ""}
`).join("\n")}

## Outstanding Tasks (${analysis.outstandingTasks.length})
${analysis.outstandingTasks.map(t => `
### 📋 ${t.title}
**Priority**: ${t.priority}
${t.description || ""}
${t.blockers?.length ? `**Blocked By**: ${t.blockers.join(", ")}` : ""}
`).join("\n")}

## Blockers (${analysis.blockers.length})
${analysis.blockers.map(b => `
### ⚠️ ${b.issue}
**Severity**: ${b.severity}
**Suggested Resolution**: ${b.suggestedResolution || "None provided"}
`).join("\n")}

## Recommendations
${analysis.recommendations.map(r => `- ${r}`).join("\n")}

---
*Generated by agentic-control AI Analyzer using Claude ${this.model}*
*Timestamp: ${new Date().toISOString()}*
`;
    }
    /**
     * Prepare conversation text for analysis
     */
    prepareConversationText(messages, maxTokens = 100000) {
        const maxChars = maxTokens * 4;
        let text = messages
            .map((m, i) => {
            const role = m.type === "user_message" ? "USER" : "ASSISTANT";
            return `[${i + 1}] ${role}:\n${m.text}\n`;
        })
            .join("\n---\n");
        if (text.length > maxChars) {
            const firstPart = text.slice(0, maxChars * 0.2);
            const lastPart = text.slice(-(maxChars * 0.8));
            text = `${firstPart}\n\n[... ${messages.length - 20} messages truncated ...]\n\n${lastPart}`;
        }
        return text;
    }
}
//# sourceMappingURL=analyzer.js.map