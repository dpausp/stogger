---
lifecycle:
  design:
    completed_at: "2026-05-03T19:00:00Z"
    draft: .agents/drafts/pytest-stogger-new-checks.md
---

## Context

6 new AST-based logging convention checks for pytest-stogger, plus WARNING-level rule infrastructure. Based on analysis of ~280 log statements across consumer projects that identified gaps in consolidation detection, context limits, exception handling, and event-ID conventions.

## Decisions

### warning-infrastructure

#### Context

Two new rules use heuristic detection with higher false-positive risk. They should be visible but not fail tests.

#### Decision

Add a boolean severity flag to the rule spec dataclass. Rules flagged as WARNING emit via the Python warnings module (custom subclass of UserWarning) instead of raising a test failure. Rules not flagged continue raising violations as errors. The flag is a default that can be overridden by config.

#### Alternatives

a. All rules as ERROR — too strict for heuristic-based detection
b. Separate rule lists — duplicates registry architecture

#### Consequences

New flag on the rule spec dataclass. New warning class. Plugin runtest method has two processing paths: error rules raise StoggerViolationError, warning rules emit warnings.warn.

### consolidation-config

#### Context

The consolidation heuristic has false positives on legitimate multi-step logging.

#### Decision

Config option `consolidate_as_error` in `[tool.pytest-stogger]` promotes the consolidation rule from WARNING to ERROR at runtime.

#### Alternatives

a. Always WARNING — too weak for CI enforcement
b. Always ERROR — too many false positives in default usage

#### Consequences

The severity flag on the consolidation rule is overridden at runtime when the config option is set. One new config key.

### log-consolidate-repeated

#### Context

Multiple sequential log calls sharing keyword argument keys indicate a missed consolidation opportunity.

#### Decision

Detect 3+ sequential log calls within a function's top-level body that share at least one keyword argument key. WARNING level, configurable to ERROR. Violation message includes a concrete merge suggestion: the shared keys and all unique keys from the group. Supports inline ignore.

#### Alternatives

a. Include nested blocks — too many false positives
b. Require shared keyword values (not just keys) — too strict

#### Consequences

Only checks top-level function body statements, not nested control-flow blocks. Overlaps partially with log-bind-threshold when sequential calls share both keywords and level.

### log-debug-context-range

#### Context

DEBUG-level logs with excessive context create noise in development output.

#### Decision

Flag log.debug() calls with more than 5 keyword arguments. Hardcoded threshold, no configuration. ERROR severity.

#### Alternatives

a. Configurable threshold — unnecessary for a clear convention
b. Higher threshold (7) — too permissive

#### Consequences

Simple keyword count check on debug calls only. Violation suggests reducing context or promoting to info level.

### log-bind-threshold

#### Context

Repeated log calls at the same level in direct succession indicate events that could be expressed as a single statement.

#### Decision

Detect 3+ sequential log calls at the same level (debug/info/warning/error) within a function's top-level body where calls are directly adjacent or separated by at most one non-log line. ERROR severity.

#### Alternatives

a. Also detect in nested blocks — too noisy
b. Require shared keywords — already covered by log-consolidate-repeated

#### Consequences

Triggers on same-level proximity without requiring shared keywords. Distance constraint (max 1 line gap between calls) prevents false positives from logically distinct calls. Overlaps with log-consolidate-repeated when sequential calls share both level and keywords — both rules fire, acceptable since the fix addresses both.

### log-exception-not-in-except

#### Context

log.exception() produces a stacktrace, meaningless outside an except block and potentially confusing.

#### Decision

Flag log.exception() calls that are not inside an except handler. ERROR severity. No inline ignore — fix is always unambiguous (replace with log.error).

#### Alternatives

a. WARNING severity — too weak for clear misuse
b. With inline ignore — unnecessary, fix is clear

#### Consequences

Only checks direct log.*() calls, not bound loggers, matching the pattern of simpler existing rules.

### log-error-in-except

#### Context

log.error() in an except block loses the stacktrace that log.exception() provides automatically.

#### Decision

Flag log.error() calls inside except handlers. Suggest using log.exception(). ERROR severity. Resolves bound logger names the same way as the existing no-log-info-in-except rule.

#### Alternatives

a. WARNING — inconsistent with existing except-block rules
b. Not implement — suboptimal logging goes undetected

#### Consequences

Follows identical pattern to no-log-info-in-except. Migration: all log.error() in except blocks → log.exception(). Inline ignore possible via existing mechanism.

### log-warning-for-not-found

#### Context

Event-IDs containing "not-found", "missing", or "absent" describe conditions that deserve at least WARNING visibility.

#### Decision

Flag log.debug() and log.info() calls where the first positional argument (event-ID) contains any of the patterns: "not-found", "missing", "absent". WARNING severity. Supports inline ignore for legitimate cases.

#### Alternatives

a. ERROR severity — too strict, false positives likely
b. Configurable patterns — config bloat

#### Consequences

Pattern matching on string literal event-IDs only — dynamic event-IDs are not checked. Walks by function to enable inline ignore resolution.

## Requirements

- All 6 rules follow the existing registry pattern and return the same violation dict type
- Each rule has positive detection tests and clean-path tests using direct dict inspection
- WARNING-level rules get pytester integration tests verifying warnings.warn behavior
- ERROR-level rules get pytester integration tests verifying StoggerViolationError
- Config option `consolidate_as_error` gets integration test
- Violation messages include file path, line number, rule name, and actionable suggestion
- New rules registered in existing file-rules list with appropriate flags
- Zero-config: new rules run automatically, visible in test output without configuration
- WARNING rules do not fail tests; ERROR rules do
- All rules respect existing inline ignore mechanism where flagged

## Scope

- Include: 6 new file-rules, WARNING infrastructure, consolidate_as_error config
- Exclude: Changes to existing rules, logging-coverage check, autofix functionality

## References

- Requirements draft: `.agents/drafts/pytest-stogger-new-checks.md`
- Logging conventions: `CONVENTIONS.md`
