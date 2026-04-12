#!/usr/bin/env python3
"""Demo: PII Scrubbing in action with stogger.

Shows how sensitive data gets automatically redacted from logs.
"""

import structlog

import stogger


def demo_pii_protection():
    """Demonstrate automatic PII protection."""
    # Initialize stogger with PII scrubbing enabled (default)
    stogger.init_logging(syslog_identifier="pii-demo")

    log = structlog.get_logger("security")

    print("🔒 PII Scrubbing Demo - Automatic Data Protection")
    print("=" * 60)
    print("Watch how sensitive data gets automatically redacted!\n")

    # These logs contain PII that should be automatically scrubbed
    log.info(
        "user_login_attempt",
        username="john.doe",
        email="john.doe@company.com",
        password="secret123",  # This should be redacted!
        ip_address="192.168.1.100",
    )

    log.warning(
        "payment_processing",
        user_email="customer@example.com",
        credit_card="4532-1234-5678-9012",  # This should be redacted!
        amount=99.99,
        api_key="sk_live_abc123xyz789",
    )  # This should be redacted!

    log.error(
        "authentication_failed",
        message="Login failed for user admin@test.com with token eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.signature",
        phone="+1-555-123-4567",  # This should be redacted!
        session_id="sess_abc123",
    )  # This should be redacted!

    log.info(
        "api_request",
        endpoint="/users/profile",
        user_data={
            "name": "Jane Smith",
            "email": "jane@example.com",  # This should be redacted!
            "phone": "(555) 987-6543",  # This should be redacted!
            "address": "123 Main St",  # This should be redacted!
        },
    )

    log.debug(
        "database_query",
        sql="SELECT * FROM users WHERE email = 'test@example.com'",  # Email in SQL should be redacted!
        execution_time=0.045,
    )

    print("\n🎉 Demo complete!")
    print(
        "💡 Notice how emails, passwords, phone numbers, etc. are automatically [REDACTED]",
    )
    print("🔐 Your logs are now safe for sharing and compliance!")


def demo_custom_pii_config():
    """Show how to customize PII scrubbing."""
    print("\n" + "=" * 60)
    print("🛠️  Custom PII Configuration Demo")
    print("=" * 60)

    # Create custom PII processor with different redaction text
    custom_scrubber = stogger.create_pii_processor(
        redaction_text="***HIDDEN***",
        custom_patterns={
            "employee_id": r"EMP\d{6}",  # Custom pattern for employee IDs
            "order_number": r"ORD-\d{8}",  # Custom pattern for order numbers
        },
        sensitive_fields=["internal_notes", "salary"],  # Additional sensitive fields
    )

    # Configure structlog with custom scrubber
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            custom_scrubber,  # Our custom PII scrubber
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    log = structlog.get_logger("custom")

    log.info(
        "employee_record",
        employee_id="EMP123456",  # Custom pattern - should be redacted
        email="employee@company.com",
        salary=75000,  # Sensitive field - should be redacted
        order_number="ORD-98765432",  # Custom pattern - should be redacted
        internal_notes="Confidential performance review",
    )  # Sensitive field - should be redacted

    print("\n💡 Custom patterns and fields are also protected!")


if __name__ == "__main__":
    demo_pii_protection()
    demo_custom_pii_config()
