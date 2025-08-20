#!/usr/bin/env python3
"""
🚀 Advanced Assistant Demo - Showcase of AST Analysis and Transformation

This demo shows the powerful capabilities of the Advanced AST Assistant
with comprehensive logging of every operation.
"""

import tempfile
from pathlib import Path
import structlog

# Initialize nicestlog for beautiful output
import nicestlog
from nicestlog.advanced_assistant import (
    AdvancedAssistant,
    ASTPattern,
    NodeType,
    analyze_python_file,
    transform_python_file,
)

nicestlog.init_logging(verbose=True, syslog_identifier="advanced_assistant_demo")
log = structlog.get_logger("demo")


def create_sample_code() -> str:
    """Create sample Python code for demonstration."""
    return """
import os
import sys

def calculate_sum(a, b, c, d, e, f):  # Too many parameters!
    print("Calculating sum of", a, b, c, d, e, f)
    result = a + b + c + d + e + f
    print("Result is:", result)
    return result

class DataProcessor:
    def process_data(self, data):
        print("Processing data:", data)
        if data is None:
            print("No data to process")
            return None
        
        processed = []
        for item in data:
            if item > 0:
                processed.append(item * 2)
            else:
                print("Skipping negative item:", item)
        
        print("Processed", len(processed), "items")
        return processed
    
    def save_results(self, results, filename):
        print("Saving results to", filename)
        try:
            with open(filename, 'w') as f:
                for result in results:
                    print(result, file=f)
            print("Results saved successfully")
        except Exception as e:
            print("Error saving results:", e)

def main():
    print("Starting data processing application")
    
    processor = DataProcessor()
    data = [1, -2, 3, -4, 5, 6, 7, 8, 9, 10]
    
    print("Input data:", data)
    
    results = processor.process_data(data)
    if results:
        processor.save_results(results, "output.txt")
    
    # Calculate sum with too many parameters
    total = calculate_sum(1, 2, 3, 4, 5, 6)
    print("Total sum:", total)
    
    print("Application finished")

if __name__ == "__main__":
    main()
"""


def demo_basic_analysis():
    """Demonstrate basic file analysis."""
    log.info(
        "demo-section-started",
        _replace_msg="🔍 Demo Section: Basic File Analysis",
        section="basic_analysis",
    )

    # Create temporary file with sample code
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(create_sample_code())
        temp_file = Path(f.name)

    try:
        # Analyze the file
        log.info(
            "analyzing-sample-file",
            _replace_msg="📊 Analyzing sample file: {file_path}",
            file_path=str(temp_file),
        )

        result = analyze_python_file(temp_file)

        # Display results
        log.info(
            "analysis-results",
            _replace_msg="✅ Analysis complete - Complexity: {complexity}, Patterns: {patterns}, Issues: {issues}",
            complexity=result.complexity_score,
            patterns=len(result.detected_patterns),
            issues=len(result.potential_issues),
            node_counts=result.node_counts,
            detected_patterns=result.detected_patterns,
            potential_issues=result.potential_issues,
            transformation_suggestions=result.transformation_suggestions,
        )

    finally:
        # Cleanup
        temp_file.unlink()


def demo_transformation():
    """Demonstrate code transformation."""
    log.info(
        "demo-section-started",
        _replace_msg="🔄 Demo Section: Code Transformation",
        section="transformation",
    )

    # Create temporary file with sample code
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(create_sample_code())
        temp_file = Path(f.name)

    try:
        # Transform the file (dry run)
        log.info(
            "transforming-sample-file",
            _replace_msg="🔧 Transforming sample file: {file_path}",
            file_path=str(temp_file),
        )

        result = transform_python_file(temp_file, dry_run=True)

        # Display transformation results
        log.info(
            "transformation-results",
            _replace_msg="✅ Transformation complete - Success: {success}, Changes: {changes}",
            success=result.success,
            changes=len(result.changes_made),
            duration=result.metrics.duration,
            nodes_analyzed=result.metrics.nodes_analyzed,
            nodes_transformed=result.metrics.nodes_transformed,
            changes_made=result.changes_made,
            patterns_matched=dict(result.metrics.patterns_matched),
        )

        # Show code differences
        if result.original_code != result.transformed_code:
            log.info(
                "code-differences-detected",
                _replace_msg="📝 Code differences detected",
                original_lines=len(result.original_code.split("\n")),
                transformed_lines=len(result.transformed_code.split("\n")),
            )

            # Log first few lines of transformed code for demo
            transformed_lines = result.transformed_code.split("\n")[:10]
            log.info(
                "transformed-code-preview",
                _replace_msg="🔍 Transformed code preview (first 10 lines)",
                preview_lines=transformed_lines,
            )

    finally:
        # Cleanup
        temp_file.unlink()


def demo_custom_patterns():
    """Demonstrate custom transformation patterns."""
    log.info(
        "demo-section-started",
        _replace_msg="🎯 Demo Section: Custom Transformation Patterns",
        section="custom_patterns",
    )

    # Create an assistant with custom patterns
    assistant = AdvancedAssistant(verbose=True)

    # Add a custom pattern to detect TODO comments
    import ast

    def is_todo_comment(node: ast.AST) -> bool:
        """Detect TODO comments in string literals."""
        return (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and "TODO" in node.value.upper()
        )

    def highlight_todo(node: ast.Constant) -> ast.Constant:
        """Add emphasis to TODO comments."""
        if isinstance(node.value, str) and "TODO" in node.value.upper():
            node.value = f"🚨 {node.value} 🚨"
        return node

    todo_pattern = ASTPattern(
        name="highlight_todos",
        description="Add emphasis to TODO comments",
        node_type=NodeType.CALL,  # We'll check constants in any context
        matcher=is_todo_comment,
        transformer=highlight_todo,
        priority=1,
        enabled=True,
    )

    assistant.add_pattern(todo_pattern)

    # Create sample code with TODOs
    sample_with_todos = '''
def example_function():
    """TODO: Add proper docstring"""
    # TODO: Implement error handling
    result = "TODO: Replace with actual calculation"
    return result
'''

    # Create temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(sample_with_todos)
        temp_file = Path(f.name)

    try:
        # Transform with custom pattern
        result = assistant.transform_file(temp_file, dry_run=True)

        log.info(
            "custom-pattern-results",
            _replace_msg="🎯 Custom pattern transformation complete",
            patterns_enabled=[p.name for p in assistant.patterns if p.enabled],
            changes_made=result.changes_made,
            success=result.success,
        )

    finally:
        # Cleanup
        temp_file.unlink()


def demo_performance_metrics():
    """Demonstrate performance metrics collection."""
    log.info(
        "demo-section-started",
        _replace_msg="📊 Demo Section: Performance Metrics",
        section="performance_metrics",
    )

    # Create a larger sample file for performance testing
    large_sample = """
import os
import sys
import json
import time
from typing import List, Dict, Optional

""" + "\n".join(
        [
            f'''
def function_{i}(param1, param2, param3):
    """Function number {i}"""
    print(f"Processing function {i}")
    result = param1 + param2 + param3
    print(f"Result: {{result}}")
    return result

class Class_{i}:
    def __init__(self):
        print(f"Initializing Class_{i}")
        self.value = {i}
    
    def method_{i}(self, data):
        print(f"Method {i} processing data")
        if data:
            return data * self.value
        return 0
'''
            for i in range(20)
        ]
    )  # Create 20 functions and classes

    # Create temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(large_sample)
        temp_file = Path(f.name)

    try:
        # Analyze and transform with timing
        import time

        start_time = time.time()

        assistant = AdvancedAssistant(verbose=True)
        result = assistant.transform_file(temp_file, dry_run=True)

        end_time = time.time()
        total_duration = end_time - start_time

        log.info(
            "performance-metrics",
            _replace_msg="⚡ Performance metrics for large file transformation",
            file_size_lines=len(large_sample.split("\n")),
            total_duration=total_duration,
            analysis_duration=result.metrics.duration,
            nodes_analyzed=result.metrics.nodes_analyzed,
            nodes_transformed=result.metrics.nodes_transformed,
            analysis_rate=result.metrics.nodes_analyzed / result.metrics.duration
            if result.metrics.duration > 0
            else 0,
            patterns_matched=dict(result.metrics.patterns_matched),
            complexity_score=result.analysis.complexity_score,
        )

    finally:
        # Cleanup
        temp_file.unlink()


def main():
    """Run all demonstrations."""
    log.info(
        "demo-started",
        _replace_msg="🚀 Starting Advanced Assistant Demonstration",
        demo_version="1.0",
        features=[
            "analysis",
            "transformation",
            "custom_patterns",
            "performance_metrics",
        ],
    )

    try:
        # Run all demo sections
        demo_basic_analysis()
        demo_transformation()
        demo_custom_patterns()
        demo_performance_metrics()

        log.info(
            "demo-completed",
            _replace_msg="✅ All demonstrations completed successfully!",
            sections_completed=4,
        )

    except Exception as e:
        log.error(
            "demo-failed",
            _replace_msg="❌ Demo failed with error: {error}",
            error=str(e),
            exception_type=type(e).__name__,
        )
        raise


if __name__ == "__main__":
    main()
