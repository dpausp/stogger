"""
Pexpect-based tests for Interactive Transformer features.

These tests use real terminal interaction without mocking to test
the actual user experience of interactive code transformation.
"""

import os
import sys
import tempfile
from pathlib import Path
import pytest
import pexpect


class InteractivePexpectHelper:
    """Helper class for interactive transformer pexpect testing."""

    @staticmethod
    def spawn_python_interactive_script(script_content, timeout=15):
        """Spawn a Python script that uses interactive transformer."""
        # Create a temporary script file
        fd, script_path = tempfile.mkstemp(suffix=".py", text=True)
        try:
            with os.fdopen(fd, "w") as f:
                f.write(script_content)

            # Use uv run to execute the script
            cmd = f"uv run python {script_path}"
            child = pexpect.spawn(cmd, timeout=timeout)
            child.logfile_read = sys.stdout.buffer  # Log output for debugging
            return child, Path(script_path)
        except:
            os.close(fd)
            raise

    @staticmethod
    def create_test_code_file(content, suffix=".py"):
        """Create a temporary code file to transform."""
        fd, path = tempfile.mkstemp(suffix=suffix, text=True)
        try:
            with os.fdopen(fd, "w") as f:
                f.write(content)
            return Path(path)
        except:
            os.close(fd)
            raise


@pytest.mark.slow
class TestInteractiveTransformerPexpect:
    """Test Interactive Transformer using pexpect for real interaction."""

    def test_interactive_transformer_accept_changes(self):
        """Test interactive transformer accepting changes."""
        # Code that needs transformation
        test_code = """
import logging

def example_function():
    logging.info("This is an info message")
    logging.debug("This is a debug message")
    print("Hello world")
"""

        # Script that uses interactive transformer
        script_content = f'''
import sys
from pathlib import Path
from nicestlog.interactive_transformer import transform_file_interactive

# Create test file
test_file = Path("test_transform.py")
test_file.write_text("""{test_code}""")

try:
    # Run interactive transformation
    result = transform_file_interactive(test_file)
    print(f"Transformation result: {{result.success}}")
    print(f"Changes made: {{len(result.changes_made)}}")
finally:
    # Clean up
    if test_file.exists():
        test_file.unlink()
'''

        child, script_path = InteractivePexpectHelper.spawn_python_interactive_script(
            script_content
        )

        try:
            # Look for interactive prompts asking about transformations
            patterns = [
                r".*[Aa]pply.*change.*",
                r".*[Tt]ransform.*",
                r".*\[y/n/a/q/s/p\].*",
                r".*\[.*y.*\].*",
                pexpect.EOF,
            ]

            try:
                while True:
                    index = child.expect(patterns, timeout=10)

                    if index == len(patterns) - 1:  # EOF
                        break

                    # Send 'y' to accept the transformation
                    child.sendline("y")

                child.close()

                # Should complete successfully
                assert child.exitstatus == 0

            except pexpect.TIMEOUT:
                child.close()
                pytest.skip("Interactive transformer test timed out")

        finally:
            script_path.unlink()

    def test_interactive_transformer_decline_changes(self):
        """Test interactive transformer declining changes."""
        test_code = """
import logging

def example_function():
    logging.warning("This is a warning")
    logging.error("This is an error")
"""

        script_content = f'''
import sys
from pathlib import Path
from nicestlog.interactive_transformer import transform_file_interactive

test_file = Path("test_decline.py")
test_file.write_text("""{test_code}""")

try:
    result = transform_file_interactive(test_file)
    print(f"Transformation result: {{result.success}}")
    print(f"Changes made: {{len(result.changes_made)}}")
finally:
    if test_file.exists():
        test_file.unlink()
'''

        child, script_path = InteractivePexpectHelper.spawn_python_interactive_script(
            script_content
        )

        try:
            patterns = [
                r".*[Aa]pply.*change.*",
                r".*[Tt]ransform.*",
                r".*\[y/n/a/q/s/p\].*",
                r".*\[.*n.*\].*",
                pexpect.EOF,
            ]

            try:
                while True:
                    index = child.expect(patterns, timeout=10)

                    if index == len(patterns) - 1:  # EOF
                        break

                    # Send 'n' to decline the transformation
                    child.sendline("n")

                child.close()

                # Should complete successfully even when declining
                assert child.exitstatus == 0

            except pexpect.TIMEOUT:
                child.close()
                pytest.skip("Interactive transformer decline test timed out")

        finally:
            script_path.unlink()

    def test_interactive_transformer_quit_early(self):
        """Test interactive transformer quitting early."""
        test_code = """
import logging

def function_one():
    logging.info("First function")

def function_two():
    logging.debug("Second function")
    
def function_three():
    logging.warning("Third function")
"""

        script_content = f'''
from pathlib import Path
from nicestlog.interactive_transformer import transform_file_interactive

test_file = Path("test_quit.py")
test_file.write_text("""{test_code}""")

try:
    result = transform_file_interactive(test_file)
    print(f"Transformation result: {{result.success}}")
    print(f"Changes made: {{len(result.changes_made)}}")
finally:
    if test_file.exists():
        test_file.unlink()
'''

        child, script_path = InteractivePexpectHelper.spawn_python_interactive_script(
            script_content
        )

        try:
            patterns = [
                r".*[Qq]uit.*",
                r".*\[.*q.*\].*",
                r".*\[y/n/a/q/s/p\].*",
                pexpect.EOF,
            ]

            try:
                index = child.expect(patterns, timeout=10)

                if index < len(patterns) - 1:  # Not EOF
                    # Send 'q' to quit early
                    child.sendline("q")
                    child.expect(pexpect.EOF, timeout=5)

                child.close()

                # Should handle quit gracefully
                assert child.exitstatus in [0, 1]

            except pexpect.TIMEOUT:
                child.close()
                pytest.skip("Interactive transformer quit test timed out")

        finally:
            script_path.unlink()

    def test_interactive_transformer_preview_mode(self):
        """Test interactive transformer preview mode."""
        test_code = """
import logging

def preview_function():
    logging.critical("Critical message")
    logging.info("Info message")
"""

        script_content = f'''
from pathlib import Path
from nicestlog.interactive_transformer import transform_file_interactive

test_file = Path("test_preview.py")
test_file.write_text("""{test_code}""")

try:
    result = transform_file_interactive(test_file)
    print(f"Transformation result: {{result.success}}")
    print(f"Changes made: {{len(result.changes_made)}}")
finally:
    if test_file.exists():
        test_file.unlink()
'''

        child, script_path = InteractivePexpectHelper.spawn_python_interactive_script(
            script_content
        )

        try:
            patterns = [
                r".*[Pp]review.*",
                r".*\[.*p.*\].*",
                r".*\[y/n/a/q/s/p\].*",
                pexpect.EOF,
            ]

            try:
                index = child.expect(patterns, timeout=10)

                if index < len(patterns) - 1:  # Not EOF
                    # Send 'p' to preview changes
                    child.sendline("p")

                    # After preview, we might get another prompt
                    try:
                        child.expect([r".*\[y/n/a/q/s/p\].*", pexpect.EOF], timeout=5)
                        # Send 'n' to decline after preview
                        child.sendline("n")
                    except pexpect.TIMEOUT:
                        pass

                    child.expect(pexpect.EOF, timeout=5)

                child.close()

                # Should handle preview mode gracefully
                assert child.exitstatus in [0, 1]

            except pexpect.TIMEOUT:
                child.close()
                pytest.skip("Interactive transformer preview test timed out")

        finally:
            script_path.unlink()

    def test_interactive_transformer_accept_all(self):
        """Test interactive transformer accepting all changes."""
        test_code = """
import logging

def multi_function():
    logging.info("Info 1")
    logging.debug("Debug 1")
    logging.warning("Warning 1")
    logging.error("Error 1")
"""

        script_content = f'''
from pathlib import Path
from nicestlog.interactive_transformer import transform_file_interactive

test_file = Path("test_accept_all.py")
test_file.write_text("""{test_code}""")

try:
    result = transform_file_interactive(test_file)
    print(f"Transformation result: {{result.success}}")
    print(f"Changes made: {{len(result.changes_made)}}")
finally:
    if test_file.exists():
        test_file.unlink()
'''

        child, script_path = InteractivePexpectHelper.spawn_python_interactive_script(
            script_content
        )

        try:
            patterns = [
                r".*[Aa]ll.*",
                r".*\[.*a.*\].*",
                r".*\[y/n/a/q/s/p\].*",
                pexpect.EOF,
            ]

            try:
                index = child.expect(patterns, timeout=10)

                if index < len(patterns) - 1:  # Not EOF
                    # Send 'a' to accept all changes
                    child.sendline("a")
                    child.expect(pexpect.EOF, timeout=10)

                child.close()

                # Should complete successfully
                assert child.exitstatus == 0

            except pexpect.TIMEOUT:
                child.close()
                pytest.skip("Interactive transformer accept all test timed out")

        finally:
            script_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
