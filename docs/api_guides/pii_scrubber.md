# PII Scrubber Module

:::{admonition} Test Coverage: 70.5%
:class: warning

This module has moderate test coverage. Some features may not work as expected.
:::

The `nicestlog.pii_scrubber` module provides PII (Personally Identifiable Information) scrubbing capabilities.

## Basic Usage

```python
from nicestlog.pii_scrubber import create_pii_processor

# Create PII processor
processor = create_pii_processor(redaction_text="[REDACTED]")

# Use as structlog processor
import structlog
structlog.configure(processors=[processor])
```

## create_pii_processor

Create a PII scrubbing processor for structlog.

```python
from nicestlog.pii_scrubber import create_pii_processor

processor = create_pii_processor(
    redaction_text="[REDACTED]"
)
```

## demo_pii_scrubbing

Demonstrate PII scrubbing capabilities.

```python
from nicestlog.pii_scrubber import demo_pii_scrubbing

demo_pii_scrubbing()
```

## Detected PII Types

The scrubber detects and redacts:

- Email addresses
- Phone numbers
- Credit card numbers
- Social security numbers
- IP addresses
- API keys

## API Reference

```{autoapi} nicestlog.pii_scrubber
:members:
```
