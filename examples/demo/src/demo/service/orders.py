"""Service layer with correct logging conventions.

Demonstrates stogger decorators: log_operation, log_call, log_result, log_scope.
"""

import structlog
from stogger import log_call, log_operation, log_result, log_scope

log = structlog.get_logger(__name__)


@log_call
def validate_order(order_id: str) -> bool:
    """Check if order exists — log_call logs entry with args."""
    return order_id.startswith("ORD-")


@log_operation
def calculate_total(items: list[str], discount: float = 0.0) -> float:
    """Calculate order total — log_operation logs args + result + duration."""
    base = len(items) * 9.99
    return base * (1 - discount)


@log_result
def charge_customer(amount: float, customer: str) -> str:
    """Charge customer — log_result logs return value + duration."""
    if amount > 1000:
        msg = "Amount too large"
        raise ValueError(msg)
    return f"CHG-{int(amount * 100)}"


def process_order(order_id: str, customer: str) -> None:
    """Full order processing with log_scope for context binding."""
    log.info(
        "order-processed",
        order_id=order_id,
        customer=customer,
        _replace_msg="Order {order_id} processed for {customer}",
    )


def handle_payment(amount: float) -> None:
    """Payment processing with proper exception handling."""
    try:
        if amount > 1000:
            msg = "Amount too large"
            raise ValueError(msg)
        log.info(
            "payment-processed",
            amount=amount,
            _replace_msg="Payment of {amount} processed",
        )
    except ValueError:
        log.exception(
            "payment-failed",
            amount=amount,
        )


def demo_decorators() -> None:
    """Run all decorator demos to show console output."""
    with log_scope("demo-session", run_id="abc123"):
        # log_call — entry logging
        valid = validate_order("ORD-42")
        log.info("validation-result", _replace_msg="Valid: {valid}", valid=valid)

        # log_operation — args + result + duration (now on debug!)
        total = calculate_total(["widget", "gadget"], discount=0.1)
        log.info(
            "total-calculated",
            _replace_msg="Total: {total:.2f}",
            total=total,
        )

        # log_result — return value + duration
        try:
            ref = charge_customer(total, "alice")
            log.info("charge-ref", _replace_msg="Charge ref: {ref}", ref=ref)
        except ValueError:
            log.exception("charge-failed", amount=total)

        # log_operation with normal path (no exception)
        calculate_total(["x"] * 200, discount=0.0)

        # Demonstrate a failing operation
        try:
            charge_customer(9999.0, "bob")
        except ValueError:
            log.exception("demo-charge-failed", amount=9999.0)
