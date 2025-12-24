#!/usr/bin/env node

/**
 * Cursor & Jules Orchestrator
 * Manages multi-agent orchestration between Cursor Cloud Agents and Google Jules.
 */

import { execSync } from 'child_process';

// Configuration from environment
const GITHUB_TOKEN = process.env.GITHUB_TOKEN || process.env.CI_GITHUB_TOKEN;
const CURSOR_TOKEN = process.env.CURSOR_TOKEN;
const GOOGLE_API_KEY = process.env.GOOGLE_API_KEY;

const CURSOR_API_URL = 'https://api.cursor.com/v0/agents';
const JULES_API_URL = 'https://jules.googleapis.com/v1alpha/sessions';

/**
 * GitHub API & CLI Helpers
 */
const github = {
  /**
   * Check status of a PR
   * @param {string} repo - Format: owner/repo
   * @param {number} prNumber 
   */
  async getPRStatus(repo, prNumber) {
    try {
      const output = execSync(`gh pr view ${prNumber} --repo ${repo} --json state,mergeable,reviewDecision`, { encoding: 'utf8' });
      return JSON.parse(output);
    } catch (error) {
      console.error(`Error fetching PR status for ${repo}#${prNumber}:`, error.message);
      return null;
    }
  },

  /**
   * Merge a PR if it's ready
   * @param {string} repo 
   * @param {number} prNumber 
   */
  async mergePR(repo, prNumber) {
    try {
      console.log(`Merging PR ${repo}#${prNumber}...`);
      execSync(`gh pr merge ${prNumber} --repo ${repo} --squash --delete-branch`, { stdio: 'inherit' });
      return true;
    } catch (error) {
      console.error(`Failed to merge PR ${repo}#${prNumber}:`, error.message);
      return false;
    }
  }
};

/**
 * Cursor Cloud Agent API
 */
const cursor = {
  async createAgent(prompt, context = {}) {
    if (!CURSOR_TOKEN) throw new Error('CURSOR_TOKEN is not set');
    
    const response = await fetch(CURSOR_API_URL, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${CURSOR_TOKEN}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ prompt, context })
    });
    
    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Cursor API Error: ${response.status} ${error}`);
    }
    
    return await response.json();
  },

  async getAgentStatus(agentId) {
    if (!CURSOR_TOKEN) throw new Error('CURSOR_TOKEN is not set');

    const response = await fetch(`${CURSOR_API_URL}/${agentId}`, {
      headers: {
        'Authorization': `Bearer ${CURSOR_TOKEN}`
      }
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Cursor API Error: ${response.status} ${error}`);
    }

    return await response.json();
  }
};

/**
 * Google Jules API
 */
const jules = {
  async createSession(instructions, files = []) {
    if (!GOOGLE_API_KEY) throw new Error('GOOGLE_API_KEY is not set');

    const response = await fetch(JULES_API_URL, {
      method: 'POST',
      headers: {
        'X-Goog-Api-Key': GOOGLE_API_KEY,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ instructions, files })
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Jules API Error: ${response.status} ${error}`);
    }

    return await response.json();
  },

  async getSessionStatus(sessionId) {
    if (!GOOGLE_API_KEY) throw new Error('GOOGLE_API_KEY is not set');

    const response = await fetch(`${JULES_API_URL}/${sessionId}`, {
      headers: {
        'X-Goog-Api-Key': GOOGLE_API_KEY
      }
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Jules API Error: ${response.status} ${error}`);
    }

    return await response.json();
  }
};

/**
 * Main Orchestration Logic
 */
async function orchestrate(options = {}) {
  const { repo, agents = [] } = options;
  console.log(`Starting orchestration for ${repo}...`);

  for (const agent of agents) {
    console.log(`Monitoring ${agent.type} agent ${agent.id}...`);
    
    let status;
    if (agent.type === 'cursor') {
      status = await cursor.getAgentStatus(agent.id);
    } else if (agent.type === 'jules') {
      status = await jules.getSessionStatus(agent.id);
    }

    console.log(`Agent ${agent.id} status: ${status.state || status.status}`);

    // Check for associated PRs if agent finished
    if (agent.prNumber) {
      const pr = await github.getPRStatus(repo, agent.prNumber);
      if (pr && pr.state === 'OPEN' && pr.mergeable === 'MERGEABLE' && pr.reviewDecision === 'APPROVED') {
        await github.mergePR(repo, agent.prNumber);
      } else {
        console.log(`PR ${repo}#${agent.prNumber} is not ready for merge. State: ${pr?.state}, Mergeable: ${pr?.mergeable}, Review: ${pr?.reviewDecision}`);
      }
    }
  }
}

// CLI Entry Point
if (import.meta.url === `file://${process.argv[1]}`) {
  const args = process.argv.slice(2);
  if (args.length === 0) {
    console.log('Usage: cursor-jules-orchestrator.mjs <repo> <agent-type:agent-id:pr-number>...');
    process.exit(1);
  }

  const repo = args[0];
  const agents = args.slice(1).map(arg => {
    const [type, id, prNumber] = arg.split(':');
    return { type, id, prNumber: prNumber ? parseInt(prNumber) : null };
  });

  orchestrate({ repo, agents }).catch(err => {
    console.error('Orchestration failed:', err);
    process.exit(1);
  });
}

export { github, cursor, jules, orchestrate };
