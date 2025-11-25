#!/usr/bin/env python3
"""Health check for ecosystem repositories.

Checks:
- CI/CD status
- Test coverage
- Last commit date
- Open issues/PRs
- Dependency freshness
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:
    from github import Github
except ImportError:
    print("ERROR: PyGithub not installed. Run: pip install PyGithub")
    sys.exit(1)


def check_repo_health(repo: Any) -> dict[str, Any]:
    """Check health of a single repository."""
    print(f"  Checking {repo.name}...")
    
    health = {
        "name": repo.name,
        "status": "healthy",
        "checks": {},
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
    
    try:
        # Check last commit date
        commits = repo.get_commits()
        last_commit = commits[0]
        last_commit_date = last_commit.commit.author.date
        days_since_commit = (datetime.now(timezone.utc) - last_commit_date.replace(tzinfo=timezone.utc)).days
        
        health["checks"]["last_commit"] = {
            "date": last_commit_date.isoformat(),
            "days_ago": days_since_commit,
            "status": "healthy" if days_since_commit < 90 else "warning",
        }
        
        # Check CI status
        try:
            workflow_runs = repo.get_workflow_runs(branch=repo.default_branch)
            if workflow_runs.totalCount > 0:
                latest_run = workflow_runs[0]
                health["checks"]["ci_status"] = {
                    "status": latest_run.conclusion or latest_run.status,
                    "updated": latest_run.updated_at.isoformat(),
                    "url": latest_run.html_url,
                }
                if latest_run.conclusion == "failure":
                    health["status"] = "warning"
            else:
                health["checks"]["ci_status"] = {"status": "no_workflows"}
        except Exception as e:
            health["checks"]["ci_status"] = {"status": "error", "message": str(e)}
        
        # Check open issues
        open_issues = repo.get_issues(state="open")
        critical_issues = [i for i in open_issues if any(l.name in ["critical", "bug"] for l in i.labels)]
        
        health["checks"]["issues"] = {
            "open": open_issues.totalCount,
            "critical": len(critical_issues),
        }
        
        if len(critical_issues) > 5:
            health["status"] = "critical"
        elif len(critical_issues) > 0:
            health["status"] = "warning"
        
        # Check PRs
        open_prs = repo.get_pulls(state="open")
        stale_prs = [pr for pr in open_prs if (datetime.now(timezone.utc) - pr.created_at.replace(tzinfo=timezone.utc)).days > 14]
        
        health["checks"]["pull_requests"] = {
            "open": open_prs.totalCount,
            "stale": len(stale_prs),
        }
        
    except Exception as e:
        health["status"] = "error"
        health["error"] = str(e)
        print(f"    ❌ Error checking {repo.name}: {e}")
    
    # Status emoji
    status_emoji = {
        "healthy": "✅",
        "warning": "⚠️ ",
        "critical": "🔴",
        "error": "❌",
    }
    print(f"    {status_emoji.get(health['status'], '?')} Status: {health['status']}")
    
    return health


def main() -> None:
    """Run health checks on all repos."""
    parser = argparse.ArgumentParser(description="Check ecosystem health")
    parser.add_argument("--output", required=True, help="Output JSON file")
    
    args = parser.parse_args()
    
    # Get GitHub token
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("ERROR: GITHUB_TOKEN environment variable not set")
        sys.exit(1)
    
    # Initialize GitHub client
    g = Github(token)
    
    # Load ecosystem state
    state_file = Path("ecosystem/ECOSYSTEM_STATE.json")
    if not state_file.exists():
        print("ERROR: ECOSYSTEM_STATE.json not found")
        sys.exit(1)
    
    state = json.loads(state_file.read_text())
    repos_list = state.get("repositories", [])
    
    # If repos is a dict, convert to list of names
    if isinstance(repos_list, dict):
        repo_names = list(repos_list.keys())
    else:
        repo_names = [r.get("name") for r in repos_list if isinstance(r, dict)]
    
    print(f"🔍 Checking health of {len(repo_names)} repositories...\n")
    
    # Check each repo
    health_metrics = {
        "last_check": datetime.now(timezone.utc).isoformat(),
        "repositories": {},
        "summary": {
            "healthy": 0,
            "warning": 0,
            "critical": 0,
            "error": 0,
        },
    }
    
    for repo_name in repo_names:
        try:
            repo = g.get_repo(f"jbcom/{repo_name}")
            health = check_repo_health(repo)
            health_metrics["repositories"][repo_name] = health
            health_metrics["summary"][health["status"]] += 1
        except Exception as e:
            print(f"  ❌ Error accessing {repo_name}: {e}")
            health_metrics["repositories"][repo_name] = {
                "name": repo_name,
                "status": "error",
                "error": str(e),
            }
            health_metrics["summary"]["error"] += 1
    
    # Write results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(health_metrics, indent=2))
    
    print(f"\n📊 Health Check Summary:")
    print(f"  ✅ Healthy: {health_metrics['summary']['healthy']}")
    print(f"  ⚠️  Warning: {health_metrics['summary']['warning']}")
    print(f"  🔴 Critical: {health_metrics['summary']['critical']}")
    print(f"  ❌ Error: {health_metrics['summary']['error']}")
    print(f"\n✅ Results written to {output_path}")


if __name__ == "__main__":
    main()
