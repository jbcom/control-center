# AI SDK v5/v6 Reference for ai-triage Package

This document summarizes the key patterns and APIs from the Vercel AI SDK documentation
for use in the ai-triage package.

## Key Breaking Changes (v4 → v5)

### Tool Definitions
```typescript
// v4 (OLD)
tool({
  parameters: z.object({ ... }),
  execute: async (args) => { ... },
});

// v5 (NEW)
tool({
  inputSchema: z.object({ ... }),
  execute: async (input) => { ... },  // 'args' renamed to 'input'
});
```

### Message Types
- `CoreMessage` → `ModelMessage`
- `Message` → `UIMessage`  
- `convertToCoreMessages` → `convertToModelMessages`

### Step Control
```typescript
// v4 (OLD)
{ maxSteps: 5 }

// v5 (NEW)
import { stepCountIs } from 'ai';
{ stopWhen: stepCountIs(5) }
```

### Tool Results
- `args` → `input`
- `result` → `output`
- `experimental_toToolResultContent` → `toModelOutput`

### Usage Tokens
```typescript
// v4
{ promptTokens, completionTokens }

// v5
{ inputTokens, outputTokens, totalTokens }
```

## Anthropic Provider Tools

### Bash Tool (Latest: bash_20250124)
```typescript
import { anthropic } from '@ai-sdk/anthropic';

const bashTool = anthropic.tools.bash_20250124({
  execute: async ({ command, restart }) => {
    // Execute bash command
    return execSync(command).toString();
  },
});

// Tool name must be 'bash'
tools: { bash: bashTool }
```

### Text Editor Tool (Latest: textEditor_20250728)
```typescript
const textEditorTool = anthropic.tools.textEditor_20250728({
  maxCharacters: 10000, // optional
  execute: async ({ command, path, old_str, new_str, file_text, insert_line, view_range }) => {
    // Handle file operations based on command
    // command: 'view' | 'create' | 'str_replace' | 'insert'
  },
});

// Tool name must be 'str_replace_based_edit_tool'
tools: { str_replace_based_edit_tool: textEditorTool }
```

### Computer Tool (Latest: computer_20250124)
```typescript
const computerTool = anthropic.tools.computer_20250124({
  displayWidthPx: 1920,
  displayHeightPx: 1080,
  displayNumber: 0, // optional for X11
  execute: async ({ action, coordinate, text }) => {
    // Handle actions: screenshot, mouse_move, left_click, etc.
    return { type: 'image', data: base64Screenshot };
  },
  toModelOutput(result) {
    return typeof result === 'string'
      ? [{ type: 'text', text: result }]
      : [{ type: 'media', data: result.data, mediaType: 'image/png' }];
  },
});
```

### Web Search Tool
```typescript
const webSearchTool = anthropic.tools.webSearch_20250305({
  maxUses: 5,
  allowedDomains: ['example.com'],
  blockedDomains: ['spam.com'],
  userLocation: {
    type: 'approximate',
    country: 'US',
    region: 'California',
  },
});
```

### Code Execution Tool
```typescript
const codeExecutionTool = anthropic.tools.codeExecution_20250825();
```

## MCP Client Integration

### HTTP Transport (Recommended for Production)
```typescript
import { experimental_createMCPClient as createMCPClient } from '@ai-sdk/mcp';

const mcpClient = await createMCPClient({
  transport: {
    type: 'http',
    url: 'https://your-server.com/mcp',
    headers: { Authorization: 'Bearer my-api-key' },
  },
  name: 'my-mcp-client',
});

const tools = await mcpClient.tools();
await mcpClient.close();
```

### Stdio Transport (Local Servers Only)
```typescript
import { Experimental_StdioMCPTransport as StdioMCPTransport } from '@ai-sdk/mcp/mcp-stdio';

const mcpClient = await createMCPClient({
  transport: new StdioMCPTransport({
    command: 'npx',
    args: ['-y', 'cursor-background-agent-mcp-server'],
    env: { CURSOR_API_KEY: process.env.CURSOR_API_KEY },
  }),
  name: 'cursor-mcp',
});
```

### SSE Transport
```typescript
const mcpClient = await createMCPClient({
  transport: {
    type: 'sse',
    url: 'https://your-server.com/sse',
    headers: { Authorization: 'Bearer my-api-key' },
  },
});
```

## generateText / streamText Patterns

### Basic Usage with Tools
```typescript
import { generateText, tool, stepCountIs } from 'ai';
import { anthropic } from '@ai-sdk/anthropic';
import { z } from 'zod';

const result = await generateText({
  model: anthropic('claude-sonnet-4-20250514'),
  tools: {
    weather: tool({
      description: 'Get weather for a location',
      inputSchema: z.object({
        location: z.string().describe('The location'),
      }),
      execute: async ({ location }) => ({
        location,
        temperature: 72,
      }),
    }),
  },
  stopWhen: stepCountIs(5),
  system: 'You are a helpful assistant.',
  prompt: 'What is the weather in San Francisco?',
});

console.log(result.text);
console.log(result.steps); // Access all steps
console.log(result.toolCalls); // Last step's tool calls
console.log(result.totalUsage); // Total token usage across all steps
```

### Streaming with onStepFinish
```typescript
const result = streamText({
  model: anthropic('claude-sonnet-4-20250514'),
  tools: { /* ... */ },
  stopWhen: stepCountIs(5),
  onStepFinish: ({ text, toolCalls, toolResults, finishReason, usage }) => {
    console.log('Step finished:', { text, toolCalls, toolResults });
  },
  onFinish: ({ text, steps, totalUsage }) => {
    console.log('Completed:', text);
  },
  prompt: 'Do something complex',
});

for await (const chunk of result.textStream) {
  process.stdout.write(chunk);
}
```

### With MCP Tools
```typescript
const mcpClient = await createMCPClient({ /* ... */ });
const mcpTools = await mcpClient.tools();

const result = await generateText({
  model: anthropic('claude-sonnet-4-20250514'),
  tools: {
    ...mcpTools, // Spread MCP tools
    myCustomTool: tool({ /* ... */ }),
  },
  stopWhen: stepCountIs(10),
  onFinish: async () => {
    await mcpClient.close();
  },
});
```

## ToolLoopAgent (AI SDK v6 Beta)

### Basic Agent
```typescript
import { ToolLoopAgent, tool } from 'ai';
import { z } from 'zod';

const agent = new ToolLoopAgent({
  model: 'anthropic/claude-sonnet-4.5',
  instructions: 'You are a helpful assistant.',
  tools: {
    weather: tool({
      description: 'Get weather',
      inputSchema: z.object({ city: z.string() }),
      execute: async ({ city }) => ({ temp: 72 }),
    }),
  },
  // Default: stopWhen: stepCountIs(20)
});

const { text, steps, toolCalls, toolResults } = await agent.generate({
  prompt: 'What is the weather in SF?',
});
```

### Structured Output with Agent
```typescript
import { ToolLoopAgent, Output, tool } from 'ai';

const agent = new ToolLoopAgent({
  model: 'anthropic/claude-sonnet-4.5',
  tools: { /* ... */ },
  output: Output.object({
    schema: z.object({
      summary: z.string(),
      temperature: z.number(),
      recommendation: z.string(),
    }),
  }),
});

const { output } = await agent.generate({
  prompt: 'What should I wear in SF?',
});
// output is typed { summary, temperature, recommendation }
```

### Tool Approval
```typescript
const paymentTool = tool({
  description: 'Process a payment',
  inputSchema: z.object({
    amount: z.number(),
    recipient: z.string(),
  }),
  needsApproval: async ({ amount }) => amount > 1000, // Dynamic approval
  execute: async ({ amount, recipient }) => {
    return await processPayment(amount, recipient);
  },
});
```

## Manual Agent Loop

For complete control over the agent loop:

```typescript
import { ModelMessage, streamText, tool } from 'ai';
import { z } from 'zod';

const messages: ModelMessage[] = [
  { role: 'user', content: 'Get the weather in NYC and SF' },
];

async function runAgent() {
  while (true) {
    const result = streamText({
      model: 'openai/gpt-4o',
      messages,
      tools: {
        getWeather: tool({
          description: 'Get the current weather',
          inputSchema: z.object({ location: z.string() }),
          // No execute - we handle it manually
        }),
      },
    });

    // Stream the response
    for await (const chunk of result.fullStream) {
      if (chunk.type === 'text-delta') {
        process.stdout.write(chunk.text);
      }
    }

    // Add response messages to history
    const responseMessages = (await result.response).messages;
    messages.push(...responseMessages);

    const finishReason = await result.finishReason;

    if (finishReason === 'tool-calls') {
      const toolCalls = await result.toolCalls;

      for (const toolCall of toolCalls) {
        if (toolCall.toolName === 'getWeather') {
          const toolOutput = await fetchWeather(toolCall.input.location);
          messages.push({
            role: 'tool',
            content: [{
              toolName: toolCall.toolName,
              toolCallId: toolCall.toolCallId,
              type: 'tool-result',
              output: { type: 'text', value: toolOutput },
            }],
          });
        }
      }
    } else {
      break; // Exit when no more tool calls
    }
  }
}
```

## Reasoning Support (Claude)

```typescript
import { anthropic, AnthropicProviderOptions } from '@ai-sdk/anthropic';
import { generateText } from 'ai';

const { text, reasoningText, reasoning } = await generateText({
  model: anthropic('claude-opus-4-20250514'),
  prompt: 'Solve this complex problem...',
  providerOptions: {
    anthropic: {
      thinking: { type: 'enabled', budgetTokens: 12000 },
    } satisfies AnthropicProviderOptions,
  },
});

console.log(reasoning);     // Array of reasoning details
console.log(reasoningText); // Combined reasoning text
console.log(text);          // Final response
```

## Type Definitions

### Key Types
```typescript
import {
  generateText,
  streamText,
  tool,
  stepCountIs,
  hasToolCall,
  type ToolSet,
  type ModelMessage,
  type UIMessage,
  type LanguageModelUsage,
  type StopCondition,
} from 'ai';
```

### Tool Types
```typescript
import { TypedToolCall, TypedToolResult, ToolSet, tool } from 'ai';

const myTools = {
  weather: tool({ /* ... */ }),
  search: tool({ /* ... */ }),
} satisfies ToolSet;

type MyToolCall = TypedToolCall<typeof myTools>;
type MyToolResult = TypedToolResult<typeof myTools>;
```

## Error Handling

```typescript
import { NoSuchToolError, InvalidToolInputError } from 'ai';

try {
  const result = await generateText({ /* ... */ });
  
  // Check for tool errors in steps
  const toolErrors = result.steps.flatMap(step =>
    step.content.filter(part => part.type === 'tool-error')
  );
  
  toolErrors.forEach(error => {
    console.log('Tool error:', error.error);
    console.log('Tool name:', error.toolName);
    console.log('Tool input:', error.input);
  });
} catch (error) {
  if (NoSuchToolError.isInstance(error)) {
    console.log('Unknown tool:', error.message);
  } else if (InvalidToolInputError.isInstance(error)) {
    console.log('Invalid input:', error.message);
  }
}
```

---

## AI SDK v6 Beta Features

### ToolLoopAgent (Experimental)
```typescript
import { ToolLoopAgent, Output, tool } from 'ai';

const agent = new ToolLoopAgent({
  model: 'anthropic/claude-sonnet-4.5',
  instructions: 'You are a helpful assistant.',
  tools: { /* ... */ },
  // Default: stopWhen: stepCountIs(20)
  output: Output.object({
    schema: z.object({ /* structured output */ }),
  }),
});

const { text, output } = await agent.generate({
  prompt: 'Your task...',
});
```

### Tool Approval
```typescript
const sensitiveAction = tool({
  description: 'Performs a sensitive action',
  inputSchema: z.object({ /* ... */ }),
  needsApproval: true, // Static approval
  // OR dynamic:
  needsApproval: async ({ amount }) => amount > 1000,
  execute: async (input) => { /* ... */ },
});
```

### Web Search Tools
```typescript
// Anthropic native web search
const webSearch = anthropic.tools.webSearch_20250305({
  maxUses: 5,
  allowedDomains: ['docs.example.com'],
});

// OpenAI web search
const openaiSearch = openai.tools.webSearch({});

// Third-party: Exa
import { webSearch } from '@exalabs/ai-sdk';
tools: { webSearch: webSearch() }
```

### Code Execution
```typescript
const codeExec = anthropic.tools.codeExecution_20250825();

const result = await generateText({
  model: anthropic('claude-sonnet-4-20250514'),
  tools: { code_execution: codeExec },
  prompt: 'Calculate the fibonacci sequence...',
});
```

### Reranking
```typescript
import { rerank } from 'ai';
import { cohere } from '@ai-sdk/cohere';

const { ranking } = await rerank({
  model: cohere.reranking('rerank-v3.5'),
  documents: ['doc1', 'doc2', 'doc3'],
  query: 'search query',
  topN: 2,
});
```

## Workflow Patterns

### Sequential Chain
```typescript
const { text: step1 } = await generateText({ /* ... */ });
const { object: analysis } = await generateObject({
  schema: analysisSchema,
  prompt: `Analyze: ${step1}`,
});
```

### Parallel Processing
```typescript
const [security, performance, quality] = await Promise.all([
  generateObject({ system: 'security expert', /* ... */ }),
  generateObject({ system: 'performance expert', /* ... */ }),
  generateObject({ system: 'quality expert', /* ... */ }),
]);
```

### Evaluator-Optimizer Loop
```typescript
while (iterations < MAX_ITERATIONS) {
  const { object: evaluation } = await generateObject({
    schema: qualitySchema,
    prompt: `Evaluate: ${currentResult}`,
  });
  
  if (evaluation.qualityScore >= 8) break;
  
  currentResult = await generateText({
    prompt: `Improve based on: ${evaluation.feedback}`,
  });
  iterations++;
}
```

---

## Package Versions

For ai-triage, use these versions:
```json
{
  "ai": "^5.0.0",
  "@ai-sdk/anthropic": "^2.0.0",
  "@ai-sdk/mcp": "^1.0.0-beta.24",
  "@modelcontextprotocol/sdk": "^1.23.0",
  "zod": "^3.24.4"
}
```

---

*Reference: Compiled from Vercel AI SDK v5/v6 documentation at https://ai-sdk.dev*
*Last updated: 2025-11-30*
