# Tidy: Logging Convention Fixes

## Changes

### 1. Postgres ImportError at DEBUG
- **File:** `src/stogger/core.py:518`
- **Change:** `log.debug("stogger-postgres-not-installed", ...)` → `log.warning("stogger-postgres-not-installed", _replace_msg="PostgreSQL logging enabled but stogger-postgres package is not installed", reason="optional package not installed")`
- **Rationale:** User explicitly set `enable_postgres=True` — they must know if the feature cannot start. DEBUG is invisible at production log levels.

### 2. JournalSender OSError at DEBUG
- **File:** `src/stogger/systemd.py:45`
- **Change:** `log.debug("journal-send-failed", socket_path=self._socket_path, error=str(e))` → `log.warning("journal-send-failed", socket_path=self._socket_path, error=str(e))`
- **Rationale:** Journal send failures are production-relevant. Operator must see when journal logging silently fails.

## Constraints
- NEVER change log semantics (only level and add _replace_msg where missing)
- NEVER remove existing context keys
- ALL quality gates must pass after changes
