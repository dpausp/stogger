"""
Simple tests for the CLI module functionality.
"""

import pytest
from unittest.mock import patch, MagicMock

from nicestlog.cli import main, init_config


class TestInitConfig:
    """Test cases for init_config function."""

    @patch("builtins.input")
    @patch("pathlib.Path.exists")
    def test_init_config_basic_flow(self, mock_exists, mock_input):
        """Test basic init_config flow."""
        mock_exists.return_value = True
        mock_input.side_effect = [
            "n",  # verbose
            "test-app",  # syslog_identifier
            "json",  # log_format
            "n",  # async_logging
            "n",  # file logging
            "n",  # translations
            "y",  # append to file
        ]

        with patch("builtins.open", create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            init_config()

            mock_file.write.assert_called_once()
            written_content = mock_file.write.call_args[0][0]
            assert "[tool.nicestlog]" in written_content
            assert 'syslog_identifier = "test-app"' in written_content

    @patch("builtins.input")
    @patch("pathlib.Path.exists")
    def test_init_config_no_pyproject(self, mock_exists, mock_input):
        """Test init_config when pyproject.toml doesn't exist."""
        mock_exists.return_value = False

        with pytest.raises(SystemExit):
            init_config()


class TestMainFunction:
    """Test cases for main function."""

    @patch("sys.argv", ["nicestlog", "init-config"])
    @patch("nicestlog.cli.init_config")
    def test_main_init_config_subcommand(self, mock_init_config):
        """Test main function with init-config subcommand."""
        with pytest.raises(SystemExit) as exc_info:
            main()
        # Typer exits with code 0 on successful command execution
        assert exc_info.value.code == 0
        mock_init_config.assert_called_once()

    def test_main_requires_subcommand(self):
        """Test that main function requires a subcommand."""
        with patch("sys.argv", ["nicestlog"]):
            with pytest.raises(SystemExit):
                main()


if __name__ == "__main__":
    pytest.main([__file__])
