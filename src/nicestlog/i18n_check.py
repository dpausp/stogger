"""
Utilities to check completeness of nicestlog i18n translation files.

This scans Python source files for usages of `_replace_msg` and `_msg_key`
within structlog logger calls and verifies that the translation file contains
entries for all detected message keys.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Set, Tuple, Dict, List
import re
import sys

try:
    import toml
except Exception:  # pragma: no cover - handled by CLI messaging
    toml = None  # type: ignore


# Regex to capture event name when a call contains _replace_msg in its args
# Matches: any_name.info("event-name", ..., _replace_msg=...)
_EVENT_WITH_REPLACE = re.compile(
    r"\.[a-zA-Z_][a-zA-Z0-9_]*\(\s*([\'\"])(?P<event>.+?)\1(?P<rest>[^\)]*?_replace_msg\s*=)",
    re.DOTALL,
)

# Regex to capture explicit _msg_key assignments
_MSG_KEY = re.compile(r"_msg_key\s*=\s*([\'\"])(?P<key>.+?)\1")

# Regex to capture .info("event") calls regardless of _replace_msg presence
_INFO_EVENT = re.compile(r"\.info\(\s*([\'\"])(?P<event>.+?)\1", re.DOTALL)


def find_required_translation_keys(paths: Iterable[Path]) -> Tuple[Set[str], Set[str]]:
    """Scan Python files for keys required by the TranslationProcessor.

    Returns:
        tuple(set(event_keys), set(msg_keys))
    """
    event_keys: Set[str] = set()
    msg_keys: Set[str] = set()

    for root in paths:
        if root.is_file() and root.suffix == ".py":
            py_files = [root]
        else:
            py_files = list(root.rglob("*.py"))

        for file in py_files:
            try:
                text = file.read_text(encoding="utf-8")
            except Exception:
                continue

            # Event names where _replace_msg is present in the same call
            for m in _EVENT_WITH_REPLACE.finditer(text):
                event_keys.add(m.group("event"))

            # Also include .info("event") calls even without _replace_msg
            for m in _INFO_EVENT.finditer(text):
                event_keys.add(m.group("event"))

            # Explicit _msg_key assignments (potentially separate)
            for m in _MSG_KEY.finditer(text):
                msg_keys.add(m.group("key"))

    return event_keys, msg_keys


def load_translation_keys(translation_file: Path) -> Set[str]:
    """Load top-level keys from a TOML translation file.

    TranslationProcessor expects a flat dict keyed by event/msg_key.
    Any top-level keys that map to non-dict values are considered message entries.
    """
    if toml is None:
        raise RuntimeError("toml package not available; install 'toml' to use i18n check")

    data = toml.load(translation_file)
    keys: Set[str] = set()
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
) -> Dict[str, object]:
    """Check translation coverage and return a report dict.

    Returns keys:
      - required_keys: set[str]
      - translation_keys: set[str]
      - missing_keys: list[str]
      - extra_keys: list[str]
      - translation_file: str
      - msg_keys_found: set[str]
    """
    event_keys, msg_keys = find_required_translation_keys(source_paths)
    required_keys = set(event_keys) | set(msg_keys)

    translation_file = translation_dir / f"{language}.toml"
    translation_keys: Set[str] = set()
    if translation_file.is_file():
        try:
            translation_keys = load_translation_keys(translation_file)
        except Exception as e:
            return {
                "error": f"Failed to load translation file: {e}",
                "translation_file": str(translation_file),
                "required_keys": sorted(required_keys),
            }
    else:
        return {
            "error": "Translation file not found",
            "translation_file": str(translation_file),
            "required_keys": sorted(required_keys),
        }

    missing = sorted(k for k in required_keys if k not in translation_keys)
    extra = sorted(k for k in translation_keys if k not in required_keys)

    return {
        "required_keys": sorted(required_keys),
        "translation_keys": sorted(translation_keys),
        "missing_keys": missing,
        "extra_keys": extra,
        "translation_file": str(translation_file),
        "msg_keys_found": sorted(msg_keys),
    }


def format_report(report: Dict[str, object]) -> str:
    if "error" in report:
        return (
            f"❌ i18n check failed: {report['error']}\n"
            f"   Translation file: {report.get('translation_file','<unknown>')}\n"
            f"   Required keys detected: {len(report.get('required_keys', []))}\n"
        )

    missing: List[str] = report.get("missing_keys", [])  # type: ignore[assignment]
    extra: List[str] = report.get("extra_keys", [])  # type: ignore[assignment]
    required_cnt = len(report.get("required_keys", []))  # type: ignore[arg-type]
    present_cnt = len(report.get("translation_keys", []))  # type: ignore[arg-type]

    lines = []
    lines.append("🌐 nicestlog i18n check")
    lines.append(f"   Translation file: {report['translation_file']}")
    lines.append(f"   Required keys: {required_cnt}")
    lines.append(f"   Present keys:  {present_cnt}")

    if missing:
        lines.append("\n❗ Missing keys:")
        for k in missing:
            lines.append(f"  - {k}")
    else:
        lines.append("\n✅ No missing keys detected.")

    if extra:
        lines.append("\nℹ️ Extra keys (not used in source):")
        for k in extra:
            lines.append(f"  - {k}")

    return "\n".join(lines)


def run_i18n_check_cli(
    path: str = ".",
    translation_dir: str = "translations",
    language: str = "en",
    strict: bool = False,
) -> int:
    """Run the i18n check and print a human-friendly report. Returns exit code."""
    source_paths = [Path(path)]
    report = check_translations(source_paths, Path(translation_dir), language)
    print(format_report(report))

    if "error" in report:
        return 2
    missing = report.get("missing_keys", [])  # type: ignore[assignment]
    if strict and missing:
        return 1
    return 0
