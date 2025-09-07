"""Assistant tools to migrate print/logging statements to structlog.

This is a minimal, safe transformer that:
- ensures each module imports structlog and has a top-level `log = structlog.get_logger()`
- rewrites `print(...)` calls to `log.info("print-output", items=[...])`

It intentionally avoids complex logging-module rewrites for safety.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
import difflib
from pathlib import Path
import re
import unicodedata


@dataclass
class MigrationResult:
    files_processed: int = 0
    files_transformed: int = 0
    diffs: dict[str, list[str]] = field(
        default_factory=dict,
    )  # path -> unified diff lines


class PrintToStructlogTransformer(ast.NodeTransformer):
    SIMPLE_EVENT_RE = re.compile(r"^[a-z0-9]+(?:[-_][a-z0-9]+)*$")

    @staticmethod
    def slugify(text: str) -> str:
        # Normalize unicode, lower-case, keep alnum, convert spaces and punctuation to '-'
        text = (
            unicodedata.normalize("NFKD", text)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
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
            # else drop
        slug = "".join(out).strip("-")
        slug = re.sub(r"-+", "-", slug)
        if not slug:
            slug = "event"
        return slug

    @staticmethod
    def derive_event_from_literal(arg: ast.AST) -> str | None:
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            candidate = PrintToStructlogTransformer.slugify(arg.value)
            return candidate
        return None

    @staticmethod
    def is_simple_event(s: str) -> bool:
        return bool(PrintToStructlogTransformer.SIMPLE_EVENT_RE.match(s))

    def __init__(self) -> None:
        super().__init__()
        self.import_structlog_present = False
        self.logger_assignment_present = False
        self.changed = False

    def visit_Import(self, node: ast.Import) -> ast.AST:
        for alias in node.names:
            if alias.name == "structlog":
                self.import_structlog_present = True
                break
        return node

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.AST:
        # Nothing to do; but keep traversal
        return node

    def visit_Assign(self, node: ast.Assign) -> ast.AST:
        # Detect pattern: log = structlog.get_logger(...)
        try:
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
        except Exception:
            pass
        return node

    def visit_call_build_print(self, node: ast.Call) -> ast.AST:
        self.changed = True
        new_func = ast.Attribute(
            value=ast.Name(id="log", ctx=ast.Load()),
            attr="info",
            ctx=ast.Load(),
        )

        # Determine event id
        event_arg: str | None = None
        if node.args:
            event_arg = self.derive_event_from_literal(node.args[0])
        event = (
            event_arg
            if (event_arg and self.is_simple_event(event_arg))
            else "print-output"
        )

        keywords: list[ast.keyword] = []

        # Build _replace_msg and remaining args mapping
        lit_first = (
            bool(node.args)
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        )
        if lit_first:
            original = node.args[0].value  # type: ignore[attr-defined]
            remaining_args = node.args[1:]
            placeholders = [f"{{a{i}}}" for i in range(len(remaining_args))]
            msg = original + ((" " + " ".join(placeholders)) if placeholders else "")
            keywords.append(
                ast.keyword(arg="_replace_msg", value=ast.Constant(value=msg)),
            )
        else:
            remaining_args = node.args
            if remaining_args:
                placeholders = [f"{{a{i}}}" for i in range(len(remaining_args))]
                msg = " ".join(placeholders)
                keywords.append(
                    ast.keyword(arg="_replace_msg", value=ast.Constant(value=msg)),
                )

        # Map positional args a0, a1, ...
        for idx, a in enumerate(remaining_args):
            keywords.append(ast.keyword(arg=f"a{idx}", value=a))

        # Preserve print kwargs under namespaced keys
        for kw in node.keywords or []:
            if kw.arg is None:
                keywords.append(ast.keyword(arg="print_kwargs", value=kw.value))
            else:
                keywords.append(ast.keyword(arg=f"print_{kw.arg}", value=kw.value))

        new_call = ast.Call(
            func=new_func,
            args=[ast.Constant(value=event)],
            keywords=keywords,
        )
        return ast.copy_location(new_call, node)

    def visit_Call(self, node: ast.Call) -> ast.AST:
        # Transform print(...) -> log.info(<event>, _replace_msg="... {a0} {a1}", a0=..., a1=...)
        if isinstance(node.func, ast.Name) and node.func.id == "print":
            return self.visit_call_build_print(node)
        return self.generic_visit(node)

    def ensure_imports_and_logger(self, tree: ast.Module) -> ast.Module:
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
            tree.body = prelude + tree.body
            self.changed = True
        return tree


def migrate_file(content: str) -> tuple[str, bool]:
    tree = ast.parse(content)
    transformer = PrintToStructlogTransformer()
    tree = transformer.visit(tree)
    ast.fix_missing_locations(tree)
    tree = transformer.ensure_imports_and_logger(tree)
    ast.fix_missing_locations(tree)
    try:
        new_code = ast.unparse(tree)
    except Exception:
        # Fallback to original content if unparse fails
        return content, False
    return new_code, transformer.changed


def migrate_directory(
    input_dir: Path,
    output_dir: Path | None,
    dry_run: bool = True,
) -> MigrationResult:
    """Migrate Python files under input_dir. Writes to output_dir if provided, else in-place."""
    result = MigrationResult()
    input_dir = Path(input_dir)
    if output_dir:
        output_dir = Path(output_dir)

    if not input_dir.exists() or not input_dir.is_dir():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    for py in input_dir.rglob("*.py"):
        # Skip generated or virtual env paths
        if any(part in {".venv", "venv", "__pycache__", ".git"} for part in py.parts):
            continue
        try:
            original = py.read_text(encoding="utf-8")
        except Exception:
            continue
        new_code, changed = migrate_file(original)
        result.files_processed += 1
        if not changed:
            # No transformation; in dry-run collect no diff. When writing to separate dir, still mirror original.
            if output_dir is not None and not dry_run:
                target_path = output_dir / py.relative_to(input_dir)
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_text(original, encoding="utf-8")
            continue

        # If changed, record diff
        if changed:
            diff_lines = list(
                difflib.unified_diff(
                    original.splitlines(keepends=True),
                    new_code.splitlines(keepends=True),
                    fromfile=str(py),
                    tofile=str(py),
                ),
            )
            result.diffs[str(py)] = diff_lines

        # Write transformed code only if not dry-run
        if not dry_run:
            target_path = (
                py if output_dir is None else (output_dir / py.relative_to(input_dir))
            )
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(new_code, encoding="utf-8")
            result.files_transformed += 1

    return result
