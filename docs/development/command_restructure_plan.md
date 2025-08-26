# Nicestlog Command Structure Restructuring Plan (Proposal)

Status: Proposal document. Some ideas may be partially implemented, others not yet. This page exists to track the direction and for future planning.

## Goal
Simplify command structure from 11 top-level commands to 8, with clearer user workflows and better organization.

## Current State (Before)

```
nicestlog (11 top-level + 5 subcommands = 16 total)
├── docs                    # Documentation viewer
├── init-config            # Configuration setup
├── check                  # Code analysis (logging coverage + AST + complexity)
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
    └── patterns           # Pattern management
```

## Target State (After)

```
nicestlog (8 top-level + 7 subcommands = 15 total)
├── check          # Unified analysis (logging coverage + i18n + ast insights)
├── fix            # Auto-fixes for nicestlog users (ruff-style)
├── migrate        # Assisted migration for new users
├── review         # Log file analysis
├── dashboard      # Web interface
├── journal        # Journal viewer
├── docs           # Documentation
├── demo           # Demos
└── tools          # Low-level utilities
    ├── ast        # Advanced AST operations
    │   ├── analyze
    │   ├── transform
    │   └── patterns
    ├── init-config
    └── generate-service
```

## Migration Plan (High level)

Phase 1: Create new commands
- nicestlog fix (NEW): Auto-fix nicestlog-specific issues for existing users
- nicestlog migrate (NEW): Assisted migration for projects adopting nicestlog
- Enhance nicestlog check: Add optional AST insights internally

Phase 2: Reorganize existing commands
- Move low-level utilities under tools
- Deprecate redundant commands where appropriate

Phase 3: Update help and documentation

Note: As of now, not all targets are implemented. The `ast` subcommands (analyze/transform/patterns) exist; `fix`/`migrate` are planned.
