# FSC Migration to jbcom-style Control Center

## Current State (Fragmented)

```
FlipsideCrypto/
├── fsc-control-center/          # Orchestration only
│   ├── .cursor/rules/
│   ├── memory-bank/
│   └── scripts/                 # Ad-hoc shell/Python
│
├── terraform-modules/           # Composite actions + TF modules
│   ├── .github/
│   │   ├── actions/            # tm-cli, pipeline-config, etc.
│   │   └── workflows/          # pipeline-generator.yml
│   ├── modules/                # Actual Terraform modules
│   └── lambda/                 # Go code for secrets
│
├── terraform-organization/      # Factory - Go generators
│   ├── cmd/                    # Go CLI tools
│   ├── generator/              # Template generation
│   └── workspaces/             # Per-repo configs
│
└── [managed repos]/            # Each has generated pipelines
    └── .github/workflows/      # Generated from factory
```

**Problems:**
- Changes require coordinating 3+ repos
- Logic duplicated between shell, Go, composite actions
- Agent must context-switch between repos constantly
- Testing is integration-only (run workflow, hope it works)
- No typing, no proper package boundaries

## Target State (Unified)

```
FlipsideCrypto/fsc-control-center/
├── packages/
│   ├── cursor-fleet/           # @fsc/cursor-fleet (or use @jbcom/cursor-fleet)
│   │   └── (agent management)
│   │
│   ├── pipeline-generator/     # @fsc/pipeline-generator
│   │   ├── src/
│   │   │   ├── config.ts       # Parse pipelines.yaml
│   │   │   ├── templates/      # Workflow templates
│   │   │   ├── generator.ts    # Core generation logic
│   │   │   └── cli.ts
│   │   └── package.json
│   │
│   ├── terraform-modules/      # Actual HCL modules (or symlink)
│   │   ├── aws-lambda/
│   │   ├── github-repository/
│   │   └── ...
│   │
│   ├── repo-bootstrap/         # @fsc/repo-bootstrap
│   │   ├── src/
│   │   │   ├── templates/      # Initial repo structure
│   │   │   ├── bootstrap.ts    # Create new managed repo
│   │   │   └── cli.ts
│   │   └── package.json
│   │
│   └── secrets-manager/        # @fsc/secrets-manager (Go or TS)
│       ├── providers/          # AWS, GCP, etc.
│       └── lambda/             # Deployment artifacts
│
├── .cursor/
│   ├── rules/                  # Agent instructions
│   └── scripts/                # Agent tooling
│
├── .github/
│   └── workflows/
│       ├── ci.yml              # Test all packages
│       └── release.yml         # Publish packages
│
├── memory-bank/                # Agent continuity
├── ECOSYSTEM.toml              # Package dependency graph
├── pnpm-workspace.yaml         # Monorepo config
└── process-compose.yml         # Local services
```

## Migration Steps

### Phase 1: Establish Structure

1. **Add pnpm workspace to fsc-control-center**
   ```yaml
   # pnpm-workspace.yaml
   packages:
     - 'packages/*'
   ```

2. **Install @jbcom/cursor-fleet**
   ```bash
   pnpm add @jbcom/cursor-fleet
   ```

3. **Create ECOSYSTEM.toml**
   ```toml
   [ecosystem]
   name = "fsc"
   
   [packages.cursor-fleet]
   source = "jbcom"  # Use jbcom's package
   
   [packages.pipeline-generator]
   type = "typescript"
   path = "packages/pipeline-generator"
   ```

### Phase 2: Extract Pipeline Generator

1. **Create packages/pipeline-generator**
   - Port logic from terraform-modules/.github/actions/
   - Make it a proper TypeScript package
   - Add unit tests

2. **Key files to port:**
   - `pipeline-config/action.yml` → `src/config.ts`
   - `pipeline-files/action.yml` → `src/generator.ts`
   - `tm-cli/action.yml` → `src/cli.ts`

3. **New workflow uses package:**
   ```yaml
   # .github/workflows/generate.yml
   - uses: actions/setup-node@v4
   - run: npx @fsc/pipeline-generator generate --config config/pipelines.yaml
   ```

### Phase 3: Extract Repo Bootstrap

1. **Port terraform-organization logic**
   - Go generators → TypeScript
   - Template rendering
   - GitHub API integration

2. **New bootstrap flow:**
   ```bash
   npx @fsc/repo-bootstrap create \
     --name new-repo \
     --template data-pipeline \
     --org FlipsideCrypto
   ```

### Phase 4: Consolidate Terraform Modules

1. **Option A: Keep separate repo, symlink**
   ```bash
   ln -s ../terraform-modules/modules packages/terraform-modules
   ```

2. **Option B: Move into control center**
   - Gives agent direct edit access
   - Requires updating all `source = "github.com/..."` refs

### Phase 5: Deprecate Old Repos

1. **terraform-modules** → Archived, points to fsc-control-center
2. **terraform-organization** → Archived, factory moved

## Benefits

| Aspect | Before | After |
|--------|--------|-------|
| Repos to coordinate | 3+ | 1 |
| Testing | Integration only | Unit + Integration |
| Typing | None | Full TypeScript |
| Agent context switches | Constant | Minimal |
| Change velocity | Days | Hours |
| Onboarding | "Read 5 repos" | "Read packages/" |

## Shared with jbcom

Both control centers use:
- `@jbcom/cursor-fleet` - Agent management
- `@jbcom/vendor-connectors` - Cloud provider SDKs
- Common patterns in ECOSYSTEM.toml

FSC-specific:
- `@fsc/pipeline-generator` - Terraform workflow generation
- `@fsc/repo-bootstrap` - FSC repo templates
- `@fsc/secrets-manager` - FSC secrets patterns

## Agent Implications

With this structure, the FSC control center agent can:

1. **Directly modify any package** - No cross-repo PRs
2. **Run tests locally** - `pnpm test` in any package
3. **Understand dependencies** - ECOSYSTEM.toml maps it
4. **Spawn specialized agents** - Using @jbcom/cursor-fleet
5. **Coordinate with jbcom** - Shared tooling, same patterns

The agent becomes a true "control manager" with direct authority over all FSC infrastructure tooling.
