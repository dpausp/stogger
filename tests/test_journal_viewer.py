"""Tests for journal_viewer module."""

import logging
import sys
from datetime import UTC, datetime, timedelta
from io import StringIO
from types import FunctionType
from unittest.mock import MagicMock, Mock, patch

from stogger.core import init_logging
from stogger_systemd.journal_viewer import JournalEntry, JournalQueryOptions, JournalViewer


class _JournalReaderStub:
    """Minimal stub matching the systemd.journal.Reader interface for spec."""

    def __iter__(self): ...
    def seek_head(self): ...
    def seek_tail(self): ...
    def get_previous(self, n): ...
    def add_match(self, *args, **kwargs): ...
    def seek_realtime(self, time): ...
    def wait(self): ...


class TestJournalEntry:
    """Test the JournalEntry dataclass."""

    def test_journal_entry_creation(self):
        """Test creating a JournalEntry."""
        timestamp = datetime.now()
        fields = {"key": "value"}
        raw_entry = {"MESSAGE": "test"}

        entry = JournalEntry(
            timestamp=timestamp,
            hostname="testhost",
            service="testservice",
            pid="1234",
            level="info",
            message="test message",
            fields=fields,
            raw_entry=raw_entry,
        )

        assert entry.timestamp == timestamp
        assert entry.hostname == "testhost"
        assert entry.service == "testservice"
        assert entry.pid == "1234"
        assert entry.level == "info"
        assert entry.message == "test message"
        assert entry.fields == fields
        assert entry.raw_entry == raw_entry


class TestJournalViewer:
    """Test the JournalViewer class."""

    def test_init_default_params(self):
        """Test initialization with default parameters."""
        viewer = JournalViewer()

        assert viewer.show_hostname is False
        assert viewer.show_pid is True
        assert viewer.show_service is True
        assert viewer.max_width == 120

    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        viewer = JournalViewer(
            show_hostname=True,
            show_pid=False,
            show_service=False,
            max_width=80,
        )

        assert viewer.show_hostname is True
        assert viewer.show_pid is False
        assert viewer.show_service is False
        assert viewer.max_width == 80

    def test_priority_to_level_mapping(self):
        """Test the priority to level mapping."""
        expected_mapping = {
            0: "critical",  # LOG_EMERG
            1: "critical",  # LOG_ALERT
            2: "critical",  # LOG_CRIT
            3: "error",  # LOG_ERR
            4: "warning",  # LOG_WARNING
            5: "info",  # LOG_NOTICE
            6: "info",  # LOG_INFO
            7: "debug",  # LOG_DEBUG
        }

        assert expected_mapping == JournalViewer.PRIORITY_TO_LEVEL

    def test_level_colors_defined(self):
        """Test that level colors are defined."""
        expected_levels = {"critical", "error", "warning", "info", "debug"}
        assert set(JournalViewer.LEVEL_COLORS.keys()) == expected_levels

    def test_parse_journal_entry_basic(self):
        """Test parsing a basic journal entry."""
        viewer = JournalViewer()

        timestamp = datetime.now()
        mock_timestamp = Mock(spec=datetime)
        mock_timestamp.timestamp.return_value = timestamp.timestamp()

        raw_entry = {
            "__REALTIME_TIMESTAMP": mock_timestamp,
            "_HOSTNAME": "testhost",
            "SYSLOG_IDENTIFIER": "testservice",
            "_PID": 1234,
            "MESSAGE": "test message",
            "PRIORITY": 6,
        }

        entry = viewer.parse_journal_entry(raw_entry)

        assert entry.hostname == "testhost"
        assert entry.service == "testservice"
        assert entry.pid == "1234"
        assert entry.message == "test message"
        assert entry.level == "info"
        assert entry.raw_entry == raw_entry

    def test_parse_journal_entry_missing_fields(self):
        """Test parsing journal entry with missing fields."""
        viewer = JournalViewer()

        raw_entry = {"MESSAGE": "test message"}

        entry = viewer.parse_journal_entry(raw_entry)

        assert entry.hostname == "unknown"
        assert entry.service == "unknown"
        assert entry.pid == ""
        assert entry.message == "test message"
        assert entry.level == "info"  # Default priority 6

    def test_parse_journal_entry_alternative_fields(self):
        """Test parsing with alternative field names."""
        viewer = JournalViewer()

        raw_entry = {
            "_COMM": "altservice",
            "SYSLOG_PID": 5678,
            "MESSAGE": "test message",
            "PRIORITY": "3",  # String priority
        }

        entry = viewer.parse_journal_entry(raw_entry)

        assert entry.service == "altservice"
        assert entry.pid == "5678"
        assert entry.level == "error"  # Priority 3

    def test_parse_journal_entry_custom_fields(self):
        """Test parsing custom stogger fields."""
        viewer = JournalViewer()

        raw_entry = {
            "MESSAGE": "test message",
            "STOGGER_USER_ID": "123",
            "STOGGER_DATA": '{"key": "value"}',
            "STOGGER_SIMPLE": "simple_value",
        }

        entry = viewer.parse_journal_entry(raw_entry)

        assert entry.fields["user_id"] == "123"
        assert entry.fields["data"] == {"key": "value"}  # Parsed JSON
        assert entry.fields["simple"] == "simple_value"

    def test_parse_journal_entry_invalid_json(self):
        """Test parsing custom fields with invalid JSON."""
        viewer = JournalViewer()

        raw_entry = {
            "MESSAGE": "test message",
            "STOGGER_INVALID": '{"invalid": json}',
        }

        entry = viewer.parse_journal_entry(raw_entry)

        # Should keep as string when JSON parsing fails
        assert entry.fields["invalid"] == '{"invalid": json}'

    def test_format_entry_basic(self):
        """Test basic entry formatting."""
        viewer = JournalViewer()

        timestamp = datetime(2023, 1, 1, 12, 30, 45, 123456)
        entry = JournalEntry(
            timestamp=timestamp,
            hostname="testhost",
            service="testservice",
            pid="1234",
            level="info",
            message="test message",
            fields={},
            raw_entry={},
        )

        result = viewer.format_entry(entry)

        assert "12:30:45.123" in result  # Timestamp
        assert "I" in result  # Info level indicator
        assert "testservice" in result  # Service name
        assert "(1234)" in result  # PID
        assert "test message" in result  # Message

    def test_format_entry_with_hostname(self):
        """Test entry formatting with hostname shown."""
        viewer = JournalViewer(show_hostname=True)

        timestamp = datetime.now()
        entry = JournalEntry(
            timestamp=timestamp,
            hostname="testhost",
            service="testservice",
            pid="1234",
            level="info",
            message="test message",
            fields={},
            raw_entry={},
        )

        result = viewer.format_entry(entry)
        assert "@testhost" in result

    def test_format_entry_without_service(self):
        """Test entry formatting without service shown."""
        viewer = JournalViewer(show_service=False)

        timestamp = datetime.now()
        entry = JournalEntry(
            timestamp=timestamp,
            hostname="testhost",
            service="testservice",
            pid="1234",
            level="info",
            message="test message",
            fields={},
            raw_entry={},
        )

        result = viewer.format_entry(entry)
        assert "[testservice]" not in result

    def test_format_entry_without_pid(self):
        """Test entry formatting without PID shown."""
        viewer = JournalViewer(show_pid=False)

        timestamp = datetime.now()
        entry = JournalEntry(
            timestamp=timestamp,
            hostname="testhost",
            service="testservice",
            pid="1234",
            level="info",
            message="test message",
            fields={},
            raw_entry={},
        )

        result = viewer.format_entry(entry)
        assert "(1234)" not in result

    def test_format_entry_with_custom_fields(self):
        """Test entry formatting with custom fields."""
        viewer = JournalViewer()

        timestamp = datetime.now()
        entry = JournalEntry(
            timestamp=timestamp,
            hostname="testhost",
            service="testservice",
            pid="1234",
            level="info",
            message="test message",
            fields={"user_id": "123", "data": {"key": "value"}, "count": 42},
            raw_entry={},
        )

        result = viewer.format_entry(entry)
        assert "user_id=123" in result
        assert "data=" in result
        assert "count=42" in result

    def test_format_entry_different_levels(self):
        """Test entry formatting with different log levels."""
        viewer = JournalViewer()

        timestamp = datetime.now()

        for level, expected_char in [
            ("critical", "C"),
            ("error", "E"),
            ("warning", "W"),
            ("info", "I"),
            ("debug", "D"),
        ]:
            entry = JournalEntry(
                timestamp=timestamp,
                hostname="testhost",
                service="testservice",
                pid="1234",
                level=level,
                message="test message",
                fields={},
                raw_entry={},
            )

            result = viewer.format_entry(entry)
            assert expected_char in result

    def test_query_journal_basic(self):
        """Test basic journal querying."""
        with patch.dict(sys.modules, {"systemd.journal": MagicMock()}) as mods:
            mock_journal = mods["systemd.journal"]
            mock_reader = Mock(spec=_JournalReaderStub)
            mock_journal.Reader.return_value = mock_reader

            # Mock journal entries
            mock_entries = [
                {"MESSAGE": "entry 1", "PRIORITY": 6},
                {"MESSAGE": "entry 2", "PRIORITY": 4},
            ]
            mock_reader.__iter__ = Mock(spec=FunctionType, return_value=iter(mock_entries))

            viewer = JournalViewer()
            entries = list(viewer.query_journal(JournalQueryOptions()))

            assert len(entries) == 2
            assert entries[0].message == "entry 1"
            assert entries[1].message == "entry 2"

            mock_reader.seek_head.assert_called_once()

    def test_query_journal_with_service_filter(self):
        """Test journal querying with service filter."""
        with patch.dict(sys.modules, {"systemd.journal": MagicMock()}) as mods:
            mock_journal = mods["systemd.journal"]
            mock_reader = Mock(spec=_JournalReaderStub)
            mock_journal.Reader.return_value = mock_reader
            mock_reader.__iter__ = Mock(spec=FunctionType, return_value=iter([]))

            viewer = JournalViewer()
            list(viewer.query_journal(JournalQueryOptions(service="myservice")))

            mock_reader.add_match.assert_called_with(SYSLOG_IDENTIFIER="myservice")

    def test_query_journal_with_level_filter(self):
        """Test journal querying with level filter."""
        with patch.dict(sys.modules, {"systemd.journal": MagicMock()}) as mods:
            mock_journal = mods["systemd.journal"]
            mock_reader = Mock(spec=_JournalReaderStub)
            mock_journal.Reader.return_value = mock_reader
            mock_reader.__iter__ = Mock(spec=FunctionType, return_value=iter([]))

            viewer = JournalViewer()
            list(viewer.query_journal(JournalQueryOptions(level="error")))

            # Should add matches for priorities 0, 1, 2, 3 (critical, error)
            expected_calls = [
                (("PRIORITY", 0),),
                (("PRIORITY", 1),),
                (("PRIORITY", 2),),
                (("PRIORITY", 3),),
            ]
            actual_calls = [call.args for call in mock_reader.add_match.call_args_list]
            assert actual_calls == expected_calls

    def test_query_journal_with_lines_limit(self):
        """Test journal querying with lines limit."""
        with patch.dict(sys.modules, {"systemd.journal": MagicMock()}) as mods:
            mock_journal = mods["systemd.journal"]
            mock_reader = Mock(spec=_JournalReaderStub)
            mock_journal.Reader.return_value = mock_reader

            # Mock many entries
            mock_entries = [{"MESSAGE": f"entry {i}", "PRIORITY": 6} for i in range(100)]
            mock_reader.__iter__ = Mock(spec=FunctionType, return_value=iter(mock_entries))

            viewer = JournalViewer()
            entries = list(viewer.query_journal(JournalQueryOptions(lines=5)))

            assert len(entries) == 5
            mock_reader.seek_tail.assert_called_once()
            mock_reader.get_previous.assert_called_once_with(5)

    def test_query_journal_follow_mode(self):
        """Test journal querying in follow mode."""
        with patch.dict(sys.modules, {"systemd.journal": MagicMock()}) as mods:
            mock_journal = mods["systemd.journal"]
            mock_reader = Mock(spec=_JournalReaderStub)
            mock_journal.Reader.return_value = mock_reader

            # Mock limited entries for follow mode
            mock_entries = [{"MESSAGE": "entry 1", "PRIORITY": 6}]
            mock_reader.__iter__ = Mock(spec=FunctionType, return_value=iter(mock_entries))

            viewer = JournalViewer()
            entries = list(viewer.query_journal(JournalQueryOptions(follow=True, lines=1)))

            assert len(entries) == 1
            mock_reader.seek_tail.assert_called_once()
            mock_reader.wait.assert_called_once()

    def test_query_journal_with_since(self):
        """Test journal querying with since parameter."""
        with patch.dict(sys.modules, {"systemd.journal": MagicMock()}) as mods:
            mock_journal = mods["systemd.journal"]
            mock_reader = Mock(spec=_JournalReaderStub)
            mock_journal.Reader.return_value = mock_reader
            mock_reader.__iter__ = Mock(spec=FunctionType, return_value=iter([]))

            viewer = JournalViewer()
            with patch.object(viewer, "parse_time_string", autospec=True) as mock_parse:
                mock_time = datetime.now()
                mock_parse.return_value = mock_time

                list(viewer.query_journal(JournalQueryOptions(since="1 hour ago")))

                mock_parse.assert_called_once_with("1 hour ago")
                mock_reader.seek_realtime.assert_called_once_with(mock_time)

    def test_query_journal_exception_handling(self, caplog):
        """Test journal querying exception handling."""
        caplog.set_level(logging.ERROR)
        with patch.dict(sys.modules, {"systemd.journal": MagicMock()}) as mods:
            mock_journal = mods["systemd.journal"]
            mock_journal.Reader.side_effect = Exception("Journal error")

            init_logging()
            viewer = JournalViewer()
            entries = list(viewer.query_journal(JournalQueryOptions()))

            assert entries == []
            assert "Error reading journal" in caplog.text

    def test_parse_time_string_relative_hours(self):
        """Test parsing relative time strings with hours."""
        viewer = JournalViewer()

        now = datetime.now()
        with patch("stogger_systemd.journal_viewer.datetime", autospec=True) as mock_dt:
            mock_dt.now.return_value = now

            result = viewer.parse_time_string("2 hours ago")
            expected = now - timedelta(hours=2)

            # Allow small time difference due to execution time
            assert abs((result - expected).total_seconds()) < 1

    def test_parse_time_string_relative_minutes(self):
        """Test parsing relative time strings with minutes."""
        viewer = JournalViewer()

        now = datetime.now()
        with patch("stogger_systemd.journal_viewer.datetime", autospec=True) as mock_dt:
            mock_dt.now.return_value = now

            result = viewer.parse_time_string("30 minutes ago")
            expected = now - timedelta(minutes=30)

            assert abs((result - expected).total_seconds()) < 1

    def test_parse_time_string_relative_days(self):
        """Test parsing relative time strings with days."""
        viewer = JournalViewer()

        now = datetime.now()
        with patch("stogger_systemd.journal_viewer.datetime", autospec=True) as mock_dt:
            mock_dt.now.return_value = now

            result = viewer.parse_time_string("3 days ago")
            expected = now - timedelta(days=3)

            assert abs((result - expected).total_seconds()) < 1

    def test_parse_time_string_today(self):
        """Test parsing 'today' time string."""
        viewer = JournalViewer()

        now = datetime(2023, 5, 15, 14, 30, 0)
        with patch("stogger_systemd.journal_viewer.datetime", autospec=True) as mock_dt:
            mock_dt.now.return_value = now

            result = viewer.parse_time_string("today")
            expected = datetime(2023, 5, 15, 0, 0, 0)

            assert result == expected

    def test_parse_time_string_yesterday(self):
        """Test parsing 'yesterday' time string."""
        viewer = JournalViewer()

        now = datetime(2023, 5, 15, 14, 30, 0)
        with patch("stogger_systemd.journal_viewer.datetime", autospec=True) as mock_dt:
            mock_dt.now.return_value = now

            result = viewer.parse_time_string("yesterday")
            expected = datetime(2023, 5, 14, 0, 0, 0)

            assert result == expected

    def test_parse_time_string_iso_format(self):
        """Test parsing ISO format time strings."""
        viewer = JournalViewer()

        result = viewer.parse_time_string("2023-05-15 14:30:00")
        expected = datetime(2023, 5, 15, 14, 30, 0)

        assert result == expected

    def test_parse_time_string_iso_format_with_t(self):
        """Test parsing ISO format with T separator."""
        viewer = JournalViewer()

        result = viewer.parse_time_string("2023-05-15T14:30:00")
        expected = datetime(2023, 5, 15, 14, 30, 0)

        assert result == expected

    def test_parse_time_string_default_fallback(self):
        """Test parsing unknown time string falls back to 1 hour ago."""
        viewer = JournalViewer()

        before = datetime.now(tz=UTC) - timedelta(hours=1)
        result = viewer.parse_time_string("invalid time string")
        after = datetime.now(tz=UTC) - timedelta(hours=1)

        assert before <= result <= after


class TestMainFunction:
    """Test the main CLI function."""

    def test_main_with_arguments(self):
        """Test main function with command line arguments."""
        with patch("sys.argv", ["journal_viewer", "-u", "myservice", "-n", "10"]):
            with patch(
                "stogger_systemd.journal_viewer.JournalViewer",
                autospec=True,
            ) as mock_viewer_class:
                mock_viewer = Mock(spec=JournalViewer)
                mock_viewer_class.return_value = mock_viewer
                mock_viewer.query_journal.return_value = []

                from stogger_systemd.journal_viewer import main

                main()

                mock_viewer_class.assert_called_once()
                mock_viewer.query_journal.assert_called_once_with(
                    JournalQueryOptions(
                        service="myservice",
                        since=None,
                        until=None,
                        level=None,
                        lines=10,
                        follow=False,
                    )
                )

    def test_main_json_output(self, caplog):
        """Test main function with JSON output."""
        caplog.set_level(logging.INFO)
        with patch("sys.argv", ["journal_viewer", "--json"]):
            with patch(
                "stogger_systemd.journal_viewer.JournalViewer",
                autospec=True,
            ) as mock_viewer_class:
                mock_viewer = Mock(spec=JournalViewer)
                mock_viewer_class.return_value = mock_viewer

                # Mock journal entry
                mock_entry = Mock(spec=JournalEntry)
                mock_entry.raw_entry = {"MESSAGE": "test"}
                mock_viewer.query_journal.return_value = [mock_entry]

                init_logging()
                from stogger_systemd.journal_viewer import main

                main()

                # Should have processed entries
                assert "Journal display completed" in caplog.text

    def test_main_formatted_output(self, caplog):
        """Test main function with formatted output."""
        caplog.set_level(logging.INFO)
        with patch("sys.argv", ["journal_viewer"]):
            with patch(
                "stogger_systemd.journal_viewer.JournalViewer",
                autospec=True,
            ) as mock_viewer_class:
                mock_viewer = Mock(spec=JournalViewer)
                mock_viewer_class.return_value = mock_viewer

                # Mock journal entry
                mock_entry = Mock(spec=JournalEntry)
                mock_viewer.query_journal.return_value = [mock_entry]
                mock_viewer.format_entry.return_value = "formatted entry"

                init_logging()
                from stogger_systemd.journal_viewer import main

                main()

                # Should have processed entries
                assert "Journal display completed" in caplog.text

    def test_main_keyboard_interrupt(self, caplog):
        """Test main function handling keyboard interrupt."""
        caplog.set_level(logging.INFO)
        with patch("sys.argv", ["journal_viewer"]):
            with patch(
                "stogger_systemd.journal_viewer.JournalViewer",
                autospec=True,
            ) as mock_viewer_class:
                mock_viewer = Mock(spec=JournalViewer)
                mock_viewer_class.return_value = mock_viewer
                mock_viewer.query_journal.side_effect = KeyboardInterrupt()

                with patch("sys.exit", autospec=True) as mock_exit:
                    init_logging()
                    from stogger_systemd.journal_viewer import main

                    main()

                    mock_exit.assert_called_once_with(0)
                    assert "User interrupted journal viewer" in caplog.text

    def test_main_general_exception(self, caplog):
        """Test main function handling general exceptions."""
        caplog.set_level(logging.ERROR)
        with patch("sys.argv", ["journal_viewer"]):
            with patch(
                "stogger_systemd.journal_viewer.JournalViewer",
                autospec=True,
            ) as mock_viewer_class:
                mock_viewer_class.side_effect = Exception("Test error")

                with patch("sys.exit", autospec=True) as mock_exit:
                    init_logging()
                    from stogger_systemd.journal_viewer import main

                    main()

                    mock_exit.assert_called_once_with(1)
                    assert "Failed to create journal viewer" in caplog.text


class TestColorImports:
    """Test color constant imports and fallbacks."""

    def test_color_constants_available(self):
        """Test that color constants are available."""
        from stogger_systemd.journal_viewer import (
            BLUE,
            BRIGHT,
            CYAN,
            DIM,
            GREEN,
            MAGENTA,
            RED,
            RESET_ALL,
            YELLOW,
        )

        # Should be strings (either ANSI codes or empty strings)
        assert isinstance(RESET_ALL, str)
        assert isinstance(BRIGHT, str)
        assert isinstance(DIM, str)
        assert isinstance(RED, str)
        assert isinstance(BLUE, str)
        assert isinstance(CYAN, str)
        assert isinstance(MAGENTA, str)
        assert isinstance(YELLOW, str)
        assert isinstance(GREEN, str)
