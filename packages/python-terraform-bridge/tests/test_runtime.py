"""Tests for TerraformRuntime integrations."""

from __future__ import annotations

from directed_inputs_class import directed_inputs
from python_terraform_bridge.runtime import TerraformRuntime


@directed_inputs(inputs={"region": "us-east-1"})
class DecoratedDataSource:
    """Minimal data source leveraging the decorator API."""

    def list_regions(self, region: str) -> dict[str, str]:
        return {"region": region}


def test_runtime_invokes_decorated_class_without_inheritance() -> None:
    """Ensure TerraformRuntime can execute decorator-based classes."""

    runtime = TerraformRuntime(DecoratedDataSource)

    result = runtime.invoke(
        "list_regions",
        from_stdin=False,
        to_stdout=False,
    )

    assert result == {"region": "us-east-1"}
