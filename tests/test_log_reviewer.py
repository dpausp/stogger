"""
Tests for log_reviewer module.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from io import StringIO

from src.nicestlog.log_reviewer import LogQualityReport, LogQualityReviewer


class TestLogQualityReport:
    """Test the LogQualityReport dataclass."""

    def test_log_quality_report_creation(self):
        """Test creating a LogQualityReport."""
        report = LogQualityReport(
            overall_score=85.5,
            overall_verdict="verziehbar",
            issues=["issue1", "issue2"],
            good_practices=["good1"],
            suggestions=["suggestion1"],
            stats={"total_lines": 100},
        )

        assert report.overall_score == 85.5
        assert report.overall_verdict == "verziehbar"
        assert report.issues == ["issue1", "issue2"]
        assert report.good_practices == ["good1"]
        assert report.suggestions == ["suggestion1"]
        assert report.stats == {"total_lines": 100}


class TestLogQualityReviewer:
    """Test the LogQualityReviewer class."""

    def test_init(self):
        """Test reviewer initialization."""
        reviewer = LogQualityReviewer()

        assert reviewer.event_patterns == []
        assert reviewer.field_patterns == []
        assert len(reviewer.bad_patterns) > 0
        assert "debug\\s*print" in reviewer.bad_patterns
        assert len(reviewer.quality_levels) == 5

    def test_quality_levels_structure(self):
        """Test quality levels are properly structured."""
        reviewer = LogQualityReviewer()

        expected_verdicts = {"leiwand", "verziehbar", "mäßig", "schlecht", "arsch"}
        actual_verdicts = {
            verdict for (_, _), (verdict, _) in reviewer.quality_levels.items()
        }

        assert actual_verdicts == expected_verdicts

    def test_analyze_log_file_success(self):
        """Test successful log file analysis."""
        reviewer = LogQualityReviewer()

        log_content = """2023-01-01 12:00:00 INFO user_login user_id=123 session_id=abc
2023-01-01 12:01:00 ERROR auth_failed user_id=456 reason="invalid password"
{"timestamp": "2023-01-01T12:02:00", "level": "INFO", "event": "api_request", "user_id": 789}"""

        # Create a proper mock Path object
        mock_path = Mock(spec=Path)
        mock_path.read_text.return_value = log_content

        report = reviewer.analyze_log_file(mock_path)

        assert isinstance(report, LogQualityReport)
        assert report.overall_score > 0
        assert report.stats["total_lines"] == 3
        assert report.stats["structured_lines"] > 0

    def test_analyze_log_file_read_error(self):
        """Test log file analysis with read error."""
        reviewer = LogQualityReviewer()

        with patch(
            "pathlib.Path.read_text", side_effect=FileNotFoundError("File not found")
        ):
            mock_path = Mock(spec=Path)
            report = reviewer.analyze_log_file(mock_path)

            assert report.overall_score == 0
            assert report.overall_verdict == "arsch"
            assert "Kann die Datei nicht lesen" in report.issues[0]

    def test_analyze_log_content(self):
        """Test direct log content analysis."""
        reviewer = LogQualityReviewer()

        log_content = """INFO: Application started
ERROR: Database connection failed"""

        report = reviewer.analyze_log_content(log_content)

        assert isinstance(report, LogQualityReport)
        assert report.stats["total_lines"] == 2
        assert "info" in report.stats["levels_found"]
        assert "error" in report.stats["levels_found"]

    def test_has_timestamp_iso_format(self):
        """Test timestamp detection with ISO format."""
        reviewer = LogQualityReviewer()

        assert reviewer._has_timestamp("2023-01-01 12:00:00 INFO message")
        assert reviewer._has_timestamp("2023-01-01T12:00:00 INFO message")
        assert not reviewer._has_timestamp("INFO message without timestamp")

    def test_has_timestamp_time_only(self):
        """Test timestamp detection with time only."""
        reviewer = LogQualityReviewer()

        assert reviewer._has_timestamp("12:00:00 INFO message")
        assert reviewer._has_timestamp("23:59:59 ERROR message")
        assert not reviewer._has_timestamp("INFO 12 message")

    def test_has_timestamp_unix(self):
        """Test timestamp detection with Unix timestamp."""
        reviewer = LogQualityReviewer()

        assert reviewer._has_timestamp("1672574400 INFO message")  # 10 digits
        assert reviewer._has_timestamp("1672574400123 INFO message")  # 13 digits
        assert not reviewer._has_timestamp("123 INFO message")  # Too short

    def test_extract_log_level_full_words(self):
        """Test log level extraction with full words."""
        reviewer = LogQualityReviewer()

        assert reviewer._extract_log_level("INFO: message") == "info"
        assert reviewer._extract_log_level("ERROR something happened") == "error"
        assert reviewer._extract_log_level("DEBUG trace info") == "debug"
        assert reviewer._extract_log_level("WARNING: be careful") == "warning"
        assert reviewer._extract_log_level("CRITICAL system failure") == "critical"
        assert reviewer._extract_log_level("FATAL error occurred") == "fatal"

    def test_extract_log_level_single_letters(self):
        """Test log level extraction with single letters."""
        reviewer = LogQualityReviewer()

        assert reviewer._extract_log_level("I message") == "i"
        assert (
            reviewer._extract_log_level("E something") == "e"
        )  # Avoid "error" which matches full word
        assert (
            reviewer._extract_log_level("D something") == "d"
        )  # Avoid "debug" which matches full word
        assert (
            reviewer._extract_log_level("W something") == "w"
        )  # Avoid "warning" which matches full word

    def test_extract_log_level_none(self):
        """Test log level extraction returns None when no level found."""
        reviewer = LogQualityReviewer()

        assert reviewer._extract_log_level("just a message") is None
        assert reviewer._extract_log_level("INFORMATION is not a level") is None

    def test_is_structured_log_json(self):
        """Test structured log detection with JSON."""
        reviewer = LogQualityReviewer()

        assert reviewer._is_structured_log('{"level": "info", "message": "test"}')
        assert not reviewer._is_structured_log('{"invalid": json}')  # Invalid JSON
        assert not reviewer._is_structured_log("not json at all")

    def test_is_structured_log_key_value(self):
        """Test structured log detection with key=value format."""
        reviewer = LogQualityReviewer()

        assert reviewer._is_structured_log("user_id=123 action=login")
        assert reviewer._is_structured_log("level=info message=test")
        assert not reviewer._is_structured_log("just a message")
        assert reviewer._is_structured_log(
            "single=value"
        )  # Single key=value is considered structured

    def test_is_structured_log_colon_format(self):
        """Test structured log detection with key:value format."""
        reviewer = LogQualityReviewer()

        assert reviewer._is_structured_log("user:123 action:login status:success")
        assert not reviewer._is_structured_log("user:123")  # Need at least 2 fields

    def test_extract_fields_json(self):
        """Test field extraction from JSON logs."""
        reviewer = LogQualityReviewer()

        fields = reviewer._extract_fields(
            '{"user_id": 123, "action": "login", "status": "success"}'
        )
        assert set(fields) == {"user_id", "action", "status"}

    def test_extract_fields_json_invalid(self):
        """Test field extraction from invalid JSON."""
        reviewer = LogQualityReviewer()

        fields = reviewer._extract_fields('{"invalid": json}')
        assert fields == []

    def test_extract_fields_key_value(self):
        """Test field extraction from key=value format."""
        reviewer = LogQualityReviewer()

        fields = reviewer._extract_fields("user_id=123 action=login status=success")
        assert set(fields) == {"user_id", "action", "status"}

    def test_extract_fields_colon_format(self):
        """Test field extraction from key:value format."""
        reviewer = LogQualityReviewer()

        fields = reviewer._extract_fields("user:123 action:login status:success")
        assert set(fields) == {"user", "action", "status"}

    def test_extract_event_name_json(self):
        """Test event name extraction from JSON."""
        reviewer = LogQualityReviewer()

        event = reviewer._extract_event_name('{"event": "user_login", "user_id": 123}')
        assert event == "user_login"

    def test_extract_event_name_key_value(self):
        """Test event name extraction from key=value format."""
        reviewer = LogQualityReviewer()

        event = reviewer._extract_event_name("event=api_request user_id=123")
        assert event == "api_request"

    def test_extract_event_name_patterns(self):
        """Test event name extraction using common patterns."""
        reviewer = LogQualityReviewer()

        assert reviewer._extract_event_name("user_login successful") == "user_login"
        assert (
            reviewer._extract_event_name("api_request_started") == "api_request_started"
        )
        assert reviewer._extract_event_name("db_query_executed") == "db_query_executed"
        assert (
            reviewer._extract_event_name("auth_token_validated")
            == "auth_token_validated"
        )

    def test_extract_event_name_none(self):
        """Test event name extraction returns None when no event found."""
        reviewer = LogQualityReviewer()

        assert reviewer._extract_event_name("just a regular message") is None
        assert reviewer._extract_event_name("no events here") is None

    def test_calculate_quality_score_empty_logs(self):
        """Test quality score calculation with empty logs."""
        reviewer = LogQualityReviewer()

        stats = {"total_lines": 0}
        score = reviewer._calculate_quality_score(stats)
        assert score == 0

    def test_calculate_quality_score_perfect_logs(self):
        """Test quality score calculation with perfect logs."""
        reviewer = LogQualityReviewer()

        stats = {
            "total_lines": 100,
            "empty_lines": 0,
            "structured_lines": 100,
            "unstructured_lines": 0,
            "levels_found": {"debug", "info", "warning", "error"},
            "events_found": {
                "user_login",
                "api_request",
                "db_query",
                "auth_check",
                "data_process",
            },
            "fields_found": {
                "user_id": 50,
                "request_id": 50,
                "session_id": 50,
                "action": 100,
                "status": 100,
                "timestamp": 100,
                "level": 100,
                "message": 100,
                "duration": 30,
                "ip_address": 50,
            },
            "timestamps_found": 100,
            "json_lines": 100,
            "debug_prints": 0,
        }

        score = reviewer._calculate_quality_score(stats)
        assert score >= 90  # Should be high quality

    def test_calculate_quality_score_poor_logs(self):
        """Test quality score calculation with poor logs."""
        reviewer = LogQualityReviewer()

        stats = {
            "total_lines": 100,
            "empty_lines": 10,
            "structured_lines": 10,
            "unstructured_lines": 80,
            "levels_found": set(),
            "events_found": set(),
            "fields_found": {},
            "timestamps_found": 5,
            "json_lines": 0,
            "debug_prints": 20,
        }

        score = reviewer._calculate_quality_score(stats)
        assert score <= 30  # Should be poor quality

    def test_get_verdict(self):
        """Test verdict generation based on score."""
        reviewer = LogQualityReviewer()

        verdict, msg = reviewer._get_verdict(95)
        assert verdict == "leiwand"
        assert "richtig geil" in msg

        verdict, msg = reviewer._get_verdict(75)
        assert verdict == "verziehbar"

        verdict, msg = reviewer._get_verdict(55)
        assert verdict == "mäßig"

        verdict, msg = reviewer._get_verdict(35)
        assert verdict == "schlecht"

        verdict, msg = reviewer._get_verdict(15)
        assert verdict == "arsch"

    def test_find_issues(self):
        """Test issue detection."""
        reviewer = LogQualityReviewer()

        stats = {
            "total_lines": 100,
            "empty_lines": 40,
            "structured_lines": 20,
            "unstructured_lines": 60,
            "levels_found": {"info"},
            "events_found": {"event1"},
            "timestamps_found": 30,
            "debug_prints": 5,
        }

        issues = reviewer._find_issues(stats)

        assert any("Debug-Prints" in issue for issue in issues)
        assert any("Timestamps" in issue for issue in issues)
        assert any("Log-Level" in issue for issue in issues)
        assert any("strukturierte Logs" in issue for issue in issues)
        assert any("Events" in issue for issue in issues)
        assert any("leere Zeilen" in issue for issue in issues)

    def test_find_good_practices(self):
        """Test good practice detection."""
        reviewer = LogQualityReviewer()

        stats = {
            "total_lines": 100,
            "structured_lines": 80,
            "unstructured_lines": 20,
            "levels_found": {"debug", "info", "warning", "error"},
            "events_found": {"event1", "event2", "event3", "event4", "event5"},
            "timestamps_found": 90,
            "debug_prints": 0,
            "fields_found": {
                "field1": 10,
                "field2": 10,
                "field3": 10,
                "field4": 10,
                "field5": 10,
                "field6": 10,
                "field7": 10,
                "field8": 10,
            },
        }

        good_practices = reviewer._find_good_practices(stats)

        assert any("strukturierte Logs" in practice for practice in good_practices)
        assert any("Timestamps" in practice for practice in good_practices)
        assert any("Log-Level" in practice for practice in good_practices)
        assert any("Events" in practice for practice in good_practices)
        assert any("Debug-Prints" in practice for practice in good_practices)
        assert any("Felder" in practice for practice in good_practices)

    def test_generate_suggestions(self):
        """Test suggestion generation."""
        reviewer = LogQualityReviewer()

        stats = {
            "total_lines": 100,
            "structured_lines": 30,
            "levels_found": {"info"},
            "events_found": {"event1"},
            "timestamps_found": 50,
            "fields_found": {"basic_field": 10},
            "debug_prints": 3,
        }

        suggestions = reviewer._generate_suggestions(stats)

        assert any("strukturierte Logs" in suggestion for suggestion in suggestions)
        assert any("Log-Level" in suggestion for suggestion in suggestions)
        assert any("Timestamps" in suggestion for suggestion in suggestions)
        assert any("Event-Namen" in suggestion for suggestion in suggestions)
        assert any("user_id" in suggestion for suggestion in suggestions)
        assert any("request_id" in suggestion for suggestion in suggestions)
        assert any("Debug-Prints" in suggestion for suggestion in suggestions)

    def test_analyze_log_lines_comprehensive(self):
        """Test comprehensive log line analysis."""
        reviewer = LogQualityReviewer()

        lines = [
            '2023-01-01 12:00:00 INFO {"event": "user_login", "user_id": 123, "session_id": "abc"}',
            '2023-01-01 12:01:00 ERROR {"event": "auth_failed", "user_id": 456, "reason": "invalid password"}',
            "2023-01-01 12:02:00 DEBUG user_action user_id=789 action=click",
            'print("debug message")',  # Bad practice
            "",  # Empty line
            "Unstructured log message without timestamp",
        ]

        report = reviewer._analyze_log_lines(lines, "test")

        assert report.stats["total_lines"] == 6
        assert report.stats["empty_lines"] == 1
        assert (
            report.stats["structured_lines"] >= 1
        )  # At least the JSON lines and key=value line
        assert report.stats["unstructured_lines"] >= 1
        assert report.stats["timestamps_found"] >= 3
        assert report.stats["debug_prints"] >= 1
        assert "info" in report.stats["levels_found"]
        assert "error" in report.stats["levels_found"]
        assert (
            len(report.stats["events_found"]) >= 1
        )  # At least some events should be found


class TestCLIFunctions:
    """Test CLI-related functions."""

    def test_print_report_text_format(self):
        """Test printing report in text format."""
        report = LogQualityReport(
            overall_score=75.5,
            overall_verdict="verziehbar",
            issues=["Issue 1", "Issue 2"],
            good_practices=["Good 1"],
            suggestions=["Suggestion 1"],
            stats={
                "total_lines": 100,
                "structured_lines": 60,
                "unstructured_lines": 40,
                "levels_found": {"info", "error"},
                "events_found": {"event1", "event2"},
                "fields_found": {"field1": 10, "field2": 20},
            },
        )

        with patch("builtins.print") as mock_print:
            from src.nicestlog.log_reviewer import print_report

            print_report(report, "text")

            # Check that print was called multiple times
            assert mock_print.call_count > 5

            # Check some key content was printed
            printed_text = " ".join(
                str(call.args[0]) for call in mock_print.call_args_list if call.args
            )
            assert "75.5" in printed_text
            assert "verziehbar" in printed_text

    def test_print_report_json_format(self):
        """Test printing report in JSON format."""
        report = LogQualityReport(
            overall_score=85.0,
            overall_verdict="verziehbar",
            issues=["Issue 1"],
            good_practices=["Good 1"],
            suggestions=["Suggestion 1"],
            stats={"total_lines": 50},
        )

        with patch("builtins.print") as mock_print:
            from src.nicestlog.log_reviewer import print_report

            print_report(report, "json")

            # Should print JSON
            mock_print.assert_called_once()
            printed_json = mock_print.call_args[0][0]

            # Verify it's valid JSON
            data = json.loads(printed_json)
            assert data["score"] == 85.0
            assert data["verdict"] == "verziehbar"
            assert data["issues"] == ["Issue 1"]

    @patch("sys.argv", ["log_reviewer", "test.log"])
    @patch("pathlib.Path.is_file", return_value=True)
    @patch("pathlib.Path.is_dir", return_value=False)
    def test_review_logs_cli_single_file(self, mock_is_dir, mock_is_file):
        """Test CLI with single file."""
        with patch(
            "src.nicestlog.log_reviewer.LogQualityReviewer"
        ) as mock_reviewer_class:
            mock_reviewer = Mock()
            mock_reviewer_class.return_value = mock_reviewer

            # Mock a good report
            mock_report = LogQualityReport(
                overall_score=80.0,
                overall_verdict="verziehbar",
                issues=[],
                good_practices=[],
                suggestions=[],
                stats={},
            )
            mock_reviewer.analyze_log_file.return_value = mock_report

            with patch("src.nicestlog.log_reviewer.print_report") as mock_print:
                from src.nicestlog.log_reviewer import review_logs_cli

                review_logs_cli()

                mock_reviewer.analyze_log_file.assert_called_once()
                mock_print.assert_called_once_with(mock_report, "text")

    @patch("sys.argv", ["log_reviewer", "test.log", "--min-score", "90"])
    @patch("pathlib.Path.is_file", return_value=True)
    @patch("pathlib.Path.is_dir", return_value=False)
    def test_review_logs_cli_low_score_exit(self, mock_is_dir, mock_is_file):
        """Test CLI exits with code 1 when score is below minimum."""
        with patch(
            "src.nicestlog.log_reviewer.LogQualityReviewer"
        ) as mock_reviewer_class:
            mock_reviewer = Mock()
            mock_reviewer_class.return_value = mock_reviewer

            # Mock a low score report
            mock_report = LogQualityReport(
                overall_score=50.0,
                overall_verdict="mäßig",
                issues=[],
                good_practices=[],
                suggestions=[],
                stats={},
            )
            mock_reviewer.analyze_log_file.return_value = mock_report

            with patch("src.nicestlog.log_reviewer.print_report"):
                with patch("sys.exit") as mock_exit:
                    mock_exit.side_effect = SystemExit(1)

                    from src.nicestlog.log_reviewer import review_logs_cli

                    with pytest.raises(SystemExit):
                        review_logs_cli()

                    mock_exit.assert_called_once_with(1)

    @patch("sys.argv", ["log_reviewer", "logdir/"])
    @patch("pathlib.Path.is_file", return_value=False)
    @patch("pathlib.Path.is_dir", return_value=True)
    def test_review_logs_cli_directory(self, mock_is_dir, mock_is_file):
        """Test CLI with directory containing log files."""
        with patch(
            "src.nicestlog.log_reviewer.LogQualityReviewer"
        ) as mock_reviewer_class:
            mock_reviewer = Mock()
            mock_reviewer_class.return_value = mock_reviewer

            # Mock log files in directory
            mock_log_files = [Mock(name="test1.log"), Mock(name="test2.log")]

            with patch("pathlib.Path.glob") as mock_glob:
                mock_glob.side_effect = [
                    mock_log_files,
                    [],
                ]  # *.log files, then *.txt files

                # Mock reports
                mock_report = LogQualityReport(
                    overall_score=75.0,
                    overall_verdict="verziehbar",
                    issues=[],
                    good_practices=[],
                    suggestions=[],
                    stats={},
                )
                mock_reviewer.analyze_log_file.return_value = mock_report

                with patch("src.nicestlog.log_reviewer.print_report") as mock_print:
                    with patch("builtins.print") as mock_builtin_print:
                        from src.nicestlog.log_reviewer import review_logs_cli

                        review_logs_cli()

                        # Should analyze both files
                        assert mock_reviewer.analyze_log_file.call_count == 2
                        assert mock_print.call_count == 2

    @patch("sys.argv", ["log_reviewer", "empty_dir/"])
    @patch("pathlib.Path.is_file", return_value=False)
    @patch("pathlib.Path.is_dir", return_value=True)
    def test_review_logs_cli_empty_directory(self, mock_is_dir, mock_is_file):
        """Test CLI with directory containing no log files."""
        with patch("pathlib.Path.glob", return_value=[]):  # No files found
            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                with patch("sys.exit") as mock_exit:
                    # Make sys.exit actually raise SystemExit to stop execution
                    mock_exit.side_effect = SystemExit(1)

                    from src.nicestlog.log_reviewer import review_logs_cli

                    with pytest.raises(SystemExit):
                        review_logs_cli()

                    mock_exit.assert_called_once_with(1)
                    assert "Keine Log-Dateien gefunden" in mock_stderr.getvalue()

    @patch("sys.argv", ["log_reviewer", "nonexistent"])
    @patch("pathlib.Path.is_file", return_value=False)
    @patch("pathlib.Path.is_dir", return_value=False)
    def test_review_logs_cli_nonexistent_path(self, mock_is_dir, mock_is_file):
        """Test CLI with nonexistent path."""
        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with patch("sys.exit") as mock_exit:
                mock_exit.side_effect = SystemExit(1)

                from src.nicestlog.log_reviewer import review_logs_cli

                with pytest.raises(SystemExit):
                    review_logs_cli()

                mock_exit.assert_called_once_with(1)
                assert "Pfad nicht gefunden" in mock_stderr.getvalue()
