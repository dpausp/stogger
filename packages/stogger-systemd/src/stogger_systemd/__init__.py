"""Systemd journal integration for stogger."""

__all__ = [
    "create_systemd_service_file",
    "demo_systemd_integration",
    "setup_systemd_logging",
]


def __getattr__(name: str) -> object:
    """Lazy imports to avoid crashing when systemd native bindings are unavailable."""
    if name == "create_systemd_service_file":
        from .systemd_integration import create_systemd_service_file

        return create_systemd_service_file
    if name == "demo_systemd_integration":
        from .systemd_integration import demo_systemd_integration

        return demo_systemd_integration
    if name == "setup_systemd_logging":
        from .systemd_integration import setup_systemd_logging

        return setup_systemd_logging
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
