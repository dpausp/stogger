from pathlib import Path
import textwrap

import nicestlog.linter as linter


def _write(tmp: Path, name: str, content: str) -> Path:
    p = tmp / name
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return p


def test_linter_suggests_log_exception(tmp_path: Path):
    code = """
    import structlog
    log = structlog.get_logger()

    def f():
        try:
            1/0
        except Exception as e:
            log.error("failed", reason="division", value=0)
    """
    p = _write(tmp_path, "a.py", code)
    stats, issues = linter.analyze_file(p)
    assert any(
        iss.category == "except_logging" and iss.suggested_level == "exception"
        for iss in issues
    )


def test_linter_accepts_log_exception_without_error_field(tmp_path: Path):
    code = """
    import structlog
    log = structlog.get_logger()

    def f():
        try:
            1/0
        except Exception:
            log.exception("failed", reason="division")
    """
    p = _write(tmp_path, "b.py", code)
    stats, issues = linter.analyze_file(p)
    # Should not flag anything for except_logging category
    assert not any(
        iss.category == "except_logging" and iss.current_level == "exception"
        for iss in issues
    )


def test_linter_flags_log_error_without_exc_info_in_except(tmp_path: Path):
    code = """
    import structlog
    log = structlog.get_logger()

    def f():
        try:
            1/0
        except Exception:
            log.error("failed", reason="division")
    """
    p = _write(tmp_path, "c.py", code)
    stats, issues = linter.analyze_file(p)
    assert any(
        iss.category == "except_logging" and iss.current_level == "error"
        for iss in issues
    )
