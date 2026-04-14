# Advanced Assistant Module

:::{admonition} Test Coverage: 84.9%
:class: tip

This module has high test coverage and is well-documented.
:::

The `stogger.advanced_assistant` module provides sophisticated AST analysis and transformation capabilities for code migration and refactoring, with comprehensive logging of every operation.

## Quick Start

```python
from pathlib import Path
from stogger.advanced_assistant import create_advanced_assistant, analyze_python_file

# Quick analysis
result = analyze_python_file(Path("my_module.py"))
print(f"Complexity: {result.complexity_score}")
print(f"Patterns: {result.detected_patterns}")

# Full assistant
assistant = create_advanced_assistant(verbose=True)
result = assistant.transform_file(Path("my_module.py"), dry_run=True)
```

## Main Classes

### AdvancedAssistant

The main entry point for AST analysis and transformation.

```python
from stogger.advanced_assistant import AdvancedAssistant

assistant = AdvancedAssistant(verbose=True)

# Analyze a file
analysis = assistant.analyze_file(Path("module.py"))
print(f"Functions: {analysis.function_count}")
print(f"Classes: {analysis.class_count}")
print(f"Issues: {analysis.potential_issues}")

# Transform a file
result = assistant.transform_file(
    Path("module.py"),
    dry_run=True  # Preview changes without writing
)
print(f"Changes: {result.changes_made}")

# Transform a directory
results = assistant.transform_directory(
    Path("src/"),
    dry_run=True
)
```

### CodeAnalysisResult

Results of deep code analysis.

```python
@dataclass
class CodeAnalysisResult:
    file_path: Path
    original_hash: str
    ast_tree: ast.Module
    node_counts: dict[str, int]
    complexity_score: int
    detected_patterns: list[str]
    potential_issues: list[str]
    transformation_suggestions: list[str]
```

### TransformationResult

Complete result of a transformation operation.

```python
@dataclass
class TransformationResult:
    original_code: str
    transformed_code: str
    analysis: CodeAnalysisResult
    metrics: TransformationMetrics
    success: bool
    changes_made: list[str]
```

## Pattern-Based Transformation

### ASTPattern

Define custom transformation patterns.

```python
from stogger.advanced_assistant import ASTPattern, NodeType, AdvancedAssistant
import ast

# Custom pattern to detect and transform print statements
def is_print_call(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call) and
        isinstance(node.func, ast.Name) and
        node.func.id == "print"
    )

def transform_print(node: ast.Call) -> ast.Call:
    # Transform print() to log.info()
    new_func = ast.Attribute(
        value=ast.Name(id="log", ctx=ast.Load()),
        attr="info",
        ctx=ast.Load()
    )
    return ast.Call(
        func=new_func,
        args=[ast.Constant(value="print-output")],
        keywords=[]
    )

pattern = ASTPattern(
    name="print_to_log",
    description="Convert print() to log.info()",
    node_type=NodeType.CALL,
    matcher=is_print_call,
    transformer=transform_print,
    priority=10
)

assistant = AdvancedAssistant()
assistant.add_pattern(pattern)
```

## Convenience Functions

### create_advanced_assistant

Create a new AdvancedAssistant instance.

```python
from stogger.advanced_assistant import create_advanced_assistant

assistant = create_advanced_assistant(verbose=True)
```

### analyze_python_file

Quick analysis of a Python file.

```python
from stogger.advanced_assistant import analyze_python_file
from pathlib import Path

result = analyze_python_file(Path("module.py"))
print(f"Complexity: {result.complexity_score}")
print(f"Patterns: {result.detected_patterns}")
```

### transform_python_file

Quick transformation of a Python file.

```python
from stogger.advanced_assistant import transform_python_file
from pathlib import Path

result = transform_python_file(Path("module.py"), dry_run=True)
if result.success:
    print(f"Changes: {result.changes_made}")
```

## Example: Directory Migration

```python
from pathlib import Path
from stogger.advanced_assistant import create_advanced_assistant

assistant = create_advanced_assistant(verbose=True)

# Preview all changes
results = assistant.transform_directory(
    Path("src/myproject"),
    dry_run=True
)

for result in results:
    if result.success and result.changes_made:
        print(f"\n{result.file_path}:")
        for change in result.changes_made:
            print(f"  - {change}")

# Apply changes
results = assistant.transform_directory(
    Path("src/myproject"),
    dry_run=False
)
```

## API Reference

```{autoapi} stogger.advanced_assistant
:members:
```
