# AST Table Output Structure Analysis

## Current Two-Table Structure

When running `nicestlog check examples/`, we get two separate tables:

### Table 1: Detailed Logging Quality Report (from linter.py)
```
MODULE                      LINES  LOGS  COVERAGE  ISSUES  SUMMARY           
-----------------------------------------------------------------------------
live_editing_demo.py          153     1      0.7%  E1      Too little logging
basic_usage.py                 88     1      1.1%  E1      Too little logging
...
```

**Value**: High - provides actionable logging quality metrics
- Shows logging coverage percentage
- Identifies specific logging issues (E1, E2, W1, etc.)
- Provides meaningful summary messages
- Includes detailed issue explanations below table

### Table 2: Directory Analysis Summary (from _display_check_directory_analysis)
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━┳━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━┓
┃ File                       ┃ LOC ┃ Functions ┃ Classes ┃ Issues ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━╇━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━┩
│ live_editing_demo.py       │  88 │         2 │       0 │      0 │
│ basic_usage.py             │  60 │         2 │       0 │      0 │
...
```

**Value**: Low - mostly redundant information
- LOC already shown in first table as LINES
- Functions/Classes count not directly actionable for logging
- Issues count is always 0 (AST issues, not logging issues)
- No meaningful insights for logging improvement

## Problem Analysis

1. **Redundancy**: LOC appears in both tables
2. **Confusion**: "Issues" column in second table is misleading (always 0)
3. **Poor UX**: Two tables split user attention
4. **Lost Context**: AST metrics aren't integrated with logging insights

## Proposed Unified Structure

Merge the valuable AST metrics (Functions, Classes) into the main logging quality table:

```
MODULE                      LINES  FUNCS  CLASSES  LOGS  COVERAGE  ISSUES  SUMMARY           
------------------------------------------------------------------------------------------
live_editing_demo.py          153      2        0     1      0.7%  E1      Too little logging
basic_usage.py                 88      2        0     1      1.1%  E1      Too little logging
...
```

**Benefits**:
- Single comprehensive view
- Functions count helps understand logging coverage context
- Classes count provides code complexity context
- Maintains all actionable information
- Cleaner, more focused output

## Implementation Plan

1. Modify `_display_check_directory_analysis` to integrate with linter output
2. Remove redundant second table
3. Ensure AST insights flow into suggestions section above table
4. Test with various codebases to ensure no information loss