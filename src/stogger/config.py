"""Configuration handling for stogger."""

import fnmatch
import sys
import time
import tomllib
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import attrs
import structlog

_TEST_DEPS_WARNED = False


@dataclass
class ProjectStructure:
    """Detected project layout used for source and test discovery.

    Attributes:
        source_dirs: Relative paths to source directories (e.g. ``["src"]``).
        test_dirs: Relative paths to test directories (e.g. ``["tests"]``).
        exclude_patterns: Glob patterns for files excluded from logging analysis.
        detection_source: How the structure was determined — ``"pyproject.toml"``,
            ``"heuristics"``, or ``"defaults"``.
        project_root: Absolute path to the project root directory.

    """

    source_dirs: list[str]
    test_dirs: list[str]
    exclude_patterns: list[str]
    detection_source: str  # "pyproject.toml", "heuristics", "defaults"
    project_root: Path

    def get_source_paths(self) -> list[Path]:
        """Resolve source directories to absolute paths.

        Returns:
            List of absolute Paths joining ``project_root`` with each
            entry in ``source_dirs``.

        """
        return [self.project_root / src_dir for src_dir in self.source_dirs]

    def get_test_paths(self) -> list[Path]:
        """Resolve test directories to absolute paths.

        Returns:
            List of absolute Paths joining ``project_root`` with each
            entry in ``test_dirs``.

        """
        return [self.project_root / test_dir for test_dir in self.test_dirs]

    def should_exclude_from_logging_analysis(self, file_path: Path) -> bool:
        """Check whether a file should be excluded from logging analysis.

        Files inside ``test_dirs`` or matching any ``exclude_patterns`` glob are
        excluded. Files outside ``project_root`` are always excluded.

        Args:
            file_path: Absolute path to the file to check.

        Returns:
            ``True`` if the file should be excluded.

        """
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
            log = structlog.get_logger(__name__)
            log.debug("file-outside-project-root", file_path=str(file_path))
            return True


def _check_test_dependencies(full_config: dict[str, Any]) -> None:
    """Warn if pytest-stogger or pytest-structlog are missing during pytest."""
    global _TEST_DEPS_WARNED

    if _TEST_DEPS_WARNED or "_pytest" not in sys.modules:
        return

    log = structlog.get_logger(__name__)
    log.debug("checking-test-dependencies", has_dependency_groups="dependency-groups" in full_config)

    _TEST_DEPS_WARNED = True

    required = {"pytest-stogger", "pytest-structlog"}
    dep_groups = full_config.get("dependency-groups", {})
    test_deps = dep_groups.get("test")

    if test_deps is None:
        msg = (
            "stogger test infrastructure incomplete: no [dependency-groups].test found in pyproject.toml. "
            "Add pytest-stogger and pytest-structlog to [dependency-groups].test."
        )
        warnings.warn(msg, UserWarning, stacklevel=2)
        return

    deps_str = " ".join(str(d).lower() for d in test_deps)
    missing = sorted(r for r in required if r not in deps_str)

    if missing:
        msg = (
            f"stogger test infrastructure incomplete: {', '.join(missing)}. "
            "Add to [dependency-groups].test in pyproject.toml."
        )
        warnings.warn(msg, UserWarning, stacklevel=2)


def _load_pyproject_config(*, verbose: bool = False) -> dict[str, Any]:
    """Load ``[tool.stogger]`` settings from ``pyproject.toml`` in cwd.

    Returns:
        Dictionary of configuration values, or an empty dict when the
        file is missing or cannot be parsed.

    """
    log = structlog.get_logger(__name__)
    pyproject_path = Path.cwd() / "pyproject.toml"
    log = log.bind(path=str(pyproject_path))

    if verbose:
        log.debug(
            "searching-for-config",
            exists=pyproject_path.is_file(),
        )

    if not pyproject_path.is_file():
        if verbose:
            log.debug("no-pyproject-found", exists=False)
        return {}
    try:
        with pyproject_path.open("rb") as f:
            config = tomllib.load(f)
        stogger_config = config.get("tool", {}).get("stogger", {})
        if "syslog_identifier" not in stogger_config:
            project_name = config.get("project", {}).get("name")
            if project_name:
                stogger_config["syslog_identifier"] = project_name
        _check_test_dependencies(config)
        if verbose:
            log.debug(
                "config-loaded-successfully",
                settings_count=len(stogger_config),
            )
    except (FileNotFoundError, tomllib.TOMLDecodeError):
        log.exception("config-loading-failed", stage="load")
        return {}
    else:
        return stogger_config


@attrs.define(slots=False)
class FormatConfig:
    """Configuration for log format settings, loaded from ``[tool.stogger.format]``.

    Attributes:
        timestamp_precision: Timestamp format — ``"iso"``, ``"iso_seconds"``,
            ``"iso_no_z"``, or ``"relative"``. Default ``"iso_seconds"``.
        min_level: Minimum log level to display. Default ``"info"``.
        show_code_info: Include file name and line number. Default ``False``.
        pad_event_width: Minimum width for the event column. Default ``30``.

    """

    timestamp_precision: str = "iso_seconds"
    min_level: str = "info"
    show_code_info: bool = False
    pad_event_width: int = 30

    def __attrs_post_init__(self) -> None:
        self._process_start: float = time.time()


@attrs.define
class StoggerConfig:
    """Central configuration for stogger, merged from ``[tool.stogger]`` in
    ``pyproject.toml`` and keyword arguments passed at construction.

    Key attributes (with defaults):

    Attributes:
        verbose (bool): Enable verbose output. Default ``False``.
        logdir (Path | None): Directory for log files. Default ``None``.
        log_cmd_output (bool): Log subprocess command output. Default ``False``.
        log_to_console (bool): Also log to the console. Default ``True``.
        syslog_identifier (str): Identifier for syslog/systemd journal.
            Default ``"stogger"``.
        show_caller_info (bool): Include caller file/line in log output.
            Default ``False``.
        translation_dir (Path | None): Directory containing message
            translations. Default ``None``.
        language (str): Language code for log messages. Default ``"en"``.
        log_format (str): Output format — ``"simple"`` or ``"json"``.
            Default ``"simple"``.
        async_logging (bool): Use asynchronous log writing. Default ``False``.
        enable_systemd (bool): Enable systemd/journal integration.
            Default ``True``.
        systemd_facility (str | None): Syslog facility for systemd output.
            Default ``None``.
        src_dir (str): Primary source directory name. Default ``"src"``.
        format (FormatConfig): Format configuration. Default ``FormatConfig()``.
        ast_respect_gitignore (bool): Honor ``.gitignore`` during AST
            analysis. Default ``True``.
        ast_max_parameters (int): Max parameters before flagging a function.
            Default ``8``.
        ast_logging_focus (bool): Focus AST analysis on logging patterns.
            Default ``True``.
        ast_enabled_patterns (list | None): Specific AST patterns to enable.
            ``None`` enables all. Default ``None``.

    """

    verbose: bool = False
    logdir: Path | None = None
    log_cmd_output: bool = False
    log_to_console: bool = True
    syslog_identifier: str = "stogger"
    show_caller_info: bool = False
    translation_dir: Path | None = None
    language: str = "en"
    log_format: str = "simple"
    async_logging: bool = False
    enable_systemd: bool = True
    systemd_facility: str | None = None
    enable_postgres: bool = False
    postgres_dsn: str | None = None
    postgres_table: str = "stogger_logs"
    src_dir: str = "src"
    format: FormatConfig = attrs.field(factory=FormatConfig)
    ast_respect_gitignore: bool = True
    ast_max_parameters: int = 8
    ast_logging_focus: bool = True
    ast_enabled_patterns: list | None = None

    def __init__(self, **kwargs: Any) -> None:
        """Initialize configuration from TOML file merged with kwargs.

        Args:
            **kwargs: Keyword arguments that override config file settings.

        """
        verbose = kwargs.get("verbose", False)
        log = structlog.get_logger(__name__)

        config = _load_pyproject_config(verbose=verbose)
        if verbose:
            log.debug("config-loaded-from-file", key_count=len(config))
        config.update(kwargs)
        if verbose:
            log.debug("config-merged-with-kwargs", kwargs_count=len(kwargs))
        # Build FormatConfig from [tool.stogger.format] section
        format_config = config.pop("format", {})
        self.__attrs_init__(  # ty: ignore[unresolved-attribute]
            verbose=config.get("verbose", False),
            logdir=Path(config["logdir"]) if config.get("logdir") else None,
            log_cmd_output=config.get("log_cmd_output", False),
            log_to_console=config.get("log_to_console", True),
            syslog_identifier=config.get("syslog_identifier", "stogger"),
            show_caller_info=config.get("show_caller_info", False),
            translation_dir=Path(config["translation_dir"]) if config.get("translation_dir") else None,
            language=config.get("language", "en"),
            log_format=config.get("log_format", "simple"),
            async_logging=config.get("async_logging", False),
            enable_systemd=config.get("enable_systemd", True),
            systemd_facility=config.get("systemd_facility", None),
            enable_postgres=config.get("enable_postgres", False),
            postgres_dsn=config.get("postgres_dsn", None),
            postgres_table=config.get("postgres_table", "stogger_logs"),
            src_dir=config.get("src_dir", "src"),
            format=FormatConfig(**format_config) if isinstance(format_config, dict) else format_config,
            ast_respect_gitignore=config.get("ast", {}).get("respect_gitignore", True),
            ast_max_parameters=config.get("ast", {}).get("max_parameters", 8),
            ast_logging_focus=config.get("ast", {}).get("logging_focus", True),
            ast_enabled_patterns=config.get("ast", {}).get("enabled_patterns", None),
        )


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
                log.info(
                    "project-structure-detected-from-pyproject",
                    path=str(pyproject_path),
                    _replace_msg="Project structure detected from {path}",
                )
                return structure
        except (OSError, ValueError, FileNotFoundError):
            log.debug("pyproject-detection-failed", path=str(pyproject_path))

    # Fall back to heuristics
    try:
        structure = _detect_from_heuristics(project_root)
        log.info(
            "project-structure-detected-from-heuristics",
            method="heuristics",
            _replace_msg="Project structure detected via heuristics",
        )
        return structure
    except (OSError, ValueError, FileNotFoundError) as e:
        log.exception("heuristic-detection-failed", project_root=str(project_root))
        msg = (
            f"Could not determine project structure for {project_root}. "
            "Please configure [tool.stogger] section in pyproject.toml with 'src_dir' and 'exclude' settings."
        )
        raise ValueError(msg) from e


def _probe_stogger_section(stogger_config: dict, project_root: Path) -> ProjectStructure | None:
    """Probe ``[tool.stogger]`` section for project structure.

    Args:
        stogger_config: Parsed ``[tool.stogger]`` dictionary.
        project_root: Absolute path to the project root.

    Returns:
        ProjectStructure if the section is present, else None.

    """
    log = structlog.get_logger(__name__)

    if not stogger_config:
        log.debug("no-stogger-section", has_section=False)
        return None
    log.debug("probing-stogger-section", src_dir=stogger_config.get("src_dir", "src"))

    src_dir = stogger_config.get("src_dir", "src")
    exclude_patterns = stogger_config.get("exclude", [])

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


def _probe_hatch_section(hatch_config: dict, project_root: Path) -> ProjectStructure | None:
    """Probe ``[tool.hatch]`` section for project structure.

    Args:
        hatch_config: Parsed ``[tool.hatch]`` dictionary.
        project_root: Absolute path to the project root.

    Returns:
        ProjectStructure if a Hatch wheel package source is found, else None.

    """
    log = structlog.get_logger(__name__)

    if not hatch_config:
        log.debug("no-hatch-section", has_section=False)
        return None
    log.debug("probing-hatch-section", has_build="build" in hatch_config)

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

    return None


def _probe_pytest_section(pytest_config: dict, project_root: Path) -> ProjectStructure | None:
    """Probe ``[tool.pytest]`` section for project structure.

    Args:
        pytest_config: Parsed ``[tool.pytest]`` dictionary.
        project_root: Absolute path to the project root.

    Returns:
        ProjectStructure if pytest testpaths are found, else None.

    """
    log = structlog.get_logger(__name__)

    if not pytest_config:
        log.debug("no-pytest-section", has_section=False)
        return None
    log.debug("probing-pytest-section", has_ini_options="ini_options" in pytest_config)

    testpaths = pytest_config.get("ini_options", {}).get("testpaths", [])
    if testpaths:
        test_dirs = [path for path in testpaths if (project_root / path).exists()]
        return _create_default_structure_with_tests(
            project_root,
            test_dirs,
            "pyproject.toml",
        )

    return None


def _detect_from_pyproject(
    project_root: Path,
    pyproject_path: Path,
) -> ProjectStructure | None:
    """Detect project structure from pyproject.toml configuration."""
    log = structlog.get_logger(__name__)
    log.debug("detecting-project-from-pyproject", path=str(pyproject_path))
    with pyproject_path.open("rb") as f:
        config = tomllib.load(f)

    tool_config = config.get("tool", {})

    result = _probe_stogger_section(tool_config.get("stogger", {}), project_root)
    if result:
        return result

    result = _probe_hatch_section(tool_config.get("hatch", {}), project_root)
    if result:
        return result

    result = _probe_pytest_section(tool_config.get("pytest", {}), project_root)
    if result:
        return result

    return None


def _detect_from_heuristics(project_root: Path) -> ProjectStructure:
    """Detect project structure using common Python project patterns."""
    log = structlog.get_logger(__name__)
    log.debug("detecting-project-from-heuristics", root=str(project_root))
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
        if py_files and not all(f.name in {"setup.py", "conftest.py"} for f in py_files):
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
    log = structlog.get_logger(__name__)
    log.debug("creating-default-structure-with-tests", test_dirs=test_dirs)
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
