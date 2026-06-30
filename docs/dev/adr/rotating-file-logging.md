# rotating-file-logging

## Context

A downstream consumer (voice-focused-desktop, a desktop dictation daemon that runs for
days) requested file rotation for long-running stogger consumers. Without rotation, the
`{syslog_identifier}.log` file in `logdir` grows unbounded and becomes too large to
inspect within a week.

The original request proposed adding `RotatingFileHandler` to
`stogger.factory._create_file_handler` and claimed `structlog.stdlib.ProcessorFormatter`
already wraps every file handler. Investigation showed this premise was broken:
`configure_stdlib_logging` (the only caller of `_create_file_handler`) had zero
production callers — only tests. The real production file path runs through
`build_logger_factories` in `core.py`, which uses `structlog.PrintLoggerFactory(file)`
on a plain `Path.open("a")` handle — no `logging.Handler` involved, no
`ProcessorFormatter` wrapping. The dead stdlib pipeline was removed in `7cfdea2`.

The actual question: how to add rotation to the live `PrintLoggerFactory` path.

## Decision

Add size-based rotation via a file-like drop-in writer
(`RotatingFileWriter` in `src/stogger/rotation.py`), exposed through three new
`init_logging` kwargs (`log_rotation`, `log_max_bytes`, `log_backup_count`) and
matching `StoggerConfig` fields / env vars. Scope is size-only; timed rotation,
compression, and multi-process locking are explicitly out of scope.

The writer implements `write()`, `flush()`, `close()` — the full public surface
that `PrintLoggerFactory` consumes — and rotates when the next write would push
file size strictly above `max_bytes`. Naming follows stdlib
`logging.handlers.RotatingFileHandler` (`base.log`, `base.log.1`, `base.log.2`, ...)
so operators familiar with stdlib don't have to relearn anything.

Rollover fires **before** the triggering write, opening a fresh base file and
landing the trigger write there — same semantics as stdlib. A file holding exactly
`max_bytes` is still valid; only the next write (which would exceed) rotates. This
is slightly more permissive than stdlib's `>=` check, which would rotate on the
first write of exactly `max_bytes` length even from an empty file.

`rotation.py` is added to `[tool.pytest-stogger.per-file-ignores]` for
`complexity-needs-log`: `write()` runs inside the structlog render → print →
file.write hot path; logging during rollover would recurse back through the
pipeline. Same rationale as `_decorators.py` and `systemd.py`.

## Alternatives

a. **stdlib `RotatingFileHandler` via `structlog.stdlib.LoggerFactory`** — would replace
the `PrintLoggerFactory` path entirely, breaking the multi-target renderer architecture
(journal/postgres/console/file dispatch via `MultiOptimisticLoggerFactory`). Disproportionate
change for one feature.

b. **Wrap `RotatingFileHandler.stream`** — `PrintLoggerFactory(handler.stream)` would
give us the file handle, but the handler's `shouldRollover` / `doRollover` would never
fire because nobody calls `handler.emit()`. Silent no-op.

c. **Timed rotation as part of this decision** — `TimedRotatingFileHandler` semantics
(`when=midnight`, `interval`, `utc`) are a separate axis with their own design questions
(locale, DST, atexit cleanup of pending rollovers). Bundling them in would inflate scope
without clear demand. Deferred to a follow-up if any consumer needs it.

d. **Compression of rotated files** — gzip/zstd of `.log.N` files reduces disk usage but
introduces CPU cost on rollover, naming variants (`.log.1.gz` vs `.log.1`), and
disagreement about format. Operators who need compression can run `logrotate(8)` on the
side or call `RotatingFileWriter._backup_path(N)` from external tooling. Not first-class.

e. **Multi-process file locking** — `RotatingFileHandler` has a `delay` + `WatchedFileHandler`
pattern for multi-process setups. stogger targets single-process applications; multi-process
deployment should use journald or postgres targets, not file rotation. Documented limitation.

## Consequences

- One new module (`rotation.py`, ~100 lines), three new config fields, three new env
  vars, three new `init_logging` kwargs. Defaults preserve current behavior exactly.
- `rotation.py` joins `_decorators.py` and `systemd.py` as logging infrastructure excluded
  from `complexity-needs-log` — same recursion-safety rationale.
- File rotation is now a documented first-class feature for daemon workloads. Future
  timed/compression support can extend the same `RotatingFileWriter` without API changes
  (just additional `match` cases in `_build_file_target`).
- Operators using `logrotate(8)` externally should leave `log_rotation="none"` to avoid
  double rotation.
