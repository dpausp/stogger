# adopt-pytest-patterns

## Context

Stogger's test suite contains 70+ substring assertions of the form
`assert "literal" in captured.err`. A targeted audit identified 11
HIGH-severity hotspots where renderer regressions or documentation drift
can pass silently — including exception traceback shape, output-section
ordering, multi-event ordering, and structured KV bindings. The user
requirement is mechanical: "wir dürfen keinen kram mehr bauen der by
default zu 99% wegdriftet".

Three independent throwaway experiments (EXP01–EXP03, under
`tests/experiments/`) each converted one HIGH hotspot to
`pytest-patterns` and confirmed convergent findings: failure diagnostics
improve categorically (per-line emoji-coded attribution with named
patterns), structural constraints become expressible (ordering,
co-occurrence, negative assertions, console/file parity), and the
`patterns` fixture auto-injects without conftest changes.

Scope of this spec: convert the Top-5 HIGH hotspots below. The remaining
6 HIGH and 14 MEDIUM/LOW hotspots are out of scope and convert
opportunistically when the surrounding test is touched for another
reason.

Conversion targets:

- `tests/test_core.py:305-335` — `_render_output_sections` (13
  substring checks, ~half tautological; section order and separator
  position unpinned)
- `tests/test_e2e_user_perspective.py:239-260` and
  `tests/test_e2e_single_module_app.py:142-168` — exception rendering
  (KV line asserted, multi-line `exception:` traceback block completely
  untested)
- `tests/test_e2e_single_module_app.py:38-77` — multi-event ordering
  (info/warning/error triad; event order, KV same-line binding, and
  console/file parity all undefended)
- `tests/test_core.py:693-705` — KV renderer branch with OR-disjunction
  (`assert K in msg or V in msg` accepts either alone)
- `/srv/s-dev/git/pytest-stogger/tests/impl_spec/test_tech_debt.py:205-221`
  — markdown table structure checked via 4 disjoint substrings (sibling
  repo; demonstrates cross-repo value)

## Decisions

### adopt-pytest-patterns

#### Context

Substring assertions cannot express ordering, co-occurrence, or
negative constraints. Failure messages are bare `AssertionError`. A
renderer change that reorders events, detaches KV bindings from their
event line, or drops the multi-line traceback block passes silently as
long as each substring still appears somewhere in the captured output.
The three experiments under `tests/experiments/` independently
demonstrate that pytest-patterns' declarative API (`in_order`,
`continuous`, `optional`, `refused`, `merge`) expresses exactly these
constraints, and its failure reporter emits a per-line status table
(`🟢=EXPECTED | ⚪️=OPTIONAL | 🟡=UNEXPECTED | 🔴=REFUSED/UNMATCHED`)
with named patterns attached.

#### Decision

Adopt `pytest-patterns` as a test dependency for stogger. Convert the
Top-5 HIGH hotspots to use its pattern API, replacing the original
substring assertions in place (not as companion tests — the experiment
files under `tests/experiments/` are throwaway prototypes and get
deleted once each conversion lands in the target file).

`pytest-patterns` is already registered in `[dependency-groups].test`
and pinned via `[tool.uv.sources]` in `pyproject.toml`.

#### Alternatives

a. **syrupy + freezegun** (snapshot-based with frozen time) — rejected.
   Snapshot diffs are opaque byte dumps without per-line structural
   attribution; normalizer boilerplate (timestamp/path/ANSI) duplicates
   what pytest-patterns handles inline; snapshots do not express the
   structural intent of the test (a reader cannot tell from a snapshot
   what the test is actually pinning).

b. **Status quo** — rejected. Drift continues undetected; the 11 HIGH
   hotspots remain as silent regression vectors.

c. **Hybrid: pytest-patterns for new tests, substring for existing** —
   rejected. Leaves HIGH hotspots indefinitely; creates two testing
   dialects in one repo; the conversion cost is bounded (each hotspot
   ~100 LOC, prototype already validated).

#### Consequences

Tests gain ordering, negative-assertion, and structural-shape coverage.
Failure diagnostics drop renderer-drift triage from minutes to seconds
(per-line labelled diff instead of bare `AssertionError`). Test LOC at
converted sites grows ~3× — accepted for the categorical quality gain.
Tests become dependent on a 0.3.x pre-1.0 plugin; see
`path-dependency-strategy`.

### ansi-stripping-helper

#### Context

pytest-patterns matches patterns line-by-line against literal text.
stogger's `ConsoleFileRenderer` emits ANSI CSI sequences when stderr
appears to be a TTY, and `capsys` captures them verbatim — so a pattern
line that should match an event line fails because the colored output
contains interspersed `\x1b[…m` codes. All three experiments hit this
gap identically and worked around it with the same ~3-line regex
helper.

#### Decision

Add a shared `strip_ansi` fixture/helper in `tests/conftest.py` that
removes ANSI CSI escape sequences from captured output. Pattern
assertions apply it before comparison: the test asserts against the
stripped text, not the raw capsys capture.

#### Alternatives

a. **Wait for pytest-patterns upstream `normalize` feature** (listed as
   TODO in the README) — rejected. No published ETA; blocks all three
   conversions indefinitely. The local helper is ~3 LOC and becomes
   obsolete (not technical debt) when upstream normalize lands.

#### Consequences

One small shared helper in `tests/conftest.py`. Documented gotcha for
adopters: `pattern_lines` does **not** strip indentation from
triple-quoted pattern strings despite its source comment claiming
otherwise — patterns must use unindented single-line concatenation
rather than indented triple-quoted blocks. (Discovered in EXP03; candidate for an upstream fix.)

### path-dependency-strategy

#### Context

`pytest-patterns` lives at `/srv/s-dev/git/pytest-patterns` and is
pinned as a non-editable path dependency via `[tool.uv.sources]` in
`pyproject.toml`. This makes the test setup host-specific: every
contributor and CI runner needs a checkout at that exact path, or
`uv sync` fails to resolve the dependency.

#### Decision

Accept the host-specific path-dep for now. Long-term: contribute fixes
upstream (the ANSI `normalize` feature, the `pattern_lines` indentation
bug) and publish `pytest-patterns` to PyPI, then drop the
`[tool.uv.sources]` override and replace it with a version pin in
`[dependency-groups].test`.

#### Alternatives

a. **Editable install (`editable = true`)** — rejected. Changes to the
   `pytest-patterns` source would silently change stogger's test
   outcomes without `uv sync` — which is itself a drift vector. The
   current non-editable behaviour (changes require explicit `uv sync`)
   is the correct contract.

b. **Vendor a copy into the stogger repo** — rejected. Divergence risk;
   dual maintenance; forks the upstream contribution path.

#### Consequences

Setup is host-specific until PyPI publish. Contributors must clone
`pytest-patterns` locally and keep it at `/srv/s-dev/git/pytest-patterns`
(or override the path). The dependency must be pinned to a specific
dev-tag for reproducibility — the current pin is the latest working
state, which should be tightened to an explicit version before merge.

## Verified By

## References

- `docs/dev/doc_testing_research.md` — full research report covering the
  drift problem, three experiments, convergent findings, and the bug
  discovered in pytest-patterns (`pattern_lines` indentation)
- `tests/experiments/test_exp01_exception_traceback.py` — exception
  rendering prototype
- `tests/experiments/test_exp02_render_output_sections.py` — output
  sections prototype
- `tests/experiments/test_exp03_event_ordering.py` — multi-event
  ordering and console/file parity prototype
- `/srv/s-dev/git/pytest-patterns/README.md` — pytest-patterns feature
  inventory and API documentation
- ADR `legacy-elimination` — adjacent cleanup work in the same area
