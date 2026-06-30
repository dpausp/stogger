"""Demo runner — shows stogger decorator output on console.

Run with: uv run python -m demo
"""

if __name__ == "__main__":
    from stogger import init_logging
    from demo.service.orders import demo_decorators

    init_logging(verbose=True)
    demo_decorators()
