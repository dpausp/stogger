Dogfooding summary for `uv run nicestlog check`

Key points:
- Files analyzed: 62
- Total lines: 14,287
- Log statements: 90
- Overall logging coverage: 0.6%
- Functions with logging: 90/747 (12.0%)
- Files needing attention: 60

Specific actionable findings:
- Change two internal info-level logs to debug in src/nicestlog/cli.py (lines ~248 and ~1693) to avoid W3-level issues.

Suggested next steps (pick one or more):
1) Auto-apply quick fixes: `uv run nicestlog check --fix` (will update the two info->debug spots).
2) Scope checks to library code to reduce noise: `uv run nicestlog check src/nicestlog`.
3) Decide policy for tests/docs/examples (ignore or lower severity) and add a config accordingly.
4) Start a targeted logging uplift in a few core modules (e.g., advanced_assistant.py, factory.py, i18n.py), adding structured debug logs around key operations and errors.
5) Tune thresholds/levels in the checker if this is expected for a library (favoring debug over info for internal flows).

See tmp_rovodev_nicestlog_check_report.txt for the full raw output.
