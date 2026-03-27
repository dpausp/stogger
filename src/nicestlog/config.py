"""Configuration handling for nicestlog."""

import fnmatch
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import structlog


@dataclass
class ProjectStructure:
    """Detected project structure information."""

    source_dirs: list[str]
    test_dirs: list[str]
    exclude_patterns: list[str]
    detection_source: str  # "pyproject.toml", "heuristics", "defaults"
    project_root: Path

    def get_source_paths(self) -> list[Path]:
        """Get absolute paths for source directories."""
        return [self.project_root / src_dir for src_dir in self.source_dirs]

    def get_test_paths(self) -> list[Path]:
        """Get absolute paths for test directories."""
        return [self.project_root / test_dir for test_dir in self.test_dirs]

    def should_exclude_from_logging_analysis(self, file_path: Path) -> bool:
        """Check if a file should be excluded from logging analysis."""
        try:
            rel_path = file_path.relative_to(self.project_root)
            rel_path_str = str(rel_path)

            # Check if file is in test directories
            for test_dir in self.test_dirs:
                if rel_path_str.startswith(test_dir + "/") or rel_path_str == test_dir:
                    return True

            # Check exclude patterns
            return any(fnmatch.fnmatch(rel_path_str, pattern) for pattern in self.exclude_patterns)
        except ValueError:
            # File is outside project root
            return True


class NicestLogConfig:
    """Manages nicestlog configuration by merging pyproject.toml settings
    with keyword arguments.
    """

    def __init__(self, **kwargs: Any):
        """Initializes the configuration.

        Args:
            **kwargs: Keyword arguments that can override config file settings.

        """
        log = structlog.get_logger(__name__)

        config = self._load_config()
        log.debug("config-loaded-from-file", key_count=len(config))
        config.update(kwargs)
        log.debug("config-merged-with-kwargs", kwargs_count=len(kwargs))

        self.verbose: bool = config.get("verbose", False)
        self.logdir: Path | None = Path(config["logdir"]) if config.get("logdir") else None
        self.log_cmd_output: bool = config.get("log_cmd_output", False)
        self.log_to_console: bool = config.get("log_to_console", True)
        self.syslog_identifier: str = config.get("syslog_identifier", "nicestlog")
        self.show_caller_info: bool = config.get("show_caller_info", False)
        self.translation_dir: Path | None = Path(config["translation_dir"]) if config.get("translation_dir") else None
        self.language: str = config.get("language", "en")
        self.log_format: str = config.get("log_format", "simple")
        self.async_logging: bool = config.get("async_logging", False)
        self.enable_pii_scrubbing: bool = config.get("enable_pii_scrubbing", True)
        self.pii_redaction_text: str = config.get("pii_redaction_text", "[REDACTED]")
        self.enable_systemd: bool = config.get("enable_systemd", True)
        self.systemd_facility: str | None = config.get("systemd_facility", None)
        self.src_dir: str = config.get("src_dir", "src")

        # AST Analysis settings
        ast_config = config.get("ast", {})
        self.ast_respect_gitignore: bool = ast_config.get("respect_gitignore", True)
        self.ast_max_parameters: int = ast_config.get("max_parameters", 8)
        self.ast_logging_focus: bool = ast_config.get("logging_focus", True)
        self.ast_enabled_patterns: list | None = ast_config.get(
            "enabled_patterns",
            None,
        )

    def _load_config(self) -> dict[str, Any]:
        """Loads nicestlog config from pyproject.toml."""
        log = structlog.get_logger(__name__)

        pyproject_path = Path.cwd() / "pyproject.toml"
        log.debug(
            "searching-for-config",
            path=str(pyproject_path),
            exists=pyproject_path.is_file(),
        )

        if not pyproject_path.is_file():
            log.debug("no-pyproject-found", path=str(pyproject_path))
            return {}
        try:
            with pyproject_path.open("rb") as f:
                config = tomllib.load(f)
            nicest_config = config.get("tool", {}).get("nicestlog", {})
            log.info(
                "config-loaded-successfully",
                path=str(pyproject_path),
                settings_count=len(nicest_config),
            )
        except (tomllib.TOMLDecodeError, Exception) as e:
            log.exception("config-loading-failed", path=str(pyproject_path), error=str(e))
            return {}
        else:
            return nicest_config


def detect_project_structure(project_root: Path | None = None) -> ProjectStructure:
    """Detect project structure using smart heuristics.

    Args:
        project_root: Project root directory. If None, uses current working directory.

    Returns:
        ProjectStructure with detected information.

    Raises:
        ValueError: If project structure cannot be determined and user configuration is required.

    """
    log = structlog.get_logger(__name__)

    if project_root is None:
        project_root = Path.cwd()

    # Try to detect from pyproject.toml first
    pyproject_path = project_root / "pyproject.toml"
    if pyproject_path.exists():
        try:
            structure = _detect_from_pyproject(project_root, pyproject_path)
            if structure:
                log.info("project-structure-detected-from-pyproject", path=str(pyproject_path))
                return structure
        except (OSError, ValueError, FileNotFoundError):
            pass

    # Fall back to heuristics
    try:
        structure = _detect_from_heuristics(project_root)
        log.info("project-structure-detected-from-heuristics")
        return structure
    except (OSError, ValueError, FileNotFoundError) as e:
        log.exception("heuristic-detection-failed", error=str(e))
        msg = (
            f"Could not determine project structure for {project_root}. "
            "Please configure [tool.nicestlog] section in pyproject.toml with 'src_dir' and 'exclude' settings."
        )
        raise ValueError(msg) from e


def _detect_from_pyproject(
    project_root: Path,
    pyproject_path: Path,
) -> ProjectStructure | None:
    """Detect project structure from pyproject.toml configuration."""
    with pyproject_path.open("rb") as f:
        config = tomllib.load(f)

    # Check nicestlog configuration
    nicest_config = config.get("tool", {}).get("nicestlog", {})
    if nicest_config:
        src_dir = nicest_config.get("src_dir", "src")
        exclude_patterns = nicest_config.get("exclude", [])

        # Detect source directories
        source_dirs = [src_dir] if (project_root / src_dir).exists() else []

        # Detect test directories from exclude patterns and common locations
        test_dirs = []
        for pattern in exclude_patterns:
            if pattern.startswith("tests"):
                test_dir = pattern.split("/")[0]
                if (project_root / test_dir).exists():
                    test_dirs.append(test_dir)

        # Add common test directories if they exist
        for test_dir in ["tests", "test"]:
            if (project_root / test_dir).exists() and test_dir not in test_dirs:
                test_dirs.append(test_dir)

        # Default exclude patterns
        default_excludes = [
            "docs/**",
            "examples/**",
            ".venv/**",
            "venv/**",
            "build/**",
            "dist/**",
            "*.egg-info/**",
            "__pycache__/**",
            ".git/**",
        ]

        # Merge configured excludes with defaults
        all_excludes = list(set(exclude_patterns + default_excludes))

        return ProjectStructure(
            source_dirs=source_dirs,
            test_dirs=test_dirs,
            exclude_patterns=all_excludes,
            detection_source="pyproject.toml",
            project_root=project_root,
        )

    # Check hatch configuration for source directory
    hatch_config = config.get("tool", {}).get("hatch", {})
    if hatch_config:
        build_config = hatch_config.get("build", {})
        wheel_config = build_config.get("targets", {}).get("wheel", {})
        packages = wheel_config.get("packages", [])

        if packages:
            # Extract source directory from packages
            for package in packages:
                if "/" in package:
                    src_dir = package.split("/")[0]
                    if (project_root / src_dir).exists():
                        return _create_default_structure_with_src(
                            project_root,
                            src_dir,
                            "pyproject.toml",
                        )

    # Check pytest configuration for test directories
    pytest_config = config.get("tool", {}).get("pytest", {})
    if pytest_config:
        testpaths = pytest_config.get("ini_options", {}).get("testpaths", [])
        if testpaths:
            test_dirs = [path for path in testpaths if (project_root / path).exists()]
            return _create_default_structure_with_tests(
                project_root,
                test_dirs,
                "pyproject.toml",
            )

    return None


def _detect_from_heuristics(project_root: Path) -> ProjectStructure:
    """Detect project structure using common Python project patterns."""
    source_dirs = []
    test_dirs = []

    # Common source directory patterns
    for src_candidate in ["src", "lib", project_root.name]:
        src_path = project_root / src_candidate
        if src_path.exists() and src_path.is_dir() and any(src_path.rglob("*.py")):
            source_dirs.append(src_candidate)
            break

    # If no src directory found, assume root is source
    if not source_dirs:
        # Check if root contains Python files (but not just setup.py)
        py_files = list(project_root.glob("*.py"))
        if py_files and not all(f.name in ["setup.py", "conftest.py"] for f in py_files):
            source_dirs.append(".")

    # Common test directory patterns
    for test_candidate in ["tests", "test", "testing"]:
        test_path = project_root / test_candidate
        if test_path.exists() and test_path.is_dir():
            test_dirs.append(test_candidate)

    # Default exclude patterns for heuristic detection
    exclude_patterns = [
        "docs/**",
        "examples/**",
        "demo/**",
        "demos/**",
        ".venv/**",
        "venv/**",
        "env/**",
        ".env/**",
        "build/**",
        "dist/**",
        "*.egg-info/**",
        "__pycache__/**",
        ".git/**",
        ".svn/**",
        ".hg/**",
        "node_modules/**",
        ".tox/**",
        ".pytest_cache/**",
        ".mypy_cache/**",
        ".coverage",
        "htmlcov/**",
    ]

    # Add test directories to exclude patterns
    exclude_patterns.extend(f"{test_dir}/**" for test_dir in test_dirs)

    if not source_dirs:
        msg = "No source directories detected"
        raise ValueError(msg)

    return ProjectStructure(
        source_dirs=source_dirs,
        test_dirs=test_dirs,
        exclude_patterns=exclude_patterns,
        detection_source="heuristics",
        project_root=project_root,
    )


def _create_default_structure_with_src(
    project_root: Path,
    src_dir: str,
    source: str,
) -> ProjectStructure:
    """Create default structure with specified source directory."""
    test_dirs = [test_candidate for test_candidate in ["tests", "test"] if (project_root / test_candidate).exists()]

    exclude_patterns = [
        "docs/**",
        "examples/**",
        ".venv/**",
        "venv/**",
        "build/**",
        "dist/**",
        "*.egg-info/**",
        "__pycache__/**",
        ".git/**",
    ]

    # Add test directories to exclude patterns
    exclude_patterns.extend(f"{test_dir}/**" for test_dir in test_dirs)

    return ProjectStructure(
        source_dirs=[src_dir],
        test_dirs=test_dirs,
        exclude_patterns=exclude_patterns,
        detection_source=source,
        project_root=project_root,
    )


def _create_default_structure_with_tests(
    project_root: Path,
    test_dirs: list[str],
    source: str,
) -> ProjectStructure:
    """Create default structure with specified test directories."""
    # Try to detect source directory
    source_dirs = []
    for src_candidate in ["src", "lib"]:
        if (project_root / src_candidate).exists():
            source_dirs.append(src_candidate)
            break

    if not source_dirs:
        source_dirs = ["."]

    exclude_patterns = [
        "docs/**",
        "examples/**",
        ".venv/**",
        "venv/**",
        "build/**",
        "dist/**",
        "*.egg-info/**",
        "__pycache__/**",
        ".git/**",
    ]

    # Add test directories to exclude patterns
    exclude_patterns.extend(f"{test_dir}/**" for test_dir in test_dirs)

    return ProjectStructure(
        source_dirs=source_dirs,
        test_dirs=test_dirs,
        exclude_patterns=exclude_patterns,
        detection_source=source,
        project_root=project_root,
    )


@dataclass
class SimpleFormatSettings:
    """Settings for simple console formatting.

    This class provides a way to configure the ConsoleFileRenderer with common formatting options.
    """

    min_level: str = "info"
    show_logger_brackets: bool = False
    show_pid: bool = False
    show_code_info: bool = False
    timestamp_format: str = "iso"
    pad_event_width: int = 30


# Standard settings object
_default_simple_format_settings = SimpleFormatSettings()
