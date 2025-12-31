#!/usr/bin/env node

/**
 * Test script for Cursor Cloud Agent API
 * 
 * Usage:
 * CURSOR_API_KEY=sk-... node scripts/test-cursor-api.mjs
 */

const CURSOR_API_KEY = process.env.CURSOR_API_KEY;
const CURSOR_BASE = 'https://api.cursor.com/v0';

if (!CURSOR_API_KEY) {
  console.error('❌ CURSOR_API_KEY not set');
  process.exit(1);
}

async function testApi() {
  console.log('🔍 Testing Cursor API...');
  
  try {
    // 1. List agents
    console.log('\n--- List Agents ---');
    const listRes = await fetch(`${CURSOR_BASE}/agents`, {
      headers: {
        'Authorization': `Bearer ${CURSOR_API_KEY}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!listRes.ok) {
      console.error(`❌ List Agents failed (${listRes.status}):`, await listRes.text());
    } else {
      const agents = await listRes.json();
      console.log(`✅ Found ${agents.agents?.length || 0} agents`);
    }

    // 2. List repositories
    console.log('\n--- List Repositories ---');
    const repoRes = await fetch(`${CURSOR_BASE}/repositories`, {
      headers: {
        'Authorization': `Bearer ${CURSOR_API_KEY}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!repoRes.ok) {
      console.error(`❌ List Repositories failed (${repoRes.status}):`, await repoRes.text());
    } else {
      const repos = await repoRes.json();
      console.log(`✅ Found ${repos.repositories?.length || 0} repositories`);
    }

    // 3. Test Launch Agent (Dry Run - usually just checking if we can send the request)
    console.log('\n--- Test Launch Agent (Check) ---');
    console.log('Note: We won\'t actually launch an agent unless you uncomment the code.');
    /*
    const launchRes = await fetch(`${CURSOR_BASE}/agents`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${CURSOR_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        prompt: { text: "Hello, this is a test from the control center." },
        source: { repository: "jbcom/control-center", ref: "main" },
        target: { autoCreatePr: false, openAsCursorGithubApp: true }
      })
    });
    
    if (!launchRes.ok) {
      console.error(`❌ Launch Agent failed (${launchRes.status}):`, await launchRes.text());
    } else {
      const agent = await launchRes.json();
      console.log(`✅ Agent launched successfully:`, agent);
    }
    */
    
  } catch (err) {
    console.error('❌ Error during test:', err.message);
  }
}

testApi();
