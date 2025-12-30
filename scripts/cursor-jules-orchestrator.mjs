#!/usr/bin/env node
/**
 * Cursor-Jules Orchestrator
 * 
 * This script is designed to be run by Cursor Cloud Agents to:
 * 1. Monitor Jules sessions for completion
 * 2. Review PRs created by Jules
 * 3. Handle AI feedback integration
 * 4. Merge PRs when ready
 * 
 * Environment variables required:
 * - JULES_API_KEY: Google Jules API key
 * - CURSOR_API_KEY: Cursor Cloud Agent API key
 * - CURSOR_GITHUB_TOKEN: GitHub token for API access
 */

const JULES_API_KEY = process.env.JULES_API_KEY;
const CURSOR_API_KEY = process.env.CURSOR_API_KEY;
const GITHUB_TOKEN = process.env.CURSOR_GITHUB_TOKEN || process.env.GITHUB_TOKEN;

if (!JULES_API_KEY) {
  console.error('JULES_API_KEY not set');
  process.exit(1);
}

if (!GITHUB_TOKEN) {
  console.error('CURSOR_GITHUB_TOKEN not set');
  process.exit(1);
}

const JULES_BASE = 'https://jules.googleapis.com/v1alpha';
const CURSOR_BASE = 'https://api.cursor.com/v0';

async function cursorApi(endpoint, options = {}) {
  if (!CURSOR_API_KEY) {
    throw new Error('CURSOR_API_KEY not set');
  }
  const res = await fetch(`${CURSOR_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Authorization': `Bearer ${CURSOR_API_KEY}`,
      'Content-Type': 'application/json',
      ...options.headers
    }
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ message: res.statusText }));
    throw new Error(`Cursor API Error (${res.status}) on ${endpoint}: ${JSON.stringify(error)}`);
  }
  return res.json();
}

async function spawnCursorAgent(repo, task, branch = 'main') {
  console.log(`🚀 Spawning Cursor agent for ${repo}...`);
  return cursorApi('/agents', {
    method: 'POST',
    body: JSON.stringify({
      prompt: { text: task },
      source: { repository: repo, ref: branch },
      target: { autoCreatePr: true }
    })
  });
}

async function getSession(sessionId) {
  const res = await fetch(`${JULES_BASE}/sessions/${sessionId}`, {
    headers: { 'X-Goog-Api-Key': JULES_API_KEY }
  });
  if (!res.ok) throw new Error(`Failed to get session ${sessionId}: ${res.statusText}`);
  return res.json();
}

async function listSessions() {
  const res = await fetch(`${JULES_BASE}/sessions`, {
    headers: { 'X-Goog-Api-Key': JULES_API_KEY }
  });
  if (!res.ok) throw new Error(`Failed to list sessions: ${res.statusText}`);
  return res.json();
}

async function ghApi(endpoint, options = {}) {
  const res = await fetch(`https://api.github.com${endpoint}`, {
    ...options,
    headers: {
      'Authorization': `Bearer ${GITHUB_TOKEN}`,
      'Accept': 'application/vnd.github+json',
      ...options.headers
    }
  });
  if (!res.ok && res.status !== 404) {
    const error = await res.json().catch(() => ({ message: res.statusText }));
    console.error(`GitHub API Error (${res.status}) on ${endpoint}:`, error);
  }
  return res.json();
}

async function checkPRStatus(owner, repo, prNumber) {
  const pr = await ghApi(`/repos/${owner}/${repo}/pulls/${prNumber}`);
  if (pr.message === 'Not Found') return null;

  const checks = await ghApi(`/repos/${owner}/${repo}/commits/${pr.head.sha}/check-runs`);
  const reviews = await ghApi(`/repos/${owner}/${repo}/pulls/${prNumber}/reviews`);
  
  const checkRuns = checks.check_runs || [];
  const allPassing = checkRuns.length > 0 && checkRuns.every(c => 
    c.status === 'completed' && (c.conclusion === 'success' || c.conclusion === 'neutral' || c.conclusion === 'skipped')
  );

  const hasChangesRequested = reviews.some(r => r.state === 'CHANGES_REQUESTED');
  const isApproved = reviews.some(r => r.state === 'APPROVED');

  return {
    pr,
    checks: checkRuns,
    allPassing,
    mergeable: pr.mergeable && (pr.mergeable_state === 'clean' || pr.mergeable_state === 'unstable'),
    hasChangesRequested,
    isApproved
  };
}

async function mergePR(owner, repo, prNumber) {
  // Safety check: ensure PR doesn't contain obvious secrets or risky files
  const files = await ghApi(`/repos/${owner}/${repo}/pulls/${prNumber}/files`);
  if (Array.isArray(files)) {
    // Improved regex to detect patterns like `API_KEY=...` or `password: "..."`
    const SENSITIVE_KEYWORD_REGEX = /("?api_?key"?|"?(client_)?secret"?|"?(access|refresh)_?token"?|password)[\s='":]+[a-zA-Z0-9_.-]{16,}/i;
    const hasSecrets = files.some(f => f.patch && SENSITIVE_KEYWORD_REGEX.test(f.patch));
    if (hasSecrets) {
      console.log(`  ⚠️ Skipping merge - PR contains potentially sensitive data.`);
      return { merged: false, message: 'Safety check failed: potential secrets detected' };
    }
  }

  console.log(`  Attempting to merge PR #${prNumber} in ${owner}/${repo}`);
  const result = await ghApi(`/repos/${owner}/${repo}/pulls/${prNumber}/merge`, {
    method: 'PUT',
    body: JSON.stringify({ merge_method: 'squash' })
  });
  console.log(`  Merge result for PR #${prNumber}: ${result.merged ? '✅ Success' : `❌ Failed: ${result.message}`}`);
  return result;
}

async function orchestrate() {
  console.log('🤖 Cursor-Jules Orchestrator starting...');
  console.log(`JULES_API_KEY: ${JULES_API_KEY ? '✅' : '❌'}`);
  console.log(`CURSOR_API_KEY: ${CURSOR_API_KEY ? '✅' : '❌'}`);
  console.log(`GITHUB_TOKEN: ${GITHUB_TOKEN ? '✅' : '❌'}`);
  
  let sessionsData;
  let activeAgents = [];
  try {
    sessionsData = await listSessions();
    if (CURSOR_API_KEY) {
      const agentsData = await cursorApi('/agents');
      activeAgents = agentsData.agents || [];
      console.log(`Found ${activeAgents.length} active Cursor agents`);
    }
  } catch (err) {
    console.error('Failed to list sessions or agents:', err.message);
    return;
  }

  console.log(`\nFound ${sessionsData.sessions?.length || 0} sessions\n`);
  
  for (const session of sessionsData.sessions || []) {
    const sessionName = session.name || 'unknown-session';
    try {
      const sessionId = sessionName.split('/').pop();
      
      // Stricter validation for sessionId
      if (!sessionId || !/^[a-zA-Z0-9_-]{10,}$/.test(sessionId)) {
        console.warn(`  [${sessionName}] ⚠️ Skipping invalid or malformed session ID.`);
        continue;
      }

      console.log(`[${sessionId}] Processing session...`);
      const details = await getSession(sessionId);
      console.log(`[${sessionId}] State: ${details.state || 'UNKNOWN'}`);
      
      if (details.state === 'COMPLETED' && details.pullRequest) {
        console.log(`[${sessionId}] Found PR: ${details.pullRequest}`);
        const match = details.pullRequest.match(/github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)/);

        if (match) {
          const [, owner, repo, prNum] = match;
          const prIdentifier = `${owner}/${repo}#${prNum}`;
          
          // Stricter validation for GitHub identifiers
          const validOwnerRepo = /^[a-zA-Z0-9._-]{1,100}$/;
          const validPrNum = /^\d{1,7}$/;
          if (!validOwnerRepo.test(owner) || !validOwnerRepo.test(repo) || !validPrNum.test(prNum)) {
            console.error(`[${sessionId}] ❌ Invalid PR parameters extracted: ${prIdentifier}`);
            continue;
          }

          console.log(`[${sessionId}] Checking status for ${prIdentifier}...`);
          const status = await checkPRStatus(owner, repo, prNum);
          
          if (!status) {
            console.warn(`[${sessionId}] ⚠️ PR ${prIdentifier} not found or error fetching status.`);
            continue;
          }

          console.log(`[${sessionId}] Status for ${prIdentifier}: CI: ${status.allPassing ? '✅' : '❌'}, Mergeable: ${status.mergeable ? '✅' : '❌'}, Review: ${status.hasChangesRequested ? '❌' : (status.isApproved ? '✅' : '⏳')}`);
          
          if (status.allPassing && status.mergeable && status.isApproved && !status.hasChangesRequested) {
            console.log(`[${sessionId}] 🔀 Conditions met. Merging ${prIdentifier}...`);
            await mergePR(owner, repo, prNum);
          } else {
            console.log(`[${sessionId}] ℹ️ Merge conditions not met for ${prIdentifier}.`);
            if (!status.allPassing && status.checks.some(c => c.conclusion === 'failure')) {
              const alreadyRunning = activeAgents.some(a =>
                a.source?.repository === `${owner}/${repo}` &&
                a.prompt?.text?.includes(`#${prNum}`)
              );

              if (alreadyRunning) {
                console.log(`[${sessionId}] ℹ️ Cursor agent already running for ${prIdentifier}.`);
              } else {
                console.log(`[${sessionId}] 🚀 Spawning Cursor agent to fix CI for ${prIdentifier}.`);
                try {
                  await spawnCursorAgent(`${owner}/${repo}`, `Fix CI failures in PR #${prNum}: ${status.pr.title}`, status.pr.head.ref);
                } catch (err) {
                  console.error(`[${sessionId}] ❌ Failed to spawn Cursor agent for ${prIdentifier}:`, err.message);
                }
              }
            }
          }
        } else {
          console.warn(`[${sessionId}] ⚠️ Could not parse PR URL: ${details.pullRequest}`);
        }
      } else if (details.state !== 'COMPLETED') {
          console.log(`[${sessionId}] ⏳ Session not yet completed.`);
      }
    } catch (err) {
      console.error(`[${sessionName}] ❌ Error processing session:`, err.message);
    }
  }
  
  console.log('\n✅ Orchestration complete');
}

orchestrate().catch(err => {
  console.error('Fatal Error:', err);
  process.exit(1);
});
