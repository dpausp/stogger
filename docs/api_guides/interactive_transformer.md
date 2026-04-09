# Interactive Transformer Module

:::{admonition} Test Coverage: 67.0%
:class: warning

This module has moderate test coverage. Some features may not work as expected.
:::

The `stogger.interactive_transformer` module provides interactive, user-guided code transformations with preview and confirmation, inspired by the amber search and replace tool.

## Basic Usage

```python
from pathlib import Path
from stoggertools.interactive_transformer import (
    create_interactive_transformer,
    transform_file_interactive,
    transform_directory_interactive,
)

# Quick interactive transformation of a single file
transform_file_interactive(Path("src/my_module.py"))

# Transform an entire directory
transform_directory_interactive(Path("src/"), pattern="*.py")
```

## InteractiveTransformer

The main class for interactive code transformation sessions.

```python
from stoggertools.interactive_transformer import InteractiveTransformer

transformer = InteractiveTransformer(
    context_lines=3,              # Lines of context to show
    enable_live_editing=True,     # Allow live editing of proposals
    use_external_editor=False,    # Use external editor for edits
)

# Transform a single file interactively
result = transformer.transform_file_interactive(Path("module.py"))

# Transform a directory
results = transformer.transform_directory_interactive(Path("src/"))
```

### Interactive Choices

During transformation, the user can choose:

| Key | Action |
|-----|--------|
| `y` | Accept this transformation |
| `n` | Reject this transformation |
| `a` | Accept all remaining transformations |
| `s` | Skip remaining transformations in this file |
| `q` | Quit the session |
| `p` | Preview with syntax highlighting |
| `e` | Live-edit the transformation |

## Convenience Functions

### create_interactive_transformer

```python
from stoggertools.interactive_transformer import create_interactive_transformer

transformer = create_interactive_transformer(context_lines=3)
```

### transform_file_interactive

```python
from stoggertools.interactive_transformer import transform_file_interactive

result = transform_file_interactive(Path("module.py"), context_lines=3)
```

### transform_directory_interactive

```python
from stoggertools.interactive_transformer import transform_directory_interactive

results = transform_directory_interactive(
    Path("src/"),
    pattern="*.py",
    context_lines=3,
)
```

## Session Summary

After completing a transformation session, a summary is displayed showing:
- Files processed
- Proposals accepted/rejected
- Files skipped
- Live edits made

## Dependencies

Requires `rich` for terminal UI:

```bash
pip install stogger[cli]
```

## API Reference

```{autoapi} stogger.interactive_transformer
:members:
```
