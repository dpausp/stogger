# Nix Flake Integration

Dieses Projekt unterstützt [Nix Flakes](https://nixos.wiki/wiki/Flakes) für reproduzierbare Development-Environments und Dependency-Management.

## 🎯 Warum Nix + UV?

- **Nix**: Verwaltet System-Tools wie `ruff`, `mypy`, `pre-commit` (reproduzierbar, pinned)
- **UV**: Verwaltet Python-Dependencies (schnell, Python-ecosystem-nativ)
- **Best of both worlds**: System-level Reproduzierbarkeit + Python-ecosystem Kompatibilität

## 🚀 Quick Start

### Mit direnv (empfohlen)
```bash
# Einmalig: direnv installieren
nix profile install nixpkgs#direnv

# Im Projektverzeichnis
direnv allow

# Automatisch aktiviert beim cd ins Verzeichnis
cd mydevtools  # Environment wird automatisch geladen
```

### Manuell
```bash
# Development shell starten
nix develop

# Oder spezifische Shells
nix develop .#minimal    # Nur essentials
nix develop .#ci         # CI environment
```

## 🛠️ Verfügbare Environments

### Default Development Shell
```bash
nix develop
# Enthält: Python 3.13, UV, Ruff, MyPy, Bandit, Pre-commit, etc.
```

### Minimal Shell
```bash
nix develop .#minimal
# Enthält nur: Python, UV, Ruff, Git
```

### CI Shell
```bash
nix develop .#ci
# Optimiert für CI/CD: Python, UV, Ruff, MyPy, Bandit, Pre-commit
```

## 📦 Nix Apps

Direkte Ausführung ohne Shell:

```bash
# Formatierung
nix run .#format

# Linting
nix run .#lint

# Tests
nix run .#test

# Hauptprogramm
nix run .#mydevtools
```

## 🔧 Konfiguration

### Python Version ändern
```nix
# In flake.nix
python = pkgs.python312;  # Statt python313
```

### Tools hinzufügen/entfernen
```nix
# In flake.nix, devTools Liste
devTools = with pkgs; [
  # Bestehende tools...
  jq                    # JSON processor
  fd                    # Better find
  ripgrep              # Better grep
];
```

### UV Integration
```bash
# UV nutzt automatisch das Nix Python
uv sync                 # Installiert in Nix Python environment
uv run pytest          # Läuft mit Nix Python
```

## 🔄 Workflow Integration

### Mit doit
```bash
# Alle doit tasks funktionieren normal
doit list
doit format
doit lint
doit test
```

### Mit Pre-commit
```bash
# Pre-commit nutzt Nix tools automatisch
pre-commit run --all-files
```

### Mit Renovate
Renovate updated weiterhin:
- Python dependencies (pyproject.toml + uv.lock)
- Pre-commit hooks

Nix dependencies werden über `flake.lock` verwaltet:
```bash
# Nix dependencies updaten
nix flake update
```

## 🐳 Docker Integration

```dockerfile
# Dockerfile mit Nix
FROM nixos/nix:latest

COPY flake.nix flake.lock ./
RUN nix develop .#ci --command echo "Dependencies cached"

COPY . .
RUN nix develop .#ci --command uv sync
RUN nix develop .#ci --command pytest
```

## 🔍 Troubleshooting

### Direnv lädt nicht
```bash
# Prüfen ob direnv installiert
which direnv

# .envrc erlauben
direnv allow

# Debug
direnv status
```

### UV findet Python nicht
```bash
# Manuell setzen
export UV_PYTHON=$(which python)

# Oder in der Shell
nix develop --command bash -c 'echo $UV_PYTHON'
```

### Flake Lock Konflikte
```bash
# Lock file neu generieren
rm flake.lock
nix flake lock

# Oder spezifische inputs updaten
nix flake lock --update-input nixpkgs
```

## 📊 Vergleich: Nix vs. UV vs. Traditional

| Tool | Scope | Pros | Cons |
|------|-------|------|------|
| **Nix** | System + Python | Reproduzierbar, deklarativ | Lernkurve, Nix-spezifisch |
| **UV** | Python only | Schnell, Standard-kompatibel | Nur Python ecosystem |
| **Traditional** | Manual | Bekannt, flexibel | Nicht reproduzierbar |

## 🎯 Best Practices

1. **Nix für System-Tools**: ruff, mypy, pre-commit, git
2. **UV für Python-Packages**: Alles aus pyproject.toml
3. **Direnv für Automatisierung**: Seamless environment switching
4. **Flake Lock Commits**: Committe flake.lock für Reproduzierbarkeit

## 🔗 Links

- [Nix Flakes](https://nixos.wiki/wiki/Flakes)
- [direnv](https://direnv.net/)
- [pyproject.nix](https://github.com/nix-community/pyproject.nix)
- [UV](https://docs.astral.sh/uv/)

## 🚀 Migration von anderen Tools

### Von Poetry
```bash
# Poetry dependencies nach pyproject.toml migrieren
poetry export --format requirements.txt | uv add -r -

# Nix environment aktivieren
nix develop
```

### Von Conda
```bash
# Environment exportieren
conda env export > environment.yml

# Relevante packages in flake.nix hinzufügen
# Python packages mit UV installieren
```

### Von venv
```bash
# Requirements extrahieren
pip freeze > requirements.txt

# Mit UV installieren
uv add -r requirements.txt

# Nix environment nutzen
nix develop
```