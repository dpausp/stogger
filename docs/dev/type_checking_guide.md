# Type Checking Best Practices Guide

This guide documents the proven methodology for systematic type checking improvements in stogger, based on our successful journey from 66 mypy errors to 0 errors.

## Overview

Type checking with mypy provides significant benefits:
- Better IDE support and autocompletion
- Reduced runtime errors
- Improved code maintainability
- Enhanced developer experience

## Strategic Approach

### Error Triage and Prioritization

Always start with comprehensive error analysis:

```bash
# Get error count by file
uv run mypy src/ | grep "error:" | cut -d: -f1 | sort | uniq -c | sort -nr

# Get specific error details
uv run mypy src/stogger/filename.py --show-error-codes
```

**Priority Order:**
1. High-impact files (most errors first)
2. Foundational modules (imported by many others) 
3. Simple fixes (missing imports, basic annotations)
4. Complex type inference issues (object types, generics)

### Common Error Categories and Solutions

| Error Type | Solution Pattern | Example |
|------------|------------------|---------|
| `var-annotated` | Add explicit type hints | `items = []` → `items: List[str] = []` |
| `assignment` | Fix type mismatches | Use `Optional[T]` or proper casting |
| `import-not-found` | Add type ignore stubs | `import systemd  # type: ignore[import-not-found]` |
| `call-overload` | Use explicit casting | `cast(List[str], dict.get("key", []))` |
| `union-attr` | Add null checks | `if obj is not None: obj.method()` |
| `arg-type` | Type casting or annotations | `len(cast(List[str], obj))` |

## Technical Patterns

### Container Type Annotations

```python
# Explicit types
data: Dict[str, Any] = {}
items: List[str] = []
```

### Optional Type Handling

```python
def process(data: Optional[List[str]]):
    if data is not None:
        for item in data:
            print(item)
```

### Dict.get() Object Type Resolution

The most common issue in stogger was `dict.get()` returning `object` type:

```python
# Explicit casting
missing_keys = cast(List[str], result.get("missing_keys", []))

# Alternative - type annotation with ignore
missing_keys: List[str] = result.get("missing_keys", [])  # type: ignore[assignment]
```

### External Dependency Imports

For dependencies without type stubs (common in stogger):

```python
try:
    import systemd  # type: ignore[import-untyped]
    from systemd.journal import Reader  # type: ignore[import-untyped]
    SYSTEMD_AVAILABLE = True
except ImportError:
    SYSTEMD_AVAILABLE = False
    systemd = None  # type: ignore[assignment]
```

### Number Type Compatibility

```python
# ❌ Poor - int/float mismatch
stats = {"avg": 0}  # int
stats["avg"] = total / count  # assigns float to int field

# ✅ Good - consistent types
stats = {"avg": 0.0}  # float from start
stats["avg"] = total / count  # float to float
```

## Systematic Workflow

### The Iterative Fix Process

1. **Run full check**: `doit check` or `uv run mypy src/`
2. **Identify patterns**: Group similar errors by type
3. **Fix by category**: Don't jump around randomly
4. **Test incrementally**: Fix 5-10 errors, then recheck
5. **Commit frequently**: Save progress with descriptive messages

### Error Resolution Strategy

```
Run mypy → Error Count Analysis
├── >20 errors: Fix by file (highest count first)
├── 5-20 errors: Fix by error type (group similar)
└── <5 errors: Fix individually

Each fix cycle:
Fix errors → Run mypy → Commit progress → Repeat
```

## Advanced Techniques

### Type Casting Guidelines

**Use `cast()` when:**
- You know the runtime type but mypy can't infer it
- Dealing with `dict.get()` returning complex types
- External API returns are correctly typed at runtime

```python
# Complex configuration structures
items = cast(List[Dict[str, Any]], config.get("items", []))

# External API results
result = cast(ApiResponse, api_call())
```

**Use `# type: ignore` when:**
- External library compatibility issues
- Complex expressions where casting is unwieldy
- Temporary fixes during development

```python
# Specific error codes are better than broad ignores
import untyped_library  # type: ignore[import-untyped]
complex_result = complex_function()  # type: ignore[return-value]
```

### Required Imports

Always ensure these common imports are available:

```python
from typing import (
    Any, Dict, List, Optional, Union, cast,
    Sized, Iterable, Collection
)
```

## Quality Assurance

### Pre-Commit Checklist

```bash
# Essential checks before committing type fixes
uv run ruff check          # Linting
uv run ruff format         # Formatting  
uv run mypy src/           # Type checking
python -m pytest tests/   # Functionality preserved
```

### Documentation Standards

Document complex type decisions:

```python
def complex_function(
    data: Dict[str, Any]  # Runtime type varies, Any needed for flexibility
) -> Optional[List[str]]:  # May return None if processing fails
    """
    Process configuration data.
    
    Args:
        data: Configuration dictionary with varying value types
        
    Returns:
        List of processed strings, or None if processing fails
    """
```

## Common Anti-Patterns

### Better Approaches

```python
# Fix root causes with proper typing
data: Dict[str, Any] = get_data()
process(data)

# Use specific error codes
result = function()  # type: ignore[return-value]

# Document why ignores are necessary
external_api_call()  # type: ignore[import-untyped] - third-party has no stubs
```

## Maintenance and Long-term Strategy

### CI Integration

Add type checking to the development workflow:

```yaml
# In CI pipeline
- name: Type Check
  run: uv run mypy src/
```

### Pre-commit Hooks

Prevent type errors from being committed:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: mypy
        name: mypy
        entry: uv run mypy
        language: system
        types: [python]
```

### Success Metrics

Track type safety improvements:
- **Error Count**: Monitor mypy error reduction over time
- **Coverage**: Ensure all modules pass type checking
- **Team Velocity**: Measure development speed improvements
- **Bug Reduction**: Track runtime type-related errors

## References

- [MyPy Documentation](https://mypy.readthedocs.io/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Type Checking Best Practices](https://typing.readthedocs.io/en/latest/source/best_practices.html)