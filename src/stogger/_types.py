"""Type definitions for stogger processors."""

from collections.abc import MutableMapping
from typing import Any, Protocol

type EventDict = MutableMapping[str, Any]


class StructlogProcessor(Protocol):
    """Protocol for structlog processors used throughout stogger."""

    def __call__(
        self,
        logger: object,
        method_name: str,
        event_dict: EventDict,
    ) -> EventDict | None: ...
