# Documentation Validation Report

**Generated**: 2026-03-27
**Project**: stogger v0.3.5

## Summary

- Total issues found: 28
- Files analyzed: 22 source modules, 10 API guide docs, 4 user guide docs, autoapi-generated docs

## Documentation Overview

| File | API Coverage | Test Coverage | Examples | Links | Status |
|------|--------------|---------------|----------|-------|--------|
| api_guides/core.md | 95% | 82.7% | ✅ 5 OK | ✅ OK | Good |
| api_guides/factory.md | 90% | 82.7% | ✅ 3 OK | ✅ OK | Good |
| api_guides/config.md | 95% | 93.4% | ✅ 4 OK | ✅ OK | Good |
| api_guides/advanced_assistant.md | 85% | 84.9% | ✅ 6 OK | ✅ OK | Good |
| api_guides/log_reviewer.md | 80% | 98.0% | ✅ 2 OK | ✅ OK | Good |
| api_guides/cli.md | 60% | 52.0% | ⚠️ 2 outdated | ✅ OK | Needs Work |
| api_guides/assistant.md | 70% | 67.1% | ✅ 1 OK | ✅ OK | Needs Work |
| api_guides/linter.md | 65% | 73.7% | ✅ 1 OK | ✅ OK | Needs Work |
| api_guides/pii_scrubber.md | 75% | 70.5% | ✅ 1 OK | ✅ OK | Needs Work |
| user_guide/getting_started.md | N/A | N/A | ✅ 4 OK | ⚠️ 1 orphan | Good |
| user_guide/best_practices.md | N/A | N/A | ✅ 12 OK | ✅ OK | Good |

### Status Categories

- **Good**: All checks pass, documentation is healthy
- **Needs Work**: Minor issues, documentation is usable
- **Critical**: Major issues, documentation is misleading or broken
- **N/A**: Not applicable (e.g., prose docs without APIs)

### Column Definitions

- **API Coverage**: % of public APIs documented
- **Test Coverage**: % of documented features with tests
- **Examples**: ✅ OK / ⚠️ X outdated / ❌ None / ❌ X broken
- **Links**: ✅ OK / ⚠️ X orphans / ❌ X broken

## Detailed Issues

### API Coverage Issues

#### Undocumented APIs

- `stogger.core.PartialFormatter` - Class documented in autoapi but not in api_guides/core.md
- `stogger.core.TranslationProcessor` - Class documented in autoapi but not in api_guides/core.md
- `stogger.core.CmdOutputFileRenderer` - Class documented in autoapi but not in api_guides/core.md
- `stogger.core.MultiRenderer` - Class documented in autoapi but not in api_guides/core.md
- `stogger.core.SelectRenderedString` - Class documented in autoapi but not in api_guides/core.md
- `stogger.core.log_to_stdlib()` - Function documented in autoapi but not in api_guides/core.md
- `stogger.core.prefix()` - Function documented in autoapi but not in api_guides/core.md
- `stogger.factory.build_shared_processors()` - Missing parameter docs in api_guides/factory.md
- `stogger.config.ProjectStructure` - Class missing from api_guides/config.md overview
- `stogger.config.SimpleFormatSettings` - Minimal documentation in api_guides/config.md
- `stogger.i18n.NicestlogTranslator` - Not documented in any api_guides
- `stogger.i18n.set_language()` - Exported function not documented
- `stogger.i18n.demo_translations()` - Exported function not documented
- `stoggertools.interactive_transformer.InteractiveTransformer` - Not documented in api_guides
- `stoggertools.interactive_transformer.UserChoice` - Enum not documented
- `stoggertools.interactive_transformer.TransformationProposal` - Dataclass not documented
- `stoggertools.interactive_transformer.InteractiveSession` - Dataclass not documented
- `stogger_eliot.HumanReadableEliotDestination` - Not documented in api_guides
- `stogger_eliot.log_action()` - Decorator not documented
- `stogger_eliot.log_call()` - Decorator not documented

#### Outdated Documentation

- `api_guides/cli.md` - References `stoggertools analyze` command which does not exist in current CLI
- `api_guides/cli.md` - References `stoggertools transform` command which does not exist in current CLI
- `api_guides/cli.md` - Missing documentation for `stoggertools check`, `stoggertools migrate`, `stoggertools docs` commands
- `api_guides/linter.md` - References `lint_file()` function which does not exist; actual API is `analyze_file()` and `lint_directory()`
- `api_guides/log_reviewer.md` - References `review_file()` and `review_directory()` functions which do not exist; actual API is `LogQualityReviewer.analyze_log_file()` and `LogQualityReviewer.analyze_log_content()`

### Test Coverage Issues

#### Documented but Untested (High Risk)

- `stogger_web.web_dashboard` - Module exposed in `__init__.py` but tests conditional on Flask availability
- `stoggertools.live_editor` - Module exposed in `__init__.py` with limited test coverage
- `stoggertools.cli_output_transformer` - Module exposed but minimal test coverage
- `stogger.log_statement_analyzer` - Module used but not directly tested
- `stoggertools.project_analyzer` - Module exposed in CLI but limited test coverage

#### Tested but Undocumented

- `stoggertools.interactive_transformer` - 67.1% coverage, exposed publicly but no api_guides page
- `stogger_eliot` - 82.7% coverage, exposed publicly but no api_guides page
- `stogger.gitignore_utils` - Well tested, used internally, exposed in CLI
- `stogger.i18n_check` - Has test coverage, CLI command exists, no api_guides

### Code Example Issues

#### Outdated Examples

- `docs/api_guides/cli.md:15-18` - Example uses `stoggertools analyze` command which does not exist
- `docs/api_guides/cli.md:21-24` - Example uses `stoggertools transform` command which does not exist

#### Missing Import Context

- `docs/api_guides/linter.md:14-20` - Example references `lint_file()` which does not exist; should use `analyze_file()` or `lint_directory()`
- `docs/api_guides/log_reviewer.md:24-29` - Example references `review_file()` which does not exist; should use `LogQualityReviewer` class

#### Incomplete Examples

- `docs/user_guide/getting_started.md:68-73` - Example references `configure()` API which is noted as "not finalized"
- `docs/api_guides/pii_scrubber.md:19-22` - Example incomplete - missing structlog.configure() setup

### Internal Consistency Issues

#### Broken Links

- `docs/user_guide/getting_started.md:79` - Link to `../features/advanced_assistant.md` - valid
- `docs/user_guide/getting_started.md:80` - Link to `../development/api_reference` - target exists

#### Orphaned Pages

- `docs/development/analysis_summary.md` - Not in toctree, no incoming links from main docs
- `docs/development/cleanup_plan.md` - Not in toctree, development-only content
- `docs/development/try_except_analysis.md` - Not in toctree, internal analysis
- `docs/development/command_restructure_plan.md` - Not in toctree, planning document
- `docs/development/todo.md` - Not in toctree, internal tracking
- `docs/development/lessons_dogfooding_check.md` - Not in toctree, internal notes
- `docs/specs/logging_rules_spec.md` - Not in toctree, specification document

#### Missing Cross-References

- `docs/api_guides/core.md` - Does not reference related `factory.md` module
- `docs/api_guides/factory.md` - Does not reference `config.md` for configuration options
- `docs/user_guide/best_practices.md` - References `logging_conventions.md` but link could be more prominent
- No api_guides page for `i18n.py` despite being exported in `__init__.py`
- No api_guides page for `interactive_transformer.py` despite being exported in `__init__.py`
- No api_guides page for `eliot_integration.py` despite being exported in `__init__.py`

## API Surface Analysis

### Exported in `__init__.py` (32 items)

| Item | Source Module | Has api_guides | Test Coverage |
|------|---------------|----------------|---------------|
| `JournalLogger` | core | ✅ | High |
| `JournalLoggerFactory` | core | ✅ | High |
| `MultiOptimisticLogger` | core | ✅ | High |
| `MultiOptimisticLoggerFactory` | core | ✅ | High |
| `StoggerConfig` | config | ✅ | High (93.4%) |
| `SystemdJournalRenderer` | core | ✅ | High |
| `analyze_python_file` | advanced_assistant | ✅ | High (84.9%) |
| `arsch` | i18n | ❌ | Unknown |
| `create_advanced_assistant` | advanced_assistant | ✅ | High |
| `create_interactive_transformer` | interactive_transformer | ❌ | Medium |
| `create_live_editor` | live_editor | ❌ | Low |
| `create_pii_processor` | pii_scrubber | ✅ | Medium (70.5%) |
| `create_systemd_service_file` | systemd_integration | ❌ | Medium |
| `demo_pii_scrubbing` | pii_scrubber | ✅ | Medium |
| `demo_systemd_integration` | systemd_integration | ❌ | Medium |
| `drop_cmd_output_logfile` | core | ✅ | High |
| `edit_code_live` | live_editor | ❌ | Low |
| `get_log_stats` | web_dashboard | ❌ | Low |
| `get_translator` | i18n | ❌ | Unknown |
| `init_command_logging` | core | ✅ | High |
| `init_early_logging` | core | ✅ | High |
| `init_i18n` | i18n | ❌ | Unknown |
| `init_logging` | core | ✅ | High |
| `leiwand` | i18n | ❌ | Unknown |
| `logging_initialized` | core | ✅ | High |
| `main` | cli | ✅ | Medium (52.0%) |
| `migrate_directory` | assistant | ✅ | Medium (67.1%) |
| `oida` | i18n | ❌ | Unknown |
| `run_dashboard` | web_dashboard | ❌ | Low |
| `setup_eliot_logging` | eliot_integration | ❌ | High |
| `setup_systemd_logging` | systemd_integration | ❌ | Medium |
| `setup_web_logging` | web_dashboard | ❌ | Low |
| `t` | i18n | ❌ | Unknown |
| `transform_directory_interactive` | interactive_transformer | ❌ | Medium |
| `transform_file_interactive` | interactive_transformer | ❌ | Medium |
| `transform_python_file` | advanced_assistant | ✅ | High |

### Missing Documentation Coverage

**i18n module** (6 exports):
- `arsch`, `leiwand`, `oida`, `t`, `get_translator`, `init_i18n`

**interactive_transformer module** (3 exports):
- `create_interactive_transformer`, `transform_directory_interactive`, `transform_file_interactive`

**live_editor module** (2 exports):
- `create_live_editor`, `edit_code_live`

**web_dashboard module** (3 exports):
- `get_log_stats`, `run_dashboard`, `setup_web_logging`

**systemd_integration module** (3 exports):
- `create_systemd_service_file`, `demo_systemd_integration`, `setup_systemd_logging`

**eliot_integration module** (1 export):
- `setup_eliot_logging`

## Test Coverage Summary

Based on available coverage data and docs/conf.py COVERAGE_TIERS:

### Tier 1: High Coverage (≥80%)

| Module | Coverage | Status |
|--------|----------|--------|
| config | 93.4% | Documented |
| log_reviewer | 98.0% | Documented |
| advanced_assistant | 84.9% | Documented |
| core | 82.7% | Documented |
| factory | 82.7% | Documented |
| eliot_integration | 82.7% | **Not documented** |
| journal_viewer | High | Documented (autoapi) |
| _regexes | High | Internal |
| __main__ | High | Internal |
| i18n | High | **Not documented** |

### Tier 2: Medium Coverage (40-80%)

| Module | Coverage | Status |
|--------|----------|--------|
| linter | 73.7% | Documented |
| pii_scrubber | 70.5% | Documented |
| assistant | 67.1% | Documented |
| interactive_transformer | ~67% | **Not documented** |
| gitignore_utils | Medium | Internal |
| project_analyzer | Medium | Internal |
| i18n_check | Medium | Internal |
| cli | 52.0% | Documented (outdated) |
| systemd_integration | Medium | **Not documented** |

### Tier 3: Low Coverage (<40%)

| Module | Coverage | Status |
|--------|----------|--------|
| live_editor | Low | **Not documented** |
| web_dashboard | Low | **Not documented** |
| log_statement_analyzer | Low | Internal |
| cli_output_transformer | Low | Internal |

## Coverage Tiers vs Documentation

The project defines coverage tiers in `docs/conf.py` but there are discrepancies:

| Tier | Expected | Actual Documentation |
|------|----------|---------------------|
| i18n | Tier 1 | ❌ No api_guides |
| eliot_integration | Tier 1 | ❌ No api_guides |
| interactive_transformer | Tier 2 | ❌ No api_guides |
| systemd_integration | Tier 2 | ❌ No api_guides |

## Recommendations Summary

1. **Critical**: Update `api_guides/cli.md` - commands referenced do not exist
2. **Critical**: Fix `api_guides/linter.md` - `lint_file()` function does not exist
3. **Critical**: Fix `api_guides/log_reviewer.md` - `review_file()` function does not exist
4. **High**: Add api_guides for `i18n` module (6 exports)
5. **High**: Add api_guides for `interactive_transformer` module (3 exports)
6. **High**: Add api_guides for `eliot_integration` module (1 export)
7. **Medium**: Add api_guides for `systemd_integration` module (3 exports)
8. **Medium**: Review orphaned development docs for removal or integration
9. **Low**: Add api_guides for `web_dashboard` module (3 exports)
10. **Low**: Add api_guides for `live_editor` module (2 exports)
