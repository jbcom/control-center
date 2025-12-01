#!/usr/bin/env python3
"""
Auto-generate workspace structure from terraform-organization config.

Reads repositories.yaml and generates:
1. config/state-paths.yaml - Complete state registry
2. terraform/workspaces/*/terragrunt.hcl - Workspace configs
3. Dependency graph visualization
"""

import yaml
import os
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(__file__).resolve().parent.parent
REPOS_YAML = Path("/tmp/repositories.yaml")

# Default backend config
BACKEND = {
    "bucket": "flipside-terraform-state",
    "region": "us-east-1", 
    "dynamodb_table": "terraform-state-lock",
    "encrypt": True,
}

def parse_repositories():
    """Parse repositories.yaml and extract pipeline configs."""
    with open(REPOS_YAML) as f:
        data = yaml.safe_load(f)
    
    defaults = data.get("defaults", {})
    default_bind = defaults.get("terraform", {}).get("generator", {}).get("workspace", {}).get("bind_to_context", {})
    
    pipelines = {}
    for name, config in data.get("pipelines", {}).items():
        if config is None:
            config = {}
        
        tf_config = config.get("terraform", {})
        gen_config = tf_config.get("generator", {}).get("workspace", {})
        ws_config = tf_config.get("workspace", {})
        backend_config = tf_config.get("backend", {})
        
        # Determine state path
        backend_path = backend_config.get("backend_bucket_workspaces_path")
        if backend_path:
            # Has explicit backend path
            state_key = f"{backend_path}/generator/terraform.tfstate"
        else:
            # Derive from name
            state_key = f"terraform/state/{name}/workspaces/generator/terraform.tfstate"
        
        # Get bind_to_context (parent dependency)
        bind_to = gen_config.get("bind_to_context", default_bind)
        
        pipelines[name] = {
            "state_key": state_key,
            "bind_to_context": bind_to,
            "providers": ws_config.get("providers", []),
            "root_dir": gen_config.get("root_dir", "."),
            "use_sync": config.get("use_sync", False),
        }
    
    return pipelines, defaults


def build_dependency_graph(pipelines):
    """Build dependency graph from bind_to_context references."""
    # Map state paths to pipeline names
    state_to_pipeline = {}
    for name, config in pipelines.items():
        state_to_pipeline[config["state_key"]] = name
    
    # Build graph
    graph = defaultdict(list)
    for name, config in pipelines.items():
        parent_state = config.get("bind_to_context", {}).get("state_path")
        if parent_state:
            # Find parent by state path prefix matching
            for state_key, parent_name in state_to_pipeline.items():
                if parent_state.startswith(state_key.rsplit("/", 2)[0]):
                    graph[parent_name].append(name)
                    break
    
    return graph


def compute_layers(pipelines):
    """Compute execution layers based on dependencies."""
    # Known root-level workspaces (layer 0)
    layer_0 = {"terraform-organization"}
    
    # Layer 1: Direct children of terraform-organization
    layer_1 = {
        "terraform-aws-organization",
        "terraform-github-organization", 
        "terraform-google-organization",
        "terraform-grafana-architecture",
    }
    
    # Layer 2: Infrastructure (networking, secrets, etc.)
    layer_2 = {
        "terraform-aws-networking",
        "terraform-aws-secretsmanager",
        "terraform-vault",
        "terraform-aws-monitoring",
        "terraform-snowflake-architecture",
    }
    
    # Layer 3: Applications
    layer_3 = set(pipelines.keys()) - layer_0 - layer_1 - layer_2
    
    layers = {}
    for name in pipelines:
        if name in layer_0:
            layers[name] = 0
        elif name in layer_1:
            layers[name] = 1
        elif name in layer_2:
            layers[name] = 2
        else:
            layers[name] = 3
    
    return layers


def generate_state_paths_yaml(pipelines, layers):
    """Generate the complete state-paths.yaml."""
    
    output = {
        "backend": BACKEND,
        "workspaces": {},
    }
    
    # Add terraform-organization (the genesis)
    output["workspaces"]["organization/generator"] = {
        "hcl_path": "terraform/workspaces/organization/generator",
        "state_key": "terraform/state/terraform-organization/workspaces/generator/terraform.tfstate",
        "layer": 0,
        "description": "Genesis workspace - bootstraps everything else",
        "migrated_from": "github.com/FlipsideCrypto/terraform-organization",
    }
    
    # Add each pipeline
    for name, config in sorted(pipelines.items(), key=lambda x: (layers.get(x[0], 99), x[0])):
        ws_name = f"pipelines/{name}"
        
        entry = {
            "hcl_path": f"terraform/workspaces/pipelines/{name}",
            "state_key": config["state_key"],
            "layer": layers.get(name, 3),
            "migrated_from": f"github.com/FlipsideCrypto/{name}",
        }
        
        if config.get("bind_to_context"):
            entry["bind_to_context"] = config["bind_to_context"]
        
        if config.get("providers"):
            entry["providers"] = config["providers"]
        
        output["workspaces"][ws_name] = entry
    
    return output


def generate_workspace_dirs(pipelines, layers):
    """Generate workspace directory structure."""
    
    workspaces_dir = REPO_ROOT / "terraform" / "workspaces"
    
    # Create organization workspace
    org_dir = workspaces_dir / "organization" / "generator"
    org_dir.mkdir(parents=True, exist_ok=True)
    
    (org_dir / "terragrunt.hcl").write_text('''include "root" {
  path = find_in_parent_folders()
}

# Genesis workspace - no dependencies
''')
    
    # Create pipeline workspaces
    pipelines_dir = workspaces_dir / "pipelines"
    
    for name, config in pipelines.items():
        ws_dir = pipelines_dir / name
        ws_dir.mkdir(parents=True, exist_ok=True)
        
        bind_to = config.get("bind_to_context", {})
        providers = config.get("providers", [])
        
        content = f'''include "root" {{
  path = find_in_parent_folders()
}}

# Pipeline: {name}
# Layer: {layers.get(name, 3)}
# Migrated from: github.com/FlipsideCrypto/{name}
'''
        
        if bind_to:
            content += f'''
# Parent context binding
dependency "parent" {{
  config_path = "../../../{bind_to.get('state_path', '').split('/workspaces/')[0].replace('terraform/state/', '')}"
  
  # Mock outputs for plan without parent
  mock_outputs = {{
    context = {{}}
  }}
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}}

inputs = {{
  parent_context = dependency.parent.outputs
}}
'''
        
        if providers:
            content += f'''
# Additional providers required
# providers: {providers}
'''
        
        (ws_dir / "terragrunt.hcl").write_text(content)
    
    return len(pipelines) + 1  # +1 for organization


def main():
    print("=" * 60)
    print("🏗️  Generating Workspace Structure from terraform-organization")
    print("=" * 60)
    print()
    
    # Parse config
    print("📖 Parsing repositories.yaml...")
    pipelines, defaults = parse_repositories()
    print(f"   Found {len(pipelines)} pipelines")
    
    # Compute layers
    print("\n📊 Computing dependency layers...")
    layers = compute_layers(pipelines)
    for layer in range(4):
        names = [n for n, l in layers.items() if l == layer]
        print(f"   Layer {layer}: {len(names)} workspaces")
    
    # Generate state-paths.yaml
    print("\n📝 Generating config/state-paths.yaml...")
    state_paths = generate_state_paths_yaml(pipelines, layers)
    
    state_paths_file = REPO_ROOT / "config" / "state-paths.yaml"
    with open(state_paths_file, 'w') as f:
        f.write("# Auto-generated from terraform-organization/config/pipeline_categories/repositories.yaml\n")
        f.write("# DO NOT EDIT state_key values - they are IMMUTABLE\n")
        f.write("#\n")
        f.write("# Layers:\n")
        f.write("#   0: Genesis (terraform-organization)\n")
        f.write("#   1: Cloud organizations (aws, github, google, grafana)\n")
        f.write("#   2: Infrastructure (networking, secrets, vault)\n")
        f.write("#   3: Applications\n\n")
        yaml.dump(state_paths, f, default_flow_style=False, sort_keys=False)
    print(f"   ✅ Written {len(state_paths['workspaces'])} workspace entries")
    
    # Generate workspace directories
    print("\n📁 Generating workspace directories...")
    count = generate_workspace_dirs(pipelines, layers)
    print(f"   ✅ Created {count} workspace directories")
    
    # Print summary
    print("\n" + "=" * 60)
    print("✅ COMPLETE")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Review config/state-paths.yaml")
    print("  2. Copy modules from terraform-modules to terraform/modules/")
    print("  3. Run: ./scripts/validate-state-paths.sh")
    print("  4. Test: cd terraform/workspaces/pipelines/compass && terragrunt init")


if __name__ == "__main__":
    main()
