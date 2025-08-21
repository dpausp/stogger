# Renovate Bot Konfiguration

Dieses Projekt verwendet [Renovate Bot](https://docs.renovatebot.com/) für automatische Dependency-Updates.

## Konfigurationsdateien

- `renovate.json` - Haupt-Renovate-Konfiguration
- `.github/renovate.json5` - GitHub-spezifische Erweiterungen

## Features

### Automatische Updates für:
- **Python Dependencies** (`pyproject.toml`)
  - Haupt-Dependencies
  - Development Dependencies (`dependency-groups.dev`)
  - Optionale Dependencies (`dependency-groups.formatting`, etc.)
- **UV Lock File** (`uv.lock`)
- **Pre-commit Hooks** (`.pre-commit-config*.yaml`)
- **GitHub Actions** (falls vorhanden)

### Gruppierung und Scheduling
- **Wöchentliche Updates**: Montags vor 6 Uhr
- **Gruppierte PRs**: Python Dependencies werden zusammengefasst
- **Security Updates**: Sofortige Updates bei Sicherheitslücken
- **Lock File Maintenance**: Wöchentliche Aktualisierung der `uv.lock`

### Auto-Merge Regeln
- **Patch Updates**: Automatisch für dev/build Dependencies
- **Pre-commit Hooks**: Automatisch für alle Updates
- **GitHub Actions**: Automatisch für Patch Updates
- **Security Updates**: Manuelle Review erforderlich

## Einrichtung

### GitHub Repository
1. Installiere die [Renovate GitHub App](https://github.com/apps/renovate)
2. Aktiviere Renovate für dein Repository
3. Die Konfiguration wird automatisch erkannt

### Self-hosted Renovate
```bash
# Mit Docker
docker run --rm \
  -e RENOVATE_TOKEN=your_token \
  -e RENOVATE_REPOSITORIES=owner/repo \
  -v $(pwd)/renovate.json:/usr/src/app/renovate.json \
  renovate/renovate

# Mit npm
npm install -g renovate
renovate --config-file=renovate.json owner/repo
```

## Konfiguration anpassen

### Häufigere Updates
```json
{
  "schedule": ["every weekday"]
}
```

### Andere Timezone
```json
{
  "timezone": "America/New_York"
}
```

### Zusätzliche Auto-Merge Regeln
```json
{
  "packageRules": [
    {
      "matchPackageNames": ["pytest"],
      "matchUpdateTypes": ["minor"],
      "automerge": true
    }
  ]
}
```

### Dependencies ignorieren
```json
{
  "ignoreDeps": ["specific-package-name"]
}
```

## Monitoring

### Dependency Dashboard
Renovate erstellt automatisch ein "Dependency Dashboard" Issue mit:
- Übersicht aller verfügbaren Updates
- Status der PRs
- Konfigurationsfehler

### Labels und Assignees
- **Labels**: `dependencies`, `security` (bei Security Updates)
- **Assignees**: `@me` (Repository Owner)
- **Reviewers**: `@me` (Repository Owner)

## Troubleshooting

### Renovate läuft nicht
1. Prüfe die Renovate App Installation
2. Validiere die JSON-Konfiguration
3. Prüfe Repository-Berechtigungen

### Zu viele PRs
```json
{
  "prConcurrentLimit": 2,
  "prHourlyLimit": 1
}
```

### Konfiguration testen
```bash
# Dry-run mit renovate CLI
renovate --dry-run --print-config owner/repo
```

## Best Practices

1. **Regelmäßige Reviews**: Auch bei Auto-Merge sollten Updates überwacht werden
2. **Testing**: CI/CD sollte alle Updates validieren
3. **Security First**: Security Updates haben höchste Priorität
4. **Graduelle Einführung**: Starte mit konservativen Einstellungen

## Links

- [Renovate Dokumentation](https://docs.renovatebot.com/)
- [Configuration Options](https://docs.renovatebot.com/configuration-options/)
- [Python Support](https://docs.renovatebot.com/modules/manager/pep621/)
- [Pre-commit Support](https://docs.renovatebot.com/modules/manager/pre-commit/)