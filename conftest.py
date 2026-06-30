"""Project-level pytest configuration."""

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Derive infrastructure_files from per-file-ignores for pytest-stogger.

    The pytest-stogger plugin hardcodes ``infrastructure_files`` as the config key
    for excluding files from ``except-must-log`` and ``complexity-needs-log`` rules.
    We derive it from ``per-file-ignores`` so there is a single source of truth.
    """
    try:
        from pytest_stogger.plugin import _CFG_KEY, _load_config  # noqa: PLC0415
    except ImportError:
        return

    cfg = _load_config(config.rootpath / "pyproject.toml")
    pfi = cfg.get("per-file-ignores", {})
    infra = [
        filename for filename, rules in pfi.items() if "except-must-log" in rules and "complexity-needs-log" in rules
    ]
    if infra:
        cfg.setdefault("infrastructure_files", infra)
    config.stash[_CFG_KEY] = cfg
