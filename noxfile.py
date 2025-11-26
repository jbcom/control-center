"""Nox configuration for jbcom control center."""

import nox

PACKAGES = [
    "extended-data-types",
    "lifecyclelogging",
    "directed-inputs-class",
    "vendor-connectors",
]

PYTHON_VERSIONS = ["3.9", "3.10", "3.11", "3.12", "3.13"]


@nox.session(python=PYTHON_VERSIONS)
def tests(session: nox.Session) -> None:
    """Run tests for all packages."""
    # Install all packages in editable mode
    session.install("-e", "packages/extended-data-types[tests]")
    session.install("-e", "packages/lifecyclelogging[tests]")
    session.install("-e", "packages/directed-inputs-class[tests]")
    session.install("-e", "packages/vendor-connectors[tests]")

    # Run tests for each package
    for pkg in PACKAGES:
        session.run("pytest", f"packages/{pkg}/tests", *session.posargs)


@nox.session(python="3.13")
def test_extended_data_types(session: nox.Session) -> None:
    """Run tests for extended-data-types only."""
    session.install("-e", "packages/extended-data-types[tests]")
    session.run("pytest", "packages/extended-data-types/tests", *session.posargs)


@nox.session(python="3.13")
def test_lifecyclelogging(session: nox.Session) -> None:
    """Run tests for lifecyclelogging only."""
    session.install("-e", "packages/extended-data-types")
    session.install("-e", "packages/lifecyclelogging[tests]")
    session.run("pytest", "packages/lifecyclelogging/tests", *session.posargs)


@nox.session(python="3.13")
def test_directed_inputs_class(session: nox.Session) -> None:
    """Run tests for directed-inputs-class only."""
    session.install("-e", "packages/extended-data-types")
    session.install("-e", "packages/directed-inputs-class[tests]")
    session.run("pytest", "packages/directed-inputs-class/tests", *session.posargs)


@nox.session(python="3.13")
def test_vendor_connectors(session: nox.Session) -> None:
    """Run tests for vendor-connectors only."""
    session.install("-e", "packages/extended-data-types")
    session.install("-e", "packages/lifecyclelogging")
    session.install("-e", "packages/vendor-connectors[tests]")
    session.run("pytest", "packages/vendor-connectors/tests", *session.posargs)


@nox.session(python="3.13")
def lint(session: nox.Session) -> None:
    """Run linting on all packages."""
    session.install("ruff>=0.2.0")
    session.run("ruff", "check", "packages/")
    session.run("ruff", "format", "--check", "packages/")


@nox.session(python="3.13")
def typecheck(session: nox.Session) -> None:
    """Run type checking on all packages."""
    session.install("mypy>=1.8.0")
    session.install("-e", "packages/extended-data-types[typing]")
    session.install("-e", "packages/lifecyclelogging[typing]")

    session.run("mypy", "packages/extended-data-types/src")
    session.run("mypy", "packages/lifecyclelogging/src")


@nox.session(python="3.13")
def format(session: nox.Session) -> None:
    """Format all packages."""
    session.install("ruff>=0.2.0")
    session.run("ruff", "format", "packages/")
    session.run("ruff", "check", "--fix", "packages/")
