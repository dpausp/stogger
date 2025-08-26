# Unified AST Analysis Table Design

## Current Problem
- Two separate tables confuse users and split attention
- Second table has misleading "Issues" column (always 0 for AST issues)
- Redundant LOC information between tables
- AST insights not integrated with logging quality metrics

## Proposed Unified Table Schema

### Enhanced Logging Quality Table
Extend the existing valuable logging quality table from linter.py with AST metrics:

```
MODULE                      LINES  FUNCS  CLASSES  LOGS  COVERAGE  ISSUES  SUMMARY           
------------------------------------------------------------------------------------------
live_editing_demo.py          153      2        0     1      0.7%  E1      Too little logging
basic_usage.py                 88      2        0     1      1.1%  E1      Too little logging
agent_migration_demo.py       214      5        0     1      0.5%  E2      Too little logging
eliot_demo.py                  84      3        0     0      0.0%  E2      Too little logging
...
```

### Column Mapping
- **MODULE**: Keep as-is (file name)
- **LINES**: Keep from linter (code lines, not total lines)
- **FUNCS**: NEW - Add from AST analysis (function count)
- **CLASSES**: NEW - Add from AST analysis (class count) 
- **LOGS**: Keep from linter (log statements count)
- **COVERAGE**: Keep from linter (logging coverage %)
- **ISSUES**: Keep from linter (E1, E2, W1, etc.)
- **SUMMARY**: Keep from linter (actionable summary text)

### Benefits of Unified Design
1. **Context-Rich**: Functions count helps understand if low logging coverage is due to few functions vs many functions without logs
2. **Single View**: All metrics in one place for better decision making
3. **Actionable**: Maintains all the valuable issue categorization and suggestions
4. **Clean**: Removes confusing redundant table

### AST Insights Integration
Instead of a separate table, integrate AST insights into the suggestions section:

```
🔧 LOGGING LEVEL ISSUES DETECTED
The following log.info() calls should be log.debug() for library internal operations:

📄 advanced_assistant_demo.py:
   Line 365: log.error('demo-failed')
   Suggested: log.exception('demo-failed')
   Reason: Inside except: prefer log.exception(...) or pass exc_info=True to include traceback

💡 AST Analysis Insights:
  • 13 files analyzed with 39 total functions
  • Average 3 functions per file suggests good code organization
  • Consider adding structured logging to functions without logs
  • No complex code patterns detected that would hinder logging adoption
```

## Implementation Strategy

### Phase 1: Modify linter.py output
- Extend `lint_directory` to accept and display AST metrics
- Add FUNCS and CLASSES columns to the existing table
- Preserve all existing functionality and formatting

### Phase 2: Modify cli.py integration  
- Pass AST analysis results to `lint_directory` 
- Remove `_display_check_directory_analysis` call
- Add AST insights to suggestions section

### Phase 3: Clean up
- Remove redundant second table display
- Ensure no information loss
- Test with various codebases

## Backward Compatibility
- JSON/TOML output formats remain unchanged
- All existing issue detection and categorization preserved
- Command-line flags and behavior unchanged
- Only visual presentation improved