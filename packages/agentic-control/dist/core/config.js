/**
 * Configuration Management for agentic-control
 *
 * Handles loading configuration from multiple sources:
 * - Environment variables
 * - Config files (agentic.config.json, agentic.config.yaml)
 * - Programmatic configuration
 */
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { setTokenConfig } from "./tokens.js";
// ============================================
// Default Configuration
// ============================================
const DEFAULT_CONFIG = {
    defaultModel: "claude-sonnet-4-20250514",
    logLevel: "info",
    verbose: false,
};
// ============================================
// Configuration State
// ============================================
let config = { ...DEFAULT_CONFIG };
// ============================================
// Configuration Loading
// ============================================
/**
 * Load configuration from a JSON file
 */
function loadJsonConfig(filePath) {
    try {
        if (!existsSync(filePath)) {
            return null;
        }
        const content = readFileSync(filePath, "utf-8");
        return JSON.parse(content);
    }
    catch {
        return null;
    }
}
/**
 * Load configuration from environment variables
 */
function loadEnvConfig() {
    const envConfig = {};
    if (process.env.AGENTIC_MODEL) {
        envConfig.defaultModel = process.env.AGENTIC_MODEL;
    }
    if (process.env.AGENTIC_REPOSITORY) {
        envConfig.defaultRepository = process.env.AGENTIC_REPOSITORY;
    }
    if (process.env.AGENTIC_COORDINATION_PR) {
        envConfig.coordinationPr = parseInt(process.env.AGENTIC_COORDINATION_PR, 10);
    }
    if (process.env.AGENTIC_LOG_LEVEL) {
        envConfig.logLevel = process.env.AGENTIC_LOG_LEVEL;
    }
    if (process.env.AGENTIC_VERBOSE === "true") {
        envConfig.verbose = true;
    }
    return envConfig;
}
/**
 * Find and load configuration from the filesystem
 * Searches in order: current directory, workspace root, home directory
 */
function findConfigFile() {
    const configNames = ["agentic.config.json", ".agenticrc", ".agenticrc.json"];
    const searchPaths = [
        process.cwd(),
        process.env.WORKSPACE_PATH ?? "/workspace",
        process.env.HOME ?? "",
    ].filter(Boolean);
    for (const searchPath of searchPaths) {
        for (const configName of configNames) {
            const filePath = join(searchPath, configName);
            if (existsSync(filePath)) {
                return filePath;
            }
        }
    }
    return null;
}
/**
 * Initialize configuration from all sources
 * Priority: env vars > config file > defaults
 */
export function initConfig(overrides) {
    // Start with defaults
    config = { ...DEFAULT_CONFIG };
    // Load from config file if found
    const configFile = findConfigFile();
    if (configFile) {
        const fileConfig = loadJsonConfig(configFile);
        if (fileConfig) {
            config = { ...config, ...fileConfig };
        }
    }
    // Load from environment
    const envConfig = loadEnvConfig();
    config = { ...config, ...envConfig };
    // Apply programmatic overrides
    if (overrides) {
        config = { ...config, ...overrides };
    }
    // Apply token configuration
    if (config.tokens) {
        setTokenConfig(config.tokens);
    }
    return config;
}
// ============================================
// Public API
// ============================================
/**
 * Get the current configuration
 */
export function getConfig() {
    return { ...config };
}
/**
 * Update configuration
 */
export function setConfig(updates) {
    config = { ...config, ...updates };
    // Also update token config if provided
    if (updates.tokens) {
        setTokenConfig(updates.tokens);
    }
}
/**
 * Get a specific configuration value
 */
export function getConfigValue(key) {
    return config[key];
}
/**
 * Check if verbose mode is enabled
 */
export function isVerbose() {
    return config.verbose ?? false;
}
/**
 * Get the default model for AI operations
 */
export function getDefaultModel() {
    return config.defaultModel ?? DEFAULT_CONFIG.defaultModel;
}
/**
 * Get the log level
 */
export function getLogLevel() {
    return config.logLevel ?? "info";
}
// ============================================
// Logging Utilities
// ============================================
const LOG_LEVELS = {
    debug: 0,
    info: 1,
    warn: 2,
    error: 3,
};
function shouldLog(level) {
    const currentLevel = LOG_LEVELS[getLogLevel()] ?? 1;
    return LOG_LEVELS[level] >= currentLevel;
}
export const log = {
    debug: (...args) => {
        if (shouldLog("debug")) {
            console.debug("[agentic:debug]", ...args);
        }
    },
    info: (...args) => {
        if (shouldLog("info")) {
            console.log("[agentic:info]", ...args);
        }
    },
    warn: (...args) => {
        if (shouldLog("warn")) {
            console.warn("[agentic:warn]", ...args);
        }
    },
    error: (...args) => {
        if (shouldLog("error")) {
            console.error("[agentic:error]", ...args);
        }
    },
};
// Initialize on import
initConfig();
//# sourceMappingURL=config.js.map