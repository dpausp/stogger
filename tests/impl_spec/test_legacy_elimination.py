"""Spec validation tests for legacy-elimination impl spec.

These tests verify the contracts defined in .agents/impl_specs/legacy-elimination.md.
"""

import ast
from pathlib import Path
from typing import ClassVar

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_ROOT = REPO_ROOT / "src" / "stogger"


# --- 1. dead-code-removal ---


class TestDeadCodeRemoval:
    """SPEC: legacy-elimination::dead-code-removal — remove dead code artifacts."""

    def test_regexes_module_deleted(self) -> None:
        """_regexes.py module must not exist."""
        assert not (SRC_ROOT / "_regexes.py").exists()

    def test_journal_logger_factory_not_in_core(self) -> None:
        """JournalLoggerFactory class must not exist in core.py source."""
        source = (SRC_ROOT / "core.py").read_text()
        tree = ast.parse(source)
        class_names = [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef)
        ]
        assert "JournalLoggerFactory" not in class_names


    def test_journal_logger_factory_not_exported(self) -> None:
        """From stogger import JournalLoggerFactory must raise ImportError."""
        import stogger
        assert not hasattr(stogger, "JournalLoggerFactory")

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
                        if (
                            isinstance(func, ast.Attribute)
                            and func.attr == "isatty"
                        ):
                            bare_isatty_found = True

        assert console_renderer_found, "ConsoleFileRenderer class not found"
        assert not bare_isatty_found, "Bare sys.stdout.isatty() call found in ConsoleFileRenderer"


# --- 2. broad-exception-cleanup ---


class TestBroadExceptionCleanup:
    """SPEC: legacy-elimination::broad-exception-cleanup — remove broad exception handling."""

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

    def test_multi_optimistic_logger_reraises(self) -> None:
        """MultiOptimisticLogger.msg must re-raise or wrap exceptions."""
        source = (SRC_ROOT / "core.py").read_text()
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "MultiOptimisticLogger":
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == "msg":
                        for child in ast.walk(item):
                            if isinstance(child, ast.Try):
                                for handler in child.handlers:
                                    has_reraise = any(
                                        isinstance(stmt, ast.Raise)
                                        for stmt in ast.walk(ast.Module(body=handler.body, type_ignores=[]))
                                    )
                                    if not has_reraise:
                                        pytest.fail(
                                            "MultiOptimisticLogger.msg silently catches exceptions without re-raising"
                                        )
                break
        else:
            pytest.fail("MultiOptimisticLogger class not found")

    def test_load_pyproject_config_no_bare_exception(self) -> None:
        """_load_pyproject_config must catch only specific exceptions, not bare Exception."""
        source = (SRC_ROOT / "config.py").read_text()
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "_load_pyproject_config":
                for child in ast.walk(node):
                    if isinstance(child, ast.ExceptHandler) and child.type is not None:
                        if isinstance(child.type, ast.Name) and child.type.id == "Exception":
                            pytest.fail("_load_pyproject_config has bare 'except Exception'")
                        if isinstance(child.type, ast.Tuple):
                            for elt in child.type.elts:
                                if isinstance(elt, ast.Name) and elt.id == "Exception":
                                    pytest.fail(
                                        "_load_pyproject_config catches 'Exception' in tuple"
                                    )
                break
        else:
            pytest.fail("_load_pyproject_config function not found")

    def test_no_pending_warnings_global(self) -> None:
        """No _PENDING_WARNINGS global in config.py."""
        source = (SRC_ROOT / "config.py").read_text()
        assert "_PENDING_WARNINGS" not in source

    def test_no_atexit_registration(self) -> None:
        """config.py must not call atexit.register."""
        source = (SRC_ROOT / "config.py").read_text()
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if (
                    isinstance(func, ast.Attribute)
                    and func.attr == "register"
                    and isinstance(func.value, ast.Name)
                    and func.value.id == "atexit"
                ):
                    pytest.fail("config.py calls atexit.register")


# --- 3. backwards-compat-purge ---


class TestBackwardsCompatPurge:
    """SPEC: legacy-elimination::backwards-compat-purge — remove backwards-compat artifacts."""

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
                        elements = [
                            elt.value
                            for elt in node.value.elts
                            if isinstance(elt, ast.Constant)
                        ]
                        assert "output" not in elements, (
                            "Bare 'output' found in KEYS_TO_SKIP_IN_JOURNAL_MESSAGE"
                        )

    def test_log_to_stdlib_removed(self) -> None:
        """log_to_stdlib function must not exist in core.py."""
        source = (SRC_ROOT / "core.py").read_text()
        tree = ast.parse(source)
        func_names = [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
        ]
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


# --- 4. vulture-whitelist-cleanup ---


class TestVultureWhitelistCleanup:
    """SPEC: legacy-elimination::vulture-whitelist-cleanup — remove stale whitelist entries."""

    STALE_REFERENCES: ClassVar[list[str]] = [
        "eliot",
        "tools_generate_service",
        "tools_review",
        "tools_journal",
        "dashboard",
        "task_install",
        "task_format",
        "napoleon_google_docstring",
        "init_i18n",
        "mock_eliot_unavailable",
    ]

    def test_vulture_whitelist_has_no_stale_entries(self) -> None:
        """Vulture whitelist must not reference stale code."""
        whitelist_path = REPO_ROOT / ".vulture_whitelist.py"
        if not whitelist_path.exists():
            pytest.skip("Whitelist file deleted entirely (acceptable)")

        source = whitelist_path.read_text()
        found = [ref for ref in self.STALE_REFERENCES if ref in source]
        assert not found, f"Stale references found in whitelist: {found}"


# --- 5. stale-documentation-fix ---


class TestStaleDocumentationFix:
    """SPEC: legacy-elimination::stale-documentation-fix — fix stale documentation."""

    def test_conventions_no_mypy_reference(self) -> None:
        """CONVENTIONS.md must not mention 'mypy'."""
        source = (REPO_ROOT / "CONVENTIONS.md").read_text()
        assert "mypy" not in source

    def test_type_checking_guide_correct_import(self) -> None:
        """docs/dev/type_checking_guide.md must use 'stogger.systemd' not 'stogger_systemd'."""
        source = (REPO_ROOT / "docs" / "dev" / "type_checking_guide.md").read_text()
        assert "stogger_systemd" not in source

    def test_adrs_no_placeholder_comments(self) -> None:
        """No ADR file may contain 'Tests will be added after implementation'."""
        adr_dir = REPO_ROOT / "docs" / "dev" / "adr"
        adr_files = sorted(adr_dir.glob("*.md"))
        assert adr_files, "No ADR files found"

        for adr_path in adr_files:
            source = adr_path.read_text()
            assert "<!-- Tests will be added after implementation -->" not in source, (
                f"Placeholder comment found in {adr_path.name}"
            )

    def test_pyproject_no_commented_infrastructure_files(self) -> None:
        """pyproject.toml must have no commented-out infrastructure_files line."""
        source = (REPO_ROOT / "pyproject.toml").read_text()
        for line in source.splitlines():
            stripped = line.strip()
            if "infrastructure_files" in stripped and stripped.startswith("#"):
                pytest.fail(f"Commented-out infrastructure_files found: {line}")


# --- 6. spec-test-lifecycle-cleanup ---


class TestSpecTestLifecycleCleanup:
    """SPEC: legacy-elimination::spec-test-lifecycle-cleanup — delete completed spec tests."""

    def test_impl_spec_decorators_docs_deleted(self) -> None:
        """tests/impl_spec/test_logging_decorators_docs.py must not exist."""
        path = REPO_ROOT / "tests" / "impl_spec" / "test_logging_decorators_docs.py"
        assert not path.exists()

    def test_impl_spec_format_config_deleted(self) -> None:
        """tests/impl_spec/test_format_config_extension.py must not exist."""
        path = REPO_ROOT / "tests" / "impl_spec" / "test_format_config_extension.py"
        assert not path.exists()

    def test_impl_spec_postgres_deleted(self) -> None:
        """tests/impl_spec/test_postgres_target.py must not exist."""
        path = REPO_ROOT / "tests" / "impl_spec" / "test_postgres_target.py"
        assert not path.exists()


# --- 7. colorama-availability-check ---


class TestColoramaAvailabilityCheck:
    """SPEC: legacy-elimination::colorama-availability-check — direct colorama import."""

    def test_colors_no_colorama_fallback(self) -> None:
        """_colors.py must import colorama directly with no conditional check."""
        source = (SRC_ROOT / "_colors.py").read_text()
        tree = ast.parse(source)

        # Must not have 'if colorama' or 'if sys.stdout.isatty() and colorama' pattern
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                test_str = ast.dump(node.test)
                if "colorama" in test_str:
                    pytest.fail("_colors.py has conditional colorama check")


# --- 8. optional-import-simplification ---


class TestOptionalImportSimplification:
    """SPEC: legacy-elimination::optional-import-simplification — direct systemd import."""

    def test_systemd_import_is_direct(self) -> None:
        """core.py must import from stogger.systemd directly, no try/except ImportError."""
        source = (SRC_ROOT / "core.py").read_text()
        tree = ast.parse(source)

        # Find try blocks that catch ImportError for stogger.systemd
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                for handler in node.handlers:
                    catches_import_error = (
                        isinstance(handler.type, ast.Name) and handler.type.id == "ImportError"
                    ) or (
                        isinstance(handler.type, ast.Tuple)
                        and any(
                            isinstance(elt, ast.Name) and elt.id == "ImportError"
                            for elt in handler.type.elts
                        )
                    )
                    if catches_import_error:
                        # Check if the try body contains a stogger.systemd import
                        try_body_source = ast.get_source_segment(source, node)
                        if try_body_source and "stogger.systemd" in try_body_source:
                            pytest.fail(
                                "stogger.systemd import wrapped in try/except ImportError"
                            )
