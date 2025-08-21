# TinyLlama Qualitätstests

## Übersicht

Das Skript `tests/test_tinyllama_quality.py` testet die Qualität von TinyLlama-Antworten mit verschiedenen Prompt-Kategorien und erstellt einen detaillierten Markdown-Report.

## Features

- **12 verschiedene Test-Kategorien**: Von einfachen Fragen bis zu komplexen technischen Problemen
- **Automatische Qualitätsbewertung**: 4 Kriterien (Relevanz, Kohärenz, Vollständigkeit, Sprachqualität)
- **Detaillierter Markdown-Report**: Vollständige Dokumentation aller Tests und Ergebnisse
- **Demo-Modus**: Funktioniert auch ohne installiertes TinyLlama-Model
- **Performance-Messung**: Antwortzeiten und Erfolgsraten

## Verwendung

### Mit echtem TinyLlama Model

```bash
# Model installieren (falls noch nicht vorhanden)
uv run llm install llm-llama-cpp
uv run llm llama-cpp download-model https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf

# Tests ausführen
cd tests
python test_tinyllama_quality.py
```

### Demo-Modus (ohne Model)

```bash
cd tests
python test_tinyllama_quality.py --demo
```

## Test-Kategorien

1. **Einfache Fragen** - Grundlegende Mathematik und Faktenwissen
2. **Programmierung** - Code-Generierung und technische Erklärungen
3. **Logik & Reasoning** - Logisches Schließen und Problemlösung
4. **Kreativität** - Reime und Geschichten
5. **Komplexe Fragen** - Technische Analysen und Vergleiche
6. **Deutsche Sprache** - Grammatik und Sprachverständnis
7. **Nonsense Test** - Umgang mit unsinnigen Fragen

## Bewertungskriterien

Jede Antwort wird auf einer Skala von 1-5 bewertet:

- **Relevanz**: Wie gut passt die Antwort zur Frage?
- **Kohärenz**: Ist die Antwort logisch und zusammenhängend?
- **Vollständigkeit**: Ist die Antwort ausführlich genug?
- **Sprachqualität**: Grammatik, Rechtschreibung, Stil

## Output

Das Skript erstellt einen detaillierten Report `tinyllama_quality_report.md` mit:

- Zusammenfassung der Gesamtleistung
- Qualität nach Kategorien
- Detaillierte Einzelergebnisse
- Fazit und Empfehlungen

## Beispiel-Ergebnis (Demo-Modus)

```
🧪 Starte TinyLlama Qualitätstests...
📝 Test 1/12: Einfache Fragen
   Prompt: Was ist 2 + 2?...
   ✅ Antwort in 0.5s (Score: 1.5/5)
...
🎯 Alle 12 Tests abgeschlossen!
📊 Generiere Report: tinyllama_quality_report.md
✅ Report gespeichert: tinyllama_quality_report.md
```

## Anpassungen

Du kannst das Skript leicht erweitern:

- Neue Test-Prompts in `get_test_prompts()` hinzufügen
- Bewertungskriterien in den `_assess_*()` Methoden anpassen
- Andere LLM-Models testen (Variable `self.model` ändern)

## Fazit

Dieses Tool hilft dir dabei, objektiv zu bewerten, ob TinyLlama für deine Anwendungsfälle geeignet ist oder ob du ein stärkeres Model benötigst.