#!/usr/bin/env python3
"""Extract log statement samples from Python projects."""
import re
import sys
from pathlib import Path


def extract_logs(project_path: str, max_per_level: int = 10):
    project = Path(project_path)
    src_path = project / "src"

    if not src_path.exists():
        print(f"No src/ directory in {project_path}")
        return

    logs = {"debug": [], "info": [], "warning": [], "error": [], "critical": [], "exception": []}

    for py_file in src_path.rglob("*.py"):
        content = py_file.read_text()
        lines = content.split("\n")

        for i, line in enumerate(lines):
            match = re.match(r"(\s+)log\.(debug|info|warning|error|critical|exception)\(", line)
            if match:
                indent = len(match.group(1))
                level = match.group(2)

                # Collect multi-line statement
                statement_lines = [line.strip()]
                paren_count = line.count("(") - line.count(")")

                j = i + 1
                while paren_count > 0 and j < len(lines):
                    next_line = lines[j]
                    if next_line.strip():  # Skip empty lines
                        statement_lines.append(next_line.strip())
                        paren_count += next_line.count("(") - next_line.count(")")
                    j += 1

                full_statement = " ".join(statement_lines)
                logs[level].append(full_statement)

    # Output
    project_name = project.name
    for level in ["debug", "info", "warning", "error", "critical", "exception"]:
        items = logs[level]
        if items:
            print(f"\n### {project_name} - {level.upper()} ({len(items)} total)")
            for item in items[:max_per_level]:
                print(f"  {item}")
            if len(items) > max_per_level:
                print(f"  ... and {len(items) - max_per_level} more")

if __name__ == "__main__":
    for project in sys.argv[1:]:
        extract_logs(project)
        print()
