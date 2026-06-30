"""Architecture enforcement rules for stogger package.

Validates the layer boundary rules of the dependency graph:

    config.py ← (no internal deps)
    _types.py ← (no internal deps)
    _colors.py ← (no internal deps)
    processors.py ← config.py
    core.py ← config.py, _types.py, processors.py, _colors.py
    factory.py ← config.py, core.py, processors.py
    __init__.py ← config.py, core.py (top-level aggregation)

Also validates legacy-elimination invariants migrated from impl_spec tests.
"""

import ast
from pathlib import Path

import pytest
from pytest_archon import archrule

PACKAGE = "stogger"
REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = REPO_ROOT / "src" / "stogger"


# --- Layer 0: Foundation modules (no internal deps) ---


def test_config_has_no_internal_deps():
    archrule("config has no internal deps", comment="config is the deepest layer").match(
        "stogger.config"
    ).should_not_import("stogger").check(PACKAGE)


def test_types_has_no_internal_deps():
    archrule("_types has no internal deps").match("stogger._types").should_not_import("stogger").check(PACKAGE)


def test_colors_has_no_internal_deps():
    archrule("_colors has no internal deps").match("stogger._colors").should_not_import("stogger").check(PACKAGE)


# --- Layer 1: processors (depends only on config) ---


def test_processors_depends_only_on_config():
    archrule("processors depends only on config").match("stogger.processors").should_not_import(
        "stogger.core", "stogger.factory", "stogger._types", "stogger._colors"
    ).check(PACKAGE)


# --- Layer 2: core (depends on config, _types, processors, _colors — NOT factory) ---


def test_core_does_not_import_factory():
    archrule("core does not import factory").match("stogger.core").should_not_import("stogger.factory").check(PACKAGE)


def test_core_does_not_import_init():
    archrule("core does not import __init__").match("stogger.core").should_not_import("stogger").check(PACKAGE)


# --- Layer 3: factory (depends on config, core, processors — NOT __init__) ---


def test_factory_does_not_import_init():
    archrule("factory does not import __init__").match("stogger.factory").should_not_import("stogger").check(PACKAGE)


# --- Top level: __init__ (aggregation only, does not import factory internals) ---


def test_init_does_not_import_processors():
    archrule("__init__ does not directly import processors").match("stogger").exclude("stogger.*").should_not_import(
        "stogger.processors"
    ).check(PACKAGE, only_direct_imports=True)


# --- Layer 2: decorators (depends on _types, config — NOT factory or __init__) ---


def test_decorators_does_not_import_factory():
    archrule("decorators does not import factory").match("stogger.decorators").should_not_import(
        "stogger.factory"
    ).check(PACKAGE)


def test_decorators_does_not_import_init():
    archrule("decorators does not import __init__").match("stogger.decorators").should_not_import("stogger").check(
        PACKAGE
    )


# ---------------------------------------------------------------------------
# Legacy-elimination invariants (migrated from impl_spec)
# ---------------------------------------------------------------------------


class TestLegacyEliminationInvariants:
    """Structural invariants that legacy code patterns have been removed."""

    def test_journal_logger_factory_not_in_core(self) -> None:
        """JournalLoggerFactory class must not exist in core.py source."""
        source = (SRC_ROOT / "core.py").read_text()
        tree = ast.parse(source)
        class_names = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        assert "JournalLoggerFactory" not in class_names

    def test_no_dead_fields_show_logger_brackets(self) -> None:
        """ConsoleFileRenderer.__init__ must NOT set self.show_logger_brackets."""
        source = (SRC_ROOT / "core.py").read_text()
        assert "self.show_logger_brackets" not in source

    def test_no_dead_fields_show_pid(self) -> None:
        """ConsoleFileRenderer.__init__ must NOT set self.show_pid."""
        source = (SRC_ROOT / "core.py").read_text()
        assert "self.show_pid" not in source

    def test_no_bare_isatty_call(self) -> None:
        """No bare sys.stdout.isatty() call with discarded result in ConsoleFileRenderer."""
        source = (SRC_ROOT / "core.py").read_text()
        tree = ast.parse(source)
        console_renderer_found = False
        bare_isatty_found = False

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "ConsoleFileRenderer":
                console_renderer_found = True
                for item in ast.walk(node):
                    if isinstance(item, ast.Expr) and isinstance(item.value, ast.Call):
                        func = item.value.func
                        if isinstance(func, ast.Attribute) and func.attr == "isatty":
                            bare_isatty_found = True

        assert console_renderer_found, "ConsoleFileRenderer class not found"
        assert not bare_isatty_found, "Bare sys.stdout.isatty() call found in ConsoleFileRenderer"

    def test_init_early_logging_no_bare_except(self) -> None:
        """init_early_logging must not have 'except Exception' broad catch."""
        source = (SRC_ROOT / "core.py").read_text()
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "init_early_logging":
                for child in ast.walk(node):
                    if (
                        isinstance(child, ast.ExceptHandler)
                        and child.type is not None
                        and isinstance(child.type, ast.Name)
                        and child.type.id == "Exception"
                    ):
                        pytest.fail("init_early_logging has broad 'except Exception'")
                break
        else:
            pytest.fail("init_early_logging function not found")

    def test_multi_renderer_reraises(self) -> None:
        """MultiRenderer.__call__ must re-raise or wrap exceptions, not silently catch."""
        source = (SRC_ROOT / "core.py").read_text()
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "MultiRenderer":
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == "__call__":
                        for child in ast.walk(item):
                            if isinstance(child, ast.Try):
                                for handler in child.handlers:
                                    has_reraise = any(
                                        isinstance(stmt, ast.Raise)
                                        for stmt in ast.walk(ast.Module(body=handler.body, type_ignores=[]))
                                    )
                                    if not has_reraise:
                                        pytest.fail(
                                            "MultiRenderer.__call__ silently catches exceptions without re-raising"
                                        )
                break
        else:
            pytest.fail("MultiRenderer class not found")

    def test_no_bare_output_in_skip_list(self) -> None:
        """KEYS_TO_SKIP_IN_JOURNAL_MESSAGE must not contain bare 'output'."""
        source = (SRC_ROOT / "core.py").read_text()
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if (
                        isinstance(target, ast.Name)
                        and target.id == "KEYS_TO_SKIP_IN_JOURNAL_MESSAGE"
                        and isinstance(node.value, ast.List)
                    ):
                        elements = [elt.value for elt in node.value.elts if isinstance(elt, ast.Constant)]
                        assert "output" not in elements, "Bare 'output' found in KEYS_TO_SKIP_IN_JOURNAL_MESSAGE"

    def test_log_to_stdlib_removed(self) -> None:
        """log_to_stdlib function must not exist in core.py."""
        source = (SRC_ROOT / "core.py").read_text()
        tree = ast.parse(source)
        func_names = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        assert "log_to_stdlib" not in func_names

    def test_no_bumpversion_in_pyproject(self) -> None:
        """pyproject.toml must have no [tool.bumpversion] section."""
        source = (REPO_ROOT / "pyproject.toml").read_text()
        assert "[tool.bumpversion]" not in source

    def test_release_script_no_stale_projects(self) -> None:
        """scripts/release.py PROJECTS dict must not contain stogger-systemd or pytest-stogger."""
        source = (REPO_ROOT / "scripts" / "release.py").read_text()
        assert "stogger-systemd" not in source
        assert "pytest-stogger" not in source

    def test_conventions_no_mypy_reference(self) -> None:
        """CONVENTIONS.md must not mention 'mypy'."""
        source = (REPO_ROOT / "CONVENTIONS.md").read_text()
        assert "mypy" not in source

    def test_type_checking_guide_correct_import(self) -> None:
        """docs/dev/type_checking_guide.md must use 'stogger.systemd' not 'stogger_systemd'."""
        source = (REPO_ROOT / "docs" / "dev" / "type_checking_guide.md").read_text()
        assert "stogger_systemd" not in source

    def test_pyproject_no_commented_infrastructure_files(self) -> None:
        """pyproject.toml must have no commented-out infrastructure_files line."""
        source = (REPO_ROOT / "pyproject.toml").read_text()
        for line in source.splitlines():
            stripped = line.strip()
            if "infrastructure_files" in stripped and stripped.startswith("#"):
                pytest.fail(f"Commented-out infrastructure_files found: {line}")

    def test_colors_no_colorama_fallback(self) -> None:
        """_colors.py must import colorama directly with no conditional check."""
        source = (SRC_ROOT / "_colors.py").read_text()
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                test_str = ast.dump(node.test)
                if "colorama" in test_str:
                    pytest.fail("_colors.py has conditional colorama check")

    def test_systemd_import_is_direct(self) -> None:
        """core.py must import from stogger.systemd directly, no try/except ImportError."""
        source = (SRC_ROOT / "core.py").read_text()
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                for handler in node.handlers:
                    catches_import_error = (
                        isinstance(handler.type, ast.Name) and handler.type.id == "ImportError"
                    ) or (
                        isinstance(handler.type, ast.Tuple)
                        and any(isinstance(elt, ast.Name) and elt.id == "ImportError" for elt in handler.type.elts)
                    )
                    if catches_import_error:
                        try_body_source = ast.get_source_segment(source, node)
                        if try_body_source and "stogger.systemd" in try_body_source:
                            pytest.fail("stogger.systemd import wrapped in try/except ImportError")
