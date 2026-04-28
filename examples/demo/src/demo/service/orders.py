"""Service layer with correct logging conventions.

This file demonstrates proper usage of ALL logging conventions.
Every rule in pytest-stogger should PASS for this file.
"""

import structlog

log = structlog.get_logger(__name__)


def process_order(order_id: str, customer: str) -> None:
    """Process a customer order — demonstrates correct info-level logging."""
    log.info(
        "order-processed",
        order_id=order_id,
        customer=customer,
        _replace_msg="Order {order_id} processed for {customer}",
    )


def check_inventory(item: str) -> bool:
    """Private helper — uses debug, not info."""
    available = item in ["widget", "gadget"]
    if not available:
        log.debug("item-not-available", item=item)
    return available


def handle_payment(amount: float) -> None:
    """Payment processing with proper exception handling."""
    try:
        # Simulate payment
        if amount > 1000:
            msg = "Amount too large"
            raise ValueError(msg)
        log.info(
            "payment-processed",
            amount=amount,
            _replace_msg="Payment of {amount} processed",
        )
    except ValueError as e:
        log.exception(
            "payment-failed",
            amount=amount,
            reason=str(e),
        )
