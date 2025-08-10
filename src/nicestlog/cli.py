"""
Command-line interface for nicestlog.
"""
import sys
from pathlib import Path
from typing import Annotated, Optional

import typer

def init_config():
    """Interactive wizard to create a [tool.nicestlog] section in pyproject.toml."""
    print("Nicestlog Configuration Wizard")
    print("This will help you create a `[tool.nicestlog]` section in your pyproject.toml.")

    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        print(f"Error: {pyproject_path.resolve()} not found.", file=sys.stderr)
        print("Please run this command in the root of your project.", file=sys.stderr)
        sys.exit(1)

    config = {}
    print("\n--- General Settings ---")
    config["verbose"] = input("Enable verbose (trace-level) logging? [y/N]: ").lower() == "y"
    config["syslog_identifier"] = input("Syslog identifier [nicestlog]: ") or "nicestlog"
    config["log_format"] = input("Log format (console/json) [console]: ") or "console"
    config["async_logging"] = input("Enable asynchronous (non-blocking) logging? [y/N]: ").lower() == "y"

    print("\n--- File Logging ---")
    if input("Enable file logging? [y/N]: ").lower() == "y":
        logdir = input("Log directory [logs]: ") or "logs"
        config["logdir"] = logdir
        config["log_cmd_output"] = input("Log external command output to a separate file? [y/N]: ").lower() == "y"

    print("\n--- Translations ---")
    if input("Enable message translations? [y/N]: ").lower() == "y":
        trans_dir = input("Translations directory [translations]: ") or "translations"
        lang = input("Default language [en]: ") or "en"
        config["translation_dir"] = trans_dir
        config["language"] = lang

    # Generate TOML snippet
    toml_snippet = "\n[tool.nicestlog]\n"
    for key, value in config.items():
        if isinstance(value, bool):
            toml_snippet += f"{key} = {str(value).lower()}\n"
        else:
            toml_snippet += f'{key} = "{value}"\n'

    print("\nGenerated config:")
    print("-" * 20)
    print(toml_snippet)
    print("-" * 20)

    if input("Append this to pyproject.toml? [Y/n]: ").lower() != "n":
        with open(pyproject_path, "a") as f:
            f.write(toml_snippet)
        print(f"Configuration successfully written to {pyproject_path}.")
    else:
        print("Aborted.")

app = typer.Typer(help="Nicestlog utility.")


@app.command("init-config")
def init_config_cmd():
    """Create a default configuration in pyproject.toml."""
    init_config()


@app.command()
def lint(
    path: Annotated[str, typer.Argument(help="Path to analyze")] = ".",
    min_coverage: Annotated[float, typer.Option(help="Minimum logging coverage %")] = 5.0,
    max_coverage: Annotated[float, typer.Option(help="Maximum logging coverage %")] = 15.0,
    strict: Annotated[bool, typer.Option(help="Use stricter coverage requirements")] = False,
):
    """Check logging coverage in your codebase."""
    run_linter(path, min_coverage, max_coverage, strict)


@app.command()
def dashboard(
    host: Annotated[str, typer.Option(help="Host to bind to")] = "127.0.0.1",
    port: Annotated[int, typer.Option(help="Port to bind to")] = 8080,
    debug: Annotated[bool, typer.Option(help="Enable debug mode")] = False,
):
    """Start the web dashboard for live log viewing."""
    run_dashboard_cmd(host, port, debug)


@app.command("generate-service")
def generate_service(
    service_name: Annotated[str, typer.Argument(help="Name of the service")],
    exec_command: Annotated[str, typer.Argument(help="Command to execute")],
    user: Annotated[Optional[str], typer.Option(help="User to run as (default: current user)")] = None,
    working_dir: Annotated[Optional[str], typer.Option("--working-dir", help="Working directory (default: current dir)")] = None,
    output: Annotated[Optional[str], typer.Option("-o", "--output", help="Output file (default: stdout)")] = None,
):
    """Generate systemd service file."""
    generate_service_cmd(service_name, exec_command, user, working_dir, output)


@app.command()
def journal(
    service: Annotated[Optional[str], typer.Option("-u", "--unit", "--service", help="Service to show logs for")] = None,
    lines: Annotated[int, typer.Option("-n", "--lines", help="Number of lines")] = 50,
    follow: Annotated[bool, typer.Option("-f", "--follow", help="Follow new entries")] = False,
    since: Annotated[Optional[str], typer.Option(help='Show logs since time (e.g., "1 hour ago")')] = None,
    level: Annotated[Optional[str], typer.Option(help="Minimum log level")] = None,
):
    """Beautiful systemd journal viewer."""
    if level and level not in ['critical', 'error', 'warning', 'info', 'debug']:
        typer.echo(f"Error: Invalid level '{level}'. Choose from: critical, error, warning, info, debug", err=True)
        raise typer.Exit(1)
    run_journal_viewer(service, lines, follow, since, level)


@app.command()
def review(
    path: Annotated[str, typer.Argument(help="Log file or directory to review")],
    format_type: Annotated[str, typer.Option("--format", help="Output format")] = "text",
    min_score: Annotated[float, typer.Option("--min-score", help="Minimum acceptable score")] = 70.0,
):
    """Review log quality with Austrian honesty."""
    if format_type not in ['text', 'json']:
        typer.echo(f"Error: Invalid format '{format_type}'. Choose from: text, json", err=True)
        raise typer.Exit(1)
    run_log_reviewer(path, format_type, min_score)


def main():
    app()

def run_linter(path: str = ".", min_coverage: float = 5.0, max_coverage: float = 15.0, strict: bool = False):
    """Run the logging linter."""
    from .linter import LoggingLinter
    
    linter = LoggingLinter()
    results = linter.analyze_directory(
        path, 
        min_coverage=min_coverage, 
        max_coverage=max_coverage, 
        strict=strict
    )
    linter.print_results(results)

def run_dashboard_cmd(host: str = "127.0.0.1", port: int = 8080, debug: bool = False):
    """Run the web dashboard."""
    from .web_dashboard import run_dashboard
    
    run_dashboard(host=host, port=port, debug=debug)

def generate_service_cmd(
    service_name: str, 
    exec_command: str, 
    user: Optional[str] = None, 
    working_dir: Optional[str] = None, 
    output: Optional[str] = None
):
    """Generate systemd service file."""
    from .systemd_integration import create_systemd_service_file
    
    # Generate service file
    service_content = create_systemd_service_file(
        service_name=service_name,
        exec_command=exec_command,
        user=user,
        working_directory=working_dir
    )
    
    # Output
    if output:
        with open(output, 'w') as f:
            f.write(service_content)
        print(f"✅ Service file written to {output}")
        print(f"💡 Install with: sudo cp {output} /etc/systemd/system/")
        print(f"💡 Enable with: sudo systemctl enable {service_name}")
        print(f"💡 Start with: sudo systemctl start {service_name}")
    else:
        print(service_content)

def run_journal_viewer(
    service: Optional[str] = None,
    lines: int = 50,
    follow: bool = False,
    since: Optional[str] = None,
    level: Optional[str] = None
):
    """Run the journal viewer."""
    from .journal_viewer import JournalViewer, SYSTEMD_AVAILABLE
    
    if not SYSTEMD_AVAILABLE:
        print("Error: systemd-python not available. Install with: pip install systemd-python", file=sys.stderr)
        sys.exit(1)
    
    # Create viewer and run
    viewer = JournalViewer()
    
    try:
        for entry in viewer.query_journal(
            service=service,
            since=since,
            level=level,
            lines=lines,
            follow=follow
        ):
            print(viewer.format_entry(entry))
    except KeyboardInterrupt:
        print("\n👋 Goodbye!", file=sys.stderr)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def run_log_reviewer(path_str: str, format_type: str = "text", min_score: float = 70.0):
    """Run the log quality reviewer."""
    from .log_reviewer import LogQualityReviewer, print_report
    from pathlib import Path
    
    reviewer = LogQualityReviewer()
    path = Path(path_str)
    
    if path.is_file():
        report = reviewer.analyze_log_file(path)
        print_report(report, format_type)
        
        if report.overall_score < min_score:
            sys.exit(1)
    
    elif path.is_dir():
        log_files = list(path.glob('*.log')) + list(path.glob('*.txt'))
        if not log_files:
            print("Keine Log-Dateien gefunden!", file=sys.stderr)
            sys.exit(1)
        
        total_score = 0
        for log_file in log_files:
            print(f"\n📁 {log_file.name}:")
            report = reviewer.analyze_log_file(log_file)
            print_report(report, format_type)
            total_score += report.overall_score
        
        avg_score = total_score / len(log_files)
        print(f"\n🎯 Durchschnittliche Qualität: {avg_score:.1f}/100")
        
        if avg_score < min_score:
            sys.exit(1)
    
    else:
        print(f"Pfad nicht gefunden: {path}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
