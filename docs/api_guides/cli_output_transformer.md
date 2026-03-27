# CLI Output Transformer Module

:::{warning} Limited Test Coverage (17.6%)

This module has limited test coverage. Use at your own risk. Contributions to improve test coverage are welcome.
:::

The `nicestlog.cli_output_transformer` module provides AST transformation capabilities to convert CLI framework output functions (typer.echo, click.echo, rich.print, etc.) to structured logging with nicestlog.

## Basic Usage

```python
from pathlib import Path
from nicestlog.cli_output_transformer import CLIOutputToStructlogTransformer

transformer = CLIOutputToStructlogTransformer()

with Path("cli_module.py").open("r") as f:
    source = f.read()

tree = transformer.transform(source)
```

## CLIOutputToStructlogTransformer

AST node transformer that converts CLI output calls to structlog calls.

```python
from nicestlog.cli_output_transformer import CLIOutputToStructlogTransformer

transformer = CLIOutputToStructlogTransformer()
```

### Supported Frameworks

The transformer detects and converts output calls from:
- **typer**: `typer.echo()`, `typer.confirm()`
- **click**: `click.echo()`, `click.secho()`
- **rich**: `rich.print()`, `console.print()`
- **argparse**: parser-based output
- **sys**: `sys.stdout.write()`, `sys.stderr.write()`

### CLIOutputCall

Dataclass representing a detected CLI output function call.

```python
@dataclass
class CLIOutputCall:
    framework: str       # 'typer', 'click', 'rich', 'argparse', 'sys'
    function: str        # 'echo', 'print', 'error', 'write'
    line_number: int
    original_call: ast.Call
    message_arg: ast.AST | None
    style_info: dict[str, Any] | None
    output_stream: str   # 'stdout', 'stderr'
```

### Static Methods

#### slugify

Convert text to a valid event identifier.

```python
event = CLIOutputToStructlogTransformer.slugify("User logged in successfully")
# Returns: "user-logged-in-successfully"
```

#### derive_event_from_literal

Extract event name from a string literal argument.

```python
event = CLIOutputToStructlogTransformer.derive_event_from_literal(
    ast.parse('"Hello World"').body[0].value
)
# Returns: "hello-world"
```

## API Reference

```{autoapi} nicestlog.cli_output_transformer
:members:
```
