"""Generic task helper utilities for mydevtools.

This module provides a comprehensive set of reusable utility functions that work
with any task runner, not just dodo. These utilities were extracted from dodo.py
to provide value across different contexts and projects.

## Key Features

- **Universal Compatibility**: All functions work standalone without dodo context
- **Test-Driven Design**: Comprehensive test coverage with working examples
- **Structured Logging**: Detailed debug information for troubleshooting
- **Error Resilience**: Graceful handling of edge cases and failures
- **Configuration Flexibility**: Configurable paths and behavior

## Function Categories

### Command Execution
- `run_subprocess()`: Centralized subprocess wrapper with output control
- `create_uv_commands()`: Create uv command action dictionaries
- `check_tool_available()`: Verify tool availability via uv

### Phase Management
- `get_current_phase()`: Read current workflow phase from file
- `set_phase()`: Update workflow phase with validation

### TODO Analysis
- `count_todo_checkboxes()`: Analyze markdown checkbox progress
- `validate_todo_phase_discipline()`: Enforce phase-based workflow rules

### Workflow Management
- `get_workflow_state()`: Read workflow status from JSON files
- `suggest_next_actions()`: Generate intelligent action suggestions

### Status Display
- `create_status_table()`: Rich table formatting for status displays
- `create_phase_panel()`: Rich panel formatting for phase information
- `get_git_status()`: Comprehensive git repository status with caching

## Configuration

The module uses several configurable constants:

- `PHASE_FILE`: Path to phase tracking file (default: ".agent-phase")
- `PHASE_TODO`: TODO phase identifier (default: "TODO")
- `PHASE_IMPL`: Implementation phase identifier (default: "IMPL")

## Usage Examples

### Basic Tool Checking
```python
from mydevtools.task_helpers import check_tool_available

# Check if pytest is available
result = check_tool_available("pytest")
if result and result.returncode == 0:
    print("pytest is available")
```

### Phase Management
```python
from mydevtools.task_helpers import get_current_phase, set_phase

# Get current phase
phase = get_current_phase()
print(f"Current phase: {phase}")

# Switch to implementation phase
set_phase("IMPL")
```

### TODO Analysis
```python
from mydevtools.task_helpers import count_todo_checkboxes

# Analyze TODO progress
progress = count_todo_checkboxes("my-todo.md")
print(f"Progress: {progress['progress_text']}")
if progress['next_item']:
    print(f"Next task: {progress['next_item']}")
```

### Workflow Integration
```python
from mydevtools.task_helpers import get_workflow_state, suggest_next_actions

# Get current workflow state
workflow = get_workflow_state()
phase_info = {"current_phase": get_current_phase()}
git_info = get_git_status()
todo_info = count_todo_checkboxes()

# Get action suggestions
actions = suggest_next_actions(phase_info, workflow, git_info, todo_info)
for action in actions:
    print(f"{action['icon']} {action['action']}: {action['reason']}")
```

## Error Handling

All functions include comprehensive error handling:

- File operations gracefully handle missing files
- Subprocess calls include timeouts and exception handling
- Invalid input is validated with clear error messages
- Logging provides detailed debugging information

## Testing

The module includes extensive doctests and unit tests. Run tests with:

```bash
uv run pytest tests/test_task_helpers.py -v
uv run python -m doctest src/mydevtools/task_helpers.py -v
```

All functions are designed to work standalone without dodo context.
"""

import contextlib
import functools
import json
import logging
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

logger = logging.getLogger(__name__)

console = Console()

# Phase management constants
PHASE_FILE = Path(".agent-phase")
PHASE_TODO = "TODO"
PHASE_IMPL = "IMPL"

# Message hierarchy constants
MSG_CRITICAL = "CRITICAL"
MSG_WARNING = "WARNING"
MSG_INFO = "INFO"
MSG_DEBUG = "DEBUG"

# Message level priorities (higher number = higher priority)
MSG_LEVELS = {
    MSG_CRITICAL: 4,
    MSG_WARNING: 3,
    MSG_INFO: 2,
    MSG_DEBUG: 1,
}


# Cache for file content to reduce redundant reads
@functools.lru_cache(maxsize=8)
def _read_file_cached(file_path: str, mtime: float) -> str:
    """Cache file content based on path and modification time.

    This function provides caching for file reads to avoid redundant I/O
    operations. The cache key includes the modification time to ensure
    cache invalidation when files are updated.

    Args:
        file_path: Path to the file to read
        mtime: File modification time (used for cache invalidation)

    Returns:
        File content as string

    Examples:
        >>> # This will read from disk
        >>> content1 = _read_file_cached("test.txt", 1234567890.0)
        >>> # This will use cached content (same mtime)
        >>> content2 = _read_file_cached("test.txt", 1234567890.0)
        >>> content1 == content2
        True

    """
    # Note: mtime parameter is used by @functools.lru_cache for cache invalidation
    # When mtime changes, a new cache entry is created automatically
    _ = mtime  # Acknowledge parameter is used by cache mechanism
    return Path(file_path).read_text(encoding="utf-8")


@contextlib.contextmanager
def subprocess_output_control(quiet: bool = True):  # noqa: FBT001,FBT002
    """Context manager for controlling subprocess output display.

    This context manager provides a clean way to control when subprocess
    output should be displayed or suppressed, with automatic cleanup.

    Args:
        quiet: If True, suppress output unless there's an error

    Yields:
        A function that can be called with (result, show_on_error=True)
        to conditionally display subprocess output

    Examples:
        >>> with subprocess_output_control(quiet=True) as show_output:
        ...     result = subprocess.run(["echo", "test"], capture_output=True, text=True)
        ...     show_output(result)  # Only shows if error occurred

    """

    def show_output(
        result: subprocess.CompletedProcess[str],
        show_on_error: bool = True,
    ) -> None:
        """Display subprocess output based on context settings."""
        env_verbose = os.environ.get("MYDEVTOOLS_VERBOSE", "").lower()
        force_verbose = env_verbose in ("1", "true", "yes")

        should_show = (
            not quiet or force_verbose or (show_on_error and result.returncode != 0)
        )

        if should_show:
            if result.stdout:
                console.print(result.stdout, end="")
            if result.stderr:
                console.print(f"[red]{result.stderr}[/red]", end="")

    try:
        yield show_output
    finally:
        # Context cleanup if needed
        pass


def should_show_message(level: str, verbose: bool | None = None) -> bool:  # noqa: FBT001
    """Determine if a message should be displayed based on its level and verbosity.

    Args:
        level: Message level (CRITICAL, WARNING, INFO, DEBUG)
        verbose: Whether verbose mode is enabled (auto-detected from env if None)

    Returns:
        True if the message should be displayed, False otherwise

    """
    if verbose is None:
        # Auto-detect verbose mode from environment
        env_verbose = os.environ.get("MYDEVTOOLS_VERBOSE", "").lower()
        verbose = env_verbose in ("1", "true", "yes")

    logger.debug(
        "checking-message-visibility",
        level=level,
        verbose_provided=verbose is not None,
        auto_detected_verbose=verbose,
    )

    if verbose:
        logger.debug("message-visible-due-to-verbose-mode", level=level)
        return True

    # In non-verbose mode, only show CRITICAL and WARNING messages
    result = level in [MSG_CRITICAL, MSG_WARNING]
    logger.debug(
        "message-visibility-determined",
        level=level,
        visible=result,
        reason="verbose_mode" if verbose else "level_filter",
    )
    return result


def format_message_with_level(level: str, message: str) -> str:
    """Format a message with appropriate styling based on its level.

    Args:
        level: Message level
        message: The message content

    Returns:
        Formatted message string with appropriate colors/icons

    """
    logger.debug(
        "formatting-message-with-level",
        level=level,
        message_length=len(message),
    )

    level_icons = {
        MSG_CRITICAL: "! ",
        MSG_WARNING: "! ",
        MSG_INFO: "i",
        MSG_DEBUG: "-",
    }

    level_colors = {
        MSG_CRITICAL: "bold red",
        MSG_WARNING: "yellow",
        MSG_INFO: "cyan",
        MSG_DEBUG: "dim white",
    }

    icon = level_icons.get(level, "-")
    color = level_colors.get(level, "white")

    formatted = f"{icon} [{color}]{level}[/{color}]: {message}"

    logger.debug(
        "message-formatted",
        level=level,
        icon=icon,
        color=color,
        formatted_length=len(formatted),
    )

    return formatted


def run_subprocess(
    cmd: list[str],
    *,
    quiet: bool = True,
    timeout: float | None = None,
    check: bool = False,
    **kwargs: Any,
) -> subprocess.CompletedProcess[str]:
    """Centralized subprocess wrapper with output control.

    This function provides a unified interface for running subprocess commands
    with smart output handling. It supports quiet mode (suppress stdout on success)
    and verbose mode (show all output).

    Args:
        cmd: Command to run as a list of strings
        quiet: If True, suppress stdout on success (default: True)

    Returns:
        CompletedProcess object with result information

    Environment Variables:
        MYDEVTOOLS_VERBOSE: If set to "1" or "true", forces verbose mode

    Examples:
        >>> # Quiet mode (default) - only shows output on failure
        >>> result = run_subprocess(["git", "status", "--porcelain"])
        >>> if result.returncode != 0:
        ...     print("Git command failed")

        >>> # Verbose mode - always shows output
        >>> result = run_subprocess(["pytest", "-v"], quiet=False)


        >>> # With timeout and error checking
        >>> result = run_subprocess(
        ...     ["uv", "run", "mypy", "."],
        ...     timeout=30,
        ...     check=True
        ... )

    """
    # Check environment variable for verbose override
    env_verbose = os.environ.get("MYDEVTOOLS_VERBOSE", "").lower()
    force_verbose = env_verbose in ("1", "true", "yes")

    # Determine if we should show output
    show_output = not quiet or force_verbose

    # Set default subprocess arguments
    default_kwargs: dict[str, Any] = {
        "capture_output": True,
        "text": True,
        "timeout": timeout,
        "check": check,  # Use the check parameter value
    }

    # Override with user-provided kwargs
    default_kwargs.update(kwargs)

    logger.debug(
        "subprocess-started",
        cmd=cmd,
        quiet=quiet,
        force_verbose=force_verbose,
        show_output=show_output,
        timeout=timeout,
    )

    try:
        check_value = default_kwargs.pop("check", False)
        result = subprocess.run(cmd, check=check_value, **default_kwargs)  # noqa: S603

        # Log the result
        logger.debug(
            "subprocess-completed",
            cmd=cmd,
            returncode=result.returncode,
            stdout_length=len(result.stdout)
            if result.stdout and hasattr(result.stdout, "__len__")
            else 0,
            stderr_length=len(result.stderr)
            if result.stderr and hasattr(result.stderr, "__len__")
            else 0,
        )

        # Show output based on mode and result
        if show_output or result.returncode != 0:
            if result.stdout:
                console.print(result.stdout, end="")
            if result.stderr:
                console.print(f"[red]{result.stderr}[/red]", end="")

        # Handle check parameter
        if check and result.returncode != 0:
            raise subprocess.CalledProcessError(  # noqa: TRY301
                result.returncode,
                cmd,
                result.stdout,
                result.stderr,
            )

        return result  # noqa: TRY300

    except subprocess.TimeoutExpired as e:
        logger.exception(
            "subprocess-timeout",
            _replace_msg="Subprocess timed out after {timeout}s: {cmd}",
            cmd=cmd,
            timeout=timeout,
            error=str(e),
        )
        # Re-raise with original exception
        raise
    except Exception as e:
        logger.exception(
            "subprocess-error",
            _replace_msg="Subprocess error for command {cmd}: {error}",
            cmd=cmd,
            error=str(e),
            error_type=type(e).__name__,
        )
        # Re-raise with original exception
        raise


def create_uv_commands(
    *commands: str,
    action: str = "run",
    **kwargs: Any,
) -> dict[str, Any]:
    """Create actions that run commands with uv.

    This is a generic utility that works with any task runner that accepts
    action dictionaries. Creates properly formatted uv command strings.

    Args:
        *commands: Variable number of command strings to run with uv
        action: The uv action to use (default: "run")
        **kwargs: Additional keyword arguments to include in result

    Returns:
        Dictionary with "actions" key containing list of uv commands,
        plus any additional kwargs

    Examples:
        >>> create_uv_commands("pytest")
        {'actions': ['uv run pytest']}

        >>> create_uv_commands("ruff check", "mypy .", verbosity=2)
        {'actions': ['uv run ruff check', 'uv run mypy .'], 'verbosity': 2}

        >>> create_uv_commands("--all-groups", action="sync")
        {'actions': ['uv sync --all-groups']}

    """
    logger.debug(
        "uv-commands-created",
        count=len(commands),
        action=action,
        commands=list(commands),
    )

    actions = [f"uv {action} {command}" for command in commands]

    result = {"actions": actions, **kwargs}

    logger.debug(
        "uv-actions-created",
        count=len(actions),
        keys=list(result.keys()),
    )

    return result


def check_tool_available(
    tool_name: str,
    command: str | None = None,
) -> subprocess.CompletedProcess[str] | None:
    """Check if a tool is available via uv run.

    This is a generic utility for checking tool availability that works
    with any project using uv for dependency management.

    Args:
        tool_name: Name of the tool to check
        command: Custom command to run (default: "{tool_name} --version")

    Returns:
        CompletedProcess result if successful, None if timeout or error

    Examples:
        >>> result = check_tool_available("pytest")
        >>> result is not None  # Returns CompletedProcess or None
        True

        >>> result = check_tool_available("nonexistent-tool-xyz")
        >>> result is not None  # Returns CompletedProcess even for non-existent tools
        True
        >>> result.returncode != 0  # Non-zero return code for non-existent tools
        True

    """
    if command is None:
        command = f"{tool_name} --version"

    logger.debug("tool-availability-check", tool=tool_name, command=command)

    try:
        cmd_parts = ["uv", "run", *command.split()]

        logger.debug("Running subprocess: %s (timeout: 10s)", cmd_parts)

        result = run_subprocess(cmd_parts, quiet=True, timeout=10)

        # Handle Mock objects in tests by checking for len() availability
        stdout_len = 0
        stderr_len = 0
        with contextlib.suppress(TypeError, AttributeError):
            stdout_len = len(result.stdout) if result.stdout else 0
            stderr_len = len(result.stderr) if result.stderr else 0

        logger.debug(
            "tool-check-completed",
            tool=tool_name,
            returncode=result.returncode,
            stdout_len=stdout_len,
            stderr_len=stderr_len,
        )

        return result  # noqa: TRY300

    except subprocess.TimeoutExpired:
        logger.warning(
            "tool-check-timeout",
            _replace_msg="Tool '{tool}' check timed out after 10 seconds (command: {command})",
            tool=tool_name,
            command=command,
        )
        return None

    except Exception as e:
        logger.exception(
            "tool-check-failed",
            _replace_msg="Tool '{tool}' check failed with exception: {error} (command: {command})",
            tool=tool_name,
            error=str(e),
            command=command,
        )
        return None


def get_current_phase() -> str:
    """Get current agent phase (TODO or IMPL).

    This is a generic utility for file-based phase tracking that works
    with any phase-based workflow system.

    Returns:
        Current phase as string ("TODO" or "IMPL"). Defaults to "TODO"
        if no phase file exists or contains invalid content.

    Examples:
        >>> phase = get_current_phase()
        >>> phase in ["TODO", "IMPL"]
        True

        >>> # Test with temporary phase file
        >>> import tempfile
        >>> from pathlib import Path
        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     phase_file = Path(tmpdir) / ".agent-phase"
        ...     _ = phase_file.write_text("IMPL")
        ...     # Would return "IMPL" if PHASE_FILE pointed to this location
        ...     "IMPL" in ["TODO", "IMPL"]  # Demonstrates valid phases
        True

    """
    logger.debug("Reading current phase from file: %s", PHASE_FILE)

    try:
        if PHASE_FILE.exists():
            phase_content = PHASE_FILE.read_text().strip().upper()
            logger.debug("Phase file content: %s", phase_content)

            if phase_content in [PHASE_TODO, PHASE_IMPL]:
                logger.debug("Valid phase found: %s", phase_content)
                return phase_content
            else:
                logger.warning(
                    "invalid-phase-content",
                    _replace_msg="Invalid phase content '{content}' in {file}, defaulting to {default}",
                    phase_content=phase_content,
                    phase_file=PHASE_FILE,
                    default_phase=PHASE_TODO,
                )
        else:
            logger.debug(
                "Phase file %s does not exist, defaulting to %s",
                PHASE_FILE,
                PHASE_TODO,
            )

    except Exception as e:
        logger.error(  # noqa: G201
            "Error reading phase file %s: %s, defaulting to %s",
            PHASE_FILE,
            e,
            PHASE_TODO,
            exc_info=True,
        )

    # Default to TODO phase if no phase file exists or on any error
    return PHASE_TODO


def set_phase(phase: str) -> None:
    """Set agent phase and create/update phase file.

    This is a generic utility for file-based phase tracking that works
    with any phase-based workflow system.

    Args:
        phase: Phase to set ("TODO" or "IMPL")

    Raises:
        ValueError: If phase is not "TODO" or "IMPL"

    Examples:
        >>> set_phase("TODO")  # Sets phase to TODO
        >>> set_phase("IMPL")  # Sets phase to IMPL

        >>> # Error handling
        >>> try:
        ...     set_phase("INVALID")
        ... except ValueError as e:
        ...     print(f"Error: {e}")
        Error: Invalid phase: INVALID. Must be TODO or IMPL

    """
    if phase not in [PHASE_TODO, PHASE_IMPL]:
        msg = f"Invalid phase: {phase}. Must be {PHASE_TODO} or {PHASE_IMPL}"
        raise ValueError(
            msg,
        )

    logger.debug("Setting phase to %s in file: %s", phase, PHASE_FILE)

    try:
        PHASE_FILE.write_text(phase)
        logger.info(
            "phase-set",
            _replace_msg="Phase successfully set to {phase} in file {file}",
            phase=phase,
            file=str(PHASE_FILE),
        )

    except Exception as e:
        logger.error(  # noqa: G201
            "Failed to write phase %s to file %s: %s",
            phase,
            PHASE_FILE,
            e,
            exc_info=True,
        )
        raise


def count_todo_checkboxes(todo_file_path: str = "_TODO-AGENT.md") -> dict[str, Any]:
    """Count TODO checkboxes and return progress information.

    Generic markdown checkbox analysis that works with any TODO file.
    Supports multiple markdown list prefixes and checkbox formats.

    Args:
        todo_file_path: Path to the TODO file (default: "_TODO-AGENT.md")

    Returns:
        Dictionary containing:
        - total: Total number of checkboxes found
        - completed: Number of completed checkboxes
        - remaining: Number of unchecked checkboxes
        - next_item: Text of first unchecked item (or None)
        - is_complete: True if all checkboxes are completed
        - progress_text: Human-readable progress description
        - completed_items: List of (line_num, line_text) for completed items
        - remaining_items: List of (line_num, line_text) for remaining items

    Examples:
        >>> # Test with non-existent file
        >>> result = count_todo_checkboxes("nonexistent.md")
        >>> result['total'] == 0
        True
        >>> result['progress_text']
        'No TODO file found'

        >>> # Test with current TODO file
        >>> result = count_todo_checkboxes("_TODO-AGENT.md")
        >>> result['total'] >= 0  # Should have some checkboxes
        True

    """
    todo_file = Path(todo_file_path)

    logger.debug("Analyzing TODO checkboxes in file: %s", todo_file)

    if not todo_file.exists():
        logger.warning(
            "todo-file-not-found",
            _replace_msg="TODO file not found: {path}",
            todo_file=str(todo_file),
        )
        return {
            "total": 0,
            "completed": 0,
            "remaining": 0,
            "next_item": None,
            "is_complete": False,
            "progress_text": "No TODO file found",
            "completed_items": [],
            "remaining_items": [],
        }

    try:
        # Use cached file reading for better performance
        file_stat = todo_file.stat()
        content = _read_file_cached(str(todo_file), file_stat.st_mtime)
        lines = content.split("\n")

        completed_items = []
        remaining_items = []
        next_item = None
        in_code_block = False

        # Regex: start optional spaces, then either '-' or '*' or digits+'.', then space, then [x]/[ ]/[OK]
        checkbox_re = re.compile(r"^\s*(?:[-*]|\d+\.)\s+\[(x| |OK)\]\s*(.*)")

        for i, line in enumerate(lines, 1):
            # Track code blocks to ignore checkboxes inside them
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue

            # Skip lines inside code blocks
            if in_code_block:
                continue

            match = checkbox_re.match(line)
            if not match:
                continue

            state = match.group(1)
            text = match.group(2).strip()

            if state.lower() == "x" or state == "OK":
                completed_items.append((i, line.strip()))
                logger.debug("Found completed checkbox at line %d: %s", i, text[:50])
            else:
                remaining_items.append((i, line.strip()))
                if next_item is None:
                    next_item = text
                logger.debug("Found unchecked checkbox at line %d: %s", i, text[:50])

        total = len(completed_items) + len(remaining_items)
        completed = len(completed_items)
        remaining = len(remaining_items)
        is_complete = remaining == 0 and total > 0

        if is_complete:
            progress_text = f"FERTIG - All {total} tasks completed!"
        elif total == 0:
            progress_text = "No checkboxes found"
        else:
            progress_text = f"{completed} of {total} completed"

        logger.info(
            "todo-analysis-complete",
            _replace_msg="TODO analysis complete: {total} total, {completed} completed, {remaining} remaining",
            total=total,
            completed=completed,
            remaining=remaining,
        )

        return {  # noqa: TRY300
            "total": total,
            "completed": completed,
            "remaining": remaining,
            "next_item": next_item,
            "is_complete": is_complete,
            "progress_text": progress_text,
            "completed_items": completed_items,
            "remaining_items": remaining_items,
        }

    except Exception as e:
        logger.error("Error reading TODO file %s: %s", todo_file, e, exc_info=True)  # noqa: G201
        return {
            "total": 0,
            "completed": 0,
            "remaining": 0,
            "next_item": None,
            "is_complete": False,
            "progress_text": f"Error reading TODO: {e}",
            "completed_items": [],
            "remaining_items": [],
        }


def validate_todo_phase_discipline(
    todo_file_path: str = "_TODO-AGENT.md",
    current_phase: str | None = None,
) -> dict[str, Any]:
    """Validate TODO phase discipline - no completed checkboxes allowed in TODO phase.

    Generic phase-based validation that works with any TODO file and phase system.
    Supports multiple markdown list prefixes and checkbox formats.

    Args:
        todo_file_path: Path to the TODO file (default: "_TODO-AGENT.md")
        current_phase: Current phase (if None, will call get_current_phase())

    Returns:
        Dictionary containing:
        - is_valid: True if validation passes
        - violations: List of violation dictionaries with line, content, issue
        - phase: Current phase that was validated
        - total_violations: Number of violations found

    Examples:
        >>> # Test with non-existent file
        >>> result = validate_todo_phase_discipline("nonexistent.md")
        >>> result['is_valid']  # Should be valid if no file exists
        True
        >>> result['total_violations']
        0

        >>> # Test with custom phase (non-TODO phases allow completed checkboxes)
        >>> result = validate_todo_phase_discipline("_TODO-AGENT.md", "IMPL")
        >>> result['is_valid']  # IMPL phase allows completed checkboxes
        True

    """
    if current_phase is None:
        current_phase = get_current_phase()

    logger.debug(
        "Validating TODO phase discipline for phase %s in file: %s",
        current_phase,
        todo_file_path,
    )

    # Only validate in TODO phase - other phases allow completed checkboxes
    if current_phase != PHASE_TODO:
        logger.debug(
            "Not in TODO phase (%s), skipping discipline validation",
            current_phase,
        )
        return {
            "is_valid": True,
            "violations": [],
            "phase": current_phase,
            "total_violations": 0,
        }

    todo_file = Path(todo_file_path)
    if not todo_file.exists():
        logger.debug("TODO file not found, no violations possible: %s", todo_file)
        return {
            "is_valid": True,
            "violations": [],
            "phase": current_phase,
            "total_violations": 0,
        }

    try:
        content = todo_file.read_text(encoding="utf-8")
        lines = content.split("\n")
        violations = []
        in_code_block = False

        # Regex to find completed checkboxes: [x] or [OK] (require space after list marker)
        checkbox_re = re.compile(r"^\s*(?:[-*]|\d+\.)\s+\[(x|OK)\]")

        for i, line in enumerate(lines, 1):
            # Track code blocks to ignore checkboxes inside them
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue

            # Skip lines inside code blocks
            if in_code_block:
                continue

            if checkbox_re.match(line):
                violation = {
                    "line": i,
                    "content": line.strip(),
                    "issue": "Completed checkbox found in TODO phase",
                }
                violations.append(violation)
                logger.warning(
                    "todo-discipline-violation",
                    _replace_msg="TODO phase discipline violation at line {line}: {content}",
                    line_number=i,
                    line_content=line.strip()[:50],
                )

        is_valid = len(violations) == 0
        total_violations = len(violations)

        if is_valid:
            logger.info(
                "todo-discipline-validation-passed",
                _replace_msg="TODO phase discipline validation passed",
            )
        else:
            logger.warning(
                "todo-discipline-validation-failed",
                _replace_msg="TODO phase discipline validation failed with {count} violations",
                total_violations=total_violations,
            )

        return {  # noqa: TRY300
            "is_valid": is_valid,
            "violations": violations,
            "phase": current_phase,
            "total_violations": total_violations,
        }

    except Exception as e:
        logger.error(  # noqa: G201
            "Error reading TODO file %s for discipline validation: %s",
            todo_file,
            e,
            exc_info=True,
        )
        return {
            "is_valid": False,
            "violations": [
                {
                    "line": 0,
                    "content": "",
                    "issue": f"Error reading TODO file: {e}",
                },
            ],
            "phase": current_phase,
            "total_violations": 1,
        }


def get_workflow_state(status_file: str = ".agent-run-status.json") -> dict[str, Any]:
    """Get current workflow state from agent run status file.

    Reads and parses the workflow state file to determine current session status,
    completed events, and workflow progress. Works with any workflow system that
    uses JSON status files.

    Args:
        status_file: Path to the workflow status file (default: ".agent-run-status.json")

    Returns:
        Dictionary containing workflow state information:
        - session_active: Whether a workflow session is currently active
        - session_started: Whether a session has been started
        - events: Dictionary of event names and their completion status
        - last_event: Name of the most recently completed event
        - raw_status: Raw status data from file (if successfully read)
        - error: Error message if file reading failed

    Examples:
        >>> # Test with current workflow state
        >>> state = get_workflow_state()
        >>> 'session_active' in state
        True
        >>> 'events' in state
        True
        >>> isinstance(state['events'], dict)
        True

        >>> # Test with non-existent file
        >>> state = get_workflow_state("nonexistent.json")
        >>> state['session_active']
        False
        >>> state['events']
        {}

    """
    logger.debug("Reading workflow state from %s", status_file)

    run_status_file = Path(status_file)

    if not run_status_file.exists():
        logger.debug("Workflow status file %s does not exist", status_file)
        return {
            "session_active": False,
            "events": {},
            "last_event": None,
            "session_started": False,
        }

    try:
        run_status = json.loads(run_status_file.read_text())
        logger.debug("Successfully read workflow status with %d keys", len(run_status))

        # Extract event information
        events = {}
        last_event = None
        last_event_time = None

        for key, value in run_status.items():
            if key.startswith("agent-") and key != "agent-run-status":
                events[key] = value
                if value and (last_event_time is None):  # Most recent completed event
                    last_event = key

        session_active = run_status.get("session_started", False)
        session_started = run_status.get("session_started", False)

        logger.info(
            "workflow-state-read",
            _replace_msg="Workflow state: session_active={active}, events={count}, last_event={last}",
            active=session_active,
            count=len(events),
            last=last_event,
        )

        return {  # noqa: TRY300
            "session_active": session_active,
            "events": events,
            "last_event": last_event,
            "session_started": session_started,
            "raw_status": run_status,
        }

    except Exception as e:
        logger.error(  # noqa: G201
            "Failed to read workflow state from %s: %s",
            status_file,
            e,
            exc_info=True,
        )
        return {
            "session_active": False,
            "events": {},
            "last_event": None,
            "session_started": False,
            "error": f"Failed to read workflow state: {e}",
        }


def suggest_next_actions(
    phase_info: dict[str, Any],
    workflow_info: dict[str, Any],
    git_info: dict[str, Any],
    todo_info: dict[str, Any],
) -> list[dict[str, Any]]:
    """Generate prioritized list of next action suggestions.

    Analyzes current phase, workflow state, git status, and TODO progress to
    suggest the most appropriate next actions. Works with any workflow system
    that provides structured state information.

    Args:
        phase_info: Dictionary with current_phase key
        workflow_info: Dictionary with session_active, last_event keys
        git_info: Dictionary with is_git_repo, is_clean, modified_count, staged_count keys
        todo_info: Dictionary with completion_rate, remaining keys

    Returns:
        List of action dictionaries, each containing:
        - priority: Action priority level (URGENT, TODO, IMPL, CODE, READY, COMMIT, PHASE)
        - icon: Emoji icon for the action
        - action: Human-readable action description
        - command: Command to execute the action
        - reason: Explanation of why this action is suggested

    Examples:
        >>> # Test basic action suggestion
        >>> actions = suggest_next_actions(
        ...     {"current_phase": "TODO"},
        ...     {"session_active": False, "last_event": None},
        ...     {"is_git_repo": True, "is_clean": True},
        ...     {"completion_rate": 0.5, "remaining": 3}
        ... )
        >>> len(actions) > 0
        True
        >>> actions[0]['priority']
        'TODO'
        >>> 'action' in actions[0]
        True

    """
    logger.debug(
        "Generating action suggestions for phase=%s, workflow=%s",
        phase_info.get("current_phase"),
        workflow_info.get("last_event"),
    )

    suggestions = []

    # Critical alerts (highest priority)
    if git_info.get("is_git_repo") and not git_info.get("is_clean", True):
        modified_count = git_info.get("modified_count", 0) + git_info.get(
            "staged_count",
            0,
        )
        suggestions.append(
            {
                "priority": "URGENT",
                "icon": "! ",
                "action": "Commit uncommitted changes",
                "command": "git add . && git commit",
                "reason": f"{modified_count} files modified",
            },
        )
        logger.info(
            "urgent-action-added",
            _replace_msg="Added urgent action for {count} uncommitted files",
            count=modified_count,
        )

    # Phase-specific workflow suggestions (only most relevant)
    current_phase = phase_info.get("current_phase", "TODO")
    last_event = workflow_info.get("last_event")

    if current_phase == "TODO":
        if not workflow_info.get("session_active", False):
            suggestions.append(
                {
                    "priority": "TODO",
                    "icon": "- ",
                    "action": "Start planning session",
                    "command": "uv run doit agent-todo-start",
                    "reason": "Begin structured TODO planning",
                },
            )
        elif todo_info.get("completion_rate", 0) < 1.0:
            suggestions.append(
                {
                    "priority": "TODO",
                    "icon": "- ",
                    "action": "Continue TODO planning",
                    "command": "Edit _TODO-AGENT.md",
                    "reason": f"Complete {todo_info.get('remaining', 0)} remaining items",
                },
            )
        # Only suggest phase switch when truly complete
        elif todo_info.get("completion_rate", 0) >= 1.0:
            suggestions.append(
                {
                    "priority": "PHASE",
                    "icon": "→",
                    "action": "Switch to implementation phase",
                    "command": "uv run doit agent-phase-impl",
                    "reason": "All TODO items completed",
                },
            )

    elif current_phase == "IMPL":
        if last_event == "agent-start" or not last_event:
            suggestions.append(
                {
                    "priority": "IMPL",
                    "icon": "- ",
                    "action": "Begin coding session",
                    "command": "uv run doit agent-coding-start",
                    "reason": "Start implementation workflow",
                },
            )
        elif last_event == "agent-coding-start":
            suggestions.append(
                {
                    "priority": "CODE",
                    "icon": "CODE",
                    "action": "Make code changes or checkpoint",
                    "command": "uv run doit agent-coding-checkpoint",
                    "reason": "Continue development",
                },
            )
        elif last_event == "agent-coding-checkpoint":
            suggestions.append(
                {
                    "priority": "READY",
                    "icon": "OK ",
                    "action": "Prepare for commit",
                    "command": "uv run doit agent-pre-commit",
                    "reason": "Validate and commit changes",
                },
            )
        elif last_event == "agent-pre-commit":
            suggestions.append(
                {
                    "priority": "COMMIT",
                    "icon": "SAVE",
                    "action": "Commit your changes",
                    "command": "git add . && git commit",
                    "reason": "Quality gates passed",
                },
            )

    # Limit to top 3 suggestions
    limited_suggestions = suggestions[:3]

    logger.info(
        "action-suggestions-generated",
        _replace_msg="Generated {total} action suggestions (limited to {limited})",
        total=len(suggestions),
        limited=len(limited_suggestions),
    )

    return limited_suggestions


# Status Display Functions


def create_info_panel(content, title, border_style="cyan", box_style=None):
    """Create a rich panel for information display with consistent formatting.

    This utility creates a properly formatted Rich panel for displaying information
    in command-line interfaces. Designed for consistent visual presentation across
    different tools and contexts.

    Args:
        content: Content to display in the panel (string or list of strings)
        title: Panel title displayed at the top
        border_style: Border color style (default: "cyan")
        box_style: Box style (default: box.ROUNDED)

    Returns:
        Rich Panel object configured for information display

    Examples:
        >>> # Basic usage
        >>> panel = create_info_panel("Hello world", "Test Panel")
        >>> print(panel.title)
        Test Panel

        >>> # With custom styling
        >>> panel = create_info_panel(["Line 1", "Line 2"], "Custom", "green")
        >>> "green" in str(panel.border_style)
        True

        >>> # With list content
        >>> lines = ["Status: OK", "Progress: 50%"]
        >>> panel = create_info_panel(lines, "Status")
        >>> "Status: OK" in str(panel.renderable)
        True

    """
    from rich import box  # noqa: PLC0415
    from rich.panel import Panel  # noqa: PLC0415

    logger.debug(
        "Creating info panel",
        extra={
            "title": title,
            "border_style": border_style,
            "content_type": type(content).__name__,
            "content_length": len(content) if hasattr(content, "__len__") else 1,
        },
    )

    if box_style is None:
        box_style = box.ROUNDED

    # Handle both string and list content
    content_text = "\n".join(content) if isinstance(content, list) else content

    panel = Panel(
        content_text,
        title=title,
        border_style=border_style,
        box=box_style,
    )

    logger.debug("Info panel created successfully with title: %s", title)
    return panel


def create_status_table(items, title="Status"):
    """Create a rich table for status display with consistent formatting.

    This utility creates a properly formatted Rich table for displaying status
    information in command-line interfaces. Designed for consistent visual
    presentation across different tools and contexts.

    Args:
        items: List of strings to display as table rows. Each item becomes
               a separate row in the table.
        title: Table title displayed at the top (default: "Status")

    Returns:
        Rich Table object configured for status display with:
        - Simple box style for clean appearance
        - Cyan-colored status column
        - No text wrapping for consistent layout
        - Proper title formatting

    Examples:
        >>> # Basic usage with simple items
        >>> items = ["OK  Tests passing", "!  2 warnings", "X  1 error"]
        >>> table = create_status_table(items, "Build Status")
        >>> print(table.title)
        Build Status

        >>> # Usage with tool status
        >>> tools = ["pytest: Available", "ruff: Available", "mypy: Missing"]
        >>> table = create_status_table(tools, "Tool Status")
        >>> len(table.rows) == 3
        True

        >>> # Empty items list
        >>> table = create_status_table([], "Empty Status")
        >>> len(table.rows) == 0
        True

    Note:
        Requires the 'rich' package for table formatting. The table is ready
        to be printed directly or included in larger Rich console outputs.

    """
    from rich import box  # noqa: PLC0415
    from rich.table import Table  # noqa: PLC0415

    logger.debug(
        "Creating status table",
        extra={
            "title": title,
            "item_count": len(items),
            "items_preview": items[:3] if items else [],
        },
    )

    table = Table(title=title, box=box.SIMPLE)
    table.add_column("Status", style="cyan", no_wrap=True)

    for item in items:
        table.add_row(item)

    logger.debug("Status table created with %d rows for title: %s", len(items), title)
    return table


def create_phase_panel(phase, description, tips):
    """Create a rich panel for phase display with dynamic styling.

    This utility creates a visually appealing Rich panel for displaying current
    workflow phase information. The panel automatically adapts its color scheme
    and styling based on the phase type for better visual distinction.

    Args:
        phase: Phase name (e.g., "TODO", "IMPL"). Determines panel color scheme:
               - "TODO": Blue styling for planning phase
               - "IMPL": Green styling for implementation phase
               - Other: Default green styling
        description: Phase description text displayed prominently at the top
        tips: List of tip strings to display as bullet points below description.
              Can be empty list for no tips.

    Returns:
        Rich Panel object configured for phase display with:
        - Dynamic color scheme based on phase
        - Rounded box style for modern appearance
        - Formatted title with phase icon
        - Structured content with description and tips

    Examples:
        >>> # TODO phase panel
        >>> panel = create_phase_panel("TODO", "Planning phase", ["Plan tasks", "Research"])
        >>> print(panel.title)
        CURRENT PHASE: TODO

        >>> # IMPL phase panel with tips
        >>> tips = ["Write tests first", "Commit frequently", "Run checkpoints"]
        >>> panel = create_phase_panel("IMPL", "Implementation phase", tips)
        >>> "IMPL" in str(panel.title)
        True

        >>> # Phase with no tips
        >>> panel = create_phase_panel("REVIEW", "Review phase", [])
        >>> "REVIEW" in str(panel.title)
        True

        >>> # Custom phase uses default green styling
        >>> panel = create_phase_panel("CUSTOM", "Custom workflow", ["Custom tip"])
        >>> "CUSTOM" in str(panel.title)
        True

    Note:
        Requires the 'rich' package for panel formatting. The panel uses
        different color schemes to help users quickly identify the current
        workflow phase and understand available actions.

    """
    from rich import box  # noqa: PLC0415
    from rich.panel import Panel  # noqa: PLC0415

    logger.debug(
        "Creating phase panel",
        extra={
            "phase": phase,
            "description": description,
            "tips_count": len(tips),
            "tips_preview": tips[:2] if tips else [],
        },
    )

    # Color scheme based on phase
    if phase == PHASE_TODO:
        border_style = "blue"
        title_style = "bold blue"
    else:
        border_style = "green"
        title_style = "bold green"

    # Build content with description and tips
    content_parts = [f"[{title_style}]{description}[/{title_style}]"]
    if tips:
        content_parts.append("")  # Empty line
        content_parts.extend(f"- {tip}" for tip in tips)

    panel = Panel(
        "\n".join(content_parts),
        title=f"- CURRENT PHASE: {phase}",
        border_style=border_style,
        box=box.ROUNDED,
    )

    logger.debug("Phase panel created for phase: %s with %d tips", phase, len(tips))
    return panel


@functools.lru_cache(maxsize=1)
def get_git_status():
    """Collect git status information with caching for performance.

    This function replaces collect_git_status() and provides caching to avoid
    redundant git command execution. The cache is cleared automatically when
    the function is called with different parameters or when the cache size
    limit is reached.

    Returns:
        Dict containing git repository status information:
        - is_git_repo: bool - Whether we are in a git repository
        - branch: str - Current branch name
        - is_clean: bool - Whether repository is clean
        - modified_count: int - Number of modified files
        - staged_count: int - Number of staged files
        - untracked_count: int - Number of untracked files
        - recent_commits: list - Recent commit information
        - ahead_behind: str - Ahead/behind status
        - status_lines: list - Raw git status lines for detailed analysis
        - error: str - Error message if any

    Example:
        >>> status = get_git_status()
        >>> 'is_git_repo' in status
        True
        >>> isinstance(status.get('branch', ''), str)
        True
        >>> isinstance(status.get('is_clean', True), bool)
        True

    """
    from typing import Any  # noqa: PLC0415

    logger.debug("Collecting git status information with caching")

    try:
        # Check if we're in a git repository
        result = run_subprocess(
            ["git", "rev-parse", "--git-dir"],
            quiet=True,
            timeout=2,
        )
        if result.returncode != 0:
            logger.debug("Not in a git repository")
            return {"is_git_repo": False, "error": "Not a git repository"}

        git_info: dict[str, Any] = {"is_git_repo": True}

        # Get current branch
        result = run_subprocess(
            ["git", "branch", "--show-current"],
            quiet=True,
            timeout=2,
        )
        git_info["branch"] = (
            result.stdout.strip() if result.returncode == 0 else "unknown"
        )
        logger.debug("Current branch: %s", git_info["branch"])

        # Get repository status
        result = run_subprocess(["git", "status", "--porcelain"], quiet=True, timeout=2)
        if result.returncode == 0:
            status_lines = [line for line in result.stdout.split("\n") if line.strip()]
            git_info["is_clean"] = len(status_lines) == 0
            # Parse git status format: XY filename
            # X = staged status, Y = working tree status
            git_info["modified_count"] = len(
                [line for line in status_lines if len(line) >= 2 and line[1] == "M"],  # noqa: PLR2004
            )
            git_info["staged_count"] = len(
                [line for line in status_lines if len(line) >= 2 and line[0] in "AM"],  # noqa: PLR2004
            )
            git_info["untracked_count"] = len(
                [line for line in status_lines if line.startswith("??")],
            )
            git_info["status_lines"] = status_lines  # Full list for detailed analysis

            logger.debug(
                "git-status-parsed",
                clean=git_info["is_clean"],
                modified=git_info["modified_count"],
                staged=git_info["staged_count"],
                untracked=git_info["untracked_count"],
            )
        else:
            git_info.update(
                {
                    "is_clean": True,
                    "modified_count": 0,
                    "staged_count": 0,
                    "untracked_count": 0,
                    "status_lines": [],
                },
            )
            logger.debug("Git status command failed, assuming clean repository")

        # Get recent commits
        result = run_subprocess(
            ["git", "log", "--oneline", "-3", "--format=%h %s (%cr)"],
            quiet=True,
            timeout=2,
        )
        if result.returncode == 0:
            git_info["recent_commits"] = [
                line.strip()
                for line in result.stdout.strip().split("\n")
                if line.strip()
            ]
        else:
            git_info["recent_commits"] = []

        # Get ahead/behind status
        result = run_subprocess(
            ["git", "status", "--porcelain=v1", "--branch"],
            quiet=True,
            timeout=2,
        )
        if result.returncode == 0 and result.stdout.strip():
            first_line = result.stdout.strip().split("\n")[0]
            if "ahead" in first_line or "behind" in first_line:
                git_info["ahead_behind"] = (
                    first_line.split("##")[1].strip() if "##" in first_line else ""
                )
            else:
                git_info["ahead_behind"] = ""
        else:
            git_info["ahead_behind"] = ""

        logger.info(
            "git-status-collected",
            _replace_msg="Git status collected successfully: repo={repo}, branch={branch}, clean={clean}",
            repo=git_info["is_git_repo"],
            branch=git_info["branch"],
            clean=git_info["is_clean"],
        )

        return git_info  # noqa: TRY300

    except subprocess.TimeoutExpired:
        logger.exception("Git commands timed out")
        return {
            "is_git_repo": True,
            "error": "Git commands timed out",
            "branch": "timeout",
            "is_clean": False,
        }
    except Exception as e:
        logger.error("Git status collection failed: %s", e, exc_info=True)  # noqa: G201
        return {"is_git_repo": False, "error": f"Git status collection failed: {e}"}


def collect_git_status():
    """Collect git status information without caching for test compatibility.

    This function provides the original collect_git_status behavior for tests
    that mock subprocess calls. For production code, use get_git_status() which
    includes caching.

    Returns:
        Dict containing git repository status information

    """
    logger.debug("collect_git_status() called - using non-cached implementation")

    try:
        # Check if we're in a git repository
        result = run_subprocess(
            ["git", "rev-parse", "--git-dir"],
            quiet=True,
            timeout=2,
        )
        if result.returncode != 0:
            logger.debug("Not in a git repository")
            return {"is_git_repo": False, "error": "Not a git repository"}

        git_info: dict[str, Any] = {"is_git_repo": True}

        # Get current branch
        result = run_subprocess(
            ["git", "branch", "--show-current"],
            quiet=True,
            timeout=2,
        )
        git_info["branch"] = (
            result.stdout.strip() if result.returncode == 0 else "unknown"
        )
        logger.debug("Current branch: %s", git_info["branch"])

        # Get repository status
        result = run_subprocess(["git", "status", "--porcelain"], quiet=True, timeout=2)
        if result.returncode == 0:
            status_lines = [line for line in result.stdout.split("\n") if line.strip()]
            git_info["is_clean"] = len(status_lines) == 0
            # Parse git status format: XY filename
            # X = staged status, Y = working tree status
            git_info["modified_count"] = len(
                [line for line in status_lines if len(line) >= 2 and line[1] == "M"],  # noqa: PLR2004
            )
            git_info["staged_count"] = len(
                [line for line in status_lines if len(line) >= 2 and line[0] in "AM"],  # noqa: PLR2004
            )
            git_info["untracked_count"] = len(
                [line for line in status_lines if line.startswith("??")],
            )
            git_info["status_lines"] = status_lines  # Full list for detailed analysis

            logger.debug(
                "git-status-parsed",
                clean=git_info["is_clean"],
                modified=git_info["modified_count"],
                staged=git_info["staged_count"],
                untracked=git_info["untracked_count"],
            )
        else:
            git_info.update(
                {
                    "is_clean": True,
                    "modified_count": 0,
                    "staged_count": 0,
                    "untracked_count": 0,
                    "status_lines": [],
                },
            )
            logger.debug("Git status command failed, assuming clean repository")

        # Get recent commits
        result = run_subprocess(
            ["git", "log", "--oneline", "-3", "--format=%h %s (%cr)"],
            quiet=True,
            timeout=2,
        )
        if result.returncode == 0:
            git_info["recent_commits"] = [
                line.strip()
                for line in result.stdout.strip().split("\n")
                if line.strip()
            ]
        else:
            git_info["recent_commits"] = []

        # Get ahead/behind status
        result = run_subprocess(
            ["git", "status", "--porcelain=v1", "--branch"],
            quiet=True,
            timeout=2,
        )
        if result.returncode == 0 and result.stdout.strip():
            first_line = result.stdout.strip().split("\n")[0]
            if "ahead" in first_line or "behind" in first_line:
                git_info["ahead_behind"] = (
                    first_line.split("##")[1].strip() if "##" in first_line else ""
                )
            else:
                git_info["ahead_behind"] = ""
        else:
            git_info["ahead_behind"] = ""

        logger.info(
            "git-status-collected",
            _replace_msg="Git status collected successfully: repo={repo}, branch={branch}, clean={clean}",
            repo=git_info["is_git_repo"],
            branch=git_info["branch"],
            clean=git_info["is_clean"],
        )

        return git_info  # noqa: TRY300

    except subprocess.TimeoutExpired:
        logger.exception("Git commands timed out")
        return {
            "is_git_repo": True,
            "error": "Git commands timed out",
            "branch": "timeout",
            "is_clean": False,
        }
    except Exception as e:
        logger.error("Git status collection failed: %s", e, exc_info=True)  # noqa: G201
        return {"is_git_repo": False, "error": f"Git status collection failed: {e}"}


def validate_todo_files_only():
    """Validate that only _TODO-AGENT.md is modified in TODO phase.

    Uses cached git status to avoid redundant git command execution.
    """
    current_phase = get_current_phase()
    if current_phase != PHASE_TODO:
        logger.debug("Not in TODO phase (%s), skipping file validation", current_phase)
        return {"is_valid": True, "violations": [], "phase": current_phase}

    logger.debug("Validating that only _TODO-AGENT.md is modified in TODO phase")

    try:
        # Use cached git status instead of running git commands directly
        git_info = get_git_status()

        if not git_info.get("is_git_repo", False):
            logger.debug("Not in a git repository, validation passes")
            return {"is_valid": True, "violations": [], "phase": current_phase}

        if git_info.get("error"):
            logger.error("Git status error: %s", git_info["error"])
            return {
                "is_valid": False,
                "violations": [
                    {"filename": "", "issue": f"Git error: {git_info['error']}"},
                ],
                "phase": current_phase,
            }

        # Parse status lines to extract modified files
        modified_files = []
        status_lines = git_info.get("status_lines", [])

        for line in status_lines:
            if line.strip():
                # Parse git status output (first 3 chars are status, rest is filename)
                status = line[:3].strip()
                filename = line[3:].strip()
                if status and filename:
                    modified_files.append({"status": status, "filename": filename})

        # Check if any files other than _TODO-AGENT.md are modified
        invalid_files = []
        for file_info in modified_files:
            if file_info["filename"] != "_TODO-AGENT.md":
                invalid_files.append(file_info)  # noqa: PERF401

        is_valid = len(invalid_files) == 0

        logger.debug(
            "TODO file validation: %d total files, %d invalid files",
            len(modified_files),
            len(invalid_files),
        )

        return {
            "is_valid": is_valid,
            "violations": invalid_files,
            "phase": current_phase,
            "modified_files": [f["filename"] for f in modified_files],
        }

    except Exception as e:
        logger.error("Error validating TODO files: %s", e, exc_info=True)  # noqa: G201
        return {
            "is_valid": False,
            "violations": [
                {"filename": "", "issue": f"Error checking modified files: {e}"},
            ],
            "phase": current_phase,
        }


def validate_phase_specific_checklist(commit_message, expected_phase):
    """Validate that the commit message contains the correct checklist for the phase."""
    logger.debug(
        "Validating phase-specific checklist",
        extra={
            "expected_phase": expected_phase,
            "commit_message_length": len(commit_message),
        },
    )

    if expected_phase == PHASE_TODO:
        required_elements = [
            "I know that we are in TODO phase",
            "I've only changed _TODO-AGENT.md",
            "I understand that I MUST commit immediately",
        ]
    else:  # IMPL phase
        required_elements = [
            "I know that we are in IMPL phase",
            "I have written tests for new functionality",
            "I understand that I MUST commit immediately",
        ]

    missing_elements = []
    for element in required_elements:
        if element not in commit_message:
            missing_elements.append(element)  # noqa: PERF401

    is_valid = len(missing_elements) == 0

    logger.debug(
        "Phase-specific checklist validation complete",
        extra={
            "is_valid": is_valid,
            "missing_count": len(missing_elements),
            "required_count": len(required_elements),
            "phase": expected_phase,
        },
    )

    return {
        "is_valid": is_valid,
        "missing_elements": missing_elements,
        "phase": expected_phase,
    }


def validate_agent_checklist():
    """Validate agent checklist items and return validation results."""
    logger.debug("Starting agent checklist validation")

    # Define the standard agent checklist items
    standard_checklist = [
        "Written tests for new functionality?",
        "_TODO-AGENT.md up-to-date?",
        "Next steps clear, can I continue right away?",
        "Everything ready for commit? Will I show the resulting commit ID to the user?",
    ]

    logger.debug("Defined %d standard checklist items", len(standard_checklist))

    # Check if there's a recent commit with checklist
    try:
        result = run_subprocess(
            ["git", "log", "-1", "--format=%B"],
            quiet=True,
        )

        if result.returncode != 0:
            return {
                "has_checklist": False,
                "total_items": 0,
                "completed_items": 0,
                "missing_items": standard_checklist,
                "validation_errors": ["No recent commit found"],
                "is_valid": False,
            }

        commit_message = result.stdout.strip()

        # Count checklist items in commit message
        completed_items = []
        incomplete_items = []

        for line in commit_message.split("\n"):
            if "- [x]" in line or "- [OK]" in line:
                completed_items.append(line.strip())
            elif "- [ ]" in line:
                incomplete_items.append(line.strip())

        total_checklist_items = len(completed_items) + len(incomplete_items)
        has_checklist = total_checklist_items > 0

        # Check for standard checklist items
        missing_standard_items = []
        for standard_item in standard_checklist:
            found = False
            for item in completed_items + incomplete_items:
                if any(
                    keyword in item.lower()
                    for keyword in standard_item.lower().split()[:3]
                ):
                    found = True
                    break
            if not found:
                missing_standard_items.append(standard_item)

        validation_errors = []
        if not has_checklist:
            validation_errors.append("No checklist found in recent commit message")
        if len(completed_items) == 0 and has_checklist:
            validation_errors.append("Checklist found but no items marked as completed")
        if missing_standard_items:
            validation_errors.append(
                f"Missing standard checklist items: {len(missing_standard_items)}",
            )

        is_valid = (
            len(validation_errors) == 0 and has_checklist and len(completed_items) > 0
        )

        return {
            "has_checklist": has_checklist,
            "total_items": total_checklist_items,
            "completed_items": len(completed_items),
            "incomplete_items": len(incomplete_items),
            "missing_items": missing_standard_items,
            "validation_errors": validation_errors,
            "is_valid": is_valid,
            "completed_list": completed_items,
            "incomplete_list": incomplete_items,
        }

    except Exception as e:  # noqa: BLE001
        return {
            "has_checklist": False,
            "total_items": 0,
            "completed_items": 0,
            "missing_items": standard_checklist,
            "validation_errors": [f"Error validating checklist: {e}"],
            "is_valid": False,
        }


def display_checklist_status(checklist_info) -> None:
    """Display checklist status with rich formatting."""
    logger.debug(
        "Displaying checklist status",
        extra={
            "has_checklist": checklist_info.get("has_checklist", False),
            "completed_items": checklist_info.get("completed_items", 0),
            "total_items": checklist_info.get("total_items", 0),
            "is_valid": checklist_info.get("is_valid", False),
            "validation_errors_count": len(checklist_info.get("validation_errors", [])),
            "missing_items_count": len(checklist_info.get("missing_items", [])),
        },
    )

    if not checklist_info["has_checklist"]:
        console.print("-  [yellow]No checklist found in recent commit[/yellow]")
        console.print("i  Consider adding agent checklist to commit messages")
        logger.info(
            "checklist-not-found",
            _replace_msg="No checklist found in recent commit",
        )
        return

    # Create checklist status panel
    status_text = f"-  Checklist: {checklist_info['completed_items']}/{checklist_info['total_items']} completed"

    if checklist_info["is_valid"]:
        console.print(f"OK  [green]{status_text}[/green]")
        logger.info(
            "checklist-validation-passed",
            _replace_msg="Checklist validation passed: {status}",
            status=status_text,
        )
    else:
        console.print(f"!   [yellow]{status_text}[/yellow]")
        logger.warning(
            "checklist-validation-failed",
            _replace_msg="Checklist validation failed: {status}",
            status_text=status_text,
        )

    # Show validation errors if any
    if checklist_info["validation_errors"]:
        console.print("ERROR [red]Checklist validation issues:[/red]")
        for error in checklist_info["validation_errors"]:
            console.print(f"  - {error}")
        logger.warning(
            "checklist-validation-errors-found",
            _replace_msg="Found {count} checklist validation errors",
            error_count=len(checklist_info["validation_errors"]),
        )

    # Show missing standard items
    if checklist_info["missing_items"]:
        console.print("-  [yellow]Missing standard checklist items:[/yellow]")
        for item in checklist_info["missing_items"][:3]:  # Show first 3
            console.print(f"  - {item}")
        if len(checklist_info["missing_items"]) > 3:  # noqa: PLR2004
            console.print(f"  ... and {len(checklist_info['missing_items']) - 3} more")
        logger.info(
            "missing-checklist-items-found",
            _replace_msg="Found {count} missing standard checklist items",
            count=len(checklist_info["missing_items"]),
        )


def show_agent_status_footer(event_name="") -> None:
    """Show consistent status footer for all agent outputs."""
    logger.debug("Showing agent status footer", extra={"event_name": event_name})

    current_phase = get_current_phase()
    todo_progress = count_todo_checkboxes()
    checklist_info = validate_agent_checklist()

    logger.debug(
        "Agent status footer data collected",
        extra={
            "current_phase": current_phase,
            "todo_progress": todo_progress.get("progress_text", ""),
            "checklist_has_checklist": checklist_info.get("has_checklist", False),
            "checklist_completed": checklist_info.get("completed_items", 0),
            "checklist_total": checklist_info.get("total_items", 0),
        },
    )

    # Create status footer panel
    footer_content = []

    # Phase and TODO progress
    footer_content.append(
        f"-  Phase: {current_phase} ({'Planning' if current_phase == PHASE_TODO else 'Implementation'})",
    )
    footer_content.append(f"-  TODO: {todo_progress['progress_text']}")

    # Next action
    if todo_progress["is_complete"]:
        footer_content.append("-  All TODO items completed - ready for new tasks!")
    elif todo_progress["next_item"]:
        footer_content.append(f"->   Next: {todo_progress['next_item'][:60]}...")
    else:
        footer_content.append(
            "i  Consider adding TODO checkboxes for progress tracking",
        )

    # Checklist status
    if checklist_info["has_checklist"]:
        checklist_status = f"Checklist: {checklist_info['completed_items']}/{checklist_info['total_items']}"
        if checklist_info["is_valid"]:
            footer_content.append(f"OK  {checklist_status}")
        else:
            footer_content.append(f"!   {checklist_status} (issues found)")
    else:
        footer_content.append("-  No recent checklist found")

    # Event-specific guidance
    if event_name:
        footer_content.append(f"*  Event: {event_name}")

    footer_panel = create_info_panel(
        footer_content,
        "- Agent Status Summary",
        border_style="cyan",
        box_style=box.SIMPLE,
    )

    console.print(footer_panel)
    logger.info(
        "agent-status-footer-displayed",
        _replace_msg="Agent status footer displayed with {count} content lines",
        count=len(footer_content),
    )


def set_phase_with_display(phase) -> None:
    """Set agent phase and create phase file with visual feedback.

    that adds rich console display functionality.
    """
    logger.debug("Setting phase with display: %s", phase)

    # Use the library function for the actual phase setting
    set_phase(phase)

    # Enhanced visual feedback (dodo-specific)
    if phase == PHASE_TODO:
        panel = create_phase_panel(
            phase,
            "-  TODO phase - Planning phase",
            [
                "Update _TODO-AGENT.md",
                "Implementation tasks blocked",
                "Use 'uv run doit agent-phase-impl' when ready to implement",
            ],
        )
    else:
        panel = create_phase_panel(
            phase,
            "-  IMPL phase - Implementation phase",
            [
                "Implementation tasks allowed",
                "agent-coding-start will work",
                "Remember: TODO-First, Implementation-Second!",
            ],
        )

    console.print(panel)
    logger.info(
        "phase-set-with-feedback",
        _replace_msg="Phase set to {phase} with visual feedback displayed",
        phase=phase,
    )


def check_phase_for_implementation() -> bool:
    """Check if current phase allows implementation. Fail hard if in TODO phase."""
    current_phase = get_current_phase()
    logger.debug("Checking phase for implementation: current_phase=%s", current_phase)

    if current_phase == PHASE_TODO:
        logger.error("Implementation blocked: currently in TODO phase")
        sys.exit(1)

    logger.debug("Implementation allowed: in %s phase", current_phase)
    return True


def check_todo_implementation_separation() -> bool:
    """Enforce TODO-First, Implementation-Second rule with user interaction check."""
    logger.debug("Checking TODO-implementation separation")

    todo_file = Path("_TODO-AGENT.md")

    if not todo_file.exists():
        logger.error(
            "TODO file _TODO-AGENT.md not found, cannot proceed with implementation",
        )
        sys.exit(1)

    # Check if TODO has recent updates (basic heuristic)
    try:
        import time  # noqa: PLC0415

        todo_mtime = todo_file.stat().st_mtime
        current_time = time.time()
        hours_since_update = (current_time - todo_mtime) / 3600

        logger.debug("TODO file last modified %.1f hours ago", hours_since_update)

        if hours_since_update > 24:  # noqa: PLR2004
            logger.warning(
                "todo-file-not-updated",
                _replace_msg="TODO file not updated in {hours} hours",
                hours_since_update=hours_since_update,
            )
    except Exception:  # noqa: BLE001
        # If we can't check file time, just continue
        logger.debug("Could not check TODO file modification time")

    logger.debug("TODO-implementation separation check passed")
    return True


def detect_todo_checkbox_changes():  # noqa: PLR0911, PLR0915
    """Detect TODO checkbox changes since last commit.

    Uses cached git status and centralized subprocess wrapper to reduce duplication.
    Supports '-', '*', and ordered list checkbox prefixes and both [ ] and [x]/[x].
    """
    todo_file = Path("_TODO-AGENT.md")
    if not todo_file.exists():
        logger.debug("No _TODO-AGENT.md file found for checkbox change detection")
        return False, "No _TODO-AGENT.md file found"

    logger.debug("Detecting TODO checkbox changes since last commit")

    try:
        # Get the current content
        current_content = todo_file.read_text(encoding="utf-8")

        # Use centralized subprocess wrapper instead of direct subprocess.run
        result = run_subprocess(
            ["git", "show", f"HEAD:{todo_file}"],
            quiet=True,
            timeout=5,
        )

        checkbox_re = re.compile(r"^\s*(?:[-*]|\d+\.)\s*\[(x| |OK)\]\s*(.*)")

        def parse_checkboxes(text: str):
            """Parse checkbox items from markdown text.

            Returns:
                tuple: (checked_items, unchecked_items, text_to_state_mapping)

            """
            checked = []  # list of (line_num, full_line, text)
            unchecked = []
            mapping = {}  # text -> state
            for i, line in enumerate(text.split("\n")):
                m = checkbox_re.match(line)
                if not m:
                    continue
                state = m.group(1)
                item_text = m.group(2).strip()
                mapping[item_text] = state
                if state.lower() == "x" or state == "OK":
                    checked.append((i, line.strip(), item_text))
                else:
                    unchecked.append((i, line.strip(), item_text))
            return checked, unchecked, mapping

        current_checked, current_unchecked, current_map = parse_checkboxes(
            current_content,
        )

        if result.returncode != 0:
            # File doesn't exist in last commit - this is initial creation
            logger.debug("TODO file not found in last commit - initial creation")
            if current_checked:
                message = f"Initial TODO creation with {len(current_checked)} completed checkboxes"
                logger.info(
                    "todo-progress-detected",
                    _replace_msg="TODO progress detected: {message}",
                    message=message,
                )
                return True, message
            else:
                message = "Initial TODO creation but no completed checkboxes yet"
                logger.debug("No TODO progress: %s", message)
                return False, message

        last_commit_content = result.stdout
        last_checked, last_unchecked, last_map = parse_checkboxes(last_commit_content)

        # Find newly checked items ([ ] -> [x]) by matching item text
        newly_checked = []
        for item_text, state in current_map.items():
            if (state.lower() == "x" or state == "OK") and last_map.get(
                item_text,
                " ",
            ) == " ":
                newly_checked.append(item_text)

        if newly_checked:
            message = f"Found {len(newly_checked)} newly checked items: {newly_checked[:2]}..."
            logger.info(
                "todo-progress-detected",
                _replace_msg="TODO progress detected: {message}",
                message=message,
            )
            return True, message

        # Check if there are any checked items at all
        if current_checked and not last_checked:
            message = f"First checkboxes completed: {len(current_checked)} items"
            logger.info(
                "todo-progress-detected",
                _replace_msg="TODO progress detected: {message}",
                message=message,
            )
            return True, message

        # Check if more items were checked
        if len(current_checked) > len(last_checked):
            message = f"Progress detected: {len(current_checked)} vs {len(last_checked)} checked items"
            logger.info(
                "todo-progress-detected",
                _replace_msg="TODO progress detected: {message}",
                message=message,
            )
            return True, message

        message = (
            f"No checkbox progress detected (current: {len(current_checked)} checked, "
            f"last: {len(last_checked)} checked)"
        )
        logger.debug("No TODO progress: %s", message)
        return False, message  # noqa: TRY300

    except Exception as e:
        error_message = f"Error checking TODO progress: {e}"
        logger.error("TODO checkbox change detection failed: %s", e, exc_info=True)  # noqa: G201
        return False, error_message


def validate_todo_discipline() -> bool:  # noqa: D103
    console.print("-  [bold blue]TODO PHASE DISCIPLINE VALIDATION[/bold blue]")
    console.print("Checking for completed checkboxes in TODO phase...")

    discipline_check = validate_todo_phase_discipline()

    if discipline_check["is_valid"]:
        console.print("OK  [green]TODO phase discipline validation passed[/green]")
        if discipline_check["phase"] == PHASE_TODO:
            console.print("-  TODO phase: No completed checkboxes found - correct!")
        else:
            console.print("-  IMPL phase: Completed checkboxes allowed")
        return True
    else:
        console.print("X  [red]TODO PHASE DISCIPLINE VALIDATION FAILED[/red]")
        console.print(
            f"ERROR Found {discipline_check['total_violations']} completed checkboxes in TODO phase!",
        )

        console.print("\n-  Violations found:")
        for violation in discipline_check["violations"]:
            console.print(f"  Line {violation['line']}: {violation['content']}")

        console.print("\ni  TODO phase is for planning only:")
        console.print("i  - Use [ ] for planning tasks, not [x]")
        console.print("i  - Mark checkboxes as done only in IMPL phase")
        console.print("i  - Use bullet points (-) for analysis and notes")
        console.print("i  - Switch to IMPL phase to mark tasks as completed")

        console.print("\n-  To fix this:")
        console.print("1. Change [x] back to [ ] in _TODO-AGENT.md")
        console.print("2. Or switch to IMPL phase: uv run doit agent-phase-impl")
        console.print("3. Then commit your changes")

        return False


def validate_no_code_in_todo() -> bool:  # noqa: D103
    logger.debug("Starting TODO files validation")

    console.print("-  [bold blue]TODO FILES VALIDATION[/bold blue]")
    console.print("Checking that only _TODO-AGENT.md is modified in TODO phase...")

    files_check = validate_todo_files_only()

    if files_check["is_valid"]:
        console.print("OK  [green]TODO files validation passed[/green]")
        logger.info(
            "todo-files-validation-passed",
            _replace_msg="TODO files validation passed",
        )

        if files_check["phase"] == PHASE_TODO:
            modified_files = files_check.get("modified_files", [])
            if modified_files:
                console.print(
                    f"-  TODO phase: Only _TODO-AGENT.md modified (found: {', '.join(modified_files)})",
                )
                logger.debug(
                    "TODO phase: only allowed files modified",
                    modified_files=modified_files,
                )
            else:
                console.print("-  TODO phase: No files modified - correct!")
                logger.debug("TODO phase: no files modified")
        else:
            console.print("-  IMPL phase: All file modifications allowed")
            logger.debug("IMPL phase: file modifications allowed")
        return True
    else:
        console.print("X  [red]TODO FILES VALIDATION FAILED[/red]")
        violation_count = len(files_check["violations"])
        console.print(
            f"ERROR Found {violation_count} files modified outside _TODO-AGENT.md!",
        )
        logger.warning(
            "todo-files-validation-failed",
            _replace_msg="TODO files validation failed with {count} violations",
            violation_count=violation_count,
        )

        console.print("\n-  Violations found:")
        for violation in files_check["violations"]:
            console.print(f"  {violation['status']} {violation['filename']}")
            logger.debug(
                "File violation found",
                filename=violation["filename"],
                status=violation["status"],
            )

        console.print("\ni  TODO phase is for planning only:")
        console.print("i  - Only modify _TODO-AGENT.md in TODO phase")
        console.print("i  - Implementation files should only be modified in IMPL phase")
        console.print("i  - Use TODO phase for planning, IMPL phase for coding")

        console.print("\n-  To fix this:")
        console.print("1. Move code changes to a separate commit")
        console.print("2. Or switch to IMPL phase: uv run doit agent-phase-impl")
        console.print("3. Then commit your changes")

        return False


def validate_impl_progress() -> bool:  # noqa: D103
    has_progress, message = detect_todo_checkbox_changes()

    if has_progress:
        return True
    else:
        # Show current checkbox status
        todo_file = Path("_TODO-AGENT.md")
        if todo_file.exists():
            content = todo_file.read_text(encoding="utf-8")
            content.count("- [x]")
            content.count("- [ ]")

        return False


def format_todo_markdown() -> bool | None:  # noqa: D103
    logger.debug("Starting TODO markdown formatting")

    console.print("-  [bold blue]MARKDOWN FORMATTING[/bold blue]")
    console.print("Formatting TODO files with mdformat...")

    todo_file = Path("_TODO-AGENT.md")
    if not todo_file.exists():
        console.print(
            "!   [yellow]No _TODO-AGENT.md found - skipping formatting[/yellow]",
        )
        logger.info(
            "todo-file-not-found",
            _replace_msg="TODO file not found, skipping formatting",
        )
        return True

    try:
        # Run mdformat on TODO file
        result = run_subprocess(
            ["uv", "run", "mdformat", str(todo_file)],
            quiet=True,
        )

        if result.returncode == 0:
            console.print("OK  [green]TODO markdown formatted successfully[/green]")
            logger.info(
                "todo-markdown-formatting-completed",
                _replace_msg="TODO markdown formatting completed successfully",
            )
            return True
        else:
            console.print("X  [red]mdformat failed:[/red]")
            console.print(result.stderr)
            logger.error(
                "mdformat failed",
                returncode=result.returncode,
                stderr=result.stderr,
            )
            return False

    except Exception as e:
        console.print(f"X  [red]Failed to run mdformat: {e}[/red]")
        logger.exception("Failed to run mdformat", error=str(e))
        return False


def run_linting(  # noqa: PLR0912
    mode: str = "strict",
    tools: list[str] | None = None,
    quiet: bool = True,  # noqa: FBT001, FBT002
) -> bool:
    """Run linting with configurable mode and tools.

    Consolidated linting function that replaces run_linting_with_warnings(),
    run_strict_linting(), and run_pre_commit_strict_linting().

    Args:
        mode: Linting mode - "strict", "warnings", or "pre-commit"
        tools: List of tools to run (default: ["ruff", "mypy", "pylint"])
        quiet: Use quiet mode for subprocess calls (default: True)

    Returns:
        True if all tools pass (or warnings mode), False if any fail in strict modes

    Examples:
        >>> # Warnings mode (always returns True)
        >>> run_linting(mode="warnings")
        True

        >>> # Strict mode (fails on first error)
        >>> run_linting(mode="strict")  # doctest: +SKIP

        >>> # Custom tools
        >>> run_linting(mode="strict", tools=["ruff", "mypy"])  # doctest: +SKIP

    """
    if tools is None:
        tools = ["ruff", "mypy", "pylint"]

    logger.debug("Running linting with mode=%s, tools=%s, quiet=%s", mode, tools, quiet)

    # Configure display based on mode
    mode_config = {
        "warnings": {
            "title": "- [bold blue]LINTING (warnings allowed)[/bold blue]",
            "fail_fast": False,
            "show_output_on_fail": True,
        },
        "strict": {
            "title": "- [bold red]STRICT LINTING (hard failures)[/bold red]",
            "fail_fast": True,
            "show_output_on_fail": True,
        },
        "pre-commit": {
            "title": "- [bold red]PRE-COMMIT STRICT LINTING[/bold red]",
            "fail_fast": True,
            "show_output_on_fail": True,
        },
    }

    config = mode_config.get(mode, mode_config["strict"])
    console.print(config["title"])

    # Tool command mappings
    tool_commands = {
        "ruff": ["uv", "run", "ruff", "check", "."],
        "mypy": ["uv", "run", "mypy", "."],
        "pylint": ["uv", "run", "pylint", "src/"],
    }

    all_passed = True

    for tool in tools:
        if tool not in tool_commands:
            logger.warning(
                "unknown-linting-tool",
                _replace_msg="Unknown linting tool: {tool}",
                tool=tool,
            )
            console.print(f"!   [yellow]Unknown tool: {tool}[/yellow]")
            continue

        try:
            cmd = tool_commands[tool]
            result = run_subprocess(cmd, quiet=quiet)

            if result.returncode == 0:
                console.print(f"OK  [green]{tool} passed[/green]")
            else:
                all_passed = False

                if mode == "warnings":
                    console.print(
                        f"!   [yellow]{tool} failed - see output above[/yellow]",
                    )
                    if config["show_output_on_fail"] and result.stdout:
                        console.print(result.stdout)
                else:
                    console.print(f"X  [red]{tool} failed[/red]")
                    if config["show_output_on_fail"] and result.stdout:
                        console.print(result.stdout)

                    if config["fail_fast"]:
                        logger.error(
                            "Linting failed in %s mode with tool %s",
                            mode,
                            tool,
                        )
                        return False

        except Exception as e:
            all_passed = False
            logger.exception("Linting tool %s failed", tool)

            if mode == "warnings":
                console.print(f"!   [yellow]{tool} error: {e}[/yellow]")
            else:
                console.print(f"X  [red]{tool} error: {e}[/red]")
                if config["fail_fast"]:
                    return False

    # In warnings mode, always return True regardless of failures
    if mode == "warnings":
        return True

    return all_passed


def run_linting_with_warnings():
    """Run linting with warnings allowed.

    Backward compatibility wrapper for run_linting().
    """
    logger.debug("Running linting with warnings (backward compatibility)")
    result = run_linting(mode="warnings")
    logger.debug("Linting with warnings completed", result=result)
    return result


def run_strict_linting():
    """Run linting with strict phase (failures will stop execution).

    Backward compatibility wrapper for run_linting().
    """
    logger.debug("Running strict linting (backward compatibility)")
    result = run_linting(mode="strict")
    logger.debug("Strict linting completed", result=result)
    return result


def task_loc():
    """Count lines of code using tokei if available. Hidden when missing."""
    logger.debug("Checking for tokei availability")

    # Try to find tokei in PATH
    tokei = shutil.which("tokei")
    if not tokei:
        # Hide task when tokei is not available
        logger.debug("tokei not found in PATH, hiding task")
        return None

    logger.debug("tokei found, creating LOC counting task")
    return {
        "actions": [f"{tokei} -s lines -o json . || true"],
        "verbosity": 2,
    }


def clean_artifacts() -> None:  # noqa: D103
    logger.debug("Starting artifact cleanup")

    artifacts = [
        "build/",
        "dist/",
        "*.egg-info/",
        ".pytest_cache/",
        ".mypy_cache/",
        "htmlcov/",
        ".coverage",
    ]

    cleaned_count = 0
    for pattern in artifacts:
        if pattern.endswith("/"):
            for path in Path().glob(pattern):
                if path.is_dir():
                    logger.debug("Removing directory: %s", path)
                    shutil.rmtree(path)
                    cleaned_count += 1
        else:
            for path in Path().glob(pattern):
                if path.exists():
                    logger.debug("Removing file: %s", path)
                    path.unlink()
                    cleaned_count += 1

    logger.info(
        "artifact-cleanup-completed",
        _replace_msg="Artifact cleanup completed",
        cleaned_count=cleaned_count,
    )

    # Remove __pycache__ directories
    for path in Path().rglob("__pycache__"):
        if path.is_dir():
            shutil.rmtree(path)

    # Remove .pyc files
    for path in Path().rglob("*.pyc"):
        path.unlink()


def switch_to_todo() -> bool:  # noqa: D103, PLR0912, PLR0915
    logger.debug("Starting TODO phase switch validation")

    # Validate current TODO completion before switching
    todo_file = Path("_TODO-AGENT.md")
    if todo_file.exists():
        console.print("- [yellow]Checking current TODO completion...[/yellow]")
        logger.debug("TODO file found, validating completion")

        try:
            content = todo_file.read_text()
            unchecked_items = []

            for i, line in enumerate(content.split("\n"), 1):
                if "- [ ]" in line:
                    unchecked_items.append(f"Line {i}: {line.strip()}")

            if unchecked_items:
                console.print("X  [red]TODO COMPLETION VALIDATION FAILED[/red]")
                console.print(
                    "ERROR Cannot switch to TODO phase with incomplete items!",
                )
                console.print(f"\n-  Found {len(unchecked_items)} unchecked items:")
                logger.warning(
                    "todo-completion-validation-failed",
                    _replace_msg="TODO completion validation failed: {count} unchecked items",
                    unchecked_count=len(unchecked_items),
                )

                # Show first 5 unchecked items
                for item in unchecked_items[:5]:
                    console.print(f"  - {item}")

                if len(unchecked_items) > 5:  # noqa: PLR2004
                    console.print(f"  ... and {len(unchecked_items) - 5} more")

                console.print("\ni  Complete current TODO items first:")
                console.print("i  - Check off completed items: [ ] -> [x]")
                console.print("i  - Or remove items that are no longer relevant")
                console.print("i  - Then try switching to TODO phase again")
                sys.exit(1)

            console.print(
                "OK  [green]Current TODO is complete - safe to switch[/green]",
            )
            logger.info(
                "todo-completion-validation-passed",
                _replace_msg="TODO completion validation passed",
            )

        except Exception as e:  # noqa: BLE001
            console.print(f"!   [yellow]Warning: Could not validate TODO: {e}[/yellow]")
            logger.warning(
                "todo-validation-failed",
                _replace_msg="TODO validation failed: {error}",
                error=str(e),
            )
    else:
        logger.debug("No TODO file found, skipping validation")

    # Validate agent checklist completion before phase switch
    console.print("- [yellow]Checking agent checklist completion...[/yellow]")
    checklist_info = validate_agent_checklist()
    logger.debug(
        "Agent checklist validation completed",
        has_checklist=checklist_info["has_checklist"],
        is_valid=checklist_info["is_valid"],
    )

    if checklist_info["has_checklist"] and not checklist_info["is_valid"]:
        console.print("X  [red]CHECKLIST VALIDATION FAILED[/red]")
        console.print("ERROR Cannot switch to TODO phase with incomplete checklist!")
        console.print("\n-  Checklist issues found:")
        logger.warning(
            "agent-checklist-validation-failed",
            _replace_msg="Agent checklist validation failed with {count} errors",
            validation_errors=checklist_info["validation_errors"],
            error_count=len(checklist_info["validation_errors"]),
        )

        for error in checklist_info["validation_errors"]:
            console.print(f"  - {error}")

        if checklist_info["incomplete_list"]:
            console.print("\n-  Incomplete checklist items:")
            for item in checklist_info["incomplete_list"][:3]:
                console.print(f"  - {item}")
            if len(checklist_info["incomplete_list"]) > 3:  # noqa: PLR2004
                console.print(
                    f"  ... and {len(checklist_info['incomplete_list']) - 3} more",
                )

        console.print("\ni  Complete agent checklist first:")
        console.print("i  - Ensure all checklist items are marked [x]")
        console.print("i  - Commit with proper checklist in message")
        console.print("i  - Then try switching to TODO phase again")
        sys.exit(1)
    elif checklist_info["has_checklist"]:
        console.print("OK  [green]Agent checklist validation passed[/green]")
        logger.info(
            "agent-checklist-validation-passed",
            _replace_msg="Agent checklist validation passed",
        )

    # Copy template when switching to TODO phase for new planning
    template_file = Path("TEMPLATE_TODO-AGENT.md")
    if template_file.exists() and not todo_file.exists():
        console.print(
            "-  [blue]Copying TEMPLATE_TODO-AGENT.md for new planning...[/blue]",
        )
        try:
            template_content = template_file.read_text()
            todo_file.write_text(template_content)
            console.print("OK  [green]Template copied to _TODO-AGENT.md[/green]")
        except Exception as e:  # noqa: BLE001
            console.print(f"X  [red]Failed to copy template: {e}[/red]")
            console.print("i  Manually copy TEMPLATE_TODO-AGENT.md to _TODO-AGENT.md")

    set_phase_with_display(PHASE_TODO)

    # Show detailed TODO progress after phase switch
    todo_progress = count_todo_checkboxes()
    console.print("\n-  [bold blue]TODO PHASE ACTIVE[/bold blue]")
    console.print("- You can now update _TODO-AGENT.md")
    console.print("- Implementation tasks are blocked")
    console.print("- MUST commit TODO changes (Rule 1)")
    console.print("- Use 'uv run doit agent-phase-impl' when ready to implement")

    # Enhanced TODO progress display
    console.print("\n- [bold cyan]TODO PROGRESS AFTER PHASE SWITCH:[/bold cyan]")
    console.print(f"-  Current status: [bold]{todo_progress['progress_text']}[/bold]")
    if todo_progress["next_item"]:
        console.print(f"->   Next item: {todo_progress['next_item'][:80]}...")
    elif todo_progress["is_complete"]:
        console.print(
            "-  [green]All TODO items completed - ready for new planning![/green]",
        )
    else:
        console.print(
            "i  [yellow]No TODO checkboxes found - ready for new planning[/yellow]",
        )

    # Show consistent status footer
    show_agent_status_footer("agent-phase-todo")

    return True


def switch_to_impl() -> bool:  # noqa: D103, PLR0912, PLR0915
    logger.debug("Starting IMPL phase switch validation")

    # Validate TODO exists before switching to implementation
    todo_file = Path("_TODO-AGENT.md")
    if not todo_file.exists():
        console.print("X  [red]TODO-FIRST RULE VIOLATION[/red]")
        console.print("ERROR No _TODO-AGENT.md found!")
        console.print("i  Create TODO file first: 'uv run doit agent-phase-todo'")
        console.print("i  Plan your work before implementing")
        logger.error("TODO file not found, cannot switch to IMPL phase")
        sys.exit(1)

    # Check if TODO has any planning content
    try:
        content = todo_file.read_text()
        content_length = len(content.strip())
        if content_length < 50:  # Very minimal content check  # noqa: PLR2004
            console.print("!   [yellow]TODO file seems very minimal[/yellow]")
            console.print(
                "i  Consider adding more detailed planning before implementation",
            )
            logger.warning(
                "todo-file-content-minimal",
                _replace_msg="TODO file content seems minimal ({length} chars)",
                content_length=content_length,
            )
        else:
            console.print(
                "OK  [green]TODO file found - ready for implementation[/green]",
            )
            logger.info(
                "todo-file-validation-passed",
                _replace_msg="TODO file validation passed",
                content_length=content_length,
            )
    except Exception as e:  # noqa: BLE001
        console.print(f"!   [yellow]Warning: Could not read TODO: {e}[/yellow]")
        logger.warning(
            "todo-file-read-failed",
            _replace_msg="Could not read TODO file: {error}",
            error=str(e),
        )

    # Validate agent checklist completion before phase switch
    console.print("- [yellow]Checking agent checklist completion...[/yellow]")
    checklist_info = validate_agent_checklist()

    if checklist_info["has_checklist"] and not checklist_info["is_valid"]:
        console.print("X  [red]CHECKLIST VALIDATION FAILED[/red]")
        console.print("ERROR Cannot switch to IMPL phase with incomplete checklist!")
        console.print("\n-  Checklist issues found:")

        for error in checklist_info["validation_errors"]:
            console.print(f"  - {error}")

        if checklist_info["incomplete_list"]:
            console.print("\n-  Incomplete checklist items:")
            for item in checklist_info["incomplete_list"][:3]:
                console.print(f"  - {item}")
            if len(checklist_info["incomplete_list"]) > 3:  # noqa: PLR2004
                console.print(
                    f"  ... and {len(checklist_info['incomplete_list']) - 3} more",
                )

        console.print("\ni  Complete agent checklist first:")
        console.print("i  - Ensure all checklist items are marked [x]")
        console.print("i  - Commit with proper checklist in message")
        console.print("i  - Then try switching to IMPL phase again")
        sys.exit(1)
    elif checklist_info["has_checklist"]:
        console.print("OK  [green]Agent checklist validation passed[/green]")

    set_phase_with_display(PHASE_IMPL)

    # Show detailed TODO progress after phase switch
    todo_progress = count_todo_checkboxes()
    console.print("\n-  [bold green]IMPL PHASE ACTIVE[/bold green]")
    console.print("- You can now run implementation tasks")
    console.print("- agent-coding-start will work")
    console.print("- Remember: TODO-First, Implementation-Second!")
    console.print("- Update _TODO-AGENT.md progress as you work")

    # Enhanced TODO progress display
    console.print("\n- [bold cyan]TODO PROGRESS AFTER PHASE SWITCH:[/bold cyan]")
    console.print(f"-  Current status: [bold]{todo_progress['progress_text']}[/bold]")
    if todo_progress["next_item"]:
        console.print(
            f"->   Next item to implement: {todo_progress['next_item'][:80]}...",
        )
    elif todo_progress["is_complete"]:
        console.print(
            "-  [green]All TODO items completed - ready for new tasks![/green]",
        )
    else:
        console.print(
            "i  [yellow]No TODO checkboxes found - consider adding implementation tasks[/yellow]",
        )

    if todo_progress["remaining"] > 0:
        console.print(
            f"*  [cyan]Focus: {todo_progress['remaining']} items remaining to complete[/cyan]",
        )

    # Show consistent status footer
    show_agent_status_footer("agent-phase-impl")

    return True


def show_agent_status(event_name="agent-status") -> None:  # noqa: PLR0912, PLR0915
    """Display comprehensive agent development status."""
    console.print("\n-  [bold blue]COMPREHENSIVE AGENT STATUS[/bold blue]")

    # Collect all status information
    current_phase = get_current_phase()
    todo_progress = count_todo_checkboxes()
    git_info = get_git_status()
    workflow_info = get_workflow_state()
    validate_agent_checklist()

    phase_info = {"current_phase": current_phase}
    todo_info = {
        "completion_rate": todo_progress["completed"] / max(todo_progress["total"], 1),
        "remaining": todo_progress["remaining"],
    }

    next_actions = suggest_next_actions(phase_info, workflow_info, git_info, todo_info)

    # 1. Critical alerts panel (if needed)
    alerts = []
    if git_info.get("is_git_repo") and not git_info.get("is_clean", True):
        alerts.append(
            f"!  {git_info.get('modified_count', 0) + git_info.get('staged_count', 0)} uncommitted files",
        )

    if alerts:
        alerts_panel = create_info_panel(
            alerts,
            "!  CRITICAL ALERTS",
            border_style="red",
        )
        console.print(alerts_panel)

    # 2. Phase and TODO status panel
    phase_content = []
    phase_content.append(
        f"-  Phase: [bold]{current_phase}[/bold] ({'Planning' if current_phase == PHASE_TODO else 'Implementation'})",
    )
    phase_content.append(
        f"-  TODO Progress: [bold]{todo_progress['progress_text']}[/bold]",
    )

    if todo_progress["next_item"] and not todo_progress["is_complete"]:
        phase_content.append(f"->   Next: {todo_progress['next_item'][:60]}...")
    elif todo_progress["is_complete"]:
        phase_content.append("-  [green]All TODO items completed![/green]")

    phase_panel = create_info_panel(
        phase_content,
        "- CURRENT CONTEXT",
        border_style="cyan",
    )
    console.print(phase_panel)

    # 3. Workflow status (condensed)
    if workflow_info.get("session_active"):
        session_status = (
            "[green]Active[/green]"
            if workflow_info.get("session_active")
            else "[yellow]Inactive[/yellow]"
        )
        last_event = workflow_info.get("last_event", "none")
        console.print(f"-  Session: {session_status} (last: {last_event})")

    # 4. Git status (condensed)
    if git_info.get("is_git_repo"):
        branch = git_info.get("branch", "unknown")
        if git_info.get("is_clean", True):
            console.print(f"-  Git: [green]Clean[/green] on {branch}")
        else:
            modified = git_info.get("modified_count", 0)
            staged = git_info.get("staged_count", 0)
            untracked = git_info.get("untracked_count", 0)
            status_parts = []
            if modified > 0:
                status_parts.append(f"{modified} modified")
            if staged > 0:
                status_parts.append(f"{staged} staged")
            if untracked > 0:
                status_parts.append(f"{untracked} untracked")
            status_str = ", ".join(status_parts)
            console.print(f"-  Git: [yellow]Dirty[/yellow] on {branch} ({status_str})")

    # 5. Next actions panel (limited to 2 most relevant)
    if next_actions:
        # Only show top 2 most relevant actions to reduce verbosity
        relevant_actions = next_actions[:2]
        actions_content = []
        for action in relevant_actions:
            priority_color = {
                "URGENT": "red",
                "TODO": "yellow",
                "IMPL": "green",
                "CODE": "cyan",
                "READY": "magenta",
                "COMMIT": "blue",
                "PHASE": "yellow",
            }.get(action["priority"], "white")

            actions_content.append(
                f"[{priority_color}]{action['icon']} {action['action']}[/{priority_color}]",
            )
            actions_content.append(f"   Command: [bold]{action['command']}[/bold]")
            actions_content.append("")

        if len(next_actions) > 2:
            actions_content.append(
                f"[dim]... and {len(next_actions) - 2} more suggestions[/dim]",
            )

        actions_panel = create_info_panel(
            "\n".join(actions_content).rstrip(),
            "i  NEXT ACTIONS",
            border_style="green",
        )
        console.print(actions_panel)

    # Show consistent status footer
    show_agent_status_footer(event_name)


def show_agent_start() -> bool:  # noqa: D103, PLR0912
    console.print("\n-  [bold blue]AGENT WORKFLOW EVENT: START[/bold blue]")

    # Show current phase and TODO progress prominently (CRITICAL - always show)
    current_phase = get_current_phase()
    todo_progress = count_todo_checkboxes()
    checklist_info = validate_agent_checklist()

    # Display status summary at the top
    console.print("\n- [bold cyan]CURRENT STATUS:[/bold cyan]")
    console.print(
        f"-  Phase: [bold]{current_phase}[/bold] ({'Planning' if current_phase == PHASE_TODO else 'Implementation'})",
    )
    console.print(f"-  TODO Progress: [bold]{todo_progress['progress_text']}[/bold]")

    # Show relevant AGENTS.md guidance
    if current_phase == PHASE_TODO:
        console.print(
            "\n[dim]📋 AGENTS.md: 'NO code changes in TODO phase. Only changes to _TODO-AGENT.md allowed.'[/dim]",
        )
    else:
        console.print(
            "\n[dim]🚀 AGENTS.md: 'Begin coding session, must be called before making any workspace changes'[/dim]",
        )

    # Display checklist status (WARNING level)
    if should_show_message(MSG_WARNING):
        display_checklist_status(checklist_info)

    # Show next item or completion status (INFO level)
    if should_show_message(MSG_INFO):
        if todo_progress["next_item"] and not todo_progress["is_complete"]:
            console.print(f"->   Next: {todo_progress['next_item'][:80]}...")
        elif todo_progress["is_complete"]:
            console.print(
                "-  [green]All TODO items completed - ready for new tasks![/green]",
            )
    # Show phase panel (INFO level)
    if should_show_message(MSG_INFO):
        if current_phase == PHASE_TODO:
            phase_panel = create_phase_panel(
                current_phase,
                "-  TODO phase - Planning phase",
                [
                    "Update TODO (file _TODO-AGENT.md) only",
                    "Implementation tasks blocked",
                    "Next event you have to trigger before changing the TODO: doit agent-todo-start",
                ],
            )
        else:
            phase_panel = create_phase_panel(
                current_phase,
                "-  IMPL phase - Implementation phase",
                [
                    "Code changes allowed",
                    "Track implementation progress in _TODO-AGENT.md - don't add new tasks!",
                    "Next event you have to trigger to write code: doit agent-coding-start",
                ],
            )
        console.print(phase_panel)

    # Show TODO content if exists (DEBUG level - only in verbose mode)
    if should_show_message(MSG_DEBUG):
        todo_file = Path("_TODO-AGENT.md")
        if todo_file.exists():
            console.print("\n-  [bold yellow]CURRENT TODO STATUS[/bold yellow]")
            try:
                todo_content = todo_file.read_text()
                # Show first 20 lines or until first ## section
                lines = todo_content.split("\n")
                preview_lines = []
                for i, line in enumerate(lines[:20]):
                    if line.startswith("## ") and i > 0:
                        break
                    preview_lines.append(line)

                console.print(
                    create_info_panel(
                        preview_lines,
                        "-  _TODO-AGENT.md Preview",
                        border_style="yellow",
                    ),
                )
            except Exception as e:  # noqa: BLE001
                console.print(f"X  Error reading TODO file: {e}")
        else:
            console.print("\n-  [yellow]No _TODO-AGENT.md found[/yellow]")
            console.print("i  Use 'uv run doit agent-phase-todo' to start planning")

    # Show key AGENTS.md points (INFO level)
    if should_show_message(MSG_INFO):
        console.print("\n-  [bold green]KEY WORKFLOW RULES[/bold green]")
        rules_panel = create_info_panel(
            """*  Core Principles:
1. Auto-commit: Always commit changes (TODO phase: _TODO-AGENT.md, IMPL phase: all)
2. TODO-First: Plan in TODO phase, implement in IMPL phase
3. No dependency YOLOing: Use 'uv run' for all Python commands
4. Test-driven: Write tests when changing code
5. English artifacts: All code, docs, commits in English

-  Phase Commands:
- uv run doit agent-phase-todo  - Switch to planning phase
- uv run doit agent-phase-impl  - Switch to implementation phase

WORKFLOW Workflow Events:
1. doit agent-start     - Call this before doing anything else.  <-- you are here
2. doit agent-coding-start     - Run this before changing any code.
3. doit agent-coding-checkpoint - Run this after making a significant code change.
4. doit agent-pre-commit       - Run mandatory checks before Git commit
5. doit agent-post-commit      - Run mandatory checks and cleanups after Git commit""",
            "-  Essential Agent Rules",
            border_style="green",
        )
        console.print(rules_panel)

    # Provide clear next steps
    console.print("\n*  [bold cyan]NEXT STEPS[/bold cyan]")
    if current_phase == PHASE_TODO:
        console.print("-  You're in TODO phase - update _TODO-AGENT.md for planning")
        console.print(
            "i  When ready: 'uv run doit agent-phase-impl' to start implementation",
        )
    else:
        console.print("-  You're in IMPL phase - ready for implementation")
        console.print("i  Start coding: 'uv run doit agent-coding-start'")

    # Show consistent status footer
    show_agent_status_footer("agent-start")

    return True


def show_start() -> bool | None:  # noqa: D103
    try:
        # Hard git status check - fail if uncommitted changes
        result = run_subprocess(["git", "status", "--porcelain"], quiet=True)
        if result.stdout.strip():
            for _line in result.stdout.strip().split("\n"):
                pass
            sys.exit(1)

        # Hard phase check - fail if in TODO phase
        check_phase_for_implementation()

        # Enforce TODO-First, Implementation-Second rule
        check_todo_implementation_separation()

        # Initialize run_status tracking for all agent events
        run_status_file = Path(".agent-run-status.json")
        run_status = {
            "agent-coding-start": False,
            "agent-coding-checkpoint": False,
            "agent-coding-end": False,
            "agent-pre-commit": False,
            "agent-post-commit": False,
            "session_started": True,
        }
        run_status_file.write_text(json.dumps(run_status, indent=2))

        # Show next steps guidance

        # Set own run_status to True
        run_status = json.loads(run_status_file.read_text())
        run_status["agent-coding-start"] = True
        run_status_file.write_text(json.dumps(run_status, indent=2))

        # Show checklist validation and status footer
        checklist_info = validate_agent_checklist()
        display_checklist_status(checklist_info)
        show_agent_status_footer("agent-coding-start")

        return True  # noqa: TRY300

    except Exception:  # noqa: BLE001
        # Don't exit here - let the task dependency system handle failures
        return False


def show_checkpoint() -> bool | None:  # noqa: D103
    try:
        # Check if coding session was started
        run_status_file = Path(".agent-run-status.json")
        if not run_status_file.exists():
            pass
        else:
            run_status = json.loads(run_status_file.read_text())
            if not run_status.get("agent-coding-start", False):
                pass

        # Show next steps guidance

        # Update run status
        if run_status_file.exists():
            run_status = json.loads(run_status_file.read_text())
            run_status["agent-coding-checkpoint"] = True
            run_status_file.write_text(json.dumps(run_status, indent=2))

        # Show consistent status footer
        show_agent_status_footer("agent-coding-checkpoint")

        return True  # noqa: TRY300

    except Exception:  # noqa: BLE001
        return True  # Don't fail the checkpoint for status tracking errors


def show_todo_start() -> bool | None:  # noqa: D103, PLR0912, PLR0915
    try:
        console.print("\n-  [bold blue]TODO PLANNING SESSION START[/bold blue]")
        console.print("*  [cyan]Structured planning workflow for TODO phase[/cyan]")

        # Validate we're in TODO phase or can switch to it
        current_phase = get_current_phase()
        if current_phase != PHASE_TODO:
            console.print("!   [yellow]Not in TODO phase - switching now [/yellow]")

            # Switch to TODO phase first
            try:
                set_phase_with_display(PHASE_TODO)
                console.print("OK  [green]Switched to TODO phase for planning[/green]")
            except Exception as e:  # noqa: BLE001
                console.print(f"X  [red]Failed to switch to TODO phase: {e}[/red]")
                return False

        # Show current TODO status and progress
        todo_progress = count_todo_checkboxes()
        console.print("\n- [bold cyan]CURRENT TODO STATUS:[/bold cyan]")
        console.print(f"-  Progress: [bold]{todo_progress['progress_text']}[/bold]")

        # Validate TODO phase discipline
        discipline_check = validate_todo_phase_discipline()
        if not discipline_check["is_valid"]:
            console.print("X  [red]TODO PHASE DISCIPLINE VIOLATION![/red]")
            console.print(
                f"ERROR Found {discipline_check['total_violations']} completed checkboxes in TODO phase",
            )
            console.print("\n-  Violations found:")
            for violation in discipline_check["violations"][:3]:  # Show first 3
                console.print(f"  Line {violation['line']}: {violation['content']}")
            if len(discipline_check["violations"]) > 3:  # noqa: PLR2004
                console.print(
                    f"  ... and {len(discipline_check['violations']) - 3} more",
                )
            console.print("\ni  TODO phase is for planning only:")
            console.print("i  - Use [ ] for planning tasks, not [x]")
            console.print("i  - Mark checkboxes as done only in IMPL phase")
            console.print("i  - Use bullet points (-) for analysis and notes")
        else:
            console.print("OK  [green]TODO phase discipline check passed[/green]")

        if todo_progress["next_item"]:
            console.print(f"->   Next item: {todo_progress['next_item'][:80]}...")
        elif todo_progress["is_complete"]:
            console.print("-  [green]All TODO items completed![/green]")
        else:
            console.print(
                "i  [yellow]No TODO checkboxes found - ready for planning[/yellow]",
            )

        # Show TODO file status
        todo_file = Path("_TODO-AGENT.md")
        if todo_file.exists():
            console.print(
                "OK  [green]_TODO-AGENT.md exists - ready for editing[/green]",
            )

            # Show brief content preview
            try:
                content = todo_file.read_text()
                lines = content.split("\n")
                preview_lines = []
                for i, line in enumerate(lines[:10]):
                    if line.startswith("## ") and i > 0:
                        break
                    preview_lines.append(line)

                console.print(
                    create_info_panel(
                        preview_lines,
                        "-  Current TODO Preview (first 10 lines)",
                        border_style="blue",
                    ),
                )
            except Exception as e:  # noqa: BLE001
                console.print(f"!   [yellow]Could not read TODO content: {e}[/yellow]")
        else:
            console.print("-  [yellow]No _TODO-AGENT.md found[/yellow]")
            console.print("i  Create TODO file to start planning")

        # Show planning guidance
        planning_panel = create_info_panel(
            """*  TODO Planning Session Guidelines:

-  Planning Activities (TODO phase only):
- Update _TODO-AGENT.md with task breakdown
- Add checkboxes for implementation tasks: - [ ] Task description
- Analyze requirements and approach
- Plan file changes and implementation steps
- Use bullet points (-) for notes and analysis

ERROR NOT Allowed in TODO Phase:
- Marking checkboxes as done: - [x] (only in IMPL phase)
- Making code changes
- Running implementation tasks

OK  When Planning is Complete:
- Commit TODO changes: git add _TODO-AGENT.md && git commit
- Switch to IMPL phase: uv run doit agent-phase-impl
- Start implementation: uv run doit agent-coding-start""",
            "-  TODO Planning Workflow",
            border_style="blue",
        )
        console.print(planning_panel)

        # Show consistent status footer
        show_agent_status_footer("agent-todo-start")

        return True  # noqa: TRY300

    except Exception as e:  # noqa: BLE001
        console.print(f"X  [red]ERROR in agent-todo-start: {e}[/red]")
        console.print("i  Planning session may not have started properly")
        return False


def run_pre_commit_strict_linting():
    """Run strict linting for pre-commit validation.

    Backward compatibility wrapper for run_linting().
    """
    return run_linting(mode="pre-commit")


def show_pre_commit() -> bool | None:  # noqa: D103
    try:
        # Check workflow dependency chain
        run_status_file = Path(".agent-run-status.json")
        if not run_status_file.exists():
            console.print("!   [yellow]WARNING: No agent session detected[/yellow]")
            console.print("i  Consider running the full workflow before committing")
        else:
            run_status = json.loads(run_status_file.read_text())
            if not run_status.get("agent-coding-end", False):
                console.print(
                    "!   [yellow]WARNING: Coding session not properly ended[/yellow]",
                )
                console.print(
                    "i  Recommended: agent-coding-start -> checkpoint -> end -> pre-commit",
                )

        console.print("\n🔒 [bold red]HARD QUALITY GATES - PRE-COMMIT[/bold red]")
        console.print("[green]OK  lint_strict passed (hard requirement)[/green]")
        console.print("[green]OK  test passed (hard requirement)[/green]\n")

        # Update run status
        if run_status_file.exists():
            run_status = json.loads(run_status_file.read_text())
            run_status["agent-pre-commit"] = True
            run_status_file.write_text(json.dumps(run_status, indent=2))

        # Get current phase for checklist
        current_phase = get_current_phase()

        # Enhanced checklist with rich formatting - phase-specific
        if current_phase == PHASE_TODO:
            checklist_content = """-  TODO PHASE CHECKLIST:

- [ ] I know that we are in TODO phase (evidence?)
- [ ] I have only changed _TODO-AGENT.md, nothing else (evidence?)
- [ ] I have tracked progress in _TODO-AGENT.md? ([X completed] / [Y total] items | Finished: [yes/no])
- [ ] Can I continue right away? (YES: [next TODO task] | NO: ask user for direction)
- [ ] I understand that I MUST commit immediately after filling this checklist
  (YES: I will run 'git add _TODO-AGENT.md && git commit' right now | NO: I need help)

- [ ] I called all relevant workflow events for phase [PHASE] ([N events called] evidence?)
- [ ] Everything ready for commit? Will I show the resulting commit ID to the user?
  (YES: [commit details] | NO: [reason])"""
            checklist_title = "-  AGENT PRE-COMMIT CHECKLIST - TODO PHASE"
        else:
            checklist_content = """-  IMPLEMENTATION PHASE CHECKLIST:

- [ ] I know that we are in IMPL phase (evidence?)
- [ ] I have written tests for new functionality (YES: [N new tests] |
      NO: [TODO phase/other reason])
- [ ] I can confirm that tests are green (YES: Number of tests ran: [N tests ran] |
      NO: Test failures: [N test failures])
- [ ] I have tracked progress in _TODO-AGENT.md? ([X completed] / [Y total] items |
      Finished: [yes/no])
- [ ] Can I continue right away? (YES: [next TODO task] |
      NO: ask user for direction!)
- [ ] I understand that I MUST commit immediately after filling this checklist
      (YES: I will run 'git add <files> && git commit' right now | NO: I need help)

- [ ] I called all relevant workflow events for phase [PHASE]
      ([N events called] evidence?)
- [ ] Everything ready for commit? Will I show the resulting commit ID to the user?
      (YES: [commit details] | NO: [reason])"""
            checklist_title = "-  AGENT PRE-COMMIT CHECKLIST - IMPL PHASE"

        checklist_panel = create_info_panel(
            checklist_content,
            checklist_title,
            border_style="green",
        )
        console.print(checklist_panel)
        console.print(
            "\n[bold green]i  Quality gates PASSED - safe to commit![/bold green]",
        )

        # CRITICAL AUTO-COMMIT REMINDER
        console.print(
            "\n!  [bold red]MANDATORY AUTO-COMMIT REMINDER (RULE 1):[/bold red]",
        )
        console.print(
            "!   [yellow]You MUST commit your changes immediately after filling the "
            "checklist above - NO DELAY ALLOWED![/yellow]",
        )
        console.print("-  [cyan]Required workflow:[/cyan]")
        console.print("   1. Fill out the checklist above")
        console.print("   2. Run: git add <files>")
        if current_phase == PHASE_TODO:
            console.print('   3. Run: git commit -m "todo: <description>"')
        else:
            console.print('   3. Run: git commit -m "<conventional commit message>"')
        console.print("   4. Run: uv run doit agent-post-commit")
        console.print("")
        console.print(
            "ERROR [red]FAILURE TO COMMIT IMMEDIATELY IS A CRITICAL RULE 1 VIOLATION![/red]",
        )
        console.print("i  [green]This reminder prevents auto-commit failures[/green]")

        # Show checklist validation and status footer
        checklist_info = validate_agent_checklist()
        display_checklist_status(checklist_info)
        show_agent_status_footer("agent-pre-commit")

        return True  # noqa: TRY300

    except Exception as e:  # noqa: BLE001
        console.print(f"X  [red]ERROR in agent-pre-commit: {e}[/red]")
        console.print("i  Quality gates may have passed, but status tracking failed")
        return True  # Don't fail for status tracking errors


def show_coding_task_finished() -> bool | None:  # noqa: D103
    try:
        # Check workflow dependency chain
        run_status_file = Path(".agent-run-status.json")
        if not run_status_file.exists():
            pass
        else:
            run_status = json.loads(run_status_file.read_text())
            if not run_status.get("agent-coding-start", False):
                pass

        # Show next steps guidance

        # Update run status
        if run_status_file.exists():
            run_status = json.loads(run_status_file.read_text())
            run_status["agent-coding-task-finished"] = True
            run_status_file.write_text(json.dumps(run_status, indent=2))

        # Show checklist validation and status footer
        checklist_info = validate_agent_checklist()
        display_checklist_status(checklist_info)
        show_agent_status_footer("agent-coding-end")

        return True  # noqa: TRY300

    except Exception:  # noqa: BLE001
        return True  # Don't fail for status tracking errors


def show_todo_end() -> bool | None:  # noqa: D103, PLR0912, PLR0915
    try:
        console.print("\n-  [bold blue]TODO PLANNING SESSION END[/bold blue]")
        console.print(
            "*  [cyan]Validating planning completion and preparing for implementation[/cyan]",
        )

        # Validate we're in TODO phase
        current_phase = get_current_phase()
        if current_phase != PHASE_TODO:
            console.print(
                "!   [yellow]Not in TODO phase - cannot end TODO session[/yellow]",
            )
            console.print("i  TODO session end requires TODO phase")
            console.print(
                "i  Use 'uv run doit agent-phase-todo' to switch to TODO phase first",
            )
            return False

        # Validate TODO file exists and has content
        todo_file = Path("_TODO-AGENT.md")
        if not todo_file.exists():
            console.print("X  [red]No _TODO-AGENT.md found![/red]")
            console.print("i  Create TODO file before ending planning session")
            console.print("i  Use 'uv run doit agent-todo-start' to begin planning")
            return False

        # Analyze TODO content and progress
        todo_progress = count_todo_checkboxes()
        console.print("\n- [bold cyan]TODO PLANNING ANALYSIS:[/bold cyan]")
        console.print(f"-  Progress: [bold]{todo_progress['progress_text']}[/bold]")

        # Validate planning quality
        validation_issues = []
        planning_quality = "good"

        try:
            content = todo_file.read_text()
            lines = content.split("\n")

            # Check for basic planning elements
            has_goal = any("goal" in line.lower() for line in lines[:20])
            has_checkboxes = todo_progress["total"] > 0
            has_files_section = any("files to modify" in line.lower() for line in lines)
            has_changes_section = any("changes:" in line.lower() for line in lines)

            if not has_goal:
                validation_issues.append("No clear task goal found in first 20 lines")
            if not has_checkboxes:
                validation_issues.append("No implementation checkboxes found")
                planning_quality = "minimal"
            elif todo_progress["total"] < 3:  # noqa: PLR2004
                validation_issues.append(
                    f"Only {todo_progress['total']} checkboxes - consider more detailed breakdown",
                )
                planning_quality = "basic"
            if not has_files_section:
                validation_issues.append("No 'Files to modify' section found")
            if not has_changes_section:
                validation_issues.append("No 'Changes:' section found")

            # Check for completed checkboxes (should not exist in TODO phase)
            if todo_progress["completed"] > 0:
                validation_issues.append(
                    f"Found {todo_progress['completed']} completed checkboxes - "
                    "these should only be marked in IMPL phase",
                )
                planning_quality = "problematic"

        except Exception as e:  # noqa: BLE001
            validation_issues.append(f"Could not analyze TODO content: {e}")
            planning_quality = "unknown"

        # Report planning quality
        if planning_quality == "good":
            console.print(
                "OK  [green]Planning quality: GOOD - ready for implementation[/green]",
            )
        elif planning_quality == "basic":
            console.print(
                "!   [yellow]Planning quality: BASIC - consider more detail[/yellow]",
            )
        elif planning_quality == "minimal":
            console.print(
                "!   [yellow]Planning quality: MINIMAL - add implementation checkboxes[/yellow]",
            )
        elif planning_quality == "problematic":
            console.print(
                "X  [red]Planning quality: PROBLEMATIC - fix issues before proceeding[/red]",
            )
        else:
            console.print(
                "UNK [yellow]Planning quality: UNKNOWN - manual review needed[/yellow]",
            )

        # Show validation issues
        if validation_issues:
            console.print("\n- [yellow]Planning validation issues:[/yellow]")
            for issue in validation_issues:
                console.print(f"  - {issue}")

        # Show transition guidance
        if planning_quality in ["good", "basic"] and todo_progress["completed"] == 0:
            transition_panel = Panel(
                """OK  Planning Complete - Ready for Implementation:

-  Next Steps:
1. Commit TODO changes: git add _TODO-AGENT.md && git commit -m "todo: ..."
2. Switch to IMPL phase: uv run doit agent-phase-impl
3. Start implementation: uv run doit agent-coding-start

*  Implementation Guidelines:
- Mark checkboxes as done: [ ] -> [x] as you complete tasks
- Update _TODO-AGENT.md progress regularly
- Commit changes with proper checklist in commit message
- Use agent workflow events for structured development""",
                title="-  Ready for Implementation",
                border_style="green",
                box=box.ROUNDED,
            )
        else:
            transition_panel = Panel(
                """!   Planning Needs Improvement:

-  Recommended Actions:
- Add more detailed implementation checkboxes
- Include 'Files to modify' and 'Changes:' sections
- Remove any completed checkboxes (save for IMPL phase)
- Ensure clear task goal and approach

-  Continue Planning:
- Update _TODO-AGENT.md with more detail
- Run 'uv run doit agent-todo-end' again when ready
- Only switch to IMPL phase when planning is complete""",
                title="-  Continue Planning",
                border_style="yellow",
                box=box.ROUNDED,
            )

        console.print(transition_panel)

        # Show consistent status footer
        show_agent_status_footer("agent-todo-end")

        return True  # noqa: TRY300

    except Exception as e:  # noqa: BLE001
        console.print(f"X  [red]ERROR in agent-todo-end: {e}[/red]")
        console.print("i  Planning session end may not have completed properly")
        return False


def show_post_commit() -> bool:  # noqa: PLR0912, PLR0915
    """Display post-commit validation and cleanup."""
    console.print("\n- [bold blue]POST-COMMIT VALIDATION[/bold blue]")
    console.print("-   [cyan]This task ALWAYS runs - enhanced reliability phase[/cyan]")

    # Show current phase and TODO progress prominently
    current_phase = get_current_phase()
    todo_progress = count_todo_checkboxes()

    console.print("\n- [bold cyan]CURRENT STATUS:[/bold cyan]")
    console.print(
        f"-  Phase: [bold]{current_phase}[/bold] ({'Planning' if current_phase == PHASE_TODO else 'Implementation'})",
    )
    console.print(f"-  TODO Progress: [bold]{todo_progress['progress_text']}[/bold]")

    if todo_progress["next_item"] and not todo_progress["is_complete"]:
        console.print(f"->   Next: {todo_progress['next_item'][:80]}...")
    elif todo_progress["is_complete"]:
        console.print("-  [green]All TODO items completed![/green]")
    elif todo_progress["total"] == 0:
        console.print("i  Consider adding TODO checkboxes for progress tracking")

    # Always run validation, even on failures - enhanced reliability
    validation_errors = []
    workflow_state_log = []

    try:
        # 1. Verify actual commit exists and get details
        result = run_subprocess(
            ["git", "log", "-1", "--format=%H|%s|%b"],
            quiet=True,
        )
        if result.returncode != 0 or not result.stdout.strip():
            validation_errors.append("No recent commit found")
        else:
            commit_parts = result.stdout.strip().split("|", 2)
            commit_hash = commit_parts[0][:8]  # Short hash
            commit_subject = commit_parts[1] if len(commit_parts) > 1 else ""
            commit_body = commit_parts[2] if len(commit_parts) > 2 else ""  # noqa: PLR2004

            console.print(f"OK  [green]Commit verified: {commit_hash}[/green]")
            console.print(f"-  Subject: {commit_subject}")

            # 2. Validate commit message format and checklist
            full_commit_msg = (
                f"{commit_subject}\n{commit_body}" if commit_body else commit_subject
            )

            # Check for checklist in commit message
            has_checklist = (
                "Quick Checklist:" in full_commit_msg or "- [" in full_commit_msg
            )
            if has_checklist:
                console.print("OK  [green]Checklist found in commit message[/green]")

                # Count completed checklist items
                completed_items = full_commit_msg.count(
                    "- [x]",
                ) + full_commit_msg.count("- [OK]")
                total_items = completed_items + full_commit_msg.count("- [ ]")

                if completed_items > 0:
                    console.print(
                        f"-  Checklist: {completed_items}/{total_items} items completed",
                    )
                else:
                    validation_errors.append(
                        "Checklist found but no items marked as completed",
                    )

                # Validate phase-specific checklist elements
                current_phase = get_current_phase()
                phase_validation = validate_phase_specific_checklist(
                    full_commit_msg,
                    current_phase,
                )

                if phase_validation["is_valid"]:
                    console.print(
                        f"OK  [green]Correct {current_phase} phase checklist validated[/green]",
                    )
                else:
                    console.print(
                        f"!   [yellow]Phase-specific checklist validation issues for {current_phase}:[/yellow]",
                    )
                    for missing_element in phase_validation["missing_elements"]:
                        console.print(f"  - Missing: {missing_element}")
                    validation_errors.append(
                        f"Phase-specific checklist elements missing for {current_phase} phase",
                    )
            else:
                validation_errors.append("No checklist found in commit message")

            # 3. Check conventional commit format (basic)
            conventional_prefixes = [
                "feat:",
                "fix:",
                "docs:",
                "style:",
                "refactor:",
                "test:",
                "chore:",
                "todo:",
            ]
            has_conventional_format = any(
                commit_subject.startswith(prefix) for prefix in conventional_prefixes
            )

            if has_conventional_format:
                console.print("OK  [green]Conventional commit format detected[/green]")
            else:
                console.print(
                    "!   [yellow]No conventional commit prefix detected[/yellow]",
                )

    except Exception as e:  # noqa: BLE001
        validation_errors.append(f"Failed to verify commit: {e}")

    # 4. Check run_status - warn if events were skipped (always runs)
    try:
        run_status_file = Path(".agent-run-status.json")
        if run_status_file.exists():
            run_status = json.loads(run_status_file.read_text())

            # Log workflow state changes
            workflow_state_log.append("- Workflow State Analysis:")
            for event, completed in run_status.items():
                if event.startswith("agent-"):
                    status_icon = "OK " if completed else "X "
                    workflow_state_log.append(f"  {status_icon} {event}: {completed}")

            run_status["agent-post-commit"] = True

            skipped_events = [
                event
                for event, completed in run_status.items()
                if event.startswith("agent-")
                and not completed
                and event != "agent-post-commit"
            ]

            if skipped_events:
                console.print(
                    "!   [yellow]WARNING: Some agent events were skipped:[/yellow]",
                )
                for event in skipped_events:
                    console.print(f"  - {event}")
                console.print("i  Consider running the full agent workflow next time")

                # Fallback behavior: suggest recovery actions
                console.print("\n-  [cyan]FALLBACK SUGGESTIONS:[/cyan]")
                if "agent-coding-start" not in skipped_events:
                    console.print("  - Next time: uv run doit agent-coding-start")
                if "agent-pre-commit" in skipped_events:
                    console.print(
                        "  - Quality gates may have been skipped - review commit carefully",
                    )
            else:
                console.print("OK  [green]All agent workflow events completed[/green]")

            run_status_file.write_text(json.dumps(run_status, indent=2))

            # Log final workflow state
            workflow_state_log.append(f"-  Final state logged to {run_status_file}")

        else:
            # Fallback: create minimal run status if missing
            console.print(
                "!   [yellow]No run status file found - creating fallback[/yellow]",
            )
            fallback_status = {
                "agent-post-commit": True,
                "fallback_created": True,
                "session_started": False,
            }
            run_status_file.write_text(json.dumps(fallback_status, indent=2))
            workflow_state_log.append("-  Fallback run status created")

    except Exception as e:  # noqa: BLE001
        validation_errors.append(f"Failed to update run status: {e}")
        # Fallback: continue without status tracking
        console.print(
            f"!   [yellow]Status tracking failed, continuing anyway: {e}[/yellow]",
        )
        workflow_state_log.append(f"X  Status tracking error: {e}")

    # 5. Report validation results (always runs)
    if validation_errors:
        console.print("\n!   [yellow]POST-COMMIT VALIDATION WARNINGS:[/yellow]")
        for error in validation_errors:
            console.print(f"  - {error}")
        console.print("\ni  Consider improving commit quality for next time")
    else:
        console.print("\n-  [bold green]POST-COMMIT VALIDATION PASSED![/bold green]")

    # 6. Display workflow state log (always runs)
    if workflow_state_log:
        console.print("\n-  [bold cyan]WORKFLOW STATE LOG:[/bold cyan]")
        for log_entry in workflow_state_log:
            console.print(f"  {log_entry}")

    console.print("\n- [cyan]Running cleanup...[/cyan]")
    console.print(
        "-   [green]POST-COMMIT COMPLETED - Enhanced reliability phase[/green]",
    )

    # Show next steps guidance
    console.print("\n*  [bold cyan]NEXT STEPS:[/bold cyan]")
    console.print("OK  If you have more work: Continue with your next task")
    console.print("OK  If you're done: No further action required")
    console.print("i  Remember: Always start new work with 'uv run doit agent-start'")

    # Always return True - this task must never fail
    return True


def show_workflow() -> bool:
    """Display agent workflow diagrams and documentation."""
    console.print("\n-  [bold blue]AGENT WORKFLOW DIAGRAMS[/bold blue]")
    console.print("📘 [cyan]Comprehensive visualization of agent workflows[/cyan]\n")

    # Read workflow diagrams from docs
    workflow_file = Path("docs/agent_workflow_diagrams.md")
    if workflow_file.exists():
        try:
            content = workflow_file.read_text()
            console.print(
                Panel(
                    content,
                    title="-  Agent Workflow Diagrams",
                    border_style="blue",
                    box=box.ROUNDED,
                ),
            )
        except Exception as e:  # noqa: BLE001
            console.print(f"X  [red]Error reading workflow diagrams: {e}[/red]")
            console.print(
                "i  [yellow]Showing fallback workflow information:[/yellow]\n",
            )

            # Fallback content
            fallback_content = """
DOCS TODO Phase Workflow:
1. agent-start -> agent-todo-start -> Plan in _TODO-AGENT.md -> agent-pre-commit -> commit -> agent-post-commit

-  IMPL Phase Workflow:
1. agent-start -> agent-coding-start -> [agent-coding-checkpoint] -> agent-pre-commit -> commit -> agent-post-commit

-  Key Principles:
- Always start with agent-start
- TODO phase: Planning only, use [ ] checkboxes
- IMPL phase: Implementation, use [x] checkboxes
- Auto-commit after pre-commit validation
- User controls phase transitions
"""
            console.print(
                Panel(
                    fallback_content,
                    title="-  Fallback Workflow Information",
                    border_style="yellow",
                    box=box.ROUNDED,
                ),
            )
    else:
        console.print(
            "X  [red]Workflow diagrams file not found: docs/agent_workflow_diagrams.md[/red]",
        )
        console.print(
            "i  [yellow]Run 'uv run doit docs' to generate documentation[/yellow]",
        )

    # Show key workflow commands
    commands_panel = Panel(
        """COMMANDS Essential Workflow Commands:

-  TODO Phase:
- uv run doit agent-start           # Start any agent session
- uv run doit agent-todo-start      # Begin TODO planning
- uv run doit agent-pre-commit      # Validate before TODO commit
- uv run doit agent-post-commit     # Cleanup after TODO commit

-  IMPL Phase:
- uv run doit agent-start           # Start any agent session
- uv run doit agent-coding-start    # Begin coding session
- uv run doit agent-coding-checkpoint # Validate during coding
- uv run doit agent-pre-commit      # Validate before code commit
- uv run doit agent-post-commit     # Cleanup after code commit

-  Phase Management:
- uv run doit agent-phase-todo       # Switch to TODO phase
- uv run doit agent-phase-impl       # Switch to IMPL phase

-  Quick Reference:
- Always commit immediately after pre-commit
- Never suggest phase switches - user decides
- Use [ ] in TODO phase, [x] in IMPL phase only
""",
        title="-  Workflow Commands Reference",
        border_style="green",
        box=box.ROUNDED,
    )
    console.print(commands_panel)

    # Show workflow tips
    tips_panel = Panel(
        """i  Workflow Tips:

*  Best Practices:
- Start every agent session with 'agent-start'
- Plan thoroughly in TODO phase before implementation
- Commit frequently with proper checklists
- Update _TODO-AGENT.md progress in IMPL phase
- Always run post-commit for cleanup

!  Common Pitfalls:
- Forgetting to run agent-pre-commit before commit
- Using [x] checkboxes in TODO phase
- Suggesting phase switches instead of waiting for user
- Not committing immediately after pre-commit validation
- Skipping agent-post-commit

OK  Success Patterns:
- TODO: Research -> Plan -> Commit -> Wait for user
- IMPL: Code -> Test -> Commit -> Update TODO -> Continue/Finalize
""",
        title="i  Workflow Tips & Best Practices",
        border_style="magenta",
        box=box.ROUNDED,
    )
    console.print(tips_panel)

    console.print("\n-  [bold green]WORKFLOW DISPLAY COMPLETE[/bold green]")
    console.print(
        "-  [cyan]See docs/agent_workflow_diagrams.md for detailed diagrams[/cyan]",
    )

    return True


def validate_all_tools() -> bool:
    """Validate that all required development tools are available."""
    console.print("\n-  [bold cyan]TOOL AVAILABILITY CHECK[/bold cyan]")
    console.print("Validating all expected development tools...\n")

    # Core tools that must be available
    tools = [
        ("bandit", "bandit --help"),
        ("build", "python -m build --help"),
        ("coverage", "coverage --version"),
        ("mdformat", "mdformat --help"),
        ("mypy", "mypy --version"),
        ("pylint", "pylint --version"),
        ("pytest", "pytest --version"),
        ("ruff", "ruff --version"),
        ("validate-pyproject", "validate-pyproject --help"),
    ]

    checked_tools: dict[str, subprocess.CompletedProcess | None] = {}
    for tool_name, command in tools:
        tool_result = check_tool_available(tool_name, command)
        checked_tools[tool_name] = tool_result

    # Summary with rich table
    table = Table(title="Tool status", box=box.SIMPLE)
    table.add_column("Tool", style="cyan", no_wrap=True)
    table.add_column("Status", style="cyan", no_wrap=True)

    tool_failed = False

    for tool_name, tool_result in checked_tools.items():
        status_ok = tool_result is not None and tool_result.returncode == 0
        tool_failed = tool_failed or not status_ok
        status_text = "OK  OK" if status_ok else "X  FAIL"
        table.add_row(tool_name, status_text)

    console.print("\n")
    console.print(table)

    # doit expects True for success, False for failure
    return not tool_failed


def validate_todo() -> bool:  # noqa: PLR0912
    """Validate TODO file syntax, structure, and formatting."""
    console.print("-  [bold blue]MARKDOWN VALIDATION[/bold blue]")
    console.print("Validating TODO file syntax, structure, and formatting...")

    todo_file = Path("_TODO-AGENT.md")
    if not todo_file.exists():
        console.print(
            "!   [yellow]No _TODO-AGENT.md found - skipping validation[/yellow]",
        )
        return True

    validation_errors = []
    warnings = []

    try:
        # 1. Check mdformat compliance first
        console.print("- Checking mdformat compliance...")
        result = run_subprocess(
            ["uv", "run", "mdformat", "--check", str(todo_file)],
            quiet=True,
        )

        if result.returncode != 0:
            validation_errors.append(
                "File is not mdformat compliant - run 'uv run doit format-markdown' to fix",
            )
        else:
            console.print("OK  [green]mdformat compliance check passed[/green]")

        # 2. Basic structure validation
        content = todo_file.read_text(encoding="utf-8")
        lines = content.split("\n")

        has_goal_section = False
        has_checkboxes = False
        checkbox_count = 0

        for i, line in enumerate(lines, 1):
            # Check for goal/task section
            if line.strip().lower().startswith("task goal") or "goal" in line.lower():
                has_goal_section = True

            # Check checkbox format
            if "- [" in line:
                checkbox_count += 1
                has_checkboxes = True

                # Validate checkbox syntax
                if not (
                    line.strip().startswith("- [ ]") or line.strip().startswith("- [x]")
                ):
                    validation_errors.append(
                        f"Line {i}: Invalid checkbox format: {line.strip()}",
                    )

            # Check for common markdown issues
            if (
                line.strip().startswith("#")
                and not line.startswith("# ")
                and len(line.strip()) > 1
            ):
                warnings.append(
                    f"Line {i}: Missing space after # in heading: {line.strip()}",
                )

            # Check for unbalanced backticks
            backtick_count = line.count("`")
            if backtick_count % 2 != 0:
                warnings.append(f"Line {i}: Unbalanced backticks: {line.strip()}")

        # Structure validation
        if not has_goal_section:
            warnings.append("No clear task goal section found")

        if not has_checkboxes:
            warnings.append("No checkboxes found - consider adding progress tracking")
        elif checkbox_count < 3:  # noqa: PLR2004
            warnings.append(
                f"Only {checkbox_count} checkboxes found - consider breaking down tasks",
            )

    except Exception as e:  # noqa: BLE001
        validation_errors.append(f"Failed to validate markdown: {e}")

    # Report results
    if validation_errors:
        console.print("X  [red]MARKDOWN VALIDATION FAILED[/red]")
        for error in validation_errors:
            console.print(f"  - {error}")
        return False

    if warnings:
        console.print("!   [yellow]MARKDOWN VALIDATION WARNINGS[/yellow]")
        for warning in warnings:
            console.print(f"  - {warning}")

    console.print("OK  [green]Markdown validation passed[/green]")
    console.print(f"  - {len(lines)} lines checked")
    console.print(f"  - {checkbox_count} checkboxes found")
    console.print(f"  - {len(warnings)} warnings")

    return True
