# 🚀 Advanced AST Assistant - Revolutionary Code Transformation

The Advanced AST Assistant is nicestlog's most powerful feature - a sophisticated code analysis and transformation engine with comprehensive logging of every operation.

## 🎯 Overview

The Advanced Assistant combines:
- **Deep AST Analysis** - Comprehensive code structure analysis
- **Pattern-Based Transformations** - Sophisticated code transformations
- **Extensive Logging** - Every operation is logged with structured data
- **Performance Metrics** - Detailed timing and performance data
- **Safety Features** - Dry-run mode, backups, and rollback capabilities

## 🔍 Key Features

### 1. **Deep Code Analysis**
```python
from nicestlog.advanced_assistant import analyze_python_file

# Analyze any Python file
result = analyze_python_file(Path("my_script.py"))

print(f"Complexity Score: {result.complexity_score}")
print(f"Patterns Detected: {result.detected_patterns}")
print(f"Issues Found: {result.potential_issues}")
print(f"Suggestions: {result.transformation_suggestions}")
```

### 2. **Intelligent Transformations**
```python
from nicestlog.advanced_assistant import transform_python_file

# Transform code with comprehensive logging
result = transform_python_file(Path("my_script.py"), dry_run=True)

print(f"Changes Made: {len(result.changes_made)}")
print(f"Duration: {result.metrics.duration:.2f}s")
print(f"Nodes Analyzed: {result.metrics.nodes_analyzed}")
```

### 3. **Custom Transformation Patterns**
```python
from nicestlog.advanced_assistant import AdvancedAssistant, ASTPattern, NodeType
import ast

# Create custom pattern
def is_todo_comment(node: ast.AST) -> bool:
    return (isinstance(node, ast.Constant) and 
            isinstance(node.value, str) and 
            "TODO" in node.value.upper())

def highlight_todo(node: ast.Constant) -> ast.Constant:
    node.value = f"🚨 {node.value} 🚨"
    return node

todo_pattern = ASTPattern(
    name="highlight_todos",
    description="Add emphasis to TODO comments",
    node_type=NodeType.CALL,
    matcher=is_todo_comment,
    transformer=highlight_todo,
    priority=1
)

# Use custom pattern
assistant = AdvancedAssistant()
assistant.add_pattern(todo_pattern)
result = assistant.transform_file(Path("my_file.py"))
```

## 🖥️ CLI Interface

The Advanced Assistant includes a rich CLI interface:

### Analyze Code
```bash
# Analyze a single file
nicestlog ast analyze my_script.py --verbose

# Analyze entire directory
nicestlog ast analyze src/ --pattern "*.py" --json

# Get detailed analysis
nicestlog ast analyze . --verbose --json > analysis.json
```

### Transform Code
```bash
# Preview transformations (safe dry-run)
nicestlog ast transform my_script.py --dry-run --verbose

# Apply transformations
nicestlog ast transform my_script.py --apply

# Transform directory with specific patterns
nicestlog ast transform src/ --enable print_to_structlog --disable add_missing_docstrings

# Transform with custom pattern selection
nicestlog ast transform . --pattern "*.py" --enable highlight_todos --apply
```

### Manage Patterns
```bash
# List available patterns
nicestlog ast patterns --list

# Show detailed pattern information
nicestlog ast patterns --details
```

## 📊 Analysis Capabilities

The Advanced Assistant analyzes:

### **Code Structure**
- Function and class definitions
- Import statements and dependencies
- Control flow complexity
- AST node distribution

### **Pattern Detection**
- Print statements (candidates for structured logging)
- Logging calls and patterns
- Functions without docstrings
- Complex functions (too many parameters)
- TODO comments and technical debt

### **Quality Metrics**
- Cyclomatic complexity scoring
- Code organization analysis
- Potential refactoring opportunities
- Performance optimization suggestions

## 🔄 Built-in Transformation Patterns

### 1. **Print to Structured Logging**
Converts `print()` statements to structured logging:

```python
# Before
print("Processing user", user_id, "with status", status)

# After  
log.info("print-message", 
         _replace_msg="Processing user {user_id} with status {status}",
         user_id=user_id, status=status)
```

### 2. **Add Missing Docstrings** (Optional)
Adds placeholder docstrings to functions:

```python
# Before
def calculate_total(items):
    return sum(items)

# After
def calculate_total(items):
    """TODO: Add docstring for calculate_total"""
    return sum(items)
```

## 📈 Performance & Metrics

Every operation includes detailed metrics:

```python
result = transform_python_file(Path("large_file.py"))

print(f"Analysis Duration: {result.metrics.duration:.2f}s")
print(f"Nodes Analyzed: {result.metrics.nodes_analyzed}")
print(f"Nodes Transformed: {result.metrics.nodes_transformed}")
print(f"Analysis Rate: {result.metrics.nodes_analyzed/result.metrics.duration:.0f} nodes/sec")
print(f"Patterns Matched: {result.metrics.patterns_matched}")
```

## 🛡️ Safety Features

### **Dry Run Mode**
Always test transformations safely:
```python
# Preview changes without modifying files
result = assistant.transform_file(Path("important.py"), dry_run=True)
```

### **Automatic Backups**
When applying changes, backups are automatically created:
```
my_script.py          # Transformed file
my_script.py.backup   # Original backup
```

### **Comprehensive Logging**
Every operation is logged with structured data:
```python
# All operations generate detailed logs
log.info("transformation-completed",
         file_path="my_script.py",
         changes_made=5,
         duration=0.15,
         patterns_matched={"print_to_structlog": 3, "add_docstrings": 2})
```

## 🎨 Rich Output

The CLI provides beautiful, informative output:

### Analysis Results
```
📊 Analysis Summary
┌─────────────────────┬─────────┐
│ File                │ my.py   │
│ Complexity Score    │ 12      │
│ Patterns Detected   │ 5       │
│ Issues Found        │ 2       │
│ Suggestions         │ 8       │
└─────────────────────┴─────────┘

🎯 Detected Patterns:
  • print_statement
  • logging_call

⚠️ Potential Issues:
  • Function 'process_data' has many parameters (7)
  • Class 'DataProcessor' has many methods (25)

💡 Transformation Suggestions:
  • Convert print() to structured logging at line 15
  • Add docstring to function 'helper_func'
```

### Transformation Results
```
🔄 Transformation Preview
┌─────────────────────┬─────────┐
│ Success             │ ✅ Yes  │
│ Changes Made        │ 5       │
│ Duration            │ 0.15s   │
│ Nodes Analyzed      │ 247     │
│ Nodes Transformed   │ 5       │
└─────────────────────┴─────────┘

📝 Changes Previewed:
  • Applied print_to_structlog at line 15
  • Applied print_to_structlog at line 23
  • Applied print_to_structlog at line 31
```

## 🚀 Advanced Usage

### Batch Processing
```python
# Transform entire project
assistant = AdvancedAssistant(verbose=True)
results = assistant.transform_directory(
    Path("src/"), 
    pattern="*.py", 
    dry_run=False
)

# Analyze results
successful = sum(1 for r in results if r.success)
total_changes = sum(len(r.changes_made) for r in results)
print(f"Transformed {successful}/{len(results)} files with {total_changes} changes")
```

### Custom Analysis Pipeline
```python
# Create specialized assistant
assistant = AdvancedAssistant()

# Add custom patterns
assistant.add_pattern(my_custom_pattern)

# Configure patterns
for pattern in assistant.patterns:
    if pattern.name == "add_missing_docstrings":
        pattern.enabled = False

# Analyze and transform
analysis = assistant.analyze_file(Path("complex_file.py"))
if analysis.complexity_score > 20:
    result = assistant.transform_file(Path("complex_file.py"), dry_run=False)
```

## 🎯 Integration with nicestlog

The Advanced Assistant is fully integrated with nicestlog's logging system:

```python
import nicestlog
import structlog

# Initialize nicestlog
nicestlog.init_logging(verbose=True, syslog_identifier="my_transformer")

# All assistant operations are automatically logged
from nicestlog.advanced_assistant import AdvancedAssistant

assistant = AdvancedAssistant(verbose=True)
result = assistant.transform_file(Path("my_file.py"))

# Logs include:
# - ast-analyzer-initialized
# - analysis-started  
# - pattern-matched
# - node-transformed
# - transformation-completed
# - And much more!
```

## 🎉 Example: Complete Workflow

```python
#!/usr/bin/env python3
import nicestlog
import structlog
from pathlib import Path
from nicestlog.advanced_assistant import AdvancedAssistant

# Initialize logging
nicestlog.init_logging(verbose=True, syslog_identifier="code_transformer")
log = structlog.get_logger()

def transform_project():
    """Transform an entire Python project."""
    log.info("project-transformation-started", project_path="./src")
    
    # Create assistant
    assistant = AdvancedAssistant(verbose=True)
    
    # Analyze first
    log.info("analyzing-project-structure")
    python_files = list(Path("src").glob("*.py"))
    
    for file_path in python_files:
        analysis = assistant.analyze_file(file_path)
        log.info("file-analyzed", 
                file=str(file_path),
                complexity=analysis.complexity_score,
                issues=len(analysis.potential_issues))
    
    # Transform with preview first
    log.info("previewing-transformations")
    results = assistant.transform_directory(Path("src"), dry_run=True)
    
    total_changes = sum(len(r.changes_made) for r in results)
    log.info("transformation-preview-complete", 
             total_changes=total_changes,
             files_affected=len([r for r in results if r.changes_made]))
    
    # Apply if changes look good
    if total_changes > 0:
        log.info("applying-transformations")
        assistant.transform_directory(Path("src"), dry_run=False)
        log.info("project-transformation-complete")

if __name__ == "__main__":
    transform_project()
```

The Advanced AST Assistant represents the cutting edge of automated code transformation, combining the power of Python's AST with nicestlog's comprehensive logging to create a tool that's both powerful and transparent. Every operation is logged, every change is tracked, and every transformation is safe and reversible.

🎊 **Transform your code with confidence!** 🎊