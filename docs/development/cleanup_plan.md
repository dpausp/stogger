# Cleanup Plan for Try-Except Suppression and Legacy Patterns

## 1. Overview

This document outlines a detailed plan for removing try-except blocks that suppress exceptions and cleaning up legacy code patterns in the nicestlog project. The goal is to improve code quality, maintainability, and error visibility while ensuring no regressions are introduced.

## 2. Identified Issues and Cleanup Strategy

### 2.1 Try-Except Blocks That Suppress Exceptions

#### Issue 1: Bare except clauses with pass
**Location**: `src/nicestlog/assistant.py` (PrintToStructlogTransformer.visit_Assign method)
**Pattern**:
```python
try:
    # Check for logger assignment
    if (
        len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "log"
        # ... more conditions
    ):
        self.logger_assignment_present = True
except Exception:
    pass
```

**Cleanup Strategy**:
Replace with proper exception handling that either:
1. Logs the exception with `logger.exception()` and re-raises it
2. Handles specific expected exceptions appropriately
3. Removes the try-except entirely if not needed

**Risk Assessment**: Low - This is in a transformer that processes AST nodes, and failing to detect a logger assignment is not critical.

#### Issue 2: Exception handling with continue
**Location**: `src/nicestlog/assistant.py` (migrate_directory function)
**Pattern**:
```python
for py in input_dir.rglob("*.py"):
    # Skip generated or virtual env paths
    if any(part in {".venv", "venv", "__pycache__", ".git"} for part in py.parts):
        continue
    try:
        original = py.read_text(encoding="utf-8")
    except Exception:
        continue
```

**Cleanup Strategy**:
Replace with specific exception handling for expected file reading issues:
1. Catch specific exceptions like `FileNotFoundError`, `PermissionError`, `UnicodeDecodeError`
2. Log the exception with appropriate context
3. Continue processing other files

**Risk Assessment**: Medium - May affect the migration process if files that were previously skipped now cause errors to be reported.

#### Issue 3: Exception handling with pass in systemd integration
**Location**: `src/nicestlog/systemd_integration.py` (detect_systemd_environment function)
**Pattern**:
```python
try:
    from systemd import daemon

    unit_name = daemon.booted()
    if unit_name:
        info["unit_name"] = unit_name
        if unit_name.endswith(".service"):
            info["service_name"] = unit_name[:-8]  # Remove .service suffix
except Exception:
    pass
```

**Cleanup Strategy**:
Replace with specific exception handling:
1. Catch `ImportError` for missing systemd modules
2. Catch specific systemd-related exceptions
3. Log meaningful error messages when systemd detection fails

**Risk Assessment**: Low - This is in a detection function that already handles the case where systemd is not available.

### 2.2 Legacy Code Patterns

#### Issue 1: Compatibility methods
**Location**: `src/nicestlog/advanced_assistant.py`
**Pattern**:
```python
@property
def issues(self) -> list[str]:
    """Alias for potential_issues for CLI compatibility."""
    return self.potential_issues

@property
def changes(self) -> list[str]:
    """Alias for changes_made for CLI compatibility."""
    return self.changes_made
```

**Cleanup Strategy**:
1. Remove these compatibility aliases
2. Update any code that uses these properties to use the canonical names
3. Update documentation and CLI help text if needed

**Risk Assessment**: High - Breaking change that may affect users of the API.

#### Issue 2: Legacy filtering method
**Location**: `src/nicestlog/linter.py`
**Pattern**:
```python
# Use project structure detection if provided, otherwise fall back to legacy method
if project_structure:
    # Smart filtering: only analyze source files for logging coverage
    # ...
else:
    # Legacy filtering method
    EXCLUDE_DIRS = {
        ".venv",
        "venv",
        "__pycache__",
        ".git",
        "build",
        "dist",
        "node_modules",
        ".tox",
        ".eggs",
    }
```

**Cleanup Strategy**:
1. Remove the legacy filtering method entirely
2. Ensure the project structure detection is always available or has a sensible default
3. Update tests that might depend on the legacy method

**Risk Assessment**: Medium - May affect the linter's behavior in projects without proper project structure detection.

#### Issue 3: Compatibility fields
**Location**: `src/nicestlog/core.py`
**Pattern**:
```python
# Keep for compatibility
event_dict["event"] = translated_msg
```

**Cleanup Strategy**:
1. Remove the duplicate field assignment
2. Update any code that depends on the "event" field to use "_translated_msg" instead
3. Document the breaking change

**Risk Assessment**: High - Breaking change that may affect users who rely on the "event" field containing the translated message.

#### Issue 4: Compatibility method for standard logging
**Location**: `src/nicestlog/systemd_integration.py`
**Pattern**:
```python
def emit(self, record):
    """Emit a log record to systemd journal.

    This method provides compatibility with standard Python logging handlers.
    """
```

**Cleanup Strategy**:
1. Remove this method if it's not essential for the core functionality
2. If it's needed, ensure it properly handles exceptions instead of suppressing them
3. Document any breaking changes

**Risk Assessment**: Medium - May affect users who are using nicestlog with standard Python logging handlers.

## 3. Implementation Priority

### High Priority (Must be addressed first)
1. Replace try-except blocks that suppress exceptions with proper error handling
2. Add structured logging for exceptions using `logger.exception()`

### Medium Priority (Address after high priority items)
1. Remove legacy filtering method in linter.py
2. Improve exception handling in systemd_integration.py

### Low Priority (Can be addressed last)
1. Remove compatibility methods in advanced_assistant.py
2. Remove compatibility emit method in systemd_integration.py
3. Remove compatibility fields in core.py

## 4. Breaking Changes Documentation

The following changes will be breaking changes that need to be documented:

1. **API Changes**:
   - Removal of `issues` and `changes` properties in `advanced_assistant.py`
   - Users should use `potential_issues` and `changes_made` instead

2. **Behavioral Changes**:
   - Removal of the "event" field duplication in `core.py`
   - Users should use "_translated_msg" field instead

3. **Removed Functionality**:
   - Legacy filtering method in `linter.py`
   - Compatibility `emit` method in `systemd_integration.py`

## 5. Testing Strategy

1. **Unit Tests**:
   - Add tests for exception handling paths in modified functions
   - Ensure all new exception handling code is covered by tests

2. **Integration Tests**:
   - Test the assistant module with files that cause exceptions
   - Test systemd integration in environments where systemd is not available

3. **Regression Tests**:
   - Run the full test suite to ensure no existing functionality is broken
   - Verify that the linter still works correctly with various project structures

## 6. Rollout Plan

1. **Phase 1**: Fix try-except suppression issues (1-2 days)
   - Replace all suppressed exceptions with proper error handling
   - Add logging for exceptions where appropriate

2. **Phase 2**: Remove legacy patterns with low risk (2-3 days)
   - Remove legacy filtering method
   - Improve systemd integration exception handling

3. **Phase 3**: Remove legacy patterns with high risk (3-5 days)
   - Remove compatibility methods and fields
   - Update documentation and user-facing code
   - Communicate breaking changes

4. **Phase 4**: Testing and validation (2-3 days)
   - Run full test suite
   - Address any issues discovered during testing
   - Verify that all changes work as expected