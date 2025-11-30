/**
 * Conversation Splitter
 * 
 * Splits large conversation JSON into smaller, readable files for analysis.
 * Used for replaying and analyzing agent sessions.
 */

import { writeFileSync, mkdirSync, existsSync } from "node:fs";
import { join } from "node:path";
import type { Conversation, Message } from "./types.js";

export interface SplitOptions {
  /** Output directory for split files */
  outputDir: string;
  /** Number of messages per batch file (default: 50) */
  batchSize?: number;
  /** Include message timestamps in filenames */
  includeTimestamps?: boolean;
  /** Pretty print JSON output */
  prettyPrint?: boolean;
}

export interface SplitResult {
  /** Total number of messages processed */
  totalMessages: number;
  /** Number of batch files created */
  batchFiles: number;
  /** Number of individual message files created */
  messageFiles: number;
  /** Path to the output directory */
  outputDir: string;
  /** List of created files */
  files: string[];
}

/**
 * Extracts the message role from various conversation formats
 */
function getMessageRole(msg: Message): string {
  // Message type uses "user_message" or "assistant_message"
  if (msg.type === "user_message") return "user";
  if (msg.type === "assistant_message") return "assistant";
  return "unknown";
}

/**
 * Formats message content for readable output
 */
function formatMessageContent(msg: Message): string {
  // Message type uses "text" field
  return msg.text || "";
}

/**
 * Creates a readable text summary of a message
 */
function createMessageSummary(msg: Message, index: number): string {
  const role = getMessageRole(msg);
  const content = formatMessageContent(msg);
  const timestamp = msg.timestamp || "";
  
  const lines: string[] = [
    `=== Message ${index + 1} ===`,
    `Role: ${role}`,
  ];
  
  if (timestamp) {
    lines.push(`Time: ${timestamp}`);
  }
  
  lines.push("", "Content:", "---", content, "---", "");
  
  return lines.join("\n");
}

/**
 * Splits a conversation into multiple files for easier analysis
 */
export async function splitConversation(
  conversation: Conversation,
  options: SplitOptions
): Promise<SplitResult> {
  const {
    outputDir,
    batchSize = 50,
    includeTimestamps = true,
    prettyPrint = true,
  } = options;

  const files: string[] = [];
  
  // Ensure output directory exists
  if (!existsSync(outputDir)) {
    mkdirSync(outputDir, { recursive: true });
  }

  const messages = conversation.messages || [];
  const totalMessages = messages.length;

  // Create individual messages directory
  const messagesDir = join(outputDir, "messages");
  mkdirSync(messagesDir, { recursive: true });

  // Create batches directory
  const batchesDir = join(outputDir, "batches");
  mkdirSync(batchesDir, { recursive: true });

  // Write conversation metadata
  const metadata = {
    agentId: conversation.agentId || "unknown",
    totalMessages,
    batchSize,
    createdAt: new Date().toISOString(),
  };
  const metadataPath = join(outputDir, "metadata.json");
  writeFileSync(metadataPath, JSON.stringify(metadata, null, 2));
  files.push(metadataPath);

  // Write individual message files
  let messageFiles = 0;
  for (let i = 0; i < messages.length; i++) {
    const msg = messages[i];
    const role = getMessageRole(msg);
    const filename = `${String(i + 1).padStart(4, "0")}_${role}.json`;
    const filepath = join(messagesDir, filename);
    
    const jsonStr = prettyPrint 
      ? JSON.stringify(msg, null, 2) 
      : JSON.stringify(msg);
    writeFileSync(filepath, jsonStr);
    files.push(filepath);
    messageFiles++;

    // Also write readable text version
    const textFilename = `${String(i + 1).padStart(4, "0")}_${role}.txt`;
    const textFilepath = join(messagesDir, textFilename);
    writeFileSync(textFilepath, createMessageSummary(msg, i));
    files.push(textFilepath);
  }

  // Write batch files
  let batchFiles = 0;
  for (let i = 0; i < messages.length; i += batchSize) {
    const batch = messages.slice(i, i + batchSize);
    const batchNum = Math.floor(i / batchSize) + 1;
    const filename = `batch_${String(batchNum).padStart(3, "0")}.json`;
    const filepath = join(batchesDir, filename);
    
    const batchData = {
      batchNumber: batchNum,
      startIndex: i,
      endIndex: Math.min(i + batchSize - 1, messages.length - 1),
      messageCount: batch.length,
      messages: batch,
    };
    
    const jsonStr = prettyPrint 
      ? JSON.stringify(batchData, null, 2) 
      : JSON.stringify(batchData);
    writeFileSync(filepath, jsonStr);
    files.push(filepath);
    batchFiles++;

    // Also write readable batch summary
    const textFilename = `batch_${String(batchNum).padStart(3, "0")}.txt`;
    const textFilepath = join(batchesDir, textFilename);
    const summaries = batch.map((msg, idx) => 
      createMessageSummary(msg, i + idx)
    ).join("\n");
    writeFileSync(textFilepath, summaries);
    files.push(textFilepath);
  }

  // Write full readable conversation
  const fullReadablePath = join(outputDir, "conversation.txt");
  const fullReadable = messages
    .map((msg, idx) => createMessageSummary(msg, idx))
    .join("\n");
  writeFileSync(fullReadablePath, fullReadable);
  files.push(fullReadablePath);

  // Write original JSON (for reference)
  const originalPath = join(outputDir, "original.json");
  const originalStr = prettyPrint 
    ? JSON.stringify(conversation, null, 2) 
    : JSON.stringify(conversation);
  writeFileSync(originalPath, originalStr);
  files.push(originalPath);

  return {
    totalMessages,
    batchFiles,
    messageFiles,
    outputDir,
    files,
  };
}

/**
 * Quick split - minimal options for rapid splitting
 */
export async function quickSplit(
  conversation: Conversation,
  outputDir: string
): Promise<SplitResult> {
  return splitConversation(conversation, { outputDir });
}
