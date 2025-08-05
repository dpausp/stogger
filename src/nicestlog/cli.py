"""
Command-line interface for nicestlog.
"""
import argparse
import sys
from pathlib import Path

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

def main():
    parser = argparse.ArgumentParser(description="Nicestlog utility.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init-config", help="Create a default configuration in pyproject.toml.")
    init_parser.set_defaults(func=init_config)
    
    # Add logging linter subcommand
    lint_parser = subparsers.add_parser("lint", help="Check logging coverage in your codebase.")
    lint_parser.add_argument("path", nargs="?", default=".", help="Path to analyze (default: current directory)")
    lint_parser.add_argument("--min-coverage", type=float, default=5.0, help="Minimum logging coverage %% (default: 5.0)")
    lint_parser.add_argument("--max-coverage", type=float, default=15.0, help="Maximum logging coverage %% (default: 15.0)")
    lint_parser.add_argument("--strict", action="store_true", help="Use stricter coverage requirements")
    lint_parser.set_defaults(func=run_linter)
    
    # Add web dashboard subcommand
    web_parser = subparsers.add_parser("dashboard", help="Start the web dashboard for live log viewing.")
    web_parser.add_argument("--host", default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)")
    web_parser.add_argument("--port", type=int, default=8080, help="Port to bind to (default: 8080)")
    web_parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    web_parser.set_defaults(func=run_dashboard_cmd)
    
    # Add systemd service generator subcommand
    systemd_parser = subparsers.add_parser("generate-service", help="Generate systemd service file.")
    systemd_parser.add_argument("service_name", help="Name of the service")
    systemd_parser.add_argument("exec_command", help="Command to execute")
    systemd_parser.add_argument("--user", help="User to run as (default: current user)")
    systemd_parser.add_argument("--working-dir", help="Working directory (default: current dir)")
    systemd_parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    systemd_parser.set_defaults(func=generate_service_cmd)

    args = parser.parse_args()
    args.func()

def run_linter():
    """Run the logging linter."""
    from .linter import main as linter_main
    linter_main()

def run_dashboard_cmd():
    """Run the web dashboard."""
    import sys
    from .web_dashboard import run_dashboard
    
    # Parse args manually since argparse is tricky with subcommands
    host = "127.0.0.1"
    port = 8080
    debug = False
    
    args = sys.argv[2:]  # Skip 'nicestlog dashboard'
    i = 0
    while i < len(args):
        if args[i] == "--host" and i + 1 < len(args):
            host = args[i + 1]
            i += 2
        elif args[i] == "--port" and i + 1 < len(args):
            port = int(args[i + 1])
            i += 2
        elif args[i] == "--debug":
            debug = True
            i += 1
        else:
            i += 1
    
    run_dashboard(host=host, port=port, debug=debug)

def generate_service_cmd():
    """Generate systemd service file."""
    import sys
    import os
    from .systemd_integration import create_systemd_service_file
    
    # Parse args manually
    args = sys.argv[2:]  # Skip 'nicestlog generate-service'
    
    if len(args) < 2:
        print("Usage: nicestlog generate-service <service_name> <exec_command>", file=sys.stderr)
        sys.exit(1)
    
    service_name = args[0]
    exec_command = args[1]
    
    # Parse optional arguments
    user = None
    working_dir = None
    output_file = None
    
    i = 2
    while i < len(args):
        if args[i] == "--user" and i + 1 < len(args):
            user = args[i + 1]
            i += 2
        elif args[i] == "--working-dir" and i + 1 < len(args):
            working_dir = args[i + 1]
            i += 2
        elif args[i] in ["--output", "-o"] and i + 1 < len(args):
            output_file = args[i + 1]
            i += 2
        else:
            i += 1
    
    # Generate service file
    service_content = create_systemd_service_file(
        service_name=service_name,
        exec_command=exec_command,
        user=user,
        working_directory=working_dir
    )
    
    # Output
    if output_file:
        with open(output_file, 'w') as f:
            f.write(service_content)
        print(f"✅ Service file written to {output_file}")
        print(f"💡 Install with: sudo cp {output_file} /etc/systemd/system/")
        print(f"💡 Enable with: sudo systemctl enable {service_name}")
        print(f"💡 Start with: sudo systemctl start {service_name}")
    else:
        print(service_content)

if __name__ == "__main__":
    main()
