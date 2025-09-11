"""Log Quality Reviewer - Analyzes your logs and tells you if they're "arsch" or not.

Reviews log quality, structure, and usefulness with Austrian directness.
"""

from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any


@dataclass
class LogQualityReport:
    """Report on log quality with Austrian honesty."""

    overall_score: float  # 0-100
    overall_verdict: str  # "arsch", "verziehbar", "leiwand"
    issues: list[str]
    good_practices: list[str]
    suggestions: list[str]
    stats: dict[str, Any]


class LogQualityReviewer:
    """Reviews log quality with Austrian directness.

    Analyzes logs for structure, usefulness, and best practices.
    Gives honest feedback about whether your logs are "arsch" or not.
    """

    def __init__(self):
        self.event_patterns = []
        self.field_patterns = []
        self.bad_patterns = [
            r"debug\s*print",
            r"console\.log",
            r"System\.out\.println",
            r"print\s*\(",
        ]

        # Austrian quality levels
        self.quality_levels = {
            (90, 100): ("leiwand", "🎉 Oida, des is richtig geil! Top-Quality Logs!"),
            (70, 89): ("verziehbar", "👍 Geht scho, aber da geht noch was!"),
            (50, 69): ("mäßig", "😐 Naja, könnt besser sein..."),
            (30, 49): ("schlecht", "😬 Oag schlecht, aber nicht hoffnungslos"),
            (0, 29): ("arsch", "💩 Komplett arsch! Des ghört neu gmacht!"),
        }

    def analyze_log_file(self, file_path: Path) -> LogQualityReport:
        """Analyze a log file for quality."""
        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.splitlines()

            return self._analyze_log_lines(lines, str(file_path))
        except Exception as e:
            return LogQualityReport(
                overall_score=0,
                overall_verdict="arsch",
                issues=[f"Kann die Datei nicht lesen: {e}"],
                good_practices=[],
                suggestions=["Fix die Datei erstmal!"],
                stats={},
            )

    def analyze_log_content(self, log_content: str) -> LogQualityReport:
        """Analyze log content directly."""
        lines = log_content.splitlines()
        return self._analyze_log_lines(lines, "content")

    def _analyze_log_lines(self, lines: list[str], _: str) -> LogQualityReport:
        """Core analysis logic."""
        issues = []
        good_practices = []
        suggestions = []
        stats: dict[str, Any] = {
            "total_lines": len(lines),
            "empty_lines": 0,
            "structured_lines": 0,
            "unstructured_lines": 0,
            "levels_found": set(),
            "events_found": set(),
            "fields_found": Counter(),
            "timestamps_found": 0,
            "json_lines": 0,
            "debug_prints": 0,
        }

        # Analyze each line
        for _line_num, line in enumerate(lines, 1):
            line = line.strip()

            if not line:
                stats["empty_lines"] += 1
                continue

            # Check for timestamps
            if self._has_timestamp(line):
                stats["timestamps_found"] += 1

            # Check for log levels
            level = self._extract_log_level(line)
            if level:
                stats["levels_found"].add(level)

            # Check if structured (JSON-like)
            if self._is_structured_log(line):
                stats["structured_lines"] += 1

                # Extract fields from structured logs
                fields = self._extract_fields(line)
                for field in fields:
                    stats["fields_found"][field] += 1

                # Extract event name
                event = self._extract_event_name(line)
                if event:
                    stats["events_found"].add(event)
            else:
                stats["unstructured_lines"] += 1

            # Check for JSON
            if line.startswith("{") and line.endswith("}"):
                stats["json_lines"] += 1

            # Check for debug prints and bad practices
            for pattern in self.bad_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    stats["debug_prints"] += 1
                    break

        # Calculate scores and generate feedback
        score = self._calculate_quality_score(stats)
        verdict, verdict_msg = self._get_verdict(score)

        # Generate specific feedback
        issues.extend(self._find_issues(stats))
        good_practices.extend(self._find_good_practices(stats))
        suggestions.extend(self._generate_suggestions(stats))

        return LogQualityReport(
            overall_score=score,
            overall_verdict=verdict,
            issues=issues,
            good_practices=good_practices,
            suggestions=suggestions,
            stats=dict(stats),
        )

    def _has_timestamp(self, line: str) -> bool:
        """Check if line has a timestamp."""
        timestamp_patterns = [
            r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}",  # ISO format
            r"\d{2}:\d{2}:\d{2}",  # Time only
            r"\d{10,13}",  # Unix timestamp
        ]
        return any(re.search(pattern, line) for pattern in timestamp_patterns)

    def _extract_log_level(self, line: str) -> str | None:
        """Extract log level from line."""
        level_patterns = [
            r"\b(DEBUG|INFO|WARN|WARNING|ERROR|CRITICAL|FATAL)\b",
            r"\b([DIWECF])\b",  # Single letter levels
        ]
        for pattern in level_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return match.group(1).lower()
        return None

    def _is_structured_log(self, line: str) -> bool:
        """Check if log line is structured."""
        # JSON format
        if line.startswith("{") and line.endswith("}"):
            try:
                json.loads(line)
                return True
            except json.JSONDecodeError:
                pass

        # Key=value format
        if re.search(r"\w+=[^\s]+", line):
            return True

        # Has multiple structured fields
        field_count = len(re.findall(r"\w+[:=][^\s]+", line))
        return field_count >= 2

    def _extract_fields(self, line: str) -> list[str]:
        """Extract field names from structured log."""
        fields = []

        # JSON format
        if line.startswith("{"):
            try:
                data = json.loads(line)
                fields.extend(data.keys())
            except json.JSONDecodeError:
                pass

        # Key=value format
        for match in re.finditer(r"(\w+)[:=]", line):
            fields.append(match.group(1))

        return fields

    def _extract_event_name(self, line: str) -> str | None:
        """Extract event name from log line."""
        # Common patterns for event names
        patterns = [
            r'"event":\s*"([^"]+)"',  # JSON event field
            r"event=([^\s]+)",  # Key=value event
            r"\b(user_\w+|api_\w+|db_\w+|auth_\w+)\b",  # Common event patterns
        ]

        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                return match.group(1)

        return None

    def _calculate_quality_score(self, stats: dict[str, Any]) -> float:
        """Calculate overall quality score (0-100)."""
        if stats["total_lines"] == 0:
            return 0

        score = 0

        # Structured logging (40 points)
        if stats["total_lines"] > 0:
            structured_ratio = stats["structured_lines"] / (
                stats["total_lines"] - stats["empty_lines"]
            )
            score += structured_ratio * 40

        # Timestamp presence (20 points)
        if stats["total_lines"] > 0:
            timestamp_ratio = stats["timestamps_found"] / (
                stats["total_lines"] - stats["empty_lines"]
            )
            score += timestamp_ratio * 20

        # Log level usage (15 points)
        if len(stats["levels_found"]) >= 3:
            score += 15
        elif len(stats["levels_found"]) >= 2:
            score += 10
        elif len(stats["levels_found"]) >= 1:
            score += 5

        # Event diversity (10 points)
        if len(stats["events_found"]) >= 5:
            score += 10
        elif len(stats["events_found"]) >= 3:
            score += 7
        elif len(stats["events_found"]) >= 1:
            score += 3

        # Field usage (10 points)
        if len(stats["fields_found"]) >= 10:
            score += 10
        elif len(stats["fields_found"]) >= 5:
            score += 7
        elif len(stats["fields_found"]) >= 2:
            score += 3

        # Penalties
        if stats["debug_prints"] > 0:
            score -= min(20, stats["debug_prints"] * 2)  # -2 per debug print, max -20

        if stats["unstructured_lines"] > stats["structured_lines"]:
            score -= 15  # Penalty for mostly unstructured logs

        return max(0, min(100, score))

    def _get_verdict(self, score: float) -> tuple[str, str]:
        """Get Austrian verdict based on score."""
        for (min_score, max_score), (verdict, message) in self.quality_levels.items():
            if min_score <= score <= max_score:
                return verdict, message
        return "arsch", "💩 Komplett arsch!"

    def _find_issues(self, stats: dict[str, Any]) -> list[str]:
        """Find specific issues with the logs."""
        issues = []

        if stats["debug_prints"] > 0:
            issues.append(
                f"🚫 {stats['debug_prints']} Debug-Prints gefunden - des ghört weg!",
            )

        if stats["timestamps_found"] < stats["total_lines"] * 0.5:
            issues.append("⏰ Zu wenig Timestamps - wann is des passiert?!")

        if len(stats["levels_found"]) < 2:
            issues.append("📊 Zu wenig Log-Level - nur INFO is fad!")

        if stats["structured_lines"] < stats["unstructured_lines"]:
            issues.append("🏗️ Zu wenig strukturierte Logs - des is a Chaos!")

        if len(stats["events_found"]) < 3:
            issues.append("🎭 Zu wenig verschiedene Events - mehr Vielfalt!")

        if stats["empty_lines"] > stats["total_lines"] * 0.3:
            issues.append("📝 Zu viele leere Zeilen - des is Platzverschwendung!")

        return issues

    def _find_good_practices(self, stats: dict[str, Any]) -> list[str]:
        """Find good practices in the logs."""
        good = []

        if stats["structured_lines"] > stats["unstructured_lines"]:
            good.append("✅ Gute strukturierte Logs - so ghört sich des!")

        if stats["timestamps_found"] > stats["total_lines"] * 0.8:
            good.append("⏰ Timestamps überall - perfekt für Debugging!")

        if len(stats["levels_found"]) >= 4:
            good.append("📊 Gute Log-Level Vielfalt - alle Situationen abgedeckt!")

        if len(stats["events_found"]) >= 5:
            good.append("🎭 Viele verschiedene Events - gute Abdeckung!")

        if stats["debug_prints"] == 0:
            good.append("🚫 Keine Debug-Prints - sauber!")

        if len(stats["fields_found"]) >= 8:
            good.append("🏷️ Viele strukturierte Felder - sehr informativ!")

        return good

    def _generate_suggestions(self, stats: dict[str, Any]) -> list[str]:
        """Generate improvement suggestions."""
        suggestions = []

        if stats["structured_lines"] < stats["total_lines"] * 0.7:
            suggestions.append(
                "💡 Mehr strukturierte Logs verwenden (JSON oder key=value)",
            )

        if len(stats["levels_found"]) < 3:
            suggestions.append(
                "💡 Mehr Log-Level verwenden (DEBUG, INFO, WARNING, ERROR)",
            )

        if stats["timestamps_found"] < stats["total_lines"] * 0.8:
            suggestions.append("💡 Timestamps zu allen Logs hinzufügen")

        if len(stats["events_found"]) < 5:
            suggestions.append("💡 Mehr aussagekräftige Event-Namen verwenden")

        if "user_id" not in stats["fields_found"]:
            suggestions.append(
                "💡 User-Kontext zu Logs hinzufügen (user_id, session_id)",
            )

        if "request_id" not in stats["fields_found"]:
            suggestions.append("💡 Request-Tracing mit request_id implementieren")

        if stats["debug_prints"] > 0:
            suggestions.append("💡 Debug-Prints durch proper Logging ersetzen")

        return suggestions


def review_logs_cli():
    """CLI interface for log review."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Log Quality Reviewer - tells you if your logs are 'arsch' or not",
        epilog="Austrian honesty included! 🇦🇹",
    )
    parser.add_argument("path", help="Log file or directory to review")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=70,
        help="Minimum acceptable score (default: 70)",
    )

    args = parser.parse_args()

    reviewer = LogQualityReviewer()
    path = Path(args.path)

    if path.is_file():
        report = reviewer.analyze_log_file(path)
        print_report(report, args.format)

        if report.overall_score < args.min_score:
            sys.exit(1)

    elif path.is_dir():
        log_files = list(path.glob("*.log")) + list(path.glob("*.txt"))
        if not log_files:
            sys.exit(1)

        total_score = 0
        for log_file in log_files:
            report = reviewer.analyze_log_file(log_file)
            print_report(report, args.format)
            total_score += report.overall_score

        avg_score = total_score / len(log_files)

        if avg_score < args.min_score:
            sys.exit(1)

    else:
        sys.exit(1)


def print_report(report: LogQualityReport, format_type: str = "text"):
    """Print the quality report."""
    if format_type == "json":
        return

    # Text format with Austrian flair



    if report.issues:
        for _issue in report.issues:
            pass

    if report.good_practices:
        for _practice in report.good_practices:
            pass

    if report.suggestions:
        for _suggestion in report.suggestions:
            pass



if __name__ == "__main__":
    review_logs_cli()
