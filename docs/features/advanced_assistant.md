# 🚀 Advanced AST Assistant

The Advanced AST Assistant provides AST-based analysis and transformations. The API and CLI described here reflect the current implementation.

- Python API: see `src/nicestlog/advanced_assistant.py`
- CLI: available under `nicestlog check` (with AST analysis by default)

## Quick Python examples

```python
from pathlib import Path
from nicestlog.advanced_assistant import (
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
nicestlog check my_script.py --verbose
nicestlog check src/ --complexity

# Transform (check with fix)
nicestlog check my_script.py --fix --dry-run --verbose
nicestlog check src/ --fix --pattern specific_pattern

# Interactive demos
nicestlog tools demo
```

For details on detected issues in logging calls, see Log Statement Analysis.


The Advanced AST Assistant is nicestlog's flagship feature that provides intelligent code transformation and analysis capabilities using Python's Abstract Syntax Tree (AST).

## Overview

The Advanced AST Assistant can automatically:

- **Transform logging statements** to follow best practices
- **Detect anti-patterns** in your logging code
- **Suggest improvements** for better structured logging
- **Refactor legacy code** to modern logging patterns

## Key Features

### 🔍 Intelligent Code Analysis

The assistant analyzes your Python code at the AST level to understand:

```python
# Before transformation
logger.info(f"User {user_id} logged in from {ip_address}")

# After transformation  
logger.info("user-login", user_id=user_id, ip_address=ip_address)
```

### 🛠️ Automatic Refactoring

Transform entire codebases with a single command:

```bash
nicestlog check src/ --fix --backup
```

### 📊 Code Quality Metrics

Get detailed reports on your logging quality:

```bash
nicestlog check src/ --complexity --verbose
```

## Usage Examples

### Basic Transformation

```python
from nicestlog.advanced_assistant import AdvancedAssistant

assistant = AdvancedAssistant()

# Transform a single file
result = assistant.transform_file("my_module.py")

# Transform with custom rules
result = assistant.transform_file(
    "my_module.py",
    rules={
        "enforce_event_style": True,
        "require_structured_data": True,
        "max_string_args": 1
    }
)
```

### Batch Processing

```python
# Transform multiple files
results = assistant.transform_directory(
    "src/",
    patterns=["*.py"],
    exclude=["tests/", "migrations/"]
)

for file_path, transformation in results.items():
    print(f"Transformed {file_path}: {transformation.changes_count} changes")
```

### Custom Rules

Define your own transformation rules:

```python
from nicestlog.advanced_assistant import TransformationRule

class CustomLogRule(TransformationRule):
    def should_transform(self, node):
        # Your custom logic here
        return isinstance(node, ast.Call) and self.is_log_call(node)
    
    def transform(self, node):
        # Your transformation logic
        return self.convert_to_structured_log(node)

assistant = AdvancedAssistant(custom_rules=[CustomLogRule()])
```

## Transformation Patterns

### String Formatting to Structured Logging

```python
# Before
log.info(f"Processing order {order_id} for customer {customer_name}")
log.warning("Failed to process payment: %s" % error_message)
log.error("Database connection failed after {} attempts".format(retry_count))

# After  
log.info("order-processing-started", order_id=order_id, customer_name=customer_name)
log.warning("payment-processing-failed", error_message=error_message)
log.error("database-connection-failed", retry_count=retry_count)
```

### Exception Handling Improvements

```python
# Before
try:
    risky_operation()
except Exception as e:
    log.error(f"Operation failed: {str(e)}")

# After
try:
    risky_operation()
except Exception as e:
    log.error("operation-failed", 
              error_type=type(e).__name__,
              error_message=str(e),
              exc_info=True)
```

### Log Level Optimization

```python
# Before
log.error("User successfully logged in")  # Wrong level!
log.debug("CRITICAL: System is down!")   # Wrong level!

# After
log.info("user-login-successful", user_id=user_id)
log.critical("system-unavailable", component="database")
```

## Configuration

### Configuration File

Create a `.nicestlog.toml` file in your project root:

```toml
[advanced_assistant]
# Transformation rules
enforce_event_style = true
require_structured_data = true
max_string_arguments = 1
prefer_dash_case = true

# Analysis settings
detect_pii_leaks = true
check_log_levels = true
validate_event_ids = true

# Output settings
backup_original = true
show_diff = true
dry_run = false

[advanced_assistant.rules]
# Custom rule configurations
max_kwargs = 7
event_id_max_length = 50
forbidden_patterns = ["password", "secret", "token"]
```

### Programmatic Configuration

```python
from nicestlog.advanced_assistant import AssistantConfig

config = AssistantConfig(
    enforce_event_style=True,
    require_structured_data=True,
    max_string_arguments=1,
    backup_original=True
)

assistant = AdvancedAssistant(config=config)
```

## CLI Usage

### Transform Command

```bash
# Check and fix a single file
nicestlog check my_file.py --fix

# Check and fix a directory
nicestlog check src/ --fix

# Dry run (preview changes)
nicestlog check src/ --fix --dry-run

# Create backups
nicestlog check src/ --fix --backup

# Custom pattern analysis
nicestlog check src/ --pattern specific_pattern
```

### Analyze Command

```bash
# Analyze code quality
nicestlog check src/

# Generate detailed analysis with complexity
nicestlog check src/ --complexity --verbose

# Check specific patterns
nicestlog check src/ --pattern specific_pattern
```

### Interactive Mode

```bash
# Interactive mode for fixes
nicestlog check src/ --fix --interactive

# Dry run to preview changes
nicestlog check src/ --fix --dry-run
```

## Integration with IDEs

### VS Code Extension

Install the nicestlog VS Code extension for real-time assistance:

```json
{
    "nicestlog.enableRealTimeAnalysis": true,
    "nicestlog.showTransformationHints": true,
    "nicestlog.autoFixOnSave": false
}
```

### PyCharm Plugin

The nicestlog PyCharm plugin provides:

- Real-time code inspection
- Quick-fix suggestions
- Refactoring tools
- Code quality metrics

## Advanced Features

### Custom AST Visitors

Create custom AST visitors for specialized transformations:

```python
import ast
from nicestlog.advanced_assistant import BaseVisitor

class CustomLogVisitor(BaseVisitor):
    def visit_Call(self, node):
        if self.is_log_call(node):
            # Custom transformation logic
            return self.transform_log_call(node)
        return node

assistant = AdvancedAssistant(visitors=[CustomLogVisitor()])
```

### Plugin System

Extend the assistant with custom plugins:

```python
from nicestlog.advanced_assistant import Plugin

class MyCustomPlugin(Plugin):
    def name(self):
        return "my-custom-plugin"
    
    def transform(self, node, context):
        # Plugin transformation logic
        pass
    
    def analyze(self, node, context):
        # Plugin analysis logic
        pass

assistant = AdvancedAssistant(plugins=[MyCustomPlugin()])
```

### Machine Learning Integration

The assistant can learn from your codebase patterns:

```python
# Train on your codebase
assistant.train_on_codebase("src/", learning_mode="adaptive")

# Apply learned patterns
assistant.transform_with_learned_patterns("new_file.py")
```

## Performance Optimization

### Parallel Processing

```python
# Enable parallel processing for large codebases
assistant = AdvancedAssistant(
    parallel=True,
    max_workers=4,
    chunk_size=100
)
```

### Caching

```python
# Enable transformation caching
assistant = AdvancedAssistant(
    enable_cache=True,
    cache_dir=".nicestlog_cache"
)
```

## Best Practices

### 1. Start with Analysis

Always analyze before transforming:

```bash
nicestlog check src/ --complexity --verbose
nicestlog check src/ --fix --backup
```

### 2. Use Dry Run

Preview changes before applying:

```bash
nicestlog check src/ --fix --dry-run
```

### 3. Incremental Transformation

Transform in small batches:

```bash
nicestlog check src/module1/ --fix --backup
nicestlog check src/module2/ --fix --backup
```

### 4. Version Control Integration

Always commit before transformation:

```bash
git add -A && git commit -m "Before nicestlog transformation"
nicestlog check src/ --fix --backup
git add -A && git commit -m "After nicestlog transformation"
```

## Troubleshooting

### Common Issues

**Syntax Errors After Transformation**
```bash
# Validate syntax after transformation
python -m py_compile transformed_file.py
```

**Performance Issues with Large Files**
```python
# Use streaming mode for large files
assistant = AdvancedAssistant(streaming_mode=True)
```

**Custom Rules Not Applied**
```python
# Debug rule application
assistant = AdvancedAssistant(debug_rules=True)
```

## API Reference

### AdvancedAssistant Class

```python
class AdvancedAssistant:
    def __init__(self, config=None, rules=None, plugins=None):
        """Initialize the Advanced AST Assistant."""
        
    def transform_file(self, file_path, output_path=None):
        """Transform a single Python file."""
        
    def transform_directory(self, directory_path, recursive=True):
        """Transform all Python files in a directory."""
        
    def analyze_file(self, file_path):
        """Analyze a file for logging issues."""
        
    def analyze_directory(self, directory_path):
        """Analyze all files in a directory."""
```

## Examples and Demos

Check out the comprehensive examples in the `examples/` directory:

- `examples/advanced_assistant_demo.py` - Complete transformation demo
- `examples/interactive_demo.py` - Interactive transformation session
- `examples/live_editing_demo.py` - Real-time code editing

## 🎊 Transform your code with confidence! 🎊

The Advanced AST Assistant makes it easy to modernize your logging practices and maintain high-quality, structured logs throughout your codebase.