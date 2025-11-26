"""Property-based tests for the Logging class in the lifecyclelogging package."""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st
from lifecyclelogging import Logging


# Strategy for valid log levels
valid_log_levels = st.sampled_from(["debug", "info", "warning", "error", "critical"])  # type: ignore[arg-type]

# Strategy for log messages
log_messages = st.text(min_size=1, max_size=1000)

# Strategy for JSON-compatible data
json_data = st.recursive(
    st.none()
    | st.booleans()
    | st.integers(min_value=-(2**53), max_value=2**53)
    | st.floats(allow_nan=False, allow_infinity=False)
    | st.text(alphabet=st.characters(blacklist_categories=("Cs",), max_codepoint=127)),
    lambda children: st.lists(children, max_size=5)
    | st.dictionaries(
        st.text(
            min_size=1,
            alphabet=st.characters(blacklist_categories=("Cs",), max_codepoint=127),
        ),
        children,
        max_size=5,
    ),
    max_leaves=10,
)

# Strategy for verbosity levels
verbosity_levels = st.integers(min_value=1, max_value=5)

# Strategy for markers
marker_names = st.text(
    min_size=1,
    max_size=50,
    alphabet=st.characters(blacklist_categories=("Cs",), max_codepoint=127),
)


@given(message=log_messages, log_level=valid_log_levels)
def test_basic_logging_properties(message: str, log_level: str) -> None:
    """Test basic logging properties using property-based testing.

    This test verifies that messages are logged correctly at various log levels.
    """
    logger = Logging(enable_console=False, enable_file=False)

    result = logger.logged_statement(message, log_level=log_level)  # type: ignore[arg-type]

    assert result is not None
    assert message in result


@given(message=log_messages, marker=marker_names)
def test_context_marker_properties(message: str, marker: str) -> None:
    """Test context marker properties using property-based testing.

    This test verifies that messages are correctly prefixed with context markers.
    """
    logger = Logging(enable_console=False, enable_file=False)

    result = logger.logged_statement(
        message,
        context_marker=marker,
        log_level="info",  # type: ignore[arg-type]
    )

    assert result is not None
    assert f"[{marker}]" in result


@given(message=log_messages, marker=marker_names)
def test_storage_marker_properties(message: str, marker: str) -> None:
    """Test storage marker properties using property-based testing.

    This test verifies that messages are stored under the correct storage markers.
    """
    logger = Logging(enable_console=False, enable_file=False)

    logger.logged_statement(
        message,
        storage_marker=marker,
        log_level="info",  # type: ignore[arg-type]
    )

    assert marker in logger.stored_messages
    assert message in next(iter(logger.stored_messages[marker]))


@given(message=log_messages, verbosity=verbosity_levels, marker=marker_names)
def test_verbosity_bypass_properties(message: str, verbosity: int, marker: str) -> None:
    """Test verbosity bypass properties using property-based testing.

    This test verifies that messages with verbosity bypass markers are logged
    regardless of verbosity settings.
    """
    logger = Logging(enable_console=False, enable_file=False)
    logger.verbosity_bypass_markers.append(marker)

    # Even with verbose disabled and high verbosity, message should appear
    result = logger.logged_statement(
        message,
        context_marker=marker,
        verbose=True,
        verbosity=verbosity,
        log_level="debug",  # type: ignore[arg-type]
    )

    assert result is not None
    assert message in result


@given(message=log_messages, verbosity=verbosity_levels)
def test_verbosity_control_properties(message: str, verbosity: int) -> None:
    """Test verbosity control properties using property-based testing.

    This test verifies that messages are suppressed or logged based on verbosity
    settings and thresholds.
    """
    logger = Logging(enable_console=False, enable_file=False)

    # First test with verbose output disabled
    result = logger.logged_statement(
        message,
        verbose=True,
        verbosity=verbosity,
        log_level="debug",  # type: ignore[arg-type]
    )
    assert result is None  # Should be suppressed

    # Then test with verbose output enabled
    logger.enable_verbose_output = True
    logger.verbosity_threshold = 3
    result = logger.logged_statement(
        message,
        verbose=True,
        verbosity=verbosity,
        log_level="debug",  # type: ignore[arg-type]
    )

    if verbosity <= logger.verbosity_threshold:
        assert result is not None
        assert message in result
    else:
        assert result is None
