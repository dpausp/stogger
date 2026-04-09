#!/usr/bin/env python3
"""🤖 Agent Migration Demo.

This script demonstrates how AI agents can use stogger's project analysis
and migration tools to automatically retrofit existing Python projects.
"""

import json
from pathlib import Path
import subprocess
import sys
import tempfile


def create_sample_project():
    """Create a sample Python project with various logging patterns."""
    # Create temporary project directory
    project_dir = Path(tempfile.mkdtemp(prefix="agent_demo_"))

    # Create main.py with print statements
    main_py = project_dir / "main.py"
    main_py.write_text('''#!/usr/bin/env python3
"""Sample application with print-based logging."""

def process_data(items):
    print("Starting data processing...")
    print(f"Processing {len(items)} items")

    results = []
    for i, item in enumerate(items):
        if item > 0:
            results.append(item * 2)
            print(f"Processed item {i}: {item} -> {item * 2}")
        else:
            print(f"Skipping negative item: {item}")

    print(f"Processing complete. {len(results)} items processed.")
    return results

def main():
    print("Application starting...")

    data = [1, -2, 3, 4, -5, 6]
    print("Input data:", data)

    results = process_data(data)
    print("Results:", results)

    print("Application finished.")

if __name__ == "__main__":
    main()
''')

    # Create utils.py with logging module
    utils_py = project_dir / "utils.py"
    utils_py.write_text('''"""Utility functions with standard logging."""
import stogger

logger = stogger.get_logger(__name__)

def validate_input(data):
    logger.info(f"Validating input data: {data}")

    if not data:
        logger.error("No data provided")
        return False

    if not isinstance(data, list):
        logger.error(f"Expected list, got {type(data)}")
        return False

    logger.info("Input validation passed")
    return True

def save_results(results, filename):
    logger.info(f"Saving {len(results)} results to {filename}")

    try:
        with open(filename, 'w') as f:
            for result in results:
                f.write(f"{result}\\n")
        logger.info("Results saved successfully")
    except Exception as e:
        logger.error(f"Failed to save results: {e}")
        raise
''')

    # Create pyproject.toml
    pyproject_toml = project_dir / "pyproject.toml"
    pyproject_toml.write_text("""[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "sample-project"
version = "0.1.0"
dependencies = []
""")

    print(f"✅ Created sample project at: {project_dir}")
    return project_dir


def run_agent_analysis(project_dir):
    """Run agent analysis on the project."""
    print("\n🔍 Running agent analysis...")

    try:
        result = subprocess.run(
            ["uv", "run", "stoggertools", "migrate", str(project_dir), "--json"],
            capture_output=True,
            text=True,
            check=True,
        )

        # Clean output - remove any logging lines before JSON
        output_lines = result.stdout.strip().split("\n")
        json_start = -1
        for i, line in enumerate(output_lines):
            if line.strip().startswith("{"):
                json_start = i
                break

        if json_start >= 0:
            json_content = "\n".join(output_lines[json_start:])
            analysis = json.loads(json_content)
            return analysis
        else:
            print(f"❌ No JSON found in output: {result.stdout}")
            return None

    except subprocess.CalledProcessError as e:
        print(f"❌ Analysis failed: {e}")
        print(f"Error output: {e.stderr}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing failed: {e}")
        print(f"Raw output: {result.stdout}")
        return None


def display_analysis_summary(analysis):
    """Display a summary of the analysis results."""
    if not analysis:
        return

    print("\n📊 Analysis Summary:")
    print(f"  Project: {analysis['project_path']}")
    print(f"  Python files: {analysis['complexity']['python_files']}")
    print(f"  Total lines: {analysis['complexity']['total_lines']}")
    print(f"  Complexity: {analysis['complexity']['complexity_category']}")

    print("\n🎯 Recommendation:")
    rec = analysis["recommendation"]
    print(f"  Strategy: {rec['strategy']}")
    print(f"  Priority: {rec['priority']}")
    print(f"  Effort: {rec['estimated_effort']}")
    print(f"  Approach: {rec['recommended_approach']}")
    print(f"  Risk: {rec['risk_level']}")

    print("\n🔍 Logging Patterns Found:")
    pattern_counts = {}
    for pattern in analysis["logging_patterns"]:
        ptype = pattern["pattern_type"]
        pattern_counts[ptype] = pattern_counts.get(ptype, 0) + 1

    for ptype, count in pattern_counts.items():
        print(f"  {ptype}: {count} occurrences")

    if analysis["warnings"]:
        print("\n⚠️ Warnings:")
        for warning in analysis["warnings"]:
            print(f"  • {warning}")


def simulate_agent_migration(project_dir, analysis):
    """Simulate how an agent would perform the migration."""
    if not analysis:
        return False

    strategy = analysis["recommendation"]["strategy"]
    print(f"\n🤖 Agent executing migration strategy: {strategy}")

    # Step 1: Add stogger dependency
    print("  1. Adding stogger dependency...")
    pyproject_path = project_dir / "pyproject.toml"
    content = pyproject_path.read_text()

    if "dependencies = []" in content:
        new_content = content.replace(
            "dependencies = []",
            'dependencies = [\n    "stogger>=1.0.0",\n]',
        )
        pyproject_path.write_text(new_content)
        print("     ✅ Added stogger to dependencies")

    # Step 2: Add stogger configuration
    print("  2. Adding stogger configuration...")
    config = """

[tool.stogger]
verbose = true
syslog_identifier = "sample-project"
translation_dir = "translations"
language = "en"
"""
    with open(pyproject_path, "a") as f:
        f.write(config)
    print("     ✅ Added stogger configuration")

    # Step 3: Preview migration
    print("  3. Previewing migration changes...")
    try:
        result = subprocess.run(
            [
                "uv",
                "run",
                "stoggertools",
                "migrate",
                str(project_dir),
                "--type",
                strategy,
                "--dry-run",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("     ✅ Migration preview successful")
            return True
        else:
            print(f"     ❌ Migration preview failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"     ❌ Migration preview error: {e}")
        return False


def main():
    """Main demo function."""
    print("🤖 AI Agent Migration Demo")
    print("=" * 50)

    # Create sample project
    project_dir = create_sample_project()

    try:
        # Run analysis
        analysis = run_agent_analysis(project_dir)

        # Display results
        display_analysis_summary(analysis)

        # Simulate migration
        success = simulate_agent_migration(project_dir, analysis)

        if success:
            print("\n🎉 Agent migration simulation completed successfully!")
            print("\nTo see the full migration in action:")
            print(f"  cd {project_dir}")
            print(
                f"  uv run stoggertools migrate . --type {analysis['recommendation']['strategy']} --backup",
            )
        else:
            print("\n❌ Agent migration simulation failed")

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        return 1

    finally:
        # Cleanup
        import shutil

        try:
            shutil.rmtree(project_dir)
            print(f"\n🧹 Cleaned up temporary project: {project_dir}")
        except Exception:
            print(f"\n⚠️ Could not clean up: {project_dir}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
