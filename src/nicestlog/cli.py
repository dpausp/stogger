"""Command-line interface for nicestlog.

This module provides the complete CLI interface including both basic and advanced
AST functionality, previously split between cli.py and cli_advanced.py.
"""

from __future__ import annotations

import dataclasses
import difflib
from importlib import resources
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import Annotated, Protocol, cast

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table
import structlog
import toml
import typer

import nicestlog

try:
    from .web_dashboard import FLASK_AVAILABLE, run_dashboard
except ImportError:
    run_dashboard = None
    FLASK_AVAILABLE = False

from .journal_viewer import SYSTEMD_AVAILABLE, JournalViewer
from .log_reviewer import LogQualityReviewer, print_report

try:
    from .config import NicestLogConfig
except ImportError:
    NicestLogConfig = None

import http.server
import socketserver
import tempfile
import threading
import webbrowser

from . import project_analyzer
from .advanced_assistant import (
    AdvancedAssistant,
    ASTPattern,
    CodeAnalysisResult,
    TransformationResult,
)
from .assistant import migrate_directory, migrate_file
from .cli_output_transformer import migrate_cli_outputs_file
from .config import detect_project_structure
from .gitignore_utils import filter_python_files
from .i18n_check import check_translations, format_report
from .interactive_transformer import (
    InteractiveTransformer,
)
from .linter import lint_directory
from .systemd_integration import ServiceConfig, create_systemd_service_file

logger = structlog.get_logger()


# Type protocol for migration results to handle different result types
class MigrationResultProtocol(Protocol):
    """Protocol for migration result types."""

    files_processed: int
    transformations_applied: int
    errors: int
    warnings: list[str]


# Initialize logging and console
log = structlog.get_logger(__name__)
console = Console()


# Version callback function
def version_callback(*, value: bool):
    """Show version and exit."""
    if value:
        try:
            version = importlib.metadata.version("nicestlog")
            console.print(f"nicestlog version {version}")
        except importlib.metadata.PackageNotFoundError:
            console.print("nicestlog version unknown (development)")
        raise typer.Exit()


# Main app with version option
app = typer.Typer(help="Nicestlog utility.", no_args_is_help=True)


# Add global version option
@app.callback()
def main_callback(
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            callback=version_callback,
            help="Show version and exit",
        ),
    ] = None,
):
    """Nicestlog utility."""


# Create tools subgroup for low-level utilities
tools_app = typer.Typer(help="🛠️ Low-level utilities and advanced tools")
app.add_typer(tools_app, name="tools")


# Add generate-service command to tools
@tools_app.command("generate-service")
def tools_generate_service(
    service_name: str = typer.Argument(..., help="Name of the service"),
    exec_command: str = typer.Argument(..., help="Command to execute"),
    user: str | None = typer.Option(None, "--user", help="User to run service as"),
    working_dir: str | None = typer.Option(
        None,
        "--working-dir",
        help="Working directory",
    ),
    output: str | None = typer.Option(None, "--output", help="Output file path"),
):
    """🔧 Generate systemd service file."""
    generate_service_cmd(service_name, exec_command, user, working_dir, output)


# Add check-advanced command to tools
@tools_app.command("check-advanced")
def tools_check_advanced(
    path: Annotated[str, typer.Argument(help="Path to check")] = ".",
    *,
    fix: Annotated[bool, typer.Option("--fix", help="Auto-fix issues")] = False,
    interactive: Annotated[bool, typer.Option("--interactive", "-i", help="Interactive mode")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Show what would be fixed")] = False,
    no_ast: Annotated[bool, typer.Option("--no-ast", help="Disable AST-based analysis")] = False,
    complexity: Annotated[bool, typer.Option("--complexity", help="Check code complexity")] = False,
    patterns: Annotated[list[str] | None, typer.Option("--pattern", help="Specific AST patterns to check")] = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose output")] = False,
):
    """🔬 Advanced check with all options for complexity analysis and AST patterns."""
    options = CheckOptions(
        path=path,
        fix=fix,
        interactive=interactive,
        dry_run=dry_run,
        no_ast=no_ast,
        complexity=complexity,
        patterns=patterns,
        verbose=verbose,
    )
    _run_check_command(options)


# Add review command to tools
@tools_app.command("review")
def tools_review(
    path: Annotated[str, typer.Argument(help="Path to review")],
    format_type: Annotated[
        str,
        typer.Option("--format", help="Output format"),
    ] = "text",
    min_score: Annotated[
        float,
        typer.Option("--min-score", help="Minimum score"),
    ] = 70.0,
):
    """📝 Review log quality and provide suggestions."""
    valid_formats = ["text", "json", "html"]
    if format_type not in valid_formats:
        console.print(
            f"❌ [red]Invalid format '{format_type}'. Valid formats: {', '.join(valid_formats)}[/red]",
        )
        raise typer.Exit(1)

    run_log_reviewer(path, format_type, min_score)


# Add journal command to tools
@tools_app.command("journal")
def tools_journal(
    unit: Annotated[
        str | None,
        typer.Option("--unit", "-u", help="Systemd unit"),
    ] = None,
    lines: Annotated[
        int,
        typer.Option("--lines", "-n", help="Number of lines to show"),
    ] = 50,
    *,
    follow: Annotated[
        bool,
        typer.Option("--follow", "-f", help="Follow log output"),
    ] = False,
    since: Annotated[
        str | None,
        typer.Option("--since", help="Show logs since"),
    ] = None,
    level: Annotated[
        str | None,
        typer.Option("--level", help="Log level filter"),
    ] = None,
):
    """📖 Beautiful systemd journal viewer."""
    if level and level not in ["debug", "info", "warning", "error", "critical"]:
        console.print(
            f"❌ [red]Invalid level '{level}'. Valid levels: debug, info, warning, error, critical[/red]",
        )
        raise typer.Exit(1)

    run_journal_viewer(unit, lines, follow=follow, since=since, level=level)


# Check if Flask is available for dashboard command
try:
    import flask  # noqa: F401

    FLASK_AVAILABLE_FOR_CLI = True
except ImportError:
    FLASK_AVAILABLE_FOR_CLI = False

# Add dashboard command to tools (only if Flask is available)
if FLASK_AVAILABLE_FOR_CLI:

    @tools_app.command("dashboard")
    def tools_dashboard(
        host: Annotated[
            str,
            typer.Option("--host", help="Host to bind to"),
        ] = "127.0.0.1",
        port: Annotated[int, typer.Option("--port", help="Port to bind to")] = 8080,
        debug: Annotated[bool, typer.Option("--debug", help="Debug mode")] = False,  # noqa: FBT002
    ):
        """🌐 Start the web dashboard."""
        run_dashboard_cmd(host, port, debug=debug)


# Sub-app for i18n related commands (moved to tools)
i18n_app = typer.Typer(help="Internationalization utilities")
tools_app.add_typer(i18n_app, name="i18n")


# Add i18n check command
@i18n_app.command("check")
def i18n_check(  # noqa: PLR0913
    src_dir: str = typer.Argument(..., help="Source directory to check"),
    translation_dir: str | None = typer.Option(
        None,
        "--translation-dir",
        help="Translation directory",
    ),
    language: Annotated[
        str,
        typer.Option("-l", "--language", help="Language code"),
    ] = "en",
    *,
    list_missing: Annotated[
        bool,
        typer.Option("--list-missing", help="List missing translations"),
    ] = False,
    fail_on_extra: Annotated[
        bool,
        typer.Option("--fail-on-extra", help="Fail on extra translations"),
    ] = False,
    strict: Annotated[
        bool,
        typer.Option("--strict", help="Strict mode - fail on any missing translations"),
    ] = False,
    verbose: Annotated[bool, typer.Option("--verbose", help="Verbose output")] = False,
):
    """🌍 Check translation completeness and quality."""
    try:
        # Convert src_dir to Path and get all Python files
        src_path = Path(src_dir)
        source_paths = [src_path] if src_path.is_file() else [src_path / p for p in src_path.glob("**/*.py")]

        # Use translation_dir or default
        trans_dir = Path(translation_dir) if translation_dir else src_path.parent / "translations"

        result = check_translations(
            source_paths=source_paths,
            translation_dir=trans_dir,
            language=language,
        )

        # Handle list_missing and fail_on_extra logic
        missing_keys = cast("list[str]", result.get("missing_keys", []))
        extra_keys = cast("list[str]", result.get("extra_keys", []))

        if list_missing:
            for key in missing_keys:
                console.print(key)
            # In list_missing mode with strict, fail if there are missing keys
            if strict and missing_keys:
                sys.exit(1)
            # In list_missing mode, only fail on extra keys if fail_on_extra is set
            if fail_on_extra and extra_keys:
                sys.exit(1)
            # Otherwise, exit successfully even if there are missing keys
            return

        # Normal mode: print report if verbose or if there are issues
        if verbose or missing_keys or extra_keys:
            report_text = format_report(result, include_debug=verbose)
            console.print(report_text)

        # Normal mode: fail if there are missing keys or extra keys (when fail_on_extra is set)
        has_errors = bool(missing_keys) or (fail_on_extra and bool(extra_keys))
        if has_errors:
            sys.exit(1)

    except (ValueError, OSError) as e:
        console.print(f"❌ [red]Error checking translations: {e}[/red]")
        sys.exit(2)


def init_config():
    """Interactive wizard to create a [tool.nicestlog] section in pyproject.toml."""
    log.debug("starting-config-wizard")

    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        log.error("pyproject-not-found", path=str(pyproject_path.resolve()))
        sys.exit(1)

    config = {}
    config["verbose"] = input("Enable verbose (trace-level) logging? [y/N]: ").lower() == "y"
    config["syslog_identifier"] = input("Syslog identifier [nicestlog]: ") or "nicestlog"
    config["log_format"] = input("Log format (console/json) [console]: ") or "console"
    config["async_logging"] = input("Enable asynchronous (non-blocking) logging? [y/N]: ").lower() == "y"

    if input("Enable file logging? [y/N]: ").lower() == "y":
        config["log_file"] = input("Log file path [app.log]: ") or "app.log"
        config["log_file_max_size"] = int(
            input("Max log file size in MB [10]: ") or "10",
        )
        config["log_file_backup_count"] = int(
            input("Number of backup files to keep [3]: ") or "3",
        )

    config["enable_structured_logging"] = input("Enable structured logging? [Y/n]: ").lower() != "n"
    if config["enable_structured_logging"]:
        config["structured_format"] = input("Structured format (json/key_value) [json]: ") or "json"

    config["enable_performance_monitoring"] = input("Enable performance monitoring? [y/N]: ").lower() == "y"

    # Write config to pyproject.toml

    try:
        with Path(pyproject_path).open() as f:
            pyproject = toml.load(f)
    except Exception:  # noqa: BLE001
        pyproject = {}

    if "tool" not in pyproject:
        pyproject["tool"] = {}
    pyproject["tool"]["nicestlog"] = config

    with Path(pyproject_path).open("w") as f:
        toml.dump(pyproject, f)

    log.debug("config-wizard-completed", config=config)


@app.command()
def docs(
    *,
    interactive: Annotated[
        bool,
        typer.Option("--interactive", "-i", help="Interactive docs browser"),
    ] = False,
    feature: Annotated[
        str | None,
        typer.Option("--feature", "-f", help="Show docs for specific feature"),
    ] = None,
    pager: Annotated[
        bool,
        typer.Option("--pager", "-p", help="Use pager for displaying docs"),
    ] = False,
):
    """📚 Show documentation and examples."""
    if interactive:
        _show_docs_interactive(use_pager=pager)
    elif feature:
        _show_feature_docs(feature, use_pager=pager)
    else:
        _show_markdown_files(
            [
                "README.md",
                "user_guide/getting_started.md",
                "user_guide/best_practices.md",
            ],
            use_pager=pager,
        )


@app.command("docs-serve")
def docs_serve(
    port: Annotated[int, typer.Option("--port", "-p", help="Port to serve on")] = 8000,
    host: Annotated[str, typer.Option("--host", help="Host to bind to")] = "127.0.0.1",
    *,
    open_browser: Annotated[
        bool,
        typer.Option("--open/--no-open", help="Open browser automatically"),
    ] = True,
    build: Annotated[
        bool,
        typer.Option("--build/--no-build", help="Build docs before serving"),
    ] = True,
):
    """🌐 Serve HTML documentation in browser."""
    _serve_html_docs(port, host, open_browser=open_browser, build=build)


@app.command("init")
def init_config_cmd(
    path: str = typer.Argument(".", help="Project path to initialize"),
    template: str | None = typer.Option(  # noqa: ARG001
        None,
        "--template",
        help="Configuration template",
    ),
    force: bool = typer.Option(False, "--force", help="Overwrite existing config"),  # noqa: ARG001,FBT001,FBT003
):
    """🔧 Initialize nicestlog configuration."""
    # Enhanced init command that works with any project path
    original_cwd = Path.cwd()
    target_path = Path(path).resolve()

    if not target_path.exists():
        console.print(f"❌ [red]Path {path} does not exist[/red]")
        raise typer.Exit(1)

    if target_path.is_file():
        target_path = target_path.parent

    # Change to target directory for init_config

    os.chdir(target_path)

    try:
        init_config()
        console.print(f"✅ [green]Configuration initialized in {target_path}[/green]")
    finally:
        os.chdir(original_cwd)


@dataclasses.dataclass
class MigrateOptions:
    """Configuration options for migrate command."""

    path: str = "."
    output: str | None = None
    mode: str = "logging"
    target: str = "nicestlog"
    interactive: bool = False
    dry_run: bool = False
    verbose: bool = False


@dataclasses.dataclass(kw_only=True)
class CheckOptions:
    """Options for the check command."""

    path: str = "."
    fix: bool = False
    interactive: bool = False
    dry_run: bool = False
    no_ast: bool = False
    complexity: bool = False
    patterns: list[str] | None = None
    verbose: bool = False


@app.command()
def check(
    path: Annotated[str, typer.Argument(help="Path to check")] = ".",
    *,
    fix: Annotated[bool, typer.Option("--fix", help="Auto-fix issues")] = False,
    interactive: Annotated[bool, typer.Option("--interactive", "-i", help="Interactive mode")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Show what would be fixed")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose output")] = False,
):
    """🔍 Check code for logging best practices with AST analysis by default.

    Examples:
      nicestlog check file.py                    # Basic linting + AST analysis
      nicestlog check file.py --fix              # Fix with AST transforms
      nicestlog check file.py --interactive      # Interactive mode
      nicestlog check file.py --dry-run --fix    # Preview fixes

    For advanced options, use: nicestlog tools check-advanced
    """
    options = CheckOptions(
        path=path,
        fix=fix,
        interactive=interactive,
        dry_run=dry_run,
        verbose=verbose,
    )
    _run_check_command(options)


def _run_check_command(options: CheckOptions):
    """Execute the check command with given options."""
    nicestlog.init_logging(verbose=options.verbose)
    log = structlog.get_logger()

    path_obj = Path(options.path)
    if not path_obj.exists():
        log.info("check-path-not-found", path=options.path, _replace_msg=f"Path {options.path} does not exist")
        sys.exit(1)

    project_structure = _detect_project_structure(path_obj, log)
    _display_mode_info(options, log)

    lint_success, ast_issues = _perform_analysis(options, path_obj, project_structure, log)

    if options.interactive and ast_issues:
        _run_interactive_mode(options, path_obj, ast_issues, log)
    elif options.fix and not options.no_ast and ast_issues:
        _run_fix_mode(options, path_obj, project_structure, log)

    _handle_check_summary(lint_success=lint_success, ast_issues=ast_issues, log=log)


def _handle_check_summary(*, lint_success: bool, ast_issues: list, log):
    """Handle and display the summary of check results."""
    if lint_success:
        log.info("check-lint-passed", _replace_msg="✅ Linting passed")
    else:
        log.info("check-lint-failed", _replace_msg="❌ Linting failed")

    if ast_issues:
        log.info("check-ast-issues-found", count=len(ast_issues), _replace_msg=f"🔍 Found {len(ast_issues)} AST issues")
    else:
        log.info("check-ast-clean", _replace_msg="🔍 No AST issues found")


def _detect_project_structure(path_obj: Path, log):
    """Detect and validate project structure."""
    try:
        if path_obj.is_dir():
            project_structure = detect_project_structure(path_obj)
            _display_project_context(project_structure, verbose=False)
        else:
            project_structure = detect_project_structure(path_obj.parent)
            _display_project_context(project_structure, verbose=False, single_file=path_obj)
    except ValueError as e:
        log.info(
            "check-project-structure-failed", error=str(e), _replace_msg=f"Project structure detection failed: {e}"
        )
        log.info(
            "check-configure-pyproject", _replace_msg="Please configure [tool.nicestlog] section in pyproject.toml"
        )
        sys.exit(1)
    else:
        return project_structure


def _display_mode_info(options: CheckOptions, log):
    """Display mode information based on options."""
    mode_info = []
    if options.fix:
        if options.interactive:
            mode_info.append("🎯 Interactive fixing")
        elif options.dry_run:
            mode_info.append("🔍 Dry run preview")
        else:
            mode_info.append("🔧 Auto-fixing")

    if not options.no_ast:
        mode_info.append("🔬 AST analysis")
    if options.complexity:
        mode_info.append("📊 Complexity check")

    if mode_info:
        log.info("check-mode-info", modes=mode_info, _replace_msg=f"Mode: {' + '.join(mode_info)}")


def _perform_analysis(options: CheckOptions, path_obj: Path, project_structure, log):
    """Perform basic linting and AST analysis."""
    basic_success = True
    if options.no_ast and not options.interactive and not options.patterns and not options.complexity:
        log.info("check-basic-linting-start", _replace_msg="Running basic linting...")
        basic_success = lint_directory(path_obj, project_structure=project_structure)

    lint_success = basic_success
    ast_issues = None

    if not options.no_ast or options.interactive or options.patterns or options.complexity:
        ast_issues = _run_ast_analysis(options, path_obj, project_structure, log)
        if ast_issues:
            _display_ast_issues(ast_issues, log)

    return lint_success, ast_issues


def _run_ast_analysis(options: CheckOptions, path_obj: Path, project_structure, log):
    """Run AST analysis on files."""
    log.info("check-ast-analysis-start", _replace_msg="Running AST analysis...")

    assistant = AdvancedAssistant(verbose=options.verbose)

    if options.patterns:
        _configure_ast_patterns(assistant, options.patterns)

    if path_obj.is_file():
        return _analyze_single_file_for_check(assistant, path_obj, options)
    else:
        return _analyze_directory_files(assistant, path_obj, project_structure, options, log)


def _configure_ast_patterns(assistant: AdvancedAssistant, patterns: list[str]):
    """Configure AST patterns based on user selection."""
    for pattern_name in patterns:
        for ast_pattern in assistant.patterns:
            if pattern_name.lower() in ast_pattern.name.lower():
                ast_pattern.enabled = True
            else:
                ast_pattern.enabled = False


def _analyze_single_file_for_check(assistant: AdvancedAssistant, path_obj: Path, options: CheckOptions):
    """Analyze a single file for check command."""
    ast_result = assistant.analyze_file(path_obj)
    _display_check_analysis_result(ast_result, show_complexity=options.complexity, verbose=options.verbose)
    return [ast_result]


def _analyze_directory_files(
    assistant: AdvancedAssistant, path_obj: Path, project_structure, options: CheckOptions, log
):
    """Analyze all files in a directory."""
    python_files = filter_python_files(path_obj, respect_gitignore=True)

    if not python_files:
        log.info(
            "check-no-files-found",
            _replace_msg="No Python files found in directory (after applying .gitignore)",
        )
        return None

    log.info(
        "check-files-analyzed",
        file_count=len(python_files),
        _replace_msg=f"Analyzing {len(python_files)} Python files (respecting .gitignore)",
    )

    ast_results = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for py_file in python_files:
            task = progress.add_task(f"Analyzing {py_file.name}...", total=None)
            result = assistant.analyze_file(py_file)
            ast_results.append(result)
            progress.remove_task(task)

    _display_unified_check_analysis(
        ast_results,
        show_complexity=options.complexity,
        verbose=options.verbose,
        directory=path_obj,
        project_structure=project_structure,
    )
    return ast_results


def _display_ast_issues(ast_issues, log):
    """Display AST issues found during analysis."""
    if ast_issues and _has_ast_issues(ast_issues):
        log.info("check-ast-issues-found", _replace_msg="AST Issues Found:")
        for result in ast_issues:
            if result.issues:
                log.info(
                    "check-file-issues",
                    file=result.file_path.name,
                    issues=result.issues,
                    _replace_msg=f"  {result.file_path.name}: {', '.join(result.issues)}",
                )


def _run_interactive_mode(path_obj: Path, log):
    """Run interactive transformation mode."""
    log.info("check-interactive-start", _replace_msg="Starting interactive mode...")
    transformer = InteractiveTransformer()

    if path_obj.is_file():
        transformer.transform_file_interactive(path_obj)
    else:
        python_files = filter_python_files(path_obj, respect_gitignore=True)
        for py_file in python_files:
            log.info("check-processing-file", file=str(py_file), _replace_msg=f"Processing: {py_file}")
            if typer.confirm(f"Transform {py_file.name}?"):
                transformer.transform_file_interactive(py_file)


def _run_fix_mode(options: CheckOptions, path_obj: Path, project_structure, log):
    """Run automatic fix mode."""
    log.info("check-fixes-start", _replace_msg="Applying AST-based fixes...")

    assistant = AdvancedAssistant(verbose=options.verbose)

    if path_obj.is_file():
        transform_result = assistant.transform_file(path_obj, dry_run=options.dry_run)
        _display_transformation_result(transform_result, options.dry_run)
    else:
        _fix_directory_files(assistant, path_obj, project_structure, options)


def _fix_directory_files(assistant: AdvancedAssistant, path_obj: Path, project_structure, options: CheckOptions):
    """Fix all files in a directory."""
    python_files = []
    for src_dir in project_structure.source_dirs:
        src_path = path_obj / src_dir if path_obj.is_dir() else path_obj.parent / src_dir
        if src_path.exists():
            src_files = filter_python_files(src_path, respect_gitignore=True)
            for py_file in src_files:
                if not project_structure.should_exclude_from_logging_analysis(py_file):
                    python_files.append(py_file)

    transform_results = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for py_file in python_files:
            task = progress.add_task(f"Transforming {py_file.name}...", total=None)
            transform_result = assistant.transform_file(py_file, dry_run=options.dry_run)
            transform_results.append(transform_result)
            progress.remove_task(task)

    _display_directory_transformation(transform_results, options.dry_run)


def _handle_check_summary(*, lint_success: bool, ast_issues, log):
    """Handle final summary and exit code."""
    has_issues = not lint_success or (ast_issues and _has_ast_issues(ast_issues))

    if has_issues:
        log.info("check-issues-found", _replace_msg="Issues found. Run with --fix to apply automatic fixes.")
        sys.exit(1)
    else:
        log.info("check-all-passed", _replace_msg="All checks passed!")


def _display_check_analysis_result(result: CodeAnalysisResult, *, show_complexity: bool, verbose: bool = False):
    """Display analysis results for check command."""
    log = structlog.get_logger()
    
    if verbose or show_complexity:
        _display_detailed_analysis(result, show_complexity, log)
    else:
        _display_compact_analysis(result, log)
    
    _display_analysis_issues(result, verbose, log)


def _display_detailed_analysis(result: CodeAnalysisResult, show_complexity: bool, log):
    """Display detailed analysis metrics."""
    log.info(
        "check-analysis-results",
        file=result.file_path.name,
        _replace_msg=f"Analysis Results for {result.file_path.name}",
    )

    log.info(
        "check-metrics",
        lines=result.lines_of_code,
        functions=result.function_count,
        classes=result.class_count,
        complexity=result.complexity_score if show_complexity else None,
        _replace_msg=f"Lines of Code: {result.lines_of_code}",
    )
    log.info("check-functions", count=result.function_count, _replace_msg=f"Functions: {result.function_count}")
    log.info("check-classes", count=result.class_count, _replace_msg=f"Classes: {result.class_count}")

    if show_complexity:
        log.info(
            "check-complexity",
            score=result.complexity_score,
            _replace_msg=f"Complexity Score: {result.complexity_score:.2f}",
        )


def _display_compact_analysis(result: CodeAnalysisResult, log):
    """Display compact analysis summary."""
    issue_count = len(result.issues) if result.issues else 0
    status = "❌" if issue_count > 0 else "✅"
    log.info(
        "check-file-status",
        file=result.file_path.name,
        issues=issue_count,
        _replace_msg=f"{status} {result.file_path.name} ({issue_count} issues)",
    )


def _display_analysis_issues(result: CodeAnalysisResult, verbose: bool, log):
    """Display issues found during analysis."""
    if not result.issues:
        if verbose:
            log.info("check-no-issues", _replace_msg="No AST issues found!")
        return

    if verbose:
        _display_verbose_issues(result.issues, log)
    else:
        _display_compact_issues(result.issues, log)


def _display_verbose_issues(issues: list[str], log):
    """Display detailed issue breakdown."""
    logging_issues, general_issues = _categorize_issues(issues)

    if logging_issues:
        log.info("Logging Improvement Opportunities:")
        for _i, issue in enumerate(logging_issues, 1):
            priority = "High" if "print" in issue.lower() else "Medium"
            log.info("logging-issue", priority=priority, issue=issue, _replace_msg=f"  {priority}: {issue}")

    if general_issues:
        log.info("Code Quality Issues:")
        for issue in general_issues:
            log.info("code-quality-issue", issue=issue, _replace_msg=f"  Complexity: {issue}")

    if logging_issues:
        _display_improvement_suggestions(log)


def _display_compact_issues(issues: list[str], log):
    """Display compact issue summary."""
    logging_count, general_count = _count_issue_types(issues)

    if logging_count > 0:
        log.info(
            "check-logging-issues-count",
            count=logging_count,
            _replace_msg=f"  🔍 {logging_count} logging issues",
        )
    if general_count > 0:
        log.info(
            "check-general-issues-count",
            count=general_count,
            _replace_msg=f"  ⚠️  {general_count} code quality issues",
        )


def _categorize_issues(issues: list[str]) -> tuple[list[str], list[str]]:
    """Categorize issues into logging and general categories."""
    logging_issues = []
    general_issues = []

    for issue in issues:
        if any(keyword in issue.lower() for keyword in ["print", "log", "logging"]):
            logging_issues.append(issue)
        else:
            general_issues.append(issue)

    return logging_issues, general_issues


def _count_issue_types(issues: list[str]) -> tuple[int, int]:
    """Count logging and general issues."""
    logging_count = sum(
        1 for issue in issues if any(keyword in issue.lower() for keyword in ["print", "log", "logging"])
    )
    general_count = len(issues) - logging_count
    return logging_count, general_count


def _display_improvement_suggestions(log):
    """Display actionable improvement suggestions."""
    log.info("check-logging-improvements", _replace_msg="Logging Improvements:")
    log.info("check-fix-suggestion", _replace_msg="  • Run with --fix to automatically convert print statements")
    log.info(
        "check-structured-logging-suggestion",
        _replace_msg="  • Consider adding structured logging to functions without logs",
    )


def _display_unified_check_analysis(
    results: list[CodeAnalysisResult],
    *,
    show_complexity: bool,
    verbose: bool = False,
    directory: Path | None = None,
    project_structure=None,
) -> bool:
    """Display unified analysis results combining logging quality and AST metrics."""
    log = structlog.get_logger()
    
    # Extract metrics and run linter
    ast_metrics, total_ast_issues, all_ast_insights = _extract_ast_metrics(results, show_complexity, directory)
    lint_success = _run_linter_with_metrics(ast_metrics, directory or results[0].file_path.parent, project_structure, log)
    
    # Display insights based on mode
    if verbose:
        _display_verbose_unified_insights(results, total_ast_issues, all_ast_insights, log)
    else:
        _display_compact_unified_summary(results, total_ast_issues, log)
    
    return lint_success


def _extract_ast_metrics(results: list[CodeAnalysisResult], show_complexity: bool, directory: Path | None) -> tuple[dict, int, list[str]]:
    """Extract AST metrics from analysis results."""
    ast_metrics = {}
    total_ast_issues = 0
    all_ast_insights = []
    
    directory_path = directory or results[0].file_path.parent
    for result in results:
        ast_metrics[str(result.file_path.relative_to(directory_path))] = {
            "functions": result.function_count,
            "classes": result.class_count,
            "complexity": result.complexity_score if show_complexity else None,
        }
        total_ast_issues += len(result.issues)
        if result.issues:
            all_ast_insights.extend(
                [f"  • {result.file_path.name}: {issue}" for issue in result.issues],
            )
    
    return ast_metrics, total_ast_issues, all_ast_insights


def _run_linter_with_metrics(ast_metrics: dict, directory_path: Path, project_structure, log) -> bool:
    """Run linter with AST metrics integration."""
    log.info("check-unified-analysis", _replace_msg="Unified Code Quality Analysis")
    
    # Set environment variable to pass AST metrics to linter
    os.environ["NICESTLOG_AST_METRICS"] = json.dumps(ast_metrics)
    
    lint_success = True
    try:
        lint_success = lint_directory(directory_path, project_structure=project_structure)
    finally:
        # Clean up environment variable
        if "NICESTLOG_AST_METRICS" in os.environ:
            del os.environ["NICESTLOG_AST_METRICS"]
    
    return lint_success


def _display_verbose_unified_insights(results: list[CodeAnalysisResult], total_ast_issues: int, all_ast_insights: list[str], log):
    """Display detailed unified analysis insights."""
    max_insights = 5
    
    if all_ast_insights:
        log.info("check-ast-insights", _replace_msg="AST Analysis Insights:")
        _display_file_statistics(results, log)
        
        if total_ast_issues > 0:
            _display_issue_details(total_ast_issues, all_ast_insights, max_insights, log)
        else:
            log.info("check-no-issues-detected", _replace_msg="  • No code quality issues detected - excellent code structure!")
        
        log.info("check-consider-structured-logging", _replace_msg="  • Consider adding structured logging to functions without logs")


def _display_file_statistics(results: list[CodeAnalysisResult], log):
    """Display file analysis statistics."""
    total_functions = sum(r.function_count for r in results)
    log.info(
        "check-files-analyzed",
        file_count=len(results),
        total_functions=total_functions,
        _replace_msg=f"  • {len(results)} files analyzed with {total_functions} total functions",
    )
    log.info(
        "check-average-functions",
        average=total_functions / len(results),
        _replace_msg=f"  • Average {total_functions / len(results):.1f} functions per file suggests good code organization",
    )


def _display_issue_details(total_ast_issues: int, all_ast_insights: list[str], max_insights: int, log):
    """Display detailed issue information."""
    log.info(
        "check-improvements-identified",
        count=total_ast_issues,
        _replace_msg=f"  • {total_ast_issues} code quality improvements identified:",
    )
    for insight in all_ast_insights[:max_insights]:
        log.info("check-insight", text=insight, _replace_msg=insight)
    if len(all_ast_insights) > max_insights:
        log.info(
            "check-more-insights",
            more=len(all_ast_insights) - max_insights,
            _replace_msg=f"    ... and {len(all_ast_insights) - max_insights} more suggestions",
        )


def _display_compact_unified_summary(results: list[CodeAnalysisResult], total_ast_issues: int, log):
    """Display compact unified analysis summary."""
    total_files = len(results)
    if total_ast_issues > 0:
        log.info(
            "check-issues-summary",
            files=total_files,
            issues=total_ast_issues,
            _replace_msg=f"{total_files} files checked, {total_ast_issues} issues found",
        )
        log.info("check-use-verbose", _replace_msg="Use --verbose for detailed analysis")
    else:
        log.info(
            "check-no-issues-found",
            files=total_files,
            _replace_msg=f"{total_files} files checked - no issues found!",
        )


def _display_check_directory_analysis(
    results: list[CodeAnalysisResult],
    *,
    show_complexity: bool,
):
    """Display analysis results for check command on directories."""
    console.print("Directory Analysis Summary", style="bold blue")

    table = Table(title="Summary Statistics")
    table.add_column("File", style="cyan")
    table.add_column("LOC", justify="right")
    table.add_column("Functions", justify="right")
    table.add_column("Classes", justify="right")
    if show_complexity:
        table.add_column("Complexity", justify="right")
    table.add_column("Issues", justify="right")

    total_loc = 0
    total_functions = 0
    total_classes = 0
    total_issues = 0

    for result in results:
        total_loc += result.lines_of_code
        total_functions += result.function_count
        total_classes += result.class_count
        total_issues += len(result.issues)

        row = [
            result.file_path.name,
            str(result.lines_of_code),
            str(result.function_count),
            str(result.class_count),
        ]

        if show_complexity:
            row.append(f"{result.complexity_score:.1f}")

        row.append(str(len(result.issues)))
        table.add_row(*row)

    # Add totals row
    totals_row = [
        "TOTAL",
        str(total_loc),
        str(total_functions),
        str(total_classes),
    ]

    if show_complexity:
        totals_row.append("-")

    totals_row.append(str(total_issues))
    table.add_row(*totals_row, style="bold")

    console.print(table)


def _has_ast_issues(ast_issues) -> bool:
    """Check if AST analysis found any issues."""
    if isinstance(ast_issues, list):
        return any(len(result.issues) > 0 for result in ast_issues)
    else:
        return len(ast_issues.issues) > 0


# Helper functions for AST operations
def _analyze_single_file(assistant: AdvancedAssistant, path: Path, *, json_output: bool):
    """Analyze a single Python file."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Analyzing {path.name}...", total=None)
        result = assistant.analyze_file(path)
        progress.remove_task(task)

    if json_output:
        console.print(json.dumps(result.to_dict(), indent=2))
    else:
        _display_analysis_result(result)


def _analyze_directory(
    assistant: AdvancedAssistant,
    path: Path,
    pattern: str,
    *,
    json_output: bool,
):
    """Analyze all Python files in a directory."""
    # Use gitignore-aware file filtering and respect project structure
    # Detect project structure to get source directories
    project_structure = detect_project_structure(path)

    # Get Python files from source directories only
    files = []
    for src_dir in project_structure.source_dirs:
        src_path = path / src_dir
        if src_path.exists():
            # Filter files respecting gitignore and project structure
            src_files = filter_python_files(src_path, respect_gitignore=True)
            # Additional filtering to exclude test files
            for py_file in src_files:
                if not project_structure.should_exclude_from_logging_analysis(
                    py_file,
                ):
                    files.extend([py_file])

    if not files:
        console.print(f"❌ [red]No files matching pattern '{pattern}' found in {path}")
        return

    results = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for file_path in files:
            if file_path.is_file():
                task = progress.add_task(f"Analyzing {file_path.name}...", total=None)
                result = assistant.analyze_file(file_path)
                results.append(result)
                progress.remove_task(task)

    if json_output:
        console.print(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        _display_directory_analysis(results)


def _transform_single_file(
    assistant: AdvancedAssistant,
    path: Path,
    *,
    dry_run: bool,
    _interactive: bool,
):
    """Transform a single Python file."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Transforming {path.name}...", total=None)
        result = assistant.transform_file(path, dry_run=dry_run)
        progress.remove_task(task)

    _display_transformation_result(result, dry_run)


def _transform_directory(
    assistant: AdvancedAssistant,
    path: Path,
    pattern: str,
    *,
    dry_run: bool,
    _interactive: bool,
):
    """Transform all Python files in a directory."""
    files = list(path.glob(pattern))
    if not files:
        console.print(f"❌ [red]No files matching pattern '{pattern}' found in {path}")
        return

    results = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for file_path in files:
            if file_path.is_file():
                task = progress.add_task(
                    f"Transforming {file_path.name}...",
                    total=None,
                )
                result = assistant.transform_file(file_path, dry_run=dry_run)
                results.append(result)
                progress.remove_task(task)

    _display_directory_transformation(results, dry_run)


def _transform_interactive(path: Path, *, _verbose: bool):
    """Run interactive transformation on a file."""
    transformer = InteractiveTransformer()
    transformer.transform_file_interactive(path)


def _display_patterns(patterns: list[ASTPattern], *, show_details: bool):
    """Display available transformation patterns."""
    table = Table(title="📋 Available Transformation Patterns")
    table.add_column("Name", style="cyan")
    table.add_column("Enabled", style="green")
    table.add_column("Priority", style="magenta", justify="right")

    if show_details:
        table.add_column("Description", style="blue")
        table.add_column("Node Type", style="yellow")

    for pattern in patterns:
        enabled_icon = "✅" if pattern.enabled else "❌"
        row = [pattern.name, enabled_icon, str(pattern.priority)]

        if show_details:
            row.extend([pattern.description, pattern.node_type.value])

        table.add_row(*row)

    console.print(table)


def _display_analysis_result(result: CodeAnalysisResult):
    """Display analysis results for a single file."""
    console.print(
        f"\n📊 [bold blue]Analysis Results for {result.file_path}[/bold blue]",
    )

    # Basic metrics
    metrics_table = Table(title="📈 Code Metrics")
    metrics_table.add_column("Metric", style="cyan")
    metrics_table.add_column("Value", style="green", justify="right")

    metrics_table.add_row("Lines of Code", str(result.lines_of_code))
    metrics_table.add_row("Functions", str(result.function_count))
    metrics_table.add_row("Classes", str(result.class_count))
    metrics_table.add_row("Complexity Score", f"{result.complexity_score:.2f}")

    console.print(metrics_table)

    # Issues found
    if result.issues:
        issues_table = Table(title="⚠️ Issues Found")
        issues_table.add_column("Type", style="red")
        issues_table.add_column("Line", style="yellow", justify="right")
        issues_table.add_column("Description", style="white")

        for i, issue in enumerate(result.issues):
            issues_table.add_row("Issue", str(i + 1), issue)

        console.print(issues_table)
    else:
        console.print("✅ [green]No issues found![/green]")


def _display_transformation_result(result: TransformationResult, *, dry_run: bool):
    """Display transformation results for a single file."""
    mode = "Preview" if dry_run else "Applied"
    console.print(
        f"\n🔄 [bold green]Transformation {mode} for {result.file_path}[/bold green]",
    )

    if result.changes_made:
        changes_table = Table(title=f"📝 Changes {mode}")
        changes_table.add_column("Pattern", style="cyan")
        changes_table.add_column("Line", style="yellow", justify="right")
        changes_table.add_column("Change", style="green")

        for i, change in enumerate(result.changes):
            changes_table.add_row("Change", str(i + 1), change)

        console.print(changes_table)

        if result.transformed_code and dry_run:
            console.print("\n📄 [bold]Transformed Code Preview:[/bold]")
            syntax = Syntax(
                result.transformed_code,
                "python",
                theme="monokai",
                line_numbers=True,
            )
            console.print(syntax)
    else:
        console.print("i [blue]No changes needed[/blue]")


def _display_directory_analysis(results: list[CodeAnalysisResult]):
    """Display analysis results for multiple files."""
    console.print("\n📊 [bold blue]Directory Analysis Summary[/bold blue]")

    summary_table = Table(title="📈 Summary Statistics")
    summary_table.add_column("File", style="cyan")
    summary_table.add_column("LOC", style="green", justify="right")
    summary_table.add_column("Functions", style="blue", justify="right")
    summary_table.add_column("Classes", style="magenta", justify="right")
    summary_table.add_column("Complexity", style="red", justify="right")
    summary_table.add_column("Issues", style="yellow", justify="right")

    total_loc = 0
    total_functions = 0
    total_classes = 0
    total_issues = 0

    for result in results:
        total_loc += result.lines_of_code
        total_functions += result.function_count
        total_classes += result.class_count
        total_issues += len(result.issues)

        summary_table.add_row(
            result.file_path.name,
            str(result.lines_of_code),
            str(result.function_count),
            str(result.class_count),
            f"{result.complexity_score:.1f}",
            str(len(result.issues)),
        )

    # Add totals row
    summary_table.add_row(
        "[bold]TOTAL[/bold]",
        f"[bold]{total_loc}[/bold]",
        f"[bold]{total_functions}[/bold]",
        f"[bold]{total_classes}[/bold]",
        "[bold]-[/bold]",
        f"[bold]{total_issues}[/bold]",
    )

    console.print(summary_table)


def _display_directory_transformation(
    results: list[TransformationResult],
    *,
    dry_run: bool,
):
    """Display transformation results for multiple files."""
    mode = "Preview" if dry_run else "Applied"
    console.print(f"\n🔄 [bold green]Directory Transformation {mode}[/bold green]")

    summary_table = Table(title="📝 Transformation Summary")
    summary_table.add_column("File", style="cyan")
    summary_table.add_column("Changes", style="green", justify="right")
    summary_table.add_column("Status", style="blue")

    total_changes = 0

    for result in results:
        changes_count = len(result.changes)
        total_changes += changes_count
        status = "✅ Modified" if result.changes_made else "INFO No changes"

        summary_table.add_row(result.file_path.name, str(changes_count), status)

    console.print(summary_table)
    console.print(f"\n📊 [bold]Total changes {mode.lower()}: {total_changes}[/bold]")


# Additional CLI commands


@dataclasses.dataclass
class MigrateOptions:
    """Options for the migrate command."""

    path: str = "."
    output: str | None = None
    dry_run: bool = False
    no_ast: bool = False
    pattern: str | None = None
    interactive: bool = False
    verbose: bool = False
    check_imports: bool = False


@app.command()
def migrate(
    path: Annotated[str, typer.Argument(help="Project path to analyze/migrate")] = ".",
    *,
    no_dry_run: Annotated[
        bool,
        typer.Option(
            "--no-dry-run",
            help="Actually apply changes (default: dry-run preview)",
        ),
    ] = False,
    migration_type: Annotated[
        str,
        typer.Option("--type", "-t", help="Migration type"),
    ] = "print-to-structlog",
    json_output: Annotated[
        bool,
        typer.Option("--json", help="JSON output for agents"),
    ] = False,
    output: Annotated[
        str | None,
        typer.Option("--output", "-o", help="Output JSON file or directory"),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Verbose output"),
    ] = False,
    interactive: Annotated[
        bool,
        typer.Option("--interactive", "-i", help="Interactive migration"),
    ] = False,
    force: Annotated[
        bool,
        typer.Option("--force", help="Overwrite existing files"),
    ] = False,
):
    """🔄 Analyze project and migrate code.

    Default behavior: Dry-run preview (safe, shows what would change)

    Examples:
      nicestlog migrate                                   # Dry-run preview of current project
      nicestlog migrate /path/to/project                  # Dry-run preview of specific project
      nicestlog migrate . --json                          # Agent analysis output
      nicestlog migrate . --no-dry-run                    # Actually apply changes
      nicestlog migrate . --no-dry-run --type logging-to-structlog  # Specific migration
      nicestlog migrate . --no-dry-run --interactive      # Interactive migration

    """
    if not no_dry_run:
        # Default behavior: Dry-run preview
        # CRITICAL FIX: Initialize logging before analysis (embarrassing for a logging tool!)
        nicestlog.init_logging(
            verbose=verbose,
            syslog_identifier="nicestlog-migrate",
            log_format="console",
        )

        try:
            result = project_analyzer.analyze_project_for_agents(path, verbose=verbose)

            if json_output or (output and output.endswith(".json")):
                # JSON output for agents or file output
                json_content = result.to_json()

                if output:
                    Path(output).write_text(json_content)
                    console.print(f"✅ [green]Analysis saved to {output}[/green]")
                else:
                    pass
            else:
                # Human-readable output
                _display_project_analysis(result, verbose=verbose)

                # Enhanced user guidance based on analysis
                _display_next_steps_guidance(result, path)

        except Exception as e:
            logger.exception("Analysis failed", error=str(e))
            console.print(f"❌ [red]Analysis failed: {e}[/red]")
            raise typer.Exit(1) from e
    else:
        # Migration behavior: Apply changes
        run_migrate_command(
            path,
            output,
            migration_type,
            dry_run=False,
            interactive=interactive,
            force=force,
        )


# Add demo command to tools
@tools_app.command("demo")
def tools_demo(
    feature: Annotated[
        str | None,
        typer.Argument(help="Demo specific feature"),
    ] = None,
    *,
    all_features: Annotated[
        bool,
        typer.Option("--all", help="Demo all features"),
    ] = False,
):
    """🎬 Run interactive demos."""
    run_demos(feature, all_features=all_features)


# Helper functions for docs display
def _show_markdown_files(filenames: list[str], *, use_pager: bool = False):
    """Show markdown files with rich formatting."""
    # Determine if we're running from source or installed package
    package_root = Path(__file__).parent
    source_docs_path = package_root.parent.parent / "docs"
    source_readme_path = package_root.parent.parent / "README.md"

    # Collect all content first
    all_content = []

    for filename in filenames:
        content = None
        # First try to load from package resources (_docs directory)
        try:
            content = resources.files("nicestlog").joinpath("_docs").joinpath(filename).read_text()
        except (FileNotFoundError, AttributeError):
            # Try alternative paths in package
            try:
                # For README.md, it might be directly in the package
                if filename == "README.md":
                    content = resources.files("nicestlog").joinpath(filename).read_text()
                else:
                    # For other docs, try without _docs prefix
                    content = resources.files("nicestlog").joinpath(filename).read_text()
            except (FileNotFoundError, AttributeError):
                # Try to read from source tree
                try:
                    if filename == "README.md":
                        content = source_readme_path.read_text()
                    else:
                        docs_path = source_docs_path / filename
                        if docs_path.exists():
                            content = docs_path.read_text()
                except (FileNotFoundError, OSError):
                    # Try relative path in current directory
                    try:
                        path = Path(filename)
                        if path.exists():
                            content = path.read_text()
                        else:
                            # Try with _docs prefix for relative paths
                            docs_path = Path("_docs") / filename
                            if docs_path.exists():
                                content = docs_path.read_text()
                    except (FileNotFoundError, OSError):
                        pass

        if content is None:
            console.print(f"❌ [red]File not found: {filename}[/red]")
            continue

        all_content.append(f"📄 {filename}\n{content}")

    # Combine all content
    full_content = "\n\n".join(all_content)

    # Use pager if requested
    if use_pager:
        _display_with_pager(full_content)
    else:
        console.print(full_content)


def _show_docs_interactive(*, use_pager: bool = False):
    """Show interactive documentation browser."""
    console.print("🔍 [bold blue]Interactive Documentation Browser[/bold blue]")
    console.print("Available documentation sections:")
    console.print("1. Getting Started")
    console.print("2. Best Practices")
    console.print("3. Advanced Features")
    console.print("4. API Reference")

    choice = input("\nSelect section (1-4): ")
    docs_map = {
        "1": ["user_guide/getting_started.md"],
        "2": ["user_guide/best_practices.md"],
        "3": ["user_guide/advanced_features.md"],
        "4": ["development/api_reference.rst"],
    }

    if choice in docs_map:
        _show_markdown_files(docs_map[choice], use_pager=use_pager)
    else:
        console.print("❌ [red]Invalid choice[/red]")
        sys.exit(1)


def _show_feature_docs(feature: str, *, use_pager: bool = False):
    """Show documentation for a specific feature."""
    feature_docs = {
        "logging": ["user_guide/getting_started.md"],
        "linting": ["user_guide/best_practices.md"],
        "ast": ["features/advanced_assistant.md"],
        "dashboard": ["features/integrations.md"],
    }

    if feature in feature_docs:
        _show_markdown_files(feature_docs[feature], use_pager=use_pager)
    else:
        console.print(f"❌ [red]No documentation found for feature: {feature}[/red]")


def _display_with_pager(content: str):
    """Display content using an appropriate pager."""
    # Check if glow is available
    glow_path = shutil.which("glow")
    if glow_path is not None:
        # Use glow as pager
        try:
            # Run glow with stdin
            if not Path(glow_path).is_absolute():
                msg = f"Invalid executable path: {glow_path}"
                raise ValueError(msg)
            subprocess.run([glow_path, "--pager", "-"], input=content, text=True, check=False)
        except (subprocess.CalledProcessError, OSError, FileNotFoundError) as e:
            logger.warning("Glow pager failed", exc_info=True, error=str(e))
            console.print(f"❌ [red]Error using glow: {e}[/red]")
            # Fall through to other pagers
        else:
            return

    # Check if bat is available
    bat_path = shutil.which("bat")
    if bat_path is not None:
        try:
            # Run bat with stdin
            if not Path(bat_path).is_absolute():
                msg = f"Invalid executable path: {bat_path}"
                raise ValueError(msg)
            subprocess.run(
                [bat_path, "--paging=always", "-"], input=content, text=True, check=False
            )
        except (subprocess.CalledProcessError, OSError, FileNotFoundError) as e:
            logger.warning("Bat pager failed", exc_info=True, error=str(e))
            console.print(f"❌ [red]Error using bat: {e}[/red]")
            # Fall through to default pager
        else:
            return

    # Fallback to less or more
    pager_cmd = shutil.which("less") or shutil.which("more")
    if pager_cmd:
        try:
            # Run the pager with stdin
            if not Path(pager_cmd).is_absolute():
                msg = f"Invalid executable path: {pager_cmd}"
                raise ValueError(msg)
            subprocess.run([pager_cmd], input=content, text=True, check=False)
        except (subprocess.CalledProcessError, OSError, FileNotFoundError) as e:
            logger.warning("Default pager failed", exc_info=True, error=str(e))
            console.print(f"❌ [red]Error using pager: {e}[/red]")
        else:
            return

    # If no pager is available, just print the content
    console.print(content)


# Implementation stubs for remaining functions


def run_dashboard_cmd(host: str = "127.0.0.1", port: int = 8080, *, debug: bool = False):
    """Run the web dashboard."""
    if not FLASK_AVAILABLE or run_dashboard is None:
        typer.echo(
            "❌ Flask is not installed. The web dashboard requires Flask.\n"
            "Install it with:\n"
            "  pip install 'nicestlog[web]'\n"
            "or\n"
            "  pip install flask>=3.0.3",
            err=True,
        )
        raise typer.Exit(1) from None
    else:
        try:
            run_dashboard(host=host, port=port, debug=debug)
        except ImportError:
            typer.echo(
                "❌ Flask is not installed. The web dashboard requires Flask.\n"
                "Install it with:\n"
                "  pip install 'nicestlog[web]'\n"
                "or\n"
                "  pip install flask>=3.0.3",
                err=True,
            )
            raise typer.Exit(1) from None


def run_journal_viewer(
    unit: str | None = None,
    lines: int = 50,
    *,
    follow: bool = False,
    since: str | None = None,
    level: str | None = None,
):
    """Run the journal viewer."""
    # Check if systemd is available
    if not SYSTEMD_AVAILABLE:
        console.print("[red]Error:[/red] systemd-python not available")
        sys.exit(1)

    viewer = JournalViewer()

    # Query and display entries
    try:
        for _entry in viewer.query_journal(
            service=unit,
            since=since,
            level=level,
            lines=lines,
            follow=follow,
        ):
            pass
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        logger.exception("Application error", error=str(e))
        console.print(f"❌ [red]Error: {e}[/red]")
        sys.exit(1)


def run_log_reviewer(path_str: str, format_type: str = "text", min_score: float = 70.0):
    """Run the log reviewer."""
    reviewer = LogQualityReviewer()

    path = Path(path_str)
    if path.is_file():
        report = reviewer.analyze_log_file(path)
        if format_type == "json":
            # Convert report to dict if it has to_dict method, otherwise use default serialization
            if hasattr(report, "to_dict"):
                report.to_dict()
            else:
                # Handle MagicMock or other objects that don't have to_dict
                {
                    "overall_score": getattr(report, "overall_score", 0.0),
                    "file_path": str(path),
                    "analysis": "Mock analysis",
                }
        else:
            print_report(report, format_type)

        # Check if score is below minimum and exit with error code
        score = getattr(report, "overall_score", 100.0)
        if score < min_score:
            sys.exit(1)

    elif path.is_dir():
        # Analyze all log files in directory
        log_files = list(path.glob("*.log")) + list(path.glob("*.txt"))
        failed_files = 0

        for log_file in log_files:
            report = reviewer.analyze_log_file(log_file)
            score = getattr(report, "overall_score", 100.0)

            if score >= min_score:
                if format_type == "json":
                    if hasattr(report, "to_dict"):
                        report.to_dict()
                    else:
                        {
                            "overall_score": score,
                            "file_path": str(log_file),
                            "analysis": "Mock analysis",
                        }
                else:
                    print_report(report, format_type)
            else:
                failed_files += 1

        if failed_files > 0:
            sys.exit(1)
    else:
        console.print(f"❌ [red]Path {path_str} does not exist[/red]")
        sys.exit(1)


def generate_service_cmd(
    service_name: str,
    exec_command: str,
    user: str | None = None,
    working_directory: str | None = None,
    output_file: str | None = None,
):
    """Generate systemd service file."""
    config = ServiceConfig(
        service_name=service_name,
        exec_command=exec_command,
        user=user,
        working_directory=working_directory,
    )
    service_content = create_systemd_service_file(config)

    if output_file:
        with Path(output_file).open("w") as f:
            f.write(service_content)
        log.info("service-file-generated", service_name=service_name, output_file=output_file)
    else:
        console.print(service_content)


def run_demos(feature: str | None = None, *, all_features: bool = False):
    """Run nicestlog feature demonstrations."""
    log.debug("starting-demos", feature=feature, all_features=all_features)

    available_demos = {
        "basic": "Basic structured logging with console output",
        "i18n": "Internationalization and message translations",
        "pii": "PII scrubbing and data protection",
        "eliot": "Eliot integration for action tracing",
        "systemd": "Systemd journal integration",
        "async": "Asynchronous logging performance",
        "complete": "Complete real-world application example",
        "lint": "Lint demo with two bad modules triggering all checks",
    }

    def print_demo_separator():
        time.sleep(0.5)

    if not feature and not all_features:
        console.print("🎬 [bold blue]Available nicestlog demos:[/bold blue]")
        for demo_name, description in available_demos.items():
            console.print(f"  • [cyan]{demo_name}[/cyan] - {description}")
        console.print("\n💡 [blue]Usage:[/blue]")
        console.print("  [cyan]nicestlog tools demo <feature>[/cyan] - Run specific demo")
        console.print("  [cyan]nicestlog tools demo --all[/cyan] - Run all demos")
        return

    demos_to_run = []
    if all_features:
        # Run all core demos, but skip heavy/side-effect demos like 'lint'
        demos_to_run = [k for k in available_demos if k != "lint"]
    elif feature in available_demos:
        demos_to_run = [feature]
    else:
        console.print(f"Unknown demo: {feature}")
        sys.exit(1)

    for demo_name in demos_to_run:
        if demo_name == "basic":
            run_basic_demo()
        elif demo_name == "i18n":
            run_i18n_demo()
        elif demo_name == "pii":
            run_pii_demo()
        elif demo_name == "eliot":
            run_eliot_demo()
        elif demo_name == "systemd":
            run_systemd_demo()
        elif demo_name == "async":
            run_async_demo()
        elif demo_name == "complete":
            run_complete_demo()
        elif demo_name == "lint":
            run_lint_demo()

        if len(demos_to_run) > 1:
            print_demo_separator()


def print_demo_header(_title: str, _description: str):
    """Print a formatted demo section header."""
    time.sleep(1)


def run_basic_demo():
    """Demonstrate basic nicestlog features."""
    print_demo_header(
        "Basic Structured Logging",
        "Console output with beautiful formatting",
    )

    # Initialize with console output
    nicestlog.init_logging(verbose=True, syslog_identifier="demo")
    log = structlog.get_logger()

    log.info(
        "application-started",
        _replace_msg="🚀 Application {name} v{version} started successfully",
        name="nicestlog-demo",
        version="1.0.0",
        pid=12345,
    )

    log.debug(
        "user-authentication",
        username="alice",
        ip="192.168.1.100",
        session_id="abc123",
        action="login_attempt",
    )

    log.warning(
        "rate-limit-approaching",
        _replace_msg="⚠️  Rate limit at {percent}% for user {user_id}",
        percent=85,
        user_id=42,
        requests_remaining=15,
    )

    log.error(
        "database-connection-failed",
        _replace_msg="💥 Database connection failed: {error}",
        error="Connection timeout",
        host="db.example.com",
        retry_count=3,
        max_retries=5,
    )

    log.debug(
        "api-request-completed",
        _replace_msg="✅ API request completed in {duration}ms",
        method="GET",
        endpoint="/api/users",
        duration=234,
        status_code=200,
        response_size=1024,
    )


def run_i18n_demo():
    """Demonstrate internationalization features."""
    print_demo_header("Internationalization (i18n)", "Multi-language log messages")

    # Load config to optionally honor translation_dir and language from pyproject.toml
    if NicestLogConfig is None:
        logger.warning("Config module not available")
        cfg = None
    else:
        cfg = NicestLogConfig()

    init_kwargs = {"verbose": True, "syslog_identifier": "i18n-demo"}
    if cfg and cfg.translation_dir:
        init_kwargs["translation_dir"] = str(cfg.translation_dir)
    if cfg and cfg.language:
        init_kwargs["language"] = cfg.language

    # Ensure nicestlog is initialized so structlog output uses our renderers
    nicestlog.init_logging(**init_kwargs)
    log = structlog.get_logger()

    log.info("user-login", username="alice", session_id="abc123")
    log.warning("rate-limit-exceeded", user_id=42, limit=100)
    log.error("database-error", error_code="DB001", table="users")


def run_pii_demo():
    """Demonstrate PII scrubbing features."""
    print_demo_header("PII Scrubbing", "Automatic removal of sensitive data")

    nicestlog.init_logging(verbose=True, syslog_identifier="pii-demo")
    log = structlog.get_logger()

    log.info(
        "user-data",
        email="user@example.com",
        password="DEMO_PASSWORD_123",
        ssn="123-45-6789",
    )
    log.debug("api-call", token="Bearer DEMO_TOKEN_456", api_key="sk_demo_abc123")


def run_eliot_demo():
    """Demonstrate Eliot integration."""
    print_demo_header("Eliot Integration", "Action tracing and structured logging")


def run_systemd_demo():
    """Demonstrate systemd integration."""
    print_demo_header("Systemd Integration", "Journal logging and service integration")


def run_async_demo():
    """Demonstrate async logging."""
    # Initialize logging
    nicestlog.init_logging(verbose=True, syslog_identifier="async-demo")
    log = structlog.get_logger()

    # Simulate sync logging
    start_time = time.time()
    for i in range(100):
        log.info("sync-message", iteration=i)
    sync_duration = time.time() - start_time

    # Simulate async logging
    start_time = time.time()
    for i in range(100):
        log.info("async-message", iteration=i)
    async_duration = time.time() - start_time

    # Calculate and display results
    sync_duration / async_duration if async_duration > 0 else 1.0


def run_complete_demo():
    """Demonstrate complete application example."""
    # Initialize logging
    nicestlog.init_logging(verbose=True, syslog_identifier="complete-demo")
    log = structlog.get_logger()

    # Simulate application lifecycle
    log.info("application-startup", version="1.0.0", environment="production")
    time.sleep(0.1)

    log.info("request-received", method="GET", path="/api/users", user_id=123)
    time.sleep(0.1)

    log.info("database-query", table="users", duration_ms=45)
    time.sleep(0.1)

    log.info("request-received", method="GET", path="/api/users", user_id=123)
    time.sleep(0.1)

    log.info("database-query", table="users", duration_ms=45)
    time.sleep(0.1)

    log.debug("request-completed", status_code=200, response_time_ms=156)


def run_lint_demo():
    """Demonstrate linting functionality."""
    print_demo_header("Linting Demo", "Code quality analysis and suggestions")


# Migration Types Configuration
MIGRATION_TYPES = {
    "print-to-structlog": {
        "description": "Convert print statements to structlog calls",
        "handler": "migrate_print_to_structlog",
        "patterns": ["print_statements", "logging_calls"],
    },
    "logging-to-structlog": {
        "description": "Convert standard logging to structlog",
        "handler": "migrate_logging_to_structlog",
        "patterns": ["logging_calls", "logger_imports"],
    },
    "cli-outputs-to-structlog": {
        "description": "Convert CLI framework outputs (typer.echo, click.echo, rich.print) to structlog",
        "handler": "migrate_cli_outputs_to_structlog",
        "patterns": ["cli_output", "print_statements"],
    },
    "format-strings": {
        "description": "Convert f-strings to structured logging",
        "handler": "migrate_format_strings",
        "patterns": ["format_strings", "string_formatting"],
    },
}


def run_migrate_command(options: MigrateOptions, *, migration_type: str, force: bool = False):
    """Execute migration command with comprehensive AST integration."""
    # 1. Validate migration type
    if migration_type not in MIGRATION_TYPES:
        console.print(f"[red]❌ Unknown migration type: {migration_type}[/red]")
        console.print(f"Available types: {', '.join(MIGRATION_TYPES.keys())}")
        console.print("\nMigration types:")
        for mt, config in MIGRATION_TYPES.items():
            console.print(f"  [cyan]{mt}[/cyan] - {config['description']}")
        raise typer.Exit(1)

    migration_config = MIGRATION_TYPES[migration_type]

    # 2. Path validation and setup
    source_path = Path(options.path)
    if not source_path.exists():
        console.print(f"[red]❌ Path {options.path} does not exist[/red]")
        raise typer.Exit(1)

    if options.output:
        target_root = Path(options.output)
        target_root.mkdir(parents=True, exist_ok=True)
        target_path = target_root / source_path.name if source_path.is_file() else target_root
    else:
        target_path = source_path  # In-place migration

    # 3. Display migration info
    console.print(
        Panel.fit(
            f"🔄 [bold blue]Code Migration[/bold blue]\n"
            f"Type: [cyan]{migration_type}[/cyan]\n"
            f"Mode: [yellow]{'Preview' if options.dry_run else 'Apply'}[/yellow]\n"
            f"Source: [green]{source_path}[/green]\n"
            f"Target: [green]{target_path}[/green]",
            title="Migration Configuration",
        ),
    )

    # No backup creation - users should use git for version control

    # 5. Interactive mode
    if options.interactive:
        console.print(
            "🎯 [bold magenta]Starting interactive migration...[/bold magenta]",
        )
        transformer = InteractiveTransformer()
        result = run_interactive_migration(
            transformer,
            source_path,
            target_path,
            migration_config,
            _dry_run=options.dry_run,
        )
        show_migration_report(result, options.dry_run)
        return

    # 6. Automatic migration
    console.print("🚀 [bold blue]Starting automatic migration...[/bold blue]")

    if source_path.is_file():
        result = migrate_single_file(
            source_path,
            target_path,
            migration_config,
            options.dry_run,
            force,
        )
    else:
        result = migrate_directory_recursive(
            source_path,
            target_path,
            migration_config,
            options.dry_run,
            force,
        )

    # 7. Show results
    show_migration_report(result, options.dry_run)

    # 8. Exit with appropriate code
    if result.errors > 0:
        raise typer.Exit(1)


def _handle_analysis_operation(assistant: AdvancedAssistant, source: Path) -> TransformationResult:
    """Handle analysis operation for advanced mode."""
    analysis_result = assistant.analyze_file(source)
    log.debug(
        "migrate-single-file-analysis-completed",
        analysis_result=analysis_result.to_dict(),
        _replace_msg=f"Analysis completed: {analysis_result}",
    )

    return TransformationResult(
        file_path=source,
        changes_made=False,
        changes=[],
        transformed_code="",
        analysis_result=analysis_result,
    )


def _handle_interactive_operation(source: Path) -> TransformationResult:
    """Handle interactive operation for advanced mode."""
    transformer = InteractiveTransformer()
    result = transformer.transform_file_interactive(source)
    log.debug(
        "migrate-single-file-interactive-completed",
        result=result.to_dict() if result else None,
        _replace_msg=f"Interactive transformation completed: {result}",
    )
    return result


def _write_transformed_file(result: TransformationResult, target: Path, *, backup: bool) -> None:
    """Write transformed file to target with optional backup."""
    if not result.changes_made or not result.transformed_code:
        return

    target.parent.mkdir(parents=True, exist_ok=True)

    if backup and target.exists():
        backup_path = target.with_suffix(f"{target.suffix}.backup")
        backup_counter = 1
        while backup_path.exists():
            backup_path = target.with_suffix(f"{target.suffix}.backup.{backup_counter}")
            backup_counter += 1

        shutil.copy2(target, backup_path)
        log.debug("backup-created", backup_path=str(backup_path), _replace_msg=f"Backup created: {backup_path}")

    with target.open("w", encoding="utf-8") as f:
        f.write(result.transformed_code)

    log.debug(
        "migrate-single-file-written",
        target=str(target),
        _replace_msg=f"Transformed file written to: {target}",
    )


def _copy_unchanged_file(source: Path, target: Path) -> None:
    """Copy source to target when no changes were made."""
    if source == target:
        return

    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    log.debug("migrate-single-file-copied", source=str(source), target=str(target))


def migrate_single_file(
    source: Path,
    target: Path,
    config: dict,
    *,
    dry_run: bool,
    _force: bool,
) -> MigrationResultProtocol:
    """Migrate a single file using the appropriate handler."""
    # CLI-outputs-to-Structlog migration (new functionality)
    if config["handler"] == "migrate_cli_outputs_to_structlog":
        try:
            # Read source file
            original_content = source.read_text(encoding="utf-8")

            # Apply CLI output migration
            new_content, changed = migrate_cli_outputs_file(original_content)

            # Create result object compatible with our interface
            class CLIOutputMigrationResult:
                def __init__(self):
                    self.files_processed = 1
                    self.transformations_applied = 1 if changed else 0
                    self.errors = 0
                    self.warnings = []

            result = CLIOutputMigrationResult()

            # Write result if not dry run and changed
            if not dry_run and changed:
                if target != source:
                    # Different target
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(new_content, encoding="utf-8")
                else:
                    # In-place migration
                    source.write_text(new_content, encoding="utf-8")

            # Show diff preview if dry run and changed
            if dry_run and changed:
                DIFF_PREVIEW_LIMIT = 20
                diff_lines = list(
                    difflib.unified_diff(
                        original_content.splitlines(keepends=True),
                        new_content.splitlines(keepends=True),
                        fromfile=str(source),
                        tofile=str(target),
                    ),
                )
                console.print(
                    "\n[bold blue]📄 Preview of CLI output migration:[/bold blue]",
                )
                for line in diff_lines[:DIFF_PREVIEW_LIMIT]:  # Show first DIFF_PREVIEW_LIMIT lines
                    if line.startswith("+"):
                        console.print(f"[green]{line.rstrip()}[/green]")
                    elif line.startswith("-"):
                        console.print(f"[red]{line.rstrip()}[/red]")
                    elif line.startswith("@@"):
                        console.print(f"[cyan]{line.rstrip()}[/cyan]")
                    else:
                        console.print(line.rstrip())
                if len(diff_lines) > DIFF_PREVIEW_LIMIT:
                    console.print(
                        f"[yellow]... and {len(diff_lines) - DIFF_PREVIEW_LIMIT} more lines[/yellow]",
                    )

        except Exception as exc:
            logger.exception("CLI output migration failed", source=str(source), error=str(exc))
            error_msg = str(exc)
            console.print(
                f"[red]❌ Error migrating CLI outputs in {source}: {exc}[/red]",
            )

            class CLIOutputErrorResult:
                def __init__(self):
                    self.files_processed = 1
                    self.transformations_applied = 0
                    self.errors = 1
                    self.warnings = [error_msg]

            return CLIOutputErrorResult()
        else:
            return result

    # Print-to-Structlog migration (existing functionality)
    elif config["handler"] == "migrate_print_to_structlog":
        try:
            # Read source file
            original_content = source.read_text(encoding="utf-8")

            # Apply migration
            new_content, changed = migrate_file(original_content)

            # Create result object compatible with our interface
            # Note: MigrationResult from assistant.py has different fields
            class PrintMigrationResult:
                def __init__(self):
                    self.files_processed = 1
                    self.transformations_applied = 1 if changed else 0
                    self.errors = 0
                    self.warnings = []

            migration_result: MigrationResultProtocol = PrintMigrationResult()

            # Write result if not dry run and changed
            if not dry_run and changed:
                if target != source:
                    # Different target
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(new_content, encoding="utf-8")
                else:
                    # In-place migration
                    source.write_text(new_content, encoding="utf-8")

            # Show diff preview if dry run and changed
            if dry_run and changed:
                DIFF_PREVIEW_LIMIT = 20
                diff_lines = list(
                    difflib.unified_diff(
                        original_content.splitlines(keepends=True),
                        new_content.splitlines(keepends=True),
                        fromfile=str(source),
                        tofile=str(target),
                    ),
                )
                console.print("\n[bold blue]📄 Preview of changes:[/bold blue]")
                for line in diff_lines[:DIFF_PREVIEW_LIMIT]:  # Show first DIFF_PREVIEW_LIMIT lines
                    if line.startswith("+"):
                        console.print(f"[green]{line.rstrip()}[/green]")
                    elif line.startswith("-"):
                        console.print(f"[red]{line.rstrip()}[/red]")
                    elif line.startswith("@@"):
                        console.print(f"[cyan]{line.rstrip()}[/cyan]")
                    else:
                        console.print(line.rstrip())
                if len(diff_lines) > DIFF_PREVIEW_LIMIT:
                    console.print(
                        f"[yellow]... and {len(diff_lines) - DIFF_PREVIEW_LIMIT} more lines[/yellow]",
                    )

        except Exception as exc:
            logger.exception("Print migration failed", source=str(source), error=str(exc))
            error_msg = str(exc)
            console.print(f"[red]❌ Error migrating {source}: {exc}[/red]")

            class PrintMigrationErrorResult:
                def __init__(self):
                    self.files_processed = 1
                    self.transformations_applied = 0
                    self.errors = 1
                    self.warnings = [error_msg]

            return PrintMigrationErrorResult()
        else:
            return migration_result

    # Extended AST migrations using Advanced Assistant
    assistant = AdvancedAssistant()

    # Get patterns for this migration type
    patterns = []
    for pattern_name in config["patterns"]:
        for ast_pattern in assistant.patterns:
            if pattern_name.lower() in ast_pattern.name.lower():
                patterns.append(ast_pattern)

    if not patterns:
        console.print(
            f"[yellow]⚠️ No AST patterns found for {config['handler']}[/yellow]",
        )
        # Fallback to basic analysis
        assistant.analyze_file(source)

        class ASTPatternResult:
            def __init__(self):
                self.files_processed = 1
                self.transformations_applied = 0
                self.errors = 0
                self.warnings = [f"No specific patterns for {config['handler']}"]

        return ASTPatternResult()

    # Apply AST transformations
    try:
        transform_result = assistant.transform_file(source, dry_run=dry_run)

        if not dry_run and transform_result.changes_made and target != source:
            # Copy transformed content to target
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(transform_result.transformed_code)

        class ASTTransformResult:
            def __init__(self):
                self.files_processed = 1
                self.transformations_applied = len(transform_result.changes)
                self.errors = 0
                self.warnings = []

        return ASTTransformResult()

    except Exception as exc:
        logger.exception("AST migration failed", source=str(source), error=str(exc))
        error_msg = str(exc)
        console.print(f"[red]❌ Error migrating {source}: {exc}[/red]")

        class ASTTransformErrorResult:
            def __init__(self):
                self.files_processed = 1
                self.transformations_applied = 0
                self.errors = 1
                self.warnings = [error_msg]

        return ASTTransformErrorResult()


def migrate_directory_recursive(
    source: Path,
    target: Path,
    config: dict,
    *,
    dry_run: bool,
    force: bool,
) -> MigrationResultProtocol:
    """Migrate all Python files in a directory recursively."""
    # For print-to-structlog, use existing directory migration
    if config["handler"] == "migrate_print_to_structlog":
        return migrate_directory(source, target, dry_run)  # type: ignore[return-value]

    # For CLI outputs migration, use custom directory migration
    elif config["handler"] == "migrate_cli_outputs_to_structlog":
        return migrate_directory_with_handler(
            source,
            target,
            migrate_cli_outputs_file,
            dry_run,
        )

    # For other migrations: Process files individually
    python_files = filter_python_files(source, respect_gitignore=True)
    if not python_files:
        console.print(f"[yellow]⚠️ No Python files found in {source}[/yellow]")

        class DirectoryMigrationResult:
            def __init__(self):
                self.files_processed = 0
                self.transformations_applied = 0
                self.errors = 0
                self.warnings = []

        return DirectoryMigrationResult()

    total_files = 0
    total_transformations = 0
    total_errors = 0
    all_warnings = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for py_file in python_files:
            task = progress.add_task(f"Migrating {py_file.name}...", total=None)

            # Calculate target file path
            rel_path = py_file.relative_to(source)
            target_file = target / rel_path if target != source else py_file

            # Migrate individual file
            result = migrate_single_file(py_file, target_file, config, dry_run, force)

            total_files += result.files_processed
            total_transformations += result.transformations_applied
            total_errors += result.errors
            all_warnings.extend(result.warnings)

            progress.remove_task(task)

    class DirectoryRecursiveResult:
        def __init__(self):
            self.files_processed = total_files
            self.transformations_applied = total_transformations
            self.errors = total_errors
            self.warnings = all_warnings

    return DirectoryRecursiveResult()


def run_interactive_migration(
    transformer: InteractiveTransformer,
    source: Path,
    _target: Path,
    config: dict,
    *,  # _dry_run is keyword-only to avoid boolean positional arg
    _dry_run: bool,
) -> MigrationResultProtocol:
    """Run interactive migration using InteractiveTransformer."""
    console.print(f"🎯 Interactive migration: {config['description']}")
    console.print("Use the interactive interface to review and apply changes.")

    try:
        # Start interactive session
        if source.is_file():
            transformer.transform_file_interactive(source)
        else:
            # For directories, process files one by one interactively
            python_files = filter_python_files(source, respect_gitignore=True)
            for py_file in python_files:
                console.print(f"\n📁 Processing: {py_file}")
                transformer.transform_file_interactive(py_file)

        # Return success result (InteractiveTransformer handles its own reporting)
        class InteractiveMigrationResult:
            def __init__(self):
                self.files_processed = 1 if source.is_file() else len(list(source.rglob("*.py")))
                self.transformations_applied = 0  # Interactive mode handles its own counting
                self.errors = 0
                self.warnings = []

        return InteractiveMigrationResult()

    except Exception as exc:
        logger.error("Interactive migration failed", exc_info=True, error=str(exc))
        error_msg = str(exc)
        console.print(f"[red]❌ Interactive migration failed: {exc}[/red]")

        class InteractiveMigrationErrorResult:
            def __init__(self):
                self.files_processed = 0
                self.transformations_applied = 0
                self.errors = 1
                self.warnings = [error_msg]

        return InteractiveMigrationErrorResult()


def migrate_directory_with_handler(
    input_dir: Path,
    output_dir: Path | None,
    migration_handler,
    *,
    dry_run: bool = True,
) -> MigrationResultProtocol:
    """Migrate Python files using a custom migration handler function."""

    class HandlerMigrationResult:
        def __init__(self):
            self.files_processed = 0
            self.transformations_applied = 0
            self.errors = 0
            self.warnings = []
            self.diffs = {}

    result = HandlerMigrationResult()
    input_dir = Path(input_dir)
    if output_dir:
        output_dir = Path(output_dir)

    if not input_dir.exists() or not input_dir.is_dir():
        msg = f"Input directory not found: {input_dir}"
        raise FileNotFoundError(msg)

    for py in filter_python_files(input_dir, respect_gitignore=True):
        try:
            original = py.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as e:
            logger.warning("Failed to read file", file=str(py), error=str(e))
            continue

        try:
            new_code, changed = migration_handler(original)
            result.files_processed += 1

            if not changed:
                # No transformation; in dry-run collect no diff. When writing to separate dir, still mirror original.
                if output_dir is not None and not dry_run:
                    target_path = output_dir / py.relative_to(input_dir)
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    target_path.write_text(original, encoding="utf-8")
                continue

            # If changed, record diff and count transformation
            if changed:
                result.transformations_applied += 1
                diff_lines = list(
                    difflib.unified_diff(
                        original.splitlines(keepends=True),
                        new_code.splitlines(keepends=True),
                        fromfile=str(py),
                        tofile=str(py),
                    ),
                )
                result.diffs[str(py)] = diff_lines

            # Write transformed code only if not dry-run
            if not dry_run:
                target_path = py if output_dir is None else (output_dir / py.relative_to(input_dir))
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_text(new_code, encoding="utf-8")

        except Exception as exc:
            logger.error("File processing failed", exc_info=True, file=str(py), error=str(exc))
            result.errors += 1
            result.warnings.append(f"Error processing {py}: {exc}")

    return result


def show_migration_report(result: MigrationResultProtocol, *, dry_run: bool):
    """Display comprehensive migration results."""
    action = "Would migrate" if dry_run else "Migrated"

    # Main results table
    results_table = Table(title=f"📊 Migration Results ({action})")
    results_table.add_column("Metric", style="cyan")
    results_table.add_column("Count", style="green", justify="right")

    results_table.add_row("Files processed", str(result.files_processed))
    results_table.add_row(
        "Transformations applied",
        str(result.transformations_applied),
    )
    results_table.add_row("Errors", str(result.errors))
    results_table.add_row("Warnings", str(len(result.warnings)))

    console.print(results_table)

    # Show warnings if any
    if result.warnings:
        console.print("\n[yellow]⚠️ Warnings:[/yellow]")
        for warning in result.warnings:
            console.print(f"  • {warning}")

    # Show status message
    if result.errors > 0:
        console.print(
            f"\n[red]❌ Migration completed with {result.errors} errors[/red]",
        )
    elif result.transformations_applied > 0:
        if dry_run:
            console.print(
                f"\n[blue]i Run without --dry-run to apply {result.transformations_applied} changes[/blue]",
            )
        else:
            console.print(
                f"\n[green]✅ Successfully applied {result.transformations_applied} transformations[/green]",
            )
    else:
        console.print(
            "\n[blue]i No changes needed - code is already in target format[/blue]",
        )


def _display_next_steps_guidance(result, path: str):
    """Display helpful next-step guidance based on analysis results."""
    console.print("\n🎯 [bold green]Next Steps & Guidance[/bold green]")

    # Check if config exists
    config_path = Path(path) / "pyproject.toml"
    has_config = config_path.exists()

    if not has_config:
        console.print(
            "📋 [yellow]No pyproject.toml found - initialize configuration first:[/yellow]",
        )
        console.print(f"   [cyan]nicestlog init {path}[/cyan]")
        console.print("")

    # Strategy-specific guidance
    rec = result.recommendation
    if rec.strategy == "cli-outputs-to-structlog":
        console.print("🔄 [blue]CLI Output Migration:[/blue]")
        console.print(
            f"   1. Run interactive migration: [cyan]nicestlog migrate {path} --type cli-outputs-to-structlog --interactive[/cyan]",
        )
        console.print(f"   2. Validate results: [cyan]nicestlog check {path}[/cyan]")
    elif rec.strategy == "print-to-structlog":
        console.print("🔄 [blue]Print-to-Structlog Migration:[/blue]")
        console.print(f"   1. Preview changes: [cyan]nicestlog migrate {path}[/cyan]")
        console.print(
            f"   2. Apply migration: [cyan]nicestlog migrate {path} --no-dry-run[/cyan]",
        )
        console.print(f"   3. Validate results: [cyan]nicestlog check {path}[/cyan]")
    elif rec.strategy == "logging-to-structlog":
        console.print("🔄 [blue]Logging-to-Structlog Migration:[/blue]")
        console.print(
            f"   1. Interactive preview: [cyan]nicestlog migrate {path} --interactive[/cyan]",
        )
        console.print(
            f"   2. Apply changes: [cyan]nicestlog migrate {path} --no-dry-run --type logging-to-structlog[/cyan]",
        )
        console.print(
            f"   3. Update imports: [cyan]nicestlog check {path} --fix[/cyan]",
        )
    elif rec.strategy == "enhancement":
        console.print("✨ [blue]Enhancement Recommendations:[/blue]")
        console.print(f"   1. Check current code: [cyan]nicestlog check {path}[/cyan]")
        console.print(f"   2. Apply fixes: [cyan]nicestlog check {path} --fix[/cyan]")
    else:  # greenfield
        console.print("🌱 [blue]Greenfield Setup:[/blue]")
        console.print(f"   1. Initialize config: [cyan]nicestlog init {path}[/cyan]")
        console.print("   2. Set up logging in your application entry point")

    # Simple guidance without backup noise
    if rec.risk_level == "high":
        console.print("\n⚠️  [yellow]Review changes carefully before applying[/yellow]")
    elif rec.risk_level == "medium":
        console.print("\n💡 [blue]Review changes before applying[/blue]")

    # Prerequisites
    if rec.prerequisites:
        console.print("\n📋 [yellow]Prerequisites:[/yellow]")
        for prereq in rec.prerequisites:
            console.print(f"   • {prereq}")

    console.print("\n💡 [blue]Need help? Run: [cyan]nicestlog --help[/cyan][/blue]")


def _display_project_context(
    project_structure,
    *,
    verbose: bool,
    single_file: Path | None = None,
):
    """Display project context and configuration being used."""
    log = structlog.get_logger()
    log.info("check-project-context", _replace_msg="Project Context")

    # Create context table
    log.info("check-configuration", _replace_msg="Configuration:")
    log.info(
        "check-project-root",
        root=str(project_structure.project_root),
        source=project_structure.detection_source,
        _replace_msg=f"Project Root: {project_structure.project_root} ({project_structure.detection_source})",
    )
    log.info(
        "check-source-dirs",
        dirs=project_structure.source_dirs,
        source=project_structure.detection_source,
        _replace_msg=f"Source Directories: {', '.join(project_structure.source_dirs)} ({project_structure.detection_source})",
    )
    log.info(
        "check-test-dirs",
        dirs=project_structure.test_dirs,
        source=project_structure.detection_source,
        _replace_msg=f"Test Directories: {', '.join(project_structure.test_dirs)} ({project_structure.detection_source})",
    )

    # Show scope information
    if single_file:
        # Single file analysis
        is_excluded = project_structure.should_exclude_from_logging_analysis(
            single_file,
        )
        scope_status = "Excluded from logging analysis" if is_excluded else "Included in logging analysis"
        log.info("check-file-scope", excluded=is_excluded, _replace_msg=f"File Scope: {scope_status}")
        if is_excluded:
            log.info("check-file-excluded", _replace_msg="This file is in a test directory or excluded pattern")
    else:
        # Directory analysis
        log.info("check-analysis-scope", _replace_msg="Analysis Scope:")
        log.info(
            "check-logging-analysis",
            dirs=project_structure.source_dirs,
            _replace_msg=f"  • Logging analysis: Source directories only ({', '.join(project_structure.source_dirs)})",
        )
        log.info("check-excluded-logging", _replace_msg="  • Excluded from logging: Tests and other patterns")
        log.info("check-code-coverage", _replace_msg="  • Code coverage: All Python files (including tests)")

        if verbose:
            MAX_EXCLUDE_PATTERNS_DISPLAY = 5
            log.info("check-exclude-patterns", _replace_msg="Exclude Patterns:")
            for pattern in project_structure.exclude_patterns[:MAX_EXCLUDE_PATTERNS_DISPLAY]:  # Show first 5
                log.info("check-pattern", pattern=pattern, _replace_msg=f"  • {pattern}")
            if len(project_structure.exclude_patterns) > MAX_EXCLUDE_PATTERNS_DISPLAY:
                log.info(
                    "check-more-patterns",
                    more=len(project_structure.exclude_patterns) - MAX_EXCLUDE_PATTERNS_DISPLAY,
                    _replace_msg=f"  • ... and {len(project_structure.exclude_patterns) - MAX_EXCLUDE_PATTERNS_DISPLAY} more",
                )


def _display_project_analysis(result, *, verbose: bool = False):
    """Display human-readable project analysis results."""
    console.print(
        f"\n🔍 [bold blue]Project Analysis: {result.project_path}[/bold blue]",
    )

    # Project Overview
    overview_table = Table(title="📊 Project Overview")
    overview_table.add_column("Metric", style="cyan")
    overview_table.add_column("Value", style="green", justify="right")

    overview_table.add_row("Python Files", str(result.complexity.python_files))
    overview_table.add_row("Total Lines", str(result.complexity.total_lines))

    console.print(overview_table)

    # Logging Patterns
    if result.logging_patterns:
        if verbose:
            # Detailed view: Show all matches with file:line
            console.print(
                f"\n🔍 [bold blue]Detailed Logging Patterns ({len(result.logging_patterns)} total):[/bold blue]"
            )

            # Group by type for better organization
            patterns_by_type = {}
            for pattern in result.logging_patterns:
                if pattern.pattern_type not in patterns_by_type:
                    patterns_by_type[pattern.pattern_type] = []
                patterns_by_type[pattern.pattern_type].append(pattern)

            for pattern_type, patterns in patterns_by_type.items():
                console.print(f"\n[bold cyan]{pattern_type.title()}:[/bold cyan] ({len(patterns)} found)")
                for pattern in patterns:
                    console.print(f"  {pattern.file_path}:{pattern.line_number} - {pattern.code_snippet}")
        else:
            # Summary view: Show aggregated counts
            patterns_table = Table(title="🔍 Logging Patterns Summary")
            patterns_table.add_column("Type", style="cyan")
            patterns_table.add_column("Count", style="yellow", justify="right")
            patterns_table.add_column("Priority", style="red", justify="right")

            pattern_counts = {}
            for pattern in result.logging_patterns:
                pattern_counts[pattern.pattern_type] = pattern_counts.get(pattern.pattern_type, 0) + 1

            for pattern_type, count in pattern_counts.items():
                priority = "High" if pattern_type == "print" else "Medium" if pattern_type == "logging" else "Low"
                patterns_table.add_row(pattern_type.title(), str(count), priority)

            console.print(patterns_table)
            console.print(
                f"\n[dim]💡 Use --verbose to see all {len(result.logging_patterns)} matches with file locations[/dim]"
            )

    # Dependencies
    deps_table = Table(title="📦 Dependencies Analysis")
    deps_table.add_column("Package", style="cyan")
    deps_table.add_column("Status", style="green")

    deps_table.add_row(
        "Standard Logging",
        "✅ Present" if result.dependencies.has_logging else "❌ Missing",
    )
    deps_table.add_row(
        "Structlog",
        "✅ Present" if result.dependencies.has_structlog else "❌ Missing",
    )

    if result.dependencies.has_other_logging:
        deps_table.add_row(
            "Other Logging",
            ", ".join(result.dependencies.has_other_logging),
        )

    console.print(deps_table)

    # Recommendation
    rec = result.recommendation
    rec_panel = Panel.fit(
        f"[bold green]Strategy:[/bold green] {rec.strategy}\n"
        f"[bold yellow]Priority:[/bold yellow] {rec.priority}\n"
        f"[bold blue]Effort:[/bold blue] {rec.estimated_effort}\n"
        f"[bold magenta]Approach:[/bold magenta] {rec.recommended_approach}\n"
        f"[bold red]Risk:[/bold red] {rec.risk_level}",
        title="🎯 Migration Recommendation",
    )
    console.print(rec_panel)

    # Steps
    if rec.steps:
        console.print("\n📋 [bold blue]Recommended Steps:[/bold blue]")
        for step in rec.steps:
            console.print(f"  {step}")

    # Warnings
    if result.warnings:
        console.print("\n[yellow]⚠️ Warnings:[/yellow]")
        for warning in result.warnings:
            console.print(f"  • {warning}")

    # Next Steps are handled by _display_next_steps_guidance - no duplication


def _configure_logging_focused_patterns(
    assistant: AdvancedAssistant,
    user_patterns: list[str] | None = None,
):
    """Configure AST patterns to focus on logging-related issues only."""
    if user_patterns:
        # User specified patterns, don't override
        return

    # Disable general complexity patterns that aren't logging-related
    for pattern in assistant.patterns:
        if pattern.name in ["add_missing_docstrings"]:
            # Keep docstring patterns disabled by default
            pattern.enabled = False
        elif "print" in pattern.name.lower() or "log" in pattern.name.lower():
            # Enable logging-related patterns
            pattern.enabled = True
        else:
            # Keep other patterns as they are
            pass

    log.debug(
        "patterns-configured-for-logging",
        _replace_msg="🎯 Configured AST patterns for logging focus",
        enabled_patterns=[p.name for p in assistant.patterns if p.enabled],
        disabled_patterns=[p.name for p in assistant.patterns if not p.enabled],
    )


def _serve_html_docs(port: int, host: str, *, open_browser: bool, build: bool):
    """Serve HTML documentation using a simple HTTP server."""
    # Try to find HTML docs in different locations
    html_docs_path = None

    # 1. Check local development build
    local_html_path = Path("docs/_build/html")
    if local_html_path.exists() and local_html_path.is_dir():
        html_docs_path = local_html_path
        console.print(f"📁 [green]Found local HTML docs at {local_html_path}[/green]")
    else:
        # 2. Check packaged docs
        try:
            # Try to find the packaged HTML docs
            html_package_path = resources.files("nicestlog").joinpath("_docs_html")
            if html_package_path.is_dir():
                # Extract to temporary directory for serving
                temp_dir = Path(tempfile.mkdtemp(prefix="nicestlog_docs_"))
                shutil.copytree(html_package_path, temp_dir / "html")
                html_docs_path = temp_dir / "html"
                console.print(
                    f"📦 [green]Using packaged HTML docs (extracted to {html_docs_path})[/green]",
                )
        except (ImportError, FileNotFoundError, AttributeError):
            pass

    # 3. Try to build docs if requested and no docs found
    if not html_docs_path and build:
        console.print("🔨 [blue]Building HTML documentation...[/blue]")
        try:
            uv_path = shutil.which("uv")
            if uv_path is None:
                console.print("❌ [red]uv command not found[/red]")
                return

            if not Path(uv_path).is_absolute():
                msg = f"Invalid executable path: {uv_path}"
                raise ValueError(msg)
            subprocess.run(
                [
                    uv_path,
                    "run",
                    "--group",
                    "docs",
                    "sphinx-build",
                    "-b",
                    "html",
                    str(Path("docs").resolve()),
                    str(Path("docs/_build/html").resolve()),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            if local_html_path.exists():
                html_docs_path = local_html_path
                console.print("✅ [green]Documentation built successfully[/green]")
            else:
                console.print("❌ [red]Build completed but HTML docs not found[/red]")
                raise typer.Exit(1)
        except subprocess.CalledProcessError as e:
            console.print(f"❌ [red]Failed to build documentation: {e}[/red]")
            console.print(f"[yellow]Error output: {e.stderr}[/yellow]")
            raise typer.Exit(1) from e
        except FileNotFoundError:
            console.print(
                "❌ [red]uv command not found. Please install uv or build docs manually.[/red]",
            )
            raise typer.Exit(1) from None

    if not html_docs_path:
        console.print("❌ [red]No HTML documentation found.[/red]")
        console.print(
            "💡 [blue]Try running with --build to build docs first, or run:[/blue]",
        )
        console.print(
            "   [cyan]uv run --group docs sphinx-build -b html docs docs/_build/html[/cyan]",
        )
        raise typer.Exit(1)

    # Change to the docs directory
    original_cwd = Path.cwd()
    os.chdir(html_docs_path)

    try:
        # Create HTTP server
        handler = http.server.SimpleHTTPRequestHandler

        # Try to bind to the specified port
        try:
            with socketserver.TCPServer((host, port), handler) as httpd:
                server_url = f"http://{host}:{port}"
                console.print(
                    f"🌐 [bold green]Serving documentation at {server_url}[/bold green]",
                )
                console.print(f"📁 [blue]Serving from: {html_docs_path}[/blue]")
                console.print("Press Ctrl+C to stop the server")

                # Open browser if requested
                if open_browser:

                    def open_browser_delayed():
                        time.sleep(1)  # Give server time to start
                        try:
                            webbrowser.open(server_url)
                            console.print(
                                f"🌍 [green]Opened {server_url} in browser[/green]",
                            )
                        except (OSError, subprocess.CalledProcessError, ImportError) as e:
                            logger.warning("Failed to open browser", error=str(e))
                            console.print(
                                f"⚠️ [yellow]Could not open browser: {e}[/yellow]",
                            )
                            console.print(
                                f"💡 [blue]Please open {server_url} manually[/blue]",
                            )

                    browser_thread = threading.Thread(target=open_browser_delayed)
                    browser_thread.daemon = True
                    browser_thread.start()

                # Start serving
                httpd.serve_forever()

        except OSError as e:
            if "Address already in use" in str(e):
                console.print(f"❌ [red]Port {port} is already in use[/red]")
                console.print("💡 [blue]Try a different port with --port[/blue]")
            else:
                console.print(f"❌ [red]Failed to start server: {e}[/red]")
            raise typer.Exit(1) from e

    except KeyboardInterrupt:
        console.print("\n👋 [blue]Server stopped[/blue]")
    finally:
        os.chdir(original_cwd)


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
