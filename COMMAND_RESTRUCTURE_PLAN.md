# Nicestlog Command Structure Restructuring Plan

## 🎯 Goal
Simplify command structure from 11 top-level commands to 8, with clearer user workflows and better organization.

## 📊 Current State (Before)

```
nicestlog (11 top-level + 5 subcommands = 16 total)
├── docs                    # Documentation viewer
├── init-config            # Configuration setup
├── lint                   # Code analysis (logging coverage)
├── dashboard              # Web interface
├── generate-service       # Systemd service generation
├── journal                # Systemd journal viewer
├── review                 # Log file quality analysis
├── demo                   # Feature demonstrations
├── assistant              # Print statement migration
├── i18n                   # Internationalization
│   └── check              # Translation validation
└── ast                    # Advanced AST operations
    ├── analyze            # Code analysis
    ├── transform          # Code transformation
    ├── interactive        # Interactive editing
    └── patterns           # Pattern management
```

## 🎯 Target State (After)

```
nicestlog (8 top-level + 7 subcommands = 15 total)
├── check          # 🔍 Unified analysis (lint + i18n + ast insights)
├── fix            # 🔧 Auto-fixes for nicestlog users (ruff-style)
├── migrate        # 🚀 Assisted migration for new users
├── review         # 📊 Log file analysis
├── dashboard      # 🌐 Web interface
├── journal        # 📰 Journal viewer
├── docs           # 📚 Documentation
├── demo           # 🎮 Demos
└── tools          # 🛠️ Low-level utilities
    ├── ast        # 🔬 Advanced AST operations
    │   ├── analyze
    │   ├── transform
    │   ├── interactive
    │   └── patterns
    ├── init-config
    └── generate-service
```

## 🔄 Migration Plan

### Phase 1: Create New Commands

#### 1.1 `nicestlog fix` (NEW)
**Purpose**: Auto-fix nicestlog-specific issues for existing users
**Target Users**: Projects already using nicestlog
**Functionality**:
- Automatic logging level corrections (log.info → log.debug for library internals)
- Fix inefficient log patterns
- Add missing log context
- Correct structlog usage patterns

**Options**:
```bash
nicestlog fix [PATH]                 # Fix all detected issues
nicestlog fix --levels              # Only fix logging levels
nicestlog fix --patterns            # Only fix log patterns
nicestlog fix --dry-run             # Preview changes without applying
nicestlog fix --interactive         # Confirm each change
```

**Backend**: Uses AST transformation engine internally

#### 1.2 `nicestlog migrate` (NEW)
**Purpose**: Assisted migration for projects adopting nicestlog
**Target Users**: New nicestlog adopters
**Functionality**:
- Convert print() statements to log.info()
- Migrate from stdlib logging to structlog
- Setup configuration files
- Fix import statements

**Options**:
```bash
nicestlog migrate [PATH]             # Full migration wizard
nicestlog migrate --from=print      # Only convert print statements
nicestlog migrate --from=logging    # Migrate from stdlib logging
nicestlog migrate --interactive     # Step-by-step guidance
nicestlog migrate --dry-run         # Preview changes
```

**Backend**: Uses existing AST transform infrastructure + print_to_structlog pattern

#### 1.3 Enhance `nicestlog check` (EXISTING)
**Current**: Already combines lint + i18n + logging level analysis
**Enhancement**: Add optional AST insights internally
**No API changes needed**: Already works as unified analysis command

### Phase 2: Reorganize Existing Commands

#### 2.1 Move to `tools` namespace
- `ast` → `tools ast` (preserve all functionality)
- `init-config` → `tools init-config`
- `generate-service` → `tools generate-service`

#### 2.2 Deprecate redundant commands
- `assistant` → Add deprecation warning, redirect to `migrate --from=print`
- `i18n check` → Keep working, but promote `check` command instead

### Phase 3: Update Help and Documentation

#### 3.1 Main help reorganization
Promote workflow commands first:
```
Main Workflows:
  check          🔍 Analyze code quality (lint + i18n + logging)
  fix            🔧 Auto-fix nicestlog issues
  migrate        🚀 Migrate to nicestlog

Standalone Tools:
  review         📊 Analyze log files
  dashboard      🌐 Web interface
  journal        📰 Systemd journal viewer
  docs           📚 Documentation
  demo           🎮 Feature demonstrations

Advanced:
  tools          🛠️ Low-level utilities and AST operations
```

#### 3.2 Add command suggestions
- When user runs deprecated command, suggest new equivalent
- Add "Did you mean?" suggestions for common typos

## 🎯 User Workflows

### Workflow 1: Existing nicestlog user wants to improve code quality
```bash
nicestlog check src/           # "What's wrong?"
nicestlog fix src/             # "Fix it automatically!"
```

### Workflow 2: New user wants to adopt nicestlog
```bash
nicestlog migrate --from=print src/    # "Help me switch to nicestlog"
nicestlog check src/                   # "Is everything correct now?"
nicestlog fix src/                     # "Fix any remaining issues"
```

### Workflow 3: Power user needs custom AST operations
```bash
nicestlog tools ast analyze src/       # Deep analysis
nicestlog tools ast patterns --list    # Manage custom patterns
nicestlog tools ast interactive src/   # Manual editing
```

### Workflow 4: DevOps setup
```bash
nicestlog tools init-config            # Setup configuration
nicestlog tools generate-service       # Create systemd service
nicestlog dashboard                    # Monitor logs
```

## 🔧 Implementation Details

### Backend Architecture
- `fix` and `migrate` both use the existing AST transformation engine
- `check` already combines multiple analysis tools
- `tools ast` preserves all current AST functionality
- No breaking changes to core functionality

### Backwards Compatibility
- All existing commands continue to work during transition period
- Deprecation warnings guide users to new commands
- Aliases can be added for smooth migration

### Command Mapping
| Old Command | New Command | Status |
|-------------|-------------|---------|
| `lint` | `check` | Integrated |
| `i18n check` | `check` | Integrated |
| `assistant` | `migrate --from=print` | Deprecated |
| `ast *` | `tools ast *` | Moved |
| `init-config` | `tools init-config` | Moved |
| `generate-service` | `tools generate-service` | Moved |
| `review` | `review` | Unchanged |
| `dashboard` | `dashboard` | Unchanged |
| `journal` | `journal` | Unchanged |
| `docs` | `docs` | Unchanged |
| `demo` | `demo` | Unchanged |

## 📈 Benefits

### For Users
1. **Clearer workflows**: check → fix → migrate
2. **Reduced cognitive load**: 8 main commands instead of 11
3. **Better discoverability**: Related functionality grouped together
4. **Ruff-style familiarity**: `fix` command works like `ruff --fix`

### For Developers
1. **Logical organization**: Tools grouped by purpose
2. **No lost functionality**: Everything preserved under new structure
3. **Easier maintenance**: Related code grouped together
4. **Better testing**: Clear separation of concerns

## 🚀 Implementation Order

1. **Phase 1**: Implement `fix` and `migrate` commands
2. **Phase 2**: Move commands to `tools` namespace with aliases
3. **Phase 3**: Add deprecation warnings and update help
4. **Phase 4**: Update documentation and examples
5. **Phase 5**: Remove deprecated commands in next major version

## ✅ Success Metrics

- [ ] `nicestlog fix` successfully auto-fixes logging level issues
- [ ] `nicestlog migrate` successfully converts print() statements
- [ ] All existing functionality preserved under new structure
- [ ] Help system clearly guides users to appropriate commands
- [ ] No breaking changes for existing users during transition
- [ ] Documentation updated to reflect new structure

## 🎯 Final Result

**From**: 11 confusing top-level commands with unclear relationships
**To**: 8 well-organized commands with clear user workflows

Users will have:
- **3 main workflow commands**: check, fix, migrate
- **4 standalone tools**: review, dashboard, journal, docs, demo
- **1 power-user namespace**: tools (with ast, init-config, generate-service)

This structure makes nicestlog more approachable for new users while preserving all power-user functionality.