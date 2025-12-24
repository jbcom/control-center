#!/usr/bin/env node

/**
 * Ecosystem Curator
 * 
 * Nightly autonomous orchestration workflow that triages issues and processes PRs
 * across all repositories in the jbcom organization.
 * 
 * Uses:
 * - Cursor Background Composer API (https://cursor.com)
 * - Google Jules API (https://jules.googleapis.com)
 * - Ollama Cloud API
 */

import { writeFile } from 'fs/promises';
import { randomUUID } from 'crypto';

const GITHUB_TOKEN = process.env.JULES_GITHUB_TOKEN || process.env.GITHUB_TOKEN;
const CURSOR_SESSION_TOKEN = process.env.CURSOR_SESSION_TOKEN;
const GOOGLE_JULES_API_KEY = process.env.GOOGLE_JULES_API_KEY;
const OLLAMA_HOST = process.env.OLLAMA_HOST || 'https://ollama.com';
const OLLAMA_API_KEY = process.env.OLLAMA_API_KEY;

// Managed organizations - control-center manages both
const ORGANIZATIONS = ['jbcom', 'strata-game-library'];
const DRY_RUN = process.env.DRY_RUN === 'true';
const TARGET_REPO = process.env.TARGET_REPO;
const TARGET_ORG = process.env.TARGET_ORG;

// Stats for the report
const stats = {
  repos_scanned: 0,
  issues_triaged: 0,
  prs_processed: 0,
  jules_sessions_created: 0,
  cursor_agents_spawned: 0,
  ollama_resolutions: 0,
  merged_prs: 0,
  dry_run: DRY_RUN,
  errors: []
};

// ============================================
// GitHub API
// ============================================
async function ghApi(endpoint, options = {}) {
  if (DRY_RUN && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(options.method)) {
    console.log(`    [DRY RUN] ghApi: ${options.method} ${endpoint}`);
    return { dry_run: true };
  }

  const fetchPage = async (url) => {
    const res = await fetch(url, {
      ...options,
      headers: {
        'Authorization': `token ${GITHUB_TOKEN}`,
        'Accept': 'application/vnd.github+json',
        'User-Agent': 'jbcom-ecosystem-curator',
        ...options.headers
      }
    });
    if (!res.ok) {
      const error = await res.json().catch(() => ({ message: res.statusText }));
      throw new Error(`GitHub API Error (${res.status}) on ${url}: ${JSON.stringify(error)}`);
    }
    const link = res.headers.get('link');
    const data = await res.json();
    return { data, link };
  };

  let url = `https://api.github.com${endpoint}`;
  if (options.allPages) {
    let allData = [];
    let currentUrl = url;
    if (!currentUrl.includes('per_page=')) {
      currentUrl += (currentUrl.includes('?') ? '&' : '?') + 'per_page=100';
    }
    while (currentUrl) {
      const { data, link } = await fetchPage(currentUrl);
      allData = allData.concat(data);
      const nextMatch = link?.match(/<([^>]+)>; rel="next"/);
      currentUrl = nextMatch ? nextMatch[1] : null;
    }
    return allData;
  }

  const { data } = await fetchPage(url);
  return data;
}

// ============================================
// Jules API
// ============================================
async function julesApi(endpoint, options = {}) {
  if (DRY_RUN && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(options.method)) {
    console.log(`    [DRY RUN] julesApi: ${options.method} ${endpoint}`);
    return { dry_run: true };
  }
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
    throw new Error(`Jules API Error (${res.status}) on ${endpoint}: ${JSON.stringify(error)}`);
  }
  return res.json();
}

// ============================================
// Cursor Background Composer API
// Based on: https://github.com/mjdierkes/cursor-background-agent-api
// ============================================
function getCursorHeaders() {
  if (!CURSOR_SESSION_TOKEN) {
    throw new Error('CURSOR_SESSION_TOKEN not set');
  }
  return {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, br',
    'Content-Type': 'application/json',
    'Cookie': `WorkosCursorSessionToken=${CURSOR_SESSION_TOKEN}`,
    'Origin': 'https://cursor.com',
    'Referer': 'https://cursor.com/agents',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
  };
}

function buildCursorPayload(repositoryUrl, taskDescription, branch = 'main') {
  const bcId = `bc-${randomUUID()}`;
  const cleanUrl = repositoryUrl.replace(/^https?:\/\//, '').replace(/\.git$/, '');
  const devcontainerUrl = repositoryUrl.replace(/\.git$/, '');

  return {
    snapshotNameOrId: cleanUrl,
    devcontainerStartingPoint: { url: devcontainerUrl, ref: branch },
    modelDetails: { modelName: 'claude-4-sonnet-thinking', maxMode: true },
    repositoryInfo: {},
    snapshotWorkspaceRootPath: '/workspace',
    autoBranch: true,
    returnImmediately: true,
    repoUrl: cleanUrl,
    conversationHistory: [{
      text: taskDescription,
      type: 'MESSAGE_TYPE_HUMAN',
      richText: JSON.stringify({
        root: {
          children: [{
            children: [{ detail: 0, format: 0, mode: 'normal', style: '', text: taskDescription, type: 'text', version: 1 }],
            direction: 'ltr', format: '', indent: 0, type: 'paragraph', version: 1, textFormat: 0, textStyle: ''
          }],
          direction: 'ltr', format: '', indent: 0, type: 'root', version: 1
        }
      })
    }],
    source: 'BACKGROUND_COMPOSER_SOURCE_WEBSITE',
    bcId: bcId,
    addInitialMessageToResponses: true
  };
}

async function cursorCreateComposer(repositoryUrl, taskDescription, branch = 'main') {
  if (DRY_RUN) {
    console.log(`    [DRY RUN] cursorCreateComposer: ${taskDescription.substring(0, 50)}...`);
    return { dry_run: true, bcId: 'dry-run-id' };
  }
  
  const payload = buildCursorPayload(repositoryUrl, taskDescription, branch);
  const res = await fetch('https://cursor.com/api/auth/startBackgroundComposerFromSnapshot', {
    method: 'POST',
    headers: getCursorHeaders(),
    body: JSON.stringify(payload)
  });
  
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Cursor API ${res.status}: ${text}`);
  }
  
  const data = await res.json();
  return { bcId: payload.bcId, ...data };
}

async function cursorListComposers(n = 100) {
  const res = await fetch('https://cursor.com/api/background-composer/list', {
    method: 'POST',
    headers: getCursorHeaders(),
    body: JSON.stringify({ n, include_status: true })
  });
  
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Cursor API ${res.status}: ${text}`);
  }
  
  return res.json();
}

// ============================================
// Ollama API
// ============================================
async function ollamaApi(messages) {
  if (DRY_RUN) {
    console.log(`    [DRY RUN] ollamaApi: chat request`);
    return { message: { content: "Dry run response" } };
  }
  const res = await fetch(`${OLLAMA_HOST}/api/chat`, {
    method: 'POST',
    body: JSON.stringify({
      model: "glm-4.6:cloud",
      messages: messages,
      stream: false
    }),
    headers: {
      'Authorization': `Bearer ${OLLAMA_API_KEY}`,
      'Content-Type': 'application/json'
    }
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ message: res.statusText }));
    throw new Error(`Ollama API Error (${res.status}): ${JSON.stringify(error)}`);
  }
  return res.json();
}

// ============================================
// Core Logic
// ============================================
async function discoverRepos() {
  const orgsToScan = TARGET_ORG ? [TARGET_ORG] : ORGANIZATIONS;
  console.log(`🔍 Discovering repositories in: ${orgsToScan.join(', ')}`);
  
  if (TARGET_REPO) {
    console.log(`   Filtering for target repository: ${TARGET_REPO}`);
    // Try to find the repo in any of the orgs
    for (const org of orgsToScan) {
      try {
        const repo = await ghApi(`/repos/${org}/${TARGET_REPO}`);
        return [repo];
      } catch (e) {
        // Try next org
      }
    }
    console.error(`   Could not find ${TARGET_REPO} in any organization`);
    return [];
  }
  
  let allRepos = [];
  for (const org of orgsToScan) {
    console.log(`   Scanning ${org}...`);
    try {
      const repos = await ghApi(`/orgs/${org}/repos`, { allPages: true });
      const activeRepos = repos.filter(r => !r.archived && !r.disabled);
      console.log(`   Found ${activeRepos.length} active repos in ${org}`);
      allRepos = allRepos.concat(activeRepos);
    } catch (e) {
      console.error(`   Error scanning ${org}: ${e.message}`);
      stats.errors.push(`Org scan error for ${org}: ${e.message}`);
    }
  }
  
  return allRepos;
}

async function triageIssue(repo, issue) {
  console.log(`  - Triaging issue #${issue.number}: ${issue.title}`);
  
  const labels = issue.labels.map(l => l.name.toLowerCase());
  const isComplex = labels.includes('complex') || labels.includes('epic') || issue.body?.length > 1000;
  const isQuestion = labels.includes('question') || issue.title.endsWith('?');

  if (isQuestion) {
    console.log(`    -> Resolving question with Ollama`);
    const response = await ollamaApi([
      { role: "system", content: "You are an expert maintainer for the jbcom ecosystem. Answer the following issue/question concisely." },
      { role: "user", content: `Issue: ${issue.title}\n\n${issue.body}` }
    ]);
    
    await ghApi(`/repos/${repo.owner.login}/${repo.name}/issues/${issue.number}/comments`, {
      method: 'POST',
      body: JSON.stringify({ body: `🤖 **Curator Response (Ollama)**:\n\n${response.message.content}` })
    });
    stats.ollama_resolutions++;
  } else if (isComplex) {
    console.log(`    -> Creating Jules session`);
    try {
      await julesApi('/sessions', {
        method: 'POST',
        body: JSON.stringify({
          prompt: `Fix issue #${issue.number}: ${issue.title}\n\n${issue.body}`,
          sourceContext: {
            source: `sources/github/${repo.owner.login}/${repo.name}`,
            githubRepoContext: { startingBranch: repo.default_branch }
          },
          automationMode: "AUTO_CREATE_PR"
        })
      });
      stats.jules_sessions_created++;
    } catch (e) {
      console.error(`      Failed to create Jules session: ${e.message}`);
      stats.errors.push(`Jules error for ${repo.name}#${issue.number}: ${e.message}`);
    }
  } else {
    console.log(`    -> Spawning Cursor Background Composer`);
    try {
      const repoUrl = `https://github.com/${repo.owner.login}/${repo.name}`;
      const task = `Fix issue #${issue.number}: ${issue.title}\n\n${issue.body || 'No description provided.'}`;
      await cursorCreateComposer(repoUrl, task, repo.default_branch);
      stats.cursor_agents_spawned++;
    } catch (e) {
      console.error(`      Failed to spawn Cursor agent: ${e.message}`);
      stats.errors.push(`Cursor error for ${repo.name}#${issue.number}: ${e.message}`);
    }
  }
  stats.issues_triaged++;
}

async function processPR(repo, pr) {
  console.log(`  - Processing PR #${pr.number}: ${pr.title}`);

  const checks = await ghApi(`/repos/${repo.owner.login}/${repo.name}/commits/${pr.head.sha}/check-runs`);
  const reviews = await ghApi(`/repos/${repo.owner.login}/${repo.name}/pulls/${pr.number}/reviews`);
  
  const allPassing = checks.check_runs?.length > 0 && checks.check_runs.every(c => 
    c.status === 'completed' && (c.conclusion === 'success' || c.conclusion === 'neutral' || c.conclusion === 'skipped')
  );
  const hasFailedCI = checks.check_runs?.some(c => c.status === 'completed' && c.conclusion === 'failure');
  const hasChangesRequested = reviews.some(r => r.state === 'CHANGES_REQUESTED');
  const isApproved = reviews.some(r => r.state === 'APPROVED');

  const repoUrl = `https://github.com/${repo.owner.login}/${repo.name}`;

  if (hasFailedCI) {
    console.log(`    -> CI Failed. Spawning Cursor to fix.`);
    try {
      await cursorCreateComposer(repoUrl, `Fix CI failures in PR #${pr.number}: ${pr.title}`, pr.head.ref);
      stats.cursor_agents_spawned++;
    } catch (e) {
      console.error(`      Failed to spawn Cursor: ${e.message}`);
      stats.errors.push(`Cursor CI fix error for ${repo.name}#${pr.number}: ${e.message}`);
    }
  } else if (hasChangesRequested) {
    console.log(`    -> Changes requested. Spawning Cursor to address.`);
    const lastReview = reviews.filter(r => r.state === 'CHANGES_REQUESTED').pop();
    try {
      await cursorCreateComposer(repoUrl, `Address review comments in PR #${pr.number}:\n\n${lastReview.body}`, pr.head.ref);
      stats.cursor_agents_spawned++;
    } catch (e) {
      console.error(`      Failed to spawn Cursor: ${e.message}`);
      stats.errors.push(`Cursor review fix error for ${repo.name}#${pr.number}: ${e.message}`);
    }
  } else if (allPassing && isApproved && pr.mergeable_state === 'clean') {
    console.log(`    -> Ready to merge. Auto-merging.`);
    await ghApi(`/repos/${repo.owner.login}/${repo.name}/pulls/${pr.number}/merge`, {
      method: 'PUT',
      body: JSON.stringify({ merge_method: 'squash' })
    });
    stats.merged_prs++;
  } else if (pr.user.login.includes('bot') || pr.user.login.includes('agent')) {
    console.log(`    -> Agent PR stuck. Asking Ollama for advice.`);
    const response = await ollamaApi([
      { role: "system", content: "You are an expert maintainer. A bot/agent PR is stuck. Analyze and suggest next steps." },
      { role: "user", content: `PR: ${pr.title}\nState: ${pr.mergeable_state}\nLabels: ${pr.labels.map(l => l.name).join(', ')}` }
    ]);
    await ghApi(`/repos/${repo.owner.login}/${repo.name}/issues/${pr.number}/comments`, {
      method: 'POST',
      body: JSON.stringify({ body: `🤖 **Curator Advice (Ollama)**:\n\n${response.message.content}` })
    });
    stats.ollama_resolutions++;
  }

  stats.prs_processed++;
}

async function manageAgents() {
  console.log(`🤖 Managing existing agents and sessions...`);
  
  // Check Cursor Composers
  if (CURSOR_SESSION_TOKEN) {
    try {
      const composers = await cursorListComposers(50);
      const active = composers.filter(c => c.status === 'running' || c.status === 'pending');
      console.log(`  Found ${active.length} active Cursor composers (of ${composers.length} total)`);
    } catch (e) {
      console.error(`  Failed to list Cursor composers: ${e.message}`);
    }
  }

  // Check Jules Sessions
  if (GOOGLE_JULES_API_KEY) {
    try {
      const sessionsData = await julesApi('/sessions');
      for (const session of sessionsData.sessions || []) {
        const sessionId = session.name.split('/')[1];
        const details = await julesApi(`/sessions/${sessionId}`);
        
        if (details.state === 'PROPOSED_PLAN') {
          console.log(`  -> Auto-approving Jules plan for session ${sessionId}`);
          await julesApi(`/sessions/${sessionId}:approvePlan`, { method: 'POST' });
        }
      }
    } catch (e) {
      console.error(`  Failed to manage Jules sessions: ${e.message}`);
    }
  }
}

async function main() {
  console.log('╔══════════════════════════════════════════════════════════════════╗');
  console.log('║                    ECOSYSTEM CURATOR                              ║');
  console.log('╚══════════════════════════════════════════════════════════════════╝');
  console.log('');
  console.log(`Time: ${new Date().toISOString()}`);
  console.log(`Dry Run: ${DRY_RUN}`);
  console.log(`Target: ${TARGET_REPO || 'All repos'}`);
  console.log('');

  // API Key Validation
  const missingVars = [];
  if (!GITHUB_TOKEN) missingVars.push('GITHUB_TOKEN');
  if (!CURSOR_SESSION_TOKEN) console.warn('⚠️  CURSOR_SESSION_TOKEN not set - Cursor agents disabled');
  if (!GOOGLE_JULES_API_KEY) console.warn('⚠️  GOOGLE_JULES_API_KEY not set - Jules sessions disabled');
  if (!OLLAMA_API_KEY) console.warn('⚠️  OLLAMA_API_KEY not set - Ollama responses disabled');
  
  if (missingVars.length > 0) {
    console.error(`❌ Critical Error: Missing required environment variables: ${missingVars.join(', ')}`);
    process.exit(1);
  }

  try {
    const repos = await discoverRepos();
    stats.repos_scanned = repos.length;
    console.log(`Found ${repos.length} repositories to process`);

    for (const repo of repos) {
      console.log(`\n📦 Repository: ${repo.full_name}`);
      
      try {
        const issues = await ghApi(`/repos/${repo.owner.login}/${repo.name}/issues?state=open`, { allPages: true });
        for (const issue of issues) {
          const labels = issue.labels?.map(l => l.name.toLowerCase()) || [];
          if (issue.assignee || labels.includes('in-progress') || labels.includes('jules') || labels.includes('cursor')) {
            continue;
          }
          if (!issue.pull_request) {
            await triageIssue(repo, issue).catch(e => {
              console.error(`      Error triaging issue #${issue.number}: ${e.message}`);
              stats.errors.push(`Triage error for ${repo.name}#${issue.number}: ${e.message}`);
            });
          }
        }

        const prs = await ghApi(`/repos/${repo.owner.login}/${repo.name}/pulls?state=open`, { allPages: true });
        for (const pr of prs) {
          await processPR(repo, pr).catch(e => {
            console.error(`      Error processing PR #${pr.number}: ${e.message}`);
            stats.errors.push(`PR error for ${repo.name}#${pr.number}: ${e.message}`);
          });
        }
      } catch (e) {
        console.error(`    Error processing repository ${repo.full_name}: ${e.message}`);
        stats.errors.push(`Repo error for ${repo.full_name}: ${e.message}`);
      }
    }

    await manageAgents();

    // Write report
    await writeFile('curator-report.json', JSON.stringify(stats, null, 2));
    
    console.log('\n═══════════════════════════════════════════════════════════════════');
    console.log('                          CURATOR REPORT                            ');
    console.log('═══════════════════════════════════════════════════════════════════');
    console.log(JSON.stringify(stats, null, 2));
    console.log('\n✅ Ecosystem Curator finished successfully');

  } catch (e) {
    console.error('Fatal Error:', e);
    stats.errors.push(e.message);
    await writeFile('curator-report.json', JSON.stringify(stats, null, 2));
    process.exit(1);
  }
}

main();
