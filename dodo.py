"""PyDoit tasks.

PyDoit is a task management and automation tool for Python projects.
For agents: Run `uv run doit list` to see all available tasks.
Run `uv run doit list | grep agent-` to see agent events.
Use `uv run doit info <task>` to inspect task dependencies and details.

See https://pydoit.org/ for complete documentation.
"""

# Add src and vendor to path for local development
from pathlib import Path
import sys

# Add src directory
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Add vendor directory for mydevtools
vendor_path = str(Path(__file__).parent / "vendor")
if vendor_path not in sys.path:
    sys.path.insert(0, vendor_path)

# Visual output helpers
from mydevtools.task_helpers import (
    clean_artifacts,
    create_uv_commands,
    format_todo_markdown,
    run_linting_with_warnings,
    show_agent_start,
    show_agent_status,
    show_checkpoint,
    show_coding_task_finished,
    show_post_commit,
    show_pre_commit,
    show_start,
    show_todo_end,
    show_todo_start,
    show_workflow,
    switch_to_impl,
    switch_to_todo,
    validate_all_tools,
    validate_impl_progress,
    validate_no_code_in_todo,
    validate_todo,
    validate_todo_discipline,
    validate_todo_files_only,
)
from rich.console import Console

console = Console()

DODO_CONFIG = {
    "default_tasks": ["default"],
    "verbosity": 2,
}

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
        return validate_all_tools()

    return {
        "actions": [run_validation],
        "verbosity": 2,
    }

def task_validate_todo():
    """Validate TODO syntax, structure, and mdformat compliance."""

    def run_validation():
        return validate_todo()

    return {
        "actions": [run_validation],
        "verbosity": 2,
    }

def task_validate_todo_phase_discipline():
    """Validate TODO phase discipline - block [x] checkboxes in TODO phase."""

    def run_validation():
        validate_todo_discipline()
        validate_no_code_in_todo()

    return {
        "actions": [run_validation],
        "verbosity": 2,
    }

def task_validate_todo_files_only():
    """Validate that only _TODO-AGENT.md is modified in TODO phase."""

    def run_validation():
        return validate_todo_files_only()

    return {
        "actions": [run_validation],
        "verbosity": 2,
    }

def task_validate_impl_progress():
    """Validate progress - no commit allowed without checkbox progress."""

    def run_validation():
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
            "format_todo_markdown",
        ],
    }

def task_format_todo_markdown():
    """Format todo file with mdformat."""
    return {
        "actions": [format_todo_markdown],
    }

def task_format_ruff():
    """Format code with ruff and apply autofixes (src only)."""
    return create_uv_commands("ruff format src/", verbosity=2)

def task_check_ruff():
    """Check code with ruff (src only)."""
    return create_uv_commands("ruff check src/", verbosity=2)

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
    return create_uv_commands("pylint src/", verbosity=2)

def task_check_radon_metrics():
    """Check code quality metrics with Radon."""
    return {
        "actions": [
            "echo '=== Cyclomatic Complexity ==='",
            "uv run radon cc src/ --total-average",
            "echo '=== Maintainability Index ==='",
            "uv run radon mi src/",
        ],
        "verbosity": 2,
    }

def task_check_security():
    """Check for security issues with Bandit."""
    return create_uv_commands("bandit -r src/", verbosity=2)

def task_check_dead_code():
    """Check for dead code with Vulture."""
    return create_uv_commands("vulture src/ --min-confidence 80", verbosity=2)

def task_fix_ruff():
    """Check Python code with Ruff and apply safe and unsafe autofixes (src only)."""
    return create_uv_commands("ruff check --fix --unsafe-fixes src/", verbosity=2)

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
    return create_uv_commands("validate-pyproject pyproject.toml", verbosity=2)

def task_validate_python_syntax():
    """Fast Python syntax checks using ruff error selectors."""
    return create_uv_commands("ruff check --select E9,F63,F7,F82", verbosity=2)

def task_check():
    """Run all normal checks."""

    def run_checks():
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
    """Run all tests."""
    return create_uv_commands("pytest", verbosity=2)

def task_test_unit():
    """Run unit tests only."""
    return create_uv_commands('pytest -m "not integration"', verbosity=2)

def task_test_integration():
    """Run integration tests only."""
    return create_uv_commands('pytest -m "integration"', verbosity=2)

def task_test_cov():
    """Run tests with coverage."""
    return create_uv_commands(
        "coverage run -m pytest",
        "coverage report",
        "coverage html",
        verbosity=2,
    )

def task_test_cov_unit():
    """Run unit tests with coverage."""
    return create_uv_commands(
        'coverage run -m pytest -m "not integration"',
        "coverage report",
        "coverage html",
        verbosity=2,
    )

def task_test_cov_integration():
    """Run integration tests with coverage."""
    return create_uv_commands(
        'coverage run -m pytest -m "integration"',
        "coverage report",
        "coverage html",
        verbosity=2,
    )

def task_cleanup():
    """Clean build/test artifacts and caches."""

    def run_cleanup():
        return clean_artifacts()

    return {
        "actions": [run_cleanup],
        "verbosity": 2,
    }

def task_build():
    """Build package."""
    return create_uv_commands(
        "python -m build",
        task_dep=["validate_pyproject", "test"],
        verbosity=2,
    )

def task_dev_setup():
    """Complete development setup."""
    return create_uv_commands("--all-groups", action="sync", verbosity=2)


# Removed duplicate task_loc definition - using the one from line 37


# Agent workflow event tasks (dash-case exposed via basename)

def task_agent_status():
    """Show comprehensive agent development status (enhanced version)."""

    def run_status():
        return show_agent_status()

    yield {
        "basename": "agent-status",
        "actions": [run_status],
        "verbosity": 2,
    }

def task_agent_start():
    """AGENTS start here, call this before doing anything else."""

    def run_start():
        return show_agent_start()

    yield {
        "basename": "agent-start",
        "actions": [run_start],
        "verbosity": 2,
    }

def task_switch_to_todo_phase():
    """Switch to TODO phase (planning phase)."""

    def run_switch():
        return switch_to_todo()

    yield {
        "basename": "switch_to_todo_phase",
        "actions": [run_switch],
        "verbosity": 2,
    }

def task_switch_to_impl_phase():
    """Switch to IMPL phase (implementation phase)."""

    def run_switch():
        show_todo_end()
        switch_to_impl()

    yield {
        "basename": "switch_to_impl_phase",
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
        return show_checkpoint()

    yield {
        "basename": "agent-coding-checkpoint",
        "actions": [run_checkpoint],
        "task_dep": ["validate_python_syntax", "fix_ruff", "format"],
        "verbosity": 2,
    }

def task_agent_coding_task_finished():
    """Update agent workflow status after coding task completion."""

    def run_finished():
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
        return show_pre_commit()

    yield {
        "basename": "agent-pre-commit",
        "actions": [run_pre_commit],
        "task_dep": ["check_strict", "test", "build"],
    }

def task_agent_post_commit():
    """Agent event post commit - cleanup."""

    def run_post_commit():
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
        return show_workflow()

    yield {
        "basename": "agent-show-workflow",
        "actions": [run_show_workflow],
        "verbosity": 2,
    }
