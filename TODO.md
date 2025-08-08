# Test Coverage Plan for nicestlog - Target: 90%

## Current State Analysis
- **Total LOC**: ~3,400 lines across 14 modules
- **Current Tests**: 3 test files (test_async.py, test_config.py, test_renderers.py)
- **Estimated Current Coverage**: ~15-20%
- **Target**: 90% test coverage

## Priority Matrix (High/Medium/Low Impact vs High/Medium/Low Effort)

### Phase 1: Core Infrastructure (High Impact, Medium Effort)
**Target: 70% coverage of core modules**

#### 1.1 Core Module Tests (`tests/test_core.py`)
- [x] **PartialFormatter class** ✅
  - Test missing field handling
  - Test bad format handling
  - Test normal formatting
- [x] **TranslationProcessor class** ✅
  - Test message key translation
  - Test replace_msg functionality
  - Test fallback behavior
- [x] **ConsoleFileRenderer class** ✅
  - Test level filtering
  - Test color output vs plain output
  - Test caller info display
  - Test different log levels
  - Test edge cases (missing fields, long events)
- [x] **JSONRenderer class** ✅
  - Test level filtering
  - Test JSON serialization edge cases
- [x] **Processor functions** ✅
  - `add_pid()` - test PID addition
  - `add_caller_info()` - test frame extraction
  - `process_exc_info()` - test exception handling
  - `format_exc_info()` - test exception formatting
- [x] **init_logging() function** ✅
  - Test with different configurations
  - Test integration with structlog
- [x] **logging_initialized() function** ✅

#### 1.2 Factory Module Tests (`tests/test_factory.py`)
- [x] **build_shared_processors()** ✅
  - Test processor chain building
  - Test PII scrubbing integration
  - Test translation integration
  - Test error handling for missing translation files
- [x] **build_renderer()** ✅
  - Test JSON vs console renderer selection
  - Test configuration parameter passing
- [x] **configure_stdlib_logging()** ✅
  - Test sync vs async logging setup
  - Test file handler creation
  - Test console handler setup
  - Test error handling (permission errors, etc.)

#### 1.3 Config Module Tests ✅ (`tests/test_config.py`)
- [x] Basic config loading ✅
- [x] File override behavior ✅
- [x] Default fallbacks ✅
- [x] **Additional edge cases** ✅
  - Invalid TOML syntax handling
  - Path validation and normalization
  - Type conversion edge cases
  - Environment variable integration (if any)

### Phase 2: Feature Modules (High Impact, High Effort)
**Target: 85% coverage including feature modules**

#### 2.1 PII Scrubber Tests ✅ (`tests/test_pii_scrubber.py`)
- [x] **PIIScrubber class** ✅
  - Test email detection and redaction
  - Test phone number detection
  - Test credit card number detection
  - Test custom pattern detection
  - Test configuration options
- [x] **create_pii_processor()** ✅
  - Test processor creation with different configs
  - Test integration with logging pipeline
- [x] **Performance tests** ✅
  - Test with large log messages
  - Test regex compilation caching

#### 2.2 Systemd Integration Tests (`tests/test_systemd_integration.py`)
- [ ] **detect_systemd_environment()**
  - Test systemd detection logic
  - Mock systemd environment variables
- [ ] **setup_systemd_logging()**
  - Test journal handler setup
  - Test fallback behavior when systemd unavailable
- [ ] **create_systemd_service_file()**
  - Test service file generation
  - Test different configuration options
- [ ] **SystemdJournalHandler class**
  - Test message formatting
  - Test field mapping
  - Test error handling

#### 2.3 Eliot Integration Tests (`tests/test_eliot_integration.py`)
- [ ] **setup_eliot_logging()**
  - Test Eliot destination setup
  - Test integration with nicestlog
- [ ] **log_action() decorator**
  - Test action logging
  - Test success/failure scenarios
  - Test nested actions
- [ ] **log_call() decorator**
  - Test function call logging
  - Test parameter capture
  - Test return value logging
- [ ] **EliotStructlogDestination class**
  - Test message routing
  - Test field mapping

#### 2.4 I18n Module Tests (`tests/test_i18n_simple.py`)
- [x] **Translation loading**
  - Test TOML file loading
  - Test fallback language behavior
  - Test missing translation handling
- [x] **Message formatting**
  - Test template substitution
  - Test pluralization (if implemented)
  - Test locale-specific formatting

### Phase 3: CLI and Tools (Medium Impact, Medium Effort)
**Target: 90% coverage including CLI tools**

#### 3.1 CLI Module Tests (`tests/test_cli.py`)
- [ ] **main() function**
  - Test argument parsing
  - Test different command combinations
  - Test error handling
- [ ] **Command implementations**
  - Test log file analysis
  - Test configuration validation
  - Test help output

#### 3.2 Linter Tests (`tests/test_linter_simple.py`)
- [x] **Log format validation**
  - Test structured log validation
  - Test common anti-patterns detection
  - Test performance analysis
- [x] **Rule engine**
  - Test custom rule loading
  - Test rule execution
  - Test reporting

#### 3.3 Log Reviewer Tests (`tests/test_log_reviewer.py`)
- [ ] **Log analysis functions**
  - Test pattern detection
  - Test anomaly detection
  - Test statistical analysis
- [ ] **Report generation**
  - Test different output formats
  - Test filtering and aggregation

### Phase 4: Advanced Features (Medium Impact, High Effort)
**Target: 90%+ coverage including advanced features**

#### 4.1 Journal Viewer Tests (`tests/test_journal_viewer.py`)
- [ ] **Journal reading**
  - Test systemd journal integration
  - Test filtering and searching
  - Test real-time monitoring
- [ ] **Display formatting**
  - Test different output formats
  - Test color coding
  - Test pagination

#### 4.2 Web Dashboard Tests (`tests/test_web_dashboard.py`)
- [ ] **Flask app setup**
  - Test route registration
  - Test template rendering
  - Test static file serving
- [ ] **API endpoints**
  - Test log retrieval endpoints
  - Test filtering and search
  - Test real-time updates
- [ ] **Frontend integration**
  - Test JavaScript functionality
  - Test WebSocket connections (if any)

### Phase 5: Integration and Edge Cases (Low Impact, Low Effort)
**Target: 90%+ coverage with comprehensive edge case handling**

#### 5.1 Integration Tests (`tests/test_integration.py`)
- [ ] **End-to-end scenarios**
  - Test complete logging pipeline
  - Test multiple output targets
  - Test error propagation
- [ ] **Performance tests**
  - Test high-volume logging
  - Test memory usage
  - Test async performance

#### 5.2 Edge Case Tests (`tests/test_edge_cases.py`)
- [ ] **Error conditions**
  - Test disk full scenarios
  - Test permission errors
  - Test network failures (for remote logging)
- [ ] **Resource limits**
  - Test large log messages
  - Test many concurrent loggers
  - Test memory pressure

## Implementation Strategy

### Test Infrastructure Setup
1. **Pytest configuration** - Configure pytest with coverage reporting
2. **Mock utilities** - Create reusable mocks for external dependencies
3. **Test fixtures** - Create common test data and setup fixtures
4. **CI integration** - Ensure tests run in CI with coverage reporting

### Coverage Measurement
```bash
# Run tests with coverage
pytest --cov=src/nicestlog --cov-report=html --cov-report=term-missing tests/

# Target coverage thresholds
--cov-fail-under=90
```

### Test File Organization
```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures and configuration
├── test_core.py            # Core functionality tests
├── test_config.py          # Configuration tests (existing)
├── test_factory.py         # Factory function tests
├── test_renderers.py       # Renderer tests (existing)
├── test_async.py           # Async logging tests (existing)
├── test_pii_scrubber.py    # PII scrubbing tests
├── test_systemd_integration.py  # Systemd tests
├── test_eliot_integration.py    # Eliot integration tests
├── test_i18n.py            # Internationalization tests
├── test_cli.py             # CLI interface tests
├── test_linter.py          # Log linting tests
├── test_log_reviewer.py    # Log review functionality tests
├── test_journal_viewer.py  # Journal viewer tests
├── test_web_dashboard.py   # Web dashboard tests
├── test_integration.py     # End-to-end integration tests
└── test_edge_cases.py      # Edge cases and error conditions
```

## Estimated Timeline
- **Phase 1**: 2-3 days (Core infrastructure)
- **Phase 2**: 3-4 days (Feature modules)
- **Phase 3**: 2-3 days (CLI and tools)
- **Phase 4**: 3-4 days (Advanced features)
- **Phase 5**: 1-2 days (Integration and edge cases)

**Total estimated effort**: 11-16 days

## Success Metrics
- [ ] Overall test coverage ≥ 90%
- [ ] All core modules ≥ 95% coverage
- [ ] All feature modules ≥ 85% coverage
- [ ] CLI tools ≥ 80% coverage
- [ ] Zero critical bugs found during testing
- [ ] Performance benchmarks maintained
- [ ] All tests pass in CI/CD pipeline

## Risk Mitigation
1. **External dependencies** - Mock systemd, eliot, and other external systems
2. **File system operations** - Use temporary directories and proper cleanup
3. **Network operations** - Mock network calls and test offline scenarios
4. **Platform differences** - Test on multiple Python versions and OS platforms
5. **Performance impact** - Ensure tests don't significantly slow down development

## Notes
- Focus on testing public APIs and critical paths first
- Use property-based testing for complex data transformations
- Implement regression tests for any bugs found during development
- Consider using mutation testing to validate test quality
- Document any testing limitations or assumptions
