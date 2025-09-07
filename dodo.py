"""PyDoit tasks.

PyDoit is a task management and automation tool for Python projects.
For agents: Run `uv run doit list` to see all available tasks.
Run `uv run doit list | grep agent-` to see agent events.
Use `uv run doit info <task>` to inspect task dependencies and details.

See https://pydoit.org/ for complete documentation.
"""

# Add paths for local development
from pathlib import Path
import os
import sys

# Add vendor directory for vendored mydevtools
vendor_dir = Path(__file__).parent / "vendor"
sys.path.insert(0, str(vendor_dir))

# Add src to path for local development
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Visual output helpers
from rich.console import Console

from mydevtools.task_helpers import (
    create_uv_commands,
    run_subprocess,
)

console = Console()

DODO_CONFIG = {
    "default_tasks": ["default"],
    "verbosity": 2,
}

def create_commands(*commands, **kwargs):
    """Create commands that work in both Nix and uv environments."""
    # Check if we're in Nix environment (has NIX_STORE in environment)
    in_nix = os.environ.get("NIX_STORE") is not None

    if in_nix:
        # In Nix environment, use tools directly
        return {"actions": list(commands), **kwargs}
    else:
        # In uv environment, use uv run prefix
        return create_uv_commands(*commands, **kwargs)

def task_default():
    """Run essential development tasks without agent events."""
    return {
        "actions": None,
        "task_dep": [
            "tool_check",
            "validate_pyproject",
            "validate_python_syntax",
            "fix",
            "format",
            "check_strict",
            "test",
            "build",
        ],
        "verbosity": 2,
    }


### Tasks for human interaction
### AGENTS: don't run these tasks directly, use agent-* events instead!


def task_tool_check():
    """Validate ALL expected tools are available."""
    def run_validation():
        from mydevtools.task_helpers import validate_all_tools
        return validate_all_tools()

    return {
        "actions": [run_validation],
        "verbosity": 2,
    }


def task_validate_todo():
    """Validate TODO syntax, structure, and mdformat compliance."""
    def run_validation():
        from mydevtools.task_helpers import validate_todo
        return validate_todo()

    return {
        "actions": [run_validation],
        "verbosity": 2,
    }


def task_validate_todo_phase_discipline():
    """Validate TODO phase discipline - block [x] checkboxes in TODO phase."""
    def run_validation():
        from mydevtools.task_helpers import validate_todo_discipline, validate_no_code_in_todo
        validate_todo_discipline()
        validate_no_code_in_todo()

    return {
        "actions": [run_validation],
        "verbosity": 2,
    }


def task_validate_todo_files_only():
    """Validate that only _TODO-AGENT.md is modified in TODO phase."""
    def run_validation():
        from mydevtools.task_helpers import validate_todo_files_only
        return validate_todo_files_only()

    return {
        "actions": [run_validation],
        "verbosity": 2,
    }


def task_validate_impl_progress():
    """Validate progress - no commit allowed without checkbox progress."""
    def run_validation():
        from mydevtools.task_helpers import validate_impl_progress
        return validate_impl_progress()

    return {
        "actions": [run_validation],
        "verbosity": 2,
    }


def task_format():
    """Run all normal formatting tasks (after ruff check)."""
    return {
        "actions": None,
        "task_dep": [
            "check_ruff",
            "format_ruff",
            "format_markdown",
        ],
    }


def task_format_markdown():
    """Format markdown files with mdformat."""
    def run_format():
        from mydevtools.task_helpers import format_todo_markdown
        return format_todo_markdown()

    return {
        "actions": [run_format],
        "verbosity": 2,
    }


def task_format_ruff():
    """Format code with ruff and apply autofixes (src only)."""
    return create_commands("ruff format src/", verbosity=2)


def task_check_ruff():
    """Check code with ruff (src only)."""
    return create_commands("ruff check src/", verbosity=2)


def task_fix():
    """Fix code quality issues automatically."""
    return {
        "actions": None,
        "task_dep": [
            "fix_ruff",
        ],
    }


def task_check_pylint_duplicates():
    """Check for duplicate code with Pylint."""
    return create_commands("pylint src/", verbosity=2)


def task_check_radon_metrics():
    """Check code quality metrics with Radon."""
    return {
        "actions": [
            "echo '=== Cyclomatic Complexity ==='",
            "radon cc src/ --total-average",
            "echo '=== Maintainability Index ==='",
            "radon mi src/",
        ],
        "verbosity": 2,
    }


def task_check_security():
    """Check for security issues with Bandit."""
    return create_commands("bandit -r src/", verbosity=2)


def task_check_dead_code():
    """Check for dead code with Vulture."""
    return create_commands("vulture src/ --min-confidence 80", verbosity=2)


def task_fix_ruff():
    """Check Python code with Ruff and apply safe and unsafe autofixes (src only)."""
    return create_commands("ruff check --fix --unsafe-fixes src/", verbosity=2)


def task_validate():
    """Validate everything."""
    return {
        "actions": None,
        "task_dep": [
            "validate_pyproject",
            "validate_python_syntax",
            "validate_todo",
            "validate_todo_phase_discipline",
        ],
    }


def task_validate_pyproject():
    """Validate pyproject.toml files."""
    if os.environ.get("NIX_STORE") is not None:
        # In Nix environment, skip this check (validate-pyproject not available)
        return {"actions": ["echo 'Skipping pyproject validation in Nix environment'"], "verbosity": 2}
    else:
        # In uv environment, use validate-pyproject
        return create_commands("validate-pyproject pyproject.toml", verbosity=2)


def task_validate_python_syntax():
    """Fast Python syntax checks using ruff error selectors."""
    return create_commands("ruff check --select E9,F63,F7,F82", verbosity=2)


def task_check():
    """Run all normal checks."""
    def run_checks():
        from mydevtools.task_helpers import run_linting_with_warnings
        return run_linting_with_warnings()

    return {
        "actions": [run_checks],
        "task_dep": [
            "validate_pyproject",
            "validate_python_syntax",
            "validate_todo_files_only",
        ],
        "verbosity": 2,
    }


def task_check_strict():
    """Run all checks with hard failures (recommended for CI)."""
    return {
        "actions": [],
        "task_dep": [
            "check_ruff",
            "check_pylint_duplicates",
            "check_radon_metrics",
            "check_security",
            "check_dead_code",
        ],
        "verbosity": 2,
    }


def task_test():
    """Run tests."""
    return create_commands("pytest", verbosity=2)


def task_test_cov():
    """Run tests with coverage."""
    return create_commands(
        "coverage run -m pytest",
        "coverage report",
        "coverage html",
        verbosity=2,
    )


def task_cleanup():
    """Clean build/test artifacts and caches."""
    def run_cleanup():
        from mydevtools.task_helpers import clean_artifacts
        return clean_artifacts()

    return {
        "actions": [run_cleanup],
        "verbosity": 2,
    }


def task_build():
    """Build package."""
    return create_commands(
        "python -m build", task_dep=["validate_pyproject", "test"], verbosity=2,
    )


def task_dev_setup():
    """Complete development setup."""
    if os.environ.get("NIX_STORE") is not None:
        # In Nix environment, use uv directly
        return {"actions": ["uv sync --all-groups"], "verbosity": 2}
    else:
        # In uv environment, use uv run
        return create_uv_commands("--all-groups", action="sync", verbosity=2)


# Removed duplicate task_loc definition - using the one from line 37


# Agent workflow event tasks (dash-case exposed via basename)


def task_agent_status():
    """Show comprehensive agent development status (enhanced version)."""
    def run_status():
        from mydevtools.task_helpers import show_agent_status
        return show_agent_status()

    yield {
        "basename": "agent-status",
        "actions": [run_status],
        "verbosity": 2,
    }


def task_agent_start():
    """AGENTS start here, call this before doing anything else."""
    def run_start():
        from mydevtools.task_helpers import show_agent_start
        return show_agent_start()

    yield {
        "basename": "agent-start",
        "actions": [run_start],
        "verbosity": 2,
    }


def task_agent_phase_todo():
    """Switch to TODO phase (planning phase)."""
    def run_switch():
        from mydevtools.task_helpers import switch_to_todo
        return switch_to_todo()

    yield {
        "basename": "agent-phase-todo",
        "actions": [run_switch],
        "verbosity": 2,
    }


def task_agent_phase_impl():
    """Switch to IMPL phase (implementation phase)."""
    def run_switch():
        from mydevtools.task_helpers import show_todo_end, switch_to_impl
        show_todo_end()
        switch_to_impl()

    yield {
        "basename": "agent-phase-impl",
        "actions": [run_switch],
        "task_dep": [
            "validate_todo",
            "validate_todo_phase_discipline",
        ],
        "verbosity": 2,
    }


def task_agent_todo_start():
    """Agent event: Work on todos - planning workflow engaged."""
    def run_start():
        from mydevtools.task_helpers import show_todo_start
        return show_todo_start()

    yield {
        "basename": "agent-todo-start",
        "actions": [run_start],
        "task_dep": [
            "validate_todo",
            "validate_todo_phase_discipline",
        ],
        "verbosity": 2,
    }


def task_agent_coding_start():
    """Agent event: Beginning of coding session (quick checks)."""
    def run_start():
        from mydevtools.task_helpers import show_start
        return show_start()

    yield {
        "basename": "agent-coding-start",
        "actions": [run_start],
        "task_dep": ["tool_check", "validate"],
        "verbosity": 2,
    }


def task_agent_coding_checkpoint():
    """Agent event: During coding - fast validation and formatting."""
    def run_checkpoint():
        from mydevtools.task_helpers import show_checkpoint
        return show_checkpoint()

    yield {
        "basename": "agent-coding-checkpoint",
        "actions": [run_checkpoint],
        "task_dep": ["validate_python_syntax", "fix_ruff", "format"],
        "verbosity": 2,
    }


def task_agent_coding_task_finished():
    """Mark coding task as finished in agent workflow."""
    def run_finished():
        from mydevtools.task_helpers import show_coding_task_finished
        return show_coding_task_finished()

    yield {
        "basename": "agent-coding-task-finished",
        "actions": [run_finished],
        "task_dep": [
            "check",
            "test",
        ],
    }


def task_agent_pre_commit():
    """Agent event pre commit - strict check + tests with coverage + build."""
    def run_pre_commit():
        from mydevtools.task_helpers import show_pre_commit
        return show_pre_commit()

    yield {
        "basename": "agent-pre-commit",
        "actions": [run_pre_commit],
        "task_dep": ["check_strict", "test", "build"],
    }


def task_agent_post_commit():
    """Agent event post commit - cleanup."""
    def run_post_commit():
        from mydevtools.task_helpers import show_post_commit
        return show_post_commit()

    yield {
        "basename": "agent-post-commit",
        "actions": [run_post_commit],
        "task_dep": ["cleanup"],
        "verbosity": 2,
    }


def task_agent_show_workflow():
    """Agent event: Display workflow diagrams and guidance."""
    def run_show_workflow():
        from mydevtools.task_helpers import show_workflow
        return show_workflow()

    yield {
        "basename": "agent-show-workflow",
        "actions": [run_show_workflow],
        "verbosity": 2,
    }
