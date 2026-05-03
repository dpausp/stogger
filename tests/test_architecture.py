"""Architecture enforcement rules for stogger package.

Validates the layer boundary rules of the dependency graph:

    config.py ← (no internal deps)
    _types.py ← (no internal deps)
    _colors.py ← (no internal deps)
    _regexes.py ← (no internal deps)
    processors.py ← config.py
    core.py ← config.py, _types.py, processors.py, _colors.py
    factory.py ← config.py, core.py, processors.py
    __init__.py ← config.py, core.py (top-level aggregation)
"""

from pytest_archon import archrule

# --- Layer 0: Foundation modules (no internal deps) ---

archrule("config has no internal deps", comment="config is the deepest layer").match(
    "stogger.config"
).should_not_import("stogger")

archrule("_types has no internal deps").match("stogger._types").should_not_import("stogger")

archrule("_colors has no internal deps").match("stogger._colors").should_not_import("stogger")

archrule("_regexes has no internal deps").match("stogger._regexes").should_not_import("stogger")

# --- Layer 1: processors (depends only on config) ---

archrule("processors depends only on config").match("stogger.processors").should_not_import(
    "stogger.core", "stogger.factory", "stogger._types", "stogger._colors", "stogger._regexes"
)

# --- Layer 2: core (depends on config, _types, processors, _colors — NOT factory) ---

archrule("core does not import factory").match("stogger.core").should_not_import("stogger.factory")

archrule("core does not import __init__").match("stogger.core").should_not_import("stogger")

# --- Layer 3: factory (depends on config, core, processors — NOT __init__) ---

archrule("factory does not import __init__").match("stogger.factory").should_not_import("stogger")

# --- Top level: __init__ (aggregation only, does not import factory internals) ---

archrule("__init__ does not import processors").match("stogger.__init__").should_not_import(
    "stogger.processors"
)
