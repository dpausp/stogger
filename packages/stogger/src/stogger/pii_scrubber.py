r"""PII (Personally Identifiable Information) Scrubber for stogger.

Automatically detects and redacts sensitive information from log messages
and structured event dictionaries. Usable as a structlog processor or
standalone scrubber.

Default regex patterns detect: email addresses, phone numbers, SSNs,
credit card numbers, IPv4 addresses, password/secret assignments,
API keys/tokens, JWT tokens, and UUIDs.

Default sensitive field names include: password, token, api_key, email,
phone_number, ssn, credit_card, address, and many more (case-insensitive
matching).

Usage as structlog processor::

    import structlog
    from stogger.pii_scrubber import create_pii_processor

    config = structlog.get_config()
    config["processors"].insert(-1, create_pii_processor())

Usage standalone::

    from stogger.pii_scrubber import PIIScrubber

    scrubber = PIIScrubber(
        custom_patterns={"zip": r"\\b\\d{5}(-\\d{4})?\\b"},
        sensitive_fields=["favorite_color"],
    )
    clean = scrubber.scrub_string("user@corp.io lives at 90210")
"""

import re
from typing import Any


class PIIScrubber:
    """Detects and redacts PII from strings, dicts, and structlog event dicts.

    Combines regex-based pattern matching with field-name detection. Any
    dictionary key matching a known sensitive field name is redacted regardless
    of value. String values are scanned for patterns like email, phone, SSN,
    credit card, IP, password assignments, API keys, JWTs, and UUIDs.

    The instance is callable and can be inserted directly into a structlog
    processor chain.
    """

    def __init__(
        self,
        custom_patterns: dict[str, str] | None = None,
        sensitive_fields: list[str] | None = None,
        redaction_text: str = "[REDACTED]",
    ) -> None:
        """Initialize PII scrubber with optional custom patterns and fields.

        Args:
            custom_patterns: Additional regex patterns as ``{name: pattern}``.
                Merged with built-in patterns. Names matching a built-in
                pattern name override it.
            sensitive_fields: Extra field names whose values should always be
                redacted. Added to the built-in set (case-insensitive).
            redaction_text: Replacement text for redacted values.

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
        self.compiled_patterns = {name: re.compile(pattern, re.IGNORECASE) for name, pattern in self.patterns.items()}

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
        """Scrub PII from a plain string using all compiled regex patterns.

        Password/secret assignment patterns preserve the field name in output
        (e.g. ``password=secret`` → ``password=[REDACTED]``). All other
        patterns replace the entire match with ``redaction_text``.

        Args:
            text: Input string to scan for PII.

        Returns:
            String with detected PII replaced by the redaction text.

        """
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
        """Scrub PII from a dictionary, recursing into nested dicts and lists.

        Values under keys matching ``sensitive_fields`` are unconditionally
        redacted. String values are regex-scanned via ``scrub_string``.
        Nested dicts and lists are processed recursively.

        Args:
            data: Dictionary to scrub. Not modified in-place; a new dict is
                returned.

        Returns:
            New dictionary with PII redacted.

        """
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
        """Scrub PII from a list, recursing into nested dicts and lists.

        Args:
            data: List to scrub. Not modified in-place.

        Returns:
            New list with PII redacted in string/dict/list items.

        """
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

        Primary entry point when used as a structlog processor. The
        ``"event"`` message is always scrubbed. System fields
        ``timestamp``, ``level``, and ``logger`` are left untouched.
        All other fields are scrubbed via field-name matching and
        regex scanning.

        The dict is modified in-place and returned.

        Args:
            event_dict: Structlog event dictionary to scrub.

        Returns:
            The same event_dict with PII redacted.

        """
        # Scrub the main event message
        if "event" in event_dict and isinstance(event_dict["event"], str):
            event_dict["event"] = self.scrub_string(event_dict["event"])

        # Scrub all other fields
        for key, value in list(event_dict.items()):
            if key in {"timestamp", "level", "logger"}:
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
        """Make the scrubber usable as a structlog processor.

        Delegates to :meth:`scrub_event_dict`.
        """
        return self.scrub_event_dict(event_dict)


# Convenience function for easy integration
def create_pii_processor(
    custom_patterns: dict[str, str] | None = None,
    sensitive_fields: list[str] | None = None,
    redaction_text: str = "[REDACTED]",
) -> PIIScrubber:
    """Create a PIIScrubber configured as a structlog processor.

    Convenience factory that returns a ``PIIScrubber`` instance. Because
    the instance is callable, it can be inserted directly into a structlog
    processor chain.

    Args:
        custom_patterns: Additional regex patterns as ``{name: pattern}``.
            Merged with built-in patterns. Names matching a built-in
            pattern name override it.
        sensitive_fields: Extra field names whose values should always be
            redacted. Added to the built-in set (case-insensitive).
        redaction_text: Replacement text for redacted values.

    Returns:
        A configured :class:`PIIScrubber` instance.

    """
    return PIIScrubber(
        custom_patterns=custom_patterns,
        sensitive_fields=sensitive_fields,
        redaction_text=redaction_text,
    )


# Demo and testing
def demo_pii_scrubbing() -> None:
    """Run built-in test cases demonstrating default PII detection.

    Covers email, phone, password, API key, credit card, IP address,
    and JWT redaction on both strings and nested dictionaries.
    """
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
