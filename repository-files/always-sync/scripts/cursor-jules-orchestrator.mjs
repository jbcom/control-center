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
 * - CURSOR_GITHUB_TOKEN: GitHub token for API access
 */

const JULES_API_KEY = process.env.JULES_API_KEY;
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
    const hasSecrets = files.some(f => f.patch && /password|secret|key|token/i.test(f.patch));
    if (hasSecrets) {
      console.log(`  ⚠️ Skipping merge - PR contains potentially sensitive data`);
      return { merged: false, message: 'Safety check failed: potential secrets detected' };
    }
  }

  return ghApi(`/repos/${owner}/${repo}/pulls/${prNumber}/merge`, {
    method: 'PUT',
    body: JSON.stringify({ merge_method: 'squash' })
  });
}

async function orchestrate() {
  console.log('🤖 Cursor-Jules Orchestrator starting...');
  console.log(`JULES_API_KEY: ${JULES_API_KEY ? '✅' : '❌'}`);
  console.log(`GITHUB_TOKEN: ${GITHUB_TOKEN ? '✅' : '❌'}`);
  
  let sessionsData;
  try {
    sessionsData = await listSessions();
  } catch (err) {
    console.error('Failed to list sessions:', err.message);
    return;
  }

  console.log(`\nFound ${sessionsData.sessions?.length || 0} sessions\n`);
  
  for (const session of sessionsData.sessions || []) {
    try {
      const sessionId = session.name.split('/')[1];
      
      // Validate sessionId format to prevent path traversal
      if (!sessionId || !/^[a-zA-Z0-9_-]+$/.test(sessionId)) {
        console.log(`  ⚠️ Skipping invalid session ID: ${sessionId}`);
        continue;
      }

      const details = await getSession(sessionId);
      console.log(`Session ${sessionId}: ${details.state || 'UNKNOWN'}`);
      
      if (details.state === 'COMPLETED' && details.pullRequest) {
        console.log(`  PR: ${details.pullRequest}`);
        const match = details.pullRequest.match(/github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)/);
        if (match) {
          const [, owner, repo, prNum] = match;
          
          // Validate extracted parameters to prevent injection
          if (!/^[a-zA-Z0-9._-]+$/.test(owner) || !/^[a-zA-Z0-9._-]+$/.test(repo) || !/^\d+$/.test(prNum)) {
            console.log(`  ⚠️ Skipping PR with invalid parameters: ${owner}/${repo}#${prNum}`);
            continue;
          }

          const status = await checkPRStatus(owner, repo, prNum);
          
          if (!status) {
            console.log(`  ⚠️ PR not found or error fetching status`);
            continue;
          }

          console.log(`  CI: ${status.allPassing ? '✅' : '❌'} | Mergeable: ${status.mergeable ? '✅' : '❌'} | Review: ${status.hasChangesRequested ? '❌ Changes Requested' : (status.isApproved ? '✅ Approved' : '⏳ Pending Approval')}`);
          
          if (status.allPassing && status.mergeable && status.isApproved && !status.hasChangesRequested) {
            console.log(`  🔀 Merging...`);
            const result = await mergePR(owner, repo, prNum);
            console.log(`  Result: ${result.merged ? '✅ Merged' : result.message || 'Failed'}`);
          } else {
            if (!status.allPassing) console.log(`  Waiting for CI to pass...`);
            if (!status.mergeable) console.log(`  Waiting for mergeable state (clean)...`);
            if (status.hasChangesRequested) console.log(`  Changes were requested. Please address them.`);
            if (!status.isApproved && !status.hasChangesRequested) console.log(`  Waiting for approval...`);
          }
        }
      }
    } catch (err) {
      console.error(`  Error processing session:`, err.message);
    }
  }
  
  console.log('\n✅ Orchestration complete');
}

orchestrate().catch(err => {
  console.error('Fatal Error:', err);
  process.exit(1);
});
