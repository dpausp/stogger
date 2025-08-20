"""
Tests for the Interactive Transformer (amber-style functionality).
"""

import ast
import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest

from nicestlog.interactive_transformer import (
    InteractiveTransformer,
    TransformationProposal,
    InteractiveSession,
    UserChoice,
    transform_file_interactive,
    create_interactive_transformer,
)
from nicestlog.advanced_assistant import AdvancedAssistant


class TestInteractiveSession:
    """Test the interactive session state."""

    def test_session_initialization(self):
        """Test session initialization."""
        session = InteractiveSession()

        assert session.total_proposals == 0
        assert session.accepted == 0
        assert session.rejected == 0
        assert session.skipped_files == 0
        assert session.auto_accept_all is False
        assert session.quit_requested is False


class TestTransformationProposal:
    """Test transformation proposal structure."""

    def test_proposal_creation(self):
        """Test creating a transformation proposal."""
        proposal = TransformationProposal(
            file_path=Path("test.py"),
            line_number=10,
            original_code='print("hello")',
            transformed_code='log.info("print-output", message="hello")',
            pattern_name="print_to_structlog",
            pattern_description="Convert print to structured logging",
            context_before=["def test():", "    # Some comment"],
            context_after=["    return True"],
            node_type="Call",
        )

        assert proposal.file_path == Path("test.py")
        assert proposal.line_number == 10
        assert "print" in proposal.original_code
        assert "log.info" in proposal.transformed_code
        assert proposal.pattern_name == "print_to_structlog"


class TestInteractiveTransformer:
    """Test the main interactive transformer."""

    def test_transformer_initialization(self):
        """Test transformer initialization."""
        assistant = AdvancedAssistant()
        transformer = InteractiveTransformer(assistant, context_lines=5)

        assert transformer.assistant == assistant
        assert transformer.context_lines == 5
        assert isinstance(transformer.session, InteractiveSession)

    def test_transformer_with_default_assistant(self):
        """Test transformer with default assistant."""
        transformer = InteractiveTransformer(context_lines=2)

        assert isinstance(transformer.assistant, AdvancedAssistant)
        assert transformer.context_lines == 2

    def test_find_transformation_proposals(self):
        """Test finding transformation proposals in code."""
        code = """
def test_function():
    print("Hello, world!")
    print("Another message")
    return True
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_file = Path(f.name)

        try:
            tree = ast.parse(code)
            assistant = AdvancedAssistant()
            transformer = InteractiveTransformer(assistant)

            proposals = transformer._find_transformation_proposals(
                temp_file, tree, code
            )

            # Should find print statements
            assert len(proposals) >= 2  # At least 2 print statements

            # Check proposal structure
            for proposal in proposals:
                assert isinstance(proposal, TransformationProposal)
                assert proposal.file_path == temp_file
                assert proposal.line_number > 0
                assert "print" in proposal.original_code.lower()

        finally:
            temp_file.unlink()

    @patch("nicestlog.interactive_transformer.Prompt.ask")
    def test_present_proposal_yes(self, mock_ask):
        """Test presenting a proposal and getting YES response."""
        mock_ask.return_value = "y"

        proposal = TransformationProposal(
            file_path=Path("test.py"),
            line_number=5,
            original_code='print("test")',
            transformed_code='log.info("print-output", message="test")',
            pattern_name="print_to_structlog",
            pattern_description="Convert print to logging",
            context_before=["def func():"],
            context_after=["    return"],
            node_type="Call",
        )

        assistant = AdvancedAssistant()
        transformer = InteractiveTransformer(assistant)

        choice = transformer._present_proposal(proposal, 1, 1)

        assert choice == UserChoice.YES
        mock_ask.assert_called_once()

    @patch("nicestlog.interactive_transformer.Prompt.ask")
    def test_present_proposal_no(self, mock_ask):
        """Test presenting a proposal and getting NO response."""
        mock_ask.return_value = "n"

        proposal = TransformationProposal(
            file_path=Path("test.py"),
            line_number=5,
            original_code='print("test")',
            transformed_code='log.info("print-output", message="test")',
            pattern_name="print_to_structlog",
            pattern_description="Convert print to logging",
            context_before=[],
            context_after=[],
            node_type="Call",
        )

        assistant = AdvancedAssistant()
        transformer = InteractiveTransformer(assistant)

        choice = transformer._present_proposal(proposal, 1, 1)

        assert choice == UserChoice.NO

    @patch("nicestlog.interactive_transformer.Prompt.ask")
    def test_present_proposal_all(self, mock_ask):
        """Test presenting a proposal and getting ALL response."""
        mock_ask.return_value = "a"

        proposal = TransformationProposal(
            file_path=Path("test.py"),
            line_number=5,
            original_code='print("test")',
            transformed_code='log.info("print-output", message="test")',
            pattern_name="print_to_structlog",
            pattern_description="Convert print to logging",
            context_before=[],
            context_after=[],
            node_type="Call",
        )

        assistant = AdvancedAssistant()
        transformer = InteractiveTransformer(assistant)

        choice = transformer._present_proposal(proposal, 1, 1)

        assert choice == UserChoice.ALL

    @patch("nicestlog.interactive_transformer.Prompt.ask")
    def test_present_proposal_quit(self, mock_ask):
        """Test presenting a proposal and getting QUIT response."""
        mock_ask.return_value = "q"

        proposal = TransformationProposal(
            file_path=Path("test.py"),
            line_number=5,
            original_code='print("test")',
            transformed_code='log.info("print-output", message="test")',
            pattern_name="print_to_structlog",
            pattern_description="Convert print to logging",
            context_before=[],
            context_after=[],
            node_type="Call",
        )

        assistant = AdvancedAssistant()
        transformer = InteractiveTransformer(assistant)

        choice = transformer._present_proposal(proposal, 1, 1)

        assert choice == UserChoice.QUIT

    def test_auto_accept_all_mode(self):
        """Test auto-accept-all mode."""
        proposal = TransformationProposal(
            file_path=Path("test.py"),
            line_number=5,
            original_code='print("test")',
            transformed_code='log.info("print-output", message="test")',
            pattern_name="print_to_structlog",
            pattern_description="Convert print to logging",
            context_before=[],
            context_after=[],
            node_type="Call",
        )

        assistant = AdvancedAssistant()
        transformer = InteractiveTransformer(assistant)
        transformer.session.auto_accept_all = True

        choice = transformer._present_proposal(proposal, 1, 1)

        assert choice == UserChoice.YES

    @patch("nicestlog.interactive_transformer.Prompt.ask")
    def test_transform_file_interactive_with_mocked_input(self, mock_ask):
        """Test interactive file transformation with mocked user input."""
        mock_ask.return_value = "y"  # Accept all changes

        code = """
def test():
    print("Hello")
    return True
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_file = Path(f.name)

        try:
            assistant = AdvancedAssistant()
            transformer = InteractiveTransformer(assistant)

            result = transformer.transform_file_interactive(temp_file)

            assert result.success is True
            # Should have found and potentially transformed print statements

        finally:
            temp_file.unlink()

    def test_create_empty_result(self):
        """Test creating empty transformation result."""
        assistant = AdvancedAssistant()
        transformer = InteractiveTransformer(assistant)

        result = transformer._create_empty_result(Path("test.py"))

        assert result.success is True
        assert len(result.changes_made) == 0
        assert result.original_code == ""
        assert result.transformed_code == ""


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_create_interactive_transformer(self):
        """Test creating interactive transformer."""
        transformer = create_interactive_transformer(context_lines=5)

        assert isinstance(transformer, InteractiveTransformer)
        assert transformer.context_lines == 5
        assert isinstance(transformer.assistant, AdvancedAssistant)

    @patch("nicestlog.interactive_transformer.Prompt.ask")
    def test_transform_file_interactive_convenience(self, mock_ask):
        """Test convenience function for file transformation."""
        mock_ask.return_value = "n"  # Reject all changes

        code = """print("test")"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_file = Path(f.name)

        try:
            result = transform_file_interactive(temp_file, context_lines=2)

            assert result.success is True

        finally:
            temp_file.unlink()


class TestErrorHandling:
    """Test error handling in interactive transformer."""

    def test_transform_nonexistent_file(self):
        """Test transforming non-existent file."""
        assistant = AdvancedAssistant()
        transformer = InteractiveTransformer(assistant)

        nonexistent_file = Path("nonexistent.py")
        result = transformer.transform_file_interactive(nonexistent_file)

        # Should handle gracefully and return empty result
        assert result.success is True
        assert len(result.changes_made) == 0

    def test_transform_invalid_python_file(self):
        """Test transforming file with invalid Python syntax."""
        invalid_code = """
def invalid_function(
    # Missing closing parenthesis and colon
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(invalid_code)
            temp_file = Path(f.name)

        try:
            assistant = AdvancedAssistant()
            transformer = InteractiveTransformer(assistant)

            result = transformer.transform_file_interactive(temp_file)

            # Should handle syntax error gracefully
            assert result.success is True
            assert len(result.changes_made) == 0

        finally:
            temp_file.unlink()


class TestUserChoiceEnum:
    """Test UserChoice enum."""

    def test_user_choice_values(self):
        """Test UserChoice enum values."""
        assert UserChoice.YES.value == "y"
        assert UserChoice.NO.value == "n"
        assert UserChoice.ALL.value == "a"
        assert UserChoice.QUIT.value == "q"
        assert UserChoice.SKIP_FILE.value == "s"
        assert UserChoice.PREVIEW.value == "p"


if __name__ == "__main__":
    pytest.main([__file__])
