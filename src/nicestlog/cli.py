"""
Command-line interface for nicestlog.
"""

import sys
import time
import os
from pathlib import Path
from typing import Annotated, Optional

import typer
import structlog
import nicestlog
import importlib.resources as resources

# Get a logger for this module
log = structlog.get_logger(__name__)


def init_config():
    """Interactive wizard to create a [tool.nicestlog] section in pyproject.toml."""
    log.info("starting-config-wizard")
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
        logdir = input("Log directory [logs]: ") or "logs"
        config["logdir"] = logdir
        config["log_cmd_output"] = (
            input("Log external command output to a separate file? [y/N]: ").lower()
            == "y"
        )

    print("\n--- Source Directory ---")
    src_dir = input("Source directory [src]: ") or "src"
    config["src_dir"] = src_dir

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


app = typer.Typer(help="Nicestlog utility.", no_args_is_help=True)

# Sub-app for i18n related commands
i18n_app = typer.Typer(help="Internationalization utilities")
app.add_typer(i18n_app, name="i18n")


@app.command()
def docs(ctx: typer.Context):
    """Show all packaged docs"""
    _show_markdown_files(["README.md", "best_practices.md"])


@app.command("init-config")
def init_config_cmd():
    """Create a default configuration in pyproject.toml."""
    init_config()


@app.command()
def lint(
    path: Annotated[str, typer.Argument(help="Path to analyze")] = ".",
    min_coverage: Annotated[
        float, typer.Option(help="Minimum logging coverage %")
    ] = 5.0,
    max_coverage: Annotated[
        float, typer.Option(help="Maximum logging coverage %")
    ] = 15.0,
    strict: Annotated[
        bool, typer.Option(help="Use stricter coverage requirements")
    ] = False,
    output_format: Annotated[
        str,
        typer.Option("--format", help="Output format: table or json"),
    ] = "table",
):
    """Check logging coverage in your codebase."""
    # Allow selecting a machine-readable output via env var without changing function signatures
    fmt = (output_format or "table").lower()
    if fmt not in {"table", "json", "toml"}:
        typer.echo("Error: Invalid format. Choose 'table', 'json' or 'toml'", err=True)
        raise typer.Exit(1)
    os.environ["NICESTLOG_LINTER_FORMAT"] = fmt

    # Keep CLI behavior simple and pass the path as provided.
    # This matches test expectations (default "." and raw values).
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
    user: Annotated[
        Optional[str], typer.Option(help="User to run as (default: current user)")
    ] = None,
    working_dir: Annotated[
        Optional[str],
        typer.Option("--working-dir", help="Working directory (default: current dir)"),
    ] = None,
    output: Annotated[
        Optional[str],
        typer.Option("-o", "--output", help="Output file (default: stdout)"),
    ] = None,
):
    """Generate systemd service file."""
    generate_service_cmd(service_name, exec_command, user, working_dir, output)


@app.command()
def journal(
    service: Annotated[
        Optional[str],
        typer.Option("-u", "--unit", "--service", help="Service to show logs for"),
    ] = None,
    lines: Annotated[int, typer.Option("-n", "--lines", help="Number of lines")] = 50,
    follow: Annotated[
        bool, typer.Option("-f", "--follow", help="Follow new entries")
    ] = False,
    since: Annotated[
        Optional[str], typer.Option(help='Show logs since time (e.g., "1 hour ago")')
    ] = None,
    level: Annotated[Optional[str], typer.Option(help="Minimum log level")] = None,
):
    """Beautiful systemd journal viewer."""
    if level and level not in ["critical", "error", "warning", "info", "debug"]:
        typer.echo(
            f"Error: Invalid level '{level}'. Choose from: critical, error, warning, info, debug",
            err=True,
        )
        raise typer.Exit(1)
    run_journal_viewer(service, lines, follow, since, level)


@app.command()
def review(
    path: Annotated[str, typer.Argument(help="Log file or directory to review")],
    format_type: Annotated[
        str, typer.Option("--format", help="Output format")
    ] = "text",
    min_score: Annotated[
        float, typer.Option("--min-score", help="Minimum acceptable score")
    ] = 70.0,
):
    """Review log quality with Austrian honesty."""
    if format_type not in ["text", "json"]:
        typer.echo(
            f"Error: Invalid format '{format_type}'. Choose from: text, json", err=True
        )
        raise typer.Exit(1)
    run_log_reviewer(path, format_type, min_score)


@app.command()
def demo(
    feature: Annotated[
        Optional[str], typer.Argument(help="Specific feature to demo")
    ] = None,
    all_features: Annotated[bool, typer.Option("--all", help="Run all demos")] = False,
):
    """Demonstrate nicestlog features with live examples."""
    run_demos(feature, all_features)

@app.command()
def assistant(
    path: Annotated[str, typer.Argument(help="Path to directory to migrate")],
    output: Annotated[
        Optional[str], typer.Option("-o", "--output", help="Output directory")
    ] = None,
    translations: Annotated[
        Optional[str], typer.Option("-t", "--translations", help="Translations file name")
    ] = "log_messages.json",
):
    """Automatically migrate print and logging statements to structlog."""
    from .assistant import migrate_directory
    from pathlib import Path

    input_dir = Path(path)
    output_dir = Path(output) if output else None
    translations_file = translations

    migrate_directory(input_dir, output_dir, translations_file)


def _show_markdown_files(filenames: list[str]):
    try:
        import sys
        from rich.console import Console
        from rich.markdown import Markdown

        console = Console()
        with console.pager():
            for idx, filename in enumerate(filenames):
                resource_path = resources.files("nicestlog").joinpath(
                    f"_docs/{filename}"
                )
                content = resource_path.read_text(encoding="utf-8")
                md = Markdown(content, code_theme="monokai")
                console.rule(f"{filename}")
                console.print(md)
                if idx < len(filenames) - 1:
                    console.print()
    except (FileNotFoundError, ModuleNotFoundError):
        typer.echo("Dokumentation nicht gefunden.", err=True)
        raise
        raise typer.Exit(1)


def main():
    app()


@i18n_app.command("check")
def i18n_check(
    path: Annotated[
        str, typer.Argument(help="Path to source (file or directory)")
    ] = ".",
    translation_dir: Annotated[
        str, typer.Option(help="Directory containing translation files")
    ] = "translations",
    language: Annotated[
        str, typer.Option("-l", "--language", help="Language code to check")
    ] = "en",
    strict: Annotated[
        bool, typer.Option(help="Exit with non-zero code if missing keys")
    ] = False,
    list_missing: Annotated[
        bool,
        typer.Option("--list-missing", help="Only list missing keys (one per line)"),
    ] = False,
    fail_on_extra: Annotated[
        bool,
        typer.Option(
            "--fail-on-extra", help="Exit non-zero if extra (unused) keys exist"
        ),
    ] = False,
):
    """Check that translation file contains entries for all _replace_msg/_msg_key usages.

    Also treats .info events without _replace_msg as requiring translation. .debug calls are ignored,
    but any .debug using _replace_msg will be listed as a warning section in the report.
    """
    try:
        from .i18n_check import check_translations, format_report
    except Exception as e:
        typer.echo(f"Error importing i18n check: {e}", err=True)
        raise typer.Exit(1)

    # Determine source paths: if user passed ".", prefer configured src_dir if present
    source_root = Path(path)
    if path == ".":
        try:
            from .config import NicestLogConfig
            cfg = NicestLogConfig()
            if cfg.src_dir:
                candidate = Path(cfg.src_dir)
                if candidate.exists():
                    source_root = candidate
        except Exception:
            pass

    report = check_translations([source_root], Path(translation_dir), language)

    if list_missing:
        missing = report.get("missing_keys", [])
        for k in missing:
            typer.echo(k)
        # In list-only mode, consider both strict (missing) and fail_on_extra
        if (strict and missing) or (fail_on_extra and report.get("extra_keys", [])):
            raise typer.Exit(1)
        raise typer.Exit(0)

    typer.echo(format_report(report))

    if "error" in report:
        raise typer.Exit(2)
    if (strict and report.get("missing_keys", [])) or (
        fail_on_extra and report.get("extra_keys", [])
    ):
        raise typer.Exit(1)


def run_linter(
    path: str = ".",
    min_coverage: float = 5.0,
    max_coverage: float = 15.0,
    strict: bool = False,
):
    """Run the logging linter."""
    # Ensure logging is initialized to avoid ugly default formatting
    try:
        if not nicestlog.logging_initialized():
            from .config import SimpleFormatSettings
            nicestlog.init_logging(
                simple_format_settings=SimpleFormatSettings(
                    show_logger_brackets=False,
                    show_pid=False,
                    show_code_info=False,
                    timestamp_format="iso_no_z",
                    pad_event_width=28,
                ),
                log_format="simple",
                log_to_console=True,
            )
    except Exception:
        # Fail silently; linter output still works without structured logging
        pass

    log.info("starting-linter", path=path, min_coverage=min_coverage, max_coverage=max_coverage, strict=strict)
    
    from .linter import lint_directory
    from pathlib import Path

    if strict:
        log.debug("applying-strict-mode", old_min=min_coverage, old_max=max_coverage)
        min_coverage = 3.0
        max_coverage = 10.0

    # Determine directory to scan. If user passed ".", prefer configured src_dir if present
    scan_path = Path(path)
    if path == ".":
        try:
            from .config import NicestLogConfig
            cfg = NicestLogConfig()
            if cfg.src_dir:
                candidate = Path(cfg.src_dir)
                # Use configured src_dir if it exists; otherwise keep '.'
                if candidate.exists():
                    scan_path = candidate
        except Exception:
            pass

    # Run the linter on the determined directory
    success = lint_directory(
        scan_path, min_coverage=min_coverage, max_coverage=max_coverage
    )

    # When output format is machine-readable, avoid extra console noise
    fmt = os.getenv("NICESTLOG_LINTER_FORMAT", "table").lower()
    if not success:
        if fmt not in {"json", "toml"}:
            print("Linting failed: files need logging attention.")
        log.error("linter-failed", path=path)
        sys.exit(1)
    else:
        if fmt not in {"json", "toml"}:
            log.info("linter-completed-successfully", path=path)


def run_dashboard_cmd(host: str = "127.0.0.1", port: int = 8080, debug: bool = False):
    """Run the web dashboard."""
    log.info("starting-web-dashboard", host=host, port=port, debug=debug)
    
    from .web_dashboard import run_dashboard

    run_dashboard(host=host, port=port, debug=debug)


def generate_service_cmd(
    service_name: str,
    exec_command: str,
    user: Optional[str] = None,
    working_dir: Optional[str] = None,
    output: Optional[str] = None,
):
    """Generate systemd service file."""
    log.info("generating-systemd-service", service_name=service_name, exec_command=exec_command,
            user=user, working_dir=working_dir, output=output)
    
    from .systemd_integration import create_systemd_service_file

    # Generate service file
    service_content = create_systemd_service_file(
        service_name=service_name,
        exec_command=exec_command,
        user=user,
        working_directory=working_dir,
    )

    # Output
    if output:
        with open(output, "w") as f:
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
    level: Optional[str] = None,
):
    """Run the journal viewer."""
    log.info("starting-journal-viewer", service=service, lines=lines, follow=follow, since=since, level=level)
    
    from .journal_viewer import JournalViewer, SYSTEMD_AVAILABLE

    if not SYSTEMD_AVAILABLE:
        log.error("systemd-not-available")
        print(
            "Error: systemd-python not available. Install with: pip install systemd-python",
            file=sys.stderr,
        )
        sys.exit(1)

    # Create viewer and run
    viewer = JournalViewer()

    try:
        for entry in viewer.query_journal(
            service=service, since=since, level=level, lines=lines, follow=follow
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
        log_files = list(path.glob("*.log")) + list(path.glob("*.txt"))
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


def run_demos(feature: Optional[str] = None, all_features: bool = False):
    """Run nicestlog feature demonstrations."""
    log.info("starting-demos", feature=feature, all_features=all_features)

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

    def print_demo_header(title: str, description: str):
        print(f"\n{'=' * 60}")
        print(f"🎭 {title}")
        print(f"📝 {description}")
        print(f"{'=' * 60}")
        time.sleep(1)

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
        action="login_attempt"
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

    log.info(
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
    # Verbose=True to show debug messages from the translator as well
    nicestlog.init_logging(**init_kwargs)

    try:
        from .i18n import demo_translations

        demo_translations()
    except ImportError:
        print("⚠️  i18n demo requires additional setup")


def run_pii_demo():
    """Demonstrate PII scrubbing."""
    print_demo_header("PII Scrubbing", "Automatic removal of sensitive data")

    try:
        from .pii_scrubber import demo_pii_scrubbing

        demo_pii_scrubbing()
    except ImportError:
        print("⚠️  PII demo requires additional setup")


def run_eliot_demo():
    """Demonstrate Eliot integration."""
    print_demo_header("Eliot Integration", "Beautiful action tracing and causality")

    try:
        from .eliot_integration import demo_eliot_integration

        demo_eliot_integration()
    except ImportError:
        print("⚠️  Eliot demo requires: pip install eliot")


def run_systemd_demo():
    """Demonstrate systemd integration."""
    print_demo_header("Systemd Integration", "Journal logging and service management")

    try:
        from .systemd_integration import demo_systemd_integration

        demo_systemd_integration()
    except ImportError:
        print("⚠️  Systemd demo requires: pip install systemd-python")


def run_async_demo():
    """Demonstrate async logging performance."""
    print_demo_header("Async Logging", "Non-blocking high-performance logging")

    import time

    print("🔄 Comparing sync vs async logging performance...")

    # Sync logging
    nicestlog.init_logging(async_logging=False, syslog_identifier="sync-demo")
    log = structlog.get_logger()

    start_time = time.time()
    for i in range(100):
        log.info("sync-message", iteration=i, data=f"payload-{i}")
    sync_duration = time.time() - start_time

    print(f"⏱️  Sync logging: {sync_duration:.3f}s for 100 messages")

    # Async logging
    nicestlog.init_logging(async_logging=True, syslog_identifier="async-demo")
    log = structlog.get_logger()

    start_time = time.time()
    for i in range(100):
        log.info("async-message", iteration=i, data=f"payload-{i}")
    async_duration = time.time() - start_time

    print(f"⚡ Async logging: {async_duration:.3f}s for 100 messages")
    print(f"🚀 Speedup: {sync_duration / async_duration:.1f}x faster")


def run_complete_demo():
    """Demonstrate a complete real-world application scenario."""
    print_demo_header("Complete Application Example", "Real-world usage patterns")
    
    from pathlib import Path
    import tempfile
    import time
    
    # Setup comprehensive logging
    with tempfile.TemporaryDirectory() as temp_dir:
        log_dir = Path(temp_dir)
    
        nicestlog.init_logging(
            verbose=True,
            logdir=log_dir,
            syslog_identifier="webapp",
            async_logging=True,
            log_cmd_output=True,
        )
    
        log = structlog.get_logger()
    
        print("🌐 Simulating web application with comprehensive logging...")
    
        # Application startup
        log.info(
            "app-startup",
            _replace_msg="🚀 Web application starting on port {port}",
            port=8080,
            version="2.1.0",
            environment="production",
        )
    
        # Database connection
        log.info(
            "db-connection",
            _replace_msg="🔌 Connected to database {db_name}",
            db_name="userdb",
            host="db.prod.com",
            pool_size=10,
        )
    
        # User requests
        for i in range(5):
            user_id = 1000 + i
            session_id = f"sess_{i:03d}"
    
            log.info(
                "request-start",
                _replace_msg="📥 Processing request {request_id}",
                request_id=f"req_{i:03d}",
                user_id=user_id,
                session_id=session_id,
                method="GET",
                path="/api/profile",
            )
    
            # Simulate processing time
            time.sleep(0.1)
    
            if i == 3:  # Simulate an error
                log.error(
                    "request-error",
                    _replace_msg="💥 Request failed: {error}",
                    request_id=f"req_{i:03d}",
                    error="User not found",
                    user_id=user_id,
                    status_code=404,
                )
            else:
                log.info(
                    "request-complete",
                    _replace_msg="✅ Request completed in {duration}ms",
                    request_id=f"req_{i:03d}",
                    duration=50 + i * 10,
                    status_code=200,
                    response_size=512,
                )
    
        # Show log files created
        log_files = list(log_dir.glob("*.log"))
        if log_files:
            print(f"\n📁 Log files created in {log_dir}:")
            for log_file in log_files:
                size = log_file.stat().st_size
                print(f"  {log_file.name}: {size} bytes")
    
        print("\n💡 This demonstrates:")
        print("  • Structured logging with meaningful events")
        print("  • File and console output")
        print("  • Request tracing with IDs")
        print("  • Error handling and context")
        print("  • Performance monitoring")


def run_lint_demo():
    """Demonstrate linter findings with two intentionally bad modules."""
    print_demo_header("Lint Demo", "Two modules that trigger all linter checks")

    import tempfile
    from pathlib import Path

    # Create a temporary project with two problematic modules
    with tempfile.TemporaryDirectory() as tmpdir:
        proj = Path(tmpdir)
        (proj / "pkg").mkdir()

        # Module 1: Too little logging and too few functions with logging
        bad_mod1 = (proj / "pkg" / "bad_module_one.py")
        bad_mod1.write_text(
            """
import structlog
log = structlog.get_logger("bad1")

# Many functions without any logging to trigger E1 and E2

def a1():
    x = 1 + 1
    return x

def a2():
    for i in range(5):
        pass

def a3():
    return sum([1,2,3])

def a4():
    return "ok"

def a5():
    v = 42
    return v

def a6():
    return 0

def a7():
    return 0

def a8():
    return 0

def a9():
    return 0

def a10():
    return 0

def a11():
    return 0

def a12():
    return 0

def a13():
    return 0

def a14():
    return 0

def a15():
    return 0

# Only one function with logging (single string argument, no structured data)

def logged_one():
    log.info("just a message")
""",
            encoding="utf-8",
        )

        # Module 2: Too much logging and almost every function logs + statement issues
        bad_mod2 = (proj / "pkg" / "bad_module_two.py")
        bad_mod2.write_text(
            """
import structlog
log = structlog.get_logger("bad2")

# Many tiny functions all logging to trigger W1 and W2

def f1():
    log.info("f1-start", user="alice")

def f2():
    log.debug(f"errorHappened-{1}")

def f3():
    log.error("user-info-update")

def f4():
    log.info("many-kwargs", a=1,b=2,c=3,d=4,e=5,f=6,g=7,h=8)

def f5():
    log.info("user-login", password="secret", token="abc")

def f6():
    log.info("ok")

def f7():
    log.info("ok2")

def f8():
    log.info("ok3")

def f9():
    log.info("ok4")

def f10():
    log.info("ok5")

# very long event id
log.info("this-is-a-very-very-very-very-very-very-long-event-id-that-is-definitely-too-long")
""",
            encoding="utf-8",
        )

        # Run the linter on the temporary project
        print("\n🧪 Running linter on demo project...\n")
        from .linter import lint_directory
        lint_directory(proj, min_coverage=5.0, max_coverage=15.0, analyze_statements=True)


if __name__ == "__main__":
    main()
