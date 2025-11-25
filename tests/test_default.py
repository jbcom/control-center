"""Example unit tests for the template package."""

import example_package


def test_package_imports() -> None:
    """Test that the package can be imported."""
    assert example_package is not None


def test_package_has_version() -> None:
    """Test that the package has a __version__ attribute."""
    assert hasattr(example_package, "__version__")
    assert isinstance(example_package.__version__, str)


def test_version_format() -> None:
    """Test that version follows expected format."""
    version = example_package.__version__
    # Should be either "0.0.0" (default) or CalVer format "YYYY.MM.BUILD"
    parts = version.split(".")
    assert len(parts) == 3
    # All parts should be numeric
    assert all(part.isdigit() for part in parts)
