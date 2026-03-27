# Live Editor Module

:::{warning} Limited Test Coverage (24.2%)

This module has limited test coverage. Use at your own risk. Contributions to improve test coverage are welcome.
:::

The `nicestlog.live_editor` module provides interactive in-terminal code editing for transformation proposals, with syntax highlighting, validation, and edit session recording for machine learning.

## Basic Usage

```python
from nicestlog.live_editor import LiveCodeEditor

editor = LiveCodeEditor(use_external_editor=False)

# Edit a transformation suggestion
final_code, accepted, session = editor.edit_transformation(
    original_code="print('hello')",
    suggested_code="log.info('hello')",
    pattern_name="print_to_structlog",
    file_path="module.py",
    line_number=42,
)
```

## LiveCodeEditor

The main editor class for interactive transformation editing.

```python
from nicestlog.live_editor import LiveCodeEditor

editor = LiveCodeEditor(
    use_external_editor=False,  # Use in-terminal editor
)
```

### edit_transformation

Edit a transformation suggestion interactively. Returns `(final_code, accepted, edit_session)`.

### save_edit_sessions

Save recorded edit sessions to a JSON file for analysis.

### get_learning_insights

Get aggregated insights from recorded edit sessions (acceptance rate, common patterns, etc.).

## EditSession

Dataclass recording a single editing session for ML:

```python
@dataclass
class EditSession:
    original_code: str
    ai_suggestion: str
    user_final_code: str
    edit_steps: list[str]
    pattern_name: str
    file_path: str
    line_number: int
    accepted: bool
    edit_duration_seconds: float
    syntax_errors_encountered: int = 0
```

## Dependencies

Requires `rich` for terminal UI:

```bash
pip install nicestlog[cli]
```

## API Reference

```{autoapi} nicestlog.live_editor
:members:
```
