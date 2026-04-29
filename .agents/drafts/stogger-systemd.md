---
lifecycle:
  requirements:
    completed_at: "2026-04-27T17:42:24Z"
    git_rev: "49277ec"
---

## Problem

Services running under systemd that use stogger produce redundant metadata in `journalctl` output: journalctl adds its own timestamp and level header, while stogger's `ConsoleFileRenderer` adds another timestamp and level indicator. The result looks like `2026-04-27T18:33:50+0200 1088556649473 svc INFO 2026-04-27T16:33:50Z I event-name` — double timestamps, double levels.

The root cause: stogger's `init_logging()` already suppresses console output when `JOURNAL_STREAM` is detected, but `JournalLoggerFactory` is a stub returning None — there is no real journal writer. Without structured `journal.send()` calls, rendered messages have no direct journal destination. The `SystemdJournalRenderer` correctly formats data for journal consumption, but nothing actually sends it to the journal.

Extracting the journal I/O into `stogger-systemd` fixes this: the real `JournalLogger` calls `journal.send()` with properly structured fields, console output is suppressed under systemd, and `journalctl` displays clean single-source entries. This also isolates the Linux-only `systemd-python` dependency from core stogger.

## Binding Decisions

### scope-split

#### Context
Core currently holds both journal data transformation (`SystemdJournalRenderer`, `JOURNAL_LEVELS`, `KEYS_TO_SKIP_IN_JOURNAL_MESSAGE`) and a stub journal logger factory. The real journal I/O (writing to systemd journal via `journal.send()`) needs a Linux-only dependency that should not burden all stogger users.

#### Decision
Only the I/O layer moves to `stogger-systemd`: `JournalLogger` (with `journal.send()`), `DummyJournalLogger`, and the real `JournalLoggerFactory`. The `SystemdJournalRenderer`, `JOURNAL_LEVELS`, `KEYS_TO_SKIP_IN_JOURNAL_MESSAGE`, and `syslog` import remain in core — they are pure data transformation with no platform-specific dependencies.

#### Alternatives
- **Full extraction**: Move renderer + levels + factory out entirely. Rejected because the renderer produces data that core's `MultiRenderer` consumes; moving it would require a plugin mechanism in core for what is ultimately just dict formatting.
- **Everything out including syslog constants**: Rejected because `syslog` is in Python stdlib on all platforms, and the renderer is useful in tests without needing actual journal I/O.

#### Consequences
Core keeps ~60 lines of journal-related formatting code. The new package is a thin I/O shim (~30 lines). The `JournalLoggerFactory` stub in core remains as fallback.

### integration-hook

#### Context
When `stogger-systemd` is installed, stogger core must discover and use the real journal logger factory instead of the stub.

#### Decision
Dynamic import in `init_logging()`: when `enable_systemd=True` (default), core attempts `from stogger_systemd import get_journal_logger_factory`. Falls back to the existing stub on `ImportError`. Zero-config for users — install the package and it works.

#### Alternatives
- **Entry point plugin**: `stogger-systemd` registers via `[project.entry-points."stogger.factories"]`. Rejected as over-engineering for a single integration point.
- **Explicit import side-effect**: User writes `import stogger_systemd` to register. Rejected because it breaks "install and it works" DX.

#### Consequences
Single try/except block in `init_logging()`. The import path `stogger_systemd.get_journal_logger_factory` is the stable contract between the two packages.

### fallback-behavior

#### Context
Most stogger users run on non-systemd systems or don't need journal integration. The fallback must be graceful.

#### Decision
When `JOURNAL_STREAM` env var is detected (running under systemd) but `stogger-systemd` is not installed: emit a one-time info-level message "systemd journal detected but stogger-systemd not available. Install stogger-systemd package for journal integration." No pip/package-manager mention. On non-systemd systems: silent skip (current stub behavior).

#### Alternatives
- **Silent skip always**: Rejected because NixOS/systemd users who expect journal output would have no indication it's missing.
- **Hard error**: Rejected because this would break existing setups that never used journal.

#### Consequences
One conditional info message in `init_logging()` when `JOURNAL_STREAM` is set. The message is informational, not a warning — journal is an optional target.

### dependency-isolation

#### Context
The new package needs both stogger (for the factory interface) and systemd-python (for journal I/O).

#### Decision
`stogger-systemd` has hard dependencies on `stogger` and `systemd-python`. Both are required.

#### Alternatives
- **systemd-python as optional dep**: Rejected because the package is useless without it.
- **No stogger dep**: Rejected because the factory must conform to stogger's logger interface.

#### Consequences
Simple dependency chain: user → stogger + stogger-systemd → systemd-python. Clean `pip install stogger-systemd` on Linux pulls everything needed.

### remaining-stubs

#### Context
Core must continue working without the extra package installed. Existing public API must remain stable.

#### Decision
Core keeps: `JournalLoggerFactory` stub (returns None), `SystemdJournalRenderer`, `JOURNAL_LEVELS`, `KEYS_TO_SKIP_IN_JOURNAL_MESSAGE`, `syslog` import. Minimal change to existing public API — no removals, only the stub gains a dynamic import attempt.

#### Alternatives
- **Generic extra-loading mechanism**: Core gets `load_extra("systemd")`. Rejected as premature abstraction — stogger-eliot would need a different integration pattern anyway.
- **Remove all journal knowledge from core**: Rejected because the renderer is needed regardless of whether journal I/O is available.

#### Consequences
No breaking changes to core's public API. `__init__.py` exports remain the same.

### versioning-strategy

#### Context
The workspace already uses hatch-vcs with shared version from the monorepo root.

#### Decision
Same VCS version as stogger. `stogger-systemd` uses `hatch-vcs` with `root = "../.."` — one git tag, all workspace packages get the same version. Compatible versions have identical version numbers.

#### Alternatives
- **Independent semver**: Rejected because users would need to track a compatibility matrix.
- **Loose pin on stogger major**: Rejected as fragile when stogger internals change.

#### Consequences
Workspace `pyproject.toml` gains a third member: `members = ["packages/stogger", "packages/pytest-stogger", "packages/stogger-systemd"]`. One release tag updates all packages.

### api-contract

#### Context
Core needs a stable, minimal interface to import from the extra package.

#### Decision
`stogger-systemd` exports one factory function: `get_journal_logger_factory()` returning a `JournalLoggerFactory` instance (compatible with structlog's logger factory interface). Plus `JournalLogger` and `DummyJournalLogger` as importable classes. The function signature: `get_journal_logger_factory() -> JournalLoggerFactory`.

#### Alternatives
- **Bare JournalLogger class**: Core would need to instantiate it, coupling core to the class constructor. Rejected.
- **Whole module as plugin**: Core imports module and accesses attributes dynamically. Rejected — no explicit contract.

#### Consequences
Single integration point. Core code in `init_logging()`: `factory = get_journal_logger_factory()` then `loggers["journal"] = factory`.

### non-linux-support

#### Context
`systemd-python` only installs on Linux. The package is meaningless on macOS/Windows.

#### Decision
`stogger-systemd` is Linux-only. Platform classifier `Operating System :: POSIX :: Linux`. No stubs or workarounds for other platforms.

#### Alternatives
- **Conditional dep with no-op stub**: Rejected because a package that installs but does nothing is confusing.
- **Pure stub wheel for non-Linux**: Rejected as unnecessary overhead.

#### Consequences
`pip install stogger-systemd` fails gracefully on non-Linux (dependency resolution error for systemd-python). This is correct behavior — journal doesn't exist on those platforms.

### migration-notice

#### Context
Existing stogger users may wonder if this is a breaking change.

#### Decision
No breaking change. stogger core never delivered actual journal I/O (the stub returned None). No changelog entry about removed functionality needed — at most a "New: stogger-systemd package available" note.

#### Alternatives
- **Minor changelog entry**: Acceptable but not required since nothing was removed.
- **Major version bump**: Rejected as overkill — no existing behavior changes.

#### Consequences
Stogger stays on its current version. `stogger-systemd` is a pure addition.

## Appendix

### Scope summary
- New package: `packages/stogger-systemd/` with `src/stogger_systemd/` layout
- Modified: `stogger/core.py` `init_logging()` (add dynamic import + JOURNAL_STREAM info message)
- Modified: root `pyproject.toml` workspace members
- Unchanged: `SystemdJournalRenderer`, `MultiRenderer`, `MultiOptimisticLogger`, `ConsoleFileRenderer`, all other renderers

### Interface contracts

**stogger-systemd public API:**
```python
# stogger_systemd/__init__.py
def get_journal_logger_factory() -> JournalLoggerFactory: ...
class JournalLogger: ...      # actual journal.send() writer
class DummyJournalLogger: ... # no-op fallback
class JournalLoggerFactory: ... # factory creating JournalLogger instances
```

**Core integration point (in init_logging):**
```python
if log_to_console and os.environ.get("JOURNAL_STREAM"):
    # Running under systemd — check if journal extra is available
    try:
        from stogger_systemd import get_journal_logger_factory
        loggers["journal"] = get_journal_logger_factory()
    except ImportError:
        log.info("systemd-journal-detected-no-extra")
elif enable_systemd:
    try:
        from stogger_systemd import get_journal_logger_factory
        loggers["journal"] = get_journal_logger_factory()
    except ImportError:
        pass  # Silent skip when not running under systemd
```

### Error communication
- JOURNAL_STREAM set + no stogger-systemd: info-level "systemd journal detected but stogger-systemd not available. Install stogger-systemd package for journal integration."
- Non-Linux install attempt: standard pip/uv error (systemd-python dependency unresolvable)
- Runtime journal.send() failure: caught by MultiOptimisticLogger (existing behavior — optimistic logging never crashes the host)

### Edge cases
- stogger-systemd installed but not running under systemd: JournalLogger created but messages go to journal anyway (journald accepts them from any process). Not a problem.
- enable_systemd=False in config: dynamic import skipped entirely, no journal target added
- Multiple init_logging() calls: structlog.configure() replaces config; no duplicate loggers
