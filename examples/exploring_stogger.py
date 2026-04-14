# ruff: noqa: T201, S108
"""Exploring stogger — a self-discovering tutorial through the public API.

This script discovers and demonstrates stogger's features using ONLY runtime
introspection: dir(), help(), __doc__ strings, importlib.resources, and actual
code execution. No source code was consulted.

Run with: python examples/exploring_stogger.py
"""

import os

# systemd sets JOURNAL_STREAM which suppresses console output.
# Remove it so this tutorial always produces visible console logs.
os.environ.pop("JOURNAL_STREAM", None)

import contextlib
import importlib.resources
import inspect
import shutil
import tempfile
from pathlib import Path

# =============================================================================
# 1. What is stogger?
# =============================================================================
print("=" * 72)
print("  EXPLORING STOGGER — A Self-Discovering Tutorial")
print("=" * 72)
print()

import stogger

print("Module docstring:")
print(stogger.__doc__)
print()

# The docstring mentions embedded documentation. Let's follow those hints.
pkg = importlib.resources.files(stogger)
print(f"Package location: {pkg}")

# __docs_path__ is a special attribute that points to the docs directory.
docs_path = getattr(stogger, "__docs_path__", None)
print(f"__docs_path__: {docs_path}")
print()

# Read llms.txt — the machine-readable documentation index.
llms_path = pkg / "llms.txt"
if llms_path.is_file():
    content = llms_path.read_text(encoding="utf-8")
    print(f"Found embedded docs index: llms.txt ({len(content)} chars)")
    # Show the first few entries as a table of contents.
    entries = [line.strip() for line in content.split("\n") if line.strip().startswith("- [")]
    print(f"  Documentation entries: {len(entries)}")
    for entry in entries[:8]:
        print(f"    {entry}")
    if len(entries) > 8:
        print(f"    ... and {len(entries) - 8} more")
else:
    print("llms.txt not found in package.")
print()

# =============================================================================
# 2. Public API surface
# =============================================================================
print("-" * 72)
print("  SECTION: Public API Surface")
print("-" * 72)
print()

print("Everything stogger exports via __all__:")
for name in stogger.__all__:
    obj = getattr(stogger, name)
    kind = type(obj).__name__
    sig = ""
    if (callable(obj) and not isinstance(obj, type)) or isinstance(obj, type):
        with contextlib.suppress(ValueError, TypeError):
            sig = str(inspect.signature(obj))
    print(f"  {name:35s} {kind:10s} {sig}")
print()

# =============================================================================
# 3. StoggerConfig — flexible configuration
# =============================================================================
print("-" * 72)
print("  SECTION: StoggerConfig — Configuration")
print("-" * 72)
print()

print(
    "StoggerConfig loads settings from [tool.stogger] in pyproject.toml and "
    "merges them with keyword arguments. Here are the defaults:"
)
print()

config = stogger.StoggerConfig()
for attr in sorted(dir(config)):
    if attr.startswith("_"):
        continue
    value = getattr(config, attr)
    if callable(value):
        continue
    print(f"  {attr:30s} = {value!r}")
print()

print("Override any setting via kwargs:")
custom_cfg = stogger.StoggerConfig(
    logdir="/tmp/my_logs",
    log_to_console=True,
    verbose=False,
    enable_pii_scrubbing=True,
)
print(f"  custom_cfg.logdir               = {custom_cfg.logdir}")
print(f"  custom_cfg.enable_pii_scrubbing = {custom_cfg.enable_pii_scrubbing}")
print(f"  custom_cfg.verbose              = {custom_cfg.verbose}")
print()

# =============================================================================
# 4. Initializing logging
# =============================================================================
print("-" * 72)
print("  SECTION: Initializing Logging")
print("-" * 72)
print()

print("stogger.init_logging() configures structlog with sensible defaults.")
sig = inspect.signature(stogger.init_logging)
print(f"  Signature: init_logging{sig}")
print()

print("Docstring:")
print(f"  {stogger.init_logging.__doc__}")
print()

print("Calling init_logging() with defaults (console output):")
stogger.init_logging()
print()

# After init_logging, loggers come from structlog (stogger wraps structlog).
import structlog

log = structlog.get_logger()
print(f"Logger type: {type(log).__name__}")
print("Logger methods: bind, new, unbind, try_unbind")
print("Log levels:     debug, info, warning, error, critical, exception")
print()

print(f"logging_initialized() confirms the system is ready: {stogger.logging_initialized()}")
print()

# =============================================================================
# 5. Basic logging with structured data
# =============================================================================
print("-" * 72)
print("  SECTION: Basic Logging")
print("-" * 72)
print()

print(
    "stogger uses structlog's key-value style. Every log call accepts a "
    "message as the first positional argument plus arbitrary keyword arguments "
    "that become structured data in the output."
)
print()

print(">>> log.info('hello-world')")
log.info("hello-world")
print()

print(">>> log.info('user-login', user_id=123, action='login', ip='10.0.0.1')")
log.info("user-login", user_id=123, action="login", ip="10.0.0.1")
print()

# =============================================================================
# 6. The _replace_msg feature — human-readable messages
# =============================================================================
print("-" * 72)
print("  SECTION: _replace_msg — Human-Readable Messages")
print("-" * 72)
print()

print(
    "stogger supports a special _replace_msg keyword argument. When provided, "
    "it formats a human-readable message using Python string formatting with "
    "the other keyword arguments as variables. This is the recommended pattern "
    "for user-facing log output."
)
print()

print("Without _replace_msg (event name shown):")
print(">>> log.info('order-created', order_id=12345, customer_id=67890)")
log.info("order-created", order_id=12345, customer_id=67890)
print()

print("With _replace_msg (formatted message shown):")
print(
    ">>> log.info('order-created', "
    "_replace_msg='Order {order_id} created for customer {customer_id}', "
    "order_id=12345, customer_id=67890)"
)
log.info(
    "order-created",
    _replace_msg="Order {order_id} created for customer {customer_id}",
    order_id=12345,
    customer_id=67890,
)
print()

print("The event name is the structured key; _replace_msg is the display text.")
print()

# =============================================================================
# 7. Log levels
# =============================================================================
print("-" * 72)
print("  SECTION: Log Levels")
print("-" * 72)
print()

print("stogger supports the standard log levels through structlog:")
print()

for level in ("debug", "info", "warning", "error", "critical"):
    method = getattr(log, level)
    print(f">>> log.{level}('this-is-a-{level}-event')")
    method(f"this-is-a-{level}-event")
    print()

# =============================================================================
# 8. Bound loggers — persistent context
# =============================================================================
print("-" * 72)
print("  SECTION: Bound Loggers (Context via bind)")
print("-" * 72)
print()

print(
    "bind() creates a new logger that automatically includes the given "
    "key-value pairs in every subsequent log call. Perfect for attaching "
    "request IDs, user info, or component names."
)
print()

request_log = log.bind(request_id="req-abc123", user_id="user-456")
print(">>> request_log = log.bind(request_id='req-abc123', user_id='user-456')")
print(">>> request_log.info('processing-request')")
request_log.info("processing-request")
print()

print(">>> request_log.warning('rate-limit-approaching', remaining=3)")
request_log.warning("rate-limit-approaching", remaining=3)
print()

print("Context is cumulative — bind more values to an already-bound logger:")
deeper = request_log.bind(step="validation")
print(">>> deeper = request_log.bind(step='validation')")
print(">>> deeper.info('validating-input')")
deeper.info("validating-input")
print()

# =============================================================================
# 9. new() — fresh context
# =============================================================================
print("-" * 72)
print("  SECTION: new() — Fresh Context")
print("-" * 72)
print()

print("new() clears existing context and starts fresh, unlike bind() which inherits the parent's bound context.")
print()

print(">>> fresh_log = log.new(session_id='sess-789')")
print(">>> fresh_log.info('new-session-started')")
fresh_log = log.new(session_id="sess-789")
fresh_log.info("new-session-started")
print()

# =============================================================================
# 10. unbind() and try_unbind()
# =============================================================================
print("-" * 72)
print("  SECTION: unbind() / try_unbind()")
print("-" * 72)
print()

print(
    "unbind(*keys) removes specific keys from the bound context. "
    "try_unbind(*keys) does the same but silently ignores keys that don't "
    "exist (no KeyError)."
)
print()

bound = log.bind(a=1, b=2, c=3)
print(">>> bound = log.bind(a=1, b=2, c=3)")
print(">>> bound.info('has-a-b-c')")
bound.info("has-a-b-c")
print()

print(">>> unbound = bound.unbind('b')")
print(">>> unbound.info('b-removed')")
unbound = bound.unbind("b")
unbound.info("b-removed")
print()

print(">>> try_unbound = bound.try_unbind('a', 'nonexistent')")
print(">>> try_unbound.info('a-removed-nonexistent-ignored')")
try_unbound = bound.try_unbind("a", "nonexistent")
try_unbound.info("a-removed-nonexistent-ignored")
print()

# =============================================================================
# 11. Exception logging
# =============================================================================
print("-" * 72)
print("  SECTION: Logging Exceptions")
print("-" * 72)
print()

print("log.exception() automatically captures the current exception traceback. Call it from within an except block.")
print()

print(">>> try:")
print("...     result = 1 / 0")
print("... except ZeroDivisionError:")
print("...     log.exception('division-failed', operation='divide')")
try:
    _ = 1 / 0
except ZeroDivisionError:
    log.exception("division-failed", operation="divide")
print()

print("With bound context, exceptions carry even more diagnostic info:")
service_log = log.bind(service="payment-gateway", version="2.1.0")
print(">>> service_log = log.bind(service='payment-gateway', version='2.1.0')")
print(">>> try:")
print("...     raise ConnectionError('Gateway timeout')")
print("... except ConnectionError:")
print("...     service_log.exception('payment-failed', amount=49.99)")
_err = ConnectionError("Gateway timeout")
try:
    raise _err
except ConnectionError:
    service_log.exception("payment-failed", amount=49.99)
print()

# =============================================================================
# 12. File logging
# =============================================================================
print("-" * 72)
print("  SECTION: File Logging")
print("-" * 72)
print()

print(
    "Pass logdir= to init_logging() to also write logs to a file. "
    "The file is named {syslog_identifier}.log (default: stogger.log) "
    "inside the given directory."
)
print()

tmpdir = tempfile.mkdtemp(prefix="stogger_tutorial_")
print(f"Re-initializing with logdir={tmpdir}")
stogger.init_logging(logdir=tmpdir, log_to_console=True)
file_log = structlog.get_logger()

print(">>> file_log.info('this-goes-to-file-and-console', dest='both')")
file_log.info("this-goes-to-file-and-console", dest="both")
print()

logfile = Path(tmpdir) / "stogger.log"
if logfile.exists():
    print(f"Contents of {logfile.name}:")
    for line in logfile.read_text().strip().split("\n"):
        print(f"  {line}")
else:
    print("  (log file not yet created)")
print()

# =============================================================================
# 13. PII scrubbing
# =============================================================================
print("-" * 72)
print("  SECTION: PII Scrubbing")
print("-" * 72)
print()

print(
    "stogger ships with a built-in PII (Personally Identifiable Information) "
    "scrubber that detects and redacts sensitive data from log output. "
    "The scrubber is callable, so it can be used directly as a structlog "
    "processor."
)
print()

print("Create a scrubber with default patterns:")
scrubber = stogger.create_pii_processor()
print(f"  Type: {type(scrubber).__name__}")
print(f"  Built-in pattern types: {', '.join(scrubber.patterns.keys())}")
print(f"  Sensitive field names:  {len(scrubber.sensitive_fields)} fields")
print(f"  Callable as structlog processor: {callable(scrubber)}")
print()

print("Scrubbing strings — emails, SSNs, phone numbers, credit cards:")
test_inputs = [
    "Contact: user@example.com",
    "SSN: 123-45-6789",
    "Phone: +1-555-123-4567",
    "Card: 4532-1234-5678-9012",
    "Normal text is untouched",
]
for text in test_inputs:
    scrubbed = scrubber.scrub_string(text)
    print(f"  IN:  {text}")
    print(f"  OUT: {scrubbed}")
print()

print("Scrubbing dictionaries — sensitive field names trigger redaction:")
data = {
    "username": "alice",
    "password": "hunter2",
    "email": "alice@example.com",
    "action": "login",
}
print(f"  IN:  {data}")
print(f"  OUT: {scrubber.scrub_dict(data)}")
print()

print("Custom patterns — add your own regex patterns and sensitive fields:")
custom_scrubber = stogger.create_pii_processor(
    custom_patterns={"project_code": r"PRJ-\d{4}", "employee_id": r"EMP-\d{6}"},
    sensitive_fields=["internal_id"],
    redaction_text="[CENSORED]",
)
result = custom_scrubber.scrub_string("Project PRJ-1234 assigned to EMP-987654")
print(f"  Custom patterns: {list(custom_scrubber.patterns.keys())}")
print(f"  Redaction text:  {custom_scrubber.redaction_text!r}")
print(f"  Scrubbed:        {result}")
print()

print(
    "As a structlog processor, the scrubber receives the event dict and "
    "returns a scrubbed version — plug it into the processor chain:"
)
event = {"event": "login", "email": "bob@corp.com", "token": "abc123"}
print(f"  IN:  {event}")
print(f"  OUT: {scrubber.scrub_event_dict(event)}")
print()

# =============================================================================
# 14. Internationalization (i18n)
# =============================================================================
print("-" * 72)
print("  SECTION: Internationalization (i18n)")
print("-" * 72)
print()

print("stogger has built-in i18n support with a translator class.")
print()

print("init_i18n(language='en') initializes a translator:")
try:
    translator = stogger.init_i18n(language="en")
    print(f"  Type: {type(translator).__name__}")
    print(f"  Language: {translator.language}")
    print(f"  Methods: {', '.join(m for m in dir(translator) if not m.startswith('_'))}")
    print()

    print(
        "t(key, section, **kwargs) is the translation shorthand. "
        "Without translation files installed, it falls back to "
        "'section.key' format:"
    )
    print(f"  t('success') = {stogger.t('success')!r}")
    print(f"  t('error') = {stogger.t('error')!r}")
    print()

    print("get_translator() returns the current translator instance:")
    current = stogger.get_translator()
    print(f"  Type: {type(current).__name__}")
except Exception as e:
    print(f"  (i18n not fully configured in this environment: {e})")
print()

# =============================================================================
# 15. Austrian dialect helpers
# =============================================================================
print("-" * 72)
print("  SECTION: Austrian Dialect Helpers")
print("-" * 72)
print()

print("stogger ships with three fun Austrian dialect functions:")
print()

print(">>> stogger.oida('hello')")
print(f"    {stogger.oida('hello')!r}")
print("    'oida' is a versatile Austrian interjection (roughly 'dude!')")
print()

print(">>> stogger.arsch('this is bad')")
print(f"    {stogger.arsch('this is bad')!r}")
print("    'arsch' marks something as bad, Austrian-style")
print()

print(">>> stogger.leiwand('this is great')")
print(f"    {stogger.leiwand('this is great')!r}")
print("    'leiwand' means awesome/solid in Austrian slang")
print()

# =============================================================================
# 16. Early logging and command logging
# =============================================================================
print("-" * 72)
print("  SECTION: Early Logging & Command Logging")
print("-" * 72)
print()

print(
    "init_early_logging() sets up a minimal structlog configuration early "
    "in startup to avoid raw dict-style messages before full init."
)
stogger.init_early_logging()
print("  init_early_logging() succeeded (no-op if already configured)")
print()

print("logging_initialized() — check if logging has been configured:")
print(f"  Result: {stogger.logging_initialized()}")
print()

print(
    "init_command_logging(log, logdir=...) adds a separate file logger for "
    "command output (e.g., Nix builds). It creates unique filenames when "
    "running under systemd (detected via INVOCATION_ID env var)."
)
print()

print(
    "drop_cmd_output_logfile(log) deletes the command output log file — "
    "useful to discard logs when nothing interesting happened."
)
print()

# =============================================================================
# 17. Internal architecture classes
# =============================================================================
print("-" * 72)
print("  SECTION: Internal Architecture Classes")
print("-" * 72)
print()

print("stogger exposes several classes that power its multi-target pipeline:")
print()

doc = stogger.JournalLoggerFactory.__doc__
print("JournalLoggerFactory:")
print(f"  {doc.strip().split(chr(10))[0] if doc else 'No docstring'}")
print()

doc = stogger.SystemdJournalRenderer.__doc__
print("SystemdJournalRenderer:")
print(f"  {doc.strip().split(chr(10))[0] if doc else 'No docstring'}")
print()

doc = stogger.MultiOptimisticLogger.__doc__
print("MultiOptimisticLogger:")
print(f"  {doc.strip().split(chr(10))[0] if doc else 'No docstring'}")
print()

doc = stogger.MultiOptimisticLoggerFactory.__doc__
print("MultiOptimisticLoggerFactory:")
print(f"  {doc.strip().split(chr(10))[0] if doc else 'No docstring'}")
print()

# =============================================================================
# 18. Embedded documentation discovery
# =============================================================================
print("-" * 72)
print("  SECTION: Embedded Documentation")
print("-" * 72)
print()

print(
    "The package ships with _sources/ containing full Sphinx documentation "
    "source files, and llms-full.txt with all docs in one file. "
    "Accessible via importlib.resources:"
)

sources_dir = pkg / "_sources"
try:
    items = sorted(p.name for p in sources_dir.iterdir())
    print(f"  _sources/ top-level: {', '.join(items)}")
except OSError:
    print("  (could not list _sources directory)")

for subdir in ("user_guide", "api_guides", "features"):
    sub = sources_dir / subdir
    try:
        guides = sorted(p.name for p in sub.iterdir())
        print(f"  {subdir}/: {len(guides)} files")
    except OSError:
        pass

llms_full = pkg / "llms-full.txt"
try:
    if llms_full.is_file():
        size = len(llms_full.read_text(encoding="utf-8"))
        print(f"  llms-full.txt: {size} chars (all docs in one file)")
except OSError:
    pass
print()

# =============================================================================
# Cleanup
# =============================================================================
shutil.rmtree(tmpdir, ignore_errors=True)

# =============================================================================
# Wrap-up
# =============================================================================
print("=" * 72)
print("  TOUR COMPLETE")
print("=" * 72)
print()
print("Key takeaways:")
print("  1. stogger.init_logging() configures everything — call it once")
print("  2. Get loggers via structlog.get_logger() (stogger wraps structlog)")
print("  3. Use .bind() to attach persistent context to loggers")
print("  4. Use _replace_msg='...' for human-readable formatted messages")
print("  5. log.exception() captures tracebacks from within except blocks")
print("  6. File logging activates by passing logdir= to init_logging()")
print("  7. PII scrubbing is built-in and extensible with custom patterns")
print("  8. StoggerConfig reads from pyproject.toml + kwargs for flexible setup")
print("  9. Austrian dialect functions (oida, arsch, leiwand) add personality")
print(" 10. Embedded docs at _sources/ and llms.txt provide full reference")
print()
print("Discovered entirely through public API introspection and embedded docs")
print("— no source code or external documentation was consulted.")
