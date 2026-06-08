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
| 2026-06-06 | src/stogger/core.py | 74 | * | inline ignore | structlog processor, logging here would recurse |
| 2026-06-06 | src/stogger/core.py | 102 | complexity-needs-log | inline ignore | structlog formatter, output pipeline must not log |
| 2026-06-06 | src/stogger/core.py | 129 | complexity-needs-log | inline ignore | structlog formatter, output pipeline must not log |
| 2026-06-06 | src/stogger/core.py | 178 | complexity-needs-log | inline ignore | structlog processor, logging here would recurse |
| 2026-06-06 | src/stogger/core.py | 188 | * | inline ignore | structlog processor, logging here would recurse |
| 2026-06-06 | src/stogger/core.py | 200 | complexity-needs-log | inline ignore | structlog processor, logging here would recurse |
| 2026-06-06 | src/stogger/core.py | 214 | complexity-needs-log | inline ignore | structlog formatter, output pipeline must not log |
| 2026-06-08 | src/stogger/core.py | 226 | * | inline ignore | structlog formatter, output pipeline must not log |
| 2026-06-08 | src/stogger/core.py | 240 | complexity-needs-log | inline ignore | structlog formatter, output pipeline must not log |
| 2026-06-08 | src/stogger/core.py | 278 | * | inline ignore | structlog formatter, output pipeline must not log |
| 2026-06-08 | src/stogger/core.py | 290 | * | inline ignore | ANSI escape helper, output pipeline must not log |
| 2026-06-08 | src/stogger/core.py | 316 | * | inline ignore | structlog formatter, output pipeline must not log |
| 2026-06-08 | src/stogger/core.py | 335 | * | inline ignore | structlog formatter, output pipeline must not log |
| 2026-06-08 | src/stogger/core.py | 351 | * | inline ignore | structlog processor, logging here would recurse |
| 2026-06-08 | src/stogger/core.py | 384 | complexity-needs-log | inline ignore | structlog processor, logging here would recurse |
| 2026-06-08 | src/stogger/core.py | 413 | complexity-needs-log | inline ignore | structlog processor, logging here would recurse |
| 2026-06-08 | src/stogger/core.py | 435 | complexity-needs-log | inline ignore | structlog processor, logging here would recurse |
| 2026-06-08 | src/stogger/core.py | 449 | * | inline ignore | structlog processor, logging here would recurse |
| 2026-06-08 | src/stogger/core.py | 493 | complexity-needs-log | inline ignore | structlog processor, logging here would recurse |
| 2026-06-08 | src/stogger/core.py | 926 | * | inline ignore | structlog processor, logging here would recurse |
| 2026-06-08 | src/stogger/core.py | 970 | * | inline ignore | json fallback / serialization, output pipeline must not log |
| 2026-06-08 | src/stogger/core.py | 982 | complexity-needs-log | inline ignore | json fallback / serialization, output pipeline must not log |
| 2026-06-08 | src/stogger/core.py | 1004 | complexity-needs-log | inline ignore | structlog processor, logging here would recurse |
| 2026-06-08 | src/stogger/core.py | 1025 | * | inline ignore | structlog processor, logging here would recurse |
| 2026-06-06 | src/stogger/decorators.py | 32 | complexity-needs-log | inline ignore | filter helper inside log_call decorator, wrapper already logs the args |
| 2026-06-03 | src/stogger/systemd.py | - | per-file: complexity-needs-log | per-file-ignores | systemd journal bridge — sends directly to journald via AF_UNIX, not stogger. |
| 2026-06-03 | src/stogger/systemd.py | - | per-file: except-must-log | per-file-ignores | systemd journal bridge — sends directly to journald via AF_UNIX, not stogger. |

*30 suppressed violation(s).*
