# Logdir Config Fallback & ENV Override

## Bug: `init_logging()` ignoriert `cfg.logdir`

**Problem**: `init_logging()` in `src/stogger/core.py` wandelt den `logdir`-Parameter in `Path(logdir) if logdir else None` um (Zeile 555), erzeugt dann die Config (Zeile 560), aber ruft `_build_logger_factories(logdir, ...)` (Zeile 588) mit dem ursprünglichen Parameter-Wert auf — nicht mit `cfg.logdir`. Der Config-Wert aus `pyproject.toml` ist tot.

**Fix**: Nach `cfg = StoggerConfig(verbose=bool(verbose))` (Zeile 560) prüfen: wenn `logdir is None`, auf `cfg.logdir` fallen.

Datei: `src/stogger/core.py`

## Feature: ENV-Var-Overrides für Config

**Problem**: Es gibt keinen generischen Mechanismus, um Config-Werte per ENV-Var zu überschreiben.

**Lösung**: `_load_env_overrides()`-Funktion in `src/stogger/config.py`, die nach `STOGGER_<KEY>`-Env-Vars sucht und einen Dict zurückgibt. Priorität: ENV > kwarg > pyproject.toml.

Unterstützte Felder mit Typkonvertierung:
- `verbose` → `STOGGER_VERBOSE` (bool)
- `logdir` → `STOGGER_LOGDIR` (Path)
- `log_cmd_output` → `STOGGER_LOG_CMD_OUTPUT` (bool)
- `log_to_console` → `STOGGER_LOG_TO_CONSOLE` (bool)
- `syslog_identifier` → `STOGGER_SYSLOG_IDENTIFIER` (str)
- `show_caller_info` → `STOGGER_SHOW_CALLER_INFO` (bool)
- `translation_dir` → `STOGGER_TRANSLATION_DIR` (Path)
- `language` → `STOGGER_LANGUAGE` (str)
- `log_format` → `STOGGER_LOG_FORMAT` (str)
- `async_logging` → `STOGGER_ASYNC_LOGGING` (bool)
- `enable_systemd` → `STOGGER_ENABLE_SYSTEMD` (bool)
- `systemd_facility` → `STOGGER_SYSTEMD_FACILITY` (str)
- `enable_postgres` → `STOGGER_ENABLE_POSTGRES` (bool)
- `postgres_dsn` → `STOGGER_POSTGRES_DSN` (str)
- `postgres_table` → `STOGGER_POSTGRES_TABLE` (str)
- `src_dir` → `STOGGER_SRC_DIR` (str)

Bool-Konvertierung: "1", "true", "yes" → True; "0", "false", "no" → False (case-insensitive). Andere Werte → ignorieren.

Einbau in `StoggerConfig.__init__`:
```python
config = _load_pyproject_config(verbose=verbose)
config.update(kwargs)       # kwargs override pyproject.toml
env_overrides = _load_env_overrides()
config.update(env_overrides)  # env overrides kwargs
```

## Tests

Datei: `tests/test_config.py` (bestehende Tests ergänzen)

**Bug-Test**: `test_init_logging_falls_back_to_cfg_logdir` — prüft dass `init_logging()` ohne `logdir`-Parameter auf `cfg.logdir` zurückfällt.
**Bug-Test**: `test_init_logging_logdir_param_wins` — prüft dass expliziter `logdir`-Parameter Vorrang hat.

**Feature-Tests**:
- `test_env_override_logdir` — `STOGGER_LOGDIR` setzen, Config laden, `cfg.logdir` prüfen
- `test_env_override_verbose` — `STOGGER_VERBOSE=true` setzen, prüfen
- `test_env_override_bool_false` — `STOGGER_LOG_TO_CONSOLE=false` setzen, prüfen
- `test_env_override_bool_invalid` — `STOGGER_VERBOSE=invalid` → ignoriert, Default bleibt
- `test_env_override_kwargs_priority` — ENV > kwarg sicherstellen
- `test_env_no_override_stogger_debug` — `STOGGER_DEBUG` bleibt von Feature unberührt
