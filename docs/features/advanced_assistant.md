# Advanced AST Assistant

The Advanced AST Assistant provides AST-based analysis and transformations. The API and CLI described here reflect the current implementation.

- Python API: see `packages/stoggertools/src/stoggertools/advanced_assistant.py`
- CLI: available under `stoggertools check` (with AST analysis by default)

## Quick Python examples

```python
from pathlib import Path
from stoggertools.advanced_assistant import (
    AdvancedAssistant,
    ASTPattern,
    NodeType,
    analyze_python_file,
    transform_python_file,
)

# Analyze a file
analysis = analyze_python_file(Path("my_script.py"))
print(analysis.complexity_score, analysis.detected_patterns)

# Transform a file (dry-run)
result = transform_python_file(Path("my_script.py"), dry_run=True)
print(len(result.changes_made), result.metrics.nodes_analyzed)

# Custom pattern
assistant = AdvancedAssistant()
assistant.add_pattern(
    ASTPattern(
        name="example",
        description="no-op",
        node_type=NodeType.CALL,
        matcher=lambda node: False,
        transformer=lambda node: node,
        priority=1,
    )
)
```

## CLI usage

```bash
# Analyze (check with AST analysis)
stoggertools check my_script.py --verbose
stoggertools check src/ --complexity

# Transform (check with fix)
stoggertools check my_script.py --fix --dry-run --verbose

# Interactive demos
stoggertools tools demo
```

For details on detected issues in logging calls, see [Log Statement Analysis](log_analysis.md).
