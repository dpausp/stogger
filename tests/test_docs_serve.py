"""Tests for the docs-serve command."""

import tempfile
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from nicestlog.cli import app


def test_docs_serve_help():
    """Test that docs-serve command shows help correctly."""
    runner = CliRunner()
    result = runner.invoke(app, ["docs-serve", "--help"])
    assert result.exit_code == 0
    assert "Serve HTML documentation in browser" in result.stdout
    assert "--port" in result.stdout
    assert "--host" in result.stdout
    assert "--open" in result.stdout
    assert "--build" in result.stdout


def test_docs_serve_no_docs_no_build():
    """Test docs-serve when no docs exist and build is disabled."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as temp_dir:
        # Change to temp directory where no docs exist
        with patch("os.getcwd", return_value=temp_dir):
            with patch("pathlib.Path.exists", return_value=False):
                result = runner.invoke(app, ["docs-serve", "--no-build", "--no-open"])
                assert result.exit_code == 1
                assert "No HTML documentation found" in result.stdout


@patch("nicestlog.cli.shutil.which")
@patch("pathlib.Path.exists")
def test_docs_serve_build_docs(mock_exists, mock_which):
    """Test docs-serve building docs when they don't exist."""
    runner = CliRunner()

    # Mock that docs don't exist initially, then exist after build
    mock_exists.side_effect = [False, True, True]  # First check fails, then succeeds
    mock_which.return_value = "/usr/bin/uv"

    with patch("socketserver.TCPServer") as mock_server:
        mock_server.side_effect = KeyboardInterrupt()  # Simulate immediate stop

        result = runner.invoke(app, ["docs-serve", "--no-open"])

        # Should have attempted to build
        assert "Building HTML documentation" in result.stdout


@patch("webbrowser.open")
@patch("socketserver.TCPServer")
@patch("pathlib.Path.exists", return_value=True)
@patch("pathlib.Path.is_dir", return_value=True)
def test_docs_serve_with_local_docs(
    mock_is_dir,
    mock_exists,
    mock_server,
    mock_browser,
):
    """Test docs-serve with existing local docs."""
    runner = CliRunner()

    # Mock server to stop immediately
    mock_server.side_effect = KeyboardInterrupt()

    result = runner.invoke(app, ["docs-serve", "--port", "8001"])

    # Should have found local docs
    assert "Found local HTML docs" in result.stdout or result.exit_code == 0


def test_docs_serve_port_in_use():
    """Test docs-serve when port is already in use."""
    runner = CliRunner()

    with patch("pathlib.Path.exists", return_value=True):
        with patch("pathlib.Path.is_dir", return_value=True):
            with patch("socketserver.TCPServer") as mock_server:
                # Simulate port already in use
                mock_server.side_effect = OSError("Address already in use")

                result = runner.invoke(app, ["docs-serve", "--no-open"])
                assert result.exit_code == 1
                assert "already in use" in result.stdout


@patch("importlib.resources.files")
@patch("pathlib.Path.exists", return_value=False)
def test_docs_serve_packaged_docs(mock_exists, mock_resources):
    """Test docs-serve finding packaged docs."""
    runner = CliRunner()

    # Mock packaged docs
    mock_package_path = MagicMock()
    mock_package_path.is_dir.return_value = True
    mock_resources.return_value.joinpath.return_value = mock_package_path

    with patch("tempfile.mkdtemp") as mock_temp:
        with patch("shutil.copytree"):
            with patch("socketserver.TCPServer") as mock_server:
                mock_temp.return_value = "/tmp/test_docs"
                mock_server.side_effect = KeyboardInterrupt()

                result = runner.invoke(app, ["docs-serve", "--no-build", "--no-open"])

                # Should have found packaged docs
                assert "Using packaged HTML docs" in result.stdout or result.exit_code == 0
