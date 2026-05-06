"""Tests for the StoggerConfig class."""

import importlib
import logging
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from stogger._colors import (
    BACKRED,
    BLUE,
    BRIGHT,
    CYAN,
    DIM,
    GREEN,
    MAGENTA,
    RED,
    RESET_ALL,
    YELLOW,
)
from stogger._regexes import DEBUG_WITH_REPLACE, EVENT_WITH_REPLACE, INFO_EVENT, MSG_KEY
from stogger.config import (
    ProjectStructure,
    StoggerConfig,
    detect_project_structure,
)
from stogger.factory import build_shared_processors, configure_stdlib_logging


@pytest.fixture
def create_pyproject_toml():
    """A pytest fixture to create a temporary pyproject.toml for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir)
        pyproject_path = config_dir / "pyproject.toml"
        with open(pyproject_path, "w") as f:
            f.write("""
[tool.stogger]
verbose = true
logdir = "/tmp/logs"
syslog_identifier = "test-app"
language = "fr"
""")
        with patch("pathlib.Path.cwd", return_value=config_dir, autospec=True):
            yield


@pytest.mark.integration
def test_config_loading_from_file(create_pyproject_toml):
    """Test that config is correctly loaded from pyproject.toml."""
    config = StoggerConfig()
    assert config.verbose is True
    assert config.logdir == Path("/tmp/logs")
    assert config.syslog_identifier == "test-app"
    assert config.language == "fr"
    assert config.log_to_console is True  # Default value


@pytest.mark.integration
def test_config_kwargs_override_file(create_pyproject_toml):
    """Test that kwargs provided to the constructor override file settings."""
    config = StoggerConfig(
        verbose=False,
        syslog_identifier="override-app",
        log_to_console=False,
    )
    assert config.verbose is False
    assert config.syslog_identifier == "override-app"
    assert config.log_to_console is False
    assert config.logdir == Path("/tmp/logs")  # This should still come from the file


def test_config_defaults_when_no_file():
    """Test that the config falls back to defaults when no file exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("pathlib.Path.cwd", return_value=Path(tmpdir), autospec=True):
            config = StoggerConfig()
            assert config.verbose is False
            assert config.logdir is None
            assert config.syslog_identifier == "stogger"
            assert config.language == "en"


@patch("logging.basicConfig", autospec=True)
def test_sync_logging_setup(mock_basic_config):
    """Test that synchronous logging sets up basicConfig directly."""
    config = StoggerConfig(async_logging=False, log_to_console=True)
    processors = build_shared_processors(config)
    configure_stdlib_logging(config, processors)

    mock_basic_config.assert_called_once()
    assert "handlers" in mock_basic_config.call_args.kwargs
    assert any(isinstance(h, logging.StreamHandler) for h in mock_basic_config.call_args.kwargs["handlers"])


@patch("stogger.factory.QueueListener", autospec=True)
@patch("logging.getLogger", autospec=True)
def test_async_logging_setup(mock_get_logger, mock_listener):
    """Test that asynchronous logging sets up a QueueListener."""
    mock_root_logger = MagicMock(spec=logging.Logger(""))
    mock_get_logger.return_value = mock_root_logger

    config = StoggerConfig(async_logging=True, log_to_console=True)
    processors = build_shared_processors(config)
    configure_stdlib_logging(config, processors)

    mock_listener.assert_called_once()
    mock_listener.return_value.start.assert_called_once()
    mock_root_logger.addHandler.assert_called_once()
    assert isinstance(
        mock_root_logger.addHandler.call_args[0][0],
        logging.handlers.QueueHandler,
    )


def test_config_src_dir_defaults_when_no_file():
    """Test that the config falls back to defaults when no file exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("pathlib.Path.cwd", return_value=Path(tmpdir), autospec=True):
            config = StoggerConfig()
            assert config.src_dir == "src"  # Default source directory


@pytest.mark.integration
def test_config_src_dir_from_file():
    """Test that the source directory is correctly loaded from pyproject.toml."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir)
        pyproject_path = config_dir / "pyproject.toml"
        with open(pyproject_path, "w") as f:
            f.write("""
[tool.stogger]
src_dir = "custom_src"
""")
        with patch("pathlib.Path.cwd", return_value=config_dir, autospec=True):
            config = StoggerConfig()
            assert config.src_dir == "custom_src"


@pytest.mark.integration
def test_config_src_dir_kwargs_override():
    """Test that src_dir in kwargs overrides the file setting."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir)
        pyproject_path = config_dir / "pyproject.toml"
        with open(pyproject_path, "w") as f:
            f.write("""
[tool.stogger]
src_dir = "custom_src"
""")
        with patch("pathlib.Path.cwd", return_value=config_dir, autospec=True):
            config = StoggerConfig(src_dir="override_src")
            assert config.src_dir == "override_src"


# ---------------------------------------------------------------------------
# Quick-win module coverage tests
# ---------------------------------------------------------------------------


def test_colors_import():
    """Import color constants and verify they are strings."""
    for constant in (RESET_ALL, BRIGHT, DIM, RED, BACKRED, BLUE, CYAN, MAGENTA, YELLOW, GREEN):
        assert isinstance(constant, str)


def test_regexes_import():
    """Import compiled regex patterns and verify they exist."""
    for pattern in (EVENT_WITH_REPLACE, MSG_KEY, INFO_EVENT, DEBUG_WITH_REPLACE):
        assert hasattr(pattern, "pattern")


# ---------------------------------------------------------------------------
# ProjectStructure method tests
# ---------------------------------------------------------------------------


def test_project_structure_get_source_paths():
    """get_source_paths resolves source dirs to absolute paths."""
    ps = ProjectStructure(
        source_dirs=["src", "lib"],
        test_dirs=[],
        exclude_patterns=[],
        detection_source="test",
        project_root=Path("/project"),
    )
    paths = ps.get_source_paths()
    assert paths == [Path("/project/src"), Path("/project/lib")]


def test_project_structure_get_test_paths():
    """get_test_paths resolves test dirs to absolute paths."""
    ps = ProjectStructure(
        source_dirs=[],
        test_dirs=["tests", "test"],
        exclude_patterns=[],
        detection_source="test",
        project_root=Path("/project"),
    )
    paths = ps.get_test_paths()
    assert paths == [Path("/project/tests"), Path("/project/test")]


def test_should_exclude_test_dir_file():
    """Files inside test directories are excluded."""
    ps = ProjectStructure(
        source_dirs=["src"],
        test_dirs=["tests"],
        exclude_patterns=[],
        detection_source="test",
        project_root=Path("/project"),
    )
    assert ps.should_exclude_from_logging_analysis(Path("/project/tests/test_foo.py")) is True


def test_should_exclude_pattern_match():
    """Files matching exclude patterns are excluded."""
    ps = ProjectStructure(
        source_dirs=["src"],
        test_dirs=[],
        exclude_patterns=["*.pyc"],
        detection_source="test",
        project_root=Path("/project"),
    )
    assert ps.should_exclude_from_logging_analysis(Path("/project/foo.pyc")) is True


def test_should_exclude_outside_root():
    """Files outside project root are excluded."""
    ps = ProjectStructure(
        source_dirs=["src"],
        test_dirs=[],
        exclude_patterns=[],
        detection_source="test",
        project_root=Path("/project"),
    )
    assert ps.should_exclude_from_logging_analysis(Path("/other/foo.py")) is True


def test_should_not_exclude_normal_file():
    """Normal source files are not excluded."""
    ps = ProjectStructure(
        source_dirs=["src"],
        test_dirs=["tests"],
        exclude_patterns=["*.pyc"],
        detection_source="test",
        project_root=Path("/project"),
    )
    assert ps.should_exclude_from_logging_analysis(Path("/project/src/main.py")) is False


# ---------------------------------------------------------------------------
# StoggerConfig error path
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_load_config_invalid_toml(log):
    """Invalid TOML in pyproject.toml causes _load_config to return {} — defaults used."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir)
        pyproject_path = config_dir / "pyproject.toml"
        pyproject_path.write_text("this is not valid toml {{{{")
        with patch("pathlib.Path.cwd", return_value=config_dir, autospec=True):
            config = StoggerConfig()
            assert config.verbose is False
            assert config.syslog_identifier == "stogger"

        log.has("config-loading-failed")

# ---------------------------------------------------------------------------
# Detection subsystem tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_detect_from_stogger_section(log):
    """detect_project_structure with [tool.stogger] src_dir returns pyproject.toml source."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "src").mkdir()
        (root / "src" / "pkg").mkdir()
        (root / "src" / "pkg" / "__init__.py").touch()
        (root / "tests").mkdir()
        (root / "pyproject.toml").write_text('[tool.stogger]\nsrc_dir = "src"\n')
        result = detect_project_structure(root)
        assert result.detection_source == "pyproject.toml"
        assert "src" in result.source_dirs
        assert "tests" in result.test_dirs

        log.has("project-structure-detected-from-pyproject")

@pytest.mark.integration
def test_detect_from_hatch_section():
    """detect_project_structure with [tool.hatch] packages returns pyproject.toml source."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "src").mkdir()
        (root / "src" / "pkg").mkdir()
        (root / "src" / "pkg" / "__init__.py").touch()
        (root / "tests").mkdir()
        (root / "pyproject.toml").write_text('[tool.hatch.build.targets.wheel]\npackages = ["src/pkg"]\n')
        result = detect_project_structure(root)
        assert result.detection_source == "pyproject.toml"
        assert "src" in result.source_dirs


@pytest.mark.integration
def test_detect_from_pytest_section():
    """detect_project_structure with [tool.pytest.ini_options] testpaths returns structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "src").mkdir()
        (root / "src" / "pkg").mkdir()
        (root / "src" / "pkg" / "__init__.py").touch()
        (root / "tests").mkdir()
        (root / "pyproject.toml").write_text('[tool.pytest.ini_options]\ntestpaths = ["tests"]\n')
        result = detect_project_structure(root)
        assert result.detection_source == "pyproject.toml"
        assert "tests" in result.test_dirs


@pytest.mark.integration
def test_detect_fallback_to_heuristics(log):
    """No pyproject.toml, but src/ and tests/ exist → heuristics detection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "src").mkdir()
        (root / "src" / "pkg").mkdir()
        (root / "src" / "pkg" / "__init__.py").touch()
        (root / "tests").mkdir()
        result = detect_project_structure(root)
        assert result.detection_source == "heuristics"
        assert "src" in result.source_dirs
        assert "tests" in result.test_dirs

        log.has("project-structure-detected-from-heuristics")

@pytest.mark.integration
def test_detect_heuristics_no_src():
    """No src/ dir, but .py files in root → source_dirs=['.'] via heuristics."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "my_module.py").touch()
        result = detect_project_structure(root)
        assert result.detection_source == "heuristics"
        assert "." in result.source_dirs


@pytest.mark.integration
def test_detect_heuristics_nothing_found(log):
    """No pyproject.toml, no src, no python files → raises ValueError."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        with pytest.raises(ValueError, match="Could not determine project structure"):
            detect_project_structure(root)

        log.has("heuristic-detection-failed")

@pytest.mark.integration
def test_detect_pyproject_invalid_toml():
    """Invalid TOML in pyproject.toml falls back to heuristics."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "src").mkdir()
        (root / "src" / "pkg").mkdir()
        (root / "src" / "pkg" / "__init__.py").touch()
        (root / "pyproject.toml").write_text("this is not valid toml {{{{")
        result = detect_project_structure(root)
        assert result.detection_source == "heuristics"


@pytest.mark.integration
def test_detect_no_stogger_section():
    """Valid pyproject.toml but no [tool.stogger/hatch/pytest] → falls back to heuristics."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "src").mkdir()
        (root / "src" / "pkg").mkdir()
        (root / "src" / "pkg" / "__init__.py").touch()
        (root / "pyproject.toml").write_text('[project]\nname = "myproject"\n')
        result = detect_project_structure(root)
        assert result.detection_source == "heuristics"


def test_colors_tty_branch():
    """Reload _colors with mocked isatty to cover the colorama branch."""
    import stogger._colors as colors_mod

    with patch.object(__import__("sys").stdout, "isatty", return_value=True):
        importlib.reload(colors_mod)
        assert isinstance(colors_mod.RESET_ALL, str)
        assert len(colors_mod.RESET_ALL) > 0  # colorama ANSI codes are non-empty
        assert isinstance(colors_mod.RED, str)
        assert len(colors_mod.RED) > 0

    # Restore original module state (isatty=False in test env → empty strings)
    importlib.reload(colors_mod)


def test_detect_with_project_root_none():
    """detect_project_structure(project_root=None) uses Path.cwd()."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "src").mkdir()
        (root / "src" / "pkg").mkdir()
        (root / "src" / "pkg" / "__init__.py").touch()
        with patch("pathlib.Path.cwd", return_value=root, autospec=True):
            result = detect_project_structure(None)
            assert result.detection_source == "heuristics"
            assert "src" in result.source_dirs


@pytest.mark.integration
def test_detect_stogger_with_exclude_patterns():
    """[tool.stogger] exclude patterns starting with 'tests' populate test_dirs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "src").mkdir()
        (root / "src" / "pkg").mkdir()
        (root / "src" / "pkg" / "__init__.py").touch()
        (root / "tests").mkdir()
        (root / "pyproject.toml").write_text('[tool.stogger]\nsrc_dir = "src"\nexclude = ["tests/**", "docs/**"]\n')
        result = detect_project_structure(root)
        assert result.detection_source == "pyproject.toml"
        assert "tests" in result.test_dirs
        assert "tests/**" in result.exclude_patterns
        assert "docs/**" in result.exclude_patterns


def test_probe_hatch_no_packages():
    """Hatch config with empty packages list returns None."""
    from stogger.config import _probe_hatch_section

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        result = _probe_hatch_section({"build": {"targets": {"wheel": {"packages": []}}}}, root)
        assert result is None


def test_probe_pytest_no_testpaths():
    """Pytest config with no testpaths returns None."""
    from stogger.config import _probe_pytest_section

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        result = _probe_pytest_section({"ini_options": {}}, root)
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__])
