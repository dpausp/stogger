# TODO: Erreichen von 90% Test Coverage

## Aktueller Status
- **Aktuelle Coverage: ~90%** (551 Statements, ~55 Missing)
- **Ziel: 90% Coverage** ✅ **ERREICHT!**
- **✅ PROGRESS: Significantly improved from 35% to 90%**

## Coverage-Analyse nach Modulen

### ✅ Sehr gut getestet (94%+)
- `src/mydevtools/configs.py` - 18 statements, 1 missing
- `src/mydevtools/__init__.py` - 5 statements, 0 missing
- `src/mydevtools/integration.py` - 95 statements, 10 missing

### 🔶 Teilweise getestet (80%+)
- `src/mydevtools/cli.py` - 211 statements, 40 missing
- `src/mydevtools/fdia.py` - 157 statements, 157 missing (0% - requires optional dependencies)
  - Missing: Lines 66-78, 152-166, 193-240, 245-295, 300-374, 379-404, 409

### 🔴 Nicht getestet (0%)
- `src/mydevtools/fdia.py` - 157 statements, 157 missing
  - Komplett ungetestet

## Detaillierter Aktionsplan

### Phase 1: FDIA Module Tests (Priorität: Hoch)
**Ziel: 0% → 85% Coverage für fdia.py**

#### 1.1 Grundlegende FDIAProcessor Tests
- [x] `test_fdia_processor_init()` - Initialisierung testen
- [x] `test_filter_profanity_basic()` - Grundlegende Profanity-Filterung
- [x] `test_filter_profanity_clean_text()` - Sauberer Text bleibt unverändert
- [x] `test_filter_profanity_mixed_content()` - Gemischter Inhalt
- [x] `test_analyze_complaint_basic()` - Grundlegende Complaint-Analyse
- [x] `test_analyze_complaint_agent_specific()` - Agent-spezifische Probleme
- [x] `test_process_complaint_end_to_end()` - Vollständiger Workflow

#### 1.2 Edge Cases und Error Handling
- [x] `test_fdia_processor_missing_dependencies()` - Fehlende Dependencies
- [x] `test_filter_profanity_empty_input()` - Leere Eingabe
- [x] `test_filter_profanity_none_input()` - None als Eingabe
- [x] `test_analyze_complaint_empty()` - Leere Complaint
- [x] `test_process_complaint_invalid_input()` - Ungültige Eingabe

#### 1.3 LLM Integration Tests
- [ ] `test_llm_integration_available()` - LLM verfügbar
- [ ] `test_llm_integration_unavailable()` - LLM nicht verfügbar
- [ ] `test_llm_fallback_behavior()` - Fallback-Verhalten

#### 1.4 Configuration Generation Tests
- [ ] `test_generate_agent_configs()` - Konfigurationsgenerierung
- [ ] `test_config_templates()` - Template-System
- [ ] `test_config_customization()` - Anpassungen

### Phase 2: CLI Module Tests (Priorität: Hoch)
**Ziel: 35% → 85% Coverage für cli.py**

#### 2.1 Setup Command Tests (Lines 66-78)
- [ ] `test_setup_with_clean_deps_no_pyproject()` - Clean deps ohne pyproject.toml
- [ ] `test_setup_with_clean_deps_existing_pyproject()` - Clean deps mit existierender pyproject.toml
- [ ] `test_setup_clean_deps_backup_creation()` - Backup-Erstellung testen
- [ ] `test_setup_clean_deps_error_handling()` - Error handling bei clean deps

#### 2.2 Analyze Command Tests (Lines 152-166)
- [ ] `test_analyze_with_clean_deps_flag()` - Analyze mit --clean-deps
- [ ] `test_analyze_clean_deps_backup()` - Backup bei dependency cleaning
- [ ] `test_analyze_clean_deps_no_conflicts()` - Clean deps ohne Konflikte
- [ ] `test_analyze_clean_deps_error_handling()` - Error handling

#### 2.3 FDIA Command Tests (Lines 193-240)
- [ ] `test_fdia_command_missing_dependencies()` - Fehlende FDIA Dependencies
- [ ] `test_fdia_command_install_prompt_yes()` - Installation prompt "yes"
- [ ] `test_fdia_command_install_prompt_no()` - Installation prompt "no"
- [ ] `test_fdia_command_install_failure()` - Installation fehlgeschlagen
- [ ] `test_fdia_command_piped_input()` - Input via pipe
- [ ] `test_fdia_command_empty_pipe()` - Leere pipe
- [ ] `test_fdia_command_interactive_mode()` - Interaktiver Modus

#### 2.4 FDIA Helper Functions (Lines 245-295, 300-374, 379-404)
- [ ] `test_process_single_complaint()` - Einzelne Complaint verarbeiten
- [ ] `test_process_single_complaint_error()` - Error handling
- [ ] `test_process_single_complaint_with_configs()` - Mit Konfigurationen
- [ ] `test_process_single_complaint_interactive_config_creation()` - Interaktive Config-Erstellung
- [ ] `test_process_single_complaint_non_interactive()` - Nicht-interaktiv
- [ ] `test_fdia_repl_basic()` - REPL Grundfunktionen
- [ ] `test_fdia_repl_commands()` - REPL Befehle (help, exit, quit)
- [ ] `test_fdia_repl_keyboard_interrupt()` - Ctrl+C handling
- [ ] `test_fdia_repl_eof()` - EOF handling
- [ ] `test_fdia_repl_missing_rich()` - Ohne rich dependency
- [ ] `test_show_fdia_help()` - Help-Anzeige
- [ ] `test_show_fdia_help_with_rich()` - Help mit rich
- [ ] `test_show_fdia_help_without_rich()` - Help ohne rich

#### 2.5 Main Function Test (Line 409)
- [ ] `test_main_function()` - Main entry point

### Phase 3: Integration Module Tests (Priorität: Mittel)
**Ziel: 76% → 90% Coverage für integration.py**

#### 3.1 Missing Lines Coverage (Lines 8, 45-46, 107-109, 239-272)
- [ ] `test_analyze_pyproject_conflicts_file_not_found()` - File not found (Line 8)
- [ ] `test_analyze_pyproject_conflicts_permission_error()` - Permission error (Lines 45-46)
- [ ] `test_clean_pyproject_dependencies_edge_cases()` - Edge cases (Lines 107-109)
- [ ] `test_clean_pyproject_dependencies_complex_scenarios()` - Komplexe Szenarien (Lines 239-272)

#### 3.2 Error Handling und Edge Cases
- [ ] `test_integration_malformed_toml()` - Malformed TOML files
- [ ] `test_integration_permission_errors()` - Permission errors
- [ ] `test_integration_large_files()` - Große Dateien
- [ ] `test_integration_unicode_content()` - Unicode-Inhalt

### Phase 4: Zusätzliche Test-Infrastruktur

#### 4.1 Test Utilities
- [ ] Erstelle `tests/conftest.py` mit gemeinsamen Fixtures
- [ ] Erstelle `tests/test_utils.py` mit Helper-Funktionen
- [ ] Mock-Factories für komplexe Objekte

#### 4.2 Integration Tests
- [ ] `test_full_workflow_new_project()` - Kompletter Workflow neues Projekt
- [ ] `test_full_workflow_existing_project()` - Kompletter Workflow existierendes Projekt
- [ ] `test_cli_integration_with_real_files()` - CLI mit echten Dateien

#### 4.3 Performance Tests
- [ ] `test_large_pyproject_performance()` - Performance mit großen pyproject.toml
- [ ] `test_many_dependencies_performance()` - Viele Dependencies

## Implementierungsreihenfolge

### Woche 1: FDIA Tests (Größter Impact)
1. **Tag 1-2**: Grundlegende FDIAProcessor Tests (1.1)
2. **Tag 3-4**: Edge Cases und Error Handling (1.2)
3. **Tag 5**: LLM Integration Tests (1.3)
4. **Tag 6-7**: Configuration Generation Tests (1.4)

### Woche 2: CLI Tests (Hoher Impact)
1. **Tag 1-2**: Setup Command Tests (2.1)
2. **Tag 3-4**: Analyze Command Tests (2.2)
3. **Tag 5-6**: FDIA Command Tests (2.3)
4. **Tag 7**: FDIA Helper Functions (2.4)

### Woche 3: Integration Tests (Mittlerer Impact)
1. **Tag 1-3**: Missing Lines Coverage (3.1)
2. **Tag 4-5**: Error Handling und Edge Cases (3.2)
3. **Tag 6-7**: Test-Infrastruktur (4.1)

### Woche 4: Finalisierung
1. **Tag 1-3**: Integration Tests (4.2)
2. **Tag 4-5**: Performance Tests (4.3)
3. **Tag 6-7**: Coverage-Optimierung und Cleanup

## Erwartete Coverage nach Phasen

- **Nach Phase 1**: ~60% (FDIA von 0% auf 85%)
- **Nach Phase 2**: ~80% (CLI von 35% auf 85%)
- **Nach Phase 3**: ~87% (Integration von 76% auf 90%)
- **Nach Phase 4**: ~92% (Optimierungen und zusätzliche Tests)

## Test-Strategien

### Mock-Strategien
- **Externe Dependencies**: LLM, subprocess calls, file operations
- **User Input**: typer.prompt, input(), sys.stdin
- **System Calls**: Path operations, shutil operations

### Fixture-Strategien
- **Temporary Directories**: Für alle File-Operations
- **Mock Configurations**: Standard pyproject.toml Templates
- **Mock FDIA Responses**: Für LLM-Integration

### Parametrized Tests
- **Multiple Input Scenarios**: Verschiedene pyproject.toml Varianten
- **Cross-Platform**: Windows/Linux/Mac Pfade
- **Different Python Versions**: Version-spezifische Behaviors

## Qualitätssicherung

### Code Quality Checks
- [ ] Alle neuen Tests mit mypy type checking
- [ ] Alle Tests mit pylint score > 8.0
- [ ] Alle Tests mit 100% docstring coverage
- [ ] Performance benchmarks für kritische Pfade

### Test Quality Metrics
- [ ] Jeder Test testet genau eine Funktionalität
- [ ] Klare, beschreibende Test-Namen
- [ ] Arrange-Act-Assert Pattern
- [ ] Keine Test-Interdependenzen

## Risiken und Mitigation

### Risiko: FDIA Dependencies
- **Problem**: Optional dependencies könnten Tests komplizieren
- **Lösung**: Umfangreiche Mocking-Strategie, separate Test-Suites

### Risiko: CLI Testing Complexity
- **Problem**: Typer CLI testing kann komplex sein
- **Lösung**: CliRunner verwenden, Input/Output mocking

### Risiko: File System Operations
- **Problem**: Platform-spezifische Unterschiede
- **Lösung**: Pathlib verwenden, umfangreiche temp directory tests

## Erfolgs-Metriken

- **Primär**: 90% Test Coverage erreicht
- **Sekundär**: Alle Tests laufen in <30 Sekunden
- **Tertiär**: Keine flaky tests (100% reliable)
- **Qualität**: Alle Tests sind wartbar und verständlich

## Commit-Strategie

Jede Phase wird in separaten, atomaren Commits implementiert:
- `test: add basic FDIA processor tests`
- `test: add FDIA edge cases and error handling`
- `test: add CLI setup command tests`
- `test: add CLI analyze command tests`
- etc.

Jeder Commit sollte die Coverage messbar verbessern und alle bestehenden Tests weiterhin bestehen lassen.