# Implementation TODO - Kürze nicestlog docs Ausgabe, entferne ablenkenden Text

Beschreibe das Problem: nicestlog docs zeigt zu viel Text, speziell in best_practices.md der Anti-Patterns Abschnitt und Summary lenken ab. Kürze für bessere Fokussierung.

## Description

*(Scope, Motivation, Research, Related work – no checkboxes here!)*

- Problem statement: Zu viel Text in docs lenkt ab, besonders für User mit geringer Aufmerksamkeitsspanne.
- Why we want to solve it (value, impact): Schnellere Info-Aufnahme, bessere UX.
- Research / references: nicestlog docs zeigt docs-Dateien, best_practices.md ist zu lang.
- Constraints: Nur docs/user_guide/best_practices.md bearbeiten, Essentials behalten.

### Task Goal

- **Outcome we want**: nicestlog docs prägnanter, ablenkender Text entfernt.
- **Success criteria**: Anti-Patterns Abschnitt gekürzt, Summary gestrafft, Essentials bleiben.

______________________________________________________________________

## Tasks

*(Top-level numbered tasks with checkboxes, each with sub-structure – explicit, not vague)*

1. [ ] **Kürze Anti-Patterns Abschnitt in best_practices.md**

   - **Context**: Der Abschnitt über wrapper functions ist zu detailliert.

   - **Success criteria** (must be checked to finish task)

     - [ ] Wrapper functions Erklärung gekürzt
     - [ ] Detection-Teil entfernt oder gekürzt
     - [ ] Essentials bleiben

   - **Files to check/modify**

     - [ ] docs/user_guide/best_practices.md

   - **Steps** (always action verbs, explicit order)

     - [ ] Lies aktuellen Anti-Patterns Abschnitt
     - [ ] Entferne detaillierte Erklärung
     - [ ] Behalte kurze Warnung

   - **Commit message hint**: "docs: shorten anti-patterns section in best practices"

1. [ ] **Straffe Summary Abschnitt**

   - **Context**: Summary ist zu lang und repetitiv.

   - **Success criteria**

     - [ ] Summary gekürzt auf Essentials
     - [ ] Wiederholungen entfernt

   - **Files to check/modify**

     - [ ] docs/user_guide/best_practices.md

   - **Steps**

     - [ ] Lies Summary
     - [ ] Kürze auf 2-3 Bullet Points
     - [ ] Entferne redundanten Text

   - **Commit message hint**: "docs: streamline summary in best practices"