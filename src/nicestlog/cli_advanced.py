"""
🎯 CLI Interface for Advanced AST Assistant

Provides command-line access to the advanced code transformation capabilities
with rich output and comprehensive logging.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, List
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
import structlog

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
console = Console()
log = structlog.get_logger("nicestlog.cli_advanced")

app = typer.Typer(
    name="advanced",
    help="🚀 Advanced AST analysis and transformation tools",
    rich_markup_mode="rich",
)


@app.command("analyze")
def analyze_command(
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


@app.command("transform")
def transform_command(
    path: Path = typer.Argument(..., help="Python file or directory to transform"),
    dry_run: bool = typer.Option(
        True, "--dry-run/--apply", help="Preview changes without applying"
    ),
    interactive: bool = typer.Option(
        False,
        "--interactive",
        "-i",
        help="Interactive mode with user confirmation (amber-style)",
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
    context_lines: int = typer.Option(
        3, "--context", "-c", help="Number of context lines to show in interactive mode"
    ),
):
    """
    🔄 Transform Python code using AST patterns.

    Applies sophisticated transformations with comprehensive logging.
    """
    action = "Preview" if dry_run else "Apply"
    console.print(
        Panel.fit(
            f"🔄 [bold green]{action} Code Transformations[/bold green]",
            subtitle=f"Target: {path}",
        )
    )

    assistant = AdvancedAssistant(verbose=verbose)

    # Configure patterns
    if enable_patterns:
        for pattern_name in enable_patterns:
            for pattern in assistant.patterns:
                if pattern.name == pattern_name:
                    pattern.enabled = True
                    console.print(f"✅ Enabled pattern: [green]{pattern_name}[/green]")

    if disable_patterns:
        for pattern_name in disable_patterns:
            for pattern in assistant.patterns:
                if pattern.name == pattern_name:
                    pattern.enabled = False
                    console.print(f"❌ Disabled pattern: [red]{pattern_name}[/red]")

    if interactive:
        _transform_interactive(assistant, path, pattern, context_lines)
    elif path.is_file():
        _transform_single_file(assistant, path, dry_run)
    elif path.is_dir():
        _transform_directory(assistant, path, pattern, dry_run)
    else:
        console.print(f"❌ [red]Error:[/red] Path {path} does not exist")
        raise typer.Exit(1)


@app.command("interactive")
def interactive_command(
    path: Path = typer.Argument(..., help="Python file or directory to transform"),
    pattern: str = typer.Option(
        "*.py", "--pattern", "-p", help="File pattern for directories"
    ),
    context_lines: int = typer.Option(
        3, "--context", "-c", help="Number of context lines to show"
    ),
    enable_patterns: Optional[List[str]] = typer.Option(
        None, "--enable", help="Enable specific patterns"
    ),
    disable_patterns: Optional[List[str]] = typer.Option(
        None, "--disable", help="Disable specific patterns"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging"
    ),
):
    """
    🎯 Interactive code transformation (amber-style).

    Transform code with user confirmation for each change.
    Shows context and asks [Y]es/[n]o/[a]ll/[q]uit for each transformation.
    """
    console.print(
        Panel.fit(
            "🎯 [bold blue]Interactive Code Transformation[/bold blue]\n"
            "[dim]Amber-style search & replace with user confirmation[/dim]",
            subtitle=f"Target: {path}",
        )
    )

    assistant = AdvancedAssistant(verbose=verbose)

    # Configure patterns
    if enable_patterns:
        for pattern_name in enable_patterns:
            for pattern in assistant.patterns:
                if pattern.name == pattern_name:
                    pattern.enabled = True
                    console.print(f"✅ Enabled pattern: [green]{pattern_name}[/green]")

    if disable_patterns:
        for pattern_name in disable_patterns:
            for pattern in assistant.patterns:
                if pattern.name == pattern_name:
                    pattern.enabled = False
                    console.print(f"❌ Disabled pattern: [red]{pattern_name}[/red]")

    _transform_interactive(assistant, path, pattern, context_lines)


@app.command("patterns")
def patterns_command(
    list_all: bool = typer.Option(
        False, "--list", "-l", help="List all available patterns"
    ),
    show_details: bool = typer.Option(
        False, "--details", "-d", help="Show detailed pattern information"
    ),
):
    """
    📋 Manage transformation patterns.

    List, enable, or disable transformation patterns.
    """
    console.print(Panel.fit("📋 [bold blue]Transformation Patterns[/bold blue]"))

    assistant = AdvancedAssistant()

    if list_all or show_details:
        _display_patterns(assistant.patterns, show_details)
    else:
        console.print(
            "Use --list to see available patterns or --details for more information"
        )


def _analyze_single_file(
    assistant: AdvancedAssistant, file_path: Path, json_output: bool
):
    """Analyze a single Python file."""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Analyzing file...", total=None)

            result = assistant.analyze_file(file_path)

            progress.update(task, description="Analysis complete!")

        if json_output:
            import json

            output = {
                "file_path": str(result.file_path),
                "complexity_score": result.complexity_score,
                "node_counts": result.node_counts,
                "detected_patterns": result.detected_patterns,
                "potential_issues": result.potential_issues,
                "transformation_suggestions": result.transformation_suggestions,
            }
            console.print(json.dumps(output, indent=2))
        else:
            _display_analysis_result(result)

    except Exception as e:
        console.print(f"❌ [red]Error analyzing file:[/red] {e}")
        raise typer.Exit(1)


def _analyze_directory(
    assistant: AdvancedAssistant, directory: Path, pattern: str, json_output: bool
):
    """Analyze all Python files in a directory."""
    files = list(directory.glob(pattern))

    if not files:
        console.print(f"❌ No files matching pattern '{pattern}' found in {directory}")
        return

    results = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Analyzing {len(files)} files...", total=len(files))

        for file_path in files:
            try:
                result = assistant.analyze_file(file_path)
                results.append(result)
                progress.advance(task)
            except Exception as e:
                console.print(f"❌ Error analyzing {file_path}: {e}")

    if json_output:
        import json

        output = []
        for result in results:
            output.append(
                {
                    "file_path": str(result.file_path),
                    "complexity_score": result.complexity_score,
                    "node_counts": result.node_counts,
                    "detected_patterns": result.detected_patterns,
                    "potential_issues": result.potential_issues,
                    "transformation_suggestions": result.transformation_suggestions,
                }
            )
        console.print(json.dumps(output, indent=2))
    else:
        _display_directory_analysis(results)


def _transform_single_file(
    assistant: AdvancedAssistant, file_path: Path, dry_run: bool
):
    """Transform a single Python file."""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Transforming file...", total=None)

            result = assistant.transform_file(file_path, dry_run=dry_run)

            progress.update(task, description="Transformation complete!")

        _display_transformation_result(result, dry_run)

    except Exception as e:
        console.print(f"❌ [red]Error transforming file:[/red] {e}")
        raise typer.Exit(1)


def _transform_directory(
    assistant: AdvancedAssistant, directory: Path, pattern: str, dry_run: bool
):
    """Transform all Python files in a directory."""
    files = list(directory.glob(pattern))

    if not files:
        console.print(f"❌ No files matching pattern '{pattern}' found in {directory}")
        return

    results = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(
            f"Transforming {len(files)} files...", total=len(files)
        )

        for file_path in files:
            try:
                result = assistant.transform_file(file_path, dry_run=dry_run)
                results.append(result)
                progress.advance(task)
            except Exception as e:
                console.print(f"❌ Error transforming {file_path}: {e}")

    _display_directory_transformation(results, dry_run)


def _display_analysis_result(result: CodeAnalysisResult):
    """Display analysis results in a rich format."""
    # Summary panel
    summary_text = f"""
[bold]File:[/bold] {result.file_path}
[bold]Complexity Score:[/bold] {result.complexity_score}
[bold]Patterns Detected:[/bold] {len(result.detected_patterns)}
[bold]Issues Found:[/bold] {len(result.potential_issues)}
[bold]Suggestions:[/bold] {len(result.transformation_suggestions)}
"""

    console.print(Panel(summary_text, title="📊 Analysis Summary", border_style="blue"))

    # Node counts table
    if result.node_counts:
        table = Table(title="🔢 AST Node Counts")
        table.add_column("Node Type", style="cyan")
        table.add_column("Count", style="magenta", justify="right")

        for node_type, count in sorted(result.node_counts.items()):
            table.add_row(node_type, str(count))

        console.print(table)

    # Detected patterns
    if result.detected_patterns:
        console.print("\n🎯 [bold]Detected Patterns:[/bold]")
        for pattern in result.detected_patterns:
            console.print(f"  • {pattern}")

    # Issues
    if result.potential_issues:
        console.print("\n⚠️ [bold yellow]Potential Issues:[/bold yellow]")
        for issue in result.potential_issues:
            console.print(f"  • [yellow]{issue}[/yellow]")

    # Suggestions
    if result.transformation_suggestions:
        console.print("\n💡 [bold green]Transformation Suggestions:[/bold green]")
        for suggestion in result.transformation_suggestions:
            console.print(f"  • [green]{suggestion}[/green]")


def _display_transformation_result(result: TransformationResult, dry_run: bool):
    """Display transformation results."""
    action = "Preview" if dry_run else "Applied"

    # Summary
    summary_text = f"""
[bold]Success:[/bold] {"✅ Yes" if result.success else "❌ No"}
[bold]Changes Made:[/bold] {len(result.changes_made)}
[bold]Duration:[/bold] {result.metrics.duration:.2f}s
[bold]Nodes Analyzed:[/bold] {result.metrics.nodes_analyzed}
[bold]Nodes Transformed:[/bold] {result.metrics.nodes_transformed}
"""

    console.print(
        Panel(summary_text, title=f"🔄 Transformation {action}", border_style="green")
    )

    # Changes made
    if result.changes_made:
        console.print(f"\n📝 [bold]Changes {action}:[/bold]")
        for change in result.changes_made:
            console.print(f"  • {change}")

    # Show code diff if there are changes
    if result.original_code != result.transformed_code and len(result.changes_made) > 0:
        console.print(f"\n📄 [bold]Code {'Preview' if dry_run else 'Changes'}:[/bold]")

        # Show a snippet of the transformed code
        lines = result.transformed_code.split("\n")
        if len(lines) > 20:
            snippet = "\n".join(lines[:20]) + "\n... (truncated)"
        else:
            snippet = result.transformed_code

        syntax = Syntax(snippet, "python", theme="monokai", line_numbers=True)
        console.print(syntax)


def _display_directory_analysis(results: List[CodeAnalysisResult]):
    """Display analysis results for multiple files."""
    # Summary table
    table = Table(title="📊 Directory Analysis Summary")
    table.add_column("File", style="cyan")
    table.add_column("Complexity", style="magenta", justify="right")
    table.add_column("Patterns", style="green", justify="right")
    table.add_column("Issues", style="yellow", justify="right")
    table.add_column("Suggestions", style="blue", justify="right")

    total_complexity = 0
    total_patterns = 0
    total_issues = 0
    total_suggestions = 0

    for result in results:
        table.add_row(
            result.file_path.name,
            str(result.complexity_score),
            str(len(result.detected_patterns)),
            str(len(result.potential_issues)),
            str(len(result.transformation_suggestions)),
        )

        total_complexity += result.complexity_score
        total_patterns += len(result.detected_patterns)
        total_issues += len(result.potential_issues)
        total_suggestions += len(result.transformation_suggestions)

    # Add totals row
    table.add_section()
    table.add_row(
        "[bold]TOTAL[/bold]",
        f"[bold]{total_complexity}[/bold]",
        f"[bold]{total_patterns}[/bold]",
        f"[bold]{total_issues}[/bold]",
        f"[bold]{total_suggestions}[/bold]",
    )

    console.print(table)


def _display_directory_transformation(
    results: List[TransformationResult], dry_run: bool
):
    """Display transformation results for multiple files."""
    action = "Previewed" if dry_run else "Applied"

    # Summary table
    table = Table(title=f"🔄 Directory Transformation {action}")
    table.add_column("File", style="cyan")
    table.add_column("Success", style="green")
    table.add_column("Changes", style="magenta", justify="right")
    table.add_column("Duration", style="blue", justify="right")

    successful = 0
    total_changes = 0
    total_duration = 0.0

    for result in results:
        success_icon = "✅" if result.success else "❌"
        table.add_row(
            result.analysis.file_path.name,
            success_icon,
            str(len(result.changes_made)),
            f"{result.metrics.duration:.2f}s",
        )

        if result.success:
            successful += 1
        total_changes += len(result.changes_made)
        total_duration += result.metrics.duration

    # Add summary row
    table.add_section()
    table.add_row(
        f"[bold]{successful}/{len(results)} files[/bold]",
        "[bold]Summary[/bold]",
        f"[bold]{total_changes}[/bold]",
        f"[bold]{total_duration:.2f}s[/bold]",
    )

    console.print(table)


def _transform_interactive(
    assistant: AdvancedAssistant, path: Path, pattern: str, context_lines: int
):
    """Transform files using interactive mode (amber-style)."""
    console.print(
        Panel.fit(
            "🎯 [bold blue]Interactive Transformation Mode[/bold blue]\n"
            "[dim]Amber-style search & replace with user confirmation[/dim]",
            subtitle=f"Target: {path}",
        )
    )

    try:
        transformer = InteractiveTransformer(assistant, context_lines=context_lines)

        if path.is_file():
            result = transformer.transform_file_interactive(path)
            if result.success and result.changes_made:
                console.print(
                    f"✅ [green]Applied {len(result.changes_made)} changes to {path}[/green]"
                )
            elif result.success:
                console.print(f"ℹ️ [blue]No changes made to {path}[/blue]")
            else:
                console.print(f"❌ [red]Failed to transform {path}[/red]")

        elif path.is_dir():
            results = transformer.transform_directory_interactive(path, pattern)
            successful = sum(1 for r in results if r.success)
            total_changes = sum(len(r.changes_made) for r in results)
            console.print(
                f"✅ [green]Processed {successful}/{len(results)} files with {total_changes} total changes[/green]"
            )

        else:
            console.print(f"❌ [red]Error:[/red] Path {path} does not exist")
            raise typer.Exit(1)

    except KeyboardInterrupt:
        console.print("\n🛑 [yellow]Transformation cancelled by user[/yellow]")
        raise typer.Exit(0)
    except Exception as e:
        console.print(f"❌ [red]Error in interactive transformation:[/red] {e}")
        raise typer.Exit(1)


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


if __name__ == "__main__":
    app()
