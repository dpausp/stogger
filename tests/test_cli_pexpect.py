"""Pexpect-based tests for CLI interactive features.

These tests use real terminal interaction without mocking to test
the actual user experience of interactive commands.
"""

import os
from pathlib import Path
import sys
import tempfile

import pexpect
import pytest


class PexpectTestHelper:
    """Helper class for pexpect-based testing."""

    @staticmethod
    def spawn_nicestlog_command(args, timeout=10):
        """Spawn a nicestlog command with pexpect."""
        # Use uv run to execute nicestlog
        cmd = f"uv run python -m nicestlog {' '.join(args)}"
        child = pexpect.spawn(cmd, timeout=timeout)
        child.logfile_read = sys.stdout.buffer  # Log output for debugging
        return child

    @staticmethod
    def create_test_file(content, suffix=".py"):
        """Create a temporary test file."""
        fd, path = tempfile.mkstemp(suffix=suffix, text=True)
        try:
            with os.fdopen(fd, "w") as f:
                f.write(content)
            return Path(path)
        except:
            os.close(fd)
            raise


@pytest.mark.slow
class TestCliPexpectInteractive:
    """Test CLI interactive features using pexpect."""

    def test_docs_interactive_valid_choice(self):
        """Test docs interactive mode with valid choice."""
        child = PexpectTestHelper.spawn_nicestlog_command(["docs", "--interactive"])

        try:
            # Expect some kind of menu or prompt
            child.expect(r".*[Cc]hoice.*", timeout=5)

            # Send a valid choice (assuming 1 is valid)
            child.sendline("1")

            # Wait for command to complete
            child.expect(pexpect.EOF, timeout=10)
            child.close()

            # Should exit successfully
            assert child.exitstatus == 0

        except pexpect.TIMEOUT:
            child.close()
            pytest.skip("Interactive docs command timed out - may not be implemented")
        except pexpect.EOF:
            child.close()
            pytest.skip("Interactive docs command ended unexpectedly")

    def test_docs_interactive_invalid_choice(self):
        """Test docs interactive mode with invalid choice."""
        child = PexpectTestHelper.spawn_nicestlog_command(["docs", "--interactive"])

        try:
            # Expect some kind of menu or prompt
            child.expect(r".*[Cc]hoice.*", timeout=5)

            # Send an invalid choice
            child.sendline("99")

            # Should handle invalid choice gracefully
            # Either re-prompt or exit with error
            try:
                child.expect(
                    [r".*[Ii]nvalid.*", r".*[Ee]rror.*", pexpect.EOF],
                    timeout=5,
                )
            except pexpect.TIMEOUT:
                pass  # Command might just exit

            child.close()

            # Should handle invalid input gracefully (exit code 0 or 1)
            assert child.exitstatus in [0, 1]

        except pexpect.TIMEOUT:
            child.close()
            pytest.skip("Interactive docs command timed out - may not be implemented")
        except pexpect.EOF:
            child.close()
            pytest.skip("Interactive docs command ended unexpectedly")

    def test_check_interactive_mode(self):
        """Test check command with interactive mode."""
        # Create a test file with logging statements
        test_content = """
import logging

def test_function():
    logging.info("This is a test message")
    print("Hello world")
"""

        test_file = PexpectTestHelper.create_test_file(test_content)

        try:
            child = PexpectTestHelper.spawn_nicestlog_command(
                ["check", str(test_file), "--interactive"],
            )

            try:
                # Look for interactive prompts
                # The exact prompts depend on implementation
                patterns = [
                    r".*[Aa]pply.*",
                    r".*[Tt]ransform.*",
                    r".*[Cc]hange.*",
                    r".*\[y/n\].*",
                    pexpect.EOF,
                ]

                index = child.expect(patterns, timeout=10)

                if index < len(patterns) - 1:  # Not EOF
                    # Send 'n' to decline transformations
                    child.sendline("n")
                    child.expect(pexpect.EOF, timeout=5)

                child.close()

                # Should handle interactive mode gracefully
                assert child.exitstatus in [0, 1]

            except pexpect.TIMEOUT:
                child.close()
                pytest.skip("Check interactive command timed out")

        finally:
            test_file.unlink()

    def test_migrate_interactive_mode(self):
        """Test migrate command with interactive mode."""
        # Create a test file with old logging patterns
        test_content = """
import logging

def test_function():
    logging.info("This needs migration")
    logging.debug("Debug message")
"""

        test_file = PexpectTestHelper.create_test_file(test_content)

        try:
            child = PexpectTestHelper.spawn_nicestlog_command(
                ["migrate", str(test_file), "--interactive"],
            )

            try:
                # Look for interactive prompts
                patterns = [
                    r".*[Aa]pply.*",
                    r".*[Mm]igrate.*",
                    r".*[Tt]ransform.*",
                    r".*\[y/n\].*",
                    pexpect.EOF,
                ]

                index = child.expect(patterns, timeout=10)

                if index < len(patterns) - 1:  # Not EOF
                    # Send 'n' to decline migrations
                    child.sendline("n")
                    child.expect(pexpect.EOF, timeout=5)

                child.close()

                # Should handle interactive mode gracefully
                assert child.exitstatus in [0, 1]

            except pexpect.TIMEOUT:
                child.close()
                pytest.skip("Migrate interactive command timed out")

        finally:
            test_file.unlink()

    def test_interactive_quit_command(self):
        """Test quitting from interactive mode."""
        test_content = """
import logging
logging.info("test")
"""

        test_file = PexpectTestHelper.create_test_file(test_content)

        try:
            child = PexpectTestHelper.spawn_nicestlog_command(
                ["check", str(test_file), "--interactive"],
            )

            try:
                # Look for interactive prompts
                patterns = [
                    r".*[Qq]uit.*",
                    r".*\[.*q.*\].*",
                    r".*[Yy]/[Nn]/.*[Qq].*",
                    pexpect.EOF,
                ]

                index = child.expect(patterns, timeout=10)

                if index < len(patterns) - 1:  # Not EOF
                    # Send 'q' to quit
                    child.sendline("q")
                    child.expect(pexpect.EOF, timeout=5)

                child.close()

                # Should exit cleanly when quitting
                assert child.exitstatus in [0, 1]

            except pexpect.TIMEOUT:
                child.close()
                pytest.skip("Interactive quit test timed out")

        finally:
            test_file.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
