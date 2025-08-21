# Integration in bestehende Projekte

## 🎯 Copier-basierte Integration (Empfohlen)

**mydevtools verwendet jetzt standardmäßig [Copier](https://copier.readthedocs.io/) für moderne, template-basierte Projektkonfiguration.**

## 🔍 Schritt 1: Projekt analysieren

Bevor du mydevtools integrierst, analysiere dein bestehendes Projekt:

```bash
# In deinem Projekt-Verzeichnis
uv add mydevtools
mydevtools analyze
```

Das Tool zeigt dir:
- Welche Dependencies bereits vorhanden sind (Duplikate)
- Welche Tool-Konfigurationen kollidieren könnten
- **Empfehlung für Copier-basierte Migration**
- Einen Migrations-Plan

## 📦 Häufige Dependency-Konflikte

### Vor mydevtools:
```toml
[project]
dependencies = [
    "requests>=2.28.0",
    "black>=23.0.0",        # ❌ Duplikat
    "mypy>=1.0.0",          # ❌ Duplikat  
    "pytest>=7.0.0",       # ❌ Duplikat
]

[project.optional-dependencies]
dev = [
    "pylint>=2.15.0",       # ❌ Duplikat
    "bandit>=1.7.0",        # ❌ Duplikat
    "pre-commit>=3.0.0",    # ❌ Duplikat
]
```

### Nach mydevtools:
```toml
[project]
dependencies = [
    "requests>=2.28.0",
    "mydevtools>=0.1.0",    # ✅ Bringt alle Tools mit
]

# optional-dependencies.dev kann komplett weg oder nur projektspezifische Tools
```

## 🔧 Tool-Konfigurationen mit Copier

### Copier-Template Ansatz:
Das Copier-Template generiert eine vollständige `pyproject.toml` mit allen Tool-Konfigurationen:

```toml
# Generiert durch Copier-Template
[tool.ruff]
line-length = 88
target-version = "py311"
# ... vollständige Konfiguration

[tool.mypy]
python_version = "3.11"
warn_return_any = true
# ... vollständige Konfiguration

[tool.pytest.ini_options]
testpaths = ["tests"]
# ... vollständige Konfiguration
```

### Anpassungen nach Copier-Setup:
```toml
# Nach dem Copier-Setup kannst du Einstellungen überschreiben
[tool.ruff]
line-length = 100        # ✅ Überschreibt Template-Default

[tool.mypy]
strict = true           # ✅ Zusätzliche Einstellung

# Projektspezifische Ignores
[[tool.mypy.overrides]]
module = "third_party.*"
ignore_missing_imports = true
```

### Template-Updates:
```bash
# Template-Updates übernehmen
mydevtools setup  # Copier fragt nach Updates

# Oder explizit updaten
copier update
```

## 🚀 Migrations-Workflow

### Copier-basiert (empfohlen):
```bash
# 1. Projekt analysieren
mydevtools analyze

# 2. Copier-Setup durchführen
mydevtools setup  # Verwendet automatisch Copier-Template

# 3. Interaktive Konfiguration (optional)
mydevtools setup --interactive

# 4. Mit automatischer Dependency-Bereinigung
mydevtools setup --clean-deps

# 5. Testen
doit check
pre-commit run --all-files
```

### Legacy-Modus (fallback):
```bash
# 1. Backup erstellen
cp pyproject.toml pyproject.toml.backup

# 2. mydevtools installieren
uv add mydevtools

# 3. Legacy-Setup verwenden
mydevtools setup --no-copier

# 4. Manuelle Dependency-Bereinigung
uv remove black mypy pytest pylint bandit pre-commit isort flake8

# 5. Pre-commit installieren
uv run pre-commit install

# 6. Testen
doit check
pre-commit run --all-files
```

### Vorteile des Copier-Ansatzes:
- ✅ **Konsistente Updates**: Template-Änderungen können einfach übernommen werden
- ✅ **Vollständige pyproject.toml**: Alle Tool-Konfigurationen in einer Datei
- ✅ **Interaktive Optionen**: Anpassbare Projekteinstellungen
- ✅ **Versionierung**: Reproduzierbare Template-Versionen

## ⚠️ Häufige Probleme

### Problem: "Tool XY not found"
```bash
# Lösung: uv sync ausführen
uv sync
```

### Problem: Konfligierende Tool-Versionen
```bash
# Lösung: Alte Dependencies komplett entfernen
uv remove black mypy pytest pylint bandit pre-commit isort flake8 safety vulture radon
uv add mydevtools
uv sync
```

### Problem: Pre-commit Hooks funktionieren nicht
```bash
# Lösung: Hooks neu installieren
uv run pre-commit uninstall
uv run pre-commit install
uv run pre-commit run --all-files
```

### Problem: Bestehende Configs werden ignoriert
```bash
# Mit Copier: Configs sind direkt in der pyproject.toml
# Keine externen Package-Configs mehr
# Alle Konfigurationen sind lokal und anpassbar
```

### Problem: Copier-Template nicht gefunden
```bash
# Lösung: Copier installieren
uv add copier

# Oder Legacy-Modus verwenden
mydevtools setup --no-copier
```

## 🎯 Best Practices

### 1. Copier-Template als Basis verwenden
```bash
# Immer mit Copier starten für konsistente Basis
mydevtools setup

# Template-Updates regelmäßig übernehmen
mydevtools setup  # Copier erkennt Updates automatisch
```

### 2. Projektspezifische Anpassungen
```toml
# Template generiert Basis-Konfiguration
# Dann projektspezifisch anpassen
[tool.ruff]
line-length = 100  # Projekt-spezifische Anpassung

[tool.mypy]
strict = true      # Zusätzliche Einstellungen
```

### 2. Projektspezifische Ignores
```toml
[tool.vulture]
# Zusätzliche Ignores für dein Projekt
paths = ["src/", "scripts/"]
ignore_names = ["_*", "test_*"]

[tool.pylint.messages_control]
# Zusätzliche Disables für dein Projekt  
disable = ["C0103"]  # invalid-name für dein Projekt OK
```

### 3. Template-Versionierung
```bash
# Bestimmte Template-Version verwenden
mydevtools setup --interactive  # Wähle Template-Version

# Template-Updates kontrolliert übernehmen
copier update --answers-file .copier-answers.yml
```

### 4. Schrittweise Migration
```bash
# 1. Erst nur mydevtools installieren
uv add mydevtools

# 2. Copier-Setup durchführen
mydevtools setup

# 3. Neue Tools einzeln testen
uv run black --check .
uv run mypy .

# 3. Configs anpassen
# 4. Alte Dependencies entfernen
# 5. Pre-commit setup
```

## 📋 Checkliste für Migration

- [ ] Backup von pyproject.toml erstellt
- [ ] `mydevtools analyze` ausgeführt
- [ ] Dependency-Konflikte aufgelöst
- [ ] Tool-Konfigurationen gemerged/ersetzt
- [ ] `doit check` läuft durch
- [ ] Pre-commit hooks funktionieren
- [ ] CI/CD Pipeline angepasst (falls nötig)
- [ ] Team über Änderungen informiert