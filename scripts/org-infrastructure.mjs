#!/usr/bin/env node

/**
 * Organization Infrastructure Setup
 * 
 * Idempotently creates essential repos for each managed organization:
 * - .github - Org-wide settings and defaults
 * - <org>.github.io - Documentation site
 * 
 * Uses @agentic/control for AI-assisted doc site generation
 */

import { writeFile } from 'fs/promises';

const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
const GOOGLE_JULES_API_KEY = process.env.GOOGLE_JULES_API_KEY;
const DRY_RUN = process.env.DRY_RUN === 'true';

// Organization configuration
const ORGANIZATIONS = {
  'jbcom': {
    domain: 'jonbogaty.com',
    description: 'jbcom ecosystem - Professional portfolio and OSS packages',
    branding: {
      primary_color: '#2563eb',
      name: 'jbcom',
      tagline: 'Building the future of game development'
    }
  },
  'strata-game-library': {
    domain: 'strata.game',
    description: 'Strata - Procedural 3D graphics library for React Three Fiber',
    branding: {
      primary_color: '#10b981',
      name: 'Strata',
      tagline: 'Procedural worlds, infinite possibilities'
    }
  },
  'agentic-dev-library': {
    domain: 'agentic.dev',
    description: 'Agentic - AI agent orchestration and fleet management',
    branding: {
      primary_color: '#8b5cf6',
      name: 'Agentic',
      tagline: 'Autonomous AI development at scale'
    }
  },
  'extended-data-library': {
    domain: 'extendeddata.dev',
    description: 'Extended Data - Enterprise data utilities and vendor connectors',
    branding: {
      primary_color: '#f59e0b',
      name: 'Extended Data',
      tagline: 'Data infrastructure that scales'
    }
  }
};

// GitHub API
async function ghApi(endpoint, options = {}) {
  if (DRY_RUN && ['POST', 'PUT', 'PATCH'].includes(options.method)) {
    console.log(`  [DRY RUN] ${options.method} ${endpoint}`);
    return { dry_run: true };
  }
  
  const res = await fetch(`https://api.github.com${endpoint}`, {
    ...options,
    headers: {
      'Authorization': `token ${GITHUB_TOKEN}`,
      'Accept': 'application/vnd.github+json',
      ...options.headers
    }
  });
  
  if (!res.ok) {
    const error = await res.json().catch(() => ({ message: res.statusText }));
    throw new Error(`GitHub API ${res.status}: ${JSON.stringify(error)}`);
  }
  
  return res.json();
}

// Check if repo exists
async function repoExists(org, repo) {
  try {
    await ghApi(`/repos/${org}/${repo}`);
    return true;
  } catch {
    return false;
  }
}

// Create repository
async function createRepo(org, name, description, options = {}) {
  console.log(`  Creating ${org}/${name}...`);
  
  return ghApi(`/orgs/${org}/repos`, {
    method: 'POST',
    body: JSON.stringify({
      name,
      description,
      homepage: options.homepage,
      private: false,
      has_issues: true,
      has_projects: true,
      has_wiki: false,
      has_discussions: options.has_discussions ?? false,
      auto_init: true,
      ...options
    })
  });
}

// Create .github repo for org-wide settings
async function ensureGitHubRepo(org, config) {
  const repoName = '.github';
  
  if (await repoExists(org, repoName)) {
    console.log(`  ✓ ${org}/${repoName} already exists`);
    return { exists: true };
  }
  
  console.log(`  Creating ${org}/${repoName}...`);
  await createRepo(org, repoName, `Organization-wide GitHub settings for ${config.branding.name}`, {
    homepage: `https://github.com/${org}`
  });
  
  // TODO: Initialize with profile README, FUNDING.yml, etc.
  return { created: true };
}

// Create <org>.github.io documentation repo
async function ensureDocsRepo(org, config) {
  const repoName = `${org}.github.io`;
  
  if (await repoExists(org, repoName)) {
    console.log(`  ✓ ${org}/${repoName} already exists`);
    return { exists: true };
  }
  
  console.log(`  Creating ${org}/${repoName}...`);
  await createRepo(org, repoName, `${config.branding.name} documentation and showcase`, {
    homepage: `https://${config.domain}`,
    has_discussions: true
  });
  
  return { created: true, needs_docs: true };
}

// Create Jules session for docs site
async function spawnJulesForDocs(org, config) {
  if (!GOOGLE_JULES_API_KEY) {
    console.log(`  ⚠️ GOOGLE_JULES_API_KEY not set - skipping Jules for ${org}`);
    return;
  }
  
  if (DRY_RUN) {
    console.log(`  [DRY RUN] Would spawn Jules for ${org}.github.io docs`);
    return;
  }
  
  const prompt = `Create a modern documentation site for ${config.branding.name}.

REQUIREMENTS:
- Use Astro with Starlight theme for documentation
- Brand colors: ${config.branding.primary_color}
- Tagline: "${config.branding.tagline}"
- Domain: ${config.domain}
- Include: Getting started, API reference, Examples, Contributing guide

BRANDING (derived from jbcom):
- Professional, modern design
- Dark mode support
- Consistent with jonbogaty.com styling but unique identity
- Use the organization's primary color as accent

STRUCTURE:
- src/content/docs/ for markdown content
- public/ for static assets
- astro.config.mjs with Starlight config
- GitHub Pages deployment workflow

Create a complete, production-ready documentation site.`;

  try {
    const res = await fetch('https://jules.googleapis.com/v1alpha/sessions', {
      method: 'POST',
      headers: {
        'X-Goog-Api-Key': GOOGLE_JULES_API_KEY,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        prompt,
        sourceContext: {
          source: `sources/github/${org}/${org}.github.io`,
          githubRepoContext: { startingBranch: 'main' }
        },
        automationMode: 'AUTO_CREATE_PR'
      })
    });
    
    if (res.ok) {
      const data = await res.json();
      console.log(`  ✓ Jules session created for ${org} docs: ${data.name}`);
      return data;
    } else if (res.status === 404) {
      console.error(`
  ❌ Jules error 404: Not Found
     This usually means the 'Google Jules' GitHub App is not installed on the '${org}' organization.
     Please install it here and re-run the script:
     ➡️ https://github.com/apps/google-jules
`);
    } else {
      const errorBody = await res.text();
      console.error(`  Jules error: ${res.status}\n  ${errorBody}`);
    }
  } catch (e) {
    console.error(`  Jules error: ${e.message}`);
  }
}

// Check for Jules app installation
async function checkJulesInstallations() {
  console.log('Jules Installation Status:');

  for (const org of Object.keys(ORGANIZATIONS)) {
    try {
      const { installations = [] } = await ghApi(`/orgs/${org}/installations`);
      const julesInstalled = installations.some(inst => inst.app_slug === 'google-jules');

      if (julesInstalled) {
        console.log(`  ✅ ${org}`);
      } else {
        console.log(`  ❌ ${org} - Missing`);
      }
    } catch (e) {
      console.log(`  ⚠️ ${org} - Error checking status: ${e.message}`);
    }
  }

  console.log(`\nInstall Jules at: https://github.com/apps/google-jules\n`);
}

async function main() {
  console.log('╔══════════════════════════════════════════════════════════════════╗');
  console.log('║              ORGANIZATION INFRASTRUCTURE SETUP                    ║');
  console.log('╚══════════════════════════════════════════════════════════════════╝\n');
  
  console.log(`Mode: ${DRY_RUN ? 'DRY RUN' : 'LIVE'}\n`);

  if (!GITHUB_TOKEN) {
    console.error('❌ GITHUB_TOKEN required');
    process.exit(1);
  }

  await checkJulesInstallations();
  
  const results = {
    orgs_processed: 0,
    github_repos_created: 0,
    docs_repos_created: 0,
    jules_sessions: 0,
    errors: []
  };
  
  for (const [org, config] of Object.entries(ORGANIZATIONS)) {
    console.log(`\n📦 Organization: ${org}`);
    console.log(`   Domain: ${config.domain}`);
    
    try {
      // Ensure .github repo
      const githubResult = await ensureGitHubRepo(org, config);
      if (githubResult.created) results.github_repos_created++;
      
      // Ensure docs repo
      const docsResult = await ensureDocsRepo(org, config);
      if (docsResult.created) {
        results.docs_repos_created++;
        
        // Spawn Jules to build docs site
        if (docsResult.needs_docs) {
          await spawnJulesForDocs(org, config);
          results.jules_sessions++;
        }
      }
      
      results.orgs_processed++;
    } catch (e) {
      console.error(`   Error: ${e.message}`);
      results.errors.push(`${org}: ${e.message}`);
    }
  }
  
  await writeFile('org-infrastructure-report.json', JSON.stringify(results, null, 2));
  
  console.log('\n' + JSON.stringify(results, null, 2));
  console.log('\n✅ Infrastructure setup complete');
}

main().catch(e => {
  console.error('Fatal:', e);
  process.exit(1);
});
