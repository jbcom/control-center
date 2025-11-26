#!/usr/bin/env python3
"""
jbcom Ecosystem Manager

A simple CLI tool to manage all jbcom repositories from the control center.
Uses the ECOSYSTEM_MANIFEST.yaml as the source of truth.

Usage:
    python manage.py status          # Show ecosystem status
    python manage.py clone-all       # Clone all repos to ./repos/
    python manage.py pull-all        # Pull latest for all repos
    python manage.py check-ci        # Check CI status across ecosystem
    python manage.py find-integration <name>  # Find repos using an integration
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import yaml


def load_manifest() -> dict:
    """Load the ecosystem manifest."""
    project_root = Path(__file__).resolve().parents[2]
    manifest_path = project_root / "ecosystem" / "ECOSYSTEM_MANIFEST.yaml"
    if not manifest_path.exists():
        print(f"❌ Manifest not found: {manifest_path}")
        sys.exit(1)
    
    with open(manifest_path) as f:
        return yaml.safe_load(f)


def get_all_repos(manifest: dict) -> list[dict]:
    """Extract all repos from manifest."""
    repos = []
    
    # Core libraries
    for lang, items in manifest.get("core_libraries", {}).items():
        for item in items:
            item["category"] = "core"
            item["language"] = lang
            repos.append(item)
    
    # Infrastructure
    for category, items in manifest.get("infrastructure", {}).items():
        for item in items:
            item["category"] = f"infra/{category}"
            repos.append(item)
    
    # Games
    for lang, items in manifest.get("games", {}).items():
        for item in items:
            item["category"] = "games"
            item["language"] = lang
            repos.append(item)
    
    return repos


def cmd_status(manifest: dict) -> None:
    """Show ecosystem status."""
    repos = get_all_repos(manifest)
    stats = manifest.get("stats", {})
    
    print("=" * 60)
    print("🌐 jbcom Ecosystem Status")
    print("=" * 60)
    print(f"\n📊 Total Active: {stats.get('total_active', len(repos))}")
    print(f"📦 Total Archived: {stats.get('total_archived', 0)}")
    
    print("\n📂 By Language:")
    for lang, count in stats.get("by_language", {}).items():
        print(f"   {lang}: {count}")
    
    print("\n🔒 By Visibility:")
    for vis, count in stats.get("by_visibility", {}).items():
        print(f"   {vis}: {count}")
    
    print("\n📋 Repositories:")
    for repo in sorted(repos, key=lambda r: r.get("category", "")):
        status_icon = "✅" if repo.get("status") == "production" else "🚧" if repo.get("status") == "active" else "💤"
        vis_icon = "🔓" if repo.get("visibility") == "public" else "🔒"
        print(f"   {status_icon} {vis_icon} {repo['name']} ({repo.get('language', 'unknown')}) - {repo.get('category', 'unknown')}")


def cmd_clone_all(manifest: dict) -> None:
    """Clone all repos to ./repos/ directory."""
    repos = get_all_repos(manifest)
    repos_dir = Path("./repos")
    repos_dir.mkdir(exist_ok=True)
    
    print(f"📥 Cloning {len(repos)} repositories to {repos_dir.absolute()}\n")
    
    for repo in repos:
        name = repo["name"]
        url = repo["url"]
        target = repos_dir / name
        
        if target.exists():
            print(f"⏭️  {name} (already exists)")
            continue
        
        print(f"📥 Cloning {name}...")
        result = subprocess.run(
            ["gh", "repo", "clone", url, str(target)],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"   ✅ Done")
        else:
            print(f"   ❌ Failed: {result.stderr}")


def cmd_pull_all(manifest: dict) -> None:
    """Pull latest for all cloned repos."""
    repos_dir = Path("./repos")
    
    if not repos_dir.exists():
        print("❌ No repos directory. Run 'clone-all' first.")
        sys.exit(1)
    
    for repo_path in sorted(repos_dir.iterdir()):
        if not repo_path.is_dir():
            continue
        
        print(f"🔄 Pulling {repo_path.name}...")
        result = subprocess.run(
            ["git", "-C", str(repo_path), "pull", "--ff-only"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            if "Already up to date" in result.stdout:
                print(f"   ✅ Up to date")
            else:
                print(f"   ✅ Updated")
        else:
            print(f"   ❌ Failed: {result.stderr}")


def cmd_find_integration(manifest: dict, integration_name: str) -> None:
    """Find repos using a specific integration."""
    repos = get_all_repos(manifest)
    
    print(f"🔍 Repos using '{integration_name}':\n")
    
    found = False
    for repo in repos:
        integrations = repo.get("has_integrations", [])
        if integration_name.lower() in [i.lower() for i in integrations]:
            found = True
            print(f"   📦 {repo['name']} ({repo.get('language', 'unknown')})")
    
    if not found:
        print(f"   No repos found using '{integration_name}'")
    
    # Check consolidation targets in vendor-connectors
    vc = None
    for lib in manifest.get("core_libraries", {}).get("python", []):
        if lib["name"] == "vendor-connectors":
            vc = lib
            break
    
    if vc:
        consolidate = vc.get("consolidate_from", [])
        for item in consolidate:
            if integration_name.lower() in item.get("path", "").lower():
                print(f"\n📋 Consolidation source:")
                print(f"   From: {item['repo']}")
                print(f"   Path: {item['path']}")
                print(f"   Lang: {item['language']}")


def cmd_check_ci(manifest: dict) -> None:
    """Check CI status across ecosystem."""
    repos = get_all_repos(manifest)
    
    print("🔍 Checking CI status...\n")
    
    for repo in repos:
        name = repo["name"]
        result = subprocess.run(
            ["gh", "run", "list", "--repo", f"jbcom/{name}", "--limit", "1", "--json", "status,conclusion,name"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            runs = json.loads(result.stdout)
            if runs:
                run = runs[0]
                status = run.get("conclusion") or run.get("status")
                icon = "✅" if status == "success" else "❌" if status == "failure" else "🔄"
                print(f"   {icon} {name}: {status}")
            else:
                print(f"   ⚪ {name}: No runs")
        else:
            print(f"   ⚠️  {name}: Could not check")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    manifest = load_manifest()
    
    if command == "status":
        cmd_status(manifest)
    elif command == "clone-all":
        cmd_clone_all(manifest)
    elif command == "pull-all":
        cmd_pull_all(manifest)
    elif command == "check-ci":
        cmd_check_ci(manifest)
    elif command == "find-integration":
        if len(sys.argv) < 3:
            print("Usage: manage.py find-integration <name>")
            sys.exit(1)
        cmd_find_integration(manifest, sys.argv[2])
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
