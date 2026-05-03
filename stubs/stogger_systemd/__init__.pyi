from typing import Any

class JournalLogger:
    syslog_identifier: str
    syslog_facility: int

    def __init__(
        self,
        syslog_identifier: str = ...,
        syslog_facility: int = ...,
    ) -> None: ...
    def msg(self, messages: dict[str, Any]) -> None: ...

class DummyJournalLogger:
    def msg(self, messages: dict[str, Any]) -> None: ...

class JournalLoggerFactory:
    def __call__(self) -> JournalLogger | DummyJournalLogger: ...

def get_journal_logger_factory() -> JournalLoggerFactory: ...
