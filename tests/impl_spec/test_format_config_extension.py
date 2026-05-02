"""Spec validation tests for format-config-extension.

These tests define the CONTRACT that format-config-extension implementation
must fulfill. All tests are marked xfail because the feature doesn't exist yet.
They will be garbage-collected after implementation makes them green.

Spec: .agents/impl_specs/format-config-extension.md

Decision coverage:
  - config-layer-attrs: StoggerConfig attrs, FormatConfig nested, no SimpleFormatSettings
  - format-config-fields: FormatConfig has 4 fields with correct defaults
  - timestamp-precision-values: build_timestamp_processor maps precision→fmt
  - pipeline-approach: ConsoleFileRenderer._format_timestamp handles all 4 formats
  - call-site-unification: single factory function, all utc=True
  - test-strategy: TOML loading + GIGO behavior
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import structlog


# ---------------------------------------------------------------------------
# config-layer-attrs: StoggerConfig uses attrs, FormatConfig is nested attrs,
# SimpleFormatSettings no longer exists
# ---------------------------------------------------------------------------


def test_stogger_config_is_attrs_class():
    """StoggerConfig must be an attrs class (has __attrs_attrs__)."""
    import attrs

    from stogger.config import StoggerConfig

    assert attrs.has(StoggerConfig)


def test_format_config_is_attrs_class():
    """FormatConfig must be an attrs class."""
    import attrs

    from stogger.config import FormatConfig

    assert attrs.has(FormatConfig)


def test_stogger_config_has_format_attr():
    """StoggerConfig must have a .format attribute of type FormatConfig."""
    from stogger.config import FormatConfig, StoggerConfig

    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("pathlib.Path.cwd", return_value=Path(tmpdir), autospec=True):
            config = StoggerConfig()
    assert isinstance(config.format, FormatConfig)


def test_simple_format_settings_removed():
    """SimpleFormatSettings must no longer exist in stogger.config."""
    import stogger.config

    assert not hasattr(stogger.config, "SimpleFormatSettings")


def test_default_simple_format_settings_removed():
    """_default_simple_format_settings must no longer exist."""
    import stogger.config

    assert not hasattr(stogger.config, "_default_simple_format_settings")


# ---------------------------------------------------------------------------
# format-config-fields: FormatConfig has exactly 4 fields with correct defaults
# ---------------------------------------------------------------------------


def test_format_config_has_four_fields():
    """FormatConfig must have exactly 4 fields."""
    import attrs

    from stogger.config import FormatConfig

    fields = {a.name for a in attrs.fields(FormatConfig)}
    assert fields == {"timestamp_precision", "min_level", "show_code_info", "pad_event_width"}


def test_format_config_default_timestamp_precision():
    """FormatConfig.timestamp_precision defaults to 'iso_seconds'."""
    from stogger.config import FormatConfig

    fc = FormatConfig()
    assert fc.timestamp_precision == "iso_seconds"


def test_format_config_default_min_level():
    """FormatConfig.min_level defaults to 'info'."""
    from stogger.config import FormatConfig

    fc = FormatConfig()
    assert fc.min_level == "info"


def test_format_config_default_show_code_info():
    """FormatConfig.show_code_info defaults to False."""
    from stogger.config import FormatConfig

    fc = FormatConfig()
    assert fc.show_code_info is False


def test_format_config_default_pad_event_width():
    """FormatConfig.pad_event_width defaults to 30."""
    from stogger.config import FormatConfig

    fc = FormatConfig()
    assert fc.pad_event_width == 30


# ---------------------------------------------------------------------------
# timestamp-precision-values: build_timestamp_processor maps each value to
# correct TimeStamper fmt parameter, default is iso_seconds
# ---------------------------------------------------------------------------


def test_build_timestamp_processor_exists():
    """build_timestamp_processor function must exist in stogger.factory."""
    from stogger.factory import build_timestamp_processor

    assert callable(build_timestamp_processor)


def test_build_timestamp_processor_iso():
    """timestamp_precision='iso' → TimeStamper(fmt='iso')."""
    from stogger.config import FormatConfig
    from stogger.factory import build_timestamp_processor

    config = type("Cfg", (), {"format": FormatConfig(timestamp_precision="iso")})()
    processor = build_timestamp_processor(config)
    assert processor is not None


def test_build_timestamp_processor_iso_seconds():
    """timestamp_precision='iso_seconds' → TimeStamper(fmt='%Y-%m-%dT%H:%M:%SZ')."""
    from stogger.config import FormatConfig
    from stogger.factory import build_timestamp_processor

    config = type("Cfg", (), {"format": FormatConfig(timestamp_precision="iso_seconds")})()
    processor = build_timestamp_processor(config)
    assert processor is not None


def test_build_timestamp_processor_iso_no_z():
    """timestamp_precision='iso_no_z' → TimeStamper(fmt='%Y-%m-%dT%H:%M:%S')."""
    from stogger.config import FormatConfig
    from stogger.factory import build_timestamp_processor

    config = type("Cfg", (), {"format": FormatConfig(timestamp_precision="iso_no_z")})()
    processor = build_timestamp_processor(config)
    assert processor is not None


def test_build_timestamp_processor_relative():
    """timestamp_precision='relative' → TimeStamper(fmt='iso') kept for pipeline."""
    from stogger.config import FormatConfig
    from stogger.factory import build_timestamp_processor

    config = type("Cfg", (), {"format": FormatConfig(timestamp_precision="relative")})()
    processor = build_timestamp_processor(config)
    assert processor is not None


def test_default_precision_is_iso_seconds():
    """When no [tool.stogger.format] section exists, default is iso_seconds."""
    from stogger.config import StoggerConfig

    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("pathlib.Path.cwd", return_value=Path(tmpdir), autospec=True):
            config = StoggerConfig()
    assert config.format.timestamp_precision == "iso_seconds"


# ---------------------------------------------------------------------------
# pipeline-approach: ConsoleFileRenderer._format_timestamp handles all four
# format values including relative with _process_start tracking
# ---------------------------------------------------------------------------


def test_renderer_format_timestamp_iso():
    """_format_timestamp with 'iso' precision passes ISO string through."""
    from stogger.config import FormatConfig
    from stogger.core import ConsoleFileRenderer

    fc = FormatConfig(timestamp_precision="iso")
    renderer = ConsoleFileRenderer(format_config=fc)
    result = renderer._format_timestamp("2026-05-02T12:34:56.123456Z", {})
    assert "2026-05-02T12:34:56.123456Z" in result


def test_renderer_format_timestamp_iso_seconds():
    """_format_timestamp with 'iso_seconds' passes string through."""
    from stogger.config import FormatConfig
    from stogger.core import ConsoleFileRenderer

    fc = FormatConfig(timestamp_precision="iso_seconds")
    renderer = ConsoleFileRenderer(format_config=fc)
    result = renderer._format_timestamp("2026-05-02T12:34:56Z", {})
    assert "2026-05-02T12:34:56Z" in result


def test_renderer_format_timestamp_iso_no_z():
    """_format_timestamp with 'iso_no_z' strips trailing Z."""
    from stogger.config import FormatConfig
    from stogger.core import ConsoleFileRenderer

    fc = FormatConfig(timestamp_precision="iso_no_z")
    renderer = ConsoleFileRenderer(format_config=fc)
    result = renderer._format_timestamp("2026-05-02T12:34:56Z", {})
    assert "2026-05-02T12:34:56" in result
    assert "12:34:56Z" not in result


def test_renderer_format_timestamp_relative():
    """_format_timestamp with 'relative' computes elapsed time from process start."""
    import time

    from stogger.config import FormatConfig
    from stogger.core import ConsoleFileRenderer

    fc = FormatConfig(timestamp_precision="relative")
    renderer = ConsoleFileRenderer(format_config=fc)

    # _process_start must be set at FormatConfig instantiation
    assert hasattr(fc, "_process_start")
    assert isinstance(fc._process_start, float)

    # Renderer should produce a relative timestamp like +X.XXXs
    result = renderer._format_timestamp("2026-05-02T12:34:56.123456Z", {})
    assert "+" in result
    assert "s" in result


def test_format_config_process_start_is_set():
    """FormatConfig stores _process_start at instantiation for relative timestamps."""
    import time

    from stogger.config import FormatConfig

    before = time.time()
    fc = FormatConfig()
    after = time.time()
    assert before <= fc._process_start <= after


# ---------------------------------------------------------------------------
# call-site-unification: build_timestamp_processor is single factory, all
# TimeStamper sites use utc=True
# ---------------------------------------------------------------------------


def test_no_raw_timestamper_in_factory():
    """factory.py must not contain direct TimeStamper() calls — only through build_timestamp_processor."""
    import inspect

    import stogger.factory

    source = inspect.getsource(stogger.factory)
    # After unification, no raw TimeStamper instantiation should remain
    assert "TimeStamper(" not in source or "build_timestamp_processor" in source.split("TimeStamper(")[0]


def test_no_raw_timestamper_in_core():
    """core.py must not contain direct TimeStamper() calls — only through build_timestamp_processor."""
    import inspect

    import stogger.core

    source = inspect.getsource(stogger.core)
    assert "TimeStamper(" not in source


def test_init_logging_uses_utc_true():
    """init_logging (formerly utc=False) must now use utc=True."""
    import inspect

    import stogger.core

    source = inspect.getsource(stogger.core.init_logging)
    assert "utc=False" not in source
    # build_timestamp_processor guarantees utc=True
    assert "build_timestamp_processor" in source or "utc=True" in source


# ---------------------------------------------------------------------------
# test-strategy: TOML loading of [tool.stogger.format] section + GIGO
# ---------------------------------------------------------------------------


def test_toml_format_section_loading():
    """[tool.stogger.format] TOML section loads into FormatConfig fields."""
    from stogger.config import StoggerConfig

    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir)
        pyproject_path = config_dir / "pyproject.toml"
        pyproject_path.write_text(
            "[tool.stogger]\n"
            "[tool.stogger.format]\n"
            'timestamp_precision = "iso"\n'
            'min_level = "debug"\n'
            "pad_event_width = 40\n"
        )
        with patch("pathlib.Path.cwd", return_value=config_dir, autospec=True):
            config = StoggerConfig()

    assert config.format.timestamp_precision == "iso"
    assert config.format.min_level == "debug"
    assert config.format.show_code_info is False
    assert config.format.pad_event_width == 40


def test_toml_format_section_partial():
    """Partial [tool.stogger.format] loads specified fields, rest defaults."""
    from stogger.config import StoggerConfig

    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir)
        pyproject_path = config_dir / "pyproject.toml"
        pyproject_path.write_text('[tool.stogger]\n[tool.stogger.format]\ntimestamp_precision = "relative"\n')
        with patch("pathlib.Path.cwd", return_value=config_dir, autospec=True):
            config = StoggerConfig()

    assert config.format.timestamp_precision == "relative"
    assert config.format.min_level == "info"  # default
    assert config.format.show_code_info is False  # default
    assert config.format.pad_event_width == 30  # default


def test_gigo_invalid_timestamp_precision():
    """Invalid timestamp_precision value produces output without crash (GIGO)."""
    from stogger.config import FormatConfig
    from stogger.factory import build_timestamp_processor

    fc = FormatConfig(timestamp_precision="not_a_real_format")
    config = type("Cfg", (), {"format": fc})()
    # Must not raise — GIGO
    processor = build_timestamp_processor(config)
    assert processor is not None


def test_toml_format_section_absent_defaults():
    """No [tool.stogger.format] section → all FormatConfig defaults used."""
    from stogger.config import StoggerConfig

    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir)
        pyproject_path = config_dir / "pyproject.toml"
        pyproject_path.write_text("[tool.stogger]\nverbose = true\n")
        with patch("pathlib.Path.cwd", return_value=config_dir, autospec=True):
            config = StoggerConfig()

    assert config.format.timestamp_precision == "iso_seconds"
    assert config.format.min_level == "info"
    assert config.format.show_code_info is False
    assert config.format.pad_event_width == 30


@pytest.fixture(autouse=True)
def _reset_structlog():
    """Reset structlog configuration after each test to avoid state leakage."""
    yield
    structlog.reset_defaults()
