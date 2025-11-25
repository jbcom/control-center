#!/usr/bin/env python3
"""Deploy workflow templates to ecosystem repositories.

This script:
1. Detects the repository type (Python lib, TS lib, Rust, game, etc.)
2. Selects appropriate workflow templates
3. Creates a PR with the workflow updates
4. Optionally auto-merges if tests pass
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

try:
    from github import Github, GithubException
    import yaml
except ImportError:
    print("ERROR: Required packages not installed")
    print("Run: pip install PyGithub pyyaml")
    sys.exit(1)


def detect_repo_type(repo: Any) -> str:
    """Detect the type of repository."""
    try:
        # Check for language indicators
        languages = repo.get_languages()
        
        # Check for specific files
        files_to_check = [
            "pyproject.toml",
            "package.json",
            "Cargo.toml",
            "setup.py",
            "go.mod",
        ]
        
        has_files = {}
        for file_name in files_to_check:
            try:
                repo.get_contents(file_name)
                has_files[file_name] = True
            except:
                has_files[file_name] = False
        
        # Determine type based on findings
        if has_files.get("pyproject.toml") or has_files.get("setup.py"):
            # Check if it's a game or library
            try:
                readme = repo.get_readme().decoded_content.decode('utf-8').lower()
                if 'game' in readme or 'pygame' in readme:
                    return "python-game"
            except:
                pass
            return "python-library"
        
        elif has_files.get("package.json"):
            try:
                pkg = json.loads(repo.get_contents("package.json").decoded_content)
                if 'phaser' in str(pkg.get('dependencies', {})) or 'game' in pkg.get('description', '').lower():
                    return "typescript-game"
            except:
                pass
            return "typescript-library"
        
        elif has_files.get("Cargo.toml"):
            try:
                cargo = repo.get_contents("Cargo.toml").decoded_content.decode('utf-8').lower()
                if 'bevy' in cargo or 'game' in cargo:
                    return "rust-game"
            except:
                pass
            return "rust-library"
        
        # Fallback to most common language
        if languages:
            primary_lang = max(languages.items(), key=lambda x: x[1])[0].lower()
            if 'python' in primary_lang:
                return "python-library"
            elif 'typescript' in primary_lang or 'javascript' in primary_lang:
                return "typescript-library"
            elif 'rust' in primary_lang:
                return "rust-library"
        
        return "unknown"
    
    except Exception as e:
        print(f"Error detecting repo type: {e}")
        return "unknown"


def get_workflow_templates(repo_type: str) -> list[Path]:
    """Get appropriate workflow templates for repo type."""
    templates_dir = Path("templates")
    
    type_map = {
        "python-library": [
            templates_dir / "python" / "library-ci.yml",
            templates_dir / "shared" / "dependabot.yml",
        ],
        "python-game": [
            templates_dir / "python" / "game-ci.yml",
            templates_dir / "shared" / "dependabot.yml",
        ],
        "typescript-library": [
            templates_dir / "typescript" / "npm-library-ci.yml",
            templates_dir / "shared" / "dependabot.yml",
        ],
        "typescript-game": [
            templates_dir / "typescript" / "game-ci.yml",
            templates_dir / "shared" / "dependabot.yml",
        ],
        "rust-library": [
            templates_dir / "rust" / "cargo-ci.yml",
            templates_dir / "shared" / "dependabot.yml",
        ],
        "rust-game": [
            templates_dir / "rust" / "game-ci.yml",
            templates_dir / "shared" / "dependabot.yml",
        ],
    }
    
    return type_map.get(repo_type, [])


def create_deployment_pr(
    repo: Any,
    workflows: list[tuple[str, str]],
    deployment_id: str,
    dry_run: bool = True
) -> str:
    """Create a PR with workflow updates."""
    branch_name = f"hub-deploy/{deployment_id}"
    
    try:
        # Get default branch
        default_branch = repo.default_branch
        base_ref = repo.get_git_ref(f"heads/{default_branch}")
        
        # Create new branch
        if not dry_run:
            repo.create_git_ref(
                ref=f"refs/heads/{branch_name}",
                sha=base_ref.object.sha
            )
        
        # Create/update workflow files
        for file_path, content in workflows:
            try:
                # Try to get existing file
                existing_file = repo.get_contents(file_path, ref=branch_name if not dry_run else default_branch)
                if not dry_run:
                    repo.update_file(
                        path=file_path,
                        message=f"🤖 Update CI/CD from control hub [{deployment_id}]",
                        content=content,
                        sha=existing_file.sha,
                        branch=branch_name
                    )
                print(f"  ✅ Would update: {file_path}")
            except:
                # File doesn't exist, create it
                if not dry_run:
                    repo.create_file(
                        path=file_path,
                        message=f"🤖 Add CI/CD from control hub [{deployment_id}]",
                        content=content,
                        branch=branch_name
                    )
                print(f"  ✅ Would create: {file_path}")
        
        # Create PR
        if not dry_run:
            pr = repo.create_pull(
                title=f"🤖 Update CI/CD from control hub [{deployment_id}]",
                body=f"""## Automated CI/CD Update
                
This PR updates CI/CD workflows from the jbcom ecosystem control hub.

**Deployment ID:** `{deployment_id}`

### Changes
- Updated workflow templates to latest versions
- Ensured consistency across ecosystem
- Applied best practices and security updates

### Testing
Workflows will be tested automatically. If all checks pass, this PR can be auto-merged.

---
*This PR was created automatically by the [jbcom control hub](https://github.com/jbcom/python-library-template)*
""",
                head=branch_name,
                base=default_branch
            )
            return pr.html_url
        else:
            print(f"  🏃 DRY RUN: Would create PR on branch {branch_name}")
            return f"[DRY RUN] Would create PR for {repo.full_name}"
    
    except Exception as e:
        print(f"  ❌ Error creating PR: {e}")
        return ""


def main() -> None:
    """Main deployment function."""
    parser = argparse.ArgumentParser(description="Deploy workflows to ecosystem repos")
    parser.add_argument("--repo", required=True, help="Repository (org/name)")
    parser.add_argument("--deployment-id", required=True, help="Deployment ID")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    
    args = parser.parse_args()
    
    # Get GitHub token
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("ERROR: GITHUB_TOKEN environment variable not set")
        sys.exit(1)
    
    # Initialize GitHub client
    g = Github(token)
    
    try:
        # Get repository
        print(f"📦 Deploying to {args.repo}")
        repo = g.get_repo(args.repo)
        
        # Detect repo type
        print("  🔍 Detecting repository type...")
        repo_type = detect_repo_type(repo)
        print(f"  📂 Type: {repo_type}")
        
        if repo_type == "unknown":
            print("  ⚠️  Unknown repository type, skipping")
            return
        
        # Get workflow templates
        print("  📝 Loading workflow templates...")
        template_files = get_workflow_templates(repo_type)
        
        workflows = []
        for template_file in template_files:
            if template_file.exists():
                content = template_file.read_text()
                # Determine target path
                if "dependabot" in template_file.name:
                    target_path = ".github/dependabot.yml"
                else:
                    target_path = f".github/workflows/{template_file.name}"
                workflows.append((target_path, content))
                print(f"    ✅ Loaded: {template_file}")
        
        if not workflows:
            print("  ⚠️  No workflows to deploy")
            return
        
        # Create PR
        print("  🚀 Creating deployment PR...")
        pr_url = create_deployment_pr(repo, workflows, args.deployment_id, args.dry_run)
        
        if pr_url:
            print(f"  ✅ PR created: {pr_url}")
        else:
            print("  ❌ Failed to create PR")
            sys.exit(1)
    
    except GithubException as e:
        print(f"ERROR: GitHub API error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
