# format-config-extension

## Context

Stogger hardcodes all timestamps to ISO 8601 with microsecond precision. The existing `SimpleFormatSettings` dataclass is dead config — unreachable from pyproject.toml or public API, with documented values that were never implemented. The broader config layer uses manual `_load_config()` parsing without validation. This spec addresses both: timestamp format configuration and a proper attrs-based config layer.

## Decisions

### config-layer-attrs

#### Context

`StoggerConfig` uses a manual `__init__` with `_load_config()` that parses TOML, merges kwargs, and extracts ~20 fields via `config.get(key, default)`. No validation, no type safety. `SimpleFormatSettings` is a separate dataclass that is never constructed from config — always defaults.

#### Decision

Migrate `StoggerConfig` to `attrs` classes with proper converters and validators. `FormatConfig` is a nested attrs class for `[tool.stogger.format]`, following the existing `[tool.stogger.ast]` precedent. `SimpleFormatSettings` is deleted — its living fields migrate to `FormatConfig`.

#### Alternatives

a. Only new `FormatConfig` as attrs, rest stays manual — rejected, half-cleaned state.
b. Pydantic instead of attrs — rejected, heavy runtime dependency for a 2-dep library.
c. attrs + cattrs — rejected, cattrs is overkill for simple TOML-to-attrs mapping.
d. Keep dataclasses with `__post_init__` validation — rejected, reimplements attrs validators.

#### Consequences

`attrs` becomes a new runtime dependency. Config loading gains type safety and validation. `SimpleFormatSettings` dies. One-time migration effort for `StoggerConfig` (~160 lines).

### format-config-fields

#### Context

`SimpleFormatSettings` has 6 fields. Three are never used from config (`show_logger_brackets`, `show_pid`, `timestamp_format`). Three are functional (`min_level`, `show_code_info`, `pad_event_width`). A new `timestamp_precision` field is needed.

#### Decision

`FormatConfig` (attrs class) contains:

| Field | Type | Default | Origin |
|---|---|---|---|
| `timestamp_precision` | `str` | `"iso_seconds"` | New |
| `min_level` | `str` | `"info"` | From SimpleFormatSettings |
| `show_code_info` | `bool` | `False` | From SimpleFormatSettings |
| `pad_event_width` | `int` | `30` | From SimpleFormatSettings |

Dead fields (`show_logger_brackets`, `show_pid`, `timestamp_format`) are not migrated.

#### Alternatives

a. Only `timestamp_precision` in FormatConfig, keep SimpleFormatSettings — rejected, defeats cleanup purpose.
b. All 6 SimpleFormatSettings fields migrated — rejected, includes dead fields.
c. No FormatConfig, fields live in StoggerConfig flat — rejected, loses sub-section structure.

#### Consequences

`ConsoleFileRenderer` receives `FormatConfig` instead of `SimpleFormatSettings`. Four fields total. Config TOML uses `[tool.stogger.format]` section.

### timestamp-precision-values

#### Context

structlog's `TimeStamper` accepts `fmt="iso"` (with µs), arbitrary strftime strings, or `fmt=None` (unix float). The feature needs four format variants with zero validation on invalid input (GIGO).

#### Decision

Four supported values:

| Value | TimeStamper fmt | Output example | Description |
|---|---|---|---|
| `"iso"` | `"iso"` | `2026-05-02T12:34:56.123456Z` | Full precision with µs |
| `"iso_seconds"` | `"%Y-%m-%dT%H:%M:%SZ"` | `2026-05-02T12:34:56Z` | Seconds only |
| `"iso_no_z"` | `"%Y-%m-%dT%H:%M:%S"` | `2026-05-02T12:34:56` | Seconds, no Z suffix |
| `"relative"` | `"iso"` (kept for pipeline) | `+2.341s` | Renderer computes delta from process start |

Default changes from `"iso"` to `"iso_seconds"` — breaking change, no deprecation. Invalid values pass through to structlog/strftime (GIGO).

#### Alternatives

a. Free-form strftime with "iso" shortcut — rejected, ugly in TOML, validation complexity.
b. Two values only (full/seconds) — rejected, drops iso_no_z and relative.
c. Validation with error on invalid value — rejected, user wants GIGO.

#### Consequences

Breaking change: existing log output loses microseconds unless user opts into `"iso"`. Three ISO variants handled by TimeStamper fmt parameter. Relative handled by renderer.

### pipeline-approach

#### Context

Three separate `TimeStamper` call sites exist (factory.py:41, core.py:507, core.py:582), all hardcoded to `fmt="iso"`. The renderer's `_format_timestamp` only strips Z for `"iso_no_z"`, passes everything else through.

#### Decision

ISO variants (`iso`, `iso_seconds`, `iso_no_z`): `TimeStamper` receives the appropriate `fmt` parameter. Renderer wraps in ANSI colors, no further transformation needed.

Relative format: `TimeStamper` keeps `fmt="iso"` (unchanged). Renderer computes `time.time() - format_config._process_start` and formats as `+X.XXXs`. The `FormatConfig` stores `_process_start: float = time.time()` at instantiation.

#### Alternatives

a. TimeStamper always `fmt=None` (unix float), custom processor formats everything — rejected, reimplements TimeStamper.
b. TimeStamper unchanged, renderer strips µs/Z from ISO strings — rejected, wasteful string manipulation.
c. Custom TimestampProcessor replaces TimeStamper — rejected, maintains own timestamp logic.

#### Consequences

Minimal pipeline change for ISO variants (just fmt parameter). Relative needs renderer change and process-start tracking. No new processors added.

### call-site-unification

#### Context

Three TimeStamper instantiations with inconsistent parameters: `init_logging()` uses `utc=False`, the other two use `utc=True`. One omits `key="timestamp"`.

#### Decision

Central `build_timestamp_processor(config)` function creates `TimeStamper` with the correct `fmt` from `config.format.timestamp_precision`. All three call sites use this function. All sites normalized to `utc=True`.

#### Alternatives

a. Config passed to each site, each creates own TimeStamper — rejected, code duplication.
b. Only fix factory.py and init_early_logging, leave init_logging — rejected, leaves inconsistency.
c. Keep all three hardcoded, renderer handles formatting — rejected, renderer becomes complex.

#### Consequences

Single source of truth for timestamp configuration. `init_logging()` gains `utc=True` (was `utc=False`). Three code paths reduced to one factory function.

### test-strategy

#### Context

Zero tests exist for timestamp config flowing from TOML through to renderer. Existing tests cover `ConsoleFileRenderer` with direct `SimpleFormatSettings` construction.

#### Decision

TDD approach. Spec-validation tests in `tests/impl_spec/test_format_config_extension.py` (xfail, garbage-collected after passing). Permanent decision tests in `tests/test_core.py` and `tests/test_config.py`. Tests cover:

- TOML `[tool.stogger.format]` loading → FormatConfig field values
- Each `timestamp_precision` value produces correct TimeStamper fmt
- Renderer output for all four format values
- Relative format shows elapsed time
- GIGO: invalid value produces output without crash
- Default is `"iso_seconds"` when no config present

#### Alternatives

a. Tests-after — rejected, no spec validation traceability.
b. Only extend existing tests — rejected, no config-flow coverage.
c. No automated tests — rejected, config pipeline is critical path.

#### Consequences

Full test coverage for config flow. Bidirectional traceability: ADR references test file paths. Spec-validation tests verify design decisions before implementation.

## Verified By

