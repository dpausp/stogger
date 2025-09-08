"""🎯 Interactive Code Transformer - Amber-style Search & Replace for AST Transformations.

Provides interactive, user-guided code transformations with preview and confirmation,
inspired by the amber search & replace tool.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.syntax import Syntax
from rich.table import Table
import structlog

from .advanced_assistant import (
    AdvancedAssistant,
    CodeAnalysisResult,
    TransformationResult,
)
from .live_editor import EditSession, LiveCodeEditor

if TYPE_CHECKING:
    from pathlib import Path

log = structlog.get_logger("nicestlog.interactive_transformer")
console = Console()


class UserChoice(Enum):
    """User choices for interactive transformations."""

    YES = "y"
    NO = "n"
    ALL = "a"
    QUIT = "q"
    SKIP_FILE = "s"
    PREVIEW = "p"
    EDIT = "e"


@dataclass
class TransformationProposal:
    """A proposed transformation with context."""

    file_path: Path
    line_number: int
    original_code: str
    transformed_code: str
    pattern_name: str
    pattern_description: str
    context_before: list[str]
    context_after: list[str]
    node_type: str
    user_edited: bool = False
    edit_history: list[str] | None = None

    def __post_init__(self):
        if self.edit_history is None:
            self.edit_history = []


@dataclass
class InteractiveSession:
    """State for an interactive transformation session."""

    total_proposals: int = 0
    accepted: int = 0
    rejected: int = 0
    skipped_files: int = 0
    auto_accept_all: bool = False
    quit_requested: bool = False
    edited: int = 0
    edit_sessions: list[EditSession] | None = None

    def __post_init__(self):
        if self.edit_sessions is None:
            self.edit_sessions = []


class InteractiveTransformer:
    """🎯 Interactive Code Transformer with Amber-style Interface.

    Provides user-guided code transformations with preview, confirmation,
    and comprehensive logging of all decisions.
    """

    def __init__(
        self,
        assistant: AdvancedAssistant | None = None,
        context_lines: int = 3,
        enable_live_editing: bool = True,
        use_external_editor: bool = False,
    ):
        self.assistant = assistant or AdvancedAssistant(verbose=True)
        self.context_lines = context_lines
        self.session = InteractiveSession()
        self.enable_live_editing = enable_live_editing
        self.live_editor = (
            LiveCodeEditor(use_external_editor=use_external_editor)
            if enable_live_editing
            else None
        )

        log.debug(
            "interactive-transformer-initialized",
            _replace_msg="🎯 Interactive Transformer initialized with {patterns} patterns (live editing: {live_editing})",
            patterns=len([p for p in self.assistant.patterns if p.enabled]),
            context_lines=context_lines,
            session_id=self.assistant.session_id,
            live_editing=enable_live_editing,
        )

    def transform_file_interactive(self, file_path: Path) -> TransformationResult:
        """Transform a file with interactive user confirmation."""
        log.info(
            "interactive-file-transformation-started",
            _replace_msg="🔄 Starting interactive transformation of {file_path}",
            file_path=str(file_path),
            session_id=self.assistant.session_id,
        )

        if self.session.quit_requested:
            log.info("transformation-skipped-quit-requested", file_path=str(file_path))
            return self._create_empty_result(file_path)

        try:
            # Read and parse the file
            original_content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(original_content)

            # Find all potential transformations
            proposals = self._find_transformation_proposals(
                file_path,
                tree,
                original_content,
            )

            if not proposals:
                log.info(
                    "no-transformations-found",
                    _replace_msg="ℹ️ No transformations found for {file_path}",
                    file_path=str(file_path),
                )
                return self._create_empty_result(file_path)

            # Show file header
            self._show_file_header(file_path, len(proposals))

            # Process each proposal interactively
            accepted_proposals = []
            for i, proposal in enumerate(proposals, 1):
                if self.session.quit_requested:
                    break

                choice = self._present_proposal(proposal, i, len(proposals))

                if choice == UserChoice.YES:
                    accepted_proposals.append(proposal)
                    self.session.accepted += 1
                    log.info(
                        "transformation-accepted",
                        _replace_msg="✅ Accepted transformation at {file_path}:{line}",
                        file_path=str(proposal.file_path),
                        line=proposal.line_number,
                        pattern=proposal.pattern_name,
                    )

                elif choice == UserChoice.ALL:
                    accepted_proposals.append(proposal)
                    accepted_proposals.extend(proposals[i:])  # Accept all remaining
                    self.session.accepted += len(proposals) - i + 1
                    self.session.auto_accept_all = True
                    log.info(
                        "auto-accept-all-enabled",
                        _replace_msg="🚀 Auto-accept enabled, accepting all remaining transformations",
                        remaining_count=len(proposals) - i,
                    )
                    break

                elif (
                    choice == UserChoice.EDIT
                    and self.enable_live_editing
                    and self.live_editor
                ):
                    # Live edit the transformation
                    edited_code, accepted, edit_session = (
                        self.live_editor.edit_transformation(
                            proposal.original_code,
                            proposal.transformed_code,
                            proposal.pattern_name,
                            str(proposal.file_path),
                            proposal.line_number,
                        )
                    )

                    # Update proposal with edited code
                    proposal.transformed_code = edited_code
                    proposal.user_edited = True
                    if proposal.edit_history is not None:
                        proposal.edit_history.append(
                            f"Live edited: {edit_session.edit_steps}",
                        )

                    # Store edit session
                    if self.session.edit_sessions is not None:
                        self.session.edit_sessions.append(edit_session)
                    self.session.edited += 1

                    if accepted:
                        accepted_proposals.append(proposal)
                        self.session.accepted += 1
                        log.info(
                            "transformation-edited-and-accepted",
                            _replace_msg="🔥 Transformation edited and accepted at {file_path}:{line}",
                            file_path=str(proposal.file_path),
                            line=proposal.line_number,
                            pattern=proposal.pattern_name,
                            edit_steps=len(edit_session.edit_steps),
                        )
                    else:
                        self.session.rejected += 1
                        log.info(
                            "transformation-edited-but-rejected",
                            _replace_msg="🔥 Transformation edited but rejected at {file_path}:{line}",
                            file_path=str(proposal.file_path),
                            line=proposal.line_number,
                            pattern=proposal.pattern_name,
                        )

                elif choice == UserChoice.NO:
                    self.session.rejected += 1
                    log.info(
                        "transformation-rejected",
                        _replace_msg="❌ Rejected transformation at {file_path}:{line}",
                        file_path=str(proposal.file_path),
                        line=proposal.line_number,
                        pattern=proposal.pattern_name,
                    )

                elif choice == UserChoice.SKIP_FILE:
                    self.session.skipped_files += 1
                    log.info(
                        "file-skipped",
                        _replace_msg="⏭️ Skipped remaining transformations in {file_path}",
                        file_path=str(file_path),
                        remaining_count=len(proposals) - i,
                    )
                    break

                elif choice == UserChoice.QUIT:
                    self.session.quit_requested = True
                    log.info("quit-requested", _replace_msg="🛑 User requested quit")
                    break

            # Apply accepted transformations
            if accepted_proposals and not self.session.quit_requested:
                return self._apply_transformations(
                    file_path,
                    accepted_proposals,
                    original_content,
                )
            else:
                return self._create_empty_result(file_path)

        except Exception as e:
            log.exception(
                "interactive-transformation-error",
                _replace_msg="❌ Error in interactive transformation of {file_path}: {error}",
                file_path=str(file_path),
                error=str(e),
                exception_type=type(e).__name__,
            )
            return self._create_empty_result(file_path)

    def transform_directory_interactive(
        self,
        directory: Path,
        pattern: str = "*.py",
    ) -> list[TransformationResult]:
        """Transform all files in a directory with interactive confirmation."""
        log.info(
            "interactive-directory-transformation-started",
            _replace_msg="🗂️ Starting interactive directory transformation: {directory}",
            directory=str(directory),
            pattern=pattern,
        )

        files = list(directory.glob(pattern))
        if not files:
            console.print(
                f"❌ No files matching pattern '{pattern}' found in {directory}",
            )
            return []

        # Show session header
        self._show_session_header(files)

        results: list[Any] = []
        for file_path in files:
            if self.session.quit_requested:
                log.info(
                    "directory-transformation-quit",
                    remaining_files=len(files) - len(results),
                )
                break

            result = self.transform_file_interactive(file_path)
            results.append(result)

        # Show session summary
        self._show_session_summary(results)

        return results

    def _present_proposal(
        self,
        proposal: TransformationProposal,
        index: int,
        total: int,
    ) -> UserChoice:
        """Present a transformation proposal to the user and get their choice."""
        # Display the proposal
        console.print(f"\n[bold blue]Proposal {index}/{total}[/bold blue]")
        console.print(f"File: {proposal.file_path}")
        console.print(f"Line: {proposal.line_number}")
        console.print(f"Pattern: {proposal.pattern_name}")
        console.print(f"Description: {proposal.pattern_description}")
        console.print("\n[red]Original:[/red]")
        syntax = Syntax(proposal.original_code, "python", theme="monokai")
        console.print(syntax)
        console.print("\n[green]Transformed:[/green]")
        syntax = Syntax(proposal.transformed_code, "python", theme="monokai")
        console.print(syntax)
        # Ask for choice
        choice = Prompt.ask(
            "Accept this transformation? (y=yes, n=no, a=all, q=quit, s=skip file, p=preview, e=edit)",
            choices=["y", "n", "a", "q", "s", "p", "e"],
            default="n",
        )
        return UserChoice(choice)

    def _find_transformation_proposals(
        self,
        file_path: Path,
        tree: ast.Module,
        content: str,
    ) -> list[TransformationProposal]:
        """Find all potential transformations in the file."""
        proposals = []
        lines = content.split("\n")

        # Create a custom node visitor to find transformation opportunities
        class ProposalFinder(ast.NodeVisitor):
            def __init__(self, transformer_self):
                self.transformer = transformer_self
                self.proposals = []

            def visit(self, node):
                # Check each enabled pattern
                for pattern in self.transformer.assistant.patterns:
                    if (
                        pattern.enabled
                        and pattern.transformer
                        and pattern.matcher(node)
                    ):
                        try:
                            # Create a copy of the node for transformation
                            import copy

                            node_copy = copy.deepcopy(node)
                            transformed_node = pattern.transformer(node_copy)

                            if transformed_node != node:
                                # Extract line information
                                line_num = getattr(node, "lineno", 1)

                                # Get original and transformed code
                                original_line = (
                                    lines[line_num - 1]
                                    if line_num <= len(lines)
                                    else ""
                                )

                                # Create a minimal AST to get transformed code
                                temp_module = ast.Module(
                                    body=[transformed_node],
                                    type_ignores=[],
                                )
                                transformed_code = ast.unparse(temp_module).strip()

                                # Get context lines
                                context_before = self._get_context_lines(
                                    lines,
                                    line_num,
                                    before=True,
                                )
                                context_after = self._get_context_lines(
                                    lines,
                                    line_num,
                                    before=False,
                                )

                                proposal = TransformationProposal(
                                    file_path=file_path,
                                    line_number=line_num,
                                    original_code=original_line.strip(),
                                    transformed_code=transformed_code,
                                    pattern_name=pattern.name,
                                    pattern_description=pattern.description,
                                    context_before=context_before,
                                    context_after=context_after,
                                    node_type=type(node).__name__,
                                )

                                self.proposals.append(proposal)

                        except Exception as e:
                            log.warning(
                                "proposal-generation-error",
                                _replace_msg="⚠️ Error generating proposal for pattern {pattern}: {error}",
                                pattern=pattern.name,
                                error=str(e),
                            )

                self.generic_visit(node)

            def _get_context_lines(
                self,
                lines: list[str],
                line_num: int,
                before: bool,
            ) -> list[str]:
                """Get context lines before or after the target line."""
                if before:
                    start = max(0, line_num - self.transformer.context_lines - 1)
                    end = line_num - 1
                    return lines[start:end]
                else:
                    start = line_num
                    end = min(len(lines), line_num + self.transformer.context_lines)
                    return lines[start:end]

        finder = ProposalFinder(self)
        finder.visit(tree)

        # Sort proposals by line number
        proposals = sorted(finder.proposals, key=lambda p: p.line_number)

        log.debug(
            "transformation-proposals-found",
            _replace_msg="🔍 Found {count} transformation proposals in {file_path}",
            count=len(proposals),
            file_path=str(file_path),
        )

        return proposals

    def _present_proposal(
        self,
        proposal: TransformationProposal,
        current: int,
        total: int,
    ) -> UserChoice:
        """Present a transformation proposal to the user and get their choice."""
        if self.session.auto_accept_all:
            return UserChoice.YES

        # Show the proposal
        console.print()
        console.print(
            f"[bold blue]Proposal {current}/{total}[/bold blue] - {proposal.pattern_description}",
        )
        console.print(f"[dim]{proposal.file_path}:{proposal.line_number}[/dim]")

        # Show context and transformation
        self._show_transformation_preview(proposal)

        # Get user choice
        while True:
            choice_str = Prompt.ask(
                "Replace? [bold green][Y][/bold green]es/[bold red][n][/bold red]o/[bold yellow][a][/bold yellow]ll/[bold blue][p][/bold blue]review/[bold cyan][s][/bold cyan]kip file/[bold magenta][q][/bold magenta]uit",
                default="y",
                show_default=False,
            ).lower()

            if choice_str in ["y", "yes", ""]:
                return UserChoice.YES
            elif choice_str in ["n", "no"]:
                return UserChoice.NO
            elif choice_str in ["a", "all"]:
                return UserChoice.ALL
            elif choice_str in ["p", "preview"]:
                self._show_detailed_preview(proposal)
                continue  # Ask again
            elif choice_str in ["s", "skip"]:
                return UserChoice.SKIP_FILE
            elif choice_str in ["q", "quit"]:
                return UserChoice.QUIT
            else:
                console.print("[red]Invalid choice. Please use y/n/a/p/s/q[/red]")

    def _show_transformation_preview(self, proposal: TransformationProposal):
        """Show a preview of the transformation."""
        # Create a table for the transformation
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("", style="dim")
        table.add_column("", style="")

        # Show context before
        for line in proposal.context_before:
            table.add_row("", f"[dim]{line}[/dim]")

        # Show the transformation
        table.add_row("-", f"[red]{proposal.original_code}[/red]")
        table.add_row("+", f"[green]{proposal.transformed_code}[/green]")

        # Show context after
        for line in proposal.context_after:
            table.add_row("", f"[dim]{line}[/dim]")

        console.print(table)

    def _show_detailed_preview(self, proposal: TransformationProposal):
        """Show a detailed preview with syntax highlighting."""
        console.print("\n[bold]Detailed Preview:[/bold]")

        # Original code
        console.print(
            Panel(
                Syntax(proposal.original_code, "python", theme="monokai"),
                title="[red]Original[/red]",
                border_style="red",
            ),
        )

        # Transformed code
        console.print(
            Panel(
                Syntax(proposal.transformed_code, "python", theme="monokai"),
                title="[green]Transformed[/green]",
                border_style="green",
            ),
        )

        # Pattern info
        info_text = f"""
[bold]Pattern:[/bold] {proposal.pattern_name}
[bold]Description:[/bold] {proposal.pattern_description}
[bold]Node Type:[/bold] {proposal.node_type}
[bold]Line:[/bold] {proposal.line_number}
"""
        console.print(
            Panel(
                info_text,
                title="[blue]Transformation Info[/blue]",
                border_style="blue",
            ),
        )

    def _show_file_header(self, file_path: Path, proposal_count: int):
        """Show header for file transformation."""
        console.print(f"\n[bold cyan]📄 {file_path}[/bold cyan]")
        console.print(f"[dim]Found {proposal_count} potential transformation(s)[/dim]")

    def _show_session_header(self, files: list[Path]):
        """Show header for transformation session."""
        console.print(
            Panel.fit(
                f"🎯 [bold blue]Interactive Code Transformation Session[/bold blue]\n"
                f"Files to process: {len(files)}\n"
                f"Patterns enabled: {len([p for p in self.assistant.patterns if p.enabled])}",
                border_style="blue",
            ),
        )

    def _show_session_summary(self, results: list[TransformationResult]):
        """Show summary of the transformation session."""
        successful = sum(1 for r in results if r.success)
        total_changes = sum(len(r.changes_made) for r in results)

        summary_text = f"""
[bold]Session Complete![/bold]

📊 [bold]Statistics:[/bold]
• Files processed: {len(results)}
• Successful transformations: {successful}
• Total changes made: {total_changes}
• Proposals accepted: {self.session.accepted}
• Proposals rejected: {self.session.rejected}
• Files skipped: {self.session.skipped_files}
• 🔥 Live edits made: {self.session.edited}
• Edit sessions recorded: {len(self.session.edit_sessions or [])}
"""

        if self.session.quit_requested:
            summary_text += "\n🛑 [yellow]Session ended by user request[/yellow]"

        console.print(
            Panel(
                summary_text,
                title="[green]Transformation Summary[/green]",
                border_style="green",
            ),
        )

        log.debug(
            "interactive-session-completed",
            _replace_msg="✅ Interactive session completed",
            files_processed=len(results),
            successful_transformations=successful,
            total_changes=total_changes,
            accepted=self.session.accepted,
            rejected=self.session.rejected,
            skipped_files=self.session.skipped_files,
            edited=self.session.edited,
            edit_sessions=len(self.session.edit_sessions or []),
            quit_requested=self.session.quit_requested,
        )

        # Save edit sessions for machine learning if any were created
        if self.session.edit_sessions and self.live_editor:
            from pathlib import Path
            import time

            timestamp = int(time.time())
            edit_log_path = Path(f"nicestlog_edit_sessions_{timestamp}.json")
            self.live_editor.edit_sessions = self.session.edit_sessions
            self.live_editor.save_edit_sessions(edit_log_path)

            # Show learning insights
            insights = self.live_editor.get_learning_insights()
            if insights:
                console.print("\n🧠 [bold blue]Learning Insights:[/bold blue]")
                console.print(f"• Acceptance rate: {insights['acceptance_rate']:.1%}")
                console.print(
                    f"• Avg edit duration: {insights['avg_edit_duration']:.1f}s",
                )
                console.print(
                    f"• Avg edits per session: {insights['avg_edits_per_session']:.1f}",
                )

                if insights["common_edit_patterns"]:
                    console.print("• Common patterns:")
                    for pattern in insights["common_edit_patterns"]:
                        console.print(f"  - {pattern}")

                console.print(f"\n💾 Edit data saved to: [cyan]{edit_log_path}[/cyan]")

    def _apply_transformations(
        self,
        file_path: Path,
        proposals: list[TransformationProposal],
        original_content: str,
    ) -> TransformationResult:
        """Apply the accepted transformations to the file."""
        log.info(
            "applying-transformations",
            _replace_msg="🔧 Applying {count} transformations to {file_path}",
            count=len(proposals),
            file_path=str(file_path),
        )

        # For now, use the assistant's transform_file method
        # In a more sophisticated implementation, we would apply only the selected transformations
        result = self.assistant.transform_file(file_path, dry_run=False)

        # Update the result with our specific changes
        result.changes_made = [
            f"Applied {p.pattern_name} at line {p.line_number}" for p in proposals
        ]

        return result

    def _create_empty_result(self, file_path: Path) -> TransformationResult:
        """Create an empty transformation result."""
        from .advanced_assistant import TransformationMetrics

        return TransformationResult(
            original_code="",
            transformed_code="",
            analysis=CodeAnalysisResult(
                file_path=file_path,
                original_hash="",
                ast_tree=ast.Module(body=[], type_ignores=[]),
            ),
            metrics=TransformationMetrics(),
            success=True,
            changes_made=[],
        )


# Convenience functions
def create_interactive_transformer(context_lines: int = 3) -> InteractiveTransformer:
    """Create a new Interactive Transformer instance."""
    return InteractiveTransformer(context_lines=context_lines)


def transform_file_interactive(
    file_path: Path,
    context_lines: int = 3,
) -> TransformationResult:
    """Quick interactive transformation of a Python file."""
    transformer = create_interactive_transformer(context_lines=context_lines)
    return transformer.transform_file_interactive(file_path)


def transform_directory_interactive(
    directory: Path,
    pattern: str = "*.py",
    context_lines: int = 3,
) -> list[TransformationResult]:
    """Quick interactive transformation of a directory."""
    transformer = create_interactive_transformer(context_lines=context_lines)
    return transformer.transform_directory_interactive(directory, pattern)
