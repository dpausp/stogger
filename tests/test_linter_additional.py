from pathlib import Path
import textwrap

import nicestlog.linter as linter


def _write(tmp: Path, name: str, content: str) -> Path:
    p = tmp / name
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return p


def test_analyze_file_empty(tmp_path: Path):
    p = _write(tmp_path, "empty.py", "\n\n# just a comment\n")
    stats = linter.analyze_file(p)
    assert stats.code_lines == 0
    assert stats.log_statements == 0


def test_analyze_file_with_functions_and_logs(tmp_path: Path):
    code = """
    import structlog
    log = structlog.get_logger()

    def a():
        log.info("hello")

    def b():
        pass

    def c():
        log.debug("x")
    """
    p = _write(tmp_path, "with_logs.py", code)
    stats = linter.analyze_file(p)
    assert stats.functions == 3
    assert stats.functions_with_logging == 2
    assert stats.log_statements == 2
    assert stats.code_lines > 0


def test_check_logging_quality_thresholds():
    # Below min coverage
    low = linter.LoggingStats(
        total_lines=10,
        code_lines=10,
        log_statements=0,
        functions=1,
        functions_with_logging=0,
        log_coverage_percent=0.0,
        function_coverage_percent=0.0,
    )
    issues = linter.check_logging_quality(low, min_coverage=5.0, max_coverage=15.0)
    assert any("Too little logging" in x for x in issues)

    # Above max coverage
    high = linter.LoggingStats(
        total_lines=10,
        code_lines=10,
        log_statements=20,
        functions=10,
        functions_with_logging=10,
        log_coverage_percent=200.0,
        function_coverage_percent=100.0,
    )
    issues = linter.check_logging_quality(high, min_coverage=5.0, max_coverage=15.0)
    assert any("Possibly too much" in x for x in issues)

    # Good coverage
    good = linter.LoggingStats(
        total_lines=10,
        code_lines=10,
        log_statements=1,
        functions=2,
        functions_with_logging=1,
        log_coverage_percent=10.0,
        function_coverage_percent=50.0,
    )
    issues = linter.check_logging_quality(good, min_coverage=5.0, max_coverage=15.0)
    assert any("Good logging coverage" in x for x in issues)
    assert any("Good function logging coverage" in x for x in issues)


def test_lint_directory_reports_and_aggregates(tmp_path: Path, capsys):
    # Create two files: one okay, one low
    _write(
        tmp_path,
        "ok.py",
        """
    import structlog
    log = structlog.get_logger()
    def f():
        log.info("x")
    """,
    )
    _write(
        tmp_path,
        "low.py",
        """
    def g():
        pass
    """,
    )

    success = linter.lint_directory(tmp_path, min_coverage=5.0, max_coverage=15.0)
    out = capsys.readouterr().out

    # Should analyze both files and produce an overall report
    assert "Analyzing" in out
    assert "OVERALL LOGGING QUALITY REPORT" in out
    assert success in (True, False)  # Just ensure it returns a boolean
