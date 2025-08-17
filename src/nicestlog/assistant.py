"""
Assistant tools to migrate print/logging statements to structlog.

This is a minimal, safe transformer that:
- ensures each module imports structlog and has a top-level `log = structlog.get_logger()`
- rewrites `print(...)` calls to `log.info("print-output", items=[...])`

It intentionally avoids complex logging-module rewrites for safety.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple
import ast


@dataclass
class MigrationResult:
    files_processed: int = 0
    files_transformed: int = 0


class PrintToStructlogTransformer(ast.NodeTransformer):
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

    def visit_Call(self, node: ast.Call) -> ast.AST:
        # Transform print(...) -> log.info("print-output", items=[<args as-is>], **kwargs)
        if isinstance(node.func, ast.Name) and node.func.id == "print":
            self.changed = True
            new_func = ast.Attribute(value=ast.Name(id="log", ctx=ast.Load()), attr="info", ctx=ast.Load())
            # Build items=[...] from positional args
            items_list = ast.List(elts=[ast.copy_location(a, a) for a in node.args], ctx=ast.Load())
            new_keywords = [ast.keyword(arg="items", value=items_list)]
            # preserve existing keyword args by nesting under kw_<name> to avoid collisions
            for kw in node.keywords or []:
                if kw.arg is None:
                    # print supports **kwargs; preserve as passthrough dictionary
                    new_keywords.append(ast.keyword(arg="print_kwargs", value=kw.value))
                else:
                    new_keywords.append(ast.keyword(arg=f"print_{kw.arg}", value=kw.value))
            new_call = ast.Call(func=new_func, args=[ast.Constant(value="print-output")], keywords=new_keywords)
            return ast.copy_location(new_call, node)
        return self.generic_visit(node)

    def ensure_imports_and_logger(self, tree: ast.Module) -> ast.Module:
        prelude: list[ast.stmt] = []
        if not self.import_structlog_present:
            prelude.append(ast.Import(names=[ast.alias(name="structlog", asname=None)]))
        if not self.logger_assignment_present:
            get_logger_call = ast.Call(
                func=ast.Attribute(value=ast.Name(id="structlog", ctx=ast.Load()), attr="get_logger", ctx=ast.Load()),
                args=[],
                keywords=[],
            )
            prelude.append(ast.Assign(targets=[ast.Name(id="log", ctx=ast.Store())], value=get_logger_call))
        if prelude:
            tree.body = prelude + tree.body
            self.changed = True
        return tree


def migrate_file(content: str) -> Tuple[str, bool]:
    tree = ast.parse(content)
    transformer = PrintToStructlogTransformer()
    transformer.visit(tree)
    tree = transformer.ensure_imports_and_logger(tree)
    try:
        new_code = ast.unparse(tree)
    except Exception:
        # Fallback to original content if unparse fails
        return content, False
    return new_code, transformer.changed


def migrate_directory(input_dir: Path, output_dir: Optional[Path], translations_file: str = "log_messages.json") -> MigrationResult:
    """Migrate Python files under input_dir. Writes to output_dir if provided, else in-place.

    translations_file is currently unused but kept for CLI compatibility and future enhancements.
    """
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
            # Copy file as-is when writing to a different output dir
            target_path = py if output_dir is None else (output_dir / py.relative_to(input_dir))
            target_path.parent.mkdir(parents=True, exist_ok=True)
            if output_dir is None:
                # in-place: only write if different to avoid touching timestamps
                if new_code != original:
                    target_path.write_text(new_code, encoding="utf-8")
            else:
                target_path.write_text(original, encoding="utf-8")
            continue

        # Write transformed code
        target_path = py if output_dir is None else (output_dir / py.relative_to(input_dir))
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(new_code, encoding="utf-8")
        result.files_transformed += 1

    return result
