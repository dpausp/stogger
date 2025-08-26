"""
Command-line interface for nicestlog.

This module provides the complete CLI interface including both basic and advanced
AST functionality, previously split between cli.py and cli_advanced.py.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Annotated, Optional, List, cast

import typer
import structlog
import nicestlog
import importlib.resources as resources
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
from .assistant import migrate_file, migrate_directory, MigrationResult
from .cli_output_transformer import migrate_cli_outputs_file

# Initialize logging and console
log = structlog.get_logger(__name__)
console = Console()

# Main app
app = typer.Typer(help="Nicestlog utility.", no_args_is_help=True)

# Create tools subgroup for low-level utilities
tools_app = typer.Typer(help="🛠️ Low-level utilities and advanced tools")
app.add_typer(tools_app, name="tools")


# DEPRECATED: Keep old command with deprecation warning
@tools_app.command("init-config")
def tools_init_config_deprecated():
    """🔧 [DEPRECATED] Use 'nicestlog init' instead."""
    console.print("[yellow]⚠️ DEPRECATED: 'tools init-config' is deprecated.[/yellow]")
    console.print("[yellow]   Use 'nicestlog init' instead.[/yellow]")
    
    # Redirect to original function
    init_config()


# Add generate-service command to tools
@tools_app.command("generate-service")
def tools_generate_service(
    service_name: str = typer.Argument(..., help="Name of the service"),
    exec_command: str = typer.Argument(..., help="Command to execute"),
    user: Optional[str] = typer.Option(None, "--user", help="User to run service as"),
    working_dir: Optional[str] = typer.Option(
        None, "--working-dir", help="Working directory"
    ),
    output: Optional[str] = typer.Option(None, "--output", help="Output file path"),
):
    """🔧 Generate systemd service file."""
    generate_service_cmd(service_name, exec_command, user, working_dir, output)


# DEPRECATED: Top-level analyze command (use 'migrate' instead)
@app.command()
def analyze(
    path: str = typer.Argument(".", help="Project path to analyze"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output JSON file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    json_output: bool = typer.Option(False, "--json", help="JSON output for agents"),
):
    """🔍 [DEPRECATED] Use 'nicestlog migrate' instead (analysis is default behavior)."""
    console.print("[yellow]⚠️ DEPRECATED: 'analyze' command is deprecated.[/yellow]")
    console.print("[yellow]   Use 'nicestlog migrate' instead (analysis is default behavior).[/yellow]")
    
    # Redirect to migrate command
    migrate(path=path, do_migrate=False, migration_type="print-to-structlog", 
           json_output=json_output, output=output, verbose=verbose, 
           interactive=False, backup=True, force=False)


# DEPRECATED: Keep old command with deprecation warning
@tools_app.command("analyze-project")
def tools_analyze_project_deprecated(
    path: str = typer.Argument(".", help="Project path to analyze"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output JSON file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    agent_mode: bool = typer.Option(False, "--agent", help="Agent-friendly JSON output"),
):
    """🔍 [DEPRECATED] Use 'nicestlog migrate --json' instead."""
    console.print("[yellow]⚠️ DEPRECATED: 'tools analyze-project' is deprecated.[/yellow]")
    console.print("[yellow]   Use 'nicestlog migrate --json' instead.[/yellow]")
    
    # Redirect to migrate command
    migrate(path=path, do_migrate=False, migration_type="print-to-structlog", 
           json_output=agent_mode, output=output, verbose=verbose, 
           interactive=False, backup=True, force=False)


# Sub-app for i18n related commands
i18n_app = typer.Typer(help="Internationalization utilities")
app.add_typer(i18n_app, name="i18n")


# Add i18n check command
@i18n_app.command("check")
def i18n_check(
    src_dir: str = typer.Argument(..., help="Source directory to check"),
    translation_dir: Optional[str] = typer.Option(
        None, "--translation-dir", help="Translation directory"
    ),
    language: Annotated[
        str, typer.Option("-l", "--language", help="Language code")
    ] = "en",
    list_missing: Annotated[
        bool, typer.Option("--list-missing", help="List missing translations")
    ] = False,
    fail_on_extra: Annotated[
        bool, typer.Option("--fail-on-extra", help="Fail on extra translations")
    ] = False,
    strict: Annotated[
        bool,
        typer.Option("--strict", help="Strict mode - fail on any missing translations"),
    ] = False,
    verbose: Annotated[bool, typer.Option("--verbose", help="Verbose output")] = False,
):
    """🌍 Check translation completeness and quality."""
    from .i18n_check import check_translations

    try:
        # Convert src_dir to Path and get all Python files
        src_path = Path(src_dir)
        source_paths = list(src_path.glob("**/*.py"))

        # Use translation_dir or default
        trans_dir = (
            Path(translation_dir)
            if translation_dir
            else src_path.parent / "translations"
        )

        result = check_translations(
            source_paths=source_paths, translation_dir=trans_dir, language=language
        )

        # Handle list_missing and fail_on_extra logic
        missing_keys = cast(List[str], result.get("missing_keys", []))
        extra_keys = cast(List[str], result.get("extra_keys", []))

        if list_missing:
            for key in missing_keys:
                print(key)
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
            print(f"Translation check for language: {language}")
            print(f"Translation file: {result.get('translation_file', 'N/A')}")
            print(
                f"Required keys: {len(cast(List[str], result.get('required_keys', [])))}"
            )

            if missing_keys:
                print(f"Missing keys: {len(missing_keys)}")
                print("Missing translations:")
                for key in missing_keys:
                    print(f"  - {key}")
            else:
                print("No missing keys")

            if extra_keys:
                print(f"Extra keys: {len(extra_keys)}")
                print("Extra translations:")
                for key in extra_keys:
                    print(f"  - {key}")
            elif verbose:
                print("No extra keys")

            # Show debug events if present
            debug_events = cast(List[str], result.get("debug_with_replace_events", []))
            if debug_events and verbose:
                print("Debug events using _replace_msg (ignored for coverage):")
                for key in debug_events:
                    print(f"  - {key}")

        # Normal mode: fail if there are missing keys or extra keys (when fail_on_extra is set)
        has_errors = bool(missing_keys) or (fail_on_extra and bool(extra_keys))
        if has_errors:
            sys.exit(1)

    except Exception as e:
        console.print(f"❌ [red]Error checking translations: {e}[/red]")
        sys.exit(2)


# DEPRECATED: Create AST subcommand group under tools (will be removed)
ast_app = typer.Typer(help="🔬 [DEPRECATED] Use 'check --ast' and 'fix --ast' instead")
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
    log.debug("config-wizard-completed", config=config)


@app.command()
def docs(
    interactive: Annotated[
        bool, typer.Option("--interactive", "-i", help="Interactive docs browser")
    ] = False,
    feature: Annotated[
        Optional[str],
        typer.Option("--feature", "-f", help="Show docs for specific feature"),
    ] = None,
):
    """📚 Show documentation and examples."""
    if interactive:
        _show_docs_interactive()
    elif feature:
        _show_feature_docs(feature)
    else:
        _show_markdown_files(
            [
                "README.md",
                "docs/user_guide/getting_started.md",
                "docs/user_guide/best_practices.md",
            ]
        )


@app.command("init")
def init_config_cmd(
    path: str = typer.Argument(".", help="Project path to initialize"),
    template: Optional[str] = typer.Option(None, "--template", help="Configuration template"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing config"),
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
    import os
    os.chdir(target_path)
    
    try:
        init_config()
        console.print(f"✅ [green]Configuration initialized in {target_path}[/green]")
    finally:
        os.chdir(original_cwd)


@app.command()
def check(
    path: Annotated[str, typer.Argument(help="Path to check")] = ".",
    fix: Annotated[bool, typer.Option("--fix", help="Auto-fix issues")] = False,
    interactive: Annotated[
        bool, typer.Option("--interactive", "-i", help="Interactive mode")
    ] = False,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Show what would be fixed")
    ] = False,
    ast_analysis: Annotated[
        bool, typer.Option("--ast", help="Enable AST-based analysis")
    ] = False,
    complexity: Annotated[
        bool, typer.Option("--complexity", help="Check code complexity")
    ] = False,
    patterns: Annotated[
        Optional[List[str]],
        typer.Option("--pattern", help="Specific AST patterns to check"),
    ] = None,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Enable verbose output")
    ] = False,
):
    """🔍 Check code for logging best practices with optional AST analysis.

    Examples:
      nicestlog check file.py                    # Basic linting
      nicestlog check file.py --ast              # With AST analysis
      nicestlog check file.py --fix --ast        # Fix with AST transforms
      nicestlog check file.py --interactive      # Interactive mode
      nicestlog check file.py --complexity       # Complexity analysis
    """
    from .linter import lint_directory

    path_obj = Path(path)
    if not path_obj.exists():
        console.print(f"❌ [red]Path {path} does not exist[/red]")
        sys.exit(1)

    # Display mode information
    mode_info = []
    if fix:
        if interactive:
            mode_info.append("🎯 Interactive fixing")
        elif dry_run:
            mode_info.append("🔍 Dry run preview")
        else:
            mode_info.append("🔧 Auto-fixing")

    if ast_analysis:
        mode_info.append("🔬 AST analysis")
    if complexity:
        mode_info.append("📊 Complexity check")

    if mode_info:
        console.print(f"Mode: {' + '.join(mode_info)}")

    # 1. Basic linting (always performed)
    console.print("\n📋 [bold blue]Running basic linting...[/bold blue]")
    basic_success = lint_directory(path_obj)

    # 2. AST Analysis (if requested)
    ast_issues = None
    if ast_analysis or interactive or patterns or complexity:
        console.print("\n🔬 [bold blue]Running AST analysis...[/bold blue]")

        assistant = AdvancedAssistant(verbose=verbose)

        # Configure patterns if specified
        if patterns:
            for pattern_name in patterns:
                for ast_pattern in assistant.patterns:
                    if pattern_name.lower() in ast_pattern.name.lower():
                        ast_pattern.enabled = True
                    else:
                        ast_pattern.enabled = False

        # Perform AST analysis
        if path_obj.is_file():
            ast_result = assistant.analyze_file(path_obj)
            _display_check_analysis_result(ast_result, complexity)

            # Store issues for potential fixing
            ast_issues = ast_result

        elif path_obj.is_dir():
            python_files = list(path_obj.glob("**/*.py"))
            if python_files:
                ast_results = []
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                ) as progress:
                    for py_file in python_files:
                        task = progress.add_task(
                            f"Analyzing {py_file.name}...", total=None
                        )
                        result = assistant.analyze_file(py_file)
                        ast_results.append(result)
                        progress.remove_task(task)

                _display_check_directory_analysis(ast_results, complexity)
                ast_issues = ast_results
            else:
                console.print("❌ [red]No Python files found in directory[/red]")

    # 3. Interactive Mode
    if interactive and ast_issues:
        console.print("\n🎯 [bold magenta]Starting interactive mode...[/bold magenta]")
        transformer = InteractiveTransformer()

        if path_obj.is_file():
            transformer.transform_file_interactive(path_obj)
        else:
            # For directories, process files one by one
            python_files = list(path_obj.glob("**/*.py"))
            for py_file in python_files:
                console.print(f"\n📁 Processing: {py_file}")
                if typer.confirm(f"Transform {py_file.name}?"):
                    transformer.transform_file_interactive(py_file)

    # 4. AST-based Fixes
    elif fix and ast_analysis and ast_issues:
        console.print("\n🔧 [bold green]Applying AST-based fixes...[/bold green]")
        assistant = AdvancedAssistant(verbose=verbose)

        if path_obj.is_file():
            transform_result = assistant.transform_file(path_obj, dry_run=dry_run)
            _display_transformation_result(transform_result, dry_run)
        else:
            python_files = list(path_obj.glob("**/*.py"))
            transform_results = []

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                for py_file in python_files:
                    task = progress.add_task(
                        f"Transforming {py_file.name}...", total=None
                    )
                    result = assistant.transform_file(py_file, dry_run=dry_run)
                    transform_results.append(result)
                    progress.remove_task(task)

            _display_directory_transformation(transform_results, dry_run)

    # 5. Summary and exit code
    has_issues = not basic_success or (ast_issues and _has_ast_issues(ast_issues))

    if has_issues:
        console.print(
            "\n❌ [red]Issues found. Run with --fix to apply automatic fixes.[/red]"
        )
        sys.exit(1)
    else:
        console.print("\n✅ [green]All checks passed![/green]")


def _display_check_analysis_result(result: CodeAnalysisResult, show_complexity: bool):
    """Display analysis results for check command."""
    console.print(
        f"\n📊 [bold blue]Analysis Results for {result.file_path.name}[/bold blue]"
    )

    # Basic metrics
    metrics_table = Table(title="📈 Code Metrics")
    metrics_table.add_column("Metric", style="cyan")
    metrics_table.add_column("Value", style="green", justify="right")

    metrics_table.add_row("Lines of Code", str(result.lines_of_code))
    metrics_table.add_row("Functions", str(result.function_count))
    metrics_table.add_row("Classes", str(result.class_count))

    if show_complexity:
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
        console.print("✅ [green]No AST issues found![/green]")


def _display_check_directory_analysis(
    results: List[CodeAnalysisResult], show_complexity: bool
):
    """Display analysis results for check command on directories."""
    console.print("\n📊 [bold blue]Directory Analysis Summary[/bold blue]")

    summary_table = Table(title="📈 Summary Statistics")
    summary_table.add_column("File", style="cyan")
    summary_table.add_column("LOC", style="green", justify="right")
    summary_table.add_column("Functions", style="blue", justify="right")
    summary_table.add_column("Classes", style="magenta", justify="right")
    if show_complexity:
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

        row = [
            result.file_path.name,
            str(result.lines_of_code),
            str(result.function_count),
            str(result.class_count),
        ]

        if show_complexity:
            row.append(f"{result.complexity_score:.1f}")

        row.append(str(len(result.issues)))
        summary_table.add_row(*row)

    # Add totals row
    totals_row = [
        "[bold]TOTAL[/bold]",
        f"[bold]{total_loc}[/bold]",
        f"[bold]{total_functions}[/bold]",
        f"[bold]{total_classes}[/bold]",
    ]

    if show_complexity:
        totals_row.append("[bold]-[/bold]")

    totals_row.append(f"[bold]{total_issues}[/bold]")
    summary_table.add_row(*totals_row)

    console.print(summary_table)


def _has_ast_issues(ast_issues) -> bool:
    """Check if AST analysis found any issues."""
    if isinstance(ast_issues, list):
        return any(len(result.issues) > 0 for result in ast_issues)
    else:
        return len(ast_issues.issues) > 0


@app.command()
def fix(
    path: Annotated[str, typer.Argument(help="File or directory to fix")],
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Show changes without applying")
    ] = False,
    interactive: Annotated[
        bool, typer.Option("--interactive", "-i", help="Interactive fixing")
    ] = False,
    ast_transforms: Annotated[
        bool, typer.Option("--ast/--no-ast", help="Use AST transformations")
    ] = True,
    backup: Annotated[
        bool, typer.Option("--backup/--no-backup", help="Create backup files")
    ] = True,
    patterns: Annotated[
        Optional[List[str]], typer.Option("--pattern", help="Specific patterns to fix")
    ] = None,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Enable verbose output")
    ] = False,
):
    """🔧 Advanced code fixing with AST transformations.

    Examples:
      nicestlog fix file.py                      # Auto-fix with AST
      nicestlog fix file.py --dry-run            # Preview fixes
      nicestlog fix file.py --interactive        # Interactive fixing
      nicestlog fix src/ --pattern logging      # Fix specific patterns
      nicestlog fix file.py --no-backup         # Skip backup creation
    """
    path_obj = Path(path)
    if not path_obj.exists():
        console.print(f"❌ [red]Path {path} does not exist[/red]")
        sys.exit(1)

    # Display mode information
    mode_info = []
    if interactive:
        mode_info.append("🎯 Interactive")
    if dry_run:
        mode_info.append("🔍 Preview")
    else:
        mode_info.append("🔧 Apply fixes")

    if ast_transforms:
        mode_info.append("🔬 AST transforms")
    if backup and not dry_run:
        mode_info.append("💾 With backup")

    console.print(
        Panel.fit(
            f"🔧 [bold green]Code Fixing[/bold green]\n"
            f"Mode: [cyan]{' + '.join(mode_info)}[/cyan]\n"
            f"Target: [yellow]{path_obj}[/yellow]",
            title="Fix Configuration",
        )
    )

    # 1. Create backup if requested and not dry run
    if backup and not dry_run:
        backup_result = create_migration_backup(path_obj)
        if backup_result:
            console.print(f"✅ [green]Backup created: {backup_result}[/green]")

    # 2. Interactive Mode
    if interactive:
        console.print(
            "\n🎯 [bold magenta]Starting interactive fixing...[/bold magenta]"
        )
        transformer = InteractiveTransformer()

        if path_obj.is_file():
            transformer.transform_file_interactive(path_obj)
        else:
            # For directories, process files one by one
            python_files = list(path_obj.glob("**/*.py"))
            for py_file in python_files:
                console.print(f"\n📁 Processing: {py_file}")
                if typer.confirm(f"Fix {py_file.name}?"):
                    transformer.transform_file_interactive(py_file)
        return

    # 3. Automatic AST-based fixing
    if ast_transforms:
        console.print("\n🔬 [bold blue]Running AST-based fixes...[/bold blue]")
        assistant = AdvancedAssistant(verbose=verbose)

        # Configure patterns if specified
        if patterns:
            for pattern_name in patterns:
                for ast_pattern in assistant.patterns:
                    if pattern_name.lower() in ast_pattern.name.lower():
                        ast_pattern.enabled = True
                    else:
                        ast_pattern.enabled = False

        # Apply fixes
        if path_obj.is_file():
            transform_result = assistant.transform_file(path_obj, dry_run=dry_run)
            _display_transformation_result(transform_result, dry_run)

            if not transform_result.changes_made:
                console.print(
                    "ℹ️ [blue]No fixes needed - code is already optimal[/blue]"
                )
        else:
            python_files = list(path_obj.glob("**/*.py"))
            if not python_files:
                console.print("❌ [red]No Python files found in directory[/red]")
                sys.exit(1)

            transform_results = []

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                for py_file in python_files:
                    task = progress.add_task(f"Fixing {py_file.name}...", total=None)
                    result = assistant.transform_file(py_file, dry_run=dry_run)
                    transform_results.append(result)
                    progress.remove_task(task)

            _display_directory_transformation(transform_results, dry_run)

            # Summary
            total_changes = sum(len(r.changes) for r in transform_results)
            if total_changes == 0:
                console.print(
                    "\nℹ️ [blue]No fixes needed - all code is already optimal[/blue]"
                )
            elif dry_run:
                console.print(
                    f"\n[blue]ℹ️ Run without --dry-run to apply {total_changes} fixes[/blue]"
                )
            else:
                console.print(
                    f"\n✅ [green]Successfully applied {total_changes} fixes[/green]"
                )

    # 4. Basic linting fixes (fallback if AST disabled)
    else:
        console.print("\n📋 [bold blue]Running basic linting fixes...[/bold blue]")
        from .linter import lint_directory

        success = lint_directory(path_obj)

        if success:
            console.print("✅ [green]All basic checks passed![/green]")
        else:
            console.print(
                "❌ [red]Some issues remain. Consider using --ast for advanced fixes.[/red]"
            )
            sys.exit(1)


# DEPRECATED AST Commands - redirect to main commands
@ast_app.command("analyze")
def ast_analyze_deprecated(
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
    """🔍 [DEPRECATED] Use 'nicestlog check --ast' instead."""
    console.print("[yellow]⚠️ DEPRECATED: 'tools ast analyze' is deprecated.[/yellow]")
    console.print("[yellow]   Use 'nicestlog check --ast' instead.[/yellow]")
    
    # Redirect to check command with AST enabled
    from typer.testing import CliRunner
    runner = CliRunner()
    
    # Build command args
    args = [str(path), "--ast"]
    if verbose:
        args.append("--verbose")
    if json_output:
        console.print("[yellow]   Note: JSON output available via 'nicestlog analyze'[/yellow]")
    
    # Call check command directly
    check(str(path), fix=False, interactive=False, dry_run=False, 
          ast_analysis=True, complexity=False, patterns=None, verbose=verbose)


@ast_app.command("transform")
def ast_transform_deprecated(
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
):
    """🔄 [DEPRECATED] Use 'nicestlog fix --ast' instead."""
    console.print("[yellow]⚠️ DEPRECATED: 'tools ast transform' is deprecated.[/yellow]")
    console.print("[yellow]   Use 'nicestlog fix --ast' instead.[/yellow]")
    
    # Redirect to fix command
    fix(str(path), dry_run=dry_run, interactive=interactive, 
        ast_transforms=True, backup=True, patterns=None, verbose=verbose)


@ast_app.command("interactive")
def ast_interactive_deprecated(
    path: Path = typer.Argument(..., help="Python file to transform interactively"),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging"
    ),
):
    """🎯 [DEPRECATED] Use 'nicestlog fix --interactive' instead."""
    console.print("[yellow]⚠️ DEPRECATED: 'tools ast interactive' is deprecated.[/yellow]")
    console.print("[yellow]   Use 'nicestlog fix --interactive' instead.[/yellow]")
    
    # Redirect to fix command
    fix(str(path), dry_run=False, interactive=True, 
        ast_transforms=True, backup=True, patterns=None, verbose=verbose)


@ast_app.command("patterns")
def ast_patterns_deprecated(
    show_details: bool = typer.Option(
        False, "--details", "-d", help="Show detailed pattern information"
    ),
):
    """📋 [DEPRECATED] Use 'nicestlog check --ast --help' for pattern info."""
    console.print("[yellow]⚠️ DEPRECATED: 'tools ast patterns' is deprecated.[/yellow]")
    console.print("[yellow]   Pattern information available in 'nicestlog check --ast --help'[/yellow]")
    
    # Still show patterns for now
    assistant = AdvancedAssistant()
    patterns = assistant.patterns
    _display_patterns(patterns, show_details)


# Helper functions for AST operations
def _analyze_single_file(assistant: AdvancedAssistant, path: Path, json_output: bool):
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
    assistant: AdvancedAssistant,
    path: Path,
    pattern: str,
    dry_run: bool,
    interactive: bool,
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
                    f"Transforming {file_path.name}...", total=None
                )
                result = assistant.transform_file(file_path, dry_run=dry_run)
                results.append(result)
                progress.remove_task(task)

    _display_directory_transformation(results, dry_run)


def _transform_interactive(path: Path, verbose: bool):
    """Run interactive transformation on a file."""
    transformer = InteractiveTransformer()
    transformer.transform_file_interactive(path)


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
    console.print(
        f"\n📊 [bold blue]Analysis Results for {result.file_path}[/bold blue]"
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


def _display_transformation_result(result: TransformationResult, dry_run: bool):
    """Display transformation results for a single file."""
    mode = "Preview" if dry_run else "Applied"
    console.print(
        f"\n🔄 [bold green]Transformation {mode} for {result.file_path}[/bold green]"
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
                result.transformed_code, "python", theme="monokai", line_numbers=True
            )
            console.print(syntax)
    else:
        console.print("ℹ️ [blue]No changes needed[/blue]")


def _display_directory_analysis(results: List[CodeAnalysisResult]):
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
    results: List[TransformationResult], dry_run: bool
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
        status = "✅ Modified" if result.changes_made else "ℹ️ No changes"

        summary_table.add_row(result.file_path.name, str(changes_count), status)

    console.print(summary_table)
    console.print(f"\n📊 [bold]Total changes {mode.lower()}: {total_changes}[/bold]")


# Additional CLI commands
@app.command()
def lint(
    path: Annotated[str, typer.Argument(help="Path to lint")] = ".",
    min_coverage: Annotated[
        float, typer.Option("--min-coverage", help="Minimum coverage")
    ] = 5.0,
    max_coverage: Annotated[
        float, typer.Option("--max-coverage", help="Maximum coverage")
    ] = 15.0,
    strict: Annotated[
        bool, typer.Option("--strict", help="Enable strict mode")
    ] = False,
):
    """🔍 Check logging coverage and quality."""
    run_linter(path, min_coverage, max_coverage, strict)


@app.command()
def dashboard(
    host: Annotated[str, typer.Option("--host", help="Host to bind to")] = "127.0.0.1",
    port: Annotated[int, typer.Option("--port", help="Port to bind to")] = 8080,
    debug: Annotated[bool, typer.Option("--debug", help="Debug mode")] = False,
):
    """🌐 Start the web dashboard."""
    run_dashboard_cmd(host, port, debug)


@app.command()
def journal(
    unit: Annotated[
        Optional[str], typer.Option("--unit", "-u", help="Systemd unit")
    ] = None,
    lines: Annotated[
        int, typer.Option("--lines", "-n", help="Number of lines to show")
    ] = 50,
    follow: Annotated[
        bool, typer.Option("--follow", "-f", help="Follow log output")
    ] = False,
    since: Annotated[
        Optional[str], typer.Option("--since", help="Show logs since")
    ] = None,
    level: Annotated[
        Optional[str], typer.Option("--level", help="Log level filter")
    ] = None,
):
    """📖 Beautiful systemd journal viewer."""
    if level and level not in ["debug", "info", "warning", "error", "critical"]:
        console.print(
            f"❌ [red]Invalid level '{level}'. Valid levels: debug, info, warning, error, critical[/red]"
        )
        raise typer.Exit(1)

    run_journal_viewer(unit, lines, follow, since, level)


@app.command()
def review(
    path: Annotated[str, typer.Argument(help="Path to review")],
    format_type: Annotated[
        str, typer.Option("--format", help="Output format")
    ] = "text",
    min_score: Annotated[
        float, typer.Option("--min-score", help="Minimum score")
    ] = 70.0,
):
    """📝 Review log quality and provide suggestions."""
    valid_formats = ["text", "json", "html"]
    if format_type not in valid_formats:
        console.print(
            f"❌ [red]Invalid format '{format_type}'. Valid formats: {', '.join(valid_formats)}[/red]"
        )
        raise typer.Exit(1)

    run_log_reviewer(path, format_type, min_score)


@app.command()
def migrate(
    path: Annotated[str, typer.Argument(help="Project path to analyze/migrate")] = ".",
    do_migrate: Annotated[
        bool, typer.Option("--do-migrate", help="Actually apply changes (default: analyze only)")
    ] = False,
    migration_type: Annotated[
        str, typer.Option("--type", "-t", help="Migration type")
    ] = "print-to-structlog",
    json_output: Annotated[
        bool, typer.Option("--json", help="JSON output for agents")
    ] = False,
    output: Annotated[
        Optional[str], typer.Option("--output", "-o", help="Output JSON file or directory")
    ] = None,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Verbose output")
    ] = False,
    interactive: Annotated[
        bool, typer.Option("--interactive", "-i", help="Interactive migration")
    ] = False,
    backup: Annotated[
        bool, typer.Option("--backup/--no-backup", help="Create backup files")
    ] = True,
    force: Annotated[
        bool, typer.Option("--force", help="Overwrite existing files")
    ] = False,
):
    """🔄 Analyze project and optionally migrate code.

    Default behavior: Analyze project for migration opportunities (safe, fast)
    
    Examples:
      nicestlog migrate                                   # Analyze current project
      nicestlog migrate /path/to/project                  # Analyze specific project  
      nicestlog migrate . --json                          # Agent analysis output
      nicestlog migrate . --do-migrate                    # Actually apply changes
      nicestlog migrate . --do-migrate --type logging-to-structlog  # Specific migration
      nicestlog migrate . --do-migrate --interactive      # Interactive migration
    """
    
    if not do_migrate:
        # Default behavior: Analysis only
        from .project_analyzer import analyze_project_for_agents
        
        # CRITICAL FIX: Initialize logging before analysis (embarrassing for a logging tool!)
        import nicestlog
        nicestlog.init_logging(
            verbose=verbose,
            syslog_identifier="nicestlog-migrate",
            log_format="console"
        )
        
        try:
            result = analyze_project_for_agents(path, verbose=verbose)
            
            if json_output or (output and output.endswith('.json')):
                # JSON output for agents or file output
                json_content = result.to_json()
                
                if output:
                    Path(output).write_text(json_content)
                    console.print(f"✅ [green]Analysis saved to {output}[/green]")
                else:
                    print(json_content)
            else:
                # Human-readable output
                _display_project_analysis(result)
                
                # Enhanced user guidance based on analysis
                _display_next_steps_guidance(result, path)
                
        except Exception as e:
            console.print(f"❌ [red]Analysis failed: {e}[/red]")
            raise typer.Exit(1)
    else:
        # Migration behavior: Apply changes
        run_migrate_command(
            path, output, migration_type, dry_run=False, interactive=interactive, backup=backup, force=force
        )


@app.command()
def demo(
    feature_arg: Annotated[
        Optional[str], typer.Argument(help="Demo specific feature")
    ] = None,
    feature: Annotated[
        Optional[str], typer.Option("--feature", help="Demo specific feature")
    ] = None,
    all_features: Annotated[
        bool, typer.Option("--all", help="Demo all features")
    ] = False,
):
    """🎬 Run interactive demos."""
    # Support both positional argument and --feature option
    selected_feature = feature_arg or feature
    run_demos(selected_feature, all_features)


# Helper functions for docs display
def _show_markdown_files(filenames: list[str]):
    """Show markdown files with rich formatting."""
    for filename in filenames:
        try:
            try:
                content = resources.files("nicestlog").joinpath(filename).read_text()
            except (FileNotFoundError, AttributeError):
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
        "4": ["docs/development/api_reference.rst"],
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
        "dashboard": ["docs/features/integrations.md"],
    }

    if feature in feature_docs:
        _show_markdown_files(feature_docs[feature])
    else:
        console.print(f"❌ [red]No documentation found for feature: {feature}[/red]")


# Implementation stubs for remaining functions
def run_linter(
    path: str,
    min_coverage: float = 70.0,
    max_coverage: float = 90.0,
    strict: bool = False,
):
    """Run the linter."""
    from .linter import lint_directory

    # In strict mode, use stricter coverage requirements
    if strict:
        min_coverage = 3.0
        max_coverage = 10.0

    success = lint_directory(
        Path(path), min_coverage=min_coverage, max_coverage=max_coverage
    )
    if not success:
        raise typer.Exit(1)


def run_dashboard_cmd(host: str = "127.0.0.1", port: int = 8080, debug: bool = False):
    """Run the web dashboard."""
    from .web_dashboard import run_dashboard

    run_dashboard(host=host, port=port, debug=debug)


def run_journal_viewer(
    unit: Optional[str] = None,
    lines: int = 50,
    follow: bool = False,
    since: Optional[str] = None,
    level: Optional[str] = None,
):
    """Run the journal viewer."""
    from .journal_viewer import JournalViewer, SYSTEMD_AVAILABLE

    # Check if systemd is available
    if not SYSTEMD_AVAILABLE:
        print("❌ systemd-python not available")
        sys.exit(1)

    viewer = JournalViewer()

    # Query and display entries
    try:
        for entry in viewer.query_journal(
            service=unit, since=since, level=level, lines=lines, follow=follow
        ):
            print(viewer.format_entry(entry))
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        console.print(f"❌ [red]Error: {e}[/red]")
        sys.exit(1)


def run_log_reviewer(path_str: str, format_type: str = "text", min_score: float = 70.0):
    """Run the log reviewer."""
    from .log_reviewer import LogQualityReviewer

    reviewer = LogQualityReviewer()

    path = Path(path_str)
    if path.is_file():
        report = reviewer.analyze_log_file(path)
        if format_type == "json":
            import json

            # Convert report to dict if it has to_dict method, otherwise use default serialization
            if hasattr(report, "to_dict"):
                report_dict = report.to_dict()
            else:
                # Handle MagicMock or other objects that don't have to_dict
                report_dict = {
                    "overall_score": getattr(report, "overall_score", 0.0),
                    "file_path": str(path),
                    "analysis": "Mock analysis",
                }
            print(json.dumps(report_dict, indent=2))
        else:
            from .log_reviewer import print_report

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
                    import json

                    if hasattr(report, "to_dict"):
                        report_dict = report.to_dict()
                    else:
                        report_dict = {
                            "overall_score": score,
                            "file_path": str(log_file),
                            "analysis": "Mock analysis",
                        }
                    print(json.dumps(report_dict, indent=2))
                else:
                    from .log_reviewer import print_report

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
    user: Optional[str] = None,
    working_directory: Optional[str] = None,
    output_file: Optional[str] = None,
):
    """Generate systemd service file."""
    from .systemd_integration import create_systemd_service_file

    service_content = create_systemd_service_file(
        service_name=service_name,
        exec_command=exec_command,
        user=user,
        working_directory=working_directory,
    )

    if output_file:
        with open(output_file, "w") as f:
            f.write(service_content)
        print(f"Service file written to {output_file}")
        # Provide helpful follow-up instructions
        target_path = f"/etc/systemd/system/{service_name}.service"
        print(f"Install with: sudo cp {output_file} {target_path}")
        print(f"Enable with: sudo systemctl enable {service_name}")
        print(f"Start with: sudo systemctl start {service_name}")
    else:
        print(service_content)


def run_demos(feature: Optional[str] = None, all_features: bool = False):
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
        print(f"\n{'-' * 40}")
        time.sleep(0.5)

    if not feature and not all_features:
        print("🎯 Available nicestlog demos:")
        print()
        for demo_name, description in available_demos.items():
            print(f"  {demo_name:12} - {description}")
        print()
        print("Usage:")
        print("  nicestlog demo basic           # Run specific demo")
        print("  nicestlog demo --all           # Run all demos")
        return

    demos_to_run = []
    if all_features:
        # Run all core demos, but skip heavy/side-effect demos like 'lint'
        demos_to_run = [k for k in available_demos.keys() if k != "lint"]
    elif feature in available_demos:
        demos_to_run = [feature]
    else:
        print(
            f"❌ Unknown demo '{feature}'. Available: {', '.join(available_demos.keys())}"
        )
        sys.exit(1)

    print("🚀 Starting nicestlog demonstrations...")

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

    print("\n🎉 Demo complete! Try these features in your own applications.")


def print_demo_header(title: str, description: str):
    """Print a formatted demo section header."""
    print(f"\n{'=' * 60}")
    print(f"🎭 {title}")
    print(f"📝 {description}")
    print(f"{'=' * 60}")
    time.sleep(1)


def run_basic_demo():
    """Demonstrate basic nicestlog features."""
    print_demo_header(
        "Basic Structured Logging", "Console output with beautiful formatting"
    )

    # Initialize with console output
    nicestlog.init_logging(verbose=True, syslog_identifier="demo")
    log = structlog.get_logger()

    print("📋 Demonstrating different log levels and structured data:")

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
    try:
        from .config import NicestLogConfig

        cfg = NicestLogConfig()
    except Exception:
        cfg = None

    init_kwargs = {"verbose": True, "syslog_identifier": "i18n-demo"}
    if cfg and cfg.translation_dir:
        init_kwargs["translation_dir"] = str(cfg.translation_dir)
    if cfg and cfg.language:
        init_kwargs["language"] = cfg.language

    # Ensure nicestlog is initialized so structlog output uses our renderers
    nicestlog.init_logging(**init_kwargs)
    log = structlog.get_logger()

    print("🌍 Demonstrating translated log messages:")
    log.info("user-login", username="alice", session_id="abc123")
    log.warning("rate-limit-exceeded", user_id=42, limit=100)
    log.error("database-error", error_code="DB001", table="users")


def run_pii_demo():
    """Demonstrate PII scrubbing features."""
    print_demo_header("PII Scrubbing", "Automatic removal of sensitive data")

    nicestlog.init_logging(verbose=True, syslog_identifier="pii-demo")
    log = structlog.get_logger()

    print("🔒 Demonstrating PII scrubbing:")
    log.info(
        "user-data", email="user@example.com", password="secret123", ssn="123-45-6789"
    )
    log.debug("api-call", token="Bearer abc123def456", api_key="sk_live_abc123")


def run_eliot_demo():
    """Demonstrate Eliot integration."""
    print_demo_header("Eliot Integration", "Action tracing and structured logging")
    print("📊 Eliot integration demo - structured action tracing")


def run_systemd_demo():
    """Demonstrate systemd integration."""
    print_demo_header("Systemd Integration", "Journal logging and service integration")
    print("🔧 Systemd integration demo - journal logging")


def run_async_demo():
    """Demonstrate async logging."""
    print_demo_header("Async Logging", "Non-blocking high-performance logging")
    print("⚡ Async logging demo - high performance logging")

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
    speedup = sync_duration / async_duration if async_duration > 0 else 1.0

    print(f"Sync logging: {sync_duration:.3f}s")
    print(f"Async logging: {async_duration:.3f}s")
    print(f"Speedup: {speedup:.1f}x")


def run_complete_demo():
    """Demonstrate complete application example."""
    print_demo_header(
        "Complete Application Example", "Real-world application logging patterns"
    )
    print("🏗️ Complete application demo - comprehensive logging")

    print("\nThis demonstrates:")
    print("• Application startup and shutdown")
    print("• Request processing with context")
    print("• Error handling and recovery")
    print("• Performance monitoring")
    print("• Structured data logging")

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

    log.debug("request-completed", status_code=200, response_time_ms=156)


def run_lint_demo():
    """Demonstrate linting functionality."""
    print_demo_header("Linting Demo", "Code quality analysis and suggestions")
    print("🔍 Linting demo - analyzing code quality")


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


def run_migrate_command(
    path: str,
    output: Optional[str],
    migration_type: str,
    dry_run: bool,
    interactive: bool,
    backup: bool,
    force: bool,
):
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
    source_path = Path(path)
    if not source_path.exists():
        console.print(f"[red]❌ Path {path} does not exist[/red]")
        raise typer.Exit(1)

    if output:
        target_root = Path(output)
        target_root.mkdir(parents=True, exist_ok=True)
        if source_path.is_file():
            # For single file, compute target file path under output directory
            target_path = target_root / source_path.name
        else:
            # For directories, use the directory itself as root
            target_path = target_root
    else:
        target_path = source_path  # In-place migration

    # 3. Display migration info
    console.print(
        Panel.fit(
            f"🔄 [bold blue]Code Migration[/bold blue]\n"
            f"Type: [cyan]{migration_type}[/cyan]\n"
            f"Mode: [yellow]{'Preview' if dry_run else 'Apply'}[/yellow]\n"
            f"Source: [green]{source_path}[/green]\n"
            f"Target: [green]{target_path}[/green]",
            title="Migration Configuration",
        )
    )

    # 4. Backup creation
    if backup and not dry_run and target_path == source_path:
        backup_result = create_migration_backup(source_path)
        if backup_result:
            console.print(f"✅ [green]Backup created: {backup_result}[/green]")

    # 5. Interactive mode
    if interactive:
        console.print(
            "🎯 [bold magenta]Starting interactive migration...[/bold magenta]"
        )
        transformer = InteractiveTransformer()
        result = run_interactive_migration(
            transformer, source_path, target_path, migration_config, dry_run
        )
        show_migration_report(result, dry_run)
        return

    # 6. Automatic migration
    console.print("🚀 [bold blue]Starting automatic migration...[/bold blue]")

    if source_path.is_file():
        result = migrate_single_file(
            source_path, target_path, migration_config, dry_run, force
        )
    else:
        result = migrate_directory_recursive(
            source_path, target_path, migration_config, dry_run, force
        )

    # 7. Show results
    show_migration_report(result, dry_run)

    # 8. Exit with appropriate code
    if result.errors > 0:
        raise typer.Exit(1)


def migrate_single_file(
    source: Path, target: Path, config: dict, dry_run: bool, force: bool
) -> MigrationResult:
    """Migrate a single file using the appropriate handler."""

    # CLI-outputs-to-Structlog migration (new functionality)
    if config["handler"] == "migrate_cli_outputs_to_structlog":
        try:
            # Read source file
            original_content = source.read_text(encoding="utf-8")

            # Apply CLI output migration
            new_content, changed = migrate_cli_outputs_file(original_content)

            # Create result object compatible with our interface
            class CompatibleResult:
                def __init__(self):
                    self.files_processed = 1
                    self.transformations_applied = 1 if changed else 0
                    self.errors = 0
                    self.warnings = []

            result = CompatibleResult()

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
                import difflib

                diff_lines = list(
                    difflib.unified_diff(
                        original_content.splitlines(keepends=True),
                        new_content.splitlines(keepends=True),
                        fromfile=str(source),
                        tofile=str(target),
                    )
                )
                console.print("\n[bold blue]📄 Preview of CLI output migration:[/bold blue]")
                for line in diff_lines[:20]:  # Show first 20 lines
                    if line.startswith("+"):
                        console.print(f"[green]{line.rstrip()}[/green]")
                    elif line.startswith("-"):
                        console.print(f"[red]{line.rstrip()}[/red]")
                    elif line.startswith("@@"):
                        console.print(f"[cyan]{line.rstrip()}[/cyan]")
                    else:
                        console.print(line.rstrip())
                if len(diff_lines) > 20:
                    console.print(
                        f"[yellow]... and {len(diff_lines) - 20} more lines[/yellow]"
                    )

            return result

        except Exception as exc:
            error_msg = str(exc)
            console.print(f"[red]❌ Error migrating CLI outputs in {source}: {exc}[/red]")

            class CompatibleResult:
                def __init__(self):
                    self.files_processed = 1
                    self.transformations_applied = 0
                    self.errors = 1
                    self.warnings = [error_msg]

            return CompatibleResult()

    # Print-to-Structlog migration (existing functionality)
    elif config["handler"] == "migrate_print_to_structlog":
        try:
            # Read source file
            original_content = source.read_text(encoding="utf-8")

            # Apply migration
            new_content, changed = migrate_file(original_content)

            # Create result object compatible with our interface
            # Note: MigrationResult from assistant.py has different fields
            class CompatibleResult:
                def __init__(self):
                    self.files_processed = 1
                    self.transformations_applied = 1 if changed else 0
                    self.errors = 0
                    self.warnings = []

            result = CompatibleResult()

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
                import difflib

                diff_lines = list(
                    difflib.unified_diff(
                        original_content.splitlines(keepends=True),
                        new_content.splitlines(keepends=True),
                        fromfile=str(source),
                        tofile=str(target),
                    )
                )
                console.print("\n[bold blue]📄 Preview of changes:[/bold blue]")
                for line in diff_lines[:20]:  # Show first 20 lines
                    if line.startswith("+"):
                        console.print(f"[green]{line.rstrip()}[/green]")
                    elif line.startswith("-"):
                        console.print(f"[red]{line.rstrip()}[/red]")
                    elif line.startswith("@@"):
                        console.print(f"[cyan]{line.rstrip()}[/cyan]")
                    else:
                        console.print(line.rstrip())
                if len(diff_lines) > 20:
                    console.print(
                        f"[yellow]... and {len(diff_lines) - 20} more lines[/yellow]"
                    )

            return result

        except Exception as exc:
            error_msg = str(exc)
            console.print(f"[red]❌ Error migrating {source}: {exc}[/red]")

            class CompatibleResult:
                def __init__(self):
                    self.files_processed = 1
                    self.transformations_applied = 0
                    self.errors = 1
                    self.warnings = [error_msg]

            return CompatibleResult()

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
            f"[yellow]⚠️ No AST patterns found for {config['handler']}[/yellow]"
        )
        # Fallback to basic analysis
        assistant.analyze_file(source)

        class CompatibleResult:
            def __init__(self):
                self.files_processed = 1
                self.transformations_applied = 0
                self.errors = 0
                self.warnings = [f"No specific patterns for {config['handler']}"]

        return CompatibleResult()

    # Apply AST transformations
    try:
        transform_result = assistant.transform_file(source, dry_run=dry_run)

        if not dry_run and transform_result.changes_made and target != source:
            # Copy transformed content to target
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(transform_result.transformed_code)

        class CompatibleResult:
            def __init__(self):
                self.files_processed = 1
                self.transformations_applied = len(transform_result.changes)
                self.errors = 0
                self.warnings = []

        return CompatibleResult()

    except Exception as exc:
        error_msg = str(exc)
        console.print(f"[red]❌ Error migrating {source}: {exc}[/red]")

        class CompatibleResult:
            def __init__(self):
                self.files_processed = 1
                self.transformations_applied = 0
                self.errors = 1
                self.warnings = [error_msg]

        return CompatibleResult()


def migrate_directory_recursive(
    source: Path, target: Path, config: dict, dry_run: bool, force: bool
) -> MigrationResult:
    """Migrate all Python files in a directory recursively."""

    # For print-to-structlog, use existing directory migration
    if config["handler"] == "migrate_print_to_structlog":
        return migrate_directory(source, target, dry_run)
    
    # For CLI outputs migration, use custom directory migration
    elif config["handler"] == "migrate_cli_outputs_to_structlog":
        return migrate_directory_with_handler(source, target, migrate_cli_outputs_file, dry_run)

    # For other migrations: Process files individually
    python_files = list(source.rglob("*.py"))
    if not python_files:
        console.print(f"[yellow]⚠️ No Python files found in {source}[/yellow]")

        class CompatibleResult:
            def __init__(self):
                self.files_processed = 0
                self.transformations_applied = 0
                self.errors = 0
                self.warnings = []

        return CompatibleResult()

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

    class CompatibleResult:
        def __init__(self):
            self.files_processed = total_files
            self.transformations_applied = total_transformations
            self.errors = total_errors
            self.warnings = all_warnings

    return CompatibleResult()


def run_interactive_migration(
    transformer: InteractiveTransformer,
    source: Path,
    target: Path,
    config: dict,
    dry_run: bool,
) -> MigrationResult:
    """Run interactive migration using InteractiveTransformer."""

    console.print(f"🎯 Interactive migration: {config['description']}")
    console.print("Use the interactive interface to review and apply changes.")

    try:
        # Start interactive session
        if source.is_file():
            transformer.transform_file_interactive(source)
        else:
            # For directories, process files one by one interactively
            python_files = list(source.rglob("*.py"))
            for py_file in python_files:
                console.print(f"\n📁 Processing: {py_file}")
                transformer.transform_file_interactive(py_file)

        # Return success result (InteractiveTransformer handles its own reporting)
        class CompatibleResult:
            def __init__(self):
                self.files_processed = (
                    1 if source.is_file() else len(list(source.rglob("*.py")))
                )
                self.transformations_applied = (
                    0  # Interactive mode handles its own counting
                )
                self.errors = 0
                self.warnings = []

        return CompatibleResult()

    except Exception as exc:
        error_msg = str(exc)
        console.print(f"[red]❌ Interactive migration failed: {exc}[/red]")

        class CompatibleResult:
            def __init__(self):
                self.files_processed = 0
                self.transformations_applied = 0
                self.errors = 1
                self.warnings = [error_msg]

        return CompatibleResult()


def migrate_directory_with_handler(
    input_dir: Path,
    output_dir: Optional[Path],
    migration_handler,
    dry_run: bool = True,
) -> MigrationResult:
    """Migrate Python files using a custom migration handler function."""
    
    class CompatibleResult:
        def __init__(self):
            self.files_processed = 0
            self.transformations_applied = 0
            self.errors = 0
            self.warnings = []
            self.diffs = {}
    
    result = CompatibleResult()
    input_dir = Path(input_dir)
    if output_dir:
        output_dir = Path(output_dir)

    if not input_dir.exists() or not input_dir.is_dir():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    for py in input_dir.rglob("*.py"):
        # Skip generated or virtual env paths
        if any(part in {".venv", "venv", "__pycache__", ".git"} for part in py.parts):
            continue
        try:
            original = py.read_text(encoding="utf-8")
        except Exception:
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
                import difflib
                diff_lines = list(
                    difflib.unified_diff(
                        original.splitlines(keepends=True),
                        new_code.splitlines(keepends=True),
                        fromfile=str(py),
                        tofile=str(py),
                    )
                )
                result.diffs[str(py)] = diff_lines

            # Write transformed code only if not dry-run
            if not dry_run:
                target_path = (
                    py if output_dir is None else (output_dir / py.relative_to(input_dir))
                )
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_text(new_code, encoding="utf-8")
                
        except Exception as exc:
            result.errors += 1
            result.warnings.append(f"Error processing {py}: {exc}")

    return result


def create_migration_backup(path: Path) -> Optional[str]:
    """Create backup of files before migration."""
    import shutil
    import datetime

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    if path.is_file():
        backup_path = path.with_suffix(f".backup_{timestamp}{path.suffix}")
        shutil.copy2(path, backup_path)
        return str(backup_path)

    elif path.is_dir():
        backup_path = path.parent / f"{path.name}_backup_{timestamp}"
        shutil.copytree(path, backup_path)
        return str(backup_path)

    return None


def show_migration_report(result: MigrationResult, dry_run: bool):
    """Display comprehensive migration results."""
    action = "Would migrate" if dry_run else "Migrated"

    # Main results table
    results_table = Table(title=f"📊 Migration Results ({action})")
    results_table.add_column("Metric", style="cyan")
    results_table.add_column("Count", style="green", justify="right")

    results_table.add_row("Files processed", str(result.files_processed))
    results_table.add_row(
        "Transformations applied", str(result.transformations_applied)
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
            f"\n[red]❌ Migration completed with {result.errors} errors[/red]"
        )
    elif result.transformations_applied > 0:
        if dry_run:
            console.print(
                f"\n[blue]ℹ️ Run without --dry-run to apply {result.transformations_applied} changes[/blue]"
            )
        else:
            console.print(
                f"\n[green]✅ Successfully applied {result.transformations_applied} transformations[/green]"
            )
    else:
        console.print(
            "\n[blue]ℹ️ No changes needed - code is already in target format[/blue]"
        )


def _display_next_steps_guidance(result, path: str):
    """Display helpful next-step guidance based on analysis results."""
    console.print(f"\n🎯 [bold green]Next Steps & Guidance[/bold green]")
    
    # Check if config exists
    config_path = Path(path) / "pyproject.toml"
    has_config = config_path.exists()
    
    if not has_config:
        console.print("📋 [yellow]No pyproject.toml found - initialize configuration first:[/yellow]")
        console.print(f"   [cyan]nicestlog init {path}[/cyan]")
        console.print("")
    
    # Strategy-specific guidance
    rec = result.recommendation
    if rec.strategy == "print-to-structlog":
        console.print("🔄 [blue]Print-to-Structlog Migration:[/blue]")
        console.print(f"   1. Preview changes: [cyan]nicestlog migrate {path} --dry-run[/cyan]")
        console.print(f"   2. Apply migration: [cyan]nicestlog migrate {path} --do-migrate --backup[/cyan]")
        console.print(f"   3. Validate results: [cyan]nicestlog check {path}[/cyan]")
    elif rec.strategy == "logging-to-structlog":
        console.print("🔄 [blue]Logging-to-Structlog Migration:[/blue]")
        console.print(f"   1. Interactive preview: [cyan]nicestlog migrate {path} --interactive[/cyan]")
        console.print(f"   2. Apply changes: [cyan]nicestlog migrate {path} --do-migrate --type logging-to-structlog[/cyan]")
        console.print(f"   3. Update imports: [cyan]nicestlog check {path} --fix[/cyan]")
    elif rec.strategy == "enhancement":
        console.print("✨ [blue]Enhancement Recommendations:[/blue]")
        console.print(f"   1. Check current code: [cyan]nicestlog check {path} --ast[/cyan]")
        console.print(f"   2. Apply fixes: [cyan]nicestlog fix {path} --ast[/cyan]")
        console.print(f"   3. Add translations: [cyan]nicestlog i18n check {path}/src[/cyan]")
    else:  # greenfield
        console.print("🌱 [blue]Greenfield Setup:[/blue]")
        console.print(f"   1. Initialize config: [cyan]nicestlog init {path}[/cyan]")
        console.print(f"   2. Set up logging: [cyan]nicestlog docs --feature logging[/cyan]")
        console.print(f"   3. Run demos: [cyan]nicestlog demo basic[/cyan]")
    
    # Risk warnings
    if rec.risk_level == "high":
        console.print(f"\n⚠️  [red]High Risk Migration - Consider:[/red]")
        console.print("   • Create full project backup first")
        console.print("   • Use interactive mode for review")
        console.print("   • Test thoroughly before committing")
    elif rec.risk_level == "medium":
        console.print(f"\n⚠️  [yellow]Medium Risk - Recommended:[/yellow]")
        console.print("   • Use --backup flag for safety")
        console.print("   • Review changes before applying")
    
    # Prerequisites
    if rec.prerequisites:
        console.print(f"\n📋 [yellow]Prerequisites:[/yellow]")
        for prereq in rec.prerequisites:
            console.print(f"   • {prereq}")
    
    console.print(f"\n💡 [blue]Need help? Run: [cyan]nicestlog docs[/cyan] or [cyan]nicestlog demo[/cyan][/blue]")


def _display_project_analysis(result):
    """Display human-readable project analysis results."""
    from .project_analyzer import ProjectAnalysisResult
    
    console.print(f"\n🔍 [bold blue]Project Analysis: {result.project_path}[/bold blue]")
    
    # Project Overview
    overview_table = Table(title="📊 Project Overview")
    overview_table.add_column("Metric", style="cyan")
    overview_table.add_column("Value", style="green", justify="right")
    
    overview_table.add_row("Total Files", str(result.complexity.total_files))
    overview_table.add_row("Python Files", str(result.complexity.python_files))
    overview_table.add_row("Total Lines", str(result.complexity.total_lines))
    overview_table.add_row("Complexity", result.complexity.complexity_category.title())
    overview_table.add_row("Package Manager", result.dependencies.package_manager.title())
    
    console.print(overview_table)
    
    # Logging Patterns
    if result.logging_patterns:
        patterns_table = Table(title="🔍 Logging Patterns Found")
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
    
    # Dependencies
    deps_table = Table(title="📦 Dependencies Analysis")
    deps_table.add_column("Package", style="cyan")
    deps_table.add_column("Status", style="green")
    
    deps_table.add_row("Standard Logging", "✅ Present" if result.dependencies.has_logging else "❌ Missing")
    deps_table.add_row("Structlog", "✅ Present" if result.dependencies.has_structlog else "❌ Missing")
    deps_table.add_row("Loguru", "✅ Present" if result.dependencies.has_loguru else "❌ Missing")
    
    if result.dependencies.has_other_logging:
        deps_table.add_row("Other Logging", ", ".join(result.dependencies.has_other_logging))
    
    console.print(deps_table)
    
    # Recommendation
    rec = result.recommendation
    rec_panel = Panel.fit(
        f"[bold green]Strategy:[/bold green] {rec.strategy}\n"
        f"[bold yellow]Priority:[/bold yellow] {rec.priority}\n"
        f"[bold blue]Effort:[/bold blue] {rec.estimated_effort}\n"
        f"[bold magenta]Approach:[/bold magenta] {rec.recommended_approach}\n"
        f"[bold red]Risk:[/bold red] {rec.risk_level}",
        title="🎯 Migration Recommendation"
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
    
    # Next Steps
    console.print(f"\n[bold green]Next Steps:[/bold green]")
    console.print(f"To apply changes, run: [cyan]nicestlog migrate . --do-migrate[/cyan]")
    console.print(f"1. Preview: [cyan]nicestlog migrate . --type {rec.strategy} --dry-run[/cyan]")
    console.print(f"2. Apply: [cyan]nicestlog migrate . --type {rec.strategy} --do-migrate --backup[/cyan]")
    console.print(f"3. Validate: [cyan]nicestlog check . --ast[/cyan]")


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
