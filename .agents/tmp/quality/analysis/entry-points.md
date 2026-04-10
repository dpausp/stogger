# Entry Point Inventory

## CLI Subcommands

### Top-level commands (on `stoggertools` Typer app)

- `stoggertools check` — source: [packages/stoggertools/src/stoggertools/cli.py:461] — description: "Check code for logging best practices with AST analysis by default." Options: `--fix`, `--interactive`, `--dry-run`, `--no-ast`, `--complexity`, `--pattern`, `--verbose`.
- `stoggertools migrate` — source: [packages/stoggertools/src/stoggertools/cli.py:1415] — description: "Analyze project and migrate code." Default is dry-run preview. Options: `--output`, `--dry-run`, `--no-dry-run`, `--type`, `--no-ast`, `--pattern`, `--interactive`, `--verbose`, `--check-imports`, `--force`, `--json`.
- `stoggertools docs` — source: [packages/stoggertools/src/stoggertools/cli.py:364] — description: "Show documentation and examples." Options: `--interactive`, `--feature`, `--pager`.
- `stoggertools docs-serve` — source: [packages/stoggertools/src/stoggertools/cli.py:396] — description: "Serve HTML documentation in browser." Options: `--port`, `--host`, `--open/--no-open`, `--build/--no-build`.
- `stoggertools init` — source: [packages/stoggertools/src/stoggertools/cli.py:414] — description: "Initialize stogger configuration." Options: `path`, `--template`, `--force`.

### `tools` subgroup (on `stoggertools tools`)

- `stoggertools tools generate-service` — source: [packages/stoggertools/src/stoggertools/cli.py:134] — description: "Generate systemd service file." Args: `service_name`, `exec_command`. Options: `--user`, `--working-dir`, `--output`.
- `stoggertools tools check-advanced` — source: [packages/stoggertools/src/stoggertools/cli.py:150] — description: "Advanced check with all options for complexity analysis and AST patterns."
- `stoggertools tools review` — source: [packages/stoggertools/src/stoggertools/cli.py:158] — description: "Review log quality and provide suggestions." Args: `path`. Options: `--format`, `--min-score`.
- `stoggertools tools journal` — source: [packages/stoggertools/src/stoggertools/cli.py:182] — description: "Beautiful systemd journal viewer." Options: `--unit`, `--lines`, `--follow`, `--since`, `--level`.
- `stoggertools tools dashboard` — source: [packages/stoggertools/src/stoggertools/cli.py:224] — description: "Start the web dashboard." Options: `--host`, `--port`, `--debug`. Only available when Flask is installed.
- `stoggertools tools demo` — source: [packages/stoggertools/src/stoggertools/cli.py:1497] — description: "Run interactive demos." Args: `feature`. Options: `--all`.

### `tools i18n` subgroup (on `stoggertools tools i18n`)

- `stoggertools tools i18n check` — source: [packages/stoggertools/src/stoggertools/cli.py:243] — description: "Check translation completeness and quality." Args: `src_dir`. Options: `--translation-dir`, `--language`, `--list-missing`, `--fail-on-extra`, `--strict`, `--verbose`.

### Hidden: `_serve_html_docs` (internal helper)

- Called by `docs-serve` command — source: [packages/stoggertools/src/stoggertools/cli.py:411] — not directly user-facing.

## Scripts / Console Entry Points

- `stoggertools` — source: [packages/stoggertools/pyproject.toml:7-8] (`stoggertools = "stoggertools:main"`) — purpose: Main CLI entry point. Calls `app()` on the root Typer instance. `main` is imported from `stoggertools.cli` via `stoggertools/__init__.py:72`.
- `python -m stoggertools` — source: [packages/stoggertools/src/stoggertools/__main__.py:1-6] — purpose: Module execution entry point, calls `main()` which invokes the Typer app.

### pyproject.toml `[project.scripts]` summary

| Package | Script | Entry Point |
|---------|--------|-------------|
| stoggertools | `stoggertools` | `stoggertools:main` |
| stogger | (none) | library only |
| stogger-web | (none) | library only |
| stogger-eliot | (none) | library only |
| stogger-systemd | (none) | library only |

## Documented Features

### README.md claims (source: /stogger/README.md)

- Multi-target logging (console, file, systemd journal simultaneously) — claimed in: [README.md:7]
- Optimistic error handling (logging failures don't crash application) — claimed in: [README.md:8]
- Rich console formatting (colored output with structured data) — claimed in: [README.md:9]
- Structured logging (machine-parseable logs) — claimed in: [README.md:10]
- Command output logging (separate logging for external command output) — claimed in: [README.md:11]
- Template-based messages (human-readable messages with graceful fallbacks) — claimed in: [README.md:12]
- Systemd integration (automatic detection and journal integration) — claimed in: [README.md:13]
- Development-friendly (rich debugging information) — claimed in: [README.md:14]
- Migration from print() to structlog — claimed in: [README.md:40]
- Migration from standard logging to structlog — claimed in: [README.md:41]
- Eliot integration — claimed in: [README.md:42]
- Sentry integration — claimed in: [README.md:43]
- Project Analysis (comprehensive assessment of logging patterns) — claimed in: [README.md:149]
- Safe Migration (analyze first, migrate only with explicit flag) — claimed in: [README.md:150]
- Interactive Mode (user confirmation for each change) — claimed in: [README.md:151]
- Risk Assessment (complexity analysis and conflict detection) — claimed in: [README.md:152]
- Safety Features (backup files, dry-run previews) — claimed in: [README.md:153]
- Agent-Friendly (JSON output for programmatic consumption) — claimed in: [README.md:154]

### docs/features/ claims

- Advanced AST Assistant (intelligent code transformation, anti-pattern detection, suggestions, refactoring) — claimed in: [docs/features/advanced_assistant.md:1-69]
- Eliot integration (human-readable action traces, `log_action`, `log_call`) — claimed in: [docs/features/integrations.md:1-25]
- Systemd integration (journal logging, service file generation, environment detection) — claimed in: [docs/features/integrations.md:27-41]
- Web Dashboard (real-time log viewer via Flask+HTMX) — claimed in: [docs/features/integrations.md:43-65]
- i18n/translation coverage check (CLI tool for verifying translation files) — claimed in: [docs/features/i18n.md:1-29]

### docs/user_guide/ claims

- `migrate` command (project analysis and migration) — claimed in: [docs/user_guide/cli_reference.md:42-61]
- `check` command (code quality and best practices with AST analysis) — claimed in: [docs/user_guide/cli_reference.md:63-79]
- `init` command (configuration initialization) — claimed in: [docs/user_guide/cli_reference.md:81-94]
- `docs` command (documentation viewer) — claimed in: [docs/user_guide/cli_reference.md:96-100]
- Migration types: `print-to-structlog`, `logging-to-structlog`, `cli-outputs-to-structlog`, `format-strings` — claimed in: [docs/user_guide/cli_reference.md:9-16]

### docs/specs/ claims

- Log Level Appropriateness rule (library code should use debug for internal ops) — claimed in: [docs/specs/logging_rules_spec.md:17-33]
- Exception Logging rule (use log.exception() in except blocks) — claimed in: [docs/specs/logging_rules_spec.md:35-51]
- Logging Coverage rule (minimum percentage of lines with logging) — claimed in: [docs/specs/logging_rules_spec.md:53-64]

## Public API (if library)

### Package: `stogger` (source: packages/stogger/src/stogger/__init__.py)

Exports declared in `__all__` (line 3-23):

- `stogger.JournalLogger` — source: [packages/stogger/src/stogger/core.py:586] — Logger that sends messages to systemd journal.
- `stogger.JournalLoggerFactory` — source: [packages/stogger/src/stogger/core.py:593] — Factory for creating journal loggers.
- `stogger.MultiOptimisticLogger` — source: [packages/stogger/src/stogger/core.py:756] — Logger distributing messages to multiple sub-loggers.
- `stogger.MultiOptimisticLoggerFactory` — source: [packages/stogger/src/stogger/core.py:742] — Factory creating MultiOptimisticLogger instances.
- `stogger.StoggerConfig` — source: [packages/stogger/src/stogger/config.py:48] — Manages stogger configuration from pyproject.toml + kwargs.
- `stogger.SystemdJournalRenderer` — source: [packages/stogger/src/stogger/core.py:634] — Renderer for systemd journal output.
- `stogger.analyze_python_file` — re-exported from stoggertools — source: [packages/stoggertools/src/stoggertools/__init__.py:63]
- `stogger.arsch` — source: [packages/stogger/src/stogger/i18n.py:205] — Austrian-style "this is bad" message helper.
- `stogger.create_advanced_assistant` — re-exported from stoggertools — source: [packages/stoggertools/src/stoggertools/__init__.py:65]
- `stogger.create_interactive_transformer` — re-exported from stoggertools — source: [packages/stoggertools/src/stoggertools/__init__.py:73]
- `stogger.create_live_editor` — re-exported from stoggertools — source: [packages/stoggertools/src/stoggertools/__init__.py:83]
- `stogger.create_pii_processor` — source: [packages/stogger/src/stogger/pii_scrubber.py:171] — Create a PII scrubber structlog processor.
- `stogger.demo_pii_scrubbing` — source: [packages/stogger/src/stogger/pii_scrubber.py:185] — Demonstrate PII scrubbing capabilities.
- `stogger.drop_cmd_output_logfile` — source: [packages/stogger/src/stogger/core.py:831] — Delete the command output log file.
- `stogger.edit_code_live` — re-exported from stoggertools — source: [packages/stoggertools/src/stoggertools/__init__.py:85]
- `stogger.get_translator` — source: [packages/stogger/src/stogger/i18n.py:167] — Get current translator instance.
- `stogger.init_command_logging` — source: [packages/stogger/src/stogger/core.py:785] — Add cmd_output_file logger factory.
- `stogger.init_early_logging` — source: [packages/stogger/src/stogger/core.py:542] — Initialize minimal logging format early.
- `stogger.init_i18n` — source: [packages/stogger/src/stogger/i18n.py:158] — Initialize internationalization.
- `stogger.init_logging` — source: [packages/stogger/src/stogger/core.py:440] — Main logging initialization (console, file, journal).
- `stogger.leiwand` — source: [packages/stogger/src/stogger/i18n.py:200] — Austrian-style "this is great" message helper.
- `stogger.logging_initialized` — source: [packages/stogger/src/stogger/core.py:866] — Check if structlog has been configured.
- `stogger.oida` — source: [packages/stogger/src/stogger/i18n.py:195] — Austrian-style exclamation helper.
- `stogger.t` — source: [packages/stogger/src/stogger/i18n.py:178] — Shorthand translation function.

Additional public symbols NOT in `__all__` but used/imported:

- `stogger.config.detect_project_structure` — source: [packages/stogger/src/stogger/config.py:123] — Detect project structure using smart heuristics.
- `stogger.config.ProjectStructure` — source: [packages/stogger/src/stogger/config.py:12] — Dataclass with source_dirs, test_dirs, exclude_patterns.
- `stogger.config.SimpleFormatSettings` — source: [packages/stogger/src/stogger/config.py:392] — Settings for simple console formatting.
- `stogger.i18n_check.check_translations` — source: [packages/stogger/src/stogger/i18n_check.py:114] — Check translation coverage and return report.
- `stogger.i18n_check.format_report` — source: [packages/stogger/src/stogger/i18n_check.py:197] — Format translation coverage report.
- `stogger.gitignore_utils.filter_python_files` — source: [packages/stogger/src/stogger/gitignore_utils.py] — Filter Python files respecting .gitignore.
- `stogger.factory.build_shared_processors` — source: [packages/stogger/src/stogger/factory.py:26] — Build processors for sync/async logging.
- `stogger.factory.configure_stdlib_logging` — source: [packages/stogger/src/stogger/factory.py:124] — Configure Python stdlib logging.
- `stogger.core.ConsoleFileRenderer` — source: [packages/stogger/src/stogger/core.py:99] — Rich console/file log renderer.
- `stogger.core.JSONRenderer` — source: [packages/stogger/src/stogger/core.py:319] — JSON renderer for structured output.
- `stogger.core.MultiRenderer` — source: [packages/stogger/src/stogger/core.py:713] — Calls multiple renderers and merges output.
- `stogger.core.TranslationProcessor` — source: [packages/stogger/src/stogger/core.py:56] — Processor for _replace_msg and translation lookups.

### Package: `stoggertools` (source: packages/stoggertools/src/stoggertools/__init__.py)

Exports declared in `__all__` (line 6-38):

All `stogger.*` exports above plus:
- `stoggertools.main` — source: [packages/stoggertools/src/stoggertools/cli.py:72 (via __init__.py:72)] — CLI entry point (Typer app).
- `stoggertools.migrate_directory` — source: [packages/stoggertools/src/stoggertools/assistant.py:205] — Migrate Python files under a directory (print-to-structlog).
- `stoggertools.oida` — re-exported from stogger.
- `stoggertools.t` — re-exported from stogger.
- `stoggertools.transform_directory_interactive` — source: [packages/stoggertools/src/stoggertools/interactive_transformer.py:681] — Quick interactive directory transformation.
- `stoggertools.transform_file_interactive` — source: [packages/stoggertools/src/stoggertools/interactive_transformer.py:672] — Quick interactive file transformation.
- `stoggertools.transform_python_file` — source: [packages/stoggertools/src/stoggertools/advanced_assistant.py:858] — Quick transformation of a Python file.

Additional public symbols NOT in `__all__` but importable:

- `stoggertools.cli.app` — source: [packages/stoggertools/src/stoggertools/cli.py:110] — Root Typer application instance.
- `stoggertools.assistant.migrate_file` — source: [packages/stoggertools/src/stoggertools/assistant.py:193] — Migrate a single file's content (print-to-structlog).
- `stoggertools.assistant.PrintToStructlogTransformer` — source: [packages/stoggertools/src/stoggertools/assistant.py:29] — AST transformer for print-to-structlog.
- `stoggertools.assistant.MigrationResult` — source: [packages/stoggertools/src/stoggertools/assistant.py:18] — Result dataclass for migration.
- `stoggertools.advanced_assistant.AdvancedAssistant` — source: [packages/stoggertools/src/stoggertools/advanced_assistant.py:516] — Main AST transformation engine.
- `stoggertools.advanced_assistant.ASTPattern` — source: [packages/stoggertools/src/stoggertools/advanced_assistant.py:42] — Pattern definition for AST matching.
- `stoggertools.advanced_assistant.CodeAnalysisResult` — source: [packages/stoggertools/src/stoggertools/advanced_assistant.py:74] — Analysis result dataclass.
- `stoggertools.advanced_assistant.TransformationResult` — source: [packages/stoggertools/src/stoggertools/advanced_assistant.py:123] — Transformation result dataclass.
- `stoggertools.advanced_assistant.TransformationMetrics` — source: [packages/stoggertools/src/stoggertools/advanced_assistant.py:55] — Metrics collected during transformation.
- `stoggertools.interactive_transformer.InteractiveTransformer` — source: [packages/stoggertools/src/stoggertools/interactive_transformer.py:85] — Interactive code transformer.
- `stoggertools.live_editor.LiveCodeEditor` — source: [packages/stoggertools/src/stoggertools/live_editor.py:42] — In-terminal code editor for transformations.
- `stoggertools.live_editor.EditSession` — source: [packages/stoggertools/src/stoggertools/live_editor.py:27] — Records an editing session for ML.
- `stoggertools.linter.lint_directory` — source: [packages/stoggertools/src/stoggertools/linter.py:619] — Lint all Python files in a directory.
- `stoggertools.linter.LoggingStats` — source: [packages/stoggertools/src/stoggertools/linter.py:44] — Statistics about logging in a file.
- `stoggertools.linter.LintOptions` — source: [packages/stoggertools/src/stoggertools/linter.py:20] — Options for linting operations.
- `stoggertools.log_reviewer.LogQualityReviewer` — source: [packages/stoggertools/src/stoggertools/log_reviewer.py:32] — Log quality reviewer with Austrian honesty.
- `stoggertools.log_reviewer.LogQualityReport` — source: [packages/stoggertools/src/stoggertools/log_reviewer.py:20] — Quality report dataclass.
- `stoggertools.cli_output_transformer.migrate_cli_outputs_file` — source: [packages/stoggertools/src/stoggertools/cli_output_transformer.py:489] — Migrate CLI output calls in a file.
- `stoggertools.cli_output_transformer.analyze_cli_outputs_in_file` — source: [packages/stoggertools/src/stoggertools/cli_output_transformer.py:507] — Analyze CLI output calls without transforming.
- `stoggertools.project_analyzer.ProjectAnalyzer` — source: [packages/stoggertools/src/stoggertools/project_analyzer.py:102] — Analyzes Python projects for migration.
- `stoggertools.project_analyzer.analyze_project_for_agents` — source: [packages/stoggertools/src/stoggertools/project_analyzer.py:937] — Convenience function for AI agents.
- `stoggertools.project_analyzer.ProjectAnalysisResult` — source: [packages/stoggertools/src/stoggertools/project_analyzer.py:81] — Complete analysis result dataclass.
- `stoggertools.log_statement_analyzer.analyze_file` — source: [packages/stoggertools/src/stoggertools/log_statement_analyzer.py:457] — Analyze log statements in a Python file.

### Package: `stogger_web` (source: packages/stogger-web/src/stogger_web/__init__.py)

Exports declared in `__all__` (line 3-8):

- `stogger_web.FLASK_AVAILABLE` — source: [packages/stogger-web/src/stogger_web/web_dashboard.py:16] — Whether Flask is importable.
- `stogger_web.get_log_stats` — source: [packages/stogger-web/src/stogger_web/web_dashboard.py:372] — Calculate log statistics from in-memory buffer.
- `stogger_web.run_dashboard` — source: [packages/stogger-web/src/stogger_web/web_dashboard.py:421] — Run the Flask web dashboard server.
- `stogger_web.setup_web_logging` — source: [packages/stogger-web/src/stogger_web/web_dashboard.py:404] — Set up web logging integration with structlog.

### Package: `stogger_systemd` (source: packages/stogger-systemd/src/stogger_systemd/__init__.py)

Exports declared in `__all__` (line 3-7):

- `stogger_systemd.create_systemd_service_file` — source: [packages/stogger-systemd/src/stogger_systemd/systemd_integration.py:222] — Generate a systemd service file with logging config.
- `stogger_systemd.demo_systemd_integration` — source: [packages/stogger-systemd/src/stogger_systemd/systemd_integration.py:364] — Demonstrate systemd integration features.
- `stogger_systemd.setup_systemd_logging` — source: [packages/stogger-systemd/src/stogger_systemd/systemd_integration.py:150] — Set up systemd journal logging integration.

Additional public symbols NOT in `__all__` but importable:

- `stogger_systemd.systemd_integration.detect_systemd_environment` — source: [packages/stogger-systemd/src/stogger_systemd/systemd_integration.py:114] — Detect systemd runtime environment.
- `stogger_systemd.systemd_integration.SystemdJournalHandler` — source: [packages/stogger-systemd/src/stogger_systemd/systemd_integration.py:33] — Advanced systemd journal handler.
- `stogger_systemd.systemd_integration.ServiceConfig` — source: [packages/stogger-systemd/src/stogger_systemd/systemd_integration.py:210] — Config for systemd service creation.
- `stogger_systemd.systemd_integration.query_journal_logs` — source: [packages/stogger-systemd/src/stogger_systemd/systemd_integration.py:275] — Query systemd journal for logs.
- `stogger_systemd.journal_viewer.JournalViewer` — source: [packages/stogger-systemd/src/stogger_systemd/journal_viewer.py:62] — Beautiful viewer for systemd journal logs.
- `stogger_systemd.journal_viewer.JournalQueryOptions` — source: [packages/stogger-systemd/src/stogger_systemd/journal_viewer.py:25] — Options for journal queries.
- `stogger_systemd.journal_viewer.JournalEntry` — source: [packages/stogger-systemd/src/stogger_systemd/journal_viewer.py:48] — Structured journal entry.
- `stogger_systemd.journal_viewer.SYSTEMD_AVAILABLE` — source: [packages/stogger-systemd/src/stogger_systemd/journal_viewer.py:39] — Whether systemd-python is importable.

### Package: `stogger_eliot` (source: packages/stogger-eliot/src/stogger_eliot/__init__.py)

Exports declared in `__all__` (line 3-5):

- `stogger_eliot.setup_eliot_logging` — source: [packages/stogger-eliot/src/stogger_eliot/eliot_integration.py:192] — Set up Eliot logging with stogger integration.

Additional public symbols NOT in `__all__` but importable:

- `stogger_eliot.eliot_integration.HumanReadableEliotDestination` — source: [packages/stogger-eliot/src/stogger_eliot/eliot_integration.py:22] — Human-readable action trace destination.
- `stogger_eliot.eliot_integration.log_action` — source: [packages/stogger-eliot/src/stogger_eliot/eliot_integration.py:243] — Context manager for logging an action.
- `stogger_eliot.eliot_integration.log_call` — source: [packages/stogger-eliot/src/stogger_eliot/eliot_integration.py:247] — Decorator to log function calls as Eliot actions.
- `stogger_eliot.eliot_integration.ELIOT_AVAILABLE` — source: [packages/stogger-eliot/src/stogger_eliot/eliot_integration.py:16] — Whether eliot is importable.

## Configuration Options

### StoggerConfig (from pyproject.toml `[tool.stogger]` section)

Source: [packages/stogger/src/stogger/config.py:48]

| Option | Type | Default | Source Line | Description |
|--------|------|---------|-------------|-------------|
| `verbose` | `bool` | `False` | config.py:67 | Enable trace-level verbose logging. |
| `logdir` | `Path\|None` | `None` | config.py:68 | Directory for log files. |
| `log_cmd_output` | `bool` | `False` | config.py:69 | Enable separate command output logging. |
| `log_to_console` | `bool` | `True` | config.py:70 | Enable console logging output. |
| `syslog_identifier` | `str` | `"stogger"` | config.py:71 | Syslog identifier for journal entries. |
| `show_caller_info` | `bool` | `False` | config.py:72 | Show caller file/line/function in logs. |
| `translation_dir` | `Path\|None` | `None` | config.py:73 | Directory containing translation TOML files. |
| `language` | `str` | `"en"` | config.py:74 | Language code for i18n. |
| `log_format` | `str` | `"simple"` | config.py:75 | Log format: `"simple"` or `"json"`. |
| `async_logging` | `bool` | `False` | config.py:76 | Enable asynchronous (non-blocking) logging via QueueHandler. |
| `enable_pii_scrubbing` | `bool` | `True` | config.py:77 | Enable PII scrubbing in log output. |
| `pii_redaction_text` | `str` | `"[REDACTED]"` | config.py:78 | Text used to replace scrubbed PII. |
| `enable_systemd` | `bool` | `True` | config.py:79 | Enable systemd journal integration. |
| `systemd_facility` | `str\|None` | `None` | config.py:80 | Syslog facility for journal entries. |
| `src_dir` | `str` | `"src"` | config.py:81 | Source directory for project structure detection. |

### AST Analysis sub-config (from `[tool.stogger.ast]`)

| Option | Type | Default | Source Line | Description |
|--------|------|---------|-------------|-------------|
| `ast.respect_gitignore` | `bool` | `True` | config.py:85 | Respect .gitignore when finding files. |
| `ast.max_parameters` | `int` | `8` | config.py:86 | Max function parameters before flagging. |
| `ast.logging_focus` | `bool` | `True` | config.py:87 | Focus analysis on logging-related code only. |
| `ast.enabled_patterns` | `list\|None` | `None` | config.py:88-91 | Specific AST patterns to enable. |

### SimpleFormatSettings (console renderer settings)

Source: [packages/stogger/src/stogger/config.py:392]

| Option | Type | Default | Source Line | Description |
|--------|------|---------|-------------|-------------|
| `min_level` | `str` | `"info"` | config.py:399 | Minimum log level to display. |
| `show_logger_brackets` | `bool` | `False` | config.py:400 | Show logger name in brackets. |
| `show_pid` | `bool` | `False` | config.py:401 | Show PID in log output. |
| `show_code_info` | `bool` | `False` | config.py:402 | Show caller code information. |
| `timestamp_format` | `str` | `"iso"` | config.py:403 | Timestamp format (iso, iso_no_z). |
| `pad_event_width` | `int` | `30` | config.py:404 | Padding width for event name column. |

### Environment Variables

| Variable | Source Line | Description |
|----------|-------------|-------------|
| `STOGGER_AST_METRICS` | cli.py:952 | JSON string passed to linter for unified display (set by check command). |
| `STOGGER_LINTER_FORMAT` | linter.py:685 | Output format for linter: `"table"` (default), `"json"`, or `"toml"`. |
| `JOURNAL_STREAM` | core.py:519 | If set, indicates running under systemd journal; suppresses console output. |
| `INVOCATION_ID` | core.py:811 | systemd invocation ID; makes command log filenames unique. |
| `SYSTEMD_EXEC_PID` | systemd_integration.py:128 | PID set by systemd; used to detect systemd environment. |
| `EDITOR` | live_editor.py:264 | External editor command for live editing (default: nano). |

### `init_logging()` keyword arguments (most commonly used)

Source: [packages/stogger/src/stogger/core.py:440]

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `verbose` | `bool` | `False` | Enable verbose/trace-level logging. |
| `logdir` | `Path\|None` | `None` | Directory for file logging. |
| `log_cmd_output` | `bool` | `False` | Enable command output file logging. |
| `log_to_console` | `bool` | `True` | Enable console logging. |
| `syslog_identifier` | `str` | `"stogger"` | Syslog identifier string. |
| `show_caller_info` | `bool` | `False` | Show code location in logs. |

### Project Structure Detection (`detect_project_structure`)

Source: [packages/stogger/src/stogger/config.py:123]

Reads from `[tool.stogger]` in pyproject.toml:
- `src_dir` — source directory name
- `exclude` — list of glob patterns to exclude from analysis

Also reads from `[tool.hatch.build.targets.wheel.packages]` and `[tool.pytest.ini_options.testpaths]`.
