/**
 * Cursor Background Composer API Client
 * Based on: https://github.com/mjdierkes/cursor-background-agent-api
 */

import { randomUUID } from 'crypto';

const CURSOR_BASE_URL = 'https://cursor.com';
const CURSOR_SESSION_TOKEN = process.env.CURSOR_SESSION_TOKEN;

// Build headers with session token
function getHeaders() {
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

// Build the complex payload for background composer
function buildPayload(options) {
  const bcId = `bc-${randomUUID()}`;
  const cleanUrl = options.repositoryUrl
    .replace(/^https?:\/\//, '')
    .replace(/\.git$/, '');
  const devcontainerUrl = options.repositoryUrl.replace(/\.git$/, '');

  return {
    snapshotNameOrId: cleanUrl,
    devcontainerStartingPoint: {
      url: devcontainerUrl,
      ref: options.branch || 'main'
    },
    modelDetails: {
      modelName: options.model || 'claude-4-sonnet-thinking',
      maxMode: true
    },
    repositoryInfo: {},
    snapshotWorkspaceRootPath: '/workspace',
    autoBranch: true,
    returnImmediately: true,
    repoUrl: cleanUrl,
    conversationHistory: [
      {
        text: options.taskDescription,
        type: 'MESSAGE_TYPE_HUMAN',
        richText: JSON.stringify({
          root: {
            children: [
              {
                children: [
                  {
                    detail: 0,
                    format: 0,
                    mode: 'normal',
                    style: '',
                    text: options.taskDescription,
                    type: 'text',
                    version: 1
                  }
                ],
                direction: 'ltr',
                format: '',
                indent: 0,
                type: 'paragraph',
                version: 1,
                textFormat: 0,
                textStyle: ''
              }
            ],
            direction: 'ltr',
            format: '',
            indent: 0,
            type: 'root',
            version: 1
          }
        })
      }
    ],
    source: 'BACKGROUND_COMPOSER_SOURCE_WEBSITE',
    bcId: bcId,
    addInitialMessageToResponses: true
  };
}

/**
 * Create a background composer task
 */
export async function createBackgroundComposer(options) {
  const payload = buildPayload(options);
  
  const response = await fetch(`${CURSOR_BASE_URL}/api/auth/startBackgroundComposerFromSnapshot`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(payload)
  });
  
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Cursor API ${response.status}: ${text}`);
  }
  
  const data = await response.json();
  return {
    bcId: payload.bcId,
    ...data
  };
}

/**
 * List background composers
 */
export async function listComposers(n = 100) {
  const response = await fetch(`${CURSOR_BASE_URL}/api/background-composer/list`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ n, include_status: true })
  });
  
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Cursor API ${response.status}: ${text}`);
  }
  
  return response.json();
}

/**
 * Get detailed composer info
 */
export async function getDetailedComposer(bcId) {
  const response = await fetch(`${CURSOR_BASE_URL}/api/background-composer/get-detailed-composer`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ bcId, n: 1, includeDiff: true, includeTeamWide: true })
  });
  
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Cursor API ${response.status}: ${text}`);
  }
  
  return response.json();
}

/**
 * Pause a composer
 */
export async function pauseComposer(bcId) {
  const response = await fetch(`${CURSOR_BASE_URL}/api/background-composer/pause`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ bcId })
  });
  
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Cursor API ${response.status}: ${text}`);
  }
  
  return response.json();
}

/**
 * Open PR from composer
 */
export async function openPr(bcId, prData = {}) {
  const response = await fetch(`${CURSOR_BASE_URL}/api/background-composer/open-pr`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ bcId, ...prData })
  });
  
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Cursor API ${response.status}: ${text}`);
  }
  
  return response.json();
}

export default {
  createBackgroundComposer,
  listComposers,
  getDetailedComposer,
  pauseComposer,
  openPr
};
