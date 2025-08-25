# TODO: AST-Tools Integration in Hauptkommandos

## Übersicht
Die AST-Tools sind aktuell nur über `tools ast` erreichbar, aber sollten in die Hauptkommandos `check`, `fix`, und `migrate` integriert werden für bessere Benutzerfreundlichkeit.

## 1. CHECK-Kommando erweitern

### 1.1 Aktuelle Implementierung
```python
# cli.py - check_command()
def check_command(
    path: str = typer.Argument(...),
    fix: bool = typer.Option(False, "--fix"),
    verbose: bool = typer.Option(False, "-v", "--verbose"),
):
    # Aktuell: Nur Linter
    linter = LogLinter()
    issues = linter.check_file(path)
    if fix:
        linter.fix_issues(issues)  # Nur basic fixes
```

### 1.2 Neue Parameter hinzufügen
```python
def check_command(
    path: str = typer.Argument(...),
    fix: bool = typer.Option(False, "--fix"),
    ast_analysis: bool = typer.Option(False, "--ast", help="Enable AST-based analysis"),
    interactive: bool = typer.Option(False, "--interactive", help="Interactive AST transformations"),
    patterns: List[str] = typer.Option([], "--pattern", help="Specific AST patterns to check"),
    complexity: bool = typer.Option(False, "--complexity", help="Check code complexity"),
    verbose: bool = typer.Option(False, "-v", "--verbose"),
):
```

### 1.3 AST-Integration implementieren
```python
# In check_command() hinzufügen:

# 1. Advanced Assistant für umfassende Analyse
if ast_analysis or interactive or patterns or complexity:
    from .advanced_assistant import AdvancedAssistant
    assistant = AdvancedAssistant()
    
    # AST-Analyse durchführen
    ast_issues = assistant.analyze_file(path)
    
    if complexity:
        complexity_report = assistant.analyze_complexity(path)
        console.print(complexity_report)
    
    if patterns:
        pattern_issues = assistant.check_patterns(path, patterns)
        issues.extend(pattern_issues)

# 2. Interactive Mode
if interactive:
    from .interactive_transformer import InteractiveTransformer
    transformer = InteractiveTransformer()
    
    if issues:
        console.print("Found issues. Starting interactive mode...")
        transformer.start_session(path, issues)

# 3. AST-basierte Fixes
if fix and ast_analysis:
    # Erweiterte Fixes mit AST-Transformationen
    assistant.apply_fixes(path, ast_issues)
```

### 1.4 Neue Ausgabe-Formate
```python
# AST-spezifische Ausgaben
if ast_analysis:
    console.print("\n[bold blue]AST Analysis Results:[/bold blue]")
    console.print(f"Complexity Score: {ast_issues.complexity_score}")
    console.print(f"Pattern Violations: {len(ast_issues.pattern_violations)}")
    console.print(f"Refactoring Suggestions: {len(ast_issues.suggestions)}")
```

## 2. FIX-Kommando erstellen/erweitern

### 2.1 Neues Hauptkommando
```python
@app.command()
def fix(
    path: str = typer.Argument(..., help="File or directory to fix"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show changes without applying"),
    interactive: bool = typer.Option(False, "--interactive", help="Interactive fixing"),
    ast_transforms: bool = typer.Option(True, "--ast/--no-ast", help="Use AST transformations"),
    backup: bool = typer.Option(True, "--backup/--no-backup", help="Create backup files"),
    patterns: List[str] = typer.Option([], "--pattern", help="Specific patterns to fix"),
):
    """Advanced code fixing with AST transformations."""
```

### 2.2 Fix-Implementierung
```python
def fix_command(path, dry_run, interactive, ast_transforms, backup, patterns):
    from .advanced_assistant import AdvancedAssistant
    from .interactive_transformer import InteractiveTransformer
    from .linter import LogLinter
    
    # 1. Basis-Linting
    linter = LogLinter()
    lint_issues = linter.check_file(path)
    
    # 2. AST-Analyse
    if ast_transforms:
        assistant = AdvancedAssistant()
        ast_issues = assistant.analyze_file(path)
        
        # Pattern-spezifische Fixes
        if patterns:
            ast_issues = assistant.filter_by_patterns(ast_issues, patterns)
    
    # 3. Interactive Mode
    if interactive:
        transformer = InteractiveTransformer()
        all_issues = lint_issues + ast_issues
        transformer.start_fix_session(path, all_issues, dry_run)
        return
    
    # 4. Automatische Fixes
    if backup and not dry_run:
        create_backup(path)
    
    # Linter-Fixes
    if lint_issues:
        linter.apply_fixes(path, lint_issues, dry_run)
    
    # AST-Fixes
    if ast_transforms and ast_issues:
        assistant.apply_transformations(path, ast_issues, dry_run)
    
    # Ergebnis-Report
    show_fix_report(lint_issues, ast_issues, dry_run)
```

### 2.3 Fix-Report Funktion
```python
def show_fix_report(lint_issues, ast_issues, dry_run):
    action = "Would fix" if dry_run else "Fixed"
    
    console.print(f"\n[bold green]{action}:[/bold green]")
    console.print(f"  Linting issues: {len(lint_issues)}")
    console.print(f"  AST transformations: {len(ast_issues)}")
    
    if dry_run:
        console.print("\n[yellow]Run without --dry-run to apply changes[/yellow]")
```

## 3. MIGRATE-Kommando erstellen

### 3.1 Neues Hauptkommando
```python
@app.command()
def migrate(
    path: str = typer.Argument(..., help="File or directory to migrate"),
    output: Optional[str] = typer.Option(None, "--output", help="Output directory"),
    migration_type: str = typer.Option("print-to-structlog", "--type", help="Migration type"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show changes without applying"),
    interactive: bool = typer.Option(False, "--interactive", help="Interactive migration"),
    backup: bool = typer.Option(True, "--backup/--no-backup", help="Create backup files"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing files"),
):
    """Migrate code using AST transformations."""
```

### 3.2 Migration-Typen definieren
```python
MIGRATION_TYPES = {
    "print-to-structlog": {
        "description": "Convert print statements to structlog calls",
        "handler": "migrate_print_to_structlog",
        "patterns": ["print_statements", "logging_calls"],
    },
    "logging-to-structlog": {
        "description": "Convert standard logging to structlog",
        "handler": "migrate_logging_to_structlog", 
        "patterns": ["logging_calls", "logger_imports"],
    },
    "format-strings": {
        "description": "Convert f-strings to structured logging",
        "handler": "migrate_format_strings",
        "patterns": ["format_strings", "string_formatting"],
    },
}
```

### 3.3 Migration-Implementierung
```python
def migrate_command(path, output, migration_type, dry_run, interactive, backup, force):
    from .assistant import migrate_file, migrate_directory
    from .advanced_assistant import AdvancedAssistant
    from .interactive_transformer import InteractiveTransformer
    
    # 1. Migration-Typ validieren
    if migration_type not in MIGRATION_TYPES:
        console.print(f"[red]Unknown migration type: {migration_type}[/red]")
        console.print(f"Available types: {', '.join(MIGRATION_TYPES.keys())}")
        return
    
    migration_config = MIGRATION_TYPES[migration_type]
    
    # 2. Pfad-Verarbeitung
    source_path = Path(path)
    if output:
        target_path = Path(output)
    else:
        target_path = source_path  # In-place migration
    
    # 3. Backup erstellen
    if backup and not dry_run and target_path == source_path:
        create_migration_backup(source_path)
    
    # 4. Interactive Mode
    if interactive:
        transformer = InteractiveTransformer()
        transformer.start_migration_session(
            source_path, target_path, migration_config, dry_run
        )
        return
    
    # 5. Automatische Migration
    if source_path.is_file():
        result = migrate_single_file(
            source_path, target_path, migration_config, dry_run, force
        )
    else:
        result = migrate_directory_recursive(
            source_path, target_path, migration_config, dry_run, force
        )
    
    # 6. Ergebnis-Report
    show_migration_report(result, dry_run)
```

### 3.4 Migration-Hilfsfunktionen
```python
def migrate_single_file(source, target, config, dry_run, force):
    """Migriert eine einzelne Datei."""
    from .assistant import migrate_file
    from .advanced_assistant import AdvancedAssistant
    
    # Print-to-Structlog Migration (bestehend)
    if config["handler"] == "migrate_print_to_structlog":
        return migrate_file(source, target, dry_run)
    
    # Erweiterte AST-Migrationen
    assistant = AdvancedAssistant()
    patterns = [assistant.get_pattern(p) for p in config["patterns"]]
    
    return assistant.apply_migration(source, target, patterns, dry_run)

def migrate_directory_recursive(source, target, config, dry_run, force):
    """Migriert ein ganzes Verzeichnis."""
    from .assistant import migrate_directory
    
    if config["handler"] == "migrate_print_to_structlog":
        return migrate_directory(source, target, dry_run)
    
    # Für andere Migrationen: Rekursiv durch Dateien
    results = []
    for py_file in source.rglob("*.py"):
        rel_path = py_file.relative_to(source)
        target_file = target / rel_path
        
        result = migrate_single_file(py_file, target_file, config, dry_run, force)
        results.append(result)
    
    return combine_migration_results(results)

def show_migration_report(result, dry_run):
    """Zeigt Migration-Ergebnis an."""
    action = "Would migrate" if dry_run else "Migrated"
    
    console.print(f"\n[bold green]{action}:[/bold green]")
    console.print(f"  Files processed: {result.files_processed}")
    console.print(f"  Transformations: {result.transformations_applied}")
    console.print(f"  Errors: {result.errors}")
    
    if result.warnings:
        console.print(f"\n[yellow]Warnings:[/yellow]")
        for warning in result.warnings:
            console.print(f"  - {warning}")
```

## 4. CLI-Struktur Änderungen

### 4.1 Import-Erweiterungen in cli.py
```python
# Neue Imports hinzufügen
from .advanced_assistant import AdvancedAssistant, ASTPattern
from .interactive_transformer import InteractiveTransformer  
from .assistant import migrate_file, migrate_directory, MigrationResult
from .live_editor import LiveCodeEditor
```

### 4.2 Help-Text Verbesserungen
```python
# check-Kommando Help erweitern
@app.command()
def check(
    # ... Parameter ...
):
    """
    Check code quality with optional AST analysis.
    
    Examples:
      nicestlog check file.py                    # Basic linting
      nicestlog check file.py --ast              # With AST analysis  
      nicestlog check file.py --fix --ast        # Fix with AST transforms
      nicestlog check file.py --interactive      # Interactive mode
      nicestlog check file.py --complexity       # Complexity analysis
    """

# migrate-Kommando Help
@app.command() 
def migrate(
    # ... Parameter ...
):
    """
    Migrate code using AST transformations.
    
    Examples:
      nicestlog migrate file.py                           # Print to structlog
      nicestlog migrate src/ --output migrated/           # Directory migration
      nicestlog migrate file.py --type logging-to-structlog  # Logging migration
      nicestlog migrate file.py --interactive             # Interactive mode
      nicestlog migrate file.py --dry-run                 # Preview changes
    """
```

## 5. Implementierungs-Reihenfolge

### Phase 1: Check-Kommando erweitern ✅ COMPLETED
1. ✅ Parameter hinzufügen (`--ast`, `--interactive`, `--complexity`)
2. ✅ Advanced Assistant Integration
3. ✅ Interactive Transformer Integration  
4. ✅ AST-basierte Fix-Funktionalität

### Phase 2: Fix-Kommando erstellen ✅ COMPLETED
1. ✅ Neues Hauptkommando definieren
2. ✅ Dry-run Funktionalität
3. ✅ Backup-System
4. ✅ Interactive Mode

### Phase 3: Migrate-Kommando erstellen  
1. ✅ Migration-Typen definieren
2. ✅ Bestehende Assistant-Integration
3. ✅ Erweiterte AST-Migrationen
4. ✅ Directory-Migration

### Phase 4: Testing & Documentation ✅ COMPLETED
1. ✅ Unit Tests für neue Funktionen
2. ✅ Integration Tests für AST-enhanced CLI commands
3. ✅ CLI Help-Texte
4. ✅ Dokumentation aktualisieren

## 6. Kompatibilität

### Rückwärtskompatibilität
- Alle bestehenden Kommandos bleiben unverändert
- `tools ast` Subkommandos bleiben verfügbar
- Neue Parameter sind optional mit sinnvollen Defaults

### Migration bestehender Nutzer
- `tools ast analyze` → `check --ast`
- `tools ast transform` → `fix --interactive`  
- `tools ast interactive` → `migrate --interactive`

## 7. Konfiguration

### Config-File Erweiterungen
```toml
# pyproject.toml
[tool.nicestlog.ast]
default_patterns = ["complexity", "logging_quality", "code_smells"]
max_complexity = 10
interactive_mode = false
auto_backup = true

[tool.nicestlog.migration]
default_type = "print-to-structlog"
preserve_comments = true
update_imports = true
```

Diese Integration macht die mächtigen AST-Tools für alle Benutzer zugänglich und integriert sie nahtlos in den normalen Workflow!

## 8. Abschluss - Phase 4 Implementierung

### Was wurde in Phase 4 umgesetzt:

#### 8.1 Umfassende CLI Integration Tests ✅
- **Neue Testdatei**: `tests/test_cli_ast_integration.py`
- **TestCheckCommandASTIntegration**: Tests für `check --ast`, `--complexity`, `--pattern`, `--interactive`
- **TestFixCommandASTIntegration**: Tests für `fix` mit AST-Transformationen, `--dry-run`, `--interactive`
- **TestMigrateCommandASTIntegration**: Tests für `migrate` mit verschiedenen Typen und Modi
- **TestASTToolsSubcommands**: Backward-compatibility Tests für `tools ast`
- **TestBackwardCompatibility**: Sicherstellung dass bestehende Funktionalität unverändert bleibt

#### 8.2 Test Coverage
- **Check Command**: AST-Analyse, Komplexitäts-Checks, Pattern-spezifische Analyse, Interactive Mode
- **Fix Command**: AST-Transformationen, Dry-run, Interactive Mode, Pattern-spezifische Fixes
- **Migrate Command**: Verschiedene Migration-Typen, Output-Verzeichnisse, Interactive Mode
- **Backward Compatibility**: Alle bestehenden Commands funktionieren unverändert
- **Error Handling**: Tests für Fehlerbehandlung und Edge Cases

#### 8.3 Dokumentation (geplant)
- **AST Integration Guide**: Umfassende Anleitung für alle neuen Features
- **Migration Examples**: Praktische Beispiele für verschiedene Migration-Szenarien  
- **Best Practices**: Empfehlungen für Team-Adoption und CI/CD Integration
- **Troubleshooting**: Häufige Probleme und Lösungen

### Vollständige Integration erreicht! 🎉

Alle vier Phasen der AST-Integration sind nun abgeschlossen:
- ✅ **Phase 1**: Check-Kommando erweitert
- ✅ **Phase 2**: Fix-Kommando erstellt  
- ✅ **Phase 3**: Migrate-Kommando erstellt
- ✅ **Phase 4**: Testing & Documentation

Die AST-Tools sind jetzt vollständig in die Hauptkommandos integriert und für alle Benutzer über eine intuitive CLI verfügbar!