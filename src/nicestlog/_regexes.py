from __future__ import annotations

import re

# Shared regexes for scanning source code
# Event with _replace_msg in same call, any log level
EVENT_WITH_REPLACE = re.compile(
    r"\.[a-zA-Z_][a-zA-Z0-9_]*\(\s*([\'\"])(?P<event>[^'\"]+)\1\s*(?P<rest>[^\)]*?_replace_msg\s*=)",
    re.DOTALL,
)

# Explicit _msg_key assignment anywhere in call
MSG_KEY = re.compile(r"_msg_key\s*=\s*([\'\"])(?P<key>.+?)\1")

# .info("event" ...)
INFO_EVENT = re.compile(r"\.info\(\s*([\'\"])(?P<event>[^'\"]+)\1", re.DOTALL)

# .debug("event" ...) with _replace_msg in args
DEBUG_WITH_REPLACE = re.compile(
    r"\.debug\(\s*([\'\"])(?P<event>.+?)\1(?P<rest>[^\)]*?_replace_msg\s*=)",
    re.DOTALL,
)
