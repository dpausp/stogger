# Unused Code Analysis Report

## Summary
Found 147 unused code items in project files (excluding .venv dependencies).

## Analysis by Category

### 1. docs/conf.py (32 items)
**Status: KEEP - These are Sphinx configuration variables**
- All variables (project, copyright, author, release, extensions, etc.) are used by Sphinx
- Vulture doesn't understand Sphinx's configuration system
- **Decision: No action needed**

### 2. dodo.py (25 items) 
**Status: KEEP - These are dodo task definitions**
- Functions like `task_install`, `task_format`, `task_lint`, etc. are dodo tasks
- They're called by the dodo task runner system, not directly in Python
- **Decision: No action needed - these are intentionally available tasks**

### 3. src/nicestlog/advanced_assistant.py (12 items)
**Status: MIXED - Some constants unused, some methods potentially valuable**

#### Unused Constants (Lines 31-54):
- `TransformationStage` enum class and its values
- AST node type constants (`CLASS_DEF`, `IMPORT`, `ASSIGN`, etc.)
- **Decision: REVIEW - These might be for future features or could be removed**

#### Unused Variables/Methods:
- Line 148: `rollback_data` - might be incomplete feature
- Line 868: `transform_directory` method - could be valuable public API
- **Decision: INVESTIGATE - Check if these should be exposed or removed**

### 4. src/nicestlog/assistant.py (2 items)
**Status: INVESTIGATE**
- Line 25: `files_transformed` variable
- Line 267: `files_transformed` attribute
- **Decision: REVIEW - Might be incomplete tracking feature**

### 5. src/nicestlog/cli.py (13 items)
**Status: MIXED - Some are CLI commands, some are internal functions**

#### CLI Commands (potentially valuable):
- `tools_generate_service`, `tools_review`, `tools_journal`, `tools_dashboard`
- `i18n_check`, `docs`, `init_config_cmd`, `check`, `migrate`, `tools_demo`
- **Decision: REVIEW - These might be incomplete CLI features**

#### Internal Functions:
- Various `_analyze_*` and `_transform_*` functions
- **Decision: INVESTIGATE - Might be dead code from refactoring**

### 6. src/nicestlog/config.py (8 items)
**Status: INVESTIGATE - Configuration attributes**
- Various config attributes like `log_cmd_output`, `enable_systemd`, etc.
- **Decision: REVIEW - These might be planned features or dead config**

### 7. Other src/ files (9 items)
**Status: MIXED**
- Various unused functions and variables across multiple files
- **Decision: CASE-BY-CASE analysis needed**

### 8. tests/ (46 items)
**Status: MOSTLY CLEANUP - Test artifacts and mock objects**
- Many unused mock attributes and variables
- Some unused test fixtures
- **Decision: SAFE TO REMOVE most test artifacts**

## Recommendations

### High Priority (Likely Dead Code):
1. Test mock artifacts - safe to remove
2. Unused variables in functions - likely dead code
3. Some internal CLI functions - might be refactoring artifacts

### Medium Priority (Investigate):
1. CLI command functions - might be incomplete features
2. Config attributes - might be planned features
3. Assistant tracking variables - might be incomplete features

### Low Priority (Likely Keep):
1. Advanced assistant constants - might be for future use
2. Public methods like `transform_directory` - might be valuable API

## Next Steps
1. Review each category systematically
2. Check git history for context on when code was added
3. Look for TODO comments or documentation mentioning these features
4. Remove obvious dead code (test artifacts)
5. Document decisions for borderline cases