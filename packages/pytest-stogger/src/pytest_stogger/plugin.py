"""pytest plugin: automatic AST-based logging convention checking.

Zero-config: install and run ``pytest`` — all rules execute automatically
against every ``.py`` file under ``src/``.

Optional configuration in ``pyproject.toml``:

    [tool.pytest-stogger]
    source = "src/mypackage"    # default: "src"
    test_dir = "tests"          # default: "tests"
    exclude = ["vendor"]
    disable_rules = []
    info_allowed_layers = []    # empty = layer rule skipped
    exempt_event_ids = []
    infrastructure_files = []
"""

from __future__ import annotations

import ast
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from .files import walk_python_files
from .report import format_violations
from .rules import (
    check_bind_for_repeating,
    check_complexity_needs_log,
    check_context_required,
    check_debug_no_replace_msg,
    check_except_must_log,
    check_exception_no_dupe,
    check_info_layer,
    check_info_requires_replace_msg,
    check_kebab_case,
    check_logging_coverage,
    check_no_fstring,
    check_no_info_in_except,
    check_private_no_info,
)


class StoggerViolationError(Exception):
    """Raised when stogger finds convention violations."""


# ---------------------------------------------------------------------------
# Rule registry
# ---------------------------------------------------------------------------


@dataclass(slots=True, frozen=True)
class _RuleSpec:
    name: str
    fn: Any
    needs_exclude_files: bool = False
    needs_info_layer: bool = False


_FILE_RULES: list[_RuleSpec] = [
    _RuleSpec("log-kebab-case-event-id", check_kebab_case),
    _RuleSpec("log-context-required", check_context_required),
    _RuleSpec("log-no-fstring", check_no_fstring),
    _RuleSpec("log-requires-replace-msg", check_info_requires_replace_msg),
    _RuleSpec("log-debug-no-replace-msg", check_debug_no_replace_msg),
    _RuleSpec("log-exception-no-error-keyword", check_exception_no_dupe),
    _RuleSpec("no-log-info-in-except", check_no_info_in_except),
    _RuleSpec("except-must-log", check_except_must_log, needs_exclude_files=True),
    _RuleSpec("log-use-bind-for-repeating-keys", check_bind_for_repeating),
    _RuleSpec("private-no-log-info", check_private_no_info),
    _RuleSpec("complexity-needs-log", check_complexity_needs_log, needs_exclude_files=True),
    _RuleSpec("log-info-layer-restriction", check_info_layer, needs_info_layer=True),
]


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

_CFG_KEY = pytest.StashKey[dict[str, Any]]()


def _load_config(pyproject_path: Path) -> dict[str, Any]:
    """Load ``[tool.pytest-stogger]`` from *pyproject_path*."""
    if not pyproject_path.is_file():
        return {}
    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)
    return data.get("tool", {}).get("pytest-stogger", {})


def _get_config(config: pytest.Config) -> dict[str, Any]:
    """Cached config — parses pyproject.toml once per session."""
    try:
        return config.stash[_CFG_KEY]
    except KeyError:
        cfg = _load_config(config.rootpath / "pyproject.toml")
        config.stash[_CFG_KEY] = cfg
        return cfg


def _source_dir(config: pytest.Config) -> Path:
    cli = config.getoption("--stogger-source")
    if cli:
        return config.rootpath / cli
    return config.rootpath / _get_config(config).get("source", "src")


def _exclude_dirs(config: pytest.Config) -> frozenset[str]:
    cli = config.getoption("--stogger-exclude")
    if cli:
        return frozenset(cli)
    return frozenset(_get_config(config).get("exclude", []))


def _active_rules(config: pytest.Config) -> list[_RuleSpec]:
    cfg = _get_config(config)
    disabled = frozenset(cfg.get("disable_rules", []))
    layers = frozenset(cfg.get("info_allowed_layers", []))
    return [
        s
        for s in _FILE_RULES
        if s.name not in disabled and (not s.needs_info_layer or layers)
    ]


def _rule_kwargs(spec: _RuleSpec, config: pytest.Config) -> dict[str, Any]:
    cfg = _get_config(config)
    kw: dict[str, Any] = {}
    if spec.needs_exclude_files:
        kw["exclude_files"] = frozenset(cfg.get("infrastructure_files", []))
    if spec.needs_info_layer:
        kw["allowed_layers"] = frozenset(cfg.get("info_allowed_layers", []))
        kw["source_root"] = _source_dir(config)
    return kw


# ---------------------------------------------------------------------------
# pytest hooks
# ---------------------------------------------------------------------------


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("stogger", "Stogger AST convention checking")
    group.addoption(
        "--stogger-source",
        help="Source directory (overrides pyproject.toml).",
    )
    group.addoption(
        "--stogger-exclude",
        nargs="*",
        help="Directory names to exclude from scanning.",
    )


def pytest_collection_modifyitems(
    session: pytest.Session,
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    """Auto-register stogger convention checks: one per source file + coverage."""
    source = _source_dir(config)
    if not source.exists():
        return

    exclude = _exclude_dirs(config)
    src_files = list(walk_python_files(source, exclude=exclude))
    if not src_files:
        return

    for path, tree in src_files:
        rel = path.relative_to(config.rootpath)
        item = StoggerItem.from_parent(
            session,
            name=str(rel),
            path=path,
            tree=tree,
        )
        item._nodeid = f"{rel}::stogger"
        items.append(item)

    cfg = _get_config(config)
    disabled = frozenset(cfg.get("disable_rules", []))

    if "logging-coverage" not in disabled:
        test_dir = config.rootpath / cfg.get("test_dir", "tests")
        if test_dir.exists():
            tst_files = list(walk_python_files(test_dir))
            cov = _CoverageItem.from_parent(
                session,
                name="logging-coverage",
                path=config.rootpath,
                source_files=src_files,
                test_files=tst_files,
                exempt_event_ids=frozenset(cfg.get("exempt_event_ids", [])),
            )
            cov._nodeid = "stogger::logging-coverage"
            items.append(cov)


# ---------------------------------------------------------------------------
# Collection classes
# ---------------------------------------------------------------------------


class StoggerItem(pytest.Item):
    def __init__(self, name: str, parent: pytest.Session, *, tree: ast.Module, **kw: Any) -> None:
        super().__init__(name, parent, **kw)
        self._tree = tree
        self.add_marker(pytest.mark.stogger)

    def runtest(self) -> None:
        single = [(self.path, self._tree)]
        violations: dict[str, list[str]] = {}
        for spec in _active_rules(self.config):
            kw: dict[str, Any] = {"source_files": single}
            kw.update(_rule_kwargs(spec, self.config))
            violations.update(spec.fn(**kw))
        if violations:
            raise StoggerViolationError(format_violations(violations))

    def repr_failure(self, excinfo: pytest.ExceptionInfo[BaseException]) -> str:
        if isinstance(excinfo.value, StoggerViolationError):
            return str(excinfo.value)
        return super().repr_failure(excinfo)  # type: ignore[return-value]

    def reportinfo(self) -> tuple[Path, int, str]:
        return self.path, 0, "[stogger]"


class _CoverageItem(pytest.Item):
    def __init__(
        self,
        name: str,
        parent: pytest.Session,
        *,
        source_files: list[tuple[Path, ast.Module]],
        test_files: list[tuple[Path, ast.Module]],
        exempt_event_ids: frozenset[str],
        **kw: Any,
    ) -> None:
        super().__init__(name, parent, **kw)
        self.add_marker(pytest.mark.stogger)
        self._source_files = source_files
        self._test_files = test_files
        self._exempt = exempt_event_ids

    def runtest(self) -> None:
        violations = check_logging_coverage(
            self._source_files,
            self._test_files,
            exempt_event_ids=self._exempt,
        )
        if violations:
            raise StoggerViolationError(format_violations(violations))

    def repr_failure(self, excinfo: pytest.ExceptionInfo[BaseException]) -> str:
        if isinstance(excinfo.value, StoggerViolationError):
            return str(excinfo.value)
        return super().repr_failure(excinfo)  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Fixtures (kept for manual / custom test usage)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def stogger_config(pytestconfig: pytest.Config) -> dict[str, Any]:
    """Raw ``[tool.pytest-stogger]`` config dict."""
    return _get_config(pytestconfig)


@pytest.fixture(scope="session")
def stogger_source(pytestconfig: pytest.Config) -> Path:
    """Resolved source directory."""
    return _source_dir(pytestconfig)


@pytest.fixture(scope="session")
def stogger_exclude(pytestconfig: pytest.Config) -> frozenset[str]:
    """Excluded directory names."""
    return _exclude_dirs(pytestconfig)


@pytest.fixture(scope="session")
def stogger_infrastructure_files(stogger_config: dict[str, Any]) -> frozenset[str]:
    """File names excluded from infrastructure-sensitive rules."""
    return frozenset(stogger_config.get("infrastructure_files", []))


@pytest.fixture(scope="session")
def stogger_test_dir(pytestconfig: pytest.Config, stogger_config: dict[str, Any]) -> Path:
    """Resolved test directory."""
    return pytestconfig.rootpath / stogger_config.get("test_dir", "tests")


@pytest.fixture(scope="session")
def source_files(
    stogger_source: Path,
    stogger_exclude: frozenset[str],
) -> list[tuple[Path, ast.Module]]:
    """All ``(path, ast.Module)`` pairs from the source directory, parsed once."""
    return list(walk_python_files(stogger_source, exclude=stogger_exclude))


@pytest.fixture(scope="session")
def test_files(stogger_test_dir: Path) -> list[tuple[Path, ast.Module]]:
    """All ``(path, ast.Module)`` pairs from the test directory, parsed once."""
    return list(walk_python_files(stogger_test_dir))
