"""Simplified tests for the linter module functionality."""

from pathlib import Path
import tempfile
import textwrap
from unittest.mock import patch

import pytest

from stoggertools.linter import (
    LoggingStats,
    LoggingVisitor,
    analyze_file,
    check_logging_quality,
    lint_directory,
)


class TestLinterBasics:
    """Basic tests for linter functionality."""

    def test_logging_stats_creation(self):
        """Test LoggingStats creation."""
        stats = LoggingStats(100, 80, 10, 5, 3, 12.5, 60.0)
        assert stats.total_lines == 100
        assert stats.code_lines == 80

    def test_logging_visitor_creation(self):
        """Test LoggingVisitor creation."""
        visitor = LoggingVisitor()
        assert visitor.log_statements == 0
        assert visitor.functions == 0

    def test_analyze_file_with_python_code(self):
        """Test analyzing a Python file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("""
import logging

def test_function():
    logging.info("This is a test")
    return True

def another_function():
    print("No logging here")
    return False
""")
            f.flush()

            try:
                stats, level_issues = analyze_file(Path(f.name))
                assert stats.total_lines > 0
                assert stats.log_statements > 0
                assert stats.functions >= 2
            finally:
                Path(f.name).unlink()

    def test_check_logging_quality(self):
        """Test logging quality check."""
        stats = LoggingStats(100, 80, 8, 5, 3, 10.0, 60.0)
        issues = check_logging_quality(stats)
        assert isinstance(issues, list)
        assert len(issues) > 0

    def test_lint_directory_empty(self):
        """Test linting empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("builtins.print"):
                result = lint_directory(Path(tmpdir))
                assert isinstance(result, bool)

    def _write(self, tmp: Path, name: str, content: str) -> Path:
        p = tmp / name
        p.write_text(textwrap.dedent(content), encoding="utf-8")
        return p

    def test_linter_suggests_log_exception(self, tmp_path: Path):
        code = """
        import structlog
        log = structlog.get_logger()

        def f():
            try:
                1/0
            except Exception as e:
                log.error("failed", reason="division", value=0)
        """
        p = self._write(tmp_path, "a.py", code)
        stats, issues = analyze_file(p)
        assert any(
            iss.category == "except_logging" and iss.suggested_level == "exception"
            for iss in issues
        )

    def test_linter_accepts_log_exception_without_error_field(self, tmp_path: Path):
        code = """
        import structlog
        log = structlog.get_logger()

        def f():
            try:
                1/0
            except Exception:
                log.exception("failed", reason="division")
        """
        p = self._write(tmp_path, "b.py", code)
        stats, issues = analyze_file(p)
        # Should not flag anything for except_logging category
        assert not any(
            iss.category == "except_logging" and iss.current_level == "exception"
            for iss in issues
        )

    def test_linter_flags_log_error_without_exc_info_in_except(self, tmp_path: Path):
        code = """
        import structlog
        log = structlog.get_logger()

        def f():
            try:
                1/0
            except Exception:
                log.error("failed", reason="division")
        """
        p = self._write(tmp_path, "c.py", code)
        stats, issues = analyze_file(p)
        assert any(
            iss.category == "except_logging" and iss.current_level == "error"
            for iss in issues
        )


if __name__ == "__main__":
    pytest.main([__file__])
