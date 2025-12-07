#!/usr/bin/env node
/**
 * Sandbox Execution Script
 * 
 * Executes AI agents in an isolated environment with support for
 * multiple runtimes (Claude, Cursor, Custom).
 * 
 * Based on patterns from claude-code-templates, adapted for agentic-control.
 */

import { spawn } from 'child_process';
import { promises as fs } from 'fs';
import path from 'path';

// Environment configuration
const WORKSPACE = process.env.AGENTIC_WORKSPACE || '/workspace';
const OUTPUT = process.env.AGENTIC_OUTPUT || '/output';
const RUNTIME = process.env.AGENTIC_SANDBOX_RUNTIME || 'claude';
const TIMEOUT = parseInt(process.env.AGENTIC_SANDBOX_TIMEOUT || '300', 10) * 1000;

/**
 * Runtime executors for different AI backends
 */
const runtimes = {
  /**
   * Claude runtime using @anthropic-ai/claude-agent-sdk
   */
  async claude(prompt, options = {}) {
    const { Anthropic } = await import('@anthropic-ai/sdk');
    const { Agent } = await import('@anthropic-ai/claude-agent-sdk');

    const client = new Anthropic();
    const agent = new Agent({
      client,
      model: options.model || 'claude-sonnet-4-20250514',
      workingDirectory: WORKSPACE,
    });

    console.log('🤖 Starting Claude agent...');
    console.log(`📁 Workspace: ${WORKSPACE}`);
    console.log(`📤 Output: ${OUTPUT}`);
    console.log('');

    const startTime = Date.now();
    let totalCost = 0;
    let turns = 0;

    // Use async generator for streaming
    const generator = agent.run(prompt);
    
    for await (const message of generator) {
      if (message.type === 'assistant') {
        for (const block of message.content) {
          if (block.type === 'text') {
            process.stdout.write(block.text);
          } else if (block.type === 'tool_use') {
            console.log(`\n🔧 Tool: ${block.name}`);
          }
        }
      } else if (message.type === 'result') {
        totalCost = message.total_cost_usd || 0;
        turns = message.num_turns || 0;
      }
    }

    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    
    console.log('\n');
    console.log('─'.repeat(50));
    console.log(`✅ Completed in ${elapsed}s (${turns} turns)`);
    console.log(`💰 Cost: $${totalCost.toFixed(5)} USD`);

    return { success: true, turns, cost: totalCost, elapsed };
  },

  /**
   * Cursor runtime (placeholder - would integrate with Cursor API)
   */
  async cursor(prompt, options = {}) {
    console.log('🖱️ Cursor runtime not yet implemented');
    console.log('   This would integrate with Cursor background agent API');
    
    // Placeholder for Cursor integration
    // Would use Cursor's API to spawn background agents
    
    return { success: false, error: 'Not implemented' };
  },

  /**
   * Custom script runtime
   */
  async custom(prompt, options = {}) {
    const script = options.script || process.env.AGENTIC_CUSTOM_SCRIPT;
    
    if (!script) {
      throw new Error('Custom runtime requires --script or AGENTIC_CUSTOM_SCRIPT');
    }

    console.log(`🔧 Running custom script: ${script}`);
    
    return new Promise((resolve, reject) => {
      const proc = spawn(script, [prompt], {
        cwd: WORKSPACE,
        env: { ...process.env, PROMPT: prompt },
        stdio: 'inherit',
      });

      proc.on('close', (code) => {
        if (code === 0) {
          resolve({ success: true });
        } else {
          reject(new Error(`Script exited with code ${code}`));
        }
      });
    });
  },
};

/**
 * Copy generated files to output directory
 */
async function extractOutput() {
  const files = await fs.readdir(WORKSPACE);
  const generatedFiles = [];

  for (const file of files) {
    const srcPath = path.join(WORKSPACE, file);
    const stat = await fs.stat(srcPath);
    
    // Copy new/modified files to output
    // In a real implementation, would track file changes
    if (stat.isFile()) {
      const destPath = path.join(OUTPUT, file);
      await fs.copyFile(srcPath, destPath);
      generatedFiles.push(file);
    }
  }

  if (generatedFiles.length > 0) {
    console.log(`\n📦 Extracted ${generatedFiles.length} files to ${OUTPUT}`);
  }
}

/**
 * Parse command line arguments
 */
function parseArgs(args) {
  const options = {
    runtime: RUNTIME,
    prompt: '',
    model: undefined,
    script: undefined,
    timeout: TIMEOUT,
    yes: false,
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    
    switch (arg) {
      case '--runtime':
      case '-r':
        options.runtime = args[++i];
        break;
      case '--prompt':
      case '-p':
        options.prompt = args[++i];
        break;
      case '--model':
      case '-m':
        options.model = args[++i];
        break;
      case '--script':
        options.script = args[++i];
        break;
      case '--timeout':
      case '-t':
        options.timeout = parseInt(args[++i], 10) * 1000;
        break;
      case '--yes':
      case '-y':
        options.yes = true;
        break;
      default:
        // Positional argument = prompt
        if (!arg.startsWith('-') && !options.prompt) {
          options.prompt = arg;
        }
    }
  }

  return options;
}

/**
 * Main execution
 */
async function main() {
  const args = process.argv.slice(2);
  const options = parseArgs(args);

  if (!options.prompt) {
    console.error('❌ Error: No prompt provided');
    console.error('Usage: sandbox run --prompt "Your task" [--runtime claude|cursor|custom]');
    process.exit(1);
  }

  const runtime = runtimes[options.runtime];
  if (!runtime) {
    console.error(`❌ Error: Unknown runtime "${options.runtime}"`);
    console.error('Available runtimes: claude, cursor, custom');
    process.exit(1);
  }

  console.log('╔════════════════════════════════════════════════════════════╗');
  console.log('║           agentic-control sandbox execution                ║');
  console.log('╠════════════════════════════════════════════════════════════╣');
  console.log(`║ Runtime:   ${options.runtime.padEnd(47)}║`);
  console.log(`║ Workspace: ${WORKSPACE.padEnd(47)}║`);
  console.log(`║ Output:    ${OUTPUT.padEnd(47)}║`);
  console.log('╚════════════════════════════════════════════════════════════╝');
  console.log('');
  console.log('📝 Prompt:');
  console.log(options.prompt);
  console.log('');
  console.log('─'.repeat(60));
  console.log('');

  try {
    // Execute with timeout
    const timeoutPromise = new Promise((_, reject) => {
      setTimeout(() => reject(new Error('Execution timeout')), options.timeout);
    });

    const result = await Promise.race([
      runtime(options.prompt, options),
      timeoutPromise,
    ]);

    // Extract output files
    await extractOutput();

    console.log('');
    console.log('🎉 Sandbox execution complete!');
    
  } catch (error) {
    console.error('');
    console.error(`❌ Error: ${error.message}`);
    process.exit(1);
  }
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
