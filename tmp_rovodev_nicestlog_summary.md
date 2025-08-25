Dogfooding summary for `uv run nicestlog check`

Key points:
- Files analyzed (scoped to src/nicestlog): 21
- Total lines: 7,514
- Log statements: 53
- Overall logging coverage: 0.7%
- Functions with logging: 53/282 (18.8%)
- Files needing attention: 21

Specific actionable findings:
- Fixed: two internal info-level logs downgraded to debug in src/nicestlog/cli.py (lines ~248 and ~1693).
- Fixed: advanced_assistant internal progress logs moved to debug (analysis-started, transformation-started, file-analysis-started, file-transformation-started, file-transformed, pattern-added).
- Fixed: i18n/factory internal info logs moved to debug for internal operations.

Suggested next steps (pick one or more):
1) Auto-apply quick fixes: already applied (cli.py info->debug updates).
2) Scope checks to library code to reduce noise: done via [tool.nicestlog].exclude (tests/docs/examples).
3) Decide policy for tests/docs/examples (ignore or lower severity) and add a config accordingly.
4) Start a targeted logging uplift in a few core modules (e.g., advanced_assistant.py, factory.py, i18n.py), adding structured debug logs around key operations and errors.
5) Tune thresholds/levels in the checker if this is expected for a library (favoring debug over info for internal flows).

See tmp_rovodev_nicestlog_check_report.txt for the full raw output.
