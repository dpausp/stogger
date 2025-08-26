"""Tests for log wrapper anti-pattern detection."""

from pathlib import Path
import tempfile
import textwrap

from nicestlog.linter import analyze_file


def test_wrapper_detection_simple_passthrough():
    """Test detection of simple passthrough wrapper functions."""
    code = textwrap.dedent("""
        import structlog
        log = structlog.get_logger()
        
        def log_info(message, **kwargs):
            log.info(message, **kwargs)
    """)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        f.flush()

        stats, issues = analyze_file(Path(f.name))

        # Should detect wrapper issue
        wrapper_issues = [issue for issue in issues if issue.category == "wrapper"]
        assert len(wrapper_issues) == 1
        assert wrapper_issues[0].event_name == "log_info"
        assert "wrapper" in wrapper_issues[0].reason.lower()


def test_wrapper_detection_conditional_logging():
    """Test detection of conditional logging wrappers."""
    code = textwrap.dedent("""
        import structlog
        log = structlog.get_logger()
        
        def maybe_log_debug(condition, message):
            if condition:
                log.debug(message)
    """)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        f.flush()

        stats, issues = analyze_file(Path(f.name))

        # Should detect wrapper issue
        wrapper_issues = [issue for issue in issues if issue.category == "wrapper"]
        assert len(wrapper_issues) == 1
        assert wrapper_issues[0].event_name == "maybe_log_debug"


def test_wrapper_detection_named_patterns():
    """Test detection of functions with wrapper-like names."""
    code = textwrap.dedent("""
        import structlog
        log = structlog.get_logger()
        
        def write_log_entry(level, message):
            if level == "info":
                log.info(message)
            elif level == "error":
                log.error(message)
                
        def emit_log_message(event, **context):
            log.info(event, **context)
    """)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        f.flush()

        stats, issues = analyze_file(Path(f.name))

        # Should detect both wrapper issues
        wrapper_issues = [issue for issue in issues if issue.category == "wrapper"]
        assert len(wrapper_issues) == 2
        wrapper_names = {issue.event_name for issue in wrapper_issues}
        assert "write_log_entry" in wrapper_names
        assert "emit_log_message" in wrapper_names


def test_wrapper_detection_ignores_good_patterns():
    """Test that good logging patterns are not flagged as wrappers."""
    code = textwrap.dedent("""
        import structlog
        log = structlog.get_logger()
        
        def process_user_data(user_id, data):
            # Validate data
            if not data:
                log.error("user-data-validation-failed", user_id=user_id)
                return False
            
            # Process data (real business logic)
            processed = data.upper()
            
            # Log success
            log.info("user-data-processed", user_id=user_id, length=len(processed))
            return processed
            
        def handle_request(request):
            log.debug("request-received", method=request.method)
            
            # Authentication logic
            if not authenticate(request):
                log.warning("authentication-failed")
                return None
            
            # Business logic
            result = process_request(request)
            log.info("request-completed", status="success")
            return result
            
        def authenticate(request):
            return True
            
        def process_request(request):
            return "processed"
    """)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        f.flush()

        stats, issues = analyze_file(Path(f.name))

        # Should not detect any wrapper issues
        wrapper_issues = [issue for issue in issues if issue.category == "wrapper"]
        assert len(wrapper_issues) == 0


def test_wrapper_detection_ignores_short_functions():
    """Test that very short functions are not flagged as wrappers."""
    code = textwrap.dedent("""
        import structlog
        log = structlog.get_logger()
        
        def log_startup():
            log.info("application-started")
    """)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        f.flush()

        stats, issues = analyze_file(Path(f.name))

        # Should not detect wrapper issues for very short functions
        wrapper_issues = [issue for issue in issues if issue.category == "wrapper"]
        assert len(wrapper_issues) == 0


def test_wrapper_detection_ignores_special_methods():
    """Test that special methods and common function names are ignored."""
    code = textwrap.dedent("""
        import structlog
        log = structlog.get_logger()
        
        class MyClass:
            def __init__(self):
                log.info("instance-created")
                
            def __str__(self):
                log.debug("string-representation-requested")
                return "MyClass"
                
            def main(self):
                log.info("main-method-called")
                
            def test_something(self):
                log.debug("test-method-called")
    """)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        f.flush()

        stats, issues = analyze_file(Path(f.name))

        # Should not detect wrapper issues for special methods
        wrapper_issues = [issue for issue in issues if issue.category == "wrapper"]
        assert len(wrapper_issues) == 0


def test_wrapper_issue_properties():
    """Test that wrapper issues have correct properties."""
    code = textwrap.dedent("""
        import structlog
        log = structlog.get_logger()
        
        def log_info(message):
            log.info(message)
    """)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        f.flush()

        stats, issues = analyze_file(Path(f.name))

        wrapper_issues = [issue for issue in issues if issue.category == "wrapper"]
        assert len(wrapper_issues) == 1

        issue = wrapper_issues[0]
        assert issue.category == "wrapper"
        assert issue.severity == "warning"
        assert issue.current_level == "wrapper"
        assert issue.suggested_level == "direct"
        assert issue.line_no == 5  # Line where function is defined
