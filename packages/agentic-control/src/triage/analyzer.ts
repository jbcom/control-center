/**
 * AI Analyzer - Provider-agnostic AI triage and assessment
 * 
 * Supports multiple AI providers via Vercel AI SDK:
 * - anthropic (@ai-sdk/anthropic)
 * - openai (@ai-sdk/openai)
 * - google (@ai-sdk/google)
 * - mistral (@ai-sdk/mistral)
 * - azure (@ai-sdk/azure)
 * 
 * Install the provider you need:
 *   pnpm add @ai-sdk/anthropic
 * 
 * Configure in agentic.config.json:
 *   { "triage": { "provider": "anthropic", "model": "claude-sonnet-4-20250514" } }
 */

import { generateObject } from "ai";
import { z } from "zod";
import { spawnSync } from "node:child_process";
import { getTriageConfig, getDefaultApiKeyEnvVar, log, getConfig } from "../core/config.js";
import { getEnvForPRReview } from "../core/tokens.js";
import type { 
  Conversation, 
  ConversationMessage,
  AnalysisResult, 
  Task, 
  Blocker,
  TriageResult,
  CodeReviewResult,
  ReviewIssue,
  ReviewImprovement,
} from "../core/types.js";

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
// Provider Loading
// ============================================

type ProviderFactory = (config: { apiKey: string }) => unknown;

// Security: Explicit allowlist of supported providers and their packages
// Dynamic imports are only allowed for these pre-defined packages
const PROVIDER_CONFIG = {
  anthropic: { package: "@ai-sdk/anthropic", factory: "createAnthropic" },
  openai: { package: "@ai-sdk/openai", factory: "createOpenAI" },
  google: { package: "@ai-sdk/google", factory: "createGoogleGenerativeAI" },
  mistral: { package: "@ai-sdk/mistral", factory: "createMistral" },
  azure: { package: "@ai-sdk/azure", factory: "createAzure" },
} as const;

type SupportedProvider = keyof typeof PROVIDER_CONFIG;

function isValidProvider(name: string): name is SupportedProvider {
  return name in PROVIDER_CONFIG;
}

async function loadProvider(providerName: string, apiKey: string): Promise<(model: string) => unknown> {
  // Security: Validate provider name against explicit allowlist
  if (!isValidProvider(providerName)) {
    throw new Error(
      `Unknown provider: ${providerName}\n` +
      `Supported providers: ${Object.keys(PROVIDER_CONFIG).join(", ")}`
    );
  }

  const config = PROVIDER_CONFIG[providerName];

  try {
    // Security: Only import from pre-defined allowlist - no user input in import path
    let module: Record<string, unknown>;
    switch (providerName) {
      case "anthropic":
        module = await import("@ai-sdk/anthropic");
        break;
      case "openai":
        module = await import("@ai-sdk/openai");
        break;
      case "google":
        module = await import("@ai-sdk/google");
        break;
      case "mistral":
        module = await import("@ai-sdk/mistral");
        break;
      case "azure":
        module = await import("@ai-sdk/azure");
        break;
      default:
        throw new Error(`Provider ${providerName} not implemented`);
    }
    
    const factory = module[config.factory] as ProviderFactory;
    
    if (typeof factory !== "function") {
      throw new Error(`Factory ${config.factory} not found in ${config.package}`);
    }
    
    const provider = factory({ apiKey });
    return (model: string) => (provider as (model: string) => unknown)(model);
  } catch (err) {
    if ((err as NodeJS.ErrnoException).code === "ERR_MODULE_NOT_FOUND") {
      throw new Error(
        `Provider package not installed: ${config.package}\n` +
        `Install it with: pnpm add ${config.package}`
      );
    }
    throw err;
  }
}

// ============================================
// Types
// ============================================

export interface AIAnalyzerOptions {
  /** AI provider: anthropic, openai, google, mistral, azure */
  provider?: string;
  /** Model to use */
  model?: string;
  /** API key (defaults to provider-specific env var) */
  apiKey?: string;
  /** Repository for GitHub operations (required for issue creation) */
  repo?: string;
}

// ============================================
// AI Analyzer Class
// ============================================

export class AIAnalyzer {
  private providerName: string;
  private model: string;
  private apiKey: string;
  private repo: string | undefined;
  private providerFn: ((model: string) => unknown) | null = null;

  constructor(options: AIAnalyzerOptions = {}) {
    const triageConfig = getTriageConfig();
    
    this.providerName = options.provider ?? triageConfig.provider ?? "anthropic";
    this.model = options.model ?? triageConfig.model ?? "claude-sonnet-4-20250514";
    this.repo = options.repo ?? getConfig().defaultRepository;

    // Determine the correct API key, respecting provider overrides
    // If provider was overridden via options, use that provider's env var
    const effectiveProvider = options.provider ?? triageConfig.provider ?? "anthropic";
    const envVarName = (options.provider && options.provider !== triageConfig.provider)
      ? getDefaultApiKeyEnvVar(effectiveProvider)
      : (triageConfig.apiKeyEnvVar ?? getDefaultApiKeyEnvVar(effectiveProvider));
    
    this.apiKey = options.apiKey ?? process.env[envVarName] ?? "";

    if (!this.apiKey) {
      // Note: We intentionally include the env var NAME (not value) in error messages
      // to help users configure their environment correctly
      const hint = getDefaultApiKeyEnvVar(effectiveProvider);
      throw new Error(
        `API key required for ${this.providerName} provider.\n` +
        `Set ${hint} environment variable or pass apiKey option.`
      );
    }
  }

  private async getProvider(): Promise<(model: string) => unknown> {
    if (!this.providerFn) {
      this.providerFn = await loadProvider(this.providerName, this.apiKey);
    }
    return this.providerFn;
  }

  /**
   * Set the repository for GitHub operations
   */
  setRepo(repo: string): void {
    this.repo = repo;
  }

  /**
   * Analyze a conversation to extract completed/outstanding tasks
   */
  async analyzeConversation(conversation: Conversation): Promise<AnalysisResult> {
    const provider = await this.getProvider();
    const messages = conversation.messages || [];
    const conversationText = this.prepareConversationText(messages);

    const { object } = await generateObject({
      model: provider(this.model) as Parameters<typeof generateObject>[0]["model"],
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
    const completedTasks: Task[] = object.completedTasks.map(t => ({
      id: t.id,
      title: t.title,
      description: t.description,
      priority: t.priority,
      category: t.category,
      status: "completed" as const,
    }));

    const outstandingTasks: Task[] = object.outstandingTasks.map(t => ({
      id: t.id,
      title: t.title,
      description: t.description,
      priority: t.priority,
      category: t.category,
      status: t.status === "blocked" ? "blocked" as const : "pending" as const,
      blockers: t.blockers,
    }));

    const blockers: Blocker[] = object.blockers.map(b => ({
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
  async reviewCode(diff: string, context?: string): Promise<CodeReviewResult> {
    const provider = await this.getProvider();
    
    const { object } = await generateObject({
      model: provider(this.model) as Parameters<typeof generateObject>[0]["model"],
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

    const issues: ReviewIssue[] = object.issues.map(i => ({
      file: i.file,
      line: i.line,
      severity: i.severity,
      category: i.category,
      description: i.description,
      suggestedFix: i.suggestedFix,
    }));

    const improvements: ReviewImprovement[] = object.improvements.map(i => ({
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
  async quickTriage(input: string): Promise<TriageResult> {
    const provider = await this.getProvider();
    
    const { object } = await generateObject({
      model: provider(this.model) as Parameters<typeof generateObject>[0]["model"],
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
  async createIssuesFromAnalysis(
    analysis: AnalysisResult,
    options?: { 
      dryRun?: boolean; 
      labels?: string[];
      assignCopilot?: boolean;
      repo?: string;
    }
  ): Promise<string[]> {
    const repo = options?.repo ?? this.repo;
    if (!repo) {
      throw new Error(
        "Repository is required for issue creation. Set via:\n" +
        "  - AIAnalyzer constructor: new AIAnalyzer({ repo: 'owner/repo' })\n" +
        "  - setRepo() method\n" +
        "  - createIssuesFromAnalysis() options: { repo: 'owner/repo' }\n" +
        "  - Config file: defaultRepository in agentic.config.json"
      );
    }

    const createdIssues: string[] = [];
    const env = { ...process.env, ...getEnvForPRReview() };

    for (const task of analysis.outstandingTasks) {
      const labels: string[] = [
        ...(options?.labels || []),
      ];
      
      if (options?.assignCopilot !== false) {
        labels.push("copilot");
      }
      
      if (task.priority === "critical" || task.priority === "high") {
        labels.push(`priority:${task.priority}`);
      }
      
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
- Follow your project's contribution guidelines
- Versioning is typically managed automatically — avoid manual version bumps

---
*Generated by agentic-control AI Analyzer*`;

      if (options?.dryRun) {
        log.info(`[DRY RUN] Would create issue: ${task.title}`);
        createdIssues.push(`[DRY RUN] ${task.title}`);
        continue;
      }

      try {
        // Build args array safely - no shell interpolation
        const args = ["issue", "create", "--repo", repo, "--title", task.title, "--body-file", "-"];
        
        // Add labels if any
        if (labels.length > 0) {
          args.push("--label", labels.join(","));
        }

        // Use spawnSync for safe command execution (no shell injection)
        const proc = spawnSync("gh", args, { 
          input: body, 
          encoding: "utf-8", 
          env,
          maxBuffer: 10 * 1024 * 1024, // 10MB
        });

        if (proc.error) {
          throw proc.error;
        }

        if (proc.status !== 0) {
          throw new Error(proc.stderr || "gh issue create failed");
        }

        const result = proc.stdout.trim();
        createdIssues.push(result);
        log.info(`✅ Created issue: ${result}`);
      } catch (err) {
        log.error(`❌ Failed to create issue: ${task.title}`, err);
      }
    }

    return createdIssues;
  }

  /**
   * Generate a comprehensive assessment report
   */
  async generateReport(conversation: Conversation): Promise<string> {
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
*Generated by agentic-control AI Analyzer using ${this.providerName}/${this.model}*
*Timestamp: ${new Date().toISOString()}*
`;
  }

  /**
   * Prepare conversation text for analysis
   */
  private prepareConversationText(messages: ConversationMessage[], maxTokens = 100000): string {
    const maxChars = maxTokens * 4;
    const APPROX_CHARS_PER_MESSAGE = 500;
    
    let text = messages
      .map((m, i) => {
        const role = m.type === "user_message" ? "USER" : "ASSISTANT";
        return `[${i + 1}] ${role}:\n${m.text}\n`;
      })
      .join("\n---\n");

    if (text.length > maxChars) {
      const firstPart = text.slice(0, Math.floor(maxChars * 0.2));
      const lastPart = text.slice(-Math.floor(maxChars * 0.8));
      const truncatedChars = text.length - (firstPart.length + lastPart.length);
      const estimatedMessages = Math.ceil(truncatedChars / APPROX_CHARS_PER_MESSAGE);
      text = `${firstPart}\n\n[... approximately ${estimatedMessages} messages truncated (${truncatedChars} chars) ...]\n\n${lastPart}`;
    }

    return text;
  }
}
