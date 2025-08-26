# Current CLI Command Structure Analysis

## Current Top-Level Commands

**Core Commands (should stay at top level):**
- `check` - Code analysis for logging best practices (CORE)
- `fix` - Advanced code fixing with AST transformations (CORE) 
- `migrate` - Project analysis and code migration (CORE)
- `init` - Initialize nicestlog configuration (CORE)
- `docs` - Show documentation and examples (CORE)

**Specialized Commands (should move to tools):**
- `review` - Review log quality and provide suggestions (SPECIALIZED)
- `journal` - Beautiful systemd journal viewer (SPECIALIZED)
- `dashboard` - Start the web dashboard (SPECIALIZED, Flask-dependent)
- `demo` - Run interactive demos (SPECIALIZED)

**Already in Tools:**
- `tools generate-service` - Generate systemd service file

**Subgroups:**
- `i18n check` - Check translation completeness (SPECIALIZED)

## Proposed New Structure

```
nicestlog
├── check                    # CORE: Logging analysis + AST + complexity
├── fix                      # CORE: Auto-fixing with transformations  
├── migrate                  # CORE: Code migration assistance
├── init                     # CORE: Configuration setup
├── docs                     # CORE: Documentation viewer
└── tools                    # Specialized utilities
    ├── review               # Log quality analysis
    ├── journal              # Systemd journal viewer
    ├── dashboard            # Web dashboard (Flask optional)
    ├── demo                 # Feature demonstrations
    ├── generate-service     # Systemd service generation (already here)
    └── i18n                 # Internationalization tools
        └── check            # Translation checking
```

## Benefits

1. **Cleaner main interface** - 5 core commands vs 9+ currently
2. **Better discoverability** - Core functions immediately visible
3. **Logical grouping** - Specialized tools grouped together
4. **Consistent with existing pattern** - `tools generate-service` already exists
5. **Easier maintenance** - Clear separation of concerns

## Migration Impact

Users will need to update:
- `nicestlog review` → `nicestlog tools review`
- `nicestlog journal` → `nicestlog tools journal` 
- `nicestlog dashboard` → `nicestlog tools dashboard`
- `nicestlog demo` → `nicestlog tools demo`
- `nicestlog i18n check` → `nicestlog tools i18n check`

Core commands remain unchanged.