"""🔍 Project Analyzer for AI Agents.

This module provides automated analysis of existing Python projects to determine
the best nicestlog migration strategy and identify potential issues.
"""

from __future__ import annotations

import ast
from dataclasses import asdict, dataclass
import fnmatch
import json
from pathlib import Path
import re
from typing import Any

import structlog

log = structlog.get_logger(__name__)


@dataclass
class LoggingPattern:
    """Represents a detected logging pattern in the codebase."""

    pattern_type: str  # 'print', 'logging', 'structlog', 'cli_output', 'custom'
    file_path: str
    line_number: int
    code_snippet: str
    severity: str  # 'high', 'medium', 'low'
    migration_priority: int  # 1-10, 10 being highest priority


@dataclass
class ProjectComplexity:
    """Project complexity metrics."""

    total_files: int
    python_files: int
    total_lines: int
    average_complexity: float
    max_complexity: float
    complexity_category: str  # 'simple', 'medium', 'complex'


@dataclass
class DependencyAnalysis:
    """Analysis of project dependencies related to logging."""

    has_logging: bool
    has_structlog: bool
    has_other_logging: list[str]
    dependency_conflicts: list[str]
    package_manager: str  # 'pip', 'poetry', 'pipenv', 'uv'


@dataclass
class MigrationRecommendation:
    """Recommended migration strategy for the project."""

    strategy: (
        str  # 'print-to-structlog', 'logging-to-structlog', 'enhancement', 'greenfield'
    )
    priority: str  # 'high', 'medium', 'low'
    estimated_effort: str  # 'low', 'medium', 'high'
    recommended_approach: str  # 'automatic', 'interactive', 'manual'
    risk_level: str  # 'low', 'medium', 'high'
    prerequisites: list[str]
    steps: list[str]


@dataclass
class ProjectAnalysisResult:
    """Complete analysis result for a project."""

    project_path: str
    analysis_timestamp: str
    logging_patterns: list[LoggingPattern]
    complexity: ProjectComplexity
    dependencies: DependencyAnalysis
    recommendation: MigrationRecommendation
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)


class ProjectAnalyzer:
    """Analyzes Python projects for nicestlog migration opportunities."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.log = structlog.get_logger("project_analyzer")

        # Patterns to detect different logging approaches
        self.print_patterns = [
            r"print\s*\(",
            r"sys\.stdout\.write",
            r"sys\.stderr\.write",
        ]

        self.logging_patterns = [
            r"logging\.",
            r"logger\.",
            r"log\.",
            r"getLogger",
        ]

        self.structlog_patterns = [
            r"structlog\.",
            r"get_logger",
            r"bind\(",
        ]

        # CLI framework output patterns
        self.cli_output_patterns = [
            r"typer\.echo\s*\(",
            r"click\.echo\s*\(",
            r"rich\.print\s*\(",
            r"console\.print\s*\(",  # Rich Console instance
            r"from rich import print",  # Rich print import
            r"parser\.error\s*\(",  # argparse error output
        ]

        # Log wrapper patterns (functions that unnecessarily wrap logging calls)
        self.wrapper_patterns = [
            r"def\s+\w*log\w*\s*\(",  # Functions with 'log' in name
            r"def\s+write_\w+\s*\(",  # write_something functions
            r"def\s+emit_\w+\s*\(",  # emit_something functions
        ]

        # Known logging libraries
        self.logging_libraries = {
            "colorlog",
            "rich",
            "click",
            "typer",
            "flask",
            "django",
            "fastapi",
            "tornado",
        }

        # Common ignore patterns (like .gitignore)
        self.default_ignore_patterns = {
            ".venv/*",
            "venv/*",
            "env/*",
            ".env/*",
            "__pycache__/*",
            "*.pyc",
            "*.pyo",
            "*.pyd",
            ".git/*",
            ".svn/*",
            ".hg/*",
            "node_modules/*",
            ".tox/*",
            ".pytest_cache/*",
            "build/*",
            "dist/*",
            "*.egg-info/*",
            ".mypy_cache/*",
            ".coverage",
            "htmlcov/*",
        }

    def analyze_project(self, project_path: Path) -> ProjectAnalysisResult:
        """Perform comprehensive analysis of a Python project."""
        self.log.info(
            "project-analysis-started",
            _replace_msg="🔍 Starting analysis of project: {project_path}",
            project_path=str(project_path),
        )

        if not project_path.exists():
            msg = f"Project path does not exist: {project_path}"
            raise ValueError(msg)

        # Gather all analysis data
        logging_patterns = self._analyze_logging_patterns(project_path)
        complexity = self._analyze_complexity(project_path)
        dependencies = self._analyze_dependencies(project_path)

        # Generate recommendation based on analysis
        recommendation = self._generate_recommendation(
            logging_patterns,
            complexity,
            dependencies,
        )

        # Collect warnings
        warnings = self._generate_warnings(logging_patterns, complexity, dependencies)

        result = ProjectAnalysisResult(
            project_path=str(project_path),
            analysis_timestamp=self._get_timestamp(),
            logging_patterns=logging_patterns,
            complexity=complexity,
            dependencies=dependencies,
            recommendation=recommendation,
            warnings=warnings,
        )

        self.log.info(
            "project-analysis-completed",
            _replace_msg="✅ Analysis completed for {project_path}",
            project_path=str(project_path),
            patterns_found=len(logging_patterns),
            recommendation=recommendation.strategy,
        )

        return result

    def _load_ignore_patterns(self, project_path: Path) -> set[str]:
        """Load ignore patterns from .gitignore, .nicestlogignore and defaults."""
        ignore_patterns = set(self.default_ignore_patterns)

        # Load .gitignore patterns
        gitignore_path = project_path / ".gitignore"
        if gitignore_path.exists():
            try:
                content = gitignore_path.read_text(encoding="utf-8")
                for line in content.split("\n"):
                    line = line.strip()
                    if line and not line.startswith("#"):
                        # Convert gitignore patterns to glob patterns
                        if line.endswith("/"):
                            ignore_patterns.add(f"{line}*")
                        else:
                            ignore_patterns.add(line)
                            ignore_patterns.add(f"{line}/*")
            except Exception as e:
                self.log.warning(
                    "gitignore-load-failed",
                    _replace_msg="Failed to load .gitignore: {error}",
                    error=str(e),
                )

        # Load .nicestlogignore patterns (custom ignore file)
        nicestlog_ignore = project_path / ".nicestlogignore"
        if nicestlog_ignore.exists():
            try:
                content = nicestlog_ignore.read_text(encoding="utf-8")
                for line in content.split("\n"):
                    line = line.strip()
                    if line and not line.startswith("#"):
                        ignore_patterns.add(line)
            except Exception as e:
                self.log.warning(
                    "nicestlogignore-load-failed",
                    _replace_msg="Failed to load .nicestlogignore: {error}",
                    error=str(e),
                )

        return ignore_patterns

    def _should_ignore_file(
        self,
        file_path: Path,
        project_path: Path,
        ignore_patterns: set[str],
    ) -> bool:
        """Check if a file should be ignored based on patterns."""
        # Get relative path from project root
        try:
            rel_path = file_path.relative_to(project_path)
        except ValueError:
            return False

        rel_path_str = str(rel_path)

        # Check against all ignore patterns
        for pattern in ignore_patterns:
            if fnmatch.fnmatch(rel_path_str, pattern):
                return True
            # Also check parent directories
            for parent in rel_path.parents:
                if fnmatch.fnmatch(str(parent), pattern):
                    return True

        return False

    def _get_python_files(self, project_path: Path) -> list[Path]:
        """Get all Python files, respecting ignore patterns."""
        ignore_patterns = self._load_ignore_patterns(project_path)
        python_files = []

        for py_file in project_path.rglob("*.py"):
            if not self._should_ignore_file(py_file, project_path, ignore_patterns):
                python_files.append(py_file)

        if self.verbose:
            total_py_files = len(list(project_path.rglob("*.py")))
            ignored_count = total_py_files - len(python_files)
            self.log.debug(
                "file-filtering-complete",
                _replace_msg="Found {total} Python files, ignored {ignored} files",
                total=total_py_files,
                ignored=ignored_count,
                included=len(python_files),
            )

        return python_files

    def _analyze_logging_patterns(self, project_path: Path) -> list[LoggingPattern]:
        """Analyze the project for different logging patterns."""
        patterns = []
        python_files = self._get_python_files(project_path)

        self.log.debug(
            "analyzing-logging-patterns",
            _replace_msg="Analyzing {file_count} Python files for logging patterns",
            file_count=len(python_files),
        )

        for py_file in python_files:
            try:
                content = py_file.read_text(encoding="utf-8")
                file_patterns = self._analyze_file_patterns(py_file, content)
                patterns.extend(file_patterns)
            except Exception as e:
                self.log.warning(
                    "file-analysis-failed",
                    _replace_msg="Failed to analyze file {file}: {error}",
                    file=str(py_file),
                    error=str(e),
                )

        return patterns

    def _analyze_file_patterns(
        self,
        file_path: Path,
        content: str,
    ) -> list[LoggingPattern]:
        """Analyze a single file for logging patterns."""
        patterns = []
        lines = content.split("\n")

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Check for CLI framework output functions first (higher priority)
            cli_pattern_found = False
            for pattern in self.cli_output_patterns:
                if re.search(pattern, line):
                    patterns.append(
                        LoggingPattern(
                            pattern_type="cli_output",
                            file_path=str(file_path),
                            line_number=line_num,
                            code_snippet=line,
                            severity="high",
                            migration_priority=8,
                        ),
                    )
                    cli_pattern_found = True
                    break

            # Check for print statements (but skip if CLI pattern already found)
            if not cli_pattern_found:
                for pattern in self.print_patterns:
                    if re.search(pattern, line):
                        patterns.append(
                            LoggingPattern(
                                pattern_type="print",
                                file_path=str(file_path),
                                line_number=line_num,
                                code_snippet=line,
                                severity="high",
                                migration_priority=9,
                            ),
                        )

            # Check for standard logging
            for pattern in self.logging_patterns:
                if re.search(pattern, line) and "structlog" not in line:
                    patterns.append(
                        LoggingPattern(
                            pattern_type="logging",
                            file_path=str(file_path),
                            line_number=line_num,
                            code_snippet=line,
                            severity="medium",
                            migration_priority=6,
                        ),
                    )

            # Check for structlog (already good!)
            for pattern in self.structlog_patterns:
                if re.search(pattern, line):
                    patterns.append(
                        LoggingPattern(
                            pattern_type="structlog",
                            file_path=str(file_path),
                            line_number=line_num,
                            code_snippet=line,
                            severity="low",
                            migration_priority=2,
                        ),
                    )

            # Check for log wrapper anti-patterns
            for pattern in self.wrapper_patterns:
                if re.search(pattern, line):
                    patterns.append(
                        LoggingPattern(
                            pattern_type="wrapper",
                            file_path=str(file_path),
                            line_number=line_num,
                            code_snippet=line,
                            severity="medium",
                            migration_priority=7,
                        ),
                    )

        return patterns

    def _analyze_complexity(self, project_path: Path) -> ProjectComplexity:
        """Analyze project complexity metrics."""
        python_files = self._get_python_files(project_path)
        total_files = len(list(project_path.rglob("*")))
        total_lines = 0
        complexities = []

        for py_file in python_files:
            try:
                content = py_file.read_text(encoding="utf-8")
                lines = len(content.split("\n"))
                total_lines += lines

                # Simple complexity metric based on AST
                try:
                    tree = ast.parse(content)
                    complexity = self._calculate_ast_complexity(tree)
                    complexities.append(complexity)
                except SyntaxError:
                    # Skip files with syntax errors
                    pass

            except Exception:
                continue

        avg_complexity = sum(complexities) / len(complexities) if complexities else 0
        max_complexity = max(complexities) if complexities else 0

        # Categorize complexity
        if len(python_files) < 5 and total_lines < 500:
            category = "simple"
        elif len(python_files) < 20 and total_lines < 2000:
            category = "medium"
        else:
            category = "complex"

        return ProjectComplexity(
            total_files=total_files,
            python_files=len(python_files),
            total_lines=total_lines,
            average_complexity=avg_complexity,
            max_complexity=max_complexity,
            complexity_category=category,
        )

    def _calculate_ast_complexity(self, tree: ast.AST) -> float:
        """Calculate a simple complexity score from AST."""
        complexity = 0.0

        for node in ast.walk(tree):
            if isinstance(node, ast.If | ast.While | ast.For):
                complexity += 1
            elif isinstance(node, ast.FunctionDef):
                complexity += 0.5
            elif isinstance(node, ast.ClassDef):
                complexity += 0.3

        return complexity

    def _analyze_dependencies(self, project_path: Path) -> DependencyAnalysis:
        """Analyze project dependencies for logging-related packages."""
        has_logging = False
        has_structlog = False
        other_logging = []
        conflicts = []
        package_manager = "unknown"

        # Check different dependency files
        dep_files = [
            ("pyproject.toml", "poetry"),
            ("requirements.txt", "pip"),
            ("Pipfile", "pipenv"),
            ("setup.py", "setuptools"),
            ("setup.cfg", "setuptools"),
        ]

        for dep_file, manager in dep_files:
            file_path = project_path / dep_file
            if file_path.exists():
                package_manager = manager
                content = file_path.read_text(encoding="utf-8")

                # Check for specific logging packages
                if "structlog" in content:
                    has_structlog = True

                # Check for other logging libraries
                for lib in self.logging_libraries:
                    if lib in content:
                        other_logging.append(lib)

                break

        # Standard logging is always available in Python
        has_logging = True

        # Detect potential conflicts

        if len(other_logging) > 2:
            conflicts.append(
                f"Multiple logging frameworks detected: {', '.join(other_logging)}",
            )

        return DependencyAnalysis(
            has_logging=has_logging,
            has_structlog=has_structlog,
            has_other_logging=other_logging,
            dependency_conflicts=conflicts,
            package_manager=package_manager,
        )

    def _generate_recommendation(
        self,
        patterns: list[LoggingPattern],
        complexity: ProjectComplexity,
        dependencies: DependencyAnalysis,
    ) -> MigrationRecommendation:
        """Generate migration recommendation based on analysis."""
        # Count pattern types
        print_count = len([p for p in patterns if p.pattern_type == "print"])
        logging_count = len([p for p in patterns if p.pattern_type == "logging"])
        structlog_count = len([p for p in patterns if p.pattern_type == "structlog"])
        cli_output_count = len([p for p in patterns if p.pattern_type == "cli_output"])
        len([p for p in patterns if p.pattern_type == "wrapper"])

        # Determine strategy
        if cli_output_count > 0:
            strategy = "cli-outputs-to-structlog"
            priority = "high"
            effort = "medium" if complexity.complexity_category == "simple" else "high"
        elif print_count > logging_count and print_count > 0:
            strategy = "print-to-structlog"
            priority = "high"
            effort = "low" if complexity.complexity_category == "simple" else "medium"
        elif logging_count > 0 and not dependencies.has_structlog:
            strategy = "logging-to-structlog"
            priority = "medium"
            effort = "medium" if complexity.complexity_category != "complex" else "high"
        elif structlog_count > 0:
            strategy = "enhancement"
            priority = "low"
            effort = "low"
        else:
            strategy = "greenfield"
            priority = "medium"
            effort = "low"

        # Determine approach
        if (
            complexity.complexity_category == "simple"
            and not dependencies.dependency_conflicts
        ):
            approach = "automatic"
            risk = "low"
        elif complexity.complexity_category == "medium":
            approach = "interactive"
            risk = "medium"
        else:
            approach = "manual"
            risk = "high"

        # Generate prerequisites and steps
        prerequisites = []
        steps = []

        if dependencies.dependency_conflicts:
            prerequisites.append("Resolve dependency conflicts")
            risk = "high"

        if not dependencies.has_structlog:
            prerequisites.append("Add structlog dependency")

        # Strategy-specific steps
        if strategy == "cli-outputs-to-structlog":
            steps = [
                "1. Run: nicestlog migrate . --type cli-outputs-to-structlog --interactive",
                "2. Validate changes",
            ]
        elif strategy == "print-to-structlog":
            steps = [
                "1. Run: nicestlog migrate . --no-dry-run --type print-to-structlog",
                "2. Validate changes",
            ]
        elif strategy == "logging-to-structlog":
            steps = [
                "1. Run: nicestlog migrate . --type logging-to-structlog --interactive",
                "2. Validate changes",
            ]
        elif strategy == "enhancement":
            steps = [
                "1. Run: nicestlog check . --fix",
                "2. Enhance existing structured logging",
            ]
        else:  # greenfield
            steps = [
                "1. Initialize nicestlog configuration: nicestlog init .",
                "2. Set up logging in main application entry point",
                "3. Implement logging throughout codebase",
            ]

        return MigrationRecommendation(
            strategy=strategy,
            priority=priority,
            estimated_effort=effort,
            recommended_approach=approach,
            risk_level=risk,
            prerequisites=prerequisites,
            steps=steps,
        )

    def _generate_warnings(
        self,
        patterns: list[LoggingPattern],
        complexity: ProjectComplexity,
        dependencies: DependencyAnalysis,
    ) -> list[str]:
        """Generate warnings based on analysis."""
        warnings = []

        if dependencies.dependency_conflicts:
            warnings.extend(dependencies.dependency_conflicts)

        if complexity.complexity_category == "complex":
            warnings.append("Complex project - consider phased migration approach")

        high_priority_patterns = [p for p in patterns if p.migration_priority >= 8]
        if len(high_priority_patterns) > 50:
            warnings.append(
                f"Large number of high-priority patterns ({len(high_priority_patterns)}) - migration may be time-consuming",
            )

        if complexity.max_complexity > 20:
            warnings.append("High complexity functions detected - review manually")

        # Check for log wrapper anti-patterns
        wrapper_patterns = [p for p in patterns if p.pattern_type == "wrapper"]
        if wrapper_patterns:
            warnings.append(
                f"Log wrapper anti-patterns detected ({len(wrapper_patterns)} functions) - "
                "consider using log.* calls directly instead of wrapper functions",
            )

        return warnings

    def _get_timestamp(self) -> str:
        """Get current timestamp as ISO string."""
        from datetime import datetime

        return datetime.now().isoformat()


def analyze_project_for_agents(
    project_path: str,
    verbose: bool = False,
) -> ProjectAnalysisResult:
    """Convenience function for AI agents to analyze a project.

    Args:
        project_path: Path to the project to analyze
        verbose: Enable verbose logging

    Returns:
        ProjectAnalysisResult with comprehensive analysis

    """
    analyzer = ProjectAnalyzer(verbose=verbose)
    return analyzer.analyze_project(Path(project_path))
