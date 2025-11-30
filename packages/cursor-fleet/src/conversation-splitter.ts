/**
 * Conversation Splitter
 * 
 * Splits large conversation JSON files into manageable chunks using @codetailor/split-json
 * and additional custom splitting for readability.
 */

import { writeFile, mkdir, readFile } from "node:fs/promises";
import { join, dirname } from "node:path";
import { createRequire } from "node:module";
import type { Conversation, Message } from "./types.js";

const require = createRequire(import.meta.url);
const split: (
  inputFilePath: string,
  outputFolder: string,
  outputPrefix: string,
  maxItemsPerFile?: number,
  minPartNumberLength?: number
) => Promise<unknown> = require("@codetailor/split-json");

export interface SplitOptions {
  /** Messages per batch file (default: 10) */
  batchSize?: number;
  /** Create individual message files (default: true) */
  individualFiles?: boolean;
  /** Create markdown versions (default: true) */
  markdown?: boolean;
  /** Create index file (default: true) */
  createIndex?: boolean;
}

export interface SplitResult {
  outputDir: string;
  messageCount: number;
  batchCount: number;
  files: {
    messages: string[];
    batches: string[];
    index?: string;
    fullConversation: string;
  };
}

/**
 * Split a conversation JSON file into a structured directory
 */
export async function splitConversation(
  conversationPath: string,
  outputDir: string,
  options: SplitOptions = {}
): Promise<SplitResult> {
  const {
    batchSize = 10,
    individualFiles = true,
    markdown = true,
    createIndex = true,
  } = options;

  // Read conversation
  const rawData = await readFile(conversationPath, "utf-8");
  const conversation: Conversation = JSON.parse(rawData);
  const messages = conversation.messages || [];

  // Create output directories
  const messagesDir = join(outputDir, "messages");
  const batchesDir = join(outputDir, "batches");
  await mkdir(messagesDir, { recursive: true });
  await mkdir(batchesDir, { recursive: true });

  const result: SplitResult = {
    outputDir,
    messageCount: messages.length,
    batchCount: Math.ceil(messages.length / batchSize),
    files: {
      messages: [],
      batches: [],
      fullConversation: conversationPath,
    },
  };

  // Extract just the messages array for split-json
  const messagesArrayPath = join(outputDir, "_messages_array.json");
  await writeFile(messagesArrayPath, JSON.stringify(messages));

  // Use split-json for batch splitting
  try {
    await split(messagesArrayPath, batchesDir, "batch-", batchSize, 3);
  } catch (err) {
    // Fallback to manual splitting if split-json fails
    console.warn("split-json failed, using manual splitting:", err);
    await manualBatchSplit(messages, batchesDir, batchSize);
  }

  // Create individual message files if requested
  if (individualFiles) {
    for (let i = 0; i < messages.length; i++) {
      const msg = messages[i];
      const num = String(i + 1).padStart(4, "0");
      const role = msg.type === "user_message" ? "USER" : "ASST";
      
      // JSON file
      const jsonPath = join(messagesDir, `${num}-${role}.json`);
      await writeFile(jsonPath, JSON.stringify(msg, null, 2));
      result.files.messages.push(jsonPath);

      // Markdown file
      if (markdown) {
        const mdPath = join(messagesDir, `${num}-${role}.md`);
        await writeFile(mdPath, formatMessageAsMarkdown(msg, i + 1));
      }
    }
  }

  // Create batch markdown files
  if (markdown) {
    for (let i = 0; i < messages.length; i += batchSize) {
      const batch = messages.slice(i, i + batchSize);
      const batchNum = String(Math.floor(i / batchSize) + 1).padStart(3, "0");
      const start = i + 1;
      const end = Math.min(i + batchSize, messages.length);
      
      const mdPath = join(batchesDir, `batch-${batchNum}.md`);
      await writeFile(mdPath, formatBatchAsMarkdown(batch, start, end));
      result.files.batches.push(mdPath);
    }
  }

  // Create index file
  if (createIndex) {
    const indexPath = join(outputDir, "INDEX.md");
    await writeFile(indexPath, createIndexMarkdown(conversation, messages));
    result.files.index = indexPath;
  }

  // Create conversation metadata
  const metaPath = join(outputDir, "metadata.json");
  await writeFile(metaPath, JSON.stringify({
    agentId: conversation.id || conversation.agentId,
    messageCount: messages.length,
    batchCount: result.batchCount,
    batchSize,
    splitAt: new Date().toISOString(),
    userMessages: messages.filter(m => m.type === "user_message").length,
    assistantMessages: messages.filter(m => m.type === "assistant_message").length,
  }, null, 2));

  // Clean up temp file
  try {
    const { unlink } = await import("node:fs/promises");
    await unlink(messagesArrayPath);
  } catch { /* ignore */ }

  return result;
}

/**
 * Manual batch splitting fallback
 */
async function manualBatchSplit(messages: Message[], outputDir: string, batchSize: number): Promise<void> {
  for (let i = 0; i < messages.length; i += batchSize) {
    const batch = messages.slice(i, i + batchSize);
    const batchNum = String(Math.floor(i / batchSize) + 1).padStart(3, "0");
    const batchPath = join(outputDir, `batch-${batchNum}.json`);
    await writeFile(batchPath, JSON.stringify(batch, null, 2));
  }
}

/**
 * Format a single message as markdown
 */
function formatMessageAsMarkdown(msg: Message, index: number): string {
  const role = msg.type === "user_message" ? "👤 User" : "🤖 Assistant";
  return `# Message ${index} - ${role}

**ID**: \`${msg.id || "N/A"}\`
**Type**: ${msg.type}
${msg.timestamp ? `**Time**: ${msg.timestamp}` : ""}

---

${msg.text}
`;
}

/**
 * Format a batch of messages as markdown
 */
function formatBatchAsMarkdown(batch: Message[], start: number, end: number): string {
  let md = `# Messages ${start}-${end}

`;
  for (let i = 0; i < batch.length; i++) {
    const msg = batch[i];
    const msgNum = start + i;
    const role = msg.type === "user_message" ? "👤 USER" : "🤖 ASSISTANT";
    md += `## [${msgNum}] ${role}

${msg.text}

---

`;
  }
  return md;
}

/**
 * Create index markdown file
 */
function createIndexMarkdown(conversation: Conversation, messages: Message[]): string {
  const userCount = messages.filter(m => m.type === "user_message").length;
  const asstCount = messages.filter(m => m.type === "assistant_message").length;

  let md = `# Conversation Index

**Agent ID**: \`${conversation.id || conversation.agentId || "Unknown"}\`
**Total Messages**: ${messages.length}
**User Messages**: ${userCount}
**Assistant Messages**: ${asstCount}

---

## Message List

| # | Type | Preview |
|---|------|---------|
`;

  for (let i = 0; i < messages.length; i++) {
    const msg = messages[i];
    const num = String(i + 1).padStart(4, "0");
    const role = msg.type === "user_message" ? "👤" : "🤖";
    const roleFile = msg.type === "user_message" ? "USER" : "ASST";
    const preview = msg.text
      .replace(/\n/g, " ")
      .replace(/\|/g, "\\|")
      .slice(0, 60);
    md += `| [${num}](messages/${num}-${roleFile}.md) | ${role} | ${preview}... |\n`;
  }

  md += `
---

## Batches

`;

  const batchSize = 10;
  const batchCount = Math.ceil(messages.length / batchSize);
  for (let i = 0; i < batchCount; i++) {
    const batchNum = String(i + 1).padStart(3, "0");
    const start = i * batchSize + 1;
    const end = Math.min((i + 1) * batchSize, messages.length);
    md += `- [Batch ${batchNum}](batches/batch-${batchNum}.md) - Messages ${start}-${end}\n`;
  }

  md += `
---

_Split by cursor-fleet at ${new Date().toISOString()}_
`;

  return md;
}

/**
 * Read a specific batch from a split conversation
 */
export async function readBatch(outputDir: string, batchNumber: number): Promise<Message[]> {
  const batchNum = String(batchNumber).padStart(3, "0");
  const batchPath = join(outputDir, "batches", `batch-${batchNum}.json`);
  const data = await readFile(batchPath, "utf-8");
  return JSON.parse(data);
}

/**
 * Read a specific message from a split conversation
 */
export async function readMessage(outputDir: string, messageNumber: number): Promise<Message> {
  const files = await import("node:fs/promises").then(m => m.readdir(join(outputDir, "messages")));
  const num = String(messageNumber).padStart(4, "0");
  const jsonFile = files.find(f => f.startsWith(num) && f.endsWith(".json"));
  if (!jsonFile) {
    throw new Error(`Message ${messageNumber} not found`);
  }
  const data = await readFile(join(outputDir, "messages", jsonFile), "utf-8");
  return JSON.parse(data);
}
