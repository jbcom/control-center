#!/usr/bin/env node
/**
 * Ecosystem Harvester
 * 
 * Runs every 15 minutes to:
 * 1. Check finished Cursor agents → process their work
 * 2. Check completed Jules sessions → process their PRs
 * 3. Find PRs ready to merge → merge them
 * 4. Request reviews on PRs needing attention
 * 
 * This complements the nightly Curator which spawns work.
 * The Harvester consumes and completes that work.
 */

import { writeFileSync } from 'fs';

const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
const CURSOR_API_KEY = process.env.CURSOR_API_KEY;
const GOOGLE_JULES_API_KEY = process.env.GOOGLE_JULES_API_KEY;
const DRY_RUN = process.env.DRY_RUN === 'true';
const ORG = 'jbcom';

const stats = {
  cursor_agents_checked: 0,
  cursor_agents_finished: 0,
  jules_sessions_checked: 0,
  jules_sessions_completed: 0,
  prs_reviewed: 0,
  prs_merged: 0,
  reviews_requested: 0,
  errors: []
};

// ============================================================================
// API Clients
// ============================================================================

async function ghApi(endpoint, options = {}) {
  const url = endpoint.startsWith('http') ? endpoint : `https://api.github.com${endpoint}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      'Authorization': `Bearer ${GITHUB_TOKEN}`,
      'Accept': 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      ...options.headers,
    },
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ message: res.statusText }));
    throw new Error(`GitHub API ${res.status}: ${JSON.stringify(error)}`);
  }
  return res.json();
}

async function cursorApi(endpoint, options = {}) {
  if (!CURSOR_API_KEY) return null;
  const auth = Buffer.from(`${CURSOR_API_KEY}:`).toString('base64');
  const res = await fetch(`https://api.cursor.com${endpoint}`, {
    ...options,
    headers: {
      'Authorization': `Basic ${auth}`,
      'Content-Type': 'application/json',
      ...options.headers
    }
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ message: res.statusText }));
    throw new Error(`Cursor API ${res.status}: ${JSON.stringify(error)}`);
  }
  return res.json();
}

async function julesApi(endpoint, options = {}) {
  if (!GOOGLE_JULES_API_KEY) return null;
  const res = await fetch(`https://jules.googleapis.com/v1alpha${endpoint}`, {
    ...options,
    headers: {
      'X-Goog-Api-Key': GOOGLE_JULES_API_KEY,
      'Content-Type': 'application/json',
      ...options.headers
    }
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ message: res.statusText }));
    throw new Error(`Jules API ${res.status}: ${JSON.stringify(error)}`);
  }
  return res.json();
}

// ============================================================================
// Cursor Agent Harvesting
// ============================================================================

async function harvestCursorAgents() {
  console.log('\n🤖 Harvesting Cursor Agents...');
  
  try {
    const { agents } = await cursorApi('/v0/agents');
    stats.cursor_agents_checked = agents.length;
    
    const finished = agents.filter(a => a.status === 'FINISHED');
    stats.cursor_agents_finished = finished.length;
    
    console.log(`  Total: ${agents.length} | Finished: ${finished.length}`);
    
    for (const agent of finished.slice(0, 20)) { // Process up to 20 per run
      const repo = agent.source?.repository?.replace('github.com/', '') || '';
      const branch = agent.target?.branchName;
      
      if (!repo || !branch) continue;
      
      console.log(`  📋 Agent ${agent.id.slice(0, 8)}: ${agent.name}`);
      console.log(`     Repo: ${repo} | Branch: ${branch}`);
      
      // Check if there's a PR for this branch
      try {
        const [owner, repoName] = repo.split('/');
        const prs = await ghApi(`/repos/${owner}/${repoName}/pulls?head=${owner}:${branch}&state=open`);
        
        if (prs.length > 0) {
          const pr = prs[0];
          console.log(`     PR #${pr.number}: ${pr.title}`);
          await processPR(owner, repoName, pr);
        } else {
          console.log(`     No PR found for branch`);
        }
      } catch (e) {
        console.log(`     Error: ${e.message}`);
      }
    }
  } catch (e) {
    console.error(`  Failed to harvest Cursor agents: ${e.message}`);
    stats.errors.push(`Cursor harvest: ${e.message}`);
  }
}

// ============================================================================
// Jules Session Harvesting
// ============================================================================

async function harvestJulesSessions() {
  console.log('\n📝 Harvesting Jules Sessions...');
  
  try {
    const { sessions } = await julesApi('/sessions');
    if (!sessions) {
      console.log('  No sessions found');
      return;
    }
    
    stats.jules_sessions_checked = sessions.length;
    
    const completed = sessions.filter(s => s.state === 'COMPLETED');
    stats.jules_sessions_completed = completed.length;
    
    console.log(`  Total: ${sessions.length} | Completed: ${completed.length}`);
    
    for (const session of completed.slice(0, 10)) { // Process up to 10 per run
      const sessionId = session.name?.split('/')[1];
      if (!sessionId) continue;
      
      try {
        const details = await julesApi(`/sessions/${sessionId}`);
        const prUrl = details.outputs?.[0]?.pullRequest?.url;
        
        console.log(`  📋 Session ${sessionId.slice(0, 8)}: ${details.title || 'Untitled'}`);
        
        if (prUrl) {
          // Extract PR info from URL
          const match = prUrl.match(/github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)/);
          if (match) {
            const [, owner, repo, prNum] = match;
            console.log(`     PR: ${owner}/${repo}#${prNum}`);
            
            try {
              const pr = await ghApi(`/repos/${owner}/${repo}/pulls/${prNum}`);
              await processPR(owner, repo, pr);
            } catch (e) {
              console.log(`     Error fetching PR: ${e.message}`);
            }
          }
        } else {
          console.log(`     No PR created yet`);
        }
      } catch (e) {
        console.log(`     Error: ${e.message}`);
      }
    }
  } catch (e) {
    console.error(`  Failed to harvest Jules sessions: ${e.message}`);
    stats.errors.push(`Jules harvest: ${e.message}`);
  }
}

// ============================================================================
// PR Processing
// ============================================================================

async function processPR(owner, repo, pr) {
  stats.prs_reviewed++;
  
  // Get PR status
  const checks = await ghApi(`/repos/${owner}/${repo}/commits/${pr.head.sha}/check-runs`).catch(() => ({ check_runs: [] }));
  const reviews = await ghApi(`/repos/${owner}/${repo}/pulls/${pr.number}/reviews`).catch(() => []);
  
  const allChecksPass = checks.check_runs?.length === 0 || 
    checks.check_runs?.every(c => c.status === 'completed' && (c.conclusion === 'success' || c.conclusion === 'skipped'));
  const hasApproval = reviews.some(r => r.state === 'APPROVED');
  const hasBlocker = reviews.some(r => r.state === 'CHANGES_REQUESTED');
  
  console.log(`     Checks: ${allChecksPass ? '✅' : '❌'} | Approved: ${hasApproval ? '✅' : '⏳'} | Blocked: ${hasBlocker ? '❌' : '✅'}`);
  
  // If ready to merge
  if (allChecksPass && !hasBlocker && pr.mergeable !== false && !pr.draft) {
    console.log(`     🚀 Ready to merge!`);
    
    if (!DRY_RUN) {
      try {
        await ghApi(`/repos/${owner}/${repo}/pulls/${pr.number}/merge`, {
          method: 'PUT',
          body: JSON.stringify({ merge_method: 'squash' })
        });
        console.log(`     ✅ Merged!`);
        stats.prs_merged++;
      } catch (e) {
        console.log(`     Merge failed: ${e.message}`);
      }
    } else {
      console.log(`     [DRY RUN] Would merge`);
    }
  }
  
  // If no reviews yet, request them
  if (reviews.length === 0 && !pr.draft) {
    console.log(`     📢 Requesting reviews...`);
    
    if (!DRY_RUN) {
      // Trigger review by commenting
      try {
        await ghApi(`/repos/${owner}/${repo}/issues/${pr.number}/comments`, {
          method: 'POST',
          body: JSON.stringify({ 
            body: '🤖 **Harvester**: This PR was created by an AI agent and is ready for review.\n\n@gemini-code-assist @amazon-q-developer Please review.' 
          })
        });
        stats.reviews_requested++;
      } catch (e) {
        // Ignore comment errors
      }
    }
  }
}

// ============================================================================
// Scan All Org PRs for Merge-Ready
// ============================================================================

async function scanOrgPRs() {
  console.log('\n🔍 Scanning org for merge-ready PRs...');
  
  try {
    // Get all repos
    const repos = await ghApi(`/orgs/${ORG}/repos?per_page=100&type=all`);
    
    for (const repo of repos.filter(r => !r.archived && !r.fork)) {
      try {
        const prs = await ghApi(`/repos/${ORG}/${repo.name}/pulls?state=open&per_page=10`);
        
        for (const pr of prs) {
          // Skip drafts
          if (pr.draft) continue;
          
          // Check if auto-merge candidate (bot PRs or labeled)
          const isBot = pr.user?.login?.includes('bot') || pr.user?.login?.includes('dependabot');
          const labels = pr.labels?.map(l => l.name) || [];
          const isAutoMerge = isBot || labels.includes('automerge') || labels.includes('dependencies');
          
          if (isAutoMerge) {
            console.log(`  📋 ${repo.name}#${pr.number}: ${pr.title.slice(0, 50)}...`);
            await processPR(ORG, repo.name, pr);
          }
        }
      } catch (e) {
        // Skip repos with errors
      }
    }
  } catch (e) {
    console.error(`  Failed to scan org PRs: ${e.message}`);
    stats.errors.push(`Org scan: ${e.message}`);
  }
}

// ============================================================================
// Main
// ============================================================================

async function harvest() {
  console.log('╔══════════════════════════════════════════════════════════════════╗');
  console.log('║              ECOSYSTEM HARVESTER - CONSUMING VALUE               ║');
  console.log('╚══════════════════════════════════════════════════════════════════╝');
  console.log(`\nTime: ${new Date().toISOString()}`);
  console.log(`Mode: ${DRY_RUN ? 'DRY RUN' : 'LIVE'}`);
  
  // Harvest from agents
  await harvestCursorAgents();
  await harvestJulesSessions();
  
  // Scan for merge-ready PRs
  await scanOrgPRs();
  
  // Report
  console.log('\n╔══════════════════════════════════════════════════════════════════╗');
  console.log('║                      HARVEST COMPLETE                            ║');
  console.log('╚══════════════════════════════════════════════════════════════════╝');
  console.log(`\n✅ Harvester finished`);
  console.log(JSON.stringify(stats, null, 2));
  
  writeFileSync('harvester-report.json', JSON.stringify(stats, null, 2));
}

harvest().catch(e => {
  console.error('Fatal error:', e);
  stats.errors.push(`Fatal: ${e.message}`);
  writeFileSync('harvester-report.json', JSON.stringify(stats, null, 2));
  process.exit(1);
});
