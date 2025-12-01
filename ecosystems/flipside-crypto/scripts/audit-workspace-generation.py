#!/usr/bin/env python3
"""
Workspace Generation Audit

For each workspace with a config.tf.json:
1. Record the existing file
2. Compare against expected generation
3. Output diagnostic report

This builds an audit trail and surfaces any discrepancies.
"""

import json
import os
import hashlib
from pathlib import Path
from datetime import datetime

WORKSPACE_ROOT = Path("/workspace/terraform/workspaces")
REPORT_DIR = Path("/workspace/reports/workspace-audit")

def hash_file(path: Path) -> str:
    """Get SHA256 hash of file contents."""
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]

def analyze_config(config_path: Path) -> dict:
    """Extract key fields from config.tf.json for analysis."""
    try:
        config = json.loads(config_path.read_text())
        return {
            "has_backend": "backend" in config.get("terraform", {}),
            "state_key": config.get("terraform", {}).get("backend", {}).get("s3", {}).get("key", "none"),
            "workspace_name": config.get("locals", {}).get("workspace_name", "unknown"),
            "providers": list(config.get("provider", {}).keys()),
            "modules": list(config.get("module", {}).keys()),
            "data_sources": list(config.get("data", {}).keys()),
            "required_version": config.get("terraform", {}).get("required_version", "unknown"),
        }
    except Exception as e:
        return {"error": str(e)}

def audit_workspaces():
    """Audit all workspaces and generate report."""
    
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total": 0,
            "with_config": 0,
            "without_config": 0,
            "by_pipeline": {},
        },
        "workspaces": [],
    }
    
    # Find all directories that look like workspaces
    for config_path in sorted(WORKSPACE_ROOT.rglob("config.tf.json")):
        ws_dir = config_path.parent
        rel_path = ws_dir.relative_to(WORKSPACE_ROOT)
        
        # Determine pipeline (first component of path)
        parts = rel_path.parts
        pipeline = parts[0] if parts else "unknown"
        ws_name = "/".join(parts[1:]) if len(parts) > 1 else parts[0]
        
        analysis = analyze_config(config_path)
        
        entry = {
            "path": str(rel_path),
            "pipeline": pipeline,
            "workspace": ws_name,
            "config_hash": hash_file(config_path),
            "config_size": config_path.stat().st_size,
            "analysis": analysis,
        }
        
        # Check for main.tf (hand-written workspace logic)
        main_tf = ws_dir / "main.tf"
        if main_tf.exists():
            entry["has_main_tf"] = True
            entry["main_tf_size"] = main_tf.stat().st_size
        else:
            entry["has_main_tf"] = False
        
        # Check for outputs.tf
        outputs_tf = ws_dir / "outputs.tf"
        entry["has_outputs"] = outputs_tf.exists()
        
        report["workspaces"].append(entry)
        report["summary"]["total"] += 1
        report["summary"]["with_config"] += 1
        
        # Count by pipeline
        if pipeline not in report["summary"]["by_pipeline"]:
            report["summary"]["by_pipeline"][pipeline] = 0
        report["summary"]["by_pipeline"][pipeline] += 1
    
    # Write JSON report
    report_path = REPORT_DIR / f"audit-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    report_path.write_text(json.dumps(report, indent=2))
    
    # Write summary markdown
    summary_path = REPORT_DIR / "LATEST.md"
    with open(summary_path, 'w') as f:
        f.write(f"# Workspace Generation Audit\n\n")
        f.write(f"**Generated**: {report['timestamp']}\n\n")
        f.write(f"## Summary\n\n")
        f.write(f"- **Total Workspaces**: {report['summary']['total']}\n")
        f.write(f"- **With config.tf.json**: {report['summary']['with_config']}\n\n")
        
        f.write(f"### By Pipeline\n\n")
        f.write("| Pipeline | Workspaces |\n")
        f.write("|----------|------------|\n")
        for pipeline, count in sorted(report["summary"]["by_pipeline"].items()):
            f.write(f"| {pipeline} | {count} |\n")
        
        f.write(f"\n## Workspace Details\n\n")
        
        current_pipeline = None
        for ws in report["workspaces"]:
            if ws["pipeline"] != current_pipeline:
                current_pipeline = ws["pipeline"]
                f.write(f"\n### {current_pipeline}\n\n")
            
            analysis = ws["analysis"]
            status = "✅" if not analysis.get("error") else "❌"
            f.write(f"- {status} **{ws['workspace']}**\n")
            f.write(f"  - State: `{analysis.get('state_key', 'N/A')}`\n")
            f.write(f"  - Providers: {', '.join(analysis.get('providers', []))}\n")
            f.write(f"  - Has main.tf: {ws['has_main_tf']}\n")
    
    print(f"✅ Audit complete")
    print(f"   Total workspaces: {report['summary']['total']}")
    print(f"   Report: {report_path}")
    print(f"   Summary: {summary_path}")
    
    return report

if __name__ == "__main__":
    audit_workspaces()
