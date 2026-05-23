"""Architecture enforcement rules for stogger package.

Validates the layer boundary rules of the dependency graph:

    config.py ← (no internal deps)
    _types.py ← (no internal deps)
    _colors.py ← (no internal deps)
    processors.py ← config.py
    core.py ← config.py, _types.py, processors.py, _colors.py
    factory.py ← config.py, core.py, processors.py
    __init__.py ← config.py, core.py (top-level aggregation)
"""

from pytest_archon import archrule

PACKAGE = "stogger"


# --- Layer 0: Foundation modules (no internal deps) ---


def test_config_has_no_internal_deps():
    archrule("config has no internal deps", comment="config is the deepest layer").match(
        "stogger.config"
    ).should_not_import("stogger").check(PACKAGE)


def test_types_has_no_internal_deps():
    archrule("_types has no internal deps").match("stogger._types").should_not_import("stogger").check(PACKAGE)


def test_colors_has_no_internal_deps():
    archrule("_colors has no internal deps").match("stogger._colors").should_not_import("stogger").check(PACKAGE)


# --- Layer 1: processors (depends only on config) ---


def test_processors_depends_only_on_config():
    archrule("processors depends only on config").match("stogger.processors").should_not_import(
        "stogger.core", "stogger.factory", "stogger._types", "stogger._colors"
    ).check(PACKAGE)


# --- Layer 2: core (depends on config, _types, processors, _colors — NOT factory) ---


def test_core_does_not_import_factory():
    archrule("core does not import factory").match("stogger.core").should_not_import("stogger.factory").check(
        PACKAGE
    )


def test_core_does_not_import_init():
    archrule("core does not import __init__").match("stogger.core").should_not_import("stogger").check(PACKAGE)


# --- Layer 3: factory (depends on config, core, processors — NOT __init__) ---


def test_factory_does_not_import_init():
    archrule("factory does not import __init__").match("stogger.factory").should_not_import("stogger").check(
        PACKAGE
    )


# --- Top level: __init__ (aggregation only, does not import factory internals) ---


def test_init_does_not_import_processors():
    archrule("__init__ does not directly import processors").match("stogger").exclude("stogger.*").should_not_import(
        "stogger.processors"
    ).check(PACKAGE, only_direct_imports=True)


# --- Layer 2: decorators (depends on _types, config — NOT factory or __init__) ---


def test_decorators_does_not_import_factory():
    archrule("decorators does not import factory").match("stogger.decorators").should_not_import(
        "stogger.factory"
    ).check(PACKAGE)


def test_decorators_does_not_import_init():
    archrule("decorators does not import __init__").match("stogger.decorators").should_not_import(
        "stogger"
    ).check(PACKAGE)
