"""
Tests for early logging initialization functionality.
"""

import subprocess
import sys
from pathlib import Path


def test_early_logging_initialization():
    """Test that early logging initialization reduces uninitialized structlog messages."""
    
    # Test script that demonstrates early initialization
    test_script = '''
import nicestlog
import structlog

# This should show proper format from the start
log = structlog.get_logger('test')
log.info('early-message', message='Should show early format')

# Full initialization should work without issues
nicestlog.init_logging(verbose=False)
log.info('after-full-init', message='Should show full format')
'''
    
    # Run the test script
    result = subprocess.run(
        [sys.executable, '-c', test_script],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent / 'src'
    )
    
    # Check that it ran successfully
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    
    # Check that we get output (meaning logging worked) - could be in stdout or stderr
    output = result.stdout + result.stderr
    assert output.strip(), "No logging output received"
    
    # Check that both messages appear
    lines = output.strip().split('\n')
    assert len(lines) >= 2, f"Expected at least 2 log lines, got: {lines}"
    
    # Find the early message line
    early_lines = [line for line in lines if 'early-message' in line]
    assert len(early_lines) == 1, f"Expected exactly 1 early message, got: {early_lines}"
    
    early_line = early_lines[0]
    assert 'Should show early format' in early_line
    assert 'T' in early_line  # ISO timestamp format
    
    # Find the full init message line
    full_init_lines = [line for line in lines if 'after-full-init' in line]
    assert len(full_init_lines) == 1, f"Expected exactly 1 full init message, got: {full_init_lines}"
    
    full_init_line = full_init_lines[0]
    assert 'Should show full format' in full_init_line


def test_early_logging_graceful_fallback():
    """Test that early logging fails gracefully if there are issues."""
    
    # Test that logging_initialized works
    test_script = '''
import nicestlog
import structlog

# Should be configured after import
print("Configured:", nicestlog.logging_initialized())

# Should still work after full init
nicestlog.init_logging()
print("Still configured:", nicestlog.logging_initialized())
'''
    
    result = subprocess.run(
        [sys.executable, '-c', test_script],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent / 'src'
    )
    
    assert result.returncode == 0
    lines = result.stdout.strip().split('\n')
    
    # Should show configured both times
    assert 'Configured: True' in lines[0]
    assert 'Still configured: True' in lines[-1]


def test_no_uninitialized_messages_in_cli():
    """Test that CLI commands don't show uninitialized structlog messages."""
    
    # Test a simple CLI command that would trigger logging
    result = subprocess.run(
        [sys.executable, '-m', 'nicestlog', '--help'],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent / 'src'
    )
    
    # Should succeed
    assert result.returncode == 0
    
    # Should not contain the old uninitialized format patterns
    output = result.stdout + result.stderr
    
    # Old format would show: [info     ] message
    # New format shows: timestamp I message
    assert '[info     ]' not in output, "Found uninitialized structlog format"
    assert '[debug    ]' not in output, "Found uninitialized structlog format"