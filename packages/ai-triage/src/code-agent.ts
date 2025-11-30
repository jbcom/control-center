import { generateText, stepCountIs } from "ai";
import { anthropic } from "@ai-sdk/anthropic";
import { execSync } from "child_process";
import { readFileSync, writeFileSync, existsSync, mkdirSync, realpathSync } from "fs";
import { dirname, resolve, relative, isAbsolute } from "path";

/**
 * Validate that a path is within the allowed working directory
 * Prevents path traversal attacks
 */
function validatePath(inputPath: string, workingDirectory: string): { valid: boolean; resolvedPath: string; error?: string } {
  try {
    const fullPath = isAbsolute(inputPath) ? inputPath : resolve(workingDirectory, inputPath);
    let pathToCheck = fullPath;
    if (!existsSync(fullPath)) {
      pathToCheck = dirname(fullPath);
      if (!existsSync(pathToCheck)) {
        pathToCheck = workingDirectory;
      }
    }
    const realPath = realpathSync(pathToCheck);
    const realWorkDir = realpathSync(workingDirectory);
    const relativePath = relative(realWorkDir, realPath);
    if (relativePath.startsWith('..') || isAbsolute(relativePath)) {
      return { valid: false, resolvedPath: fullPath, error: `Path traversal detected: ${inputPath}` };
    }
    return { valid: true, resolvedPath: fullPath };
  } catch (error) {
    return { valid: false, resolvedPath: inputPath, error: `Path validation error: ${error instanceof Error ? error.message : String(error)}` };
  }
}

export interface CodeAgentConfig {
  workingDirectory: string;
  maxSteps?: number;
}

/**
 * Code Agent using Vercel AI SDK with Anthropic's built-in tools:
 * - Bash tool for running commands
 * - Text Editor tool for viewing/editing files
 */
export class CodeAgent {
  private config: CodeAgentConfig;

  constructor(config: CodeAgentConfig) {
    this.config = config;
  }

  /**
   * Execute a task using Claude with bash and text editor tools
   */
  async execute(task: string): Promise<{
    success: boolean;
    result: string;
    steps: Array<{
      toolName: string;
      input: unknown;
      output: string;
    }>;
  }> {
    const steps: Array<{ toolName: string; input: unknown; output: string }> = [];

    // Create bash tool with actual execution
    const bashTool = anthropic.tools.bash_20250124({
      execute: async ({ command, restart }) => {
        if (restart) {
          return "Shell restarted";
        }
        
        try {
          const output = execSync(command, {
            cwd: this.config.workingDirectory,
            encoding: "utf-8",
            maxBuffer: 10 * 1024 * 1024, // 10MB
            timeout: 60000, // 60 seconds
          });
          
          steps.push({ toolName: "bash", input: { command }, output });
          return output;
        } catch (error) {
          const errorMsg = error instanceof Error ? error.message : String(error);
          steps.push({ toolName: "bash", input: { command }, output: `Error: ${errorMsg}` });
          return `Error executing command: ${errorMsg}`;
        }
      },
    });

    // Create text editor tool with actual file operations
    const textEditorTool = anthropic.tools.textEditor_20250124({
      execute: async ({ command, path, file_text, insert_line, new_str, old_str, view_range }) => {
        // Security: Validate path to prevent path traversal attacks
        const pathValidation = validatePath(path, this.config.workingDirectory);
        if (!pathValidation.valid) {
          steps.push({ toolName: "str_replace_editor", input: { command, path }, output: `Security Error: ${pathValidation.error}` });
          return `Security Error: ${pathValidation.error}`;
        }
        const fullPath = pathValidation.resolvedPath;

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
                  result = selectedLines
                    .map((line, i) => `${start + i}: ${line}`)
                    .join("\n");
                } else {
                  result = lines
                    .map((line, i) => `${i + 1}: ${line}`)
                    .join("\n");
                }
              }
              break;
            }

            case "create": {
              if (!file_text) {
                result = "Error: file_text is required for create command";
              } else {
                const dir = dirname(fullPath);
                if (!existsSync(dir)) {
                  mkdirSync(dir, { recursive: true });
                }
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

          steps.push({ 
            toolName: "str_replace_editor", 
            input: { command, path, file_text, insert_line, new_str, old_str, view_range }, 
            output: result 
          });
          return result;
        } catch (error) {
          const errorMsg = error instanceof Error ? error.message : String(error);
          steps.push({ 
            toolName: "str_replace_editor", 
            input: { command, path }, 
            output: `Error: ${errorMsg}` 
          });
          return `Error: ${errorMsg}`;
        }
      },
    });

    try {
      const result = await generateText({
        model: anthropic("claude-sonnet-4-20250514"),
        tools: {
          bash: bashTool,
          str_replace_editor: textEditorTool,
        },
        stopWhen: stepCountIs(this.config.maxSteps ?? 20),
        system: `You are a code assistant with access to bash and file editing tools.
Working directory: ${this.config.workingDirectory}

Guidelines:
- Use bash to run commands, tests, and git operations
- Use str_replace_editor to view and edit files
- Be precise with file paths
- Verify changes work before considering task complete
- If a command fails, analyze the error and try to fix it`,
        prompt: task,
      });

      return {
        success: true,
        result: result.text,
        steps,
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
   * Fix a specific file based on feedback
   */
  async fixFile(
    filePath: string,
    feedback: string,
    suggestion?: string
  ): Promise<{
    success: boolean;
    result: string;
    diff?: string;
  }> {
    const task = suggestion
      ? `Fix the file ${filePath} based on this feedback:
${feedback}

Apply this suggested change:
${suggestion}`
      : `Fix the file ${filePath} based on this feedback:
${feedback}

Analyze the file, understand the issue, and make the appropriate fix.`;

    const result = await this.execute(task);

    // Get diff if we made changes
    let diff: string | undefined;
    if (result.success) {
      try {
        diff = execSync(`git diff ${filePath}`, {
          cwd: this.config.workingDirectory,
          encoding: "utf-8",
        });
      } catch {
        // No diff available
      }
    }

    return {
      success: result.success,
      result: result.result,
      diff,
    };
  }

  /**
   * Run tests and fix failures
   */
  async fixTests(testCommand: string = "npm test"): Promise<{
    success: boolean;
    result: string;
    iterations: number;
  }> {
    const task = `Run the tests with "${testCommand}" and fix any failures.

Process:
1. Run the test command
2. If tests fail, analyze the failure
3. Fix the code causing the failure
4. Re-run tests
5. Repeat until all tests pass or you've tried 5 times`;

    const result = await this.execute(task);
    
    // Count iterations from steps
    const testRuns = result.steps.filter(
      (s) => s.toolName === "bash" && 
        typeof s.input === "object" && 
        s.input !== null &&
        "command" in s.input &&
        String(s.input.command).includes("test")
    ).length;

    return {
      success: result.success,
      result: result.result,
      iterations: testRuns,
    };
  }

  /**
   * Commit changes with a message
   */
  async commitChanges(message: string): Promise<{
    success: boolean;
    commitSha?: string;
  }> {
    const result = await this.execute(
      `Stage all changes and commit with message: "${message}"
      
Use these commands:
1. git add -A
2. git commit -m "${message}"
3. Output the commit SHA`
    );

    // Extract commit SHA from steps
    const commitStep = result.steps.find(
      (s) => s.toolName === "bash" && s.output.includes("commit")
    );
    
    let commitSha: string | undefined;
    if (commitStep) {
      const shaMatch = commitStep.output.match(/\[[\w-]+ ([a-f0-9]+)\]/);
      if (shaMatch) {
        commitSha = shaMatch[1];
      }
    }

    return {
      success: result.success,
      commitSha,
    };
  }
}
