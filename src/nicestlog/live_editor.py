"""🔥 Live Code Editor - Interactive editing of transformation proposals.

Provides in-terminal code editing with syntax highlighting and validation.
Records all user edits for machine learning and pattern improvement.
"""

import ast
import json
import os
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

import structlog
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.syntax import Syntax

log = structlog.get_logger("nicestlog.live_editor")
console = Console()


@dataclass
class EditSession:
    """Records an editing session for machine learning."""

    original_code: str
    ai_suggestion: str
    user_final_code: str
    edit_steps: list[str]
    pattern_name: str
    file_path: str
    line_number: int
    accepted: bool
    edit_duration_seconds: float
    syntax_errors_encountered: int = 0


class LiveCodeEditor:
    """🔥 Live Code Editor for Interactive Transformations.

    Allows users to edit AI transformation suggestions in real-time
    with syntax highlighting, validation, and comprehensive logging.
    """

    def __init__(self, *, use_external_editor: bool = False) -> None:
        self.use_external_editor = use_external_editor
        self.edit_sessions: list[EditSession] = []

        log.debug(
            "live-editor-initialized",
            _replace_msg="🔥 Live Code Editor initialized (external: {external})",
            external=use_external_editor,
        )

    def edit_transformation(
        self,
        original_code: str,
        suggested_code: str,
        pattern_name: str,
        file_path: str,
        line_number: int,
    ) -> tuple[str, bool, EditSession]:
        """Edit a transformation suggestion interactively.

        Returns:
            - Final code (user-edited or original suggestion)
            - Whether user accepted the result
            - Edit session data for ML

        """
        start_time = time.time()

        log.info(
            "edit-session-started",
            _replace_msg="🔥 Starting edit session for {pattern} at {file}:{line}",
            pattern=pattern_name,
            file=file_path,
            line=line_number,
        )

        edit_steps = []
        current_code = suggested_code
        syntax_errors = 0

        # Show the initial suggestion
        self._show_edit_interface(original_code, current_code, pattern_name)

        while True:
            choice = self._get_edit_choice()

            if choice == "edit":
                new_code, had_errors = self._edit_code_interactive(current_code)
                if had_errors:
                    syntax_errors += 1

                if new_code != current_code:
                    edit_steps.append(f"Changed: {current_code!r} -> {new_code!r}")
                    current_code = new_code

                    log.info(
                        "code-edited",
                        _replace_msg="✏️ User edited code",
                        original_length=len(suggested_code),
                        new_length=len(current_code),
                        edit_step=len(edit_steps),
                    )

                    # Show updated interface
                    self._show_edit_interface(original_code, current_code, pattern_name)

            elif choice == "accept":
                end_time = time.time()
                duration = end_time - start_time

                session = EditSession(
                    original_code=original_code,
                    ai_suggestion=suggested_code,
                    user_final_code=current_code,
                    edit_steps=edit_steps,
                    pattern_name=pattern_name,
                    file_path=file_path,
                    line_number=line_number,
                    accepted=True,
                    edit_duration_seconds=duration,
                    syntax_errors_encountered=syntax_errors,
                )

                self.edit_sessions.append(session)

                log.info(
                    "edit-session-accepted",
                    _replace_msg="✅ Edit session accepted after {duration:.1f}s with {edits} edits",
                    duration=duration,
                    edits=len(edit_steps),
                    syntax_errors=syntax_errors,
                    final_code_length=len(current_code),
                )

                return current_code, True, session

            elif choice == "reject":
                end_time = time.time()
                duration = end_time - start_time

                session = EditSession(
                    original_code=original_code,
                    ai_suggestion=suggested_code,
                    user_final_code=current_code,
                    edit_steps=edit_steps,
                    pattern_name=pattern_name,
                    file_path=file_path,
                    line_number=line_number,
                    accepted=False,
                    edit_duration_seconds=duration,
                    syntax_errors_encountered=syntax_errors,
                )

                self.edit_sessions.append(session)

                log.info(
                    "edit-session-rejected",
                    _replace_msg="❌ Edit session rejected after {duration:.1f}s",
                    duration=duration,
                    edits=len(edit_steps),
                    syntax_errors=syntax_errors,
                )

                return suggested_code, False, session

            elif choice == "reset":
                edit_steps.append("RESET to original suggestion")
                current_code = suggested_code
                console.print("🔄 [yellow]Reset to original AI suggestion[/yellow]")
                self._show_edit_interface(original_code, current_code, pattern_name)

    def _show_edit_interface(
        self,
        original_code: str,
        current_code: str,
        pattern_name: str,
    ) -> None:
        """Show the editing interface with before/after comparison."""
        console.print("\n" + "=" * 80)
        console.print(
            f"🔥 [bold blue]Live Code Editor[/bold blue] - Pattern: [cyan]{pattern_name}[/cyan]",
        )

        # Original code
        console.print(
            Panel(
                Syntax(original_code, "python", theme="monokai", line_numbers=False),
                title="[red]Original Code[/red]",
                border_style="red",
            ),
        )

        # Current suggestion/edit
        console.print(
            Panel(
                Syntax(current_code, "python", theme="monokai", line_numbers=False),
                title="[green]Current Transformation[/green]",
                border_style="green",
            ),
        )

    def _get_edit_choice(self) -> str:
        """Get user's choice for what to do next."""
        while True:
            choice = Prompt.ask(
                (
                    "🔥 [bold yellow][e][/bold yellow]dit/[bold green][a][/bold green]ccept"
                    "/[bold red][r][/bold red]eject/[bold blue]reset[/bold blue]"
                ),
                default="e",
                show_default=False,
            ).lower()

            if choice in {"e", "edit"}:
                return "edit"
            if choice in {"a", "accept"}:
                return "accept"
            if choice in {"r", "reject"}:
                return "reject"
            if choice == "reset":
                return "reset"
            console.print("[red]Invalid choice. Use e/a/r/reset[/red]")

    def _edit_code_interactive(self, current_code: str) -> tuple[str, bool]:
        """Edit code interactively in the terminal."""
        if self.use_external_editor:
            return self._edit_with_external_editor(current_code)
        return self._edit_with_inline_editor(current_code)

    def _edit_with_inline_editor(self, current_code: str) -> tuple[str, bool]:
        """Simple inline editor for quick edits."""
        console.print(
            "\n🔥 [bold]Inline Editor[/bold] - Enter your code (empty line to finish):",
        )
        console.print("[dim]Current code:[/dim]")
        console.print(f"[cyan]{current_code}[/cyan]")
        console.print("\n[dim]Enter new code (or press Enter to keep current):[/dim]")

        new_code = Prompt.ask("Code", default=current_code)

        # Validate syntax
        had_errors = False
        try:
            ast.parse(new_code)
            console.print("✅ [green]Syntax valid![/green]")
        except SyntaxError as e:
            console.print(f"⚠️ [yellow]Syntax warning: {e}[/yellow]")
            if not Confirm.ask("Continue with syntax error?"):
                return current_code, True
            had_errors = True

        return new_code, had_errors

    def _edit_with_external_editor(self, current_code: str) -> tuple[str, bool]:
        """Edit code with external editor (vim, nano, etc.)."""
        editor = os.environ.get("EDITOR", "nano")
        # Validate editor to prevent shell injection
        allowed_editors = {"nano", "vim", "vi", "emacs", "code", "subl"}
        editor_name = Path(editor).name
        if editor_name not in allowed_editors:
            console.print(f"❌ [red]Unsupported editor: {editor_name}[/red]")
            return current_code, True

        # Create temporary file
        with tempfile.NamedTemporaryFile(encoding="utf-8", mode="w", suffix=".py", delete=False) as f:
            f.write(current_code)
            temp_path = f.name

        try:
            # Open editor
            console.print(f"🔥 Opening {editor}...")
            # S603: editor is validated against allowed list
            result = subprocess.run([editor, temp_path], check=False)

            if result.returncode != 0:
                console.print(
                    f"❌ [red]Editor exited with error code {result.returncode}[/red]",
                )
                return current_code, True

            # Read edited content
            with Path(temp_path).open(encoding="utf-8") as f:
                new_code = f.read().strip()

            # Validate syntax
            had_errors = False
            try:
                ast.parse(new_code)
                console.print("✅ [green]Syntax valid![/green]")
            except SyntaxError as e:
                console.print(f"⚠️ [yellow]Syntax error: {e}[/yellow]")
                if not Confirm.ask("Continue with syntax error?"):
                    return current_code, True
                had_errors = True

            return new_code, had_errors

        finally:
            # Cleanup
            Path(temp_path).unlink()

    def save_edit_sessions(self, output_path: Path) -> None:
        """Save all edit sessions for machine learning analysis."""
        sessions_data = [
            {
                "original_code": session.original_code,
                "ai_suggestion": session.ai_suggestion,
                "user_final_code": session.user_final_code,
                "edit_steps": session.edit_steps,
                "pattern_name": session.pattern_name,
                "file_path": session.file_path,
                "line_number": session.line_number,
                "accepted": session.accepted,
                "edit_duration_seconds": session.edit_duration_seconds,
                "syntax_errors_encountered": session.syntax_errors_encountered,
            }
            for session in self.edit_sessions
        ]

        output_path.write_text(json.dumps(sessions_data, indent=2), encoding="utf-8")

        log.info(
            "edit-sessions-saved",
            _replace_msg="💾 Saved {count} edit sessions to {path}",
            count=len(sessions_data),
            path=str(output_path),
        )

    def get_learning_insights(self) -> dict:
        """Analyze edit sessions to extract learning insights."""
        if not self.edit_sessions:
            return {}

        total_sessions = len(self.edit_sessions)
        accepted_sessions = sum(1 for s in self.edit_sessions if s.accepted)

        # Pattern analysis
        pattern_stats = {}
        for session in self.edit_sessions:
            pattern = session.pattern_name
            if pattern not in pattern_stats:
                pattern_stats[pattern] = {
                    "total": 0,
                    "accepted": 0,
                    "avg_edits": 0.0,
                    "avg_duration": 0.0,
                }

            pattern_stats[pattern]["total"] += 1
            if session.accepted:
                pattern_stats[pattern]["accepted"] += 1
            pattern_stats[pattern]["avg_edits"] += len(session.edit_steps)
            pattern_stats[pattern]["avg_duration"] += session.edit_duration_seconds

        # Calculate averages
        for stats in pattern_stats.values():
            if stats["total"] > 0:
                stats["avg_edits"] = float(stats["avg_edits"]) / float(stats["total"])
                stats["avg_duration"] = float(stats["avg_duration"]) / float(
                    stats["total"],
                )
                stats["acceptance_rate"] = float(stats["accepted"]) / float(
                    stats["total"],
                )

        insights = {
            "total_sessions": total_sessions,
            "acceptance_rate": accepted_sessions / total_sessions,
            "avg_edit_duration": sum(s.edit_duration_seconds for s in self.edit_sessions) / total_sessions,
            "avg_edits_per_session": sum(len(s.edit_steps) for s in self.edit_sessions) / total_sessions,
            "pattern_statistics": pattern_stats,
            "common_edit_patterns": self._extract_common_edit_patterns(),
        }

        log.info(
            "learning-insights-generated",
            _replace_msg="🧠 Generated learning insights from {sessions} sessions",
            sessions=total_sessions,
            acceptance_rate=insights["acceptance_rate"],
            avg_duration=insights["avg_edit_duration"],
        )

        return insights

    def _extract_common_edit_patterns(self) -> list[str]:
        """Extract common patterns from user edits."""
        all_edits = []
        for session in self.edit_sessions:
            all_edits.extend(session.edit_steps)

        # Simple pattern extraction (could be much more sophisticated)
        patterns = []

        # Look for common transformations
        if any("log.info" in edit for edit in all_edits):
            patterns.append("Users prefer log.info over other logging methods")

        if any("_replace_msg" in edit for edit in all_edits):
            patterns.append("Users often add _replace_msg parameter")

        if any('f"' in edit for edit in all_edits):
            patterns.append("Users prefer f-strings for formatting")

        return patterns


# Convenience functions
def create_live_editor(*, use_external_editor: bool = False) -> LiveCodeEditor:
    """Create a new Live Code Editor instance."""
    return LiveCodeEditor(use_external_editor=use_external_editor)


def edit_code_live(
    original_code: str,
    suggested_code: str,
    pattern_name: str,
    file_path: str,
    line_number: int,
) -> tuple[str, bool, EditSession]:
    """Quick live editing of a code transformation."""
    editor = create_live_editor()
    return editor.edit_transformation(
        original_code,
        suggested_code,
        pattern_name,
        file_path,
        line_number,
    )
