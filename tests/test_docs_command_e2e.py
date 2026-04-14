"""E2E tests for `stoggertools docs` command.

Tests the real CLI flow: argument parsing -> command execution -> output verification.
No mocks -- uses Typer's CliRunner with real file lookups.

SPEC: AGENTS.md - every command MUST have an E2E test.
"""

import pytest
from stoggertools.cli import app
from typer.testing import CliRunner

runner = CliRunner()


@pytest.mark.integration
def test_docs_no_args_exits_zero():
    result = runner.invoke(app, ["docs"])
    assert result.exit_code == 0
    assert "stogger" in result.output.lower()


@pytest.mark.integration
def test_docs_help_flag():
    result = runner.invoke(app, ["docs", "--help"])
    assert result.exit_code == 0
    assert "Show documentation" in result.output
    assert "--interactive" in result.output
    assert "--feature" in result.output


@pytest.mark.integration
def test_docs_feature_logging():
    result = runner.invoke(app, ["docs", "--feature", "logging"])
    assert result.exit_code == 0


@pytest.mark.integration
def test_docs_feature_linting():
    result = runner.invoke(app, ["docs", "--feature", "linting"])
    assert result.exit_code == 0


@pytest.mark.integration
def test_docs_feature_ast():
    result = runner.invoke(app, ["docs", "--feature", "ast"])
    assert result.exit_code == 0


@pytest.mark.integration
def test_docs_feature_nonexistent_shows_error():
    result = runner.invoke(app, ["docs", "--feature", "nonexistent"])
    assert "No documentation found" in result.output


@pytest.mark.integration
def test_docs_interactive_mode():
    result = runner.invoke(app, ["docs", "--interactive"], input="1\n")
    assert result.exit_code == 0
    assert "Interactive Documentation Browser" in result.output
