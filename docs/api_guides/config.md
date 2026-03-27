# Configuration Module

:::{admonition} Test Coverage: 93.4%
:class: tip

This module has high test coverage and is well-documented.
:::

The `nicestlog.config` module provides configuration management for nicestlog, supporting both pyproject.toml configuration and programmatic overrides.

## NicestLogConfig

The main configuration class that merges pyproject.toml settings with runtime overrides.

### Basic Usage

```python
from nicestlog.config import NicestLogConfig

# Load from pyproject.toml with defaults
config = NicestLogConfig()

# Override specific settings
config = NicestLogConfig(
    verbose=True,
    log_format="json",
    logdir=Path("/var/log/myapp")
)
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `verbose` | bool | False | Enable debug-level logging |
| `logdir` | Path \| None | None | Directory for log files |
| `log_cmd_output` | bool | False | Enable command output logging |
| `log_to_console` | bool | True | Output to console |
| `syslog_identifier` | str | "nicestlog" | Systemd journal identifier |
| `show_caller_info` | bool | False | Include caller info in logs |
| `translation_dir` | Path \| None | None | Directory for translation files |
| `language` | str | "en" | Language for translations |
| `log_format` | str | "simple" | Log format: "simple" or "json" |
| `async_logging` | bool | False | Enable async logging |
| `enable_pii_scrubbing` | bool | True | Enable PII redaction |
| `pii_redaction_text` | str | "[REDACTED]" | Text for redacted PII |
| `enable_systemd` | bool | True | Enable systemd journal integration |
| `src_dir` | str | "src" | Source directory for analysis |

### pyproject.toml Configuration

```toml
[tool.nicestlog]
verbose = false
syslog_identifier = "my-app"
log_format = "json"
async_logging = false
enable_structured_logging = true
enable_performance_monitoring = true

# AST Analysis settings
[tool.nicestlog.ast]
respect_gitignore = true
max_parameters = 8
logging_focus = true
```

## Project Structure Detection

### detect_project_structure

Detects project structure using smart heuristics.

```python
from nicestlog.config import detect_project_structure
from pathlib import Path

structure = detect_project_structure(Path.cwd())

print(f"Source dirs: {structure.source_dirs}")
print(f"Test dirs: {structure.test_dirs}")
print(f"Detection source: {structure.detection_source}")
```

### ProjectStructure

Data class containing detected project information.

```python
@dataclass
class ProjectStructure:
    source_dirs: list[str]
    test_dirs: list[str]
    exclude_patterns: list[str]
    detection_source: str  # "pyproject.toml", "heuristics", "defaults"
    project_root: Path
```

Methods:
- `get_source_paths()` - Get absolute paths for source directories
- `get_test_paths()` - Get absolute paths for test directories
- `should_exclude_from_logging_analysis(file_path)` - Check if file should be excluded

## SimpleFormatSettings

Settings for console formatting.

```python
from nicestlog.config import SimpleFormatSettings

settings = SimpleFormatSettings(
    min_level="info",
    show_logger_brackets=False,
    show_pid=False,
    show_code_info=False,
    timestamp_format="iso",
    pad_event_width=30
)
```

## Example: Full Configuration

```python
from pathlib import Path
from nicestlog.config import NicestLogConfig, detect_project_structure

# Detect project structure
structure = detect_project_structure()
print(f"Detected from: {structure.detection_source}")

# Create configuration
config = NicestLogConfig(
    verbose=True,
    logdir=Path("./logs"),
    log_format="json",
    enable_pii_scrubbing=True,
    translation_dir=Path("./translations"),
    language="de"
)

# Access settings
print(f"Log format: {config.log_format}")
print(f"PII scrubbing: {config.enable_pii_scrubbing}")
```

## API Reference

```{autoapi} nicestlog.config
:members:
```
