# Fix Annotation Breakage + Build Script

## Problem 1: pytest-stogger does not recognize em-dash annotations

The annotation pass changed 11 trailing `# stogger: ignore` comments
to `# stogger: ignore — <reason>`. pytest-stogger parses the text
after `ignore` as a rule name. The em-dash `—` is not a valid rule,
so these 11 functions are now UNSUPPRESSED.

StoggerViolationError reports 7 violations (4 except-must-log +
3 complexity-needs-log) at core.py lines 74, 196, 271, 276, 449,
912, 964.

## Fix 1

Revert the 11 trailing comments back to bare `# stogger: ignore`.
The block comments above each function (e.g.
`# stogger: ignore — structlog processor, logging here would recurse`)
already provide the rationale documentation. The trailing comment
is the functional suppression marker and must stay in the format
pytest-stogger recognizes.

Lines to revert (search for `# stogger: ignore —` at END of line,
not in block comments):
- All 11 trailing comments matching pattern `  # stogger: ignore — *`
  on def/signature lines

Replace each with bare `  # stogger: ignore`.

DO NOT touch block comments above functions (lines starting with
`    # stogger: ignore —` or `# stogger: ignore —`).

## Problem 2: build_docs_for_package.py copytree fails

`scripts/build_docs_for_package.py` line 35 calls
`shutil.copytree(sources_src, TARGET_DIR / "_sources")` without
`dirs_exist_ok=True`. When `_docs/_sources/` exists from a previous
build, this raises `File exists` error.

## Fix 2

Add `dirs_exist_ok=True` to the `shutil.copytree` call at line 35
of `scripts/build_docs_for_package.py`.

## Files to Change

- `src/stogger/core.py` — revert 11 trailing comments
- `scripts/build_docs_for_package.py` — add dirs_exist_ok=True
