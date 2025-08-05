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

    args = parser.parse_args()
    args.func()

if __name__ == "__main__":
    main()
