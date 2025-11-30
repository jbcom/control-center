/**
 * Unified AI Agent
 * 
 * A complete AI-powered development agent combining:
 * - Anthropic's built-in tools (bash, text_editor)
 * - Cursor Agent MCP (manage background agents)
 * - GitHub MCP (PR/issue management)
 * - Context7 MCP (documentation)
 * 
 * This agent can autonomously:
 * - Triage PRs and issues
 * - Fix code based on feedback
 * - Spawn and coordinate sub-agents
 * - Look up documentation
 * - Execute shell commands
 * - Edit files
 */

import { generateText, streamText, tool, stepCountIs, type ToolSet } from "ai";
import { anthropic } from "@ai-sdk/anthropic";
import { execSync } from "child_process";
import { readFileSync, writeFileSync, existsSync, mkdirSync } from "fs";
import { dirname } from "path";
import { z } from "zod";
import { 
  initializeMCPClients, 
  getMCPTools, 
  closeMCPClients,
  type MCPClientConfig,
  type MCPClients 
} from "./mcp-clients.js";

export interface UnifiedAgentConfig {
  /** Working directory for file operations */
  workingDirectory?: string;
  /** Maximum steps for multi-step tool calls */
  maxSteps?: number;
  /** MCP client configuration */
  mcp?: MCPClientConfig;
  /** Model to use (default: claude-sonnet-4-20250514) */
  model?: string;
  /** Enable verbose logging */
  verbose?: boolean;
}

export interface AgentResult {
  success: boolean;
  result: string;
  steps: AgentStep[];
  usage?: {
    /** Token count for input/prompt (AI SDK v5 naming) */
    inputTokens: number;
    /** Token count for output/completion (AI SDK v5 naming) */
    outputTokens: number;
    /** Total token count */
    totalTokens: number;
  };
}

export interface AgentStep {
  toolName: string;
  input: unknown;
  output: string;
  timestamp: Date;
}

export class UnifiedAgent {
  private config: Required<Omit<UnifiedAgentConfig, 'mcp'>> & { mcp?: MCPClientConfig };
  private mcpClients: MCPClients | null = null;
  private initialized = false;

  constructor(config: UnifiedAgentConfig = {}) {
    this.config = {
      workingDirectory: config.workingDirectory ?? process.cwd(),
      maxSteps: config.maxSteps ?? 25,
      model: config.model ?? "claude-sonnet-4-20250514",
      verbose: config.verbose ?? false,
      mcp: config.mcp,
    };
  }

  /**
   * Initialize MCP clients and prepare the agent
   */
  async initialize(): Promise<void> {
    if (this.initialized) return;

    this.log("🚀 Initializing Unified Agent...");
    
    // Initialize MCP clients
    this.mcpClients = await initializeMCPClients(this.config.mcp);
    this.initialized = true;
    
    this.log("✅ Agent initialized");
  }

  /**
   * Close all connections and clean up
   */
  async close(): Promise<void> {
    if (this.mcpClients) {
      await closeMCPClients(this.mcpClients);
      this.mcpClients = null;
    }
    this.initialized = false;
  }

  /**
   * Execute a task with full tool access
   */
  async execute(task: string): Promise<AgentResult> {
    await this.initialize();

    const steps: AgentStep[] = [];
    const recordStep = (toolName: string, input: unknown, output: string) => {
      steps.push({ toolName, input, output, timestamp: new Date() });
      if (this.config.verbose) {
        console.log(`  🔧 ${toolName}:`, typeof input === 'string' ? input.slice(0, 100) : JSON.stringify(input).slice(0, 100));
      }
    };

    // Build tool set
    const tools = await this.buildToolSet(recordStep);

    try {
      const result = await generateText({
        model: anthropic(this.config.model),
        tools,
        stopWhen: stepCountIs(this.config.maxSteps),
        system: this.getSystemPrompt(),
        prompt: task,
      });

      return {
        success: true,
        result: result.text,
        steps,
        // AI SDK v5: usage has inputTokens, outputTokens, totalTokens
        usage: result.usage ? {
          inputTokens: result.usage.inputTokens ?? 0,
          outputTokens: result.usage.outputTokens ?? 0,
          totalTokens: result.usage.totalTokens ?? 0,
        } : undefined,
      };
    } catch (error) {
      return {
        success: false,
        result: error instanceof Error ? error.message : String(error),
        steps,
      };
    }
  }

  /**
   * Execute a task with streaming output
   */
  async *stream(task: string): AsyncGenerator<string> {
    await this.initialize();

    const steps: AgentStep[] = [];
    const recordStep = (toolName: string, input: unknown, output: string) => {
      steps.push({ toolName, input, output, timestamp: new Date() });
    };

    const tools = await this.buildToolSet(recordStep);

    const result = streamText({
      model: anthropic(this.config.model),
      tools,
      stopWhen: stepCountIs(this.config.maxSteps),
      system: this.getSystemPrompt(),
      prompt: task,
    });

    for await (const chunk of result.textStream) {
      yield chunk;
    }
  }

  /**
   * Build the complete tool set combining Anthropic tools and MCP tools
   */
  private async buildToolSet(
    recordStep: (name: string, input: unknown, output: string) => void
  ) {
    // Start with Anthropic's built-in tools
    const bashTool = anthropic.tools.bash_20250124({
      execute: async ({ command, restart }) => {
        if (restart) {
          recordStep("bash", { restart: true }, "Shell restarted");
          return "Shell restarted";
        }
        
        try {
          const output = execSync(command, {
            cwd: this.config.workingDirectory,
            encoding: "utf-8",
            maxBuffer: 10 * 1024 * 1024,
            timeout: 120000,
          });
          
          recordStep("bash", { command }, output);
          return output;
        } catch (error) {
          const errorMsg = error instanceof Error ? error.message : String(error);
          recordStep("bash", { command }, `Error: ${errorMsg}`);
          return `Error: ${errorMsg}`;
        }
      },
    });

    const textEditorTool = anthropic.tools.textEditor_20250124({
      execute: async ({ command, path, file_text, insert_line, new_str, old_str, view_range }) => {
        const fullPath = path.startsWith("/") 
          ? path 
          : `${this.config.workingDirectory}/${path}`;

        try {
          let result: string;

          switch (command) {
            case "view": {
              if (!existsSync(fullPath)) {
                result = `Error: File not found: ${path}`;
              } else {
                const content = readFileSync(fullPath, "utf-8");
                const lines = content.split("\n");
                
                if (view_range && view_range.length === 2) {
                  const [start, end] = view_range;
                  const selectedLines = lines.slice(start - 1, end);
                  result = selectedLines.map((line, i) => `${start + i}: ${line}`).join("\n");
                } else {
                  result = lines.map((line, i) => `${i + 1}: ${line}`).join("\n");
                }
              }
              break;
            }

            case "create": {
              if (!file_text) {
                result = "Error: file_text is required for create command";
              } else {
                const dir = dirname(fullPath);
                if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
                writeFileSync(fullPath, file_text);
                result = `Created file: ${path}`;
              }
              break;
            }

            case "str_replace": {
              if (!old_str || new_str === undefined) {
                result = "Error: old_str and new_str are required for str_replace";
              } else if (!existsSync(fullPath)) {
                result = `Error: File not found: ${path}`;
              } else {
                const content = readFileSync(fullPath, "utf-8");
                if (!content.includes(old_str)) {
                  result = `Error: old_str not found in file`;
                } else {
                  const newContent = content.replace(old_str, new_str);
                  writeFileSync(fullPath, newContent);
                  result = `Replaced text in ${path}`;
                }
              }
              break;
            }

            case "insert": {
              if (insert_line === undefined || new_str === undefined) {
                result = "Error: insert_line and new_str are required for insert";
              } else if (!existsSync(fullPath)) {
                result = `Error: File not found: ${path}`;
              } else {
                const content = readFileSync(fullPath, "utf-8");
                const lines = content.split("\n");
                lines.splice(insert_line, 0, new_str);
                writeFileSync(fullPath, lines.join("\n"));
                result = `Inserted text at line ${insert_line} in ${path}`;
              }
              break;
            }

            default:
              result = `Unknown command: ${command}`;
          }

          recordStep("str_replace_editor", { command, path }, result);
          return result;
        } catch (error) {
          const errorMsg = error instanceof Error ? error.message : String(error);
          recordStep("str_replace_editor", { command, path }, `Error: ${errorMsg}`);
          return `Error: ${errorMsg}`;
        }
      },
    });

    // Collect all tools - we use 'as ToolSet' since we're building a dynamic toolset
    // that combines Anthropic provider tools with custom tools and MCP tools
    const tools: ToolSet = {
      bash: bashTool,
      str_replace_editor: textEditorTool,
    } as ToolSet;

    // Add custom utility tools (AI SDK v5: use inputSchema instead of parameters)
    tools.git_status = tool({
      description: "Get current git status including branch, staged files, and modified files",
      inputSchema: z.object({}),
      execute: async () => {
        try {
          const status = execSync("git status --porcelain -b", {
            cwd: this.config.workingDirectory,
            encoding: "utf-8",
          });
          recordStep("git_status", {}, status);
          return status;
        } catch (error) {
          const msg = error instanceof Error ? error.message : String(error);
          recordStep("git_status", {}, `Error: ${msg}`);
          return `Error: ${msg}`;
        }
      },
    });

    tools.git_diff = tool({
      description: "Get git diff for staged or unstaged changes",
      inputSchema: z.object({
        staged: z.boolean().optional().describe("Show staged changes only"),
        file: z.string().optional().describe("Specific file to diff"),
      }),
      execute: async ({ staged, file }) => {
        try {
          const args = staged ? ["--cached"] : [];
          if (file) args.push(file);
          const diff = execSync(`git diff ${args.join(" ")}`, {
            cwd: this.config.workingDirectory,
            encoding: "utf-8",
          });
          recordStep("git_diff", { staged, file }, diff || "(no changes)");
          return diff || "(no changes)";
        } catch (error) {
          const msg = error instanceof Error ? error.message : String(error);
          recordStep("git_diff", { staged, file }, `Error: ${msg}`);
          return `Error: ${msg}`;
        }
      },
    });

    // Add MCP tools if available
    if (this.mcpClients) {
      const mcpTools = await getMCPTools(this.mcpClients);
      Object.assign(tools, mcpTools);
    }

    return tools as ToolSet;
  }

  /**
   * Get the system prompt for the agent
   */
  private getSystemPrompt(): string {
    return `You are an expert software development agent with access to powerful tools.

## Your Capabilities

### Code Operations (Anthropic Tools)
- **bash**: Execute shell commands for git, tests, builds, etc.
- **str_replace_editor**: View and edit files with precision

### Git Utilities
- **git_status**: Quick git status check
- **git_diff**: View changes in working directory

### MCP Integrations (when available)
- **Cursor Agent MCP**: Spawn and manage background agents, get conversations
- **GitHub MCP**: Create/update PRs, manage issues, search code, push files
- **Context7 MCP**: Look up current documentation for any library

## Working Directory
${this.config.workingDirectory}

## Guidelines

1. **Be thorough**: Verify your changes work before reporting success
2. **Use appropriate tools**: Prefer MCP tools for GitHub operations over raw git commands
3. **Handle errors gracefully**: If something fails, try to understand why and fix it
4. **Document your actions**: Explain what you're doing as you do it
5. **Test your changes**: Run tests and linting after making code changes

## When Triaging PRs
1. First understand the current state (CI status, feedback, changes)
2. Identify all blockers and unaddressed feedback
3. Fix issues systematically, starting with CI failures
4. Commit and push changes
5. Verify CI passes after your changes

## When Spawning Sub-Agents
1. Use specific, actionable task descriptions
2. Include relevant context (PR numbers, file paths, etc.)
3. Monitor agent progress and handle failures`;
  }

  private log(message: string): void {
    if (this.config.verbose) {
      console.log(message);
    }
  }
}

/**
 * Convenience function to run a one-shot task
 */
export async function runTask(
  task: string, 
  config?: UnifiedAgentConfig
): Promise<AgentResult> {
  const agent = new UnifiedAgent(config);
  try {
    return await agent.execute(task);
  } finally {
    await agent.close();
  }
}
