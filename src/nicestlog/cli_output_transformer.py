"""CLI Output to Structlog Transformer.

This module provides AST transformation capabilities to convert CLI framework
output functions (typer.echo, click.echo, rich.print, etc.) to structured
logging with nicestlog, while preserving styling and formatting information.
"""



import ast
from contextlib import suppress
from dataclasses import dataclass
import re
from typing import Any
import unicodedata


@dataclass
class CLIOutputCall:
    """Represents a detected CLI output function call."""

    framework: str  # 'typer', 'click', 'rich', 'argparse', 'sys'
    function: str  # 'echo', 'print', 'error', 'write'
    line_number: int
    original_call: ast.Call
    message_arg: ast.AST | None = None
    style_info: dict[str, Any] | None = None
    output_stream: str = "stdout"  # 'stdout', 'stderr'


class CLIOutputToStructlogTransformer(ast.NodeTransformer):
    """Transform CLI framework output calls to structlog calls."""

    SIMPLE_EVENT_RE = re.compile(r"^[a-z0-9]+(?:[-_][a-z0-9]+)*$")

    def __init__(self) -> None:
        super().__init__()
        self.import_structlog_present = False
        self.logger_assignment_present = False
        self.changed = False
        self.detected_calls: list[CLIOutputCall] = []

        # Track imports to understand available functions
        self.imports = {
            "typer": False,
            "click": False,
            "rich": False,
            "argparse": False,
            "sys": False,
        }

        # Track rich console instances
        self.rich_console_vars: set[str] = set()

    @staticmethod
    def slugify(text: str) -> str:
        """Convert text to a valid event identifier."""
        text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
        text = text.lower()
        out = []
        prev_sep = False
        for ch in text:
            if ch.isalnum():
                out.append(ch)
                prev_sep = False
            elif ch in "-_ /.:,;|()[]{}+*#'\"!?@%$^&`~":
                if not prev_sep:
                    out.append("-")
                    prev_sep = True
        slug = "".join(out).strip("-")
        slug = re.sub(r"-+", "-", slug)
        if not slug:
            slug = "cli-output"
        return slug

    @staticmethod
    def derive_event_from_literal(arg: ast.AST) -> str | None:
        """Extract event name from string literal."""
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            candidate = CLIOutputToStructlogTransformer.slugify(arg.value)
            return candidate
        return None

    @staticmethod
    def is_simple_event(s: str) -> bool:
        """Check if string is a valid simple event name."""
        return bool(CLIOutputToStructlogTransformer.SIMPLE_EVENT_RE.match(s))

    def visit_Import(self, node: ast.Import) -> ast.AST:
        """Track imports of CLI frameworks."""
        for alias in node.names:
            if alias.name == "structlog":
                self.import_structlog_present = True
            elif alias.name in self.imports:
                self.imports[alias.name] = True
        return node

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.AST:
        """Track from imports of CLI frameworks."""
        if (node.module == "rich" and any(alias.name == "print" for alias in node.names)) or (
            node.module == "rich.console" and any(alias.name == "Console" for alias in node.names)
        ):
            self.imports["rich"] = True
        return node

    def visit_Assign(self, node: ast.Assign) -> ast.AST:
        """Track logger assignments and rich console instances."""
        # Detect pattern: log = structlog.get_logger(...)
        with suppress(Exception):
            if (
                len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "log"
                and isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Attribute)
                and isinstance(node.value.func.value, ast.Name)
                and node.value.func.value.id == "structlog"
                and node.value.func.attr == "get_logger"
            ):
                self.logger_assignment_present = True

        # Detect rich Console instances: console = Console()
        if (
            len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "Console"
        ):
            self.rich_console_vars.add(node.targets[0].id)

        return node

    def detect_cli_output_call(self, node: ast.Call) -> CLIOutputCall | None:
        """Detect and classify CLI output function calls."""
        # typer.echo()
        if (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "typer"
            and node.func.attr == "echo"
        ):
            return self._analyze_typer_echo(node)

        # click.echo()
        elif (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "click"
            and node.func.attr == "echo"
        ):
            return self._analyze_click_echo(node)

        # rich.print() or imported print from rich
        elif (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "rich"
            and node.func.attr == "print"
        ):
            return self._analyze_rich_print(node)

        # console.print() (Rich Console instance)
        elif (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id in self.rich_console_vars
            and node.func.attr == "print"
        ):
            return self._analyze_rich_console_print(node)

        # parser.error() (argparse)
        elif (
            isinstance(node.func, ast.Attribute) and node.func.attr == "error" and isinstance(node.func.value, ast.Name)
        ):
            return self._analyze_argparse_error(node)

        # sys.stdout.write() / sys.stderr.write()
        elif (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Attribute)
            and isinstance(node.func.value.value, ast.Name)
            and node.func.value.value.id == "sys"
            and node.func.value.attr in ["stdout", "stderr"]
            and node.func.attr == "write"
        ):
            return self._analyze_sys_write(node)

        return None

    def _analyze_typer_echo(self, node: ast.Call) -> CLIOutputCall:
        """Analyze typer.echo() call."""
        call_info = CLIOutputCall(
            framework="typer",
            function="echo",
            line_number=node.lineno,
            original_call=node,
            style_info={},
        )

        # Extract message (first positional arg)
        if node.args:
            call_info.message_arg = node.args[0]

        # Extract styling and options from keywords
        for kw in node.keywords or []:
            if kw.arg == "err" and isinstance(kw.value, ast.Constant) and kw.value.value:
                call_info.output_stream = "stderr"
            elif kw.arg == "fg":
                if call_info.style_info is None:
                    call_info.style_info = {}
                call_info.style_info["color"] = self._extract_color_value(kw.value)
            elif kw.arg == "bg":
                if call_info.style_info is None:
                    call_info.style_info = {}
                call_info.style_info["bg_color"] = self._extract_color_value(kw.value)
            elif kw.arg in ["bold", "italic", "underline", "dim"]:
                if isinstance(kw.value, ast.Constant) and kw.value.value:
                    if call_info.style_info is None:
                        call_info.style_info = {}
                    call_info.style_info[kw.arg] = True

        return call_info

    def _analyze_click_echo(self, node: ast.Call) -> CLIOutputCall:
        """Analyze click.echo() call."""
        call_info = CLIOutputCall(
            framework="click",
            function="echo",
            line_number=node.lineno,
            original_call=node,
            style_info={},
        )

        # Extract message (first positional arg)
        if node.args:
            call_info.message_arg = node.args[0]

        # Extract options from keywords
        for kw in node.keywords or []:
            if kw.arg == "err" and isinstance(kw.value, ast.Constant) and kw.value.value:
                call_info.output_stream = "stderr"

        return call_info

    def _analyze_rich_print(self, node: ast.Call) -> CLIOutputCall:
        """Analyze rich.print() call."""
        call_info = CLIOutputCall(
            framework="rich",
            function="print",
            line_number=node.lineno,
            original_call=node,
            style_info={},
        )

        # Extract message (first positional arg)
        if node.args:
            call_info.message_arg = node.args[0]

        # Extract styling from keywords
        for kw in node.keywords or []:
            if kw.arg == "style":
                if call_info.style_info is None:
                    call_info.style_info = {}
                call_info.style_info["style"] = self._extract_string_value(kw.value)

        return call_info

    def _analyze_rich_console_print(self, node: ast.Call) -> CLIOutputCall:
        """Analyze console.print() call (Rich Console instance)."""
        call_info = CLIOutputCall(
            framework="rich",
            function="console_print",
            line_number=node.lineno,
            original_call=node,
            style_info={},
        )

        # Extract message (first positional arg)
        if node.args:
            call_info.message_arg = node.args[0]

        # Extract styling and options from keywords
        for kw in node.keywords or []:
            if kw.arg == "stderr" and isinstance(kw.value, ast.Constant) and kw.value.value:
                call_info.output_stream = "stderr"
            elif kw.arg == "style":
                if call_info.style_info is None:
                    call_info.style_info = {}
                call_info.style_info["style"] = self._extract_string_value(kw.value)

        return call_info

    def _analyze_argparse_error(self, node: ast.Call) -> CLIOutputCall:
        """Analyze parser.error() call."""
        call_info = CLIOutputCall(
            framework="argparse",
            function="error",
            line_number=node.lineno,
            original_call=node,
            output_stream="stderr",
        )

        # Extract message (first positional arg)
        if node.args:
            call_info.message_arg = node.args[0]

        return call_info

    def _analyze_sys_write(self, node: ast.Call) -> CLIOutputCall:
        """Analyze sys.stdout.write() / sys.stderr.write() call."""
        stream = (
            "stderr"
            if hasattr(node.func, "value") and hasattr(node.func.value, "attr") and node.func.value.attr == "stderr"
            else "stdout"
        )

        call_info = CLIOutputCall(
            framework="sys",
            function="write",
            line_number=node.lineno,
            original_call=node,
            output_stream=stream,
        )

        # Extract message (first positional arg)
        if node.args:
            call_info.message_arg = node.args[0]

        return call_info

    def _extract_color_value(self, node: ast.AST) -> str | None:
        """Extract color value from AST node."""
        if isinstance(node, ast.Constant):
            return str(node.value)
        elif isinstance(node, ast.Attribute):
            # Handle typer.colors.RED, etc.
            if (
                isinstance(node.value, ast.Attribute)
                and isinstance(node.value.value, ast.Name)
                and node.value.value.id == "typer"
                and node.value.attr == "colors"
            ):
                return node.attr.lower()
        return None

    def _extract_string_value(self, node: ast.AST) -> str | None:
        """Extract string value from AST node."""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None

    def visit_Call(self, node: ast.Call) -> ast.AST:
        """Transform CLI output calls to structlog calls."""
        cli_call = self.detect_cli_output_call(node)

        if cli_call:
            self.detected_calls.append(cli_call)
            return self._transform_cli_call_to_structlog(cli_call)

        return self.generic_visit(node)

    def _transform_cli_call_to_structlog(self, cli_call: CLIOutputCall) -> ast.Call:
        """Transform a CLI output call to a structlog call."""
        self.changed = True

        # Create log.info() call
        new_func = ast.Attribute(
            value=ast.Name(id="log", ctx=ast.Load()),
            attr=self._determine_log_level(cli_call),
            ctx=ast.Load(),
        )

        # Determine event name
        event_arg = None
        if cli_call.message_arg:
            event_arg = self.derive_event_from_literal(cli_call.message_arg)

        event = (
            event_arg
            if (event_arg and self.is_simple_event(event_arg))
            else f"cli-{cli_call.framework}-{cli_call.function}"
        )

        keywords: list[ast.keyword] = []

        # Build _replace_msg and remaining args mapping
        if cli_call.message_arg:
            if isinstance(cli_call.message_arg, ast.Constant) and isinstance(
                cli_call.message_arg.value,
                str,
            ):
                # Simple string message
                original = cli_call.message_arg.value
                keywords.append(
                    ast.keyword(arg="_replace_msg", value=ast.Constant(value=original)),
                )
            else:
                # Complex expression - preserve as a0
                keywords.append(
                    ast.keyword(arg="_replace_msg", value=ast.Constant(value="{a0}")),
                )
                if cli_call.message_arg is not None and isinstance(
                    cli_call.message_arg,
                    ast.expr,
                ):
                    keywords.append(ast.keyword(arg="a0", value=cli_call.message_arg))

        # Add CLI-specific metadata
        keywords.append(
            ast.keyword(
                arg="cli_framework",
                value=ast.Constant(value=cli_call.framework),
            ),
        )
        keywords.append(
            ast.keyword(
                arg="cli_function",
                value=ast.Constant(value=cli_call.function),
            ),
        )
        keywords.append(
            ast.keyword(
                arg="cli_output_stream",
                value=ast.Constant(value=cli_call.output_stream),
            ),
        )

        # Add styling information
        if cli_call.style_info:
            for style_key, style_value in cli_call.style_info.items():
                keywords.append(
                    ast.keyword(
                        arg=f"cli_{style_key}",
                        value=ast.Constant(value=style_value),
                    ),
                )

        # Preserve original call arguments as metadata (for complex cases)
        remaining_args = cli_call.original_call.args[1:] if len(cli_call.original_call.args) > 1 else []
        for idx, arg in enumerate(remaining_args):
            keywords.append(ast.keyword(arg=f"a{idx + 1}", value=arg))

        # Preserve original keyword arguments
        for kw in cli_call.original_call.keywords or []:
            if kw.arg is None:
                keywords.append(ast.keyword(arg="cli_kwargs", value=kw.value))
            else:
                keywords.append(ast.keyword(arg=f"cli_{kw.arg}", value=kw.value))

        new_call = ast.Call(
            func=new_func,
            args=[ast.Constant(value=event)],
            keywords=keywords,
        )

        return ast.copy_location(new_call, cli_call.original_call)

    def _determine_log_level(self, cli_call: CLIOutputCall) -> str:
        """Determine appropriate log level for CLI call."""
        if cli_call.output_stream == "stderr":
            return "error" if cli_call.function == "error" else "warning"
        elif cli_call.framework == "argparse" and cli_call.function == "error":
            return "error"
        else:
            return "info"

    def ensure_imports_and_logger(self, tree: ast.Module) -> ast.Module:
        """Ensure structlog import and logger assignment are present."""
        prelude: list[ast.stmt] = []

        if not self.import_structlog_present:
            prelude.append(ast.Import(names=[ast.alias(name="structlog", asname=None)]))

        if not self.logger_assignment_present:
            get_logger_call = ast.Call(
                func=ast.Attribute(
                    value=ast.Name(id="structlog", ctx=ast.Load()),
                    attr="get_logger",
                    ctx=ast.Load(),
                ),
                args=[],
                keywords=[],
            )
            prelude.append(
                ast.Assign(
                    targets=[ast.Name(id="log", ctx=ast.Store())],
                    value=get_logger_call,
                ),
            )

        if prelude:
            # Insert after any module docstring
            insert_pos = 0
            if (
                tree.body
                and isinstance(tree.body[0], ast.Expr)
                and isinstance(tree.body[0].value, ast.Constant)
                and isinstance(tree.body[0].value.value, str)
            ):
                insert_pos = 1

            tree.body = tree.body[:insert_pos] + prelude + tree.body[insert_pos:]
            self.changed = True

        return tree


def migrate_cli_outputs_file(content: str) -> tuple[str, bool]:
    """Migrate CLI output calls in a single file."""
    tree = ast.parse(content)
    transformer = CLIOutputToStructlogTransformer()
    tree = transformer.visit(tree)
    ast.fix_missing_locations(tree)
    tree = transformer.ensure_imports_and_logger(tree)
    ast.fix_missing_locations(tree)

    try:
        new_code = ast.unparse(tree)
    except (ValueError, TypeError):
        # Fallback to original content if unparse fails
        return content, False

    return new_code, transformer.changed


def analyze_cli_outputs_in_file(content: str) -> list[CLIOutputCall]:
    """Analyze CLI output calls in a file without transforming."""
    tree = ast.parse(content)
    transformer = CLIOutputToStructlogTransformer()
    transformer.visit(tree)  # Just visit to detect calls
    return transformer.detected_calls
