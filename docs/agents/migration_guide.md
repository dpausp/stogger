# 🤖 AI Agent Migration Guide for nicestlog

## Overview

This guide helps AI agents analyze existing Python projects and systematically retrofit them with nicestlog for superior structured logging. The goal is to provide clear decision trees and automated workflows for seamless adoption.

## 🎯 Agent Use Case

**Scenario**: Agent encounters an existing Python project that needs better logging
**Goal**: Retrofit the project with nicestlog using minimal manual intervention
**Outcome**: Project has structured, translatable, and maintainable logging

## 📋 Phase 1: Project Analysis

### Step 1: Initial Project Scan

```bash
# Scan project structure and identify logging patterns
nicestlog migrate . --json > project_analysis.json

# Check existing logging coverage
nicestlog check . --ast --complexity --verbose
```

**Agent Decision Points:**
- Does project use `print()` statements for output? → **High Priority Migration**
- Does project use standard `logging` module? → **Medium Priority Migration** 
- Does project have existing structured logging? → **Enhancement Migration**
- Does project have no logging? → **Greenfield Implementation**

### Step 2: Dependency Analysis

Check `pyproject.toml`, `requirements.txt`, or `setup.py` for:
- Existing logging dependencies (logging, loguru, etc.)
- Structlog already present
- Conflicting logging frameworks

### Step 3: Codebase Complexity Assessment

```bash
# Get detailed metrics
nicestlog migrate . --json | jq '.[] | {file: .file_path, complexity: .complexity_score, issues: (.issues | length)}'
```

**Complexity Thresholds:**
- **Simple** (< 5 files, < 500 LOC): Direct migration
- **Medium** (5-20 files, 500-2000 LOC): Phased migration
- **Complex** (> 20 files, > 2000 LOC): Strategic migration with testing

## 🔄 Phase 2: Migration Strategy Selection

### Strategy A: Print-to-Structlog (Most Common)

**When to use:** Project uses `print()` statements for logging/debugging

```bash
# Preview changes
nicestlog migrate . --type print-to-structlog --dry-run

# Apply with backup
nicestlog migrate . --type print-to-structlog --backup
```

**Agent checklist:**
- [ ] Backup created
- [ ] All print statements identified
- [ ] Context-appropriate log levels assigned
- [ ] Structured data extracted from print arguments

### Strategy B: Logging-to-Structlog

**When to use:** Project uses standard Python logging

```bash
# Analyze logging patterns first
grep -r "logging\." . --include="*.py" | head -20

# Apply migration
nicestlog migrate . --type logging-to-structlog --interactive
```

### Strategy C: Enhancement Migration

**When to use:** Project has some structured logging but needs improvement

```bash
# Focus on specific improvements
nicestlog fix . --ast --pattern logging --verbose
```

## 🛠️ Phase 3: Implementation Workflow

### Step 1: Environment Setup

```bash
# Add nicestlog to project dependencies
echo 'nicestlog = "^1.0.0"' >> pyproject.toml

# Or for requirements.txt projects
echo 'nicestlog>=1.0.0' >> requirements.txt
```

### Step 2: Configuration Integration

Create or update `pyproject.toml`:

```toml
[tool.nicestlog]
verbose = true
syslog_identifier = "your-project-name"
translation_dir = "translations"
language = "en"
log_format = "console"
async_logging = true
```

### Step 3: Initialize Translations

```bash
# Create translation directory
mkdir -p translations

# Generate initial English translations
nicestlog tools i18n check . --translation-dir translations -l en --list-missing > missing_keys.txt

# Create basic translation file
cat > translations/en.toml << 'EOF'
# Auto-generated translations for your project
application-started = "🚀 Application {name} started successfully"
user-login = "User {username} logged in from {ip}"
error-occurred = "❌ Error: {error}"
EOF
```

## 🧪 Phase 4: Testing and Validation

### Step 1: Verify Migration

```bash
# Check translation completeness
nicestlog tools i18n check . --translation-dir translations -l en --strict

# Lint the migrated code
nicestlog check . --ast --verbose

# Run project tests to ensure functionality
python -m pytest  # or your test command
```

### Step 2: Quality Assurance

```bash
# Review log quality
nicestlog review . --format text --min-score 80

# Check for any remaining issues
nicestlog check . --ast --verbose
```

## 📊 Phase 5: Monitoring and Optimization

### Performance Check

```bash
# Test logging performance
python -c "
import nicestlog
import structlog
import time

nicestlog.init_logging(verbose=True)
log = structlog.get_logger()

start = time.time()
for i in range(1000):
    log.info('performance-test', iteration=i, data={'key': 'value'})
end = time.time()

print(f'1000 log entries in {end-start:.3f}s')
"
```

### Integration Verification

- [ ] Console output is readable and structured
- [ ] File logging works (if configured)
- [ ] Systemd journal integration (if applicable)
- [ ] Translation system functional
- [ ] No performance degradation

## 🚨 Common Pitfalls and Solutions

### Issue: Import Conflicts

**Problem:** Existing `import logging` conflicts with nicestlog
**Solution:** Use aliased imports or gradual migration

```python
# Before
import logging
log = logging.getLogger(__name__)

# After
import structlog
log = structlog.get_logger(__name__)
```

### Issue: Performance Concerns

**Problem:** Logging overhead in tight loops
**Solution:** Use async logging and conditional debug logging

```python
# Enable async logging
nicestlog.init_logging(async_logging=True)

# Conditional debug logging
if log.isEnabledFor(logging.DEBUG):
    log.debug("expensive-operation", data=expensive_computation())
```

### Issue: Translation Maintenance

**Problem:** Missing translations for new log messages
**Solution:** CI integration for translation checks

```yaml
# .github/workflows/i18n-check.yml
- name: Check translations
  run: |
    uv run nicestlog tools i18n check . --translation-dir translations -l en --strict --fail-on-extra
```

## 🎯 Success Metrics

After migration, the project should have:

- [ ] **Zero print statements** for logging purposes
- [ ] **100% translation coverage** for user-facing log messages
- [ ] **Structured log data** with consistent field naming
- [ ] **Appropriate log levels** (debug, info, warning, error)
- [ ] **Context preservation** through bound loggers
- [ ] **Performance maintained** or improved
- [ ] **CI integration** for log quality checks

## 🔗 Next Steps

1. **Advanced Features**: Explore systemd integration, web dashboard
2. **Monitoring**: Set up log aggregation and analysis
3. **Team Training**: Document project-specific logging conventions
4. **Continuous Improvement**: Regular log quality reviews

## 📚 Additional Resources

- [nicestlog Best Practices](../user_guide/best_practices.md)
- [Advanced AST Assistant](../features/advanced_assistant.md)
- [Translation System Guide](../user_guide/advanced_features.md)
- [Performance Optimization](../user_guide/quick_practices.md)