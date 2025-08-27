"""
🚀 Advanced AST Assistant - Revolutionary Code Transformation with Comprehensive Logging

This module provides sophisticated AST analysis and transformation capabilities with
extensive logging of every step. Perfect for complex code migrations and refactoring.

Features:
- Deep AST analysis with pattern detection
- Multi-stage transformation pipeline
- Comprehensive logging of all operations
- Rollback capabilities
- Performance metrics
- Safety checks and validation
"""

from __future__ import annotations

import ast
import time
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union
from enum import Enum
import structlog

# Initialize our logger for the assistant itself
log = structlog.get_logger("nicestlog.advanced_assistant")


class TransformationStage(Enum):
    """Stages of the transformation pipeline."""

    ANALYSIS = "analysis"
    VALIDATION = "validation"
    PREPARATION = "preparation"
    TRANSFORMATION = "transformation"
    POST_PROCESSING = "post_processing"
    VERIFICATION = "verification"


class NodeType(Enum):
    """Types of AST nodes we can analyze."""

    FUNCTION_DEF = "function_def"
    CLASS_DEF = "class_def"
    IMPORT = "import"
    CALL = "call"
    ASSIGN = "assign"
    IF = "if"
    FOR = "for"
    WHILE = "while"
    TRY = "try"
    WITH = "with"


@dataclass
class ASTPattern:
    """Represents a pattern to match in the AST."""

    name: str
    description: str
    node_type: NodeType
    matcher: Callable[[ast.AST], bool]
    transformer: Optional[Callable[[ast.AST], ast.AST]] = None
    priority: int = 0
    enabled: bool = True


@dataclass
class TransformationMetrics:
    """Metrics collected during transformation."""

    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    nodes_analyzed: int = 0
    nodes_transformed: int = 0
    patterns_matched: Dict[str, int] = field(default_factory=dict)
    errors_encountered: List[str] = field(default_factory=list)
    warnings_generated: List[str] = field(default_factory=list)

    @property
    def duration(self) -> float:
        """Calculate transformation duration."""
        end = self.end_time or time.time()
        return end - self.start_time


@dataclass
class CodeAnalysisResult:
    """Results of deep code analysis."""

    file_path: Path
    original_hash: str
    ast_tree: ast.Module
    node_counts: Dict[str, int] = field(default_factory=dict)
    complexity_score: int = 0
    detected_patterns: List[str] = field(default_factory=list)
    potential_issues: List[str] = field(default_factory=list)
    transformation_suggestions: List[str] = field(default_factory=list)

    @property
    def lines_of_code(self) -> int:
        """Calculate lines of code from the AST."""
        return len(ast.unparse(self.ast_tree).splitlines())

    @property
    def function_count(self) -> int:
        """Count of function definitions."""
        return self.node_counts.get("FunctionDef", 0)

    @property
    def class_count(self) -> int:
        """Count of class definitions."""
        return self.node_counts.get("ClassDef", 0)

    @property
    def issues(self) -> List[str]:
        """Alias for potential_issues for CLI compatibility."""
        return self.potential_issues

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "file_path": str(self.file_path),
            "original_hash": self.original_hash,
            "node_counts": self.node_counts,
            "complexity_score": self.complexity_score,
            "detected_patterns": self.detected_patterns,
            "potential_issues": self.potential_issues,
            "transformation_suggestions": self.transformation_suggestions,
            "lines_of_code": self.lines_of_code,
            "function_count": self.function_count,
            "class_count": self.class_count,
        }


@dataclass
class TransformationResult:
    """Complete result of a transformation operation."""

    original_code: str
    transformed_code: str
    analysis: CodeAnalysisResult
    metrics: TransformationMetrics
    success: bool
    changes_made: List[str] = field(default_factory=list)
    rollback_data: Optional[Dict[str, Any]] = None

    @property
    def file_path(self) -> Path:
        """Get the file path from the analysis."""
        return self.analysis.file_path

    @property
    def changes(self) -> List[str]:
        """Alias for changes_made for CLI compatibility."""
        return self.changes_made


class AdvancedASTAnalyzer(ast.NodeVisitor):
    """
    🔍 Advanced AST Analyzer with comprehensive logging.

    Performs deep analysis of Python code structure, detecting patterns,
    complexity, and potential transformation opportunities.
    """

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.metrics = TransformationMetrics()
        self.node_counts: Dict[str, int] = {}
        self.complexity_score = 0
        self.detected_patterns: List[str] = []
        self.potential_issues: List[str] = []
        self.transformation_suggestions: List[str] = []
        self.current_depth = 0

        log.debug(
            "ast-analyzer-initialized",
            _replace_msg="🔍 AST Analyzer initialized for {file_path}",
            file_path=str(file_path),
            analyzer_id=id(self),
        )

    def analyze(self, tree: ast.Module) -> CodeAnalysisResult:
        """Perform comprehensive analysis of the AST."""
        log.debug(
            "analysis-started",
            _replace_msg="🚀 Starting deep AST analysis for {file_path}",
            file_path=str(self.file_path),
            total_nodes=len(list(ast.walk(tree))),
        )

        # Reset state
        self.metrics = TransformationMetrics()
        self.node_counts.clear()
        self.complexity_score = 0
        self.detected_patterns.clear()
        self.potential_issues.clear()
        self.transformation_suggestions.clear()

        # Perform the analysis
        self.visit(tree)

        # Calculate final metrics
        self.metrics.end_time = time.time()

        # Create hash of original code
        original_code = ast.unparse(tree)
        original_hash = hashlib.sha256(original_code.encode()).hexdigest()

        result = CodeAnalysisResult(
            file_path=self.file_path,
            original_hash=original_hash,
            ast_tree=tree,
            node_counts=self.node_counts.copy(),
            complexity_score=self.complexity_score,
            detected_patterns=self.detected_patterns.copy(),
            potential_issues=self.potential_issues.copy(),
            transformation_suggestions=self.transformation_suggestions.copy(),
        )

        log.debug(
            "analysis-completed",
            _replace_msg="✅ AST analysis completed for {file_path} in {duration:.2f}s",
            file_path=str(self.file_path),
            duration=self.metrics.duration,
            nodes_analyzed=self.metrics.nodes_analyzed,
            complexity_score=self.complexity_score,
            patterns_detected=len(self.detected_patterns),
            issues_found=len(self.potential_issues),
        )

        return result

    def visit(self, node: ast.AST) -> None:
        """Visit a node with comprehensive logging."""
        self.current_depth += 1
        self.metrics.nodes_analyzed += 1

        node_type = type(node).__name__
        self.node_counts[node_type] = self.node_counts.get(node_type, 0) + 1

        # Log every 100 nodes to track progress
        if self.metrics.nodes_analyzed % 100 == 0:
            log.debug(
                "analysis-progress",
                _replace_msg="📊 Analyzed {count} nodes, current depth: {depth}",
                count=self.metrics.nodes_analyzed,
                depth=self.current_depth,
                current_node_type=node_type,
            )

        # Analyze specific node types
        self._analyze_node_specific(node)

        # Continue traversal
        self.generic_visit(node)
        self.current_depth -= 1

    def _analyze_node_specific(self, node: ast.AST) -> None:
        """Analyze specific node types for patterns and issues."""
        node_type = type(node).__name__

        if isinstance(node, ast.FunctionDef):
            self._analyze_function(node)
        elif isinstance(node, ast.ClassDef):
            self._analyze_class(node)
        elif isinstance(node, ast.Call):
            self._analyze_call(node)
        elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
            self._analyze_import(node)
        elif isinstance(node, (ast.If, ast.For, ast.While)):
            self.complexity_score += 1
            log.debug(
                "complexity-increase",
                _replace_msg="🔄 Complexity increased by control structure: {node_type}",
                node_type=node_type,
                line_number=getattr(node, "lineno", "unknown"),
                new_complexity=self.complexity_score,
            )

    def _analyze_function(self, node: ast.FunctionDef) -> None:
        """Analyze function definitions - focus only on logging-related functions."""
        arg_count = len(node.args.args)
        has_docstring = (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        )

        # Check if this function contains logging calls
        has_logging_calls = self._function_has_logging_calls(node)

        log.debug(
            "function-analyzed",
            _replace_msg="🔧 Function '{name}' analyzed: {arg_count} args, docstring: {has_docstring}, logging: {has_logging}",
            name=node.name,
            arg_count=arg_count,
            has_docstring=has_docstring,
            has_logging=has_logging_calls,
            line_number=node.lineno,
        )

        # Only analyze parameter count for functions that actually contain logging calls
        # This prevents false positives on CLI commands, constructors, etc.
        if (
            has_logging_calls
            and arg_count > 7
            and not self._is_common_function_pattern(node.name)
        ):
            issue = f"Logging function '{node.name}' has many parameters ({arg_count}) - consider reducing complexity (line {node.lineno})"
            self.potential_issues.append(issue)
            log.warning(
                "logging-function-too-many-params",
                _replace_msg="⚠️ {issue}",
                issue=issue,
                function_name=node.name,
                param_count=arg_count,
                line_number=node.lineno,
            )

        # Only suggest docstrings for logging-related functions
        if has_logging_calls and not has_docstring:
            suggestion = (
                f"Add docstring to logging function '{node.name}' (line {node.lineno})"
            )
            self.transformation_suggestions.append(suggestion)

    def _function_has_logging_calls(self, node: ast.FunctionDef) -> bool:
        """Check if a function contains actual logging calls (log.info, log.error, etc.)."""
        logging_call_count = 0

        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                # Check for log.method() calls (structured logging)
                if isinstance(child.func, ast.Attribute):
                    if (
                        isinstance(child.func.value, ast.Name)
                        and child.func.value.id in ["log", "logger"]
                        and child.func.attr
                        in [
                            "debug",
                            "info",
                            "warning",
                            "error",
                            "exception",
                            "critical",
                        ]
                    ):
                        logging_call_count += 1
                    # Check for logging.method() calls (standard logging)
                    elif (
                        hasattr(child.func.value, "id")
                        and child.func.value.id == "logging"
                        and child.func.attr
                        in [
                            "debug",
                            "info",
                            "warning",
                            "error",
                            "exception",
                            "critical",
                        ]
                    ):
                        logging_call_count += 1
                # Check for print statements (also considered logging-related)
                elif isinstance(child.func, ast.Name):
                    if child.func.id == "print":
                        logging_call_count += 1

        # Only consider it a "logging function" if it has multiple logging calls
        # or if it's primarily focused on logging (more than just incidental logging)
        return logging_call_count >= 2

    def _analyze_class(self, node: ast.ClassDef) -> None:
        """Analyze class definitions."""
        method_count = sum(1 for n in node.body if isinstance(n, ast.FunctionDef))

        log.debug(
            "class-analyzed",
            _replace_msg="🏗️ Class '{name}' analyzed: {method_count} methods",
            name=node.name,
            method_count=method_count,
            line_number=node.lineno,
        )

        if method_count > 20:
            issue = f"Class '{node.name}' has many methods ({method_count})"
            self.potential_issues.append(issue)

    def _analyze_call(self, node: ast.Call) -> None:
        """Analyze function calls."""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id

            # Detect print statements
            if func_name == "print":
                self.detected_patterns.append("print_statement")
                self.transformation_suggestions.append(
                    f"Convert print() to structured logging at line {node.lineno}"
                )
                log.debug(
                    "print-detected",
                    _replace_msg="🖨️ Print statement detected at line {line}",
                    line=node.lineno,
                    args_count=len(node.args),
                )

        elif isinstance(node.func, ast.Attribute):
            # Detect logging calls
            if hasattr(node.func, "attr") and node.func.attr in [
                "info",
                "debug",
                "warning",
                "error",
            ]:
                self.detected_patterns.append("logging_call")
                log.debug(
                    "logging-call-detected",
                    _replace_msg="📝 Logging call detected: {method}",
                    method=node.func.attr,
                    line=node.lineno,
                )

    def _analyze_import(self, node: Union[ast.Import, ast.ImportFrom]) -> None:
        """Analyze import statements."""
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        else:
            modules = [node.module] if node.module else []

        log.debug(
            "import-analyzed",
            _replace_msg="📦 Import analyzed: {modules}",
            modules=modules,
            line=node.lineno,
        )

    def _is_common_function_pattern(self, function_name: str) -> bool:
        """Check if this is a common function pattern that should not be flagged."""
        # Common patterns that often have many parameters
        common_patterns = [
            "__init__",  # Constructor methods
            "__new__",  # Constructor methods
            "init",  # Initialization functions
            "setup",  # Setup functions
            "configure",  # Configuration functions
            "create",  # Factory functions
            "build",  # Builder functions
            "main",  # Main functions (often have CLI args)
            "migrate",  # Migration/transformation functions
            "transform",  # Transformation functions
            "analyze",  # Analysis functions
            "process",  # Processing functions
            "handle",  # Handler functions
            "run",  # Runner functions
            "execute",  # Execution functions
            "command",  # Command functions
        ]

        # Check if function name matches common patterns
        name_lower = function_name.lower()
        for pattern in common_patterns:
            if pattern in name_lower:
                return True

        return False


class AdvancedTransformer(ast.NodeTransformer):
    """
    🔄 Advanced AST Transformer with pattern-based transformations.

    Applies sophisticated transformations based on detected patterns,
    with comprehensive logging and rollback capabilities.
    """

    def __init__(self, patterns: List[ASTPattern]):
        self.patterns = {p.name: p for p in patterns if p.enabled}
        self.metrics = TransformationMetrics()
        self.changes_made: List[str] = []
        self.transformation_id = hashlib.sha256(
            str(time.time()).encode(), usedforsecurity=False
        ).hexdigest()[:8]

        log.debug(
            "transformer-initialized",
            _replace_msg="🔄 Advanced Transformer initialized with {pattern_count} patterns",
            pattern_count=len(self.patterns),
            transformation_id=self.transformation_id,
            enabled_patterns=list(self.patterns.keys()),
        )

    def transform(self, tree: ast.Module) -> ast.Module:
        """Apply all transformations to the AST."""
        log.debug(
            "transformation-started",
            _replace_msg="🚀 Starting transformation with ID {transformation_id}",
            transformation_id=self.transformation_id,
            total_patterns=len(self.patterns),
        )

        self.metrics = TransformationMetrics()
        self.changes_made.clear()

        # Apply transformations
        transformed_tree = self.visit(tree)

        # Finalize metrics
        self.metrics.end_time = time.time()

        log.debug(
            "transformation-completed",
            _replace_msg="✅ Transformation {transformation_id} completed in {duration:.2f}s",
            transformation_id=self.transformation_id,
            duration=self.metrics.duration,
            nodes_transformed=self.metrics.nodes_transformed,
            changes_made=len(self.changes_made),
            patterns_matched=dict(self.metrics.patterns_matched),
        )

        return transformed_tree  # type: ignore[return-value]

    def visit(self, node: ast.AST) -> ast.AST:
        """Visit and potentially transform a node."""
        self.metrics.nodes_analyzed += 1

        # Check all patterns against this node
        for pattern_name, pattern in self.patterns.items():
            if pattern.matcher(node):
                self.metrics.patterns_matched[pattern_name] = (
                    self.metrics.patterns_matched.get(pattern_name, 0) + 1
                )

                log.debug(
                    "pattern-matched",
                    _replace_msg="🎯 Pattern '{pattern}' matched at line {line}",
                    pattern=pattern_name,
                    line=getattr(node, "lineno", "unknown"),
                    node_type=type(node).__name__,
                )

                if not pattern.transformer:
                    log.debug(
                        "pattern-matched-no-transformer",
                        _replace_msg="ℹ️ Pattern '{pattern}' matched but has no transformer",
                        pattern=pattern_name,
                        line=getattr(node, "lineno", "unknown"),
                        node_type=type(node).__name__,
                    )

                if pattern.transformer:
                    try:
                        new_node = pattern.transformer(node)
                        if new_node != node:
                            self.metrics.nodes_transformed += 1
                            change_desc = f"Applied {pattern_name} at line {getattr(node, 'lineno', 'unknown')}"
                            self.changes_made.append(change_desc)

                            log.debug(
                                "node-transformed",
                                _replace_msg="🔧 {change_desc}",
                                change_desc=change_desc,
                                pattern=pattern_name,
                                original_type=type(node).__name__,
                                new_type=type(new_node).__name__,
                            )

                            node = new_node
                    except Exception as e:
                        error_msg = f"Error applying {pattern_name}: {str(e)}"
                        self.metrics.errors_encountered.append(error_msg)
                        log.error(
                            "transformation-error",
                            _replace_msg="❌ {error_msg}",
                            error_msg=error_msg,
                            pattern=pattern_name,
                            exception_type=type(e).__name__,
                        )

        # Continue with standard transformation
        return self.generic_visit(node)


class AdvancedAssistant:
    """
    🎯 Advanced Code Assistant - The Ultimate AST Transformation Engine

    Combines deep analysis, pattern detection, and sophisticated transformations
    with comprehensive logging of every operation.
    """

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.patterns: List[ASTPattern] = []
        self.session_id = hashlib.sha256(
            str(time.time()).encode(), usedforsecurity=False
        ).hexdigest()[:12]

        # Initialize default patterns
        self._initialize_default_patterns()

        log.debug(
            "assistant-initialized",
            _replace_msg="🎯 Advanced Assistant initialized (session: {session_id})",
            session_id=self.session_id,
            verbose=verbose,
            default_patterns=len(self.patterns),
        )

    def _initialize_default_patterns(self) -> None:
        """Initialize default transformation patterns."""

        # Pattern 1: Convert print statements to structured logging
        def is_print_call(node: ast.AST) -> bool:
            return (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "print"
            )

        def transform_print_to_log(node: ast.Call) -> ast.Call:
            """Transform print() to log.info()"""
            new_func = ast.Attribute(
                value=ast.Name(id="log", ctx=ast.Load()), attr="info", ctx=ast.Load()
            )

            # Create event name from first argument if it's a string
            event = "print-output"
            keywords = []

            if (
                node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            ):
                event = "print-message"
                keywords.append(ast.keyword(arg="_replace_msg", value=node.args[0]))
                # Add remaining args as parameters
                for i, arg in enumerate(node.args[1:], 1):
                    keywords.append(ast.keyword(arg=f"arg{i}", value=arg))
            else:
                # Add all args as parameters
                for i, arg in enumerate(node.args):
                    keywords.append(ast.keyword(arg=f"arg{i}", value=arg))

            new_call = ast.Call(
                func=new_func, args=[ast.Constant(value=event)], keywords=keywords
            )

            return ast.copy_location(new_call, node)

        self.patterns.append(
            ASTPattern(
                name="print_to_structlog",
                description="Convert print() calls to structured logging",
                node_type=NodeType.CALL,
                matcher=is_print_call,
                transformer=transform_print_to_log,  # type: ignore[arg-type]
                priority=10,
            )
        )

        # Pattern 2: Add missing docstrings
        def is_function_without_docstring(node: ast.AST) -> bool:
            if not isinstance(node, ast.FunctionDef):
                return False

            return not (
                node.body
                and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
                and isinstance(node.body[0].value.value, str)
            )

        def add_docstring(node: ast.FunctionDef) -> ast.FunctionDef:
            """Add a basic docstring to functions that don't have one."""
            docstring = ast.Expr(
                value=ast.Constant(value=f"TODO: Add docstring for {node.name}")
            )
            node.body.insert(0, docstring)
            return node

        self.patterns.append(
            ASTPattern(
                name="add_missing_docstrings",
                description="Add placeholder docstrings to functions",
                node_type=NodeType.FUNCTION_DEF,
                matcher=is_function_without_docstring,
                transformer=add_docstring,  # type: ignore[arg-type]
                priority=5,
                enabled=False,  # Disabled by default
            )
        )

        log.debug(
            "default-patterns-initialized",
            _replace_msg="📋 Initialized {count} default transformation patterns",
            count=len(self.patterns),
            pattern_names=[p.name for p in self.patterns],
        )

    def add_pattern(self, pattern: ASTPattern) -> None:
        """Add a custom transformation pattern."""
        self.patterns.append(pattern)
        log.debug(
            "pattern-added",
            _replace_msg="➕ Added custom pattern: {name}",
            name=pattern.name,
            description=pattern.description,
            priority=pattern.priority,
            enabled=pattern.enabled,
        )

    def analyze_file(self, file_path: Path) -> CodeAnalysisResult:
        """Perform comprehensive analysis of a Python file."""
        log.debug(
            "file-analysis-started",
            _replace_msg="🔍 Starting analysis of {file_path}",
            file_path=str(file_path),
            session_id=self.session_id,
        )

        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)

            analyzer = AdvancedASTAnalyzer(file_path)
            result = analyzer.analyze(tree)

            log.debug(
                "file-analysis-completed",
                _replace_msg="✅ Analysis completed for {file_path}",
                file_path=str(file_path),
                complexity_score=result.complexity_score,
                patterns_detected=len(result.detected_patterns),
                issues_found=len(result.potential_issues),
            )

            return result

        except Exception as e:
            log.error(
                "file-analysis-failed",
                _replace_msg="❌ Failed to analyze {file_path}: {error}",
                file_path=str(file_path),
                error=str(e),
                exception_type=type(e).__name__,
            )
            raise

    def transform_file(
        self, file_path: Path, dry_run: bool = False
    ) -> TransformationResult:
        """Transform a Python file using all enabled patterns."""
        log.debug(
            "file-transformation-started",
            _replace_msg="🔄 Starting transformation of {file_path} (dry_run: {dry_run})",
            file_path=str(file_path),
            dry_run=dry_run,
            session_id=self.session_id,
            enabled_patterns=[p.name for p in self.patterns if p.enabled],
        )

        try:
            log.debug(
                "read-file",
                _replace_msg="📖 Reading and parsing file {file_path}",
                file_path=str(file_path),
            )
            # Read and analyze the file
            original_content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(original_content)

            # Perform analysis
            analysis = self.analyze_file(file_path)

            # Apply transformations
            enabled_patterns = [p for p in self.patterns if p.enabled]
            log.debug(
                "apply-transformations",
                _replace_msg="🧩 Applying {count} enabled patterns",
                count=len(enabled_patterns),
                enabled_patterns=[p.name for p in enabled_patterns],
            )
            transformer = AdvancedTransformer(enabled_patterns)
            transformed_tree = transformer.transform(tree)

            # Generate new code
            log.debug(
                "generate-code",
                _replace_msg="🧪 Generating code from transformed AST",
            )
            transformed_content = ast.unparse(transformed_tree)

            # Create result
            result = TransformationResult(
                original_code=original_content,
                transformed_code=transformed_content,
                analysis=analysis,
                metrics=transformer.metrics,
                success=True,
                changes_made=transformer.changes_made.copy(),
            )

            # Write file if not dry run
            if not dry_run and transformed_content != original_content:
                log.debug(
                    "write-backup",
                    _replace_msg="🗂️ Creating backup file for {file_path}",
                    file_path=str(file_path),
                )
                # Create backup
                backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
                backup_path.write_text(original_content)

                # Write transformed content
                log.debug(
                    "write-transformed",
                    _replace_msg="✍️ Writing transformed content to {file_path}",
                    file_path=str(file_path),
                )
                file_path.write_text(transformed_content)

                log.debug(
                    "file-transformed",
                    _replace_msg="💾 File {file_path} transformed and saved (backup: {backup_path})",
                    file_path=str(file_path),
                    backup_path=str(backup_path),
                    changes_count=len(transformer.changes_made),
                )

            log.debug(
                "file-transformation-completed",
                _replace_msg="✅ Transformation completed for {file_path}",
                file_path=str(file_path),
                success=True,
                changes_made=len(transformer.changes_made),
                duration=transformer.metrics.duration,
            )

            return result

        except Exception as e:
            log.error(
                "file-transformation-failed",
                _replace_msg="❌ Failed to transform {file_path}: {error}",
                file_path=str(file_path),
                error=str(e),
                exception_type=type(e).__name__,
            )

            return TransformationResult(
                original_code="",
                transformed_code="",
                analysis=CodeAnalysisResult(
                    file_path=file_path,
                    original_hash="",
                    ast_tree=ast.Module(body=[], type_ignores=[]),
                ),
                metrics=TransformationMetrics(),
                success=False,
            )

    def transform_directory(
        self, directory: Path, pattern: str = "*.py", dry_run: bool = False
    ) -> List[TransformationResult]:
        """Transform all Python files in a directory."""
        log.debug(
            "directory-transformation-started",
            _replace_msg="🗂️ Starting directory transformation: {directory}",
            directory=str(directory),
            pattern=pattern,
            dry_run=dry_run,
            session_id=self.session_id,
        )

        files = list(directory.glob(pattern))
        log.debug(
            "directory-files-selected",
            _replace_msg="📁 Selected {count} files for transformation in {directory}",
            count=len(files),
            directory=str(directory),
        )
        results = []

        for file_path in files:
            if file_path.is_file():
                try:
                    result = self.transform_file(file_path, dry_run=dry_run)
                    results.append(result)
                except Exception as e:
                    log.error(
                        "file-transformation-error",
                        _replace_msg="❌ Error transforming {file_path}: {error}",
                        file_path=str(file_path),
                        error=str(e),
                    )

        successful = sum(1 for r in results if r.success)
        total_changes = sum(len(r.changes_made) for r in results)

        log.debug(
            "directory-transformation-completed",
            _replace_msg="✅ Directory transformation completed: {successful}/{total} files, {changes} changes",
            successful=successful,
            total=len(results),
            changes=total_changes,
            directory=str(directory),
        )

        return results


# Convenience functions for easy usage
def create_advanced_assistant(verbose: bool = True) -> AdvancedAssistant:
    """Create a new Advanced Assistant instance."""
    return AdvancedAssistant(verbose=verbose)


def analyze_python_file(file_path: Path) -> CodeAnalysisResult:
    """Quick analysis of a Python file."""
    assistant = create_advanced_assistant()
    return assistant.analyze_file(file_path)


def transform_python_file(
    file_path: Path, dry_run: bool = True
) -> TransformationResult:
    """Quick transformation of a Python file."""
    assistant = create_advanced_assistant()
    return assistant.transform_file(file_path, dry_run=dry_run)
