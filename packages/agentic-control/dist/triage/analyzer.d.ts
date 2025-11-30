/**
 * AI Analyzer - Uses Claude for fast triage and assessment
 *
 * Automatically analyzes:
 * - Conversation history for completed/outstanding tasks
 * - Code changes for issues and improvements
 * - Creates GitHub issues from analysis
 */
import type { Conversation, AnalysisResult, TriageResult, CodeReviewResult } from "../core/types.js";
export interface AIAnalyzerOptions {
    /** Anthropic API key (defaults to ANTHROPIC_API_KEY env var) */
    apiKey?: string;
    /** Model to use */
    model?: string;
    /** Repository for GitHub operations */
    repo?: string;
}
export declare class AIAnalyzer {
    private anthropic;
    private model;
    private repo;
    constructor(options?: AIAnalyzerOptions);
    /**
     * Analyze a conversation to extract completed/outstanding tasks
     */
    analyzeConversation(conversation: Conversation): Promise<AnalysisResult>;
    /**
     * Review code changes and identify issues
     */
    reviewCode(diff: string, context?: string): Promise<CodeReviewResult>;
    /**
     * Quick triage - fast assessment of what needs attention
     */
    quickTriage(input: string): Promise<TriageResult>;
    /**
     * Create GitHub issues from analysis
     * Always uses PR review token for consistent identity
     */
    createIssuesFromAnalysis(analysis: AnalysisResult, options?: {
        dryRun?: boolean;
        labels?: string[];
        assignCopilot?: boolean;
    }): Promise<string[]>;
    /**
     * Generate a comprehensive assessment report
     */
    generateReport(conversation: Conversation): Promise<string>;
    /**
     * Prepare conversation text for analysis
     */
    private prepareConversationText;
}
//# sourceMappingURL=analyzer.d.ts.map