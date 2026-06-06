# Stogger Tech Debt

Diese Datei wird automatisch von **pytest-stogger** erzeugt und bietet eine Übersicht aller aktuell unterdrückten Stogger-Regelverletzungen.

Jede Regel hat einen konkreten Zweck: kebab-case-Event-IDs ermöglichen Log-Aggregation, `_replace_msg` erzeugt lesbare Meldungen, und der Verzicht auf f-Strings erlaubt strukturiertes Rendering — unterdrückte Regeln fehlen in der Produktion und verhindern bei Fehlern die Diagnose. Saubere Logging-Konventionen beschleunigen Debugging und erleichtern das Onboarding.

Um einen Eintrag zu beheben: **Datei und Zeile** in der Tabelle aufsuchen, verstehen was die Regel fordert, den Unterdrückungskommentar (`# stogger: ignore`) entfernen und das zugrunde liegende Problem beheben. Danach verschwindet der Eintrag beim nächsten Lauf automatisch.

| First Seen | File | Line | Rule | Mechanism | Rationale |
|---|---|---|---|---|---|
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
| 2026-06-06 | src/stogger/core.py | 226 | complexity-needs-log | inline ignore | structlog formatter, output pipeline must not log |
| 2026-06-06 | src/stogger/core.py | 264 | * | inline ignore | structlog formatter, output pipeline must not log |
| 2026-06-06 | src/stogger/core.py | 276 | * | inline ignore | ANSI escape helper, output pipeline must not log |
| 2026-06-06 | src/stogger/core.py | 302 | * | inline ignore | structlog formatter, output pipeline must not log |
| 2026-06-06 | src/stogger/core.py | 321 | * | inline ignore | structlog formatter, output pipeline must not log |
| 2026-06-06 | src/stogger/core.py | 337 | * | inline ignore | structlog processor, logging here would recurse |
| 2026-06-06 | src/stogger/core.py | 369 | complexity-needs-log | inline ignore | structlog processor, logging here would recurse |
| 2026-06-06 | src/stogger/core.py | 398 | complexity-needs-log | inline ignore | structlog processor, logging here would recurse |
| 2026-06-06 | src/stogger/core.py | 420 | complexity-needs-log | inline ignore | structlog processor, logging here would recurse |
| 2026-06-06 | src/stogger/core.py | 434 | * | inline ignore | structlog processor, logging here would recurse |
| 2026-06-06 | src/stogger/core.py | 478 | complexity-needs-log | inline ignore | structlog processor, logging here would recurse |
| 2026-06-06 | src/stogger/core.py | 912 | * | inline ignore | structlog processor, logging here would recurse |
| 2026-06-06 | src/stogger/core.py | 956 | * | inline ignore | json fallback / serialization, output pipeline must not log |
| 2026-06-06 | src/stogger/core.py | 968 | complexity-needs-log | inline ignore | json fallback / serialization, output pipeline must not log |
| 2026-06-06 | src/stogger/core.py | 990 | complexity-needs-log | inline ignore | structlog processor, logging here would recurse |
| 2026-06-06 | src/stogger/core.py | 1011 | * | inline ignore | structlog processor, logging here would recurse |
| 2026-06-06 | src/stogger/decorators.py | 32 | complexity-needs-log | inline ignore | filter helper inside log_call decorator, wrapper already logs the args |
| 2026-06-03 | src/stogger/systemd.py | - | per-file: complexity-needs-log | per-file-ignores | systemd journal bridge — sends directly to journald via AF_UNIX, not stogger. |
| 2026-06-03 | src/stogger/systemd.py | - | per-file: except-must-log | per-file-ignores | systemd journal bridge — sends directly to journald via AF_UNIX, not stogger. |

_29 suppressed violation(s)._
