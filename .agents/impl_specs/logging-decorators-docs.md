---
lifecycle:
  requirements:
    completed_at: "2026-05-04T14:00:00Z"
    git_rev: "be50a11"
---

# logging-decorators-docs

## Context

The logging decorators (`log_call`, `log_result`, `log_operation`, `log_scope`) are implemented and functional (commit be50a11) but documentation-invisible. Docstrings lack structured parameter docs. Autoapi skips `_decorators.py` (underscore prefix). No user-facing prose exists. Users cannot discover or learn the decorators through docs.

## Decisions

### docstring-quality

#### Context

Existing docstrings describe behavior in 1-2 sentences but omit structured parameter documentation, return types, raised exceptions, and usage examples. Other stogger public APIs (e.g., `init_logging`) have full Args/Returns/Raises docstrings.

#### Decision

Enrich all 5 public docstrings (`log_call`, `log_result`, `log_operation`, `log_scope`, `LogScope`) with Google-style Args, Returns, Raises, and Examples sections. Match the quality of `init_logging` in `core.py`.

#### Alternatives

a. Numpy-style docstrings — inconsistent with existing codebase convention
b. Minimal docstrings + separate docs — forces users to look in two places

#### Consequences

`help(log_call)` and generated API docs both show complete usage information. Single source of truth per function.

### api-docs-visibility

#### Context

Autoapi skips `_decorators.py` because the `autoapi_skip_member` hook in `conf.py` rejects names starting with `_`. The re-exports in `core.py` are bare imports (`# noqa: F401`) so autoapi doesn't document them either. Generated `docs/api/stogger/core/index.rst` has zero decorator entries.

#### Decision

Add manual Sphinx directives to `docs/api/stogger/core/index.rst` for the 5 re-exported names. Use `.. py:function::` for decorators and `.. py:class::` for `LogScope`, with `:canonical:` pointing to `stogger._decorators` source. This keeps the private module hidden while surfacing the public API.

#### Alternatives

a. Modify `autoapi_skip_member` to allow `_decorators` — exposes private module internals
b. Move decorators to public `decorators.py` — violates architecture decision (Layer 2 placement)

#### Consequences

Decorators appear in generated HTML docs under `stogger.core`. Source links go to `_decorators.py` which is acceptable since users navigate via public API, not module internals.

### user-guide-integration

#### Context

`docs/user_guide/logging_patterns.md` has manual "Function Tracing" and "Timing Operations" patterns that are exactly what the decorators automate. Users reading that page have no indication that decorators exist.

#### Decision

Add a new "Decorators" section to `logging_patterns.md` after the "Common Patterns" section. Cover all 4 features (`@log_call`, `@log_result`, `@log_operation`, `log_scope()`) with practical examples. Cross-reference from the existing "Function Tracing" and "Timing Operations" subsections.

#### Alternatives

a. New standalone page `docs/user_guide/decorators.md` — fragments the logging patterns narrative
b. No user guide, rely on API docs only — poor discoverability for new users

#### Consequences

Users reading logging patterns naturally discover decorators. Single coherent page covers manual and automated approaches.

## Requirements

### Files to Modify

- **Modify**: `src/stogger/_decorators.py` — enriched docstrings for all 5 public names
- **Modify**: `docs/api/stogger/core/index.rst` — add decorator entries to summary lists and module contents
- **Modify**: `docs/user_guide/logging_patterns.md` — add "Decorators" section with examples

### Docstring Requirements

Each decorator must document: Args (func, include_args, exclude_args with types and semantics), event format (fields emitted), exception behavior. `LogScope` must document constructor args, `add_fields`, enter/exit lifecycle, async support. `log_scope` must document name and **fields parameters. All must include a 2-3 line usage example.

### User Guide Requirements

New section must show: basic usage of all 4 features, arg filtering example, exception handling example, async usage. Each example must be self-contained and runnable.

## References

- `.agents/impl_specs/logging-decorators.md` — original implementation spec with event schemas and interface contracts
