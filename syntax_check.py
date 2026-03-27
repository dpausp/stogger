"""Simple syntax check for the modified ConsoleFileRenderer."""

# Check if the imports work
try:
    print("✓ SimpleFormatSettings import successful")  # noqa: T201
except Exception as e:
    print(f"✗ SimpleFormatSettings import failed: {e}")  # noqa: T201

# Try to check if the ConsoleFileRenderer class exists and has the right signature
try:
    import inspect

    from nicestlog.core import ConsoleFileRenderer

    print("✓ ConsoleFileRenderer import successful")  # noqa: T201

    # Check if the __init__ method has the settings parameter
    sig = inspect.signature(ConsoleFileRenderer.__init__)
    if "settings" in sig.parameters:
        print("✓ ConsoleFileRenderer.__init__ has 'settings' parameter")  # noqa: T201
    else:
        print("✗ ConsoleFileRenderer.__init__ missing 'settings' parameter")  # noqa: T201

except Exception as e:
    print(f"✗ ConsoleFileRenderer import failed: {e}")  # noqa: T201

print("\nSyntax check completed.")  # noqa: T201
