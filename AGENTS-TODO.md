# AGENTS TODO - Session Management

## Current Session Goal
🧹 **CLI Entschlackung** - Remove legacy/unnecessary CLI commands and options. No legacy users to worry about - clean slate approach.

## Analysis: CLI Commands to Remove/Simplify

### DEPRECATED Commands Found (✅ REMOVED!)
- [x] **`analyze`** (line 84-111) - redirects to `migrate`, completely redundant
- [x] **`tools init-config`** (line 58-65) - redirects to `init`, just remove it  
- [x] **`tools analyze-project`** (line 114-142) - redirects to `migrate --json`, redundant
- [x] **`tools ast`** (entire subapp, line 249-250) - redirects to main commands
- [x] **`ast_analyze_deprecated`** (line 805-843) - redirects to `check --ast`
- [x] **`ast_transform_deprecated`** (line 846-875) - redirects to `fix --ast`
- [x] **`ast_interactive_deprecated`** (line 878-900) - redirects to `fix --interactive`
- [x] **`ast_patterns_deprecated`** (line 903-918) - redirects to help text

### 🎉 Results
- **179 lines of code removed** (2612 → 2433 lines)
- **8 deprecated commands eliminated**
- **5 test classes/methods removed** (for deleted commands)
- CLI is now clean and focused
- Only `tools generate-service` remains (actually useful)
- All tests passing ✅

### Potential Simplifications
- [ ] **`tools` subgroup** - evaluate if all tools commands are necessary
- [ ] **Complex parameter combinations** - simplify overly complex command signatures
- [ ] **Redundant options** - remove duplicate functionality

### Files to Check/Modify
- `src/nicestlog/cli.py` - main CLI file (2612 lines - very large!)
- Check for other CLI-related files
- Update help texts and documentation

### Next Steps
1. ✅ Scan full CLI structure and identify all deprecated/legacy items
2. ✅ Remove deprecated commands without breaking changes  
3. [x] **Fix failing tests** - remove tests for deleted commands
4. [ ] Simplify complex command signatures (if needed)
5. [ ] Update documentation

## Session Notes
- CLI has 2612 lines - definitely needs cleanup
- Found immediate candidates: `tools init-config` and `analyze` commands
- No legacy users means we can be aggressive with cleanup