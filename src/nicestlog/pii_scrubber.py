"""PII (Personally Identifiable Information) Scrubber for nicestlog.

Automatically detects and redacts sensitive information from log messages.
"""

from __future__ import annotations

import re
from typing import Any



class PIIScrubber:
    """Scrubs PII from log messages using regex patterns and field name detection."""

    def __init__(
        self,
        custom_patterns: dict[str, str] | None = None,
        sensitive_fields: list[str] | None = None,
        redaction_text: str = "[REDACTED]",
    ):
        """Initialize PII scrubber.

        Args:
            custom_patterns: Additional regex patterns {name: pattern}
            sensitive_fields: Field names that should always be redacted
            redaction_text: Text to replace sensitive data with

        """
        self.redaction_text = redaction_text

        # Default PII patterns
        self.patterns = {
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "phone": r"(\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}",
            "ssn": r"\b\d{3}-?\d{2}-?\d{4}\b",
            "credit_card": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
            "ip_address": r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b",
            "password": r'(?i)(password|passwd|pwd|secret|token|key)\s*[:=]\s*[^\s\'"]+',
            "api_key": r'(?i)(api[_-]?key|apikey|access[_-]?token)\s*[:=]\s*[^\s\'"]+',
            "jwt": r"eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*",
            "uuid": r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
        }

        # Add custom patterns
        if custom_patterns:
            self.patterns.update(custom_patterns)

        # Compile patterns for performance
        self.compiled_patterns = {
            name: re.compile(pattern, re.IGNORECASE)
            for name, pattern in self.patterns.items()
        }

        # Sensitive field names (case-insensitive)
        self.sensitive_fields = {
            "password",
            "passwd",
            "pwd",
            "secret",
            "token",
            "key",
            "api_key",
            "access_token",
            "refresh_token",
            "auth_token",
            "session_id",
            "email",
            "email_address",
            "phone",
            "phone_number",
            "ssn",
            "social_security_number",
            "credit_card",
            "card_number",
            "account_number",
            "routing_number",
            "iban",
            "swift",
            "address",
            "street_address",
            "home_address",
            "billing_address",
        }

        if sensitive_fields:
            self.sensitive_fields.update(f.lower() for f in sensitive_fields)

    def scrub_string(self, text: str) -> str:
        """Scrub PII from a string."""
        if not isinstance(text, str):
            return text

        result = text
        for pattern_name, pattern in self.compiled_patterns.items():
            if pattern_name == "password":
                # Special handling for password patterns to keep the field name
                result = pattern.sub(
                    lambda m: f"{m.group(1)}={self.redaction_text}",
                    result,
                )
            else:
                result = pattern.sub(self.redaction_text, result)

        return result

    def scrub_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Scrub PII from dictionary values and sensitive field names."""
        if not isinstance(data, dict):
            return data

        scrubbed: dict[str, Any] = {}
        for key, value in data.items():
            # Check if field name is sensitive
            if key.lower() in self.sensitive_fields:
                scrubbed[key] = self.redaction_text
            elif isinstance(value, str):
                scrubbed[key] = self.scrub_string(value)
            elif isinstance(value, dict):
                scrubbed[key] = self.scrub_dict(value)
            elif isinstance(value, list):
                scrubbed[key] = self.scrub_list(value)
            else:
                scrubbed[key] = value

        return scrubbed

    def scrub_list(self, data: list[Any]) -> list[Any]:
        """Scrub PII from list items."""
        if not isinstance(data, list):
            return data

        scrubbed: list[Any] = []
        for item in data:
            if isinstance(item, str):
                scrubbed.append(self.scrub_string(item))
            elif isinstance(item, dict):
                scrubbed.append(self.scrub_dict(item))
            elif isinstance(item, list):
                scrubbed.append(self.scrub_list(item))
            else:
                scrubbed.append(item)

        return scrubbed

    def scrub_event_dict(self, event_dict: dict[str, Any]) -> dict[str, Any]:
        """Scrub PII from a structlog event dictionary.

        This is the main method used as a structlog processor.
        """
        # Scrub the main event message
        if "event" in event_dict and isinstance(event_dict["event"], str):
            event_dict["event"] = self.scrub_string(event_dict["event"])

        # Scrub all other fields
        for key, value in list(event_dict.items()):
            if key in ["timestamp", "level", "logger"]:
                continue  # Skip system fields

            if key.lower() in self.sensitive_fields:
                event_dict[key] = self.redaction_text
            elif isinstance(value, str):
                event_dict[key] = self.scrub_string(value)
            elif isinstance(value, dict):
                event_dict[key] = self.scrub_dict(value)
            elif isinstance(value, list):
                event_dict[key] = self.scrub_list(value)

        return event_dict

    def __call__(self, _, __, event_dict):
        """Make the scrubber callable as a structlog processor."""
        return self.scrub_event_dict(event_dict)


# Convenience function for easy integration
def create_pii_processor(
    custom_patterns: dict[str, str] | None = None,
    sensitive_fields: list[str] | None = None,
    redaction_text: str = "[REDACTED]",
) -> PIIScrubber:
    """Create a PII scrubber processor for structlog."""
    return PIIScrubber(
        custom_patterns=custom_patterns,
        sensitive_fields=sensitive_fields,
        redaction_text=redaction_text,
    )


# Demo and testing
def demo_pii_scrubbing():
    """Demonstrate PII scrubbing capabilities."""
    scrubber = PIIScrubber()


    # Test data with various PII
    test_cases = [
        {
            "description": "Email addresses",
            "input": "User john.doe@example.com logged in",
            "expected": "Email should be redacted",
        },
        {
            "description": "Phone numbers",
            "input": "Contact: +1-555-123-4567 or (555) 987-6543",
            "expected": "Phone numbers should be redacted",
        },
        {
            "description": "Passwords in logs",
            "input": "Login failed: password=secret123 for user admin",
            "expected": "Password value should be redacted",
        },
        {
            "description": "API keys",
            "input": "API_KEY=sk_live_abc123xyz789 used for payment",
            "expected": "API key should be redacted",
        },
        {
            "description": "Credit card numbers",
            "input": "Payment with card 4532-1234-5678-9012 processed",
            "expected": "Card number should be redacted",
        },
        {
            "description": "IP addresses",
            "input": "Request from 192.168.1.100 blocked",
            "expected": "IP should be redacted",
        },
        {
            "description": "JWT tokens",
            "input": "Token: eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.signature",
            "expected": "JWT should be redacted",
        },
    ]

    for test in test_cases:
        scrubber.scrub_string(test["input"])

    # Test dictionary scrubbing
    test_dict = {
        "user_id": 12345,
        "email": "user@example.com",
        "password": "secret123",
        "phone": "+1-555-123-4567",
        "message": "Contact me at john@test.com",
        "metadata": {"api_key": "sk_test_abc123", "session_id": "sess_xyz789"},
    }

    scrubber.scrub_dict(test_dict)



if __name__ == "__main__":
    demo_pii_scrubbing()
