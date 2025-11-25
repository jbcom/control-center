# Vendor Connectors: Multi-Language Architecture

## Overview

`vendor-connectors` should be a **polyglot library** providing unified API client interfaces for external services. Both Python and TypeScript implementations should exist, with feature parity as a goal.

## Proposed Structure

```
vendor-connectors/
├── python/
│   ├── pyproject.toml
│   ├── src/
│   │   └── cloud_connectors/
│   │       ├── __init__.py
│   │       ├── base/           # Base classes, errors, utils
│   │       ├── aws/            # AWS services
│   │       ├── google/         # Google Cloud + APIs
│   │       ├── github/         # GitHub API
│   │       ├── slack/          # Slack API
│   │       ├── vault/          # HashiCorp Vault
│   │       ├── zoom/           # Zoom API
│   │       ├── meshy/          # 🆕 Meshy 3D asset generation
│   │       ├── anthropic/      # 🆕 Claude API
│   │       ├── openai/         # 🆕 OpenAI API
│   │       ├── freesound/      # 🆕 Freesound audio API
│   │       └── google_fonts/   # 🆕 Google Fonts API
│   └── tests/
│
├── node/
│   ├── package.json
│   ├── tsconfig.json
│   ├── src/
│   │   ├── index.ts
│   │   ├── base/               # Base classes, errors, utils
│   │   ├── aws/                # AWS services
│   │   ├── google/             # Google Cloud + APIs
│   │   ├── github/             # GitHub API
│   │   ├── slack/              # Slack API
│   │   ├── vault/              # HashiCorp Vault
│   │   ├── zoom/               # Zoom API
│   │   ├── meshy/              # 🆕 FROM ser-plonk/realm-walker-story
│   │   ├── anthropic/          # 🆕 FROM realm-walker-story
│   │   ├── openai/             # 🆕 FROM realm-walker-story
│   │   ├── freesound/          # Raise NotImplemented
│   │   └── google_fonts/       # Raise NotImplemented
│   └── tests/
│
├── README.md
├── CONNECTORS.md               # Feature matrix
└── .github/
    └── workflows/
        ├── python-ci.yml
        └── node-ci.yml
```

## Feature Matrix

| Connector | Python | TypeScript | Source |
|-----------|--------|------------|--------|
| AWS | ✅ | ❌ | vendor-connectors |
| Google Cloud | ✅ | ❌ | vendor-connectors |
| GitHub | ✅ | ❌ | vendor-connectors |
| Slack | ✅ | ❌ | vendor-connectors |
| Vault | ✅ | ❌ | vendor-connectors |
| Zoom | ✅ | ❌ | vendor-connectors |
| **Meshy** | ❌ | ✅ | ser-plonk, realm-walker-story |
| **Anthropic** | ❌ | ✅ | realm-walker-story |
| **OpenAI** | ❌ | ✅ | realm-walker-story, echoes-of-beastlight |
| **Freesound** | ✅ | ❌ | ai_game_dev |
| **Google Fonts** | ✅ | ❌ | ai_game_dev |

## Consolidation Plan

### Phase 1: Extract from Game Repos

1. **From `ser-plonk`** (TypeScript):
   ```
   asset_manager/meshy/ → node/src/meshy/
   ```

2. **From `realm-walker-story`** (TypeScript):
   ```
   src/ai/MeshyClient.ts → node/src/meshy/
   src/ai/AnthropicClient.ts → node/src/anthropic/
   src/ai/AIClient.ts → node/src/base/
   ```

3. **From `ai_game_dev`** (Python):
   ```
   src/ai_game_dev/audio/freesound_client.py → python/src/cloud_connectors/freesound/
   src/ai_game_dev/fonts/google_fonts.py → python/src/cloud_connectors/google_fonts/
   ```

### Phase 2: Cross-Implement

For each connector, implement in the "missing" language:

```typescript
// node/src/freesound/index.ts
export class FreesoundClient {
  constructor() {
    throw new Error("FreesoundClient not yet implemented in TypeScript. Use Python version.");
  }
}
```

```python
# python/src/cloud_connectors/meshy/__init__.py
class MeshyClient:
    def __init__(self):
        raise NotImplementedError(
            "MeshyClient not yet implemented in Python. Use TypeScript version."
        )
```

### Phase 3: Feature Parity

Gradually implement missing connectors in each language based on usage patterns.

## Interface Consistency

Both languages should follow the same patterns:

### Python
```python
from cloud_connectors import MeshyClient

client = MeshyClient(api_key="...")
result = await client.generate_3d_model(prompt="a cute otter")
```

### TypeScript
```typescript
import { MeshyClient } from '@jbcom/cloud-connectors';

const client = new MeshyClient({ apiKey: '...' });
const result = await client.generate3dModel({ prompt: 'a cute otter' });
```

## Publishing

| Language | Registry | Package Name |
|----------|----------|--------------|
| Python | PyPI | `cloud-connectors` |
| TypeScript | npm | `@jbcom/cloud-connectors` |

## Benefits

1. **DRY**: No more duplicated API clients across game repos
2. **Tested**: Centralized testing and maintenance
3. **Versioned**: Proper releases and changelogs
4. **Discoverable**: One place to find all integrations
5. **Consistent**: Same patterns across languages

## Migration Path for Game Repos

After consolidation, game repos update their dependencies:

```python
# Before (ai_game_dev)
from ai_game_dev.audio.freesound_client import FreesoundClient

# After
from cloud_connectors import FreesoundClient
```

```typescript
// Before (ser-plonk)
import { MeshyClient } from '../asset_manager/meshy';

// After
import { MeshyClient } from '@jbcom/cloud-connectors';
```
