"""doit tasks for mydevtools projects."""

from pathlib import Path


def uv_actions(*commands, **kwargs):
    return {"actions": [f"uv run {command}" for command in commands], **kwargs}


def task_install():
    """Install dependencies."""
    return {
        "actions": ["uv sync --no-group=ruff --all-groups"],
        "verbosity": 2,
    }


def task_format():
    """Format code with ruff."""
    return uv_actions(
        "ruff format .",
        "ruff check --fix .",
        verbosity=2,
    )


def task_validate_pyproject():
    return uv_actions(
        "validate-pyproject pyproject.toml",
    )


def task_python_syntax():
    """Run quick syntax checks."""
    return uv_actions(
        "ruff check --select E9,F63,F7,F82",
    )


def task_typecheck():
    """Run mypy type checker"""
    return uv_actions(
        "mypy src/",
        verbosity=2,
    )


def task_lint():
    """Run all linters."""
    return uv_actions(
        "pylint src/ --fail-under 9 -E",
        verbosity=2,
    )


def task_complexity():
    """Analyze code complexity."""
    return uv_actions(
        "radon cc src/ -a",
        "radon mi src/",
        verbosity=2,
    )


def task_security():
    """Run security checks."""
    return uv_actions(
        "bandit -r src/ --configfile pyproject.toml",
        verbosity=2,
    )


def task_dead_code():
    """Find dead code."""
    return uv_actions(
        "vulture src/ --min-confidence 80 --ignore-names subprocess",
        verbosity=2,
    )


def task_test():
    """Run tests."""
    return uv_actions(
        "pytest",
        verbosity=2,
    )


def task_test_cov():
    """Run tests with coverage."""
    return uv_actions(
        "coverage run -m pytest",
        "coverage report",
        "coverage html",
        verbosity=2,
    )


def task_all_checks():
    """Run all checks (format, lint, complexity, test)."""
    return {
        "actions": None,
        "task_dep": [
            "validate_pyproject",
            "python_syntax",
            "format",
            "lint",
            "typecheck",
            "complexity",
            "security",
            "dead_code",
            "test",
            "test_cov",
        ],
        "verbosity": 2,
    }


def task_check():
    """Compatibility alias: run the same suite as 'all_checks'."""
    return {
        "actions": None,
        "task_dep": ["all_checks"],
        "verbosity": 2,
    }


def task_cleanup():
    """Clean build artifacts."""
    import shutil

    def clean_artifacts():
        """Remove build artifacts."""
        artifacts = [
            "build/",
            "dist/",
            "*.egg-info/",
            ".pytest_cache/",
            ".mypy_cache/",
            "htmlcov/",
            ".coverage",
        ]

        for pattern in artifacts:
            if pattern.endswith("/"):
                # Directory
                for path in Path(".").glob(pattern):
                    if path.is_dir():
                        shutil.rmtree(path)
                        print(f"Removed directory: {path}")
            else:
                # File or pattern
                for path in Path(".").glob(pattern):
                    if path.is_file():
                        path.unlink()
                        print(f"Removed file: {path}")

        # Remove __pycache__ directories
        for path in Path(".").rglob("__pycache__"):
            if path.is_dir():
                shutil.rmtree(path)
                print(f"Removed __pycache__: {path}")

        # Remove .pyc files
        for path in Path(".").rglob("*.pyc"):
            path.unlink()
            print(f"Removed .pyc: {path}")

    return {
        "actions": [clean_artifacts],
        "verbosity": 2,
    }


def task_build():
    """Build package."""
    return {
        "actions": ["uv build"],
        "task_dep": ["validate_pyproject", "python_syntax"],
        "verbosity": 2,
    }


def task_pre_commit_install():
    """Install pre-commit hooks."""
    return uv_actions(
        "pre-commit install",
        verbosity=2,
    )


def task_pre_commit_run():
    """Run pre-commit on all files."""
    return uv_actions(
        "pre-commit run --all-files",
        verbosity=2,
    )


def task_dev_setup():
    """Complete development setup."""
    return {
        "actions": None,
        "task_dep": ["install", "pre_commit_install"],
        "verbosity": 2,
    }


def task_nix_update():
    """Update Nix flake dependencies."""
    return {
        "actions": [
            "nix flake update",
            "echo '✅ Nix dependencies updated in flake.lock'",
        ],
        "verbosity": 2,
    }


def task_nix_build():
    """Build package with Nix."""
    return {
        "actions": ["nix build"],
        "verbosity": 2,
    }


def task_nix_shell():
    """Enter Nix development shell."""
    return {
        "actions": ["nix develop"],
        "verbosity": 2,
    }


def task_nix_env_info():
    """Show Nix environment information."""

    def show_nix_info():
        """Display Nix environment status."""
        import os
        import subprocess

        print("🔍 Environment Information:")

        # Check if we're in a Nix shell
        if os.environ.get("IN_NIX_SHELL"):
            print("✅ Running in Nix shell")
        else:
            print("❌ Not in Nix shell")

        # Check if Nix is available
        try:
            result = subprocess.run(
                ["nix", "--version"], capture_output=True, text=True, check=True
            )
            print(f"❄️  Nix: {result.stdout.strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Nix not available")

        # Check if direnv is active
        if os.environ.get("DIRENV_DIR"):
            print("✅ direnv active")
        else:
            print("❌ direnv not active")

        # Show tool versions
        tools = ["python", "uv", "ruff", "mypy"]
        for tool in tools:
            try:
                result = subprocess.run(
                    [tool, "--version"], capture_output=True, text=True, check=True
                )
                version = result.stdout.strip().split("\n")[0]
                print(f"🔧 {tool.capitalize()}: {version}")
            except (subprocess.CalledProcessError, FileNotFoundError):
                print(f"❌ {tool} not available")

    return {
        "actions": [show_nix_info],
        "verbosity": 2,
    }


def task_update():
    """Update from remote repository and optionally reinstall with uv."""
    import subprocess

    def update_from_remote():
        """Pull from remote, show changes, and ask for installation."""
        # Load local configuration
        try:
            from src.mydevtools.local_config import get_config

            config = get_config()
        except ImportError:
            # Fallback if config module not available
            config = None

        # Helper functions for config-aware prompts
        def get_emoji(emoji: str) -> str:
            if config and not config.should_show_emojis():
                return ""
            return emoji + " "

        def ask_user(prompt: str, default_answer: str) -> bool:
            if default_answer == "yes":
                print(f"{get_emoji('✅')}Auto-answering 'yes' to: {prompt}")
                return True
            elif default_answer == "no":
                print(f"{get_emoji('❌')}Auto-answering 'no' to: {prompt}")
                return False
            else:  # "ask"
                try:
                    response = (
                        input(f"\n{get_emoji('🤔')}{prompt} [y/N]: ").strip().lower()
                    )
                    return response in ["y", "yes"]
                except (EOFError, KeyboardInterrupt):
                    print(f"\n{get_emoji('❌')}Aborted by user")
                    return False

        try:
            # Check if we're in a git repository
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                print(f"{get_emoji('❌')}Not in a git repository")
                return False

            # Get configuration values
            remote_name = config.get_remote_name() if config else "origin"
            max_commits = config.get_max_commits_to_show() if config else 10
            default_pull = config.get_default_pull_answer() if config else "ask"
            default_install = config.get_default_install_answer() if config else "ask"
            install_cmd = (
                config.get_install_command()
                if config
                else "uv tool install --reinstall ."
            )

            # Get current commit before pull
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
            )
            old_commit = result.stdout.strip()

            # Fetch from remote
            print(f"{get_emoji('🔄')}Fetching from {remote_name}...")
            subprocess.run(["git", "fetch", remote_name], check=True)

            # Check if there are updates available
            result = subprocess.run(
                ["git", "rev-list", "--count", "HEAD..@{u}"],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                print(f"{get_emoji('⚠️')}No upstream branch configured")
                return False

            commits_behind = int(result.stdout.strip())

            if commits_behind == 0:
                print(f"{get_emoji('✅')}Already up to date")
                return True

            print(f"{get_emoji('📦')}{commits_behind} new commit(s) available")

            # Show what would be pulled
            print(f"\n{get_emoji('📋')}Changes that would be applied:")
            subprocess.run(
                [
                    "git",
                    "log",
                    "--oneline",
                    "--graph",
                    "HEAD..@{u}",
                    f"--max-count={max_commits}",
                ]
            )

            # Ask user if they want to pull
            if not ask_user("Pull these changes?", default_pull):
                print(f"{get_emoji('❌')}Update cancelled")
                return False

            # Pull the changes
            print(f"{get_emoji('⬇️')}Pulling changes...")
            subprocess.run(["git", "pull"], check=True)

            # Get new commit after pull
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
            )
            new_commit = result.stdout.strip()

            if old_commit == new_commit:
                print(f"{get_emoji('✅')}No changes were pulled")
                return True

            print(f"{get_emoji('✅')}Successfully updated!")

            # Show the actual changes that were applied
            print(f"\n{get_emoji('📝')}Applied changes:")
            subprocess.run(
                ["git", "log", "--oneline", "--graph", f"{old_commit}..{new_commit}"]
            )

            # Ask if user wants to reinstall
            if ask_user("Reinstall with uv tool?", default_install):
                print(f"{get_emoji('🔄')}Reinstalling...")
                try:
                    # Try to get the package name from pyproject.toml
                    package_name = "mydevtools"  # fallback
                    try:
                        import tomllib

                        with open("pyproject.toml", "rb") as f:
                            data = tomllib.load(f)
                            package_name = data.get("project", {}).get(
                                "name", package_name
                            )
                    except Exception as e:
                        print(f"Warning: Could not parse pyproject.toml: {e}")

                    # Use configured install command
                    if " " in install_cmd:
                        cmd_parts = install_cmd.split()
                    else:
                        cmd_parts = [install_cmd]

                    subprocess.run(cmd_parts, check=True)
                    print(f"{get_emoji('✅')}Successfully reinstalled {package_name}!")
                except subprocess.CalledProcessError as e:
                    print(f"{get_emoji('❌')}Installation failed: {e}")
                    print(f"{get_emoji('💡')}Try manually: {install_cmd}")
                    return False
            else:
                print(f"{get_emoji('⚠️')}Skipped installation")
                print(f"{get_emoji('💡')}Run '{install_cmd}' to install manually")

            return True

        except subprocess.CalledProcessError as e:
            print(f"{get_emoji('❌')}Git operation failed: {e}")
            return False
        except Exception as e:
            print(f"{get_emoji('❌')}Unexpected error: {e}")
            return False

    return {
        "actions": [update_from_remote],
        "verbosity": 2,
    }


def task_update_all():
    """Update everything: git, UV dependencies, and Nix flake."""

    def update_all_deps():
        """Update all dependency sources."""
        import os
        import subprocess

        def get_emoji(emoji: str) -> str:
            return emoji + " "

        print(f"{get_emoji('🔄')}Updating all dependencies...")

        # 1. Update UV dependencies
        print(f"\n{get_emoji('📦')}Updating Python dependencies with UV...")
        try:
            subprocess.run(["uv", "sync", "--upgrade"], check=True)
            print(f"{get_emoji('✅')}UV dependencies updated")
        except subprocess.CalledProcessError as e:
            print(f"{get_emoji('❌')}UV update failed: {e}")

        # 2. Update Nix flake (if available)
        if os.path.exists("flake.nix"):
            print(f"\n{get_emoji('❄️')}Updating Nix flake dependencies...")
            try:
                subprocess.run(["nix", "flake", "update"], check=True)
                print(f"{get_emoji('✅')}Nix dependencies updated")
            except subprocess.CalledProcessError as e:
                print(f"{get_emoji('❌')}Nix update failed: {e}")
            except FileNotFoundError:
                print(f"{get_emoji('⚠️')}Nix not available, skipping flake update")
        else:
            print(f"{get_emoji('⚠️')}No flake.nix found, skipping Nix update")

        # 3. Update pre-commit hooks
        print(f"\n{get_emoji('🪝')}Updating pre-commit hooks...")
        try:
            subprocess.run(["pre-commit", "autoupdate"], check=True)
            print(f"{get_emoji('✅')}Pre-commit hooks updated")
        except subprocess.CalledProcessError as e:
            print(f"{get_emoji('❌')}Pre-commit update failed: {e}")
        except FileNotFoundError:
            print(f"{get_emoji('⚠️')}Pre-commit not available")

        print(f"\n{get_emoji('🎉')}All updates completed!")
        print(f"{get_emoji('💡')}Run 'doit nix_env_info' to check your environment")

    return {
        "actions": [update_all_deps],
        "verbosity": 2,
    }


def task_loc():
    """Count lines of code (LOC) for src and tests using tokei.

    - Shows separate counts for src and tests plus a combined total
    - Requires the 'tokei' binary. If unavailable, the task degrades gracefully.
    """
    import shutil

    if shutil.which("tokei") is None:
        # Hide task entirely when tokei is not available
        return None

    def _calc_and_print_loc():
        import json
        from pathlib import Path as _Path
        import subprocess

        def run_tokei(path: str) -> dict:
            if not _Path(path).exists():
                return {"code": 0, "comments": 0, "blanks": 0}
            try:
                result = subprocess.run(
                    ["tokei", path, "--output", "json"],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=60,
                )
            except subprocess.TimeoutExpired:
                print(f"Timeout while running tokei on '{path}'.")
                return {"code": 0, "comments": 0, "blanks": 0}

            try:
                data = json.loads(result.stdout or "{}")
            except json.JSONDecodeError:
                print(
                    f"Failed to parse tokei output for '{path}'. Raw output:\n{result.stdout}"
                )
                return {"code": 0, "comments": 0, "blanks": 0}

            if isinstance(data, dict) and isinstance(data.get("Total"), dict):
                stats_total = data["Total"]
                code = int(stats_total.get("code", 0))
                comments = int(stats_total.get("comments", 0))
                blanks = int(stats_total.get("blanks", 0))
            else:
                code = comments = blanks = 0
                for stats in data.values():
                    # Each value should be a dict with code/comments/blanks
                    if isinstance(stats, dict):
                        code += int(stats.get("code", 0))
                        comments += int(stats.get("comments", 0))
                        blanks += int(stats.get("blanks", 0))
            return {"code": code, "comments": comments, "blanks": blanks}

        def fmt(stats: dict) -> str:
            total = stats["code"] + stats["comments"] + stats["blanks"]
            return (
                f"code={stats['code']:,} comments={stats['comments']:,} "
                f"blanks={stats['blanks']:,} total={total:,}"
            )

        def run_tokei_languages(path: str) -> dict:
            """Return per-language stats {lang: {code, comments, blanks}}."""
            from collections import defaultdict

            if not _Path(path).exists():
                return {}
            try:
                result = subprocess.run(
                    ["tokei", path, "--output", "json"],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=60,
                )
            except subprocess.TimeoutExpired:
                return {}
            try:
                data = json.loads(result.stdout or "{}")
            except json.JSONDecodeError:
                return {}
            agg: dict[str, dict[str, int]] = defaultdict(
                lambda: {"code": 0, "comments": 0, "blanks": 0}
            )
            if isinstance(data, dict):
                for lang, stats in data.items():
                    if lang == "Total" or not isinstance(stats, dict):
                        continue
                    agg[lang]["code"] += int(stats.get("code", 0))
                    agg[lang]["comments"] += int(stats.get("comments", 0))
                    agg[lang]["blanks"] += int(stats.get("blanks", 0))
            return dict(agg)

        src_stats = run_tokei("src")
        tests_stats = run_tokei("tests")
        total_stats = {
            "code": src_stats["code"] + tests_stats["code"],
            "comments": src_stats["comments"] + tests_stats["comments"],
            "blanks": src_stats["blanks"] + tests_stats["blanks"],
        }

        print("LOC summary (tokei):")
        print(f" - src:   {fmt(src_stats)}")
        print(f" - tests: {fmt(tests_stats)}")
        print(f" - total: {fmt(total_stats)}")

        # Per-language view (top 10 by total code)
        src_lang = run_tokei_languages("src")
        tests_lang = run_tokei_languages("tests")
        langs = set(src_lang) | set(tests_lang)
        if langs:

            def total_code(lang: str) -> int:
                return int(src_lang.get(lang, {}).get("code", 0)) + int(
                    tests_lang.get(lang, {}).get("code", 0)
                )

            top_sorted = sorted(langs, key=total_code, reverse=True)
            top_sorted = top_sorted[:10]
            print("\nPer-language (top 10 by code):")
            for lang in top_sorted:
                s_code = int(src_lang.get(lang, {}).get("code", 0))
                t_code = int(tests_lang.get(lang, {}).get("code", 0))
                tot = s_code + t_code
                print(f" - {lang}: src={s_code:,} tests={t_code:,} total={tot:,}")

    return {
        "actions": [_calc_and_print_loc],
        "verbosity": 2,
    }


# Note: Use 'doit list' to see all available tasks


# Configuration
DODOFILE_ENCODING = "utf-8"
