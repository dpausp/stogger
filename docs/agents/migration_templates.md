# 🛠️ Migration Templates for AI Agents

This document provides ready-to-use templates for common nicestlog migration scenarios.

## Template 1: Simple Print-to-Structlog Migration

### Use Case
Small to medium projects using `print()` statements for logging/debugging.

### Agent Workflow
```bash
# 1. Analyze project
nicestlog migrate . --json > analysis.json

# 2. Check if strategy is print-to-structlog
STRATEGY=$(cat analysis.json | jq -r '.recommendation.strategy')
if [ "$STRATEGY" = "print-to-structlog" ]; then
    echo "✅ Print-to-structlog migration recommended"
else
    echo "❌ Different strategy needed: $STRATEGY"
    exit 1
fi

# 3. Add dependency
echo 'nicestlog = "^1.0.0"' >> pyproject.toml

# 4. Create configuration
cat > pyproject.toml.append << 'EOF'

[tool.nicestlog]
verbose = true
syslog_identifier = "your-project"
translation_dir = "translations"
language = "en"
EOF
cat pyproject.toml.append >> pyproject.toml

# 5. Create translations directory
mkdir -p translations

# 6. Perform migration with backup
nicestlog migrate . --type print-to-structlog --backup --dry-run
# Review changes, then apply:
nicestlog migrate . --type print-to-structlog --backup

# 7. Generate translation file
nicestlog tools i18n check . --translation-dir translations -l en --list-missing > missing_keys.txt
# Create basic translations based on missing keys

# 8. Validate
nicestlog check . --ast
nicestlog tools i18n check . --translation-dir translations -l en --strict
```

### Expected Transformations

**Before:**
```python
def process_data(data):
    print("Processing data:", data)
    if not data:
        print("No data provided")
        return None
    print(f"Processed {len(data)} items")
    return data
```

**After:**
```python
import structlog
log = structlog.get_logger(__name__)

def process_data(data):
    log.info("processing-data", _replace_msg="Processing data", data=data)
    if not data:
        log.warning("no-data-provided", _replace_msg="No data provided")
        return None
    log.info("processing-completed", _replace_msg="Processing completed with {items_count} items", items_count=len(data))
    return data
```

## Template 2: Logging-to-Structlog Migration

### Use Case
Projects using Python's standard logging module.

### Agent Workflow
```bash
# 1. Analyze and verify strategy
nicestlog migrate . --json | jq '.recommendation.strategy'
# Should return: "logging-to-structlog"

# 2. Interactive migration (recommended for logging)
nicestlog migrate . --type logging-to-structlog --interactive --backup

# 3. Update imports manually or with sed
find . -name "*.py" -exec sed -i 's/import logging/import structlog/g' {} \;
find . -name "*.py" -exec sed -i 's/logging.getLogger/structlog.get_logger/g' {} \;

# 4. Initialize nicestlog in main module
cat > init_logging.py << 'EOF'
import nicestlog
nicestlog.init_logging(verbose=True, syslog_identifier="your-project")
EOF

# 5. Validate and fix remaining issues
nicestlog check . --ast --fix
```

### Expected Transformations

**Before:**
```python
import logging
logger = logging.getLogger(__name__)

def authenticate_user(username, password):
    logger.info(f"Authentication attempt for user: {username}")
    if not username:
        logger.error("Username is required")
        return False
    logger.info(f"User {username} authenticated successfully")
    return True
```

**After:**
```python
import structlog
log = structlog.get_logger(__name__)

def authenticate_user(username, password):
    log.info("authentication-attempt", _replace_msg="Authentication attempt for {username}", username=username)
    if not username or not password:
        log.error("authentication-failed", _replace_msg="Authentication failed for {username}", username=username)
        return False
    log.info("authentication-successful", _replace_msg="Authentication successful for {username}", username=username)
    return True
```

## Template 3: Enhancement Migration

### Use Case
Projects already using structlog but need nicestlog improvements.

### Agent Workflow
```bash
# 1. Verify enhancement strategy
nicestlog migrate . --json | jq '.recommendation.strategy'
# Should return: "enhancement"

# 2. Add nicestlog and enhance existing logging
nicestlog check . --ast --fix --verbose

# 3. Add translation support
mkdir -p translations
nicestlog tools i18n check . --translation-dir translations -l en --list-missing > missing_keys.txt

# 4. Create comprehensive translation file
python << 'EOF'
import json
with open('missing_keys.txt', 'r') as f:
    keys = [line.strip() for line in f if line.strip()]

translations = {}
for key in keys:
    # Generate human-readable translations
    readable = key.replace('-', ' ').replace('_', ' ').title()
    translations[key] = f"📝 {readable}"

with open('translations/en.toml', 'w') as f:
    for key, value in translations.items():
        f.write(f'{key} = "{value}"\n')
EOF

# 5. Optimize performance
nicestlog review . --format json | jq '.overall_score'
```

## Template 4: Greenfield Implementation

### Use Case
New projects or projects with minimal logging.

### Agent Workflow
```bash
# 1. Set up nicestlog from scratch
cat > pyproject.toml << 'EOF'
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "your-project"
version = "0.1.0"
dependencies = [
    "nicestlog>=1.0.0",
]

[tool.nicestlog]
verbose = true
syslog_identifier = "your-project"
translation_dir = "translations"
language = "en"
log_format = "console"
async_logging = true
EOF

# 2. Create main application with logging
cat > main.py << 'EOF'
#!/usr/bin/env python3
"""Main application with nicestlog integration."""

import nicestlog
import structlog

# Initialize logging
nicestlog.init_logging()
log = structlog.get_logger(__name__)

def main():
    log.info("application-started", _replace_msg="Application started", version="0.1.0")
    try:
        log.info("application-running", _replace_msg="Application running")
        # Your application logic here
    except Exception as e:
        log.exception("application-error", _replace_msg="Application error occurred", error=str(e))
    finally:
        log.info("application-completed", _replace_msg="Application completed")

if __name__ == "__main__":
    exit(main())
EOF

# 3. Create translation files
mkdir -p translations
cat > translations/en.toml << 'EOF'
application-started = "🚀 Application started (version: {version})"
application-running = "⚙️ Application is running"
application-error = "❌ Application error: {error}"
application-completed = "✅ Application completed successfully"
EOF

# 4. Validate setup
python main.py
nicestlog tools i18n check . --translation-dir translations -l en --strict
```

## Template 5: CI/CD Integration

### Use Case
Adding nicestlog quality checks to continuous integration.

### GitHub Actions Workflow
```yaml
# .github/workflows/logging-quality.yml
name: Logging Quality Check

on: [push, pull_request]

jobs:
  logging-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install uv
        uses: astral-sh/setup-uv@v3
        
      - name: Install dependencies
        run: uv sync --locked
        
      - name: Check logging quality
        run: |
          uv run nicestlog check . --ast --verbose
          
      - name: Check translation completeness
        run: |
          uv run nicestlog tools i18n check . --translation-dir translations -l en --strict --fail-on-extra
          
      - name: Analyze project structure
        run: |
          uv run nicestlog migrate . --json > analysis.json
          cat analysis.json | jq '.recommendation'
```

### Pre-commit Hook
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: nicestlog-check
        name: nicestlog quality check
        entry: uv run nicestlog check . --ast
        language: system
        types: [python]
        
      - id: nicestlog-i18n
        name: nicestlog translation check
        entry: uv run nicestlog tools i18n check . --translation-dir translations -l en --strict
        language: system
        files: '^(.*\.py|translations/.*\.toml)$'
```

## Template 6: Performance-Critical Migration

### Use Case
High-performance applications where logging overhead matters.

### Agent Workflow
```bash
# 1. Analyze performance requirements
nicestlog migrate . --json | jq '.complexity'

# 2. Configure for performance
cat > pyproject.toml.perf << 'EOF'
[tool.nicestlog]
verbose = false  # Disable debug logging in production
async_logging = true  # Enable async for performance
log_format = "json"  # JSON is faster than console formatting
syslog_identifier = "high-perf-app"
EOF

# 3. Migrate with performance considerations
nicestlog migrate . --type print-to-structlog --backup

# 4. Add conditional debug logging
find . -name "*.py" -exec sed -i 's/log\.debug(/if log.isEnabledFor(logging.DEBUG): log.debug(/g' {} \;

# 5. Benchmark before/after
python << 'EOF'
import time
import structlog
import nicestlog

# Benchmark logging performance
nicestlog.init_logging(async_logging=True)
log = structlog.get_logger()

start = time.time()
for i in range(10000):
    log.info("performance-test", iteration=i, data={"key": "value"})
end = time.time()

print(f"10,000 log entries in {end-start:.3f}s")
print(f"Rate: {10000/(end-start):.0f} logs/second")
EOF
```

## Template 7: Docker/Container Integration

### Use Case
Containerized applications with proper log handling.

### Dockerfile Integration
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --locked

# Copy application
COPY . .

# Configure logging for containers
ENV NICESTLOG_VERBOSE=false
ENV NICESTLOG_LOG_FORMAT=json
ENV NICESTLOG_SYSLOG_IDENTIFIER=myapp

# Run application
CMD ["uv", "run", "python", "main.py"]
```

### Docker Compose with Log Aggregation
```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    environment:
      - NICESTLOG_VERBOSE=false
      - NICESTLOG_LOG_FORMAT=json
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    depends_on:
      - fluentd

  fluentd:
    image: fluent/fluentd:v1.16
    volumes:
      - ./fluentd.conf:/fluentd/etc/fluent.conf
    ports:
      - "24224:24224"
```

## Success Validation Checklist

After applying any template, validate with:

```bash
# ✅ Code quality
nicestlog check . --ast --verbose

# ✅ Translation completeness  
nicestlog tools i18n check . --translation-dir translations -l en --strict

# ✅ Performance check
python -c "
import time
import nicestlog
import structlog

nicestlog.init_logging()
log = structlog.get_logger()

start = time.time()
for i in range(1000):
    log.info('test', i=i)
duration = time.time() - start
print(f'1000 logs in {duration:.3f}s - {"✅ PASS" if duration < 1.0 else "❌ SLOW"}')
"

# ✅ Integration test
python -c "
import nicestlog
import structlog

nicestlog.init_logging(verbose=True)
log = structlog.get_logger()

log.info('integration-test', status='success')
print('✅ Integration test passed')
"
```