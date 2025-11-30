/**
 * Configuration Management for agentic-control
 *
 * Handles loading configuration from multiple sources:
 * - Environment variables
 * - Config files (agentic.config.json, agentic.config.yaml)
 * - Programmatic configuration
 */
import type { TokenConfig } from "./types.js";
export interface AgenticConfig {
    /** Token configuration for multi-org access */
    tokens?: Partial<TokenConfig>;
    /** Default model for AI operations */
    defaultModel?: string;
    /** Default repository for fleet operations */
    defaultRepository?: string;
    /** Coordination PR number for fleet communication */
    coordinationPr?: number;
    /** Log level */
    logLevel?: "debug" | "info" | "warn" | "error";
    /** Whether to enable verbose output */
    verbose?: boolean;
    /** MCP server configuration */
    mcp?: {
        serverPath?: string;
        command?: string;
        args?: string[];
    };
}
/**
 * Initialize configuration from all sources
 * Priority: env vars > config file > defaults
 */
export declare function initConfig(overrides?: Partial<AgenticConfig>): AgenticConfig;
/**
 * Get the current configuration
 */
export declare function getConfig(): AgenticConfig;
/**
 * Update configuration
 */
export declare function setConfig(updates: Partial<AgenticConfig>): void;
/**
 * Get a specific configuration value
 */
export declare function getConfigValue<K extends keyof AgenticConfig>(key: K): AgenticConfig[K];
/**
 * Check if verbose mode is enabled
 */
export declare function isVerbose(): boolean;
/**
 * Get the default model for AI operations
 */
export declare function getDefaultModel(): string;
/**
 * Get the log level
 */
export declare function getLogLevel(): string;
export declare const log: {
    debug: (...args: unknown[]) => void;
    info: (...args: unknown[]) => void;
    warn: (...args: unknown[]) => void;
    error: (...args: unknown[]) => void;
};
//# sourceMappingURL=config.d.ts.map