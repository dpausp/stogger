# Migration Note: lint → check

## ⚠️ Breaking Change

The `lint` command has been removed in favor of the more powerful `check` command.

### Migration Guide

**Old usage:**
```bash
nicestlog lint .                    # Basic linting
nicestlog lint --strict             # Strict mode  
nicestlog lint --min-coverage 10    # Custom coverage
```

**New usage:**
```bash
nicestlog check .                   # Basic linting (same functionality)
nicestlog check . --ast             # Enhanced with AST analysis
nicestlog check . --fix             # With auto-fixing
nicestlog check . --complexity      # With complexity analysis
```

### Why the change?

The `check` command provides all functionality of `lint` plus:
- ✅ AST-based analysis
- ✅ Interactive fixing modes  
- ✅ Complexity analysis
- ✅ Pattern-specific checks
- ✅ Auto-fixing capabilities

No functionality was lost - `check` is a superset of `lint`.