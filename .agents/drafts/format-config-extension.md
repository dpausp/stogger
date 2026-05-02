---
lifecycle:
  requirements:
    completed_at: "2026-05-02T12:00:00Z"
    git_rev: "cf1638b"
---

# format-config-extension

## Problem

Stogger hardcodes all timestamps to ISO 8601 with microsecond precision (`2026-05-02T12:34:56.123456Z`). The microseconds are visually noisy for most use cases. The existing `SimpleFormatSettings.timestamp_format` field is dead config — not loadable from pyproject.toml, not connected to the TimeStamper processor, and its documented value `"relative"` was never implemented. Users need control over timestamp precision and format via standard Python project configuration.

## Binding Decisions

### scope-boundary

#### Context

The user wants to "extend format config, close to structlog but generic". The current `SimpleFormatSettings` dataclass has multiple dead fields beyond timestamps (show_pid, show_logger_brackets, pad_event_width).

#### Decision

Scope is **timestamp format only** — precision options and display variants. Other SimpleFormatSettings fields are explicitly out of scope for this change.

#### Alternatives

a. Include all SimpleFormatSettings fields — rejected, scope creep beyond the stated problem.
b. Generic format plugin system — rejected, over-engineering for the current need.
c. Microseconds-only fix — rejected, defers the generic problem.

#### Consequences

Other dead config fields remain dead. A future change may address them separately.

### timestamp-precision

#### Context

TimeStamper produces ISO strings with microseconds. structlog's TimeStamper supports fmt="iso", fmt=None (unix), and arbitrary strftime strings. Users need choice over precision.

#### Decision

Four supported values for `timestamp_precision`:

| Value | Output example | Description |
|---|---|---|
| `"iso"` | `2026-05-02T12:34:56.123456Z` | Full precision with microseconds |
| `"iso_seconds"` | `2026-05-02T12:34:56Z` | Seconds only, no microseconds |
| `"iso_no_z"` | `2026-05-02T12:34:56` | Seconds only, no trailing Z |
| `"relative"` | `+2.341s` | Seconds since process start |

Invalid values pass through — structlog/strftime produces whatever it produces. No validation, GIGO.

#### Alternatives

a. structlog-style free-form strftime — rejected, complex validation, ugly in TOML.
b. Two values (full/seconds) — rejected, drops iso_no_z use case.
c. Arbitrary strftime with "iso" shortcut — rejected, UX concern for validation.

#### Consequences

Four well-defined options covering all current use cases. Users who put garbage in get garbage out — no guard rails, by design.

### config-surface

#### Context

Currently no user-facing format configuration exists. SimpleFormatSettings is unreachable from pyproject.toml or public API.

#### Decision

Configuration via `[tool.stogger.format]` section in `pyproject.toml`:

```toml
[tool.stogger.format]
timestamp_precision = "iso_seconds"
```

#### Alternatives

a. Parameter on init_logging() — rejected, not Python-idiomatic for project config.
b. Both TOML and parameter — rejected, two config paths to maintain.
c. Environment variable — rejected, not Python-idiomatic.

#### Consequences

Single configuration path. Standard Python project convention. Discoverable via pyproject.toml.

### backward-compat

#### Context

Current default is ISO with microseconds. Changing the default is a breaking change for any consumer parsing log output.

#### Decision

**Default changes to `"iso_seconds"`** (no microseconds). Hard switch, no deprecation period. Users who need microseconds must explicitly set `timestamp_precision = "iso"`.

#### Alternatives

a. Keep "iso" as default — rejected, microseconds stay noisy.
b. Deprecation warning — rejected, user said "egal".
c. Major version bump — rejected, overhead for a format detail.

#### Consequences

Breaking change. Existing log parsers that depend on microsecond precision will break. Users must opt-in to get microseconds back. This is intentional.

### naming-philosophy

#### Context

Format values could follow structlog conventions, use short codes, or be self-descriptive.

#### Decision

Descriptive, Python-idiomatic names: `"iso"`, `"iso_seconds"`, `"iso_no_z"`, `"relative"`. No structlog knowledge required to understand them.

#### Alternatives

a. structlog-compatible names — rejected, strftime strings are ugly in TOML.
b. Short codes (full/secs/noz) — rejected, cryptic.
c. Semantic names (precise/human/machine) — rejected, ambiguous.

#### Consequences

Self-documenting values. Consistent pattern: base format + qualifier.

### relative-semantics

#### Context

"relative" was documented in the existing SimpleFormatSettings docstring but never implemented. Need to define what it means.

#### Decision

`"relative"` means **seconds since process start**, formatted as `+2.341s` (with milliseconds, no microseconds).

#### Alternatives

a. Human-readable ("2s ago") — rejected, complex (pluralization, thresholds).
b. Unix timestamp (epoch seconds) — rejected, "relative" would be misleading.
c. Seconds since start, integer only — rejected, loses sub-second precision.

#### Consequences

Requires tracking process start time. Useful for performance observation. Millisecond precision balances readability and usefulness.

### error-strategy

#### Context

What happens when a user configures an invalid value like `timestamp_precision = "fancy"`?

#### Decision

Pass through to structlog/strftime — no validation. Invalid values produce unexpected but non-crashing output. GIGO by design.

#### Alternatives

a. Hard error at init_logging() — rejected, user explicitly wants permissive behavior.
b. Warning + fallback to default — rejected, adds complexity for no benefit.
c. Silent fallback — rejected, hides the misconfiguration.

#### Consequences

No validation code to maintain. Users are trusted to configure correctly. "Fancy" input produces fancy output.

### discovery

#### Context

New configuration option needs to be findable by users.

#### Decision

Document in **both** README (configuration section with TOML example) and `init_logging()` docstring (referencing available format options and TOML path).

#### Alternatives

a. README only — rejected, misses programmatic discovery.
b. Docstring only — rejected, misses project-level discovery.
c. Changelog only — rejected, only visible after release.

#### Consequences

Two documentation locations to maintain. Full coverage of discovery paths.

### dead-format-docs

#### Context

The existing `SimpleFormatSettings.timestamp_format` docstring documents `"relative"` as a valid value but it was never implemented. The field is dead config (unreachable from user config).

#### Decision

Remove `"relative"` from the old docstring. The new `timestamp_precision` field under `[tool.stogger.format]` replaces the entire `timestamp_format` concept. Old field documentation is cleaned up to avoid confusion.

#### Alternatives

a. Keep as-is — rejected, documented-but-unimplemented is worse than missing.
b. Mark as "planned" — rejected, produces a lie.

#### Consequences

Clean documentation. No false promises. New field with new semantics replaces the old dead field.

## Appendix

### Scope Summary

- **IN**: timestamp_precision config via [tool.stogger.format], four format values (iso, iso_seconds, iso_no_z, relative), TOML loading, README + docstring documentation
- **OUT**: other SimpleFormatSettings fields (show_pid, show_logger_brackets, pad_event_width), init_logging() parameter, environment variables, format plugin system

### Interface Contract

**Usage example (pyproject.toml):**
```toml
[tool.stogger]
log_format = "simple"

[tool.stogger.format]
timestamp_precision = "iso_seconds"  # iso | iso_seconds | iso_no_z | relative
```

**Discovery path:** User finds `[tool.stogger]` in README → sees `[tool.stogger.format]` sub-section → available values documented inline.

**Error behavior:** Invalid values produce unexpected output, no crash. E.g. `timestamp_precision = "fancy"` → structlog interprets as strftime → garbled but non-breaking output.

### Known Gaps for /design

- Reconcile old `SimpleFormatSettings.timestamp_format` with new `timestamp_precision` field — migrate or replace?
- How to track process start time for `"relative"` format
- How the new `[tool.stogger.format]` section maps to TimeStamper fmt parameter
- Wire format config through the pipeline: TOML → StoggerConfig → TimeStamper → ConsoleFileRenderer
