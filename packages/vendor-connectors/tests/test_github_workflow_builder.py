"""Tests for GitHub workflow builder utility."""

from __future__ import annotations

from ruamel.yaml import YAML

from vendor_connectors.github import build_github_actions_workflow


def test_build_github_actions_workflow_generates_yaml():
    jobs = {
        "build": {
            "runs-on": "ubuntu-latest",
            "steps": [
                {"name": "Checkout", "uses": "actions/checkout@v4"},
                {"name": "Run tests", "run": "pytest"},
            ],
        }
    }

    workflow_yaml = build_github_actions_workflow(
        workflow_name="CI",
        jobs=jobs,
        concurrency_group="ci-main",
        environment_variables={"FOO": "bar"},
        secrets={"TOKEN": "GITHUB_TOKEN"},
        events={"push": True, "pull_request": False},
        inputs={"run-tests": {"required": False, "type": "boolean", "default": True}},
    )

    parsed = YAML().load(workflow_yaml)

    assert parsed["name"] == "CI"
    assert parsed["concurrency"] == "ci-main"
    assert parsed["env"]["FOO"] == "bar"
    assert parsed["env"]["TOKEN"] == "${{ secrets.GITHUB_TOKEN }}"
    assert "workflow_dispatch" in parsed["on"]
    assert parsed["jobs"]["build"]["steps"][1]["run"] == "pytest"
