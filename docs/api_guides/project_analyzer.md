# Project Analyzer Module

:::{admonition} Test Coverage: 55.3%
:class: warning

This module has moderate test coverage. Some features may not work as expected.
:::

The `nicestlog.project_analyzer` module provides automated analysis of existing Python projects to determine the best nicestlog migration strategy and identify potential issues.

## Basic Usage

```python
from pathlib import Path
from nicestlog.project_analyzer import ProjectAnalyzer

analyzer = ProjectAnalyzer(Path("."))
report = analyzer.analyze()

print(f"Strategy: {report.recommendation.strategy}")
print(f"Priority: {report.recommendation.priority}")
print(f"Patterns found: {len(report.logging_patterns)}")
```

## Main Classes

### ProjectAnalyzer

Analyzes a Python project for logging migration readiness.

```python
from nicestlog.project_analyzer import ProjectAnalyzer

analyzer = ProjectAnalyzer(
    project_root=Path("."),
    verbose=True,
)

report = analyzer.analyze()
```

### ProjectAnalysisReport

Complete analysis results including patterns, complexity, dependencies, and recommendations.

Key attributes:
- `logging_patterns`: Detected logging patterns (print, logging, structlog, etc.)
- `complexity`: Project complexity metrics
- `dependencies`: Dependency analysis
- `recommendation`: Migration strategy recommendation

### LoggingPattern

Represents a detected logging pattern.

```python
@dataclass
class LoggingPattern:
    pattern_type: str       # 'print', 'logging', 'structlog', 'cli_output', 'custom'
    file_path: str
    line_number: int
    code_snippet: str
    severity: str           # 'high', 'medium', 'low'
    migration_priority: int  # 1-10
```

### MigrationRecommendation

```python
@dataclass
class MigrationRecommendation:
    strategy: str           # 'print-to-structlog', 'logging-to-structlog', etc.
    priority: str           # 'high', 'medium', 'low'
    estimated_effort: str   # 'low', 'medium', 'high'
    recommended_approach: str  # 'automatic', 'interactive', 'manual'
    risk_level: str         # 'low', 'medium', 'high'
    prerequisites: list[str]
    steps: list[str]
```

## API Reference

```{autoapi} nicestlog.project_analyzer
:members:
```
