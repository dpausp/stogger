---
lifecycle:
  requirements:
    completed_at: "2026-05-03T18:00:00Z"
    git_rev: c4f0f2b
---

## Problem

pytest-stogger erzwingt 12 AST-basierte Logging-Konventionen. Basierend auf einem Sample von ~280 Log-Statements aus 3 Projekten (batou-type, code-rag, docdisco) wurden 6 Lücken identifiziert, die zu unnötigem Log-Noise, fehlendem Context und ungenutztem Structlog-Potential führen.

## Binding Decisions

### scope-batch

#### Context

Es gibt 6 vorgeschlagene Checks. Zu viele auf einmal risking Qualität, zu wenige liefern nicht den erwarteten Mehrwert.

#### Decision

Alle 6 Checks in einem Durchgang umsetzen:
1. `log-consolidate-repeated` — 3+ Log-Calls in direkter Folge mit shared Context → zusammenfassen
2. `log-debug-context-range` — max 5 key-value pairs bei DEBUG
3. `log-bind-threshold` — wiederholter key-value 3+ Mal → log.bind() nutzen
4. `log-exception-not-in-except` — log.exception() außerhalb except-Block
5. `log-error-in-except` — log.error() in except-Block statt log.exception()
6. `log-warning-for-not-found` — WARNING bei "not found" Event-IDs

#### Alternatives

a. Nur Top 3 — schneller, aber Lücken bleiben
b. Nur 1 MVP — zu wenig Impact

#### Consequences

Größerer Durchgang, aber alle Checks folgen demselben Registry-Pattern und teilen Helper-Funktionen.

### consolidate-severity

#### Context

Die Consolidation-Heuristik hat False Positives bei legitimen Multi-Step-Logging.

#### Decision

Config-gesteuert: Default WARNING, kann per Config auf ERROR gestellt werden via `consolidate_as_error = true`.

#### Alternatives

a. Immer WARNING — zu schwach für CI
b. Immer ERROR — zu viele False Positives

#### Consequences

Neue Config-Option `consolidate_as_error` in `[tool.pytest-stogger]`.

### debug-range-config

#### Context

Konvention ist "2-3 key-values normal, max 5". Braucht das einen konfigurierbaren Schwellwert?

#### Decision

Fester Wert 5 — hardcoded wie die meisten Rules. Kein Config-Overhead.

#### Alternatives

a. Per Config (debug_max_context) — flexibel aber unnötig
b. Nur Warning bei >7 — zu großzügig

#### Consequences

Hardgrenze bei 5 key-value pairs für DEBUG. Darüber → Violation.

### exception-placement

#### Context

log.exception() erzeugt einen Stacktrace — ohne except-Block ist das sinnlos oder verwirrend.

#### Decision

Eigenständiger Check: `log-exception-not-in-except`. log.exception() nur erlaubt innerhalb von except-Blöcken.

#### Alternatives

a. Mit Inline-Ignore — nicht nötig, klarer Fix
b. Nicht umsetzen — zu noisy

#### Consequences

Klare Rule mit klarer Migration: exception() → error() wenn außerhalb von except.

### consolidate-message-ux

#### Context

Fehlermeldungen müssen dem User helfen, nicht nur informieren.

#### Decision

Zeige Merge-Vorschlag: betroffene Zeilen + konkreter Vorschlag wie die zusammengefasste Statement aussehen könnte.

#### Alternatives

a. Nur Zeilen + Count — nicht hilfreich genug
b. Diff-Style — zu komplex für ersten Wurf

#### Consequences

Die Violation-Message enthält ein konkretes Code-Beispiel.

## Scope Boundaries

- INCLUDE: 6 neue File-Rules im bestehenden Registry-Pattern
- INCLUDE: Neue Config-Option `consolidate_as_error`
- EXCLUDE: Changes an bestehenden Rules
- EXCLUDE: Changes am logging-coverage Check
- EXCLUDE: Autofix-Funktionalität (nur Detection)

## Open Questions

- Severity der restlichen 5 Checks (ERROR wie bestehende Rules?)
- Default-Severity für bind-threshold und error-in-except
- Interface: wie werden die neuen Rules in --help und Status-Output sichtbar?

### severity-strategy

#### Context

6 neue Checks mit unterschiedlicher Heuristik-Qualität. Klare AST-basierte Rules können ERROR sein, heuristische sollten WARNING sein.

#### Decision

Gemischt:
- ERROR: `log-exception-not-in-except`, `log-error-in-except`, `log-debug-context-range`, `log-bind-threshold`
- WARNING (config-steuerbar): `log-consolidate-repeated`, `log-warning-for-not-found`

#### Alternatives

a. Alle ERROR — zu streng für heuristische Checks
b. Alle WARNING — zu schwach für klare Rules

#### Consequences

Zwei Severity-Level in der Rule-Architektur. Needs flag `needs_warning_severity` auf _RuleSpec oder Config-basiert.

### error-in-except-severity

#### Context

log.error() in except-Block verliert den Stacktrace — suboptimal aber nicht falsch.

#### Decision

ERROR — strenger als ursprünglich empfohlen. log.exception() ist in except-Blöcken immer die bessere Wahl.

#### Alternatives

a. WARNING — weniger Breakage aber schwächer
b. Nicht umsetzen — bestehende no-log-info-in-except reicht

#### Consequences

Migration: alle log.error() in except-Blöcken → log.exception(). Inline-Ignore möglich.

### warning-not-found-fp

#### Context

Pattern-Matching auf Event-IDs (*-not-found, *-missing, *-absent) hat False Positives.

#### Decision

Inline-Ignore: # stogger: ignore log-warning-for-not-found für legitime Fälle.

#### Alternatives

a. Exempt-List in Config — flexibel aber Config-Bloat
b. Nicht umsetzen — zu heuristisch

#### Consequences

Neue Rule mit needs_inline_ignores=True Flag.

### bind-threshold-value

#### Context

Wiederholter key-value in Scope → log.bind() nutzen.

#### Decision

Schwellwert 3 — konsistent mit bestehender check_bind_for_repeating die auch bei 3 Wiederholungen triggert.

#### Alternatives

a. 2 Mal — strenger
b. Config-gesteuert — unnötig, 3 ist bewährt

#### Consequences

Konsistente Schwelle im Codebase. Kein neuer Config-Wert nötig.

## Scope Boundaries (Updated)

- INCLUDE: 6 neue File-Rules im bestehenden Registry-Pattern
- INCLUDE: Neue Config-Option `consolidate_as_error`
- INCLUDE: Severity-Level ERROR vs WARNING für neue Rules
- EXCLUDE: Changes an bestehenden Rules
- EXCLUDE: Changes am logging-coverage Check
- EXCLUDE: Autofix-Funktionalität (nur Detection)

### warning-pytest-output

#### Context

WARNING-Level Rules sollen den Test nicht failen lassen, aber sichtbar sein.

#### Decision

Normale `pytest.warning` — Test besteht, Warning wird angezeigt. Konsistent mit Python-Warnings.

#### Alternatives

a. Eigener Item-Typ — zu komplex
b. Nur in Summary — nicht prominent genug

#### Consequences

Plugin nutzt `warnings.warn()` statt `StoggerViolationError` für WARNING-Level Rules.

### warning-flag-architecture

#### Context

Rule-Architektur braucht ein Konzept für Severity-Level.

#### Decision

Neues Flag `is_warning: bool = False` auf `_RuleSpec`. Plugin entscheidet basierend auf Flag ob ERROR oder WARNING.

#### Alternatives

a. Config pro Rule — flexibel aber Config-Bloat
b. Separate Rule-Liste — dupliziert Architektur

#### Consequences

Neues Feld auf _RuleSpec. Plugin.py muss zwei Pfade haben: ERROR-Path (bestehend) + WARNING-Path (neu, via warnings.warn).

### discoverability

#### Context

Neue Rules sollen für Consumer-Projekte sofort nützlich sein.

#### Decision

Automatisch sichtbar — Zero-Config. Neue Rules laufen wie bestehende, werden im Test-Output sichtbar.

#### Alternatives

a. Disabled per Default — sicher aber weniger nützlich

#### Consequences

Consumer-Projekte sehen neue Rules sofort. WARNING-Level Rules brechen nicht, ERROR-Level Rules können per disable_rules deaktiviert werden.

## Scope Boundaries (Final)

- INCLUDE: 6 neue File-Rules im bestehenden Registry-Pattern
- INCLUDE: Neues `is_warning` Flag auf `_RuleSpec`
- INCLUDE: WARNING-Path via `warnings.warn()` in plugin.py
- INCLUDE: Neue Config-Option `consolidate_as_error`
- EXCLUDE: Changes an bestehenden Rules
- EXCLUDE: Changes am logging-coverage Check
- EXCLUDE: Autofix-Funktionalität (nur Detection)

- Interface: wie werden die neuen Rules in --help und Status-Output sichtbar?
- Brauchen wir ein neues `needs_warning_severity` Flag auf `_RuleSpec`?
- Wie wird WARNING im pytest-Output dargestellt? ( eigenes Item-Type oder nur in Summary?)
