#!/usr/bin/env node
/**
 * Investigation Script: Test Cursor API Followup Delivery
 * 
 * This script tests the reliability of bidirectional followup delivery
 * between Cursor agents using the Cursor API.
 * 
 * Test Scenario:
 * 1. Launch Agent A
 * 2. Launch Agent B
 * 3. Agent A sends followup to Agent B
 * 4. Poll Agent B conversation to verify receipt
 * 5. Agent B sends followup to Agent A
 * 6. Poll Agent A conversation to verify receipt
 * 
 * Expected: Both agents should see followups in their conversation history
 * Observed: Need to test if followups reliably appear or if there's eventual consistency delay
 */

import { CursorAPI } from "./cursor-api.js";
import type { Conversation } from "./types.js";

interface TestResult {
  success: boolean;
  message: string;
  details?: unknown;
}

class FollowupDeliveryTest {
  private api: CursorAPI;
  private testRepo: string;
  private testRef: string;

  constructor() {
    this.api = new CursorAPI();
    // Use a test repository - must have Cursor GitHub App installed
    this.testRepo = process.env.TEST_REPO || "https://github.com/jbcom/jbcom-control-center";
    this.testRef = process.env.TEST_REF || "main";
  }

  /**
   * Wait for a specific time
   */
  private async wait(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Check if a conversation contains a specific text
   */
  private conversationContains(conversation: Conversation, searchText: string): boolean {
    return conversation.messages.some(msg => 
      msg.text?.includes(searchText)
    );
  }

  /**
   * Poll conversation until text appears or timeout
   */
  private async pollForText(
    agentId: string,
    searchText: string,
    timeoutMs: number = 60000,
    intervalMs: number = 5000
  ): Promise<TestResult> {
    const startTime = Date.now();
    let attempts = 0;

    while (Date.now() - startTime < timeoutMs) {
      attempts++;
      const convResult = await this.api.getAgentConversation(agentId);
      
      if (!convResult.success || !convResult.data) {
        console.log(`  ⚠️  Attempt ${attempts}: Failed to get conversation - ${convResult.error}`);
      } else {
        if (this.conversationContains(convResult.data, searchText)) {
          return {
            success: true,
            message: `Text found after ${attempts} attempts (${Date.now() - startTime}ms)`,
            details: { attempts, elapsed: Date.now() - startTime }
          };
        }
        console.log(`  ⏳ Attempt ${attempts}: Text not found yet (${convResult.data.messages.length} messages)`);
      }

      await this.wait(intervalMs);
    }

    return {
      success: false,
      message: `Text not found after ${attempts} attempts (${timeoutMs}ms timeout)`,
      details: { attempts, timeout: timeoutMs }
    };
  }

  /**
   * Run the followup delivery test
   */
  async runTest(): Promise<void> {
    console.log("🧪 Testing Cursor API Followup Delivery\n");
    console.log(`Repository: ${this.testRepo}`);
    console.log(`Ref: ${this.testRef}\n`);

    try {
      // ===== Step 1: Launch Agent A =====
      console.log("1️⃣  Launching Agent A...");
      const agentAResult = await this.api.launchAgent({
        prompt: {
          text: "TEST AGENT A - Do nothing, just wait for followup messages. Mark this task as COMPLETED when you receive a followup from Agent B."
        },
        source: {
          repository: this.testRepo,
          ref: this.testRef
        }
      });

      if (!agentAResult.success || !agentAResult.data) {
        console.error("❌ Failed to launch Agent A:", agentAResult.error);
        return;
      }

      const agentAId = agentAResult.data.id;
      console.log(`✅ Agent A launched: ${agentAId}\n`);

      // ===== Step 2: Launch Agent B =====
      console.log("2️⃣  Launching Agent B...");
      const agentBResult = await this.api.launchAgent({
        prompt: {
          text: "TEST AGENT B - Do nothing, just wait for followup messages. Mark this task as COMPLETED when you receive a followup from Agent A."
        },
        source: {
          repository: this.testRepo,
          ref: this.testRef
        }
      });

      if (!agentBResult.success || !agentBResult.data) {
        console.error("❌ Failed to launch Agent B:", agentBResult.error);
        return;
      }

      const agentBId = agentBResult.data.id;
      console.log(`✅ Agent B launched: ${agentBId}\n`);

      // Wait for agents to initialize
      console.log("⏳ Waiting 10s for agents to initialize...\n");
      await this.wait(10000);

      // ===== Step 3: Agent A sends followup to Agent B =====
      console.log("3️⃣  Agent A sending followup to Agent B...");
      const followupAtoB = `FOLLOWUP_A_TO_B: Hello from Agent A (${agentAId})`;
      const followupAResult = await this.api.addFollowup(agentBId, {
        text: followupAtoB
      });

      if (!followupAResult.success) {
        console.error("❌ Failed to send followup A→B:", followupAResult.error);
        return;
      }
      console.log("✅ Followup A→B sent successfully\n");

      // ===== Step 4: Poll Agent B for the followup =====
      console.log("4️⃣  Polling Agent B conversation for followup from A...");
      const resultBReceived = await this.pollForText(agentBId, "FOLLOWUP_A_TO_B", 60000, 5000);
      
      if (resultBReceived.success) {
        console.log(`✅ ${resultBReceived.message}\n`);
      } else {
        console.error(`❌ ${resultBReceived.message}\n`);
        console.log("⚠️  Agent B did NOT receive followup from Agent A");
        console.log("   This indicates a potential API limitation or delay\n");
      }

      // ===== Step 5: Agent B sends followup to Agent A =====
      console.log("5️⃣  Agent B sending followup to Agent A...");
      const followupBtoA = `FOLLOWUP_B_TO_A: Hello from Agent B (${agentBId})`;
      const followupBResult = await this.api.addFollowup(agentAId, {
        text: followupBtoA
      });

      if (!followupBResult.success) {
        console.error("❌ Failed to send followup B→A:", followupBResult.error);
        return;
      }
      console.log("✅ Followup B→A sent successfully\n");

      // ===== Step 6: Poll Agent A for the followup =====
      console.log("6️⃣  Polling Agent A conversation for followup from B...");
      const resultAReceived = await this.pollForText(agentAId, "FOLLOWUP_B_TO_A", 60000, 5000);
      
      if (resultAReceived.success) {
        console.log(`✅ ${resultAReceived.message}\n`);
      } else {
        console.error(`❌ ${resultAReceived.message}\n`);
        console.log("⚠️  Agent A did NOT receive followup from Agent B");
        console.log("   This indicates a potential API limitation or delay\n");
      }

      // ===== Summary =====
      console.log("\n📊 Test Summary:");
      console.log("─────────────────────────────────────");
      console.log(`Agent A → Agent B: ${resultBReceived.success ? '✅ DELIVERED' : '❌ NOT DELIVERED'}`);
      console.log(`Agent B → Agent A: ${resultAReceived.success ? '✅ DELIVERED' : '❌ NOT DELIVERED'}`);
      console.log("─────────────────────────────────────");

      if (resultBReceived.success && resultAReceived.success) {
        console.log("\n✅ CONCLUSION: Bidirectional followups ARE working reliably");
        console.log("   The issue may be with specific usage patterns or timing");
      } else if (!resultBReceived.success && !resultAReceived.success) {
        console.log("\n❌ CONCLUSION: Bidirectional followups are NOT working");
        console.log("   This is a confirmed Cursor API limitation");
      } else {
        console.log("\n⚠️  CONCLUSION: Followups are PARTIALLY working");
        console.log("   There may be eventual consistency issues");
      }

      console.log(`\nAgent IDs for manual verification:`);
      console.log(`  Agent A: ${agentAId}`);
      console.log(`  Agent B: ${agentBId}`);

    } catch (error) {
      console.error("\n💥 Test failed with error:", error);
      throw error;
    }
  }
}

// Run the test if this is the main module
if (import.meta.url === `file://${process.argv[1]}`) {
  const test = new FollowupDeliveryTest();
  test.runTest()
    .then(() => {
      console.log("\n✅ Test completed");
      process.exit(0);
    })
    .catch(error => {
      console.error("\n❌ Test failed:", error);
      process.exit(1);
    });
}

export { FollowupDeliveryTest };
