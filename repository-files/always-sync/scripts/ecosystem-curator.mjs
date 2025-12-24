#!/usr/bin/env node

/**
 * Ecosystem Curator
 * 
 * Nightly autonomous orchestration workflow that triages issues and processes PRs
 * across all repositories in the jbcom organization.
 */

import { writeFile } from 'fs/promises';

const GITHUB_TOKEN = process.env.JULES_GITHUB_TOKEN || process.env.GITHUB_TOKEN;
const CURSOR_API_KEY = process.env.CURSOR_API_KEY;
const GOOGLE_JULES_API_KEY = process.env.GOOGLE_JULES_API_KEY;
const OLLAMA_API_URL = process.env.OLLAMA_API_URL || 'https://ollama.com/api';
const ORG = 'jbcom';
const DRY_RUN = process.env.DRY_RUN === 'true';
const TARGET_REPO = process.env.TARGET_REPO;

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

async function cursorApi(endpoint, options = {}) {
  if (DRY_RUN && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(options.method)) {
    console.log(`    [DRY RUN] cursorApi: ${options.method} ${endpoint}`);
    return { dry_run: true };
  }
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
    throw new Error(`Cursor API Error (${res.status}) on ${endpoint}: ${JSON.stringify(error)}`);
  }
  return res.json();
}

async function ollamaApi(messages) {
  if (DRY_RUN) {
    console.log(`    [DRY RUN] ollamaApi: chat request`);
    return { message: { content: "Dry run response" } };
  }
  const res = await fetch(`${OLLAMA_API_URL}/chat`, {
    method: 'POST',
    body: JSON.stringify({
      model: "glm-4.6:cloud",
      messages: messages,
      stream: false
    }),
    headers: { 'Content-Type': 'application/json' }
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ message: res.statusText }));
    throw new Error(`Ollama API Error (${res.status}): ${JSON.stringify(error)}`);
  }
  return res.json();
}

async function discoverRepos() {
  console.log(`🔍 Discovering repositories in ${ORG}...`);
  if (TARGET_REPO) {
    console.log(`   Filtering for target repository: ${TARGET_REPO}`);
    try {
      const repo = await ghApi(`/repos/${ORG}/${TARGET_REPO}`);
      return [repo];
    } catch (e) {
      console.error(`   Error finding target repo ${TARGET_REPO}: ${e.message}`);
      return [];
    }
  }
  const repos = await ghApi(`/orgs/${ORG}/repos`, { allPages: true });
  return repos.filter(r => !r.archived && !r.disabled);
}

async function triageIssue(repo, issue) {
  console.log(`  - Triaging issue #${issue.number}: ${issue.title}`);
  
  // Logic to determine if complex or quick fix
  // For now, let's use labels or keywords.
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
          prompt: `Fix issue #${issue.number}: ${issue.title}

${issue.body}`,
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
    console.log(`    -> Spawning Cursor agent`);
    try {
      await cursorApi('/v0/agents', {
        method: 'POST',
        body: JSON.stringify({
          prompt: { text: `Fix issue #${issue.number}: ${issue.title}\n\n${issue.body}` },
          source: { repository: `${repo.owner.login}/${repo.name}`, ref: repo.default_branch },
          target: { autoCreatePr: true, branchName: `fix/issue-${issue.number}` }
        })
      });
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

  if (hasFailedCI) {
    console.log(`    -> CI Failed. Spawning agent to fix.`);
    await cursorApi('/v0/agents', {
      method: 'POST',
      body: JSON.stringify({
        prompt: { text: `Fix CI failures in PR #${pr.number}: ${pr.title}` },
        source: { repository: `${repo.owner.login}/${repo.name}`, ref: pr.head.ref },
        target: { autoCreatePr: false } // Push to existing branch
      })
    });
    stats.cursor_agents_spawned++;
  } else if (hasChangesRequested) {
    console.log(`    -> Changes requested. Spawning agent to address.`);
    const lastReview = reviews.filter(r => r.state === 'CHANGES_REQUESTED').pop();
    await cursorApi('/v0/agents', {
      method: 'POST',
      body: JSON.stringify({
        prompt: { text: `Address review comments in PR #${pr.number}:\n\n${lastReview.body}` },
        source: { repository: `${repo.owner.login}/${repo.name}`, ref: pr.head.ref },
        target: { autoCreatePr: false }
      })
    });
    stats.cursor_agents_spawned++;
  } else if (allPassing && isApproved && pr.mergeable_state === 'clean') {
    console.log(`    -> Ready to merge. Auto-merging.`);
    await ghApi(`/repos/${repo.owner.login}/${repo.name}/pulls/${pr.number}/merge`, {
      method: 'PUT',
      body: JSON.stringify({ merge_method: 'squash' })
    });
    stats.merged_prs++;
  } else if (pr.user.login.includes('bot') || pr.user.login.includes('agent')) {
    // If it's an agent's PR and it's stuck, maybe ask Ollama for advice
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
  
  // Check Cursor Agents
  try {
    const agents = await cursorApi('/v0/agents');
    console.log(`  Found ${agents.length || 0} active Cursor agents`);
  } catch (e) {
    console.error(`  Failed to list Cursor agents: ${e.message}`);
  }

  // Check Jules Sessions
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

async function main() {
  // API Key Validation
  const missingVars = [];
  if (!GITHUB_TOKEN) missingVars.push('JULES_GITHUB_TOKEN or GITHUB_TOKEN');
  if (!CURSOR_API_KEY) missingVars.push('CURSOR_API_KEY');
  if (!GOOGLE_JULES_API_KEY) missingVars.push('GOOGLE_JULES_API_KEY');
  
  if (missingVars.length > 0) {
    console.error(`❌ Critical Error: Missing required environment variables: ${missingVars.join(', ')}`);
    process.exit(1);
  }

  try {
    const repos = await discoverRepos();
    stats.repos_scanned = repos.length;

    for (const repo of repos) {
      console.log(`\n📦 Repository: ${repo.full_name}`);
      
      try {
        const issues = await ghApi(`/repos/${repo.owner.login}/${repo.name}/issues?state=open`, { allPages: true });
        for (const issue of issues) {
          // Skip if issue has an assignee or is already being processed by an agent
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
    console.log('\n✅ Ecosystem Curator finished successfully');
    console.log(JSON.stringify(stats, null, 2));

  } catch (e) {
    console.error('Fatal Error:', e);
    stats.errors.push(e.message);
    await writeFile('curator-report.json', JSON.stringify(stats, null, 2));
    process.exit(1);
  }
}

main();
