# Stogger Tech Debt

Diese Datei wird automatisch von **pytest-stogger** erzeugt und bietet eine Übersicht
aller aktuell unterdrückten Stogger-Regelverletzungen.

Jede Regel hat einen konkreten Zweck: kebab-case-Event-IDs ermöglichen Log-Aggregation,
`_replace_msg` erzeugt lesbare Meldungen, und der Verzicht auf f-Strings erlaubt
strukturiertes Rendering — unterdrückte Regeln fehlen in der Produktion und verhindern
bei Fehlern die Diagnose.
Saubere Logging-Konventionen beschleunigen Debugging und erleichtern das Onboarding.

Um einen Eintrag zu beheben: **Datei und Zeile** in der Tabelle aufsuchen, verstehen was
die Regel fordert, den Unterdrückungskommentar (`# stogger: ignore`) entfernen und das
zugrunde liegende Problem beheben.
Danach verschwindet der Eintrag beim nächsten Lauf automatisch.

| First Seen | File | Line | Rule | Mechanism | Rationale |
| --- | --- | --- | --- | --- | --- |
| 2026-06-03 | src/stogger/__init__.py | - | per-file: except-must-log | per-file-ignores | Package init — runs before logger is configured. |
| 2026-06-03 | src/stogger/_colors.py | - | per-file: complexity-needs-log | per-file-ignores | Low-level ANSI helpers — logging would corrupt colorized output. |
| 2026-06-03 | src/stogger/_colors.py | - | per-file: except-must-log | per-file-ignores | Low-level ANSI helpers — logging would corrupt colorized output. |
| 2026-06-22 | src/stogger/core.py | 111 | * | inline ignore | structlog processor, logging here would recurse |
| 2026-06-22 | src/stogger/core.py | 139 | complexity-needs-log | inline ignore | structlog formatter, output pipeline must not log |
| 2026-06-22 | src/stogger/core.py | 166 | complexity-needs-log | inline ignore | structlog formatter, output pipeline must not log |
| 2026-06-22 | src/stogger/core.py | 229 | complexity-needs-log | inline ignore | structlog processor, logging here would recurse |
| 2026-06-22 | src/stogger/core.py | 239 | * | inline ignore | structlog processor, logging here would recurse |
| 2026-06-22 | src/stogger/core.py | 251 | complexity-needs-log | inline ignore | structlog processor, logging here would recurse |
| 2026-06-22 | src/stogger/core.py | 265 | complexity-needs-log | inline ignore | structlog formatter, output pipeline must not log |
| 2026-06-22 | src/stogger/core.py | 277 | * | inline ignore | structlog formatter, output pipeline must not log |
| 2026-06-22 | src/stogger/core.py | 291 | complexity-needs-log | inline ignore | structlog formatter, output pipeline must not log |
| 2026-06-22 | src/stogger/core.py | 329 | * | inline ignore | structlog formatter, output pipeline must not log |
| 2026-06-22 | src/stogger/core.py | 341 | * | inline ignore | ANSI escape helper, output pipeline must not log |
| 2026-06-22 | src/stogger/core.py | 367 | * | inline ignore | structlog formatter, output pipeline must not log |
| 2026-06-22 | src/stogger/core.py | 386 | * | inline ignore | structlog formatter, output pipeline must not log |
| 2026-06-22 | src/stogger/core.py | 402 | * | inline ignore | structlog processor, logging here would recurse |
| 2026-06-22 | src/stogger/core.py | 435 | complexity-needs-log | inline ignore | structlog processor, logging here would recurse |
| 2026-06-22 | src/stogger/core.py | 464 | complexity-needs-log | inline ignore | structlog processor, logging here would recurse |
| 2026-06-22 | src/stogger/core.py | 486 | complexity-needs-log | inline ignore | structlog processor, logging here would recurse |
| 2026-06-22 | src/stogger/core.py | 500 | * | inline ignore | structlog processor, logging here would recurse |
| 2026-06-22 | src/stogger/core.py | 544 | complexity-needs-log | inline ignore | structlog processor, logging here would recurse |
| 2026-06-22 | src/stogger/core.py | 1055 | * | inline ignore | structlog processor, logging here would recurse |
| 2026-06-22 | src/stogger/core.py | 1099 | * | inline ignore | json fallback / serialization, output pipeline must not log |
| 2026-06-22 | src/stogger/core.py | 1111 | complexity-needs-log | inline ignore | json fallback / serialization, output pipeline must not log |
| 2026-06-22 | src/stogger/core.py | 1133 | complexity-needs-log | inline ignore | structlog processor, logging here would recurse |
| 2026-06-22 | src/stogger/core.py | 1154 | * | inline ignore | structlog processor, logging here would recurse |
| 2026-06-22 | src/stogger/core.py | 1178 | * | inline ignore | this IS the last processor; log.*() here would recurse |
| 2026-06-22 | src/stogger/core.py | 1235 | * | inline ignore | this IS the logger; calling log.*() here would recurse |
| 2026-06-23 | src/stogger/core.py | 1283 | exempt: logging-cmd-output-no-logdir | exempt_event_ids | - |
| 2026-06-23 | src/stogger/core.py | 1301 | exempt: cmd-output-file-open-failed | exempt_event_ids | - |
| 2026-06-23 | src/stogger/core.py | 1310 | exempt: logging-cmd-output | exempt_event_ids | - |
| 2026-06-23 | src/stogger/core.py | 1344 | exempt: logging-cmd-output-file-not-found | exempt_event_ids | - |
| 2026-06-30 | src/stogger/core.py | 1353 | exempt: logging-cmd-output-drop | exempt_event_ids | - |
| 2026-06-06 | src/stogger/decorators.py | 32 | complexity-needs-log | inline ignore | filter helper inside log_call decorator, wrapper already logs the args |
| 2026-06-22 | src/stogger/rotation.py | - | per-file: complexity-needs-log | per-file-ignores | hot path; logging during rotation would recurse back through the pipeline. |
| 2026-06-03 | src/stogger/systemd.py | - | per-file: complexity-needs-log | per-file-ignores | systemd journal bridge — sends directly to journald via AF_UNIX, not stogger. |
| 2026-06-03 | src/stogger/systemd.py | - | per-file: except-must-log | per-file-ignores | systemd journal bridge — sends directly to journald via AF_UNIX, not stogger. |

*38 suppressed violation(s).*
