# AGENTS TODO - Session Management

## Current Session Goal
**CRITICAL REFACTOR**: Fix CLI command structure chaos and create proper implementation plan

## 🚨 PROBLEM IDENTIFIED
Current CLI has inconsistent command structure:
- Top-level: `migrate`, `check`, `fix`, `lint`, `review` 
- Under `tools`: `analyze-project`, `generate-service`, `init-config`
- Under `tools ast`: `analyze`, `transform`, `interactive`, `patterns`
- Under `i18n`: `check`

This is confusing and inconsistent! Need clean design.

## 📋 IMPLEMENTATION PLAN - CLI Restructure

### Phase 1: Design New Command Structure ⏳
- [x] **1.1** Analyze current commands and group logically
- [x] **1.2** Design consistent top-level structure  
- [x] **1.3** Create command hierarchy specification
- [ ] **1.4** Document migration path for existing users
- [ ] **1.5** Update help texts and documentation

#### 1.1 ANALYSIS COMPLETE ✅

**Current Command Chaos:**
```
TOP-LEVEL (11 commands):
├── docs        📚 Show documentation and examples
├── init        🔧 Initialize nicestlog configuration  
├── check       🔍 Check code for logging best practices with optional AST analysis
├── fix         🔧 Advanced code fixing with AST transformations
├── lint        🔍 Check logging coverage and quality
├── dashboard   🌐 Start the web dashboard
├── journal     📖 Beautiful systemd journal viewer
├── review      📝 Review log quality and provide suggestions
├── migrate     🔄 Migrate code using AST transformations
├── demo        🎬 Run interactive demos
└── tools       🛠️ Low-level utilities and advanced tools
    ├── init-config        🔧 Initialize nicestlog configuration (DUPLICATE!)
    ├── generate-service   🔧 Generate systemd service file
    ├── analyze-project    🔍 Analyze project for nicestlog migration opportunities
    └── ast                🔬 Advanced AST analysis and transformation
        ├── analyze        🔍 Perform deep AST analysis of Python code
        ├── transform      🔄 Transform Python code using AST patterns
        ├── interactive    🎯 Interactive AST transformation with real-time preview
        └── patterns       📋 List available AST transformation patterns
└── i18n        Internationalization utilities
    └── check   🌍 Check translation completeness and quality
```

**PROBLEMS IDENTIFIED:**
1. **Duplicate commands**: `init` vs `tools init-config`
2. **Inconsistent grouping**: AST commands buried under `tools ast`
3. **Confusing hierarchy**: 3 levels deep for common operations
4. **Agent unfriendly**: `tools analyze-project` is hard to discover
5. **Mixed abstractions**: Some commands are workflows, others are utilities

### Phase 2: Implement New Structure ⏳  
- [x] **2.1** Create new command groups in cli.py
- [x] **2.2** Move commands to appropriate groups
- [x] **2.3** Add deprecation warnings for old commands
- [x] **2.4** Update all help texts and descriptions
- [x] **2.5** Test all command paths work correctly

#### 2.1-2.3 IMPLEMENTATION COMPLETE ✅

**NEW TOP-LEVEL COMMANDS ADDED:**
- ✅ `nicestlog analyze` (was: `tools analyze-project`)
- ✅ `nicestlog init [path]` (enhanced from: `init` + `tools init-config`)

**DEPRECATED COMMANDS WITH WARNINGS:**
- ⚠️ `tools analyze-project` → redirects to `analyze`
- ⚠️ `tools init-config` → redirects to `init`
- ⚠️ `tools ast analyze` → redirects to `check --ast`
- ⚠️ `tools ast transform` → redirects to `fix --ast`
- ⚠️ `tools ast interactive` → redirects to `fix --interactive`
- ⚠️ `tools ast patterns` → shows deprecation warning

**AGENT-FRIENDLY IMPROVEMENTS:**
- `analyze` is now prominent top-level command
- `--json` flag for clean agent output
- Enhanced `init` works with any project path
- Clear deprecation messages with exact replacements

### Phase 3: Update Documentation ⏳
- [ ] **3.1** Update README.md with new command structure
- [ ] **3.2** Update user guide documentation
- [ ] **3.3** Update agent migration templates
- [ ] **3.4** Update examples to use new commands
- [ ] **3.5** Create migration guide for existing users

### Phase 4: Testing & Validation ⏳
- [ ] **4.1** Test all commands work as expected
- [ ] **4.2** Test backward compatibility warnings
- [ ] **4.3** Update integration tests
- [ ] **4.4** Validate agent workflows still work
- [ ] **4.5** Performance test command loading

#### 1.2 NEW STRUCTURE DESIGN ✅

**CLEAN COMMAND STRUCTURE:**
```
nicestlog
├── analyze [path]              # 🔍 Project analysis (was: tools analyze-project)
├── migrate [path]              # 🔄 Code migration (existing)
├── check [path]                # 🔍 Code quality check (existing) 
├── fix [path]                  # 🔧 Auto-fix issues (existing)
├── init [path]                 # 🔧 Initialize config (merge: init + tools init-config)
├── docs                        # 📚 Documentation (existing)
├── demo                        # 🎬 Demos (existing)
├── review [path]               # 📝 Log quality review (existing)
├── lint [path]                 # 🔍 Linting (existing)
├── dashboard                   # 🌐 Web dashboard (existing)
├── journal                     # 📖 Journal viewer (existing)
└── i18n
    └── check                   # 🌍 Translation check (existing)
```

**DESIGN PRINCIPLES:**
1. **Flat hierarchy**: Max 2 levels (except specialized i18n)
2. **Verb-based naming**: All commands are actions
3. **Logical flow**: analyze → migrate → check → fix
4. **Agent-first**: `analyze` is prominent and discoverable
5. **Consistency**: All path-based commands follow same pattern

**COMMAND CATEGORIES:**
- **Analysis**: `analyze`, `check`, `lint`, `review`
- **Transformation**: `migrate`, `fix`
- **Setup**: `init`
- **Utilities**: `docs`, `demo`, `dashboard`, `journal`
- **Specialized**: `i18n check`

**REMOVED/MERGED:**
- ❌ `tools generate-service` → Remove (niche utility)
- ❌ `tools ast *` → Integrate into `check --ast`, `fix --ast`
- ✅ `tools init-config` → Merge into `init`
- ✅ `tools analyze-project` → Promote to `analyze`

#### 1.3 COMMAND HIERARCHY SPECIFICATION ✅

**DETAILED COMMAND SPECIFICATION:**

```yaml
# nicestlog CLI Command Specification v2.0

commands:
  analyze:
    description: "🔍 Analyze project for nicestlog migration opportunities"
    args: ["path"]
    options:
      - "--output/-o": "Output JSON file"
      - "--verbose/-v": "Verbose output"
      - "--json": "JSON output for agents"
    examples:
      - "nicestlog analyze ."
      - "nicestlog analyze /path/to/project --json"
      - "nicestlog analyze . --output analysis.json"
    migration_from: "tools analyze-project"
    
  migrate:
    description: "🔄 Migrate code using AST transformations"
    args: ["path"]
    options:
      - "--type/-t": "Migration type (print-to-structlog, logging-to-structlog)"
      - "--dry-run": "Preview changes"
      - "--interactive/-i": "Interactive mode"
      - "--backup/--no-backup": "Create backup files"
    examples:
      - "nicestlog migrate . --type print-to-structlog --dry-run"
      - "nicestlog migrate src/ --interactive"
    migration_from: "migrate (existing)"
    
  check:
    description: "🔍 Check code for logging best practices"
    args: ["path"]
    options:
      - "--fix": "Auto-fix issues"
      - "--ast": "Enable AST analysis"
      - "--interactive/-i": "Interactive mode"
      - "--complexity": "Check complexity"
      - "--pattern": "Specific patterns"
    examples:
      - "nicestlog check ."
      - "nicestlog check . --ast --fix"
      - "nicestlog check . --interactive"
    migration_from: "check (existing) + tools ast analyze"
    
  fix:
    description: "🔧 Auto-fix logging issues with AST transformations"
    args: ["path"]
    options:
      - "--dry-run": "Preview fixes"
      - "--interactive/-i": "Interactive fixing"
      - "--backup/--no-backup": "Create backup files"
      - "--pattern": "Specific patterns to fix"
    examples:
      - "nicestlog fix . --dry-run"
      - "nicestlog fix src/ --interactive"
    migration_from: "fix (existing) + tools ast transform"
    
  init:
    description: "🔧 Initialize nicestlog configuration"
    args: ["[path]"]
    options:
      - "--template": "Configuration template"
      - "--force": "Overwrite existing config"
    examples:
      - "nicestlog init"
      - "nicestlog init /path/to/project"
    migration_from: "init + tools init-config (merged)"
    
  # Utility commands (unchanged)
  docs:
    description: "📚 Show documentation and examples"
    migration_from: "docs (existing)"
    
  demo:
    description: "🎬 Run interactive demos"
    migration_from: "demo (existing)"
    
  review:
    description: "📝 Review log quality and provide suggestions"
    migration_from: "review (existing)"
    
  lint:
    description: "🔍 Check logging coverage and quality"
    migration_from: "lint (existing)"
    
  dashboard:
    description: "🌐 Start the web dashboard"
    migration_from: "dashboard (existing)"
    
  journal:
    description: "📖 Beautiful systemd journal viewer"
    migration_from: "journal (existing)"

subcommands:
  i18n:
    description: "🌍 Internationalization utilities"
    commands:
      check:
        description: "Check translation completeness and quality"
        migration_from: "i18n check (existing)"

deprecated_commands:
  tools:
    deprecation_message: "Use top-level commands instead"
    replacements:
      "tools analyze-project": "analyze"
      "tools init-config": "init"
      "tools ast analyze": "check --ast"
      "tools ast transform": "fix --ast"
      "tools ast interactive": "fix --interactive"
      "tools ast patterns": "check --ast --help"
    removal_version: "v2.0.0"
```

**BACKWARD COMPATIBILITY STRATEGY:**
1. **Deprecation warnings**: Show for 2 minor versions
2. **Alias support**: Old commands redirect to new ones
3. **Clear migration messages**: Tell users exact replacement
4. **Documentation**: Update immediately, keep old examples with warnings

## 🔧 TECHNICAL IMPLEMENTATION NOTES

### Command Mapping
- `tools analyze-project` → `analyze`
- `tools init-config` → `init` 
- `tools generate-service` → Remove (rarely used, can be separate tool)
- `tools ast *` → Integrate into `check --ast`, `fix --ast`
- All others stay at top-level

### Backward Compatibility
- Keep old commands with deprecation warnings for 2 versions
- Provide clear migration messages
- Update all documentation immediately

### Testing Strategy
- Unit tests for each command
- Integration tests for workflows
- Backward compatibility tests
- Agent workflow validation tests

## 🎯 SUCCESS CRITERIA
- [ ] All commands have consistent structure
- [ ] Agent workflows use clean `nicestlog analyze` command
- [ ] Documentation is updated and clear
- [ ] Backward compatibility maintained with warnings
- [ ] Performance is maintained or improved
- [ ] All tests pass

## Session Notes
- **CRITICAL ISSUE**: CLI structure is inconsistent and confusing
- **ROOT CAUSE**: Organic growth without design principles
- **SOLUTION**: Clean redesign with proper implementation plan
- **PRIORITY**: High - affects all user and agent interactions

## Previous Session Achievements (Completed)
- ✅ Agent Migration Guide created
- ✅ Project Analyzer Tool implemented
- ✅ Migration Templates documented
- ✅ Agent Demo working
- ✅ JSON output for programmatic consumption
- ✅ Decision trees and risk assessment
- ✅ Step-by-step workflows