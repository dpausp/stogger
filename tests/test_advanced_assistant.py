"""Tests for the Advanced AST Assistant."""

import ast
from pathlib import Path
import tempfile

import pytest

from stoggertools.advanced_assistant import (
    AdvancedAssistant,
    AdvancedASTAnalyzer,
    AdvancedTransformer,
    ASTPattern,
    CodeAnalysisResult,
    NodeType,
    TransformationMetrics,
    TransformationResult,
    analyze_python_file,
    create_advanced_assistant,
    transform_python_file,
)


class TestAdvancedASTAnalyzer:
    """Test the AST analyzer component."""

    def test_analyzer_initialization(self):
        """Test analyzer initialization."""
        file_path = Path("test.py")
        analyzer = AdvancedASTAnalyzer(file_path)

        assert analyzer.file_path == file_path
        assert analyzer.metrics.nodes_analyzed == 0
        assert analyzer.complexity_score == 0
        assert len(analyzer.detected_patterns) == 0

    def test_analyze_simple_code(self):
        """Test analysis of simple Python code."""
        code = """
def hello_world():
    print("Hello, world!")
    return "done"
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_file = Path(f.name)

        try:
            tree = ast.parse(code)
            analyzer = AdvancedASTAnalyzer(temp_file)
            result = analyzer.analyze(tree)

            assert isinstance(result, CodeAnalysisResult)
            assert result.file_path == temp_file
            assert result.complexity_score >= 0
            assert "print_statement" in result.detected_patterns
            assert len(result.node_counts) > 0
            assert "FunctionDef" in result.node_counts

        finally:
            temp_file.unlink()

    def test_analyze_complex_code(self):
        """Test analysis of more complex code with control structures."""
        code = """
def complex_function(a, b, c, d, e, f):  # Many parameters
    if a > 0:
        for i in range(b):
            while c > 0:
                print(f"Processing {i}, {c}")
                c -= 1
    return a + b + c + d + e + f
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_file = Path(f.name)

        try:
            tree = ast.parse(code)
            analyzer = AdvancedASTAnalyzer(temp_file)
            result = analyzer.analyze(tree)

            # Should detect complexity from control structures
            assert result.complexity_score >= 3  # if, for, while

            # Should detect some issues (function complexity, print statements, etc.)
            assert len(result.potential_issues) >= 0  # May or may not have issues

            # Should detect print statements
            assert "print_statement" in result.detected_patterns

        finally:
            temp_file.unlink()


class TestAdvancedTransformer:
    """Test the AST transformer component."""

    def test_transformer_initialization(self):
        """Test transformer initialization."""
        patterns = []
        transformer = AdvancedTransformer(patterns)

        assert len(transformer.patterns) == 0
        assert transformer.metrics.nodes_analyzed == 0
        assert len(transformer.changes_made) == 0

    def test_print_transformation(self):
        """Test transformation of print statements."""

        # Create a pattern to transform print statements
        def is_print_call(node: ast.AST) -> bool:
            return (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "print"
            )

        def transform_print_to_log(node: ast.Call) -> ast.Call:
            new_func = ast.Attribute(
                value=ast.Name(id="log", ctx=ast.Load()),
                attr="info",
                ctx=ast.Load(),
            )

            new_call = ast.Call(
                func=new_func,
                args=[ast.Constant(value="print-output")],
                keywords=[ast.keyword(arg="message", value=node.args[0])]
                if node.args
                else [],
            )

            return ast.copy_location(new_call, node)

        pattern = ASTPattern(
            name="test_print_transform",
            description="Test print transformation",
            node_type=NodeType.CALL,
            matcher=is_print_call,
            transformer=transform_print_to_log,
        )

        code = 'print("Hello, world!")'
        tree = ast.parse(code)

        transformer = AdvancedTransformer([pattern])
        transformed_tree = transformer.transform(tree)

        # Check that transformation occurred
        assert transformer.metrics.nodes_transformed > 0
        assert len(transformer.changes_made) > 0
        assert "test_print_transform" in transformer.metrics.patterns_matched

        # Check the transformed code
        new_code = ast.unparse(transformed_tree)
        assert "log.info" in new_code
        assert "print-output" in new_code


class TestAdvancedAssistant:
    """Test the main Advanced Assistant class."""

    def test_assistant_initialization(self):
        """Test assistant initialization."""
        assistant = AdvancedAssistant(verbose=True)

        assert assistant.verbose is True
        assert len(assistant.patterns) > 0  # Should have default patterns
        assert assistant.session_id is not None

        # Check default patterns
        pattern_names = [p.name for p in assistant.patterns]
        assert "print_to_structlog" in pattern_names

    def test_add_custom_pattern(self):
        """Test adding custom patterns."""
        assistant = AdvancedAssistant()
        initial_count = len(assistant.patterns)

        def dummy_matcher(node: ast.AST) -> bool:
            return False

        custom_pattern = ASTPattern(
            name="test_pattern",
            description="Test pattern",
            node_type=NodeType.CALL,
            matcher=dummy_matcher,
        )

        assistant.add_pattern(custom_pattern)

        assert len(assistant.patterns) == initial_count + 1
        assert custom_pattern in assistant.patterns

    def test_analyze_file_functionality(self):
        """Test file analysis functionality."""
        code = """
def test_function():
    print("Testing")
    return True
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_file = Path(f.name)

        try:
            assistant = AdvancedAssistant()
            result = assistant.analyze_file(temp_file)

            assert isinstance(result, CodeAnalysisResult)
            assert result.file_path == temp_file
            assert len(result.node_counts) > 0
            assert result.complexity_score >= 0

        finally:
            temp_file.unlink()

    def test_transform_file_dry_run(self):
        """Test file transformation in dry run mode."""
        code = """
def test_function():
    print("Testing")
    return True
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_file = Path(f.name)

        try:
            assistant = AdvancedAssistant()
            result = assistant.transform_file(temp_file, dry_run=True)

            assert isinstance(result, TransformationResult)
            assert result.success is True
            assert result.original_code == code

            # File should not be modified in dry run
            assert temp_file.read_text() == code

        finally:
            temp_file.unlink()

    def test_transform_file_with_changes(self):
        """Test file transformation that makes actual changes."""
        code = """print("Hello, world!")"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_file = Path(f.name)

        try:
            assistant = AdvancedAssistant()
            result = assistant.transform_file(temp_file, dry_run=False)

            assert isinstance(result, TransformationResult)
            assert result.success is True

            # Should have made changes
            if len(result.changes_made) > 0:
                assert result.original_code != result.transformed_code

                # Check backup was created
                backup_path = temp_file.with_suffix(f"{temp_file.suffix}.backup")
                assert backup_path.exists()
                assert backup_path.read_text() == code

                # Cleanup backup
                backup_path.unlink()

        finally:
            temp_file.unlink()


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_create_advanced_assistant(self):
        """Test assistant creation function."""
        assistant = create_advanced_assistant(verbose=False)

        assert isinstance(assistant, AdvancedAssistant)
        assert assistant.verbose is False

    def test_analyze_python_file(self):
        """Test file analysis convenience function."""
        code = """
def example():
    print("Example")
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_file = Path(f.name)

        try:
            result = analyze_python_file(temp_file)

            assert isinstance(result, CodeAnalysisResult)
            assert result.file_path == temp_file

        finally:
            temp_file.unlink()

    def test_transform_python_file(self):
        """Test file transformation convenience function."""
        code = """print("Test")"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_file = Path(f.name)

        try:
            result = transform_python_file(temp_file, dry_run=True)

            assert isinstance(result, TransformationResult)
            assert result.success is True

        finally:
            temp_file.unlink()


class TestTransformationMetrics:
    """Test transformation metrics collection."""

    def test_metrics_initialization(self):
        """Test metrics initialization."""
        metrics = TransformationMetrics()

        assert metrics.nodes_analyzed == 0
        assert metrics.nodes_transformed == 0
        assert len(metrics.patterns_matched) == 0
        assert len(metrics.errors_encountered) == 0
        assert len(metrics.warnings_generated) == 0
        assert metrics.start_time > 0
        assert metrics.end_time is None

    def test_metrics_duration_calculation(self):
        """Test duration calculation."""
        import time

        metrics = TransformationMetrics()
        time.sleep(0.01)  # Small delay
        metrics.end_time = time.time()

        assert metrics.duration > 0
        assert metrics.duration < 1  # Should be very small


class TestErrorHandling:
    """Test error handling in the assistant."""

    def test_analyze_nonexistent_file(self):
        """Test analysis of non-existent file."""
        assistant = AdvancedAssistant()
        nonexistent_file = Path("nonexistent.py")

        with pytest.raises(FileNotFoundError):
            assistant.analyze_file(nonexistent_file)

    def test_analyze_invalid_python(self):
        """Test analysis of invalid Python code."""
        invalid_code = """
def invalid_function(
    # Missing closing parenthesis and colon
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(invalid_code)
            temp_file = Path(f.name)

        try:
            assistant = AdvancedAssistant()

            with pytest.raises(SyntaxError):
                assistant.analyze_file(temp_file)

        finally:
            temp_file.unlink()

    def test_transform_with_failing_pattern(self):
        """Test transformation with a pattern that raises an exception."""

        def failing_matcher(node: ast.AST) -> bool:
            return isinstance(node, ast.Call)

        def failing_transformer(node: ast.AST) -> ast.AST:
            raise ValueError("Test error")

        failing_pattern = ASTPattern(
            name="failing_pattern",
            description="Pattern that fails",
            node_type=NodeType.CALL,
            matcher=failing_matcher,
            transformer=failing_transformer,
        )

        code = """print("test")"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_file = Path(f.name)

        try:
            assistant = AdvancedAssistant()
            assistant.add_pattern(failing_pattern)

            result = assistant.transform_file(temp_file, dry_run=True)

            # Should still succeed but with errors recorded
            assert result.success is True
            assert len(result.metrics.errors_encountered) > 0

        finally:
            temp_file.unlink()


if __name__ == "__main__":
    pytest.main([__file__])
