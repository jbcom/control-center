#!/usr/bin/env node

/**
 * Organization App Installation Manager
 *
 * Tracks and reports on GitHub App installations across all managed organizations.
 * GitHub doesn't allow programmatic app installation - this generates installation URLs.
 */

import { writeFile } from 'fs/promises';

const GITHUB_TOKEN = process.env.GITHUB_TOKEN;

// Apps that should be installed on all organizations
const REQUIRED_APPS = [
  { slug: 'google-labs-jules', name: 'Google Jules', purpose: 'AI code generation', priority: 'critical' },
  { slug: 'cursor', name: 'Cursor', purpose: 'AI code assistant', priority: 'critical' },
  { slug: 'claude', name: 'Claude', purpose: 'AI assistant', priority: 'high' },
  { slug: 'gemini-code-assist', name: 'Gemini Code Assist', purpose: 'AI code review', priority: 'high' },
  { slug: 'amazon-q-developer', name: 'Amazon Q Developer', purpose: 'AI code review', priority: 'high' },
  { slug: 'renovate', name: 'Renovate', purpose: 'Dependency updates', priority: 'high' },
  { slug: 'settings', name: 'Settings', purpose: 'Repo settings sync', priority: 'medium' },
];

// Optional apps (nice to have)
const OPTIONAL_APPS = [
  { slug: 'doppler-secretops-platform', name: 'Doppler', purpose: 'Secrets management', priority: 'low' },
  { slug: 'chatgpt-codex-connector', name: 'ChatGPT Codex', purpose: 'AI assistant', priority: 'low' },
  { slug: '21st-connector', name: '21st Connector', purpose: 'UI generation', priority: 'low' },
  { slug: 'render', name: 'Render', purpose: 'Deployment', priority: 'low' },
];

const ORGANIZATIONS = ['jbcom', 'strata-game-library', 'agentic-dev-library', 'extended-data-library'];

async function ghApi(endpoint) {
  const res = await fetch(`https://api.github.com${endpoint}`, {
    headers: {
      'Authorization': `token ${GITHUB_TOKEN}`,
      'Accept': 'application/vnd.github+json',
    }
  });
  if (!res.ok) throw new Error(`GitHub API ${res.status}`);
  return res.json();
}

async function getOrgApps(org) {
  try {
    const data = await ghApi(`/orgs/${org}/installations`);
    return data.installations.map(i => i.app_slug);
  } catch (e) {
    console.error(`  Error fetching apps for ${org}: ${e.message}`);
    return [];
  }
}

function getInstallUrl(appSlug, org) {
  return `https://github.com/apps/${appSlug}/installations/new/permissions?target_id=${org}`;
}

async function main() {
  console.log('╔══════════════════════════════════════════════════════════════════╗');
  console.log('║           ORGANIZATION APP INSTALLATION REPORT                   ║');
  console.log('╚══════════════════════════════════════════════════════════════════╝\n');

  if (!GITHUB_TOKEN) {
    console.error('❌ GITHUB_TOKEN required');
    process.exit(1);
  }

  const report = {
    timestamp: new Date().toISOString(),
    organizations: {},
    missing: [],
    installUrls: []
  };

  // Gather app installation status
  for (const org of ORGANIZATIONS) {
    console.log(`\n📦 ${org}`);
    const installedApps = await getOrgApps(org);

    report.organizations[org] = {
      installed: installedApps,
      missing_required: [],
      missing_optional: []
    };

    // Check required apps
    for (const app of REQUIRED_APPS) {
      if (installedApps.includes(app.slug)) {
        console.log(`  ✅ ${app.name}`);
      } else {
        console.log(`  ❌ ${app.name} (${app.priority})`);
        report.organizations[org].missing_required.push(app.slug);
        report.missing.push({ org, app: app.slug, priority: app.priority });
        report.installUrls.push({
          org,
          app: app.name,
          slug: app.slug,
          priority: app.priority,
          url: getInstallUrl(app.slug, org)
        });
      }
    }

    // Check optional apps
    for (const app of OPTIONAL_APPS) {
      if (!installedApps.includes(app.slug)) {
        report.organizations[org].missing_optional.push(app.slug);
      }
    }
  }

  // Summary
  console.log('\n' + '═'.repeat(70));
  console.log('INSTALLATION SUMMARY');
  console.log('═'.repeat(70));

  const criticalMissing = report.missing.filter(m => m.priority === 'critical');
  const highMissing = report.missing.filter(m => m.priority === 'high');

  console.log(`\n🔴 Critical Missing: ${criticalMissing.length}`);
  console.log(`🟠 High Priority Missing: ${highMissing.length}`);
  console.log(`📊 Total Missing: ${report.missing.length}`);

  if (report.installUrls.length > 0) {
    console.log('\n📋 INSTALLATION URLS (click to install):');
    console.log('─'.repeat(70));

    // Group by app for easier installation
    const byApp = {};
    for (const item of report.installUrls) {
      if (!byApp[item.slug]) byApp[item.slug] = [];
      byApp[item.slug].push(item.org);
    }

    for (const [slug, orgs] of Object.entries(byApp)) {
      const app = [...REQUIRED_APPS, ...OPTIONAL_APPS].find(a => a.slug === slug);
      console.log(`\n${app?.name || slug} (${app?.priority || 'unknown'}):`);
      console.log(`  https://github.com/apps/${slug}/installations/new`);
      console.log(`  Missing on: ${orgs.join(', ')}`);
    }
  }

  // Generate markdown report
  let markdown = `# GitHub App Installation Report

Generated: ${report.timestamp}

## Summary

| Metric | Count |
|--------|-------|
| Critical Missing | ${criticalMissing.length} |
| High Priority Missing | ${highMissing.length} |
| Total Missing | ${report.missing.length} |

## Organization Status

`;

  for (const [org, status] of Object.entries(report.organizations)) {
    markdown += `### ${org}\n\n`;
    markdown += `| App | Status |\n|-----|--------|\n`;

    for (const app of REQUIRED_APPS) {
      const installed = status.installed.includes(app.slug);
      markdown += `| ${app.name} | ${installed ? '✅' : '❌'} |\n`;
    }
    markdown += '\n';
  }

  markdown += `## Installation Links\n\n`;
  markdown += `Click each link to install the app:\n\n`;

  const byApp = {};
  for (const item of report.installUrls) {
    if (!byApp[item.slug]) byApp[item.slug] = { name: item.app, priority: item.priority, orgs: [] };
    byApp[item.slug].orgs.push(item.org);
  }

  for (const [slug, data] of Object.entries(byApp)) {
    markdown += `### ${data.name} (${data.priority})\n\n`;
    markdown += `Install: https://github.com/apps/${slug}/installations/new\n\n`;
    markdown += `Missing on: ${data.orgs.join(', ')}\n\n`;
  }

  await writeFile('org-apps-report.json', JSON.stringify(report, null, 2));
  await writeFile('org-apps-report.md', markdown);

  console.log('\n\n📄 Reports saved: org-apps-report.json, org-apps-report.md');

  // Exit with error if critical apps missing
  if (criticalMissing.length > 0) {
    console.log('\n⚠️  Critical apps missing - manual installation required');
    process.exit(1);
  }
}

main().catch(e => {
  console.error('Fatal:', e);
  process.exit(1);
});
