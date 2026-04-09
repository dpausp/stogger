"""Utilities to check completeness of stogger i18n translation files.

This scans Python source files for usages of `_replace_msg` and `_msg_key`
within structlog logger calls and verifies that the translation file contains
entries for all detected message keys.
"""

import tomllib
from collections.abc import Iterable
from pathlib import Path
from typing import cast

from ._regexes import (
    DEBUG_WITH_REPLACE as _DEBUG_WITH_REPLACE,
)
from ._regexes import (
    EVENT_WITH_REPLACE as _EVENT_WITH_REPLACE,
)
from ._regexes import (
    INFO_EVENT as _INFO_EVENT,
)
from ._regexes import (
    MSG_KEY as _MSG_KEY,
)

# Excluded directories when scanning for Python files
EXCLUDE_DIRS = {
    ".venv",
    "venv",
    "__pycache__",
    ".git",
    ".tox",
    ".nox",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".direnv",
    "node_modules",
    "build",
    "dist",
    ".eggs",
}


def find_required_translation_keys(paths: Iterable[Path]) -> tuple[set[str], set[str]]:
    """Scan Python files for keys required by the TranslationProcessor.

    Returns:
        tuple(set(event_keys), set(msg_keys))

    """
    event_keys, msg_keys, _ = scan_translation_keys(paths)
    return event_keys, msg_keys


def scan_translation_keys(paths: Iterable[Path]) -> tuple[set[str], set[str], set[str]]:
    """Scan Python files for all translation-related keys in a single pass.

    This optimized function reduces IO by scanning files once and extracting
    all needed information: event keys, message keys, and debug events.

    Returns:
        tuple(set(event_keys), set(msg_keys), set(debug_events))

    """
    event_keys: set[str] = set()
    msg_keys: set[str] = set()
    debug_events: set[str] = set()

    for root in paths:
        if root.is_file() and root.suffix == ".py":
            py_files = [root]
        else:
            py_files = [p for p in root.rglob("*.py") if not any(part in EXCLUDE_DIRS for part in p.parts)]

        for file in py_files:
            try:
                text = file.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue

            # Event names where _replace_msg is present in the same call
            event_keys.update(m.group("event") for m in _EVENT_WITH_REPLACE.finditer(text))

            # Also include .info("event") calls even without _replace_msg
            event_keys.update(m.group("event") for m in _INFO_EVENT.finditer(text))

            # Explicit _msg_key assignments (potentially separate)
            msg_keys.update(m.group("key") for m in _MSG_KEY.finditer(text))

            # Debug events that use _replace_msg (should be excluded from requirements)
            debug_events.update(m.group("event") for m in _DEBUG_WITH_REPLACE.finditer(text))

    return event_keys, msg_keys, debug_events


def load_translation_keys(translation_file: Path) -> set[str]:
    """Load top-level keys from a TOML translation file.

    TranslationProcessor expects a flat dict keyed by event/msg_key.
    Any top-level keys that map to non-dict values are considered message entries.
    """
    with translation_file.open("rb") as f:
        data = tomllib.load(f)
    keys: set[str] = set()
    if isinstance(data, dict):
        for k, v in data.items():
            # Section tables are dicts; those are NOT TranslationProcessor entries
            if not isinstance(v, dict):
                keys.add(k)
    return keys


def check_translations(
    source_paths: Iterable[Path],
    translation_dir: Path,
    language: str = "en",
) -> dict[str, object]:
    """Check translation coverage and return a report dict.

    Returns keys:
      - required_keys: set[str]
      - translation_keys: set[str]
      - missing_keys: list[str]
      - missing_by_level: dict[str, list[str]]
      - extra_keys: list[str]
      - translation_file: str
      - msg_keys_found: set[str]
      - debug_with_replace_events: set[str]
    """
    # Use optimized single-pass scanning to reduce IO
    event_keys, msg_keys, debug_events = scan_translation_keys(source_paths)

    translation_file = translation_dir / f"{language}.toml"
    translation_keys: set[str] = set()
    if translation_file.is_file():
        try:
            translation_keys = load_translation_keys(translation_file)
        except (OSError, ValueError, KeyError) as e:
            return {
                "error": f"Failed to load translation file: {e}",
                "translation_file": str(translation_file),
                "required_keys": sorted(event_keys),
            }
    else:
        return {
            "error": "Translation file not found",
            "translation_file": str(translation_file),
            "required_keys": sorted(event_keys),
        }

    # Debug events are collected during the single scan pass above.
    # These are excluded from required translation coverage as nicestlog
    # does not require translations for debug-level messages.
    debug_with_replace = debug_events

    # Compute required keys: all event/info/_msg_key minus debug ones
    required_keys = (set(event_keys) | set(msg_keys)) - debug_events

    missing = sorted(k for k in required_keys if k not in translation_keys)
    extra = sorted(k for k in translation_keys if k not in required_keys)

    # Derive missing_by_level using a simple heuristic on key names
    # Group keys as INFO (default), WARNING (contains 'warn'), ERROR/CRITICAL (contains 'error'/'critical')
    def key_level(name: str) -> str:
        lower = name.lower()
        if any(x in lower for x in ["critical", "fatal"]):
            return "CRITICAL"
        if "error" in lower or "fail" in lower:
            return "ERROR"
        if "warn" in lower:
            return "WARNING"
        # default info-ish
        return "INFO"

    missing_by_level: dict[str, list[str]] = {
        "INFO": [],
        "WARNING": [],
        "ERROR": [],
        "CRITICAL": [],
    }
    for k in missing:
        missing_by_level[key_level(k)].append(k)

    return {
        "required_keys": sorted(required_keys),
        "translation_keys": sorted(translation_keys),
        "missing_keys": missing,
        "missing_by_level": {lvl: sorted(v) for lvl, v in missing_by_level.items()},
        "extra_keys": extra,
        "translation_file": str(translation_file),
        "msg_keys_found": sorted(msg_keys),
        "debug_with_replace_events": sorted(debug_with_replace),
    }


def format_report(report: dict[str, object], *, include_debug: bool = True) -> str:
    # If --list-missing is requested via env/flag, handled in CLI wrapper.
    # This function returns the pretty report.

    if "error" in report:
        return (
            f"❌ i18n check failed: {report['error']}\n"
            f"   Translation file: {report.get('translation_file', '<unknown>')}\n"
            f"   Required keys detected: {len(cast('list[str]', report.get('required_keys', [])))}\n"
        )

    missing: list[str] = report.get("missing_keys", [])  # type: ignore[assignment]
    extra: list[str] = report.get("extra_keys", [])  # type: ignore[assignment]
    required_cnt = len(report.get("required_keys", []))  # type: ignore[arg-type]
    present_cnt = len(report.get("translation_keys", []))  # type: ignore[arg-type]

    lines = []
    lines.extend(
        (
            "🌐 stogger i18n check",
            f"   Translation file: {report['translation_file']}",
            f"   Required keys: {required_cnt}",
            f"   Present keys:  {present_cnt}",
        )
    )

    if missing:
        lines.append("\n❗ Missing keys:")
        # Grouped by level for better insight
        mbl: dict[str, list[str]] = report.get("missing_by_level", {})  # type: ignore[assignment]
        for level in ["INFO", "WARNING", "ERROR", "CRITICAL"]:
            keys = mbl.get(level, []) if isinstance(mbl, dict) else []
            if not keys:
                continue
            lines.append(f"  {level}:")
            lines.extend(f"    - {k}" for k in keys)
    else:
        lines.append("\n✅ No missing keys detected.")

    if extra:
        lines.append("\ni Extra keys (not used in source):")
        lines.extend(f"  - {k}" for k in extra)

    if include_debug:
        dbg = cast("list[str]", report.get("debug_with_replace_events", []))
        if dbg:
            lines.append("\n⚠️ Debug events using _replace_msg (ignored for coverage):")
            lines.extend(f"  - {k}" for k in dbg)

    return "\n".join(lines)


def run_i18n_check_cli(
    path: str = ".",
    translation_dir: str = "translations",
    language: str = "en",
    *,
    strict: bool = False,
) -> int:
    """Run the i18n check and print a human-friendly report. Returns exit code."""
    source_paths = [Path(path)]
    report = check_translations(source_paths, Path(translation_dir), language)

    if "error" in report:
        return 2
    missing = report.get("missing_keys", [])  # type: ignore[assignment]
    if strict and missing:
        return 1
    return 0
