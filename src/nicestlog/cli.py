"""
Command-line interface for nicestlog.

This module provides the complete CLI interface including both basic and advanced
AST functionality, previously split between cli.py and cli_advanced.py.
"""

from __future__ import annotations

import sys
import time
import os
from pathlib import Path
from typing import Annotated, Optional, List

import typer
import structlog
import nicestlog
import importlib.resources as resources
from colorama import Fore, Style
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax

from .advanced_assistant import (
    AdvancedAssistant,
    ASTPattern,
    TransformationResult,
    CodeAnalysisResult,
)
from .interactive_transformer import (
    InteractiveTransformer,
)

# Initialize logging and console
log = structlog.get_logger(__name__)
console = Console()

# Main app
app = typer.Typer(help="Nicestlog utility.", no_args_is_help=True)

# Create tools subgroup for low-level utilities
tools_app = typer.Typer(help="🛠️ Low-level utilities and advanced tools")
app.add_typer(tools_app, name="tools")

# Sub-app for i18n related commands
i18n_app = typer.Typer(help="Internationalization utilities")
app.add_typer(i18n_app, name="i18n")

# Create AST subcommand group under tools
ast_app = typer.Typer(help="🔬 Advanced AST analysis and transformation")
tools_app.add_typer(ast_app, name="ast")


def init_config():
    """Interactive wizard to create a [tool.nicestlog] section in pyproject.toml."""
    log.debug("starting-config-wizard")
    print("Nicestlog Configuration Wizard")
    print(
        "This will help you create a `[tool.nicestlog]` section in your pyproject.toml."
    )

    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        log.error("pyproject-not-found", path=str(pyproject_path.resolve()))
        print(f"Error: {pyproject_path.resolve()} not found.", file=sys.stderr)
        print("Please run this command in the root of your project.", file=sys.stderr)
        sys.exit(1)

    config = {}
    print("\n--- General Settings ---")
    config["verbose"] = (
        input("Enable verbose (trace-level) logging? [y/N]: ").lower() == "y"
    )
    config["syslog_identifier"] = (
        input("Syslog identifier [nicestlog]: ") or "nicestlog"
    )
    config["log_format"] = input("Log format (console/json) [console]: ") or "console"
    config["async_logging"] = (
        input("Enable asynchronous (non-blocking) logging? [y/N]: ").lower() == "y"
    )

    print("\n--- File Logging ---")
    if input("Enable file logging? [y/N]: ").lower() == "y":
        config["log_file"] = input("Log file path [app.log]: ") or "app.log"
        config["log_file_max_size"] = int(
            input("Max log file size in MB [10]: ") or "10"
        )
        config["log_file_backup_count"] = int(
            input("Number of backup files to keep [3]: ") or "3"
        )

    print("\n--- Structured Logging ---")
    config["enable_structured_logging"] = (
        input("Enable structured logging? [Y/n]: ").lower() != "n"
    )
    if config["enable_structured_logging"]:
        config["structured_format"] = (
            input("Structured format (json/key_value) [json]: ") or "json"
        )

    print("\n--- Performance ---")
    config["enable_performance_monitoring"] = (
        input("Enable performance monitoring? [y/N]: ").lower() == "y"
    )

    # Write config to pyproject.toml
    import toml

    try:
        with open(pyproject_path, "r") as f:
            pyproject = toml.load(f)
    except Exception:
        pyproject = {}

    if "tool" not in pyproject:
        pyproject["tool"] = {}
    pyproject["tool"]["nicestlog"] = config

    with open(pyproject_path, "w") as f:
        toml.dump(pyproject, f)

    print(f"\n✅ Configuration written to {pyproject_path}")
    print("You can now use nicestlog with your custom settings!")
    log.info("config-wizard-completed", config=config)


@app.command()
def docs(
    interactive: Annotated[
        bool, typer.Option("--interactive", "-i", help="Interactive docs browser")
    ] = False,
    feature: Annotated[
        Optional[str], typer.Option("--feature", "-f", help="Show docs for specific feature")
    ] = None,
):
    """📚 Show documentation and examples."""
    if interactive:
        _show_docs_interactive()
    elif feature:
        _show_feature_docs(feature)
    else:
        _show_markdown_files([
            "README.md",
            "docs/user_guide/getting_started.md",
            "docs/user_guide/best_practices.md"
        ])


@app.command("init")
def init_config_cmd():
    """🔧 Initialize nicestlog configuration."""
    init_config()


@app.command()
def check(
    path: Annotated[str, typer.Argument(help="Path to check")] = ".",
    fix: Annotated[bool, typer.Option("--fix", help="Auto-fix issues")] = False,
    interactive: Annotated[bool, typer.Option("--interactive", "-i", help="Interactive mode")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Show what would be fixed")] = False,
):
    """🔍 Check code for logging best practices."""
    from .linter import lint_directory
    
    path_obj = Path(path)
    if not path_obj.exists():
        print(f"❌ Path {path} does not exist", file=sys.stderr)
        sys.exit(1)
    
    if fix:
        if interactive:
            print("🔧 Interactive fixing mode")
        elif dry_run:
            print("🔍 Dry run mode - showing what would be fixed")
        else:
            print("🔧 Auto-fixing issues")
    
    lint_directory(path_obj, fix=fix, interactive=interactive, dry_run=dry_run)


# AST Commands
@ast_app.command("analyze")
def ast_analyze(
    path: Path = typer.Argument(..., help="Python file or directory to analyze"),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging"
    ),
    json_output: bool = typer.Option(
        False, "--json", "-j", help="Output results as JSON"
    ),
    pattern: str = typer.Option(
        "*.py", "--pattern", "-p", help="File pattern for directories"
    ),
):
    """
    🔍 Perform deep AST analysis of Python code.

    Analyzes code structure, complexity, patterns, and potential issues.
    """
    console.print(
        Panel.fit(
            "🔍 [bold blue]Advanced AST Analysis[/bold blue]",
            subtitle=f"Analyzing: {path}",
        )
    )

    assistant = AdvancedAssistant(verbose=verbose)

    if path.is_file():
        _analyze_single_file(assistant, path, json_output)
    elif path.is_dir():
        _analyze_directory(assistant, path, pattern, json_output)
    else:
        console.print(f"❌ [red]Error:[/red] Path {path} does not exist")
        raise typer.Exit(1)


@ast_app.command("transform")
def ast_transform(
    path: Path = typer.Argument(..., help="Python file or directory to transform"),
    dry_run: bool = typer.Option(
        True, "--dry-run/--apply", help="Preview changes without applying"
    ),
    interactive: bool = typer.Option(
        False,
        "--interactive",
        "-i",
        help="Interactive mode with user confirmation",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging"
    ),
    pattern: str = typer.Option(
        "*.py", "--pattern", "-p", help="File pattern for directories"
    ),
    enable_patterns: Optional[List[str]] = typer.Option(
        None, "--enable", help="Enable specific patterns"
    ),
    disable_patterns: Optional[List[str]] = typer.Option(
        None, "--disable", help="Disable specific patterns"
    ),
):
    """
    🔄 Transform Python code using AST patterns.

    Applies intelligent transformations to improve code quality and logging.
    """
    console.print(
        Panel.fit(
            "🔄 [bold green]AST Code Transformation[/bold green]",
            subtitle=f"Target: {path} | Mode: {'Preview' if dry_run else 'Apply'}",
        )
    )

    assistant = AdvancedAssistant(verbose=verbose)

    # Configure patterns
    if enable_patterns:
        assistant.enable_patterns(enable_patterns)
    if disable_patterns:
        assistant.disable_patterns(disable_patterns)

    if path.is_file():
        _transform_single_file(assistant, path, dry_run, interactive)
    elif path.is_dir():
        _transform_directory(assistant, path, pattern, dry_run, interactive)
    else:
        console.print(f"❌ [red]Error:[/red] Path {path} does not exist")
        raise typer.Exit(1)


@ast_app.command("interactive")
def ast_interactive(
    path: Path = typer.Argument(..., help="Python file to transform interactively"),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging"
    ),
):
    """
    🎯 Interactive AST transformation with real-time preview.

    Provides an amber-style interactive interface for code transformation.
    """
    if not path.is_file():
        console.print(f"❌ [red]Error:[/red] Path {path} must be a file")
        raise typer.Exit(1)

    console.print(
        Panel.fit(
            "🎯 [bold magenta]Interactive AST Transformation[/bold magenta]",
            subtitle=f"File: {path}",
        )
    )

    _transform_interactive(path, verbose)


@ast_app.command("patterns")
def ast_patterns(
    show_details: bool = typer.Option(
        False, "--details", "-d", help="Show detailed pattern information"
    ),
):
    """
    📋 List available AST transformation patterns.

    Shows all available patterns with their status and descriptions.
    """
    assistant = AdvancedAssistant()
    patterns = assistant.get_available_patterns()
    _display_patterns(patterns, show_details)


# Helper functions for AST operations
def _analyze_single_file(
    assistant: AdvancedAssistant, path: Path, json_output: bool
):
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
        import json
        console.print(json.dumps(result.to_dict(), indent=2))
    else:
        _display_analysis_result(result)


def _analyze_directory(
    assistant: AdvancedAssistant, path: Path, pattern: str, json_output: bool
):
    """Analyze all Python files in a directory."""
    import glob
    
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
                task = progress.add_task(f"Analyzing {file_path.name}...", total=None)
                result = assistant.analyze_file(file_path)
                results.append(result)
                progress.remove_task(task)

    if json_output:
        import json
        console.print(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        _display_directory_analysis(results)


def _transform_single_file(
    assistant: AdvancedAssistant, path: Path, dry_run: bool, interactive: bool
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
    assistant: AdvancedAssistant, path: Path, pattern: str, dry_run: bool, interactive: bool
):
    """Transform all Python files in a directory."""
    import glob
    
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
                task = progress.add_task(f"Transforming {file_path.name}...", total=None)
                result = assistant.transform_file(file_path, dry_run=dry_run)
                results.append(result)
                progress.remove_task(task)

    _display_directory_transformation(results, dry_run)


def _transform_interactive(path: Path, verbose: bool):
    """Run interactive transformation on a file."""
    transformer = InteractiveTransformer(verbose=verbose)
    transformer.run(path)


def _display_patterns(patterns: List[ASTPattern], show_details: bool):
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
    console.print(f"\n📊 [bold blue]Analysis Results for {result.file_path}[/bold blue]")
    
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
        
        for issue in result.issues:
            issues_table.add_row(issue.type, str(issue.line), issue.description)
        
        console.print(issues_table)
    else:
        console.print("✅ [green]No issues found![/green]")


def _display_transformation_result(result: TransformationResult, dry_run: bool):
    """Display transformation results for a single file."""
    mode = "Preview" if dry_run else "Applied"
    console.print(f"\n🔄 [bold green]Transformation {mode} for {result.file_path}[/bold green]")
    
    if result.changes_made:
        changes_table = Table(title=f"📝 Changes {mode}")
        changes_table.add_column("Pattern", style="cyan")
        changes_table.add_column("Line", style="yellow", justify="right")
        changes_table.add_column("Change", style="green")
        
        for change in result.changes:
            changes_table.add_row(change.pattern, str(change.line), change.description)
        
        console.print(changes_table)
        
        if result.transformed_code and dry_run:
            console.print("\n📄 [bold]Transformed Code Preview:[/bold]")
            syntax = Syntax(result.transformed_code, "python", theme="monokai", line_numbers=True)
            console.print(syntax)
    else:
        console.print("ℹ️ [blue]No changes needed[/blue]")


def _display_directory_analysis(results: List[CodeAnalysisResult]):
    """Display analysis results for multiple files."""
    console.print(f"\n📊 [bold blue]Directory Analysis Summary[/bold blue]")
    
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
            str(len(result.issues))
        )
    
    # Add totals row
    summary_table.add_row(
        "[bold]TOTAL[/bold]",
        f"[bold]{total_loc}[/bold]",
        f"[bold]{total_functions}[/bold]",
        f"[bold]{total_classes}[/bold]",
        "[bold]-[/bold]",
        f"[bold]{total_issues}[/bold]"
    )
    
    console.print(summary_table)


def _display_directory_transformation(results: List[TransformationResult], dry_run: bool):
    """Display transformation results for multiple files."""
    mode = "Preview" if dry_run else "Applied"
    console.print(f"\n🔄 [bold green]Directory Transformation {mode}[/bold green]")
    
    summary_table = Table(title=f"📝 Transformation Summary")
    summary_table.add_column("File", style="cyan")
    summary_table.add_column("Changes", style="green", justify="right")
    summary_table.add_column("Status", style="blue")
    
    total_changes = 0
    
    for result in results:
        changes_count = len(result.changes)
        total_changes += changes_count
        status = "✅ Modified" if result.changes_made else "ℹ️ No changes"
        
        summary_table.add_row(
            result.file_path.name,
            str(changes_count),
            status
        )
    
    console.print(summary_table)
    console.print(f"\n📊 [bold]Total changes {mode.lower()}: {total_changes}[/bold]")


# Additional CLI commands
@app.command()
def lint(
    path: Annotated[str, typer.Argument(help="Path to lint")] = ".",
    min_coverage: Annotated[float, typer.Option("--min-coverage", help="Minimum coverage")] = 70.0,
    max_coverage: Annotated[float, typer.Option("--max-coverage", help="Maximum coverage")] = 90.0,
):
    """🔍 Lint code for logging best practices."""
    run_linter(path, min_coverage, max_coverage)


@app.command()
def dashboard(
    host: Annotated[str, typer.Option("--host", help="Host to bind to")] = "127.0.0.1",
    port: Annotated[int, typer.Option("--port", help="Port to bind to")] = 8080,
    debug: Annotated[bool, typer.Option("--debug", help="Debug mode")] = False,
):
    """🌐 Launch web dashboard."""
    run_dashboard_cmd(host, port, debug)


@app.command()
def journal(
    follow: Annotated[bool, typer.Option("--follow", "-f", help="Follow log output")] = False,
    unit: Annotated[Optional[str], typer.Option("--unit", "-u", help="Systemd unit")] = None,
):
    """📖 View systemd journal logs."""
    run_journal_viewer(follow, unit)


@app.command()
def review(
    path: Annotated[str, typer.Argument(help="Path to review")],
    format_type: Annotated[str, typer.Option("--format", help="Output format")] = "text",
    min_score: Annotated[float, typer.Option("--min-score", help="Minimum score")] = 70.0,
):
    """📝 Review log files for quality."""
    run_log_reviewer(path, format_type, min_score)


@app.command()
def demo(
    feature: Annotated[Optional[str], typer.Option("--feature", help="Demo specific feature")] = None,
    all_features: Annotated[bool, typer.Option("--all", help="Demo all features")] = False,
):
    """🎬 Run interactive demos."""
    run_demos(feature, all_features)


# Helper functions for docs display
def _show_markdown_files(filenames: list[str]):
    """Show markdown files with rich formatting."""
    for filename in filenames:
        try:
            if resources.files("nicestlog").joinpath(filename).exists():
                content = resources.files("nicestlog").joinpath(filename).read_text()
            else:
                # Try relative path
                path = Path(filename)
                if path.exists():
                    content = path.read_text()
                else:
                    console.print(f"❌ [red]File not found: {filename}[/red]")
                    continue
            
            console.print(f"\n📄 [bold blue]{filename}[/bold blue]")
            console.print(content)
        except Exception as e:
            console.print(f"❌ [red]Error reading {filename}: {e}[/red]")


def _show_docs_interactive():
    """Show interactive documentation browser."""
    console.print("🔍 [bold blue]Interactive Documentation Browser[/bold blue]")
    console.print("Available documentation sections:")
    console.print("1. Getting Started")
    console.print("2. Best Practices") 
    console.print("3. Advanced Features")
    console.print("4. API Reference")
    
    choice = input("\nSelect section (1-4): ")
    docs_map = {
        "1": ["docs/user_guide/getting_started.md"],
        "2": ["docs/user_guide/best_practices.md"],
        "3": ["docs/user_guide/advanced_features.md"],
        "4": ["docs/development/api_reference.rst"]
    }
    
    if choice in docs_map:
        _show_markdown_files(docs_map[choice])
    else:
        console.print("❌ [red]Invalid choice[/red]")


def _show_feature_docs(feature: str):
    """Show documentation for a specific feature."""
    feature_docs = {
        "logging": ["docs/user_guide/getting_started.md"],
        "linting": ["docs/user_guide/best_practices.md"],
        "ast": ["docs/features/advanced_assistant.md"],
        "dashboard": ["docs/features/integrations.md"]
    }
    
    if feature in feature_docs:
        _show_markdown_files(feature_docs[feature])
    else:
        console.print(f"❌ [red]No documentation found for feature: {feature}[/red]")


# Implementation stubs for remaining functions
def run_linter(path: str, min_coverage: float = 70.0, max_coverage: float = 90.0):
    """Run the linter."""
    from .linter import lint_directory
    lint_directory(Path(path), min_coverage=min_coverage, max_coverage=max_coverage)


def run_dashboard_cmd(host: str = "127.0.0.1", port: int = 8080, debug: bool = False):
    """Run the web dashboard."""
    from .web_dashboard import run_dashboard
    run_dashboard(host=host, port=port, debug=debug)


def run_journal_viewer(follow: bool = False, unit: Optional[str] = None):
    """Run the journal viewer."""
    from .journal_viewer import JournalViewer
    viewer = JournalViewer()
    viewer.run(follow=follow, unit=unit)


def run_log_reviewer(path_str: str, format_type: str = "text", min_score: float = 70.0):
    """Run the log reviewer."""
    from .log_reviewer import LogReviewer
    reviewer = LogReviewer()
    reviewer.review_path(Path(path_str), format_type=format_type, min_score=min_score)


def run_demos(feature: Optional[str] = None, all_features: bool = False):
    """Run demos."""
    console.print("🎬 [bold blue]Nicestlog Demos[/bold blue]")
    if feature:
        console.print(f"Running demo for: {feature}")
    elif all_features:
        console.print("Running all feature demos")
    else:
        console.print("Available demos: basic, advanced, ast, linting")


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()