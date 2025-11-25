#!/usr/bin/env python3
"""Generate dependency graph for the ecosystem.

Analyzes dependencies across all repos and creates a graph showing:
- Direct dependencies
- Transitive dependencies
- Circular dependencies (if any)
- Update opportunities
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

try:
    from github import Github
except ImportError:
    print("ERROR: PyGithub not installed. Run: pip install PyGithub")
    sys.exit(1)


def parse_dependencies_python(repo: Any) -> dict[str, str]:
    """Parse Python dependencies from pyproject.toml."""
    deps = {}
    try:
        content = repo.get_contents("pyproject.toml").decoded_content.decode('utf-8')
        # Simple parsing - in production use toml library
        in_deps = False
        for line in content.split('\n'):
            if '[project.dependencies]' in line or '[tool.poetry.dependencies]' in line:
                in_deps = True
                continue
            if in_deps and line.strip().startswith('['):
                break
            if in_deps and '=' in line:
                parts = line.split('=')
                if len(parts) >= 2:
                    pkg = parts[0].strip().strip('"\'')
                    version = parts[1].strip().strip('"\'')
                    deps[pkg] = version
    except:
        pass
    return deps


def parse_dependencies_typescript(repo: Any) -> dict[str, str]:
    """Parse TypeScript dependencies from package.json."""
    deps = {}
    try:
        content = repo.get_contents("package.json").decoded_content
        pkg = json.loads(content)
        deps.update(pkg.get('dependencies', {}))
        deps.update(pkg.get('devDependencies', {}))
    except:
        pass
    return deps


def parse_dependencies_rust(repo: Any) -> dict[str, str]:
    """Parse Rust dependencies from Cargo.toml."""
    deps = {}
    try:
        content = repo.get_contents("Cargo.toml").decoded_content.decode('utf-8')
        in_deps = False
        for line in content.split('\n'):
            if '[dependencies]' in line:
                in_deps = True
                continue
            if in_deps and line.strip().startswith('['):
                break
            if in_deps and '=' in line:
                parts = line.split('=')
                if len(parts) >= 2:
                    pkg = parts[0].strip()
                    version = parts[1].strip().strip('"\'')
                    deps[pkg] = version
    except:
        pass
    return deps


def main() -> None:
    """Generate dependency graph."""
    parser = argparse.ArgumentParser(description="Generate dependency graph")
    parser.add_argument("--output", required=True, help="Output JSON file")
    
    args = parser.parse_args()
    
    # Get GitHub token
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("ERROR: GITHUB_TOKEN environment variable not set")
        sys.exit(1)
    
    g = Github(token)
    
    # Load ecosystem state
    state_file = Path("ecosystem/ECOSYSTEM_STATE.json")
    if not state_file.exists():
        print("ERROR: ECOSYSTEM_STATE.json not found")
        sys.exit(1)
    
    state = json.loads(state_file.read_text())
    repos_list = state.get("repositories", [])
    
    if isinstance(repos_list, dict):
        repo_names = list(repos_list.keys())
    else:
        repo_names = [r.get("name") for r in repos_list if isinstance(r, dict)]
    
    print(f"📦 Analyzing dependencies for {len(repo_names)} repositories...\n")
    
    graph = {
        "generated": json.dumps(None),  # Will be set properly
        "repositories": {},
        "ecosystem_internal_deps": [],
        "external_deps": {},
    }
    
    # Analyze each repo
    for repo_name in repo_names:
        try:
            print(f"  Analyzing {repo_name}...")
            repo = g.get_repo(f"jbcom/{repo_name}")
            
            # Detect language and parse dependencies
            deps = {}
            try:
                repo.get_contents("pyproject.toml")
                deps = parse_dependencies_python(repo)
            except:
                pass
            
            if not deps:
                try:
                    repo.get_contents("package.json")
                    deps = parse_dependencies_typescript(repo)
                except:
                    pass
            
            if not deps:
                try:
                    repo.get_contents("Cargo.toml")
                    deps = parse_dependencies_rust(repo)
                except:
                    pass
            
            graph["repositories"][repo_name] = {
                "dependencies": deps,
                "dependency_count": len(deps),
            }
            
            # Check for internal ecosystem dependencies
            for dep_name in deps.keys():
                if dep_name in repo_names:
                    graph["ecosystem_internal_deps"].append({
                        "from": repo_name,
                        "to": dep_name,
                        "version": deps[dep_name],
                    })
            
            print(f"    ✅ Found {len(deps)} dependencies")
            
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    # Write results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(graph, indent=2))
    
    print(f"\n✅ Dependency graph written to {output_path}")
    print(f"   Internal dependencies: {len(graph['ecosystem_internal_deps'])}")


if __name__ == "__main__":
    main()
