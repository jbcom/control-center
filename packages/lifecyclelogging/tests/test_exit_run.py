"""Unit tests for exit_run and log_results methods in the Logging class."""

from __future__ import annotations

import base64
import json
import os

from pathlib import Path
from unittest.mock import patch

import pytest

from lifecyclelogging import ExitRunError, Logging


@pytest.fixture
def logger() -> Logging:
    """Create a Logging instance for testing."""
    return Logging(
        enable_console=False,
        enable_file=False,
        enable_verbose_output=True,
        verbosity_threshold=5,
    )


class TestLogResults:
    """Tests for the log_results method."""

    def test_log_results_creates_file(self, logger: Logging, tmp_path: Path) -> None:
        """Test that log_results creates a JSON file with results."""
        os.chdir(tmp_path)
        results = {"key": "value"}
        logger.log_results(results, "test_results")

        log_file = tmp_path / "test_results.json"
        assert log_file.exists()
        content = json.loads(log_file.read_text())
        assert content == results

    def test_log_results_custom_extension(
        self, logger: Logging, tmp_path: Path
    ) -> None:
        """Test log_results with custom file extension."""
        os.chdir(tmp_path)
        results = {"key": "value"}
        logger.log_results(results, "test_results", ext=".txt")

        log_file = tmp_path / "test_results.txt"
        assert log_file.exists()

    def test_log_results_no_formatting(self, logger: Logging, tmp_path: Path) -> None:
        """Test log_results with no_formatting=True."""
        os.chdir(tmp_path)
        results = "raw string data"
        logger.log_results(results, "raw_results", no_formatting=True)

        log_file = tmp_path / "raw_results.json"
        assert log_file.exists()
        assert log_file.read_text() == "raw string data"

    def test_log_results_respects_verbosity(
        self, logger: Logging, tmp_path: Path
    ) -> None:
        """Test that log_results respects verbosity settings."""
        os.chdir(tmp_path)
        logger.enable_verbose_output = False
        results = {"key": "value"}
        logger.log_results(results, "verbose_results", verbose=True, verbosity=1)

        log_file = tmp_path / "verbose_results.json"
        assert not log_file.exists()


class TestExitRunNoExit:
    """Tests for exit_run with exit_on_completion=False."""

    def test_exit_run_returns_results(self, logger: Logging, tmp_path: Path) -> None:
        """Test that exit_run returns results when not exiting."""
        os.chdir(tmp_path)
        results = {"key": "value"}
        output = logger.exit_run(results, exit_on_completion=False)
        assert output == results

    def test_exit_run_none_results(self, logger: Logging, tmp_path: Path) -> None:
        """Test that exit_run handles None results."""
        os.chdir(tmp_path)
        output = logger.exit_run(None, exit_on_completion=False)
        assert output == {}

    def test_exit_run_unhump_results(self, logger: Logging, tmp_path: Path) -> None:
        """Test that exit_run converts camelCase to snake_case."""
        os.chdir(tmp_path)
        results = {"myKey": {"nestedKey": "value"}}
        output = logger.exit_run(results, unhump_results=True, exit_on_completion=False)
        assert "my_key" in output
        assert "nested_key" in output["my_key"]

    def test_exit_run_key_transform_snake_case(
        self, logger: Logging, tmp_path: Path
    ) -> None:
        """Test key_transform with snake_case string."""
        os.chdir(tmp_path)
        results = {"myKey": {"nestedKey": "value"}}
        output = logger.exit_run(
            results, key_transform="snake_case", exit_on_completion=False
        )
        assert "my_key" in output
        assert "nested_key" in output["my_key"]

    def test_exit_run_key_transform_camel_case(
        self, logger: Logging, tmp_path: Path
    ) -> None:
        """Test key_transform with camel_case string."""
        os.chdir(tmp_path)
        results = {"my_key": {"nested_key": "value"}}
        output = logger.exit_run(
            results, key_transform="camel_case", exit_on_completion=False
        )
        assert "myKey" in output
        assert "nestedKey" in output["myKey"]

    def test_exit_run_key_transform_pascal_case(
        self, logger: Logging, tmp_path: Path
    ) -> None:
        """Test key_transform with pascal_case string."""
        os.chdir(tmp_path)
        results = {"my_key": {"nested_key": "value"}}
        output = logger.exit_run(
            results, key_transform="pascal_case", exit_on_completion=False
        )
        assert "MyKey" in output
        assert "NestedKey" in output["MyKey"]

    def test_exit_run_key_transform_kebab_case(
        self, logger: Logging, tmp_path: Path
    ) -> None:
        """Test key_transform with kebab_case string."""
        os.chdir(tmp_path)
        results = {"myKey": {"nestedKey": "value"}}
        output = logger.exit_run(
            results, key_transform="kebab_case", exit_on_completion=False
        )
        assert "my-key" in output
        assert "nested-key" in output["my-key"]

    def test_exit_run_key_transform_custom_callable(
        self, logger: Logging, tmp_path: Path
    ) -> None:
        """Test key_transform with custom callable."""
        os.chdir(tmp_path)
        results = {"myKey": {"nestedKey": "value"}}
        output = logger.exit_run(
            results, key_transform=lambda k: k.upper(), exit_on_completion=False
        )
        assert "MYKEY" in output
        assert "NESTEDKEY" in output["MYKEY"]

    def test_exit_run_key_transform_invalid_raises(
        self, logger: Logging, tmp_path: Path
    ) -> None:
        """Test that invalid key_transform string raises ValueError."""
        os.chdir(tmp_path)
        with pytest.raises(ValueError, match="Unknown key_transform"):
            logger.exit_run(
                {"key": "value"}, key_transform="invalid_case", exit_on_completion=False
            )

    def test_exit_run_key_transform_nested_lists(
        self, logger: Logging, tmp_path: Path
    ) -> None:
        """Test key_transform handles nested lists of dicts."""
        os.chdir(tmp_path)
        results = {"myList": [{"itemKey": "v1"}, {"itemKey": "v2"}]}
        output = logger.exit_run(
            results, key_transform="snake_case", exit_on_completion=False
        )
        assert "my_list" in output
        assert all("item_key" in item for item in output["my_list"])

    def test_exit_run_with_prefix(self, logger: Logging, tmp_path: Path) -> None:
        """Test exit_run with prefix adds prefix to keys."""
        os.chdir(tmp_path)
        results = {"item1": {"fieldName": "value1"}}
        output = logger.exit_run(
            results,
            prefix="test",
            exit_on_completion=False,
        )
        assert "item1" in output
        assert "test_field_name" in output["item1"]

    def test_exit_run_prefix_allowlist(self, logger: Logging, tmp_path: Path) -> None:
        """Test exit_run only prefixes allowed keys."""
        os.chdir(tmp_path)
        results = {"item1": {"allowedField": "v1", "excludedField": "v2"}}
        output = logger.exit_run(
            results,
            prefix="pre",
            prefix_allowlist=["allowedField"],
            exit_on_completion=False,
        )
        assert "pre_allowed_field" in output["item1"]
        assert "excluded_field" in output["item1"]

    def test_exit_run_prefix_denylist(self, logger: Logging, tmp_path: Path) -> None:
        """Test exit_run excludes denied keys from prefixing."""
        os.chdir(tmp_path)
        results = {"item1": {"normalField": "v1", "excludedField": "v2"}}
        output = logger.exit_run(
            results,
            prefix="pre",
            prefix_denylist=["excludedField", "excluded_field"],
            exit_on_completion=False,
        )
        assert "pre_normal_field" in output["item1"]
        assert "excluded_field" in output["item1"]

    def test_exit_run_prefix_with_nested_lists(
        self, logger: Logging, tmp_path: Path
    ) -> None:
        """Test exit_run with prefix transforms keys in nested lists of dicts."""
        os.chdir(tmp_path)
        results = {
            "item1": {
                "myList": [{"itemKey": "v1"}, {"itemKey": "v2"}],
                "simpleField": "value",
            }
        }
        output = logger.exit_run(
            results,
            prefix="pre",
            exit_on_completion=False,
        )
        assert "item1" in output
        assert "pre_my_list" in output["item1"]
        assert "pre_simple_field" in output["item1"]
        # Verify that nested dict keys inside lists are also transformed
        assert all("item_key" in item for item in output["item1"]["pre_my_list"])

    def test_exit_run_sort_by_field(self, logger: Logging, tmp_path: Path) -> None:
        """Test exit_run sorts results by specified field."""
        os.chdir(tmp_path)
        results = {
            "a": {"sortKey": "zebra", "data": "first"},
            "b": {"sortKey": "apple", "data": "second"},
        }
        output = logger.exit_run(
            results,
            sort_by_field="sortKey",
            exit_on_completion=False,
        )
        assert "zebra" in output
        assert "apple" in output

    def test_exit_run_sort_by_field_duplicate_values(
        self, logger: Logging, tmp_path: Path
    ) -> None:
        """Test sort_by_field handles duplicate field values without data loss."""
        os.chdir(tmp_path)
        results = {
            "a": {"sortKey": "same_value", "data": "first"},
            "b": {"sortKey": "same_value", "data": "second"},
            "c": {"sortKey": "same_value", "data": "third"},
            "d": {"sortKey": "unique", "data": "fourth"},
        }
        output = logger.exit_run(
            results,
            sort_by_field="sortKey",
            exit_on_completion=False,
        )
        # All items should be preserved - no data loss
        assert len(output) == len(results)
        # First occurrence uses the field value as key
        assert "same_value" in output
        # Subsequent duplicates get numeric suffixes
        assert "same_value_1" in output
        assert "same_value_2" in output
        assert "unique" in output
        # Verify data is correct
        assert output["same_value"]["data"] == "first"
        assert output["same_value_1"]["data"] == "second"
        assert output["same_value_2"]["data"] == "third"
        assert output["unique"]["data"] == "fourth"

    def test_exit_run_sort_missing_field_raises(
        self, logger: Logging, tmp_path: Path
    ) -> None:
        """Test that sort_by_field raises when field is missing."""
        os.chdir(tmp_path)
        results = {"a": {"otherField": "value"}}
        with pytest.raises(RuntimeError, match="formatting error"):
            logger.exit_run(
                results,
                sort_by_field="missingField",
                exit_on_completion=False,
            )

    def test_exit_run_with_errors_raises(self, logger: Logging, tmp_path: Path) -> None:
        """Test that exit_run raises when error_list is not empty."""
        os.chdir(tmp_path)
        logger.error_list.append("Test error 1")
        logger.error_list.append("Test error 2")

        with pytest.raises(RuntimeError, match="Test error 1"):
            logger.exit_run({"key": "value"}, exit_on_completion=False)


class TestExitRunWithExit:
    """Tests for exit_run with exit_on_completion=True."""

    def test_exit_run_writes_to_stdout_and_exits(
        self, logger: Logging, tmp_path: Path
    ) -> None:
        """Test that exit_run writes JSON to stdout and exits."""
        os.chdir(tmp_path)
        results = {"key": "value"}

        with (
            patch("sys.stdout.write") as mock_write,
            patch("sys.exit") as mock_exit,
        ):
            logger.exit_run(results)
            mock_write.assert_called_once()
            written = mock_write.call_args[0][0]
            assert json.loads(written) == results
            mock_exit.assert_called_once_with(0)

    def test_exit_run_wraps_in_key(self, logger: Logging, tmp_path: Path) -> None:
        """Test that exit_run wraps results in specified key."""
        os.chdir(tmp_path)
        results = {"inner": "data"}

        with (
            patch("sys.stdout.write") as mock_write,
            patch("sys.exit"),
        ):
            logger.exit_run(results, key="outer")
            written = json.loads(mock_write.call_args[0][0])
            assert "outer" in written
            assert written["outer"] == results

    def test_exit_run_encode_to_base64(self, logger: Logging, tmp_path: Path) -> None:
        """Test that exit_run encodes entire result to base64."""
        os.chdir(tmp_path)
        results = {"key": "value"}

        with (
            patch("sys.stdout.write") as mock_write,
            patch("sys.exit"),
        ):
            logger.exit_run(results, encode_to_base64=True, key="encoded")
            written = json.loads(mock_write.call_args[0][0])
            decoded = base64.b64decode(written["encoded"]).decode("utf-8")
            assert "key" in decoded

    def test_exit_run_encode_all_values(self, logger: Logging, tmp_path: Path) -> None:
        """Test that exit_run encodes each value to base64."""
        os.chdir(tmp_path)
        results = {"item1": {"data": "value1"}, "item2": {"data": "value2"}}

        with (
            patch("sys.stdout.write") as mock_write,
            patch("sys.exit"),
        ):
            logger.exit_run(results, encode_all_values_to_base64=True)
            written = json.loads(mock_write.call_args[0][0])
            for key in ["item1", "item2"]:
                decoded = base64.b64decode(written[key]).decode("utf-8")
                assert "data" in decoded


class TestExitRunError:
    """Tests for ExitRunError exception."""

    def test_exit_run_error_is_exported(self) -> None:
        """Test that ExitRunError is properly exported."""
        # ExitRunError is imported at module level - verify it's a proper Exception subclass
        assert issubclass(ExitRunError, Exception)

    def test_exit_run_error_message(self) -> None:
        """Test ExitRunError can be raised with a message."""
        msg = "test message"
        with pytest.raises(ExitRunError, match=msg):
            raise ExitRunError(msg)
