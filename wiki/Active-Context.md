# Active Context

## Current Focus
- **Architectural Refactor** - Decorator-based input handling and Terraform bridge
- **terraform-modules Migration** - 97% complete (134/138 functions)
- **Package Development** - Three interconnected packages being enhanced

## Session: Nov 29, 2025 (Architectural Evolution)

### Architectural Changes

#### 1. directed-inputs-class: Inheritance → Decorators

**Problem**: Old API forced inheritance and boilerplate
```python
# OLD (WET pattern)
class MyService(DirectedInputsClass):
    def list_users(self, domain: str | None = None):
        domain = self.get_input("domain", domain)  # Manual everywhere!
        return self._client.list_users(domain)
```

**Solution**: New decorator-based API
```python
# NEW (DRY pattern)
from directed_inputs_class import directed_inputs, input_config

@directed_inputs(from_stdin=True)
class MyService:
    def list_users(self, domain: str | None = None):
        # domain is automatically populated from stdin/env!
        return self._client.list_users(domain)
    
    @input_config("api_key", source_name="API_KEY", required=True)
    def secure_method(self, api_key: str):
        return self._client.secure(api_key)
```

**Files Created**:
| File | Purpose |
|------|---------|
| `directed_inputs_class/decorators.py` | `@directed_inputs`, `@input_config` |
| `tests/test_decorators.py` | 23 new tests |

**Status**: ✅ Complete (39 tests passing)

#### 2. python-terraform-bridge: New OSS Package

**Purpose**: Extract Terraform ↔ Python bridge code from terraform-modules

**Key Innovation**: Decorator-based registration (replaces docstring parsing)
```python
from python_terraform_bridge import TerraformRegistry

registry = TerraformRegistry()

@registry.data_source(key="users", module_class="github")
def list_users(org: str | None = None) -> dict:
    return {...}

# Generate Terraform modules
registry.generate_modules("./terraform-modules")
```

**Components**:
| Component | Purpose |
|-----------|---------|
| `module_resources.py` | Generate Terraform modules from Python methods |
| `registry.py` | Decorator-based method registration |
| `parameter.py` | Parameter definition and type inference |
| `runtime.py` | External data provider runtime |
| `cli.py` | CLI tool (`terraform-bridge generate/list/run`) |

**Status**: ✅ Complete (50 tests passing)

#### 3. Integration Path

The architectural relationship:
```
directed-inputs-class          python-terraform-bridge
        │                               │
        │ @directed_inputs              │ @registry.data_source
        │ @input_config                 │ @registry.null_resource
        │                               │
        └───────────┬───────────────────┘
                    │
                    ▼
            terraform-modules
           (consumer, not owned)
```

### Migration Status Summary

```
Progress: [█████████████████░] 97%

Cloud Operations (vendor-connectors):
  Completed: 134 functions
  Remaining: 4 functions (complex preprocessing)
  Not Migrating: 7 functions (FSC-specific)

Terraform Bridge (python-terraform-bridge):
  Core: ✅ Complete
  Tests: ✅ 50 passing
  
Input Handling (directed-inputs-class):
  Decorator API: ✅ Complete
  Tests: ✅ 39 passing (23 new + 16 legacy)
```

### Remaining Functions (4 total)

| Function | Source | Notes |
|----------|--------|-------|
| `label_aws_account` | terraform_data_source.py | Terraform preprocessing |
| `classify_aws_accounts` | terraform_data_source.py | Depends on label_account |
| `preprocess_aws_organization` | terraform_data_source.py | Terraform preprocessing |
| `build_github_actions_workflow` | terraform_data_source.py | Complex YAML builder |

### NOT Migrating (FSC-Specific)

| Function | Reason |
|----------|--------|
| `get_new_aws_controltower_accounts_from_google` | Cross-provider sync logic |
| `get_aws_access_google_groups` | FSC naming conventions |
| `update_aws_account_access_google_groups` | FSC group management |
| `create_dbt_cloud_extended_attribute` | dbt Cloud specific |
| `generate_github_actions_files` | FSC workflow patterns |
| `get_missing_github_files` | FSC repo standards |
| `create_google_data_models_project_*` | FSC project naming |

## PR Plan

See [`.cursor/agents/terraform-modules-migration/PR_PLAN.md`](/.cursor/agents/terraform-modules-migration/PR_PLAN.md) for the complete PR dependency chain and handoff protocol.

## Documentation

| Document | Location | Purpose |
|----------|----------|---------|
| Orchestration | `.cursor/agents/terraform-modules-migration/ORCHESTRATION.md` | Full context |
| vendor-connectors API | `packages/vendor-connectors/API_REFERENCE.md` | API reference |
| vendor-connectors Migration | `packages/vendor-connectors/MIGRATION_STATUS.md` | Migration tracking |
| python-terraform-bridge | `packages/python-terraform-bridge/README.md` | Package docs |

## Tracking Issues
| Repo | Issue | Description |
|------|-------|-------------|
| FlipsideCrypto/terraform-modules | #220 | Migration gap analysis (authoritative) |
| jbcom/jbcom-control-center | #245 | Migration implementation PR |

## Next Actions

1. Create focused PRs (per PR Plan above)
2. Update directed-inputs-class README for new decorator API
3. Integrate python-terraform-bridge with terraform-modules
4. Complete remaining 4 function migrations
