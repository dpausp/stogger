# stogger-systemd

## Context

Services running under systemd produce redundant metadata in journalctl — double timestamps and level indicators because journalctl adds its own header while stogger's ConsoleFileRenderer adds another. JournalLoggerFactory is a stub returning None, so nothing writes to the journal via journal.send(). Extracting the journal I/O into a separate workspace package with an optional dependency on systemd-python fixes this.

## Decisions

### packaging-model

#### Context

The journal I/O needs isolation from core because systemd-python only installs on Linux. The project uses hatch-vcs with src-layout. Users should be able to install a separate package from PyPI.

#### Decision

uv workspace with separate package. Root pyproject.toml stays as stogger package and becomes workspace root via [tool.uv.workspace] members = ["packages/*"]. New package at packages/stogger-systemd/ with its own pyproject.toml. Both packages share VCS version via hatch-vcs with raw-options.root pointing to the git root. Install via pip install stogger-systemd which pulls stogger + systemd-python.

#### Alternatives

a. Optional extra in same distribution (pip install stogger[systemd]) — no package separation, all code in one wheel. Rejected: users expect separate package for separate concern.
b. Separate repository — maximum isolation but versioning nightmare for shared VCS. Rejected.
c. Inline module with conditional import — no isolation, all users carry the import overhead. Rejected.

#### Consequences

Two independently publishable packages sharing one VCS tag. packages/stogger-systemd/ declares stogger as dependency, uses [tool.uv.sources] stogger = { workspace = true } during development. Platform isolation at dependency level — pip install stogger-systemd fails gracefully on non-Linux via systemd-python resolution.

### scope-split

#### Context

Core holds journal data transformation (SystemdJournalRenderer, JOURNAL_LEVELS) and a stub logger factory. The real journal I/O needs the systemd-python dependency.

#### Decision

Only the I/O layer moves to packages/stogger-systemd/: JournalLogger (with journal.send()), DummyJournalLogger, and the real JournalLoggerFactory. Renderer, level constants, and syslog import stay in core — pure data transformation, no platform deps.

#### Alternatives

a. Full extraction of renderer + factory — requires plugin mechanism in core for dict formatting. Rejected.
b. Everything including syslog constants out — syslog is stdlib on all platforms, renderer useful in tests. Rejected.

#### Consequences

Core keeps ~60 lines of journal formatting. New package is a thin I/O shim (~30 lines). Stub in core remains as fallback.

### integration-hook

#### Context

Core must discover the real journal logger factory when stogger-systemd is installed. Since it is a separate package, ImportError fires when it is not installed.

#### Decision

Dynamic import with ImportError fallback. Core attempts from stogger_systemd import get_journal_logger_factory. Falls back to stub on ImportError. Zero-config for users.

#### Alternatives

a. Entry point plugin — over-engineering for single integration point. Rejected.
b. Explicit import stogger_systemd side-effect — breaks "install and it works" DX. Rejected.
c. None-check pattern — only needed when module is always present (same distribution). Not applicable for separate package. Rejected.

#### Consequences

Single try/except block. The import path stogger_systemd.get_journal_logger_factory is the stable contract between packages.

### enable-systemd-source

#### Context

init_logging() needs to know whether to attempt journal registration. StoggerConfig already has an enable_systemd field read from [tool.stogger] in pyproject.toml.

#### Decision

enable_systemd comes from pyproject.toml config only — no new kwarg on init_logging(). The function reads StoggerConfig internally to get the setting. Convention over configuration: the config file is the source of truth.

#### Alternatives

a. New kwarg enable_systemd: bool = True — adds another parameter to an already long signature. Rejected.
b. Accept StoggerConfig object — API break for existing callers. Rejected.

#### Consequences

init_logging() gains a side-effect (reading pyproject.toml via StoggerConfig). Programmatic override requires writing to [tool.stogger] or calling StoggerConfig(enable_systemd=False) separately.

### journal-registration-flow

#### Context

init_logging() currently builds a loggers dict, then calls structlog.configure(). Journal registration is completely absent. Console suppression under JOURNAL_STREAM exists but is unrelated.

#### Decision

Standalone block after loggers-dict construction, before structlog.configure(). Flow: (1) file logger, (2) console logger with JOURNAL_STREAM suppression, (3) journal logger via dynamic import — independent of console, gated by enable_systemd from config, (4) configure. Console suppression and journal registration are decoupled concerns.

#### Alternatives

a. Journal registration inside if log_to_console block — conflates two concerns. Rejected.
b. Separate helper function _try_register_journal() — over-abstraction for one try/except. Rejected.

#### Consequences

Clear control flow. JOURNAL_STREAM detection triggers info message when import fails, but does not gate the import attempt itself.

### systemd-facility-plumbing

#### Context

StoggerConfig.systemd_facility exists but init_logging() hardcodes syslog.LOG_LOCAL1 in the SystemdJournalRenderer constructor (core.py line 493). LOG_LOCAL1 was fc-agent-specific. The renderer's own default is LOG_LOCAL0 (line 642).

#### Decision

Fix now. init_logging() reads systemd_facility from StoggerConfig and passes it through to SystemdJournalRenderer unchanged. When config value is None, uses LOG_LOCAL0 (the renderer's own default). No type conversion — config value is passed as-is.

#### Alternatives

a. Keep LOG_LOCAL1 default — backward compat with fc-agent, but was never a conscious decision. Rejected.
b. Convert str to int via getattr(syslog, value) — adds complexity for a field that should match the renderer's expected type. Rejected.

#### Consequences

Existing users with [tool.stogger] systemd_facility set get correct behavior. Users relying on the hardcoded LOG_LOCAL1 get LOG_LOCAL0 instead — no practical impact since journal filtering rarely distinguishes between LOCAL0/LOCAL1.

### fallback-behavior

#### Context

Most stogger users don't need journal integration. Fallback must be graceful.

#### Decision

When JOURNAL_STREAM detected but stogger-systemd not installed (ImportError): one-time info message "systemd journal detected but stogger-systemd not available. Install stogger-systemd package for journal integration." No package manager mention. Non-systemd: silent skip.

#### Alternatives

a. Silent skip always — NixOS/systemd users have no indication journal is missing. Rejected.
b. Hard error — breaks existing setups that never used journal. Rejected.

#### Consequences

One conditional info message when JOURNAL_STREAM is set. Informational, not a warning.

### api-contract

#### Context

Core needs a stable, minimal interface to import from the extra package.

#### Decision

stogger-systemd exports get_journal_logger_factory() -> JournalLoggerFactory (structlog-compatible factory). Plus JournalLogger and DummyJournalLogger as importable classes.

#### Alternatives

a. Bare JournalLogger class — core would need to instantiate, coupling to constructor. Rejected.
b. Whole module as plugin — no explicit contract. Rejected.

#### Consequences

Single integration point. Core: factory = get_journal_logger_factory() then loggers["journal"] = factory.

### test-strategy

#### Context

Integration point in core.py must be testable without systemd-python.

#### Decision

Dual test locations. Permanent tests in tests/test_systemd_integration.py — mock stogger_systemd import via unittest.mock.patch. Spec-validation tests in tests/impl_spec/ until Phase 2 makes them green, then cleanup. Test matrix: (1) enable_systemd=True + import succeeds -> journal registered, (2) enable_systemd=True + ImportError -> fallback, (3) enable_systemd=False -> no import attempt, (4) JOURNAL_STREAM + ImportError -> info message.

#### Alternatives

a. Only spec-validation tests — no permanent coverage after cleanup. Rejected.
b. Only permanent tests — spec-validation contract not explicitly tracked. Rejected.

#### Consequences

All four integration paths tested without systemd-python dependency.

### migration-notice

#### Context

Existing stogger users may wonder if this is breaking.

#### Decision

No breaking change. Core never delivered actual journal I/O (stub returned None). At most "New: stogger-systemd package available" note.

#### Alternatives

a. Minor changelog entry — acceptable but not required since nothing removed. Rejected as unnecessary.
b. Major version bump — overkill, no behavior changes. Rejected.

#### Consequences

Stogger stays on current version. stogger-systemd is a pure addition.

## Verified By

