# Implementation TODO - Entferne negative Code-Beispiele aus docs

Beschreibe das Problem: Negative (❌) Code-Beispiele in docs verseuchen Agent-Kontext. Entferne sie, behalte nur positive (✅) Beispiele.

## Description

*(Scope, Motivation, Research, Related work – no checkboxes here!)*

- Problem statement: ❌ Beispiele lenken ab und verunreinigen Kontext für Agents.
- Why we want to solve it (value, impact): Sauberer Kontext, bessere Fokussierung auf korrekte Patterns.
- Research / references: In best_practices.md und anderen docs.
- Constraints: Nur ❌ Beispiele entfernen, ✅ Beispiele und Erklärungen behalten.

### Task Goal

- **Outcome we want**: Docs zeigen nur korrekte Code-Beispiele, keine negativen.
- **Success criteria**: Alle ❌ Beispiele entfernt, ✅ Beispiele bleiben.

______________________________________________________________________

## Tasks

*(Top-level numbered tasks with checkboxes, each with sub-structure – explicit, not vague)*

1. [ ] **Entferne ❌ Beispiele aus best_practices.md**

   - **Context**: Anti-Patterns zeigen schlechte Beispiele, die Kontext verseuchen.

   - **Success criteria** (must be checked to finish task)

     - [ ] Alle ❌ Code-Blöcke entfernt
     - [ ] ✅ Beispiele bleiben
     - [ ] Erklärungen angepasst falls nötig

   - **Files to check/modify**

     - [ ] docs/user_guide/best_practices.md

   - **Steps** (always action verbs, explicit order)

     - [ ] Durchsuche nach ❌ Beispielen
     - [ ] Entferne sie komplett
     - [ ] Stelle sicher, ✅ Beispiele bleiben klar

   - **Commit message hint**: "docs: remove negative code examples from best practices"

1. [ ] **Prüfe andere docs auf ❌ Beispiele**

   - **Context**: Stelle sicher, keine anderen docs betroffen.

   - **Success criteria**

     - [ ] Andere docs-Dateien geprüft
     - [ ] Keine ❌ Beispiele gefunden oder entfernt

   - **Files to check/modify**

     - [ ] docs/ Verzeichnis

   - **Steps**

     - [ ] Grep nach ❌ in docs/
     - [ ] Entferne falls gefunden

   - **Commit message hint**: "docs: check and remove negative examples from all docs"
