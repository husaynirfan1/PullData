"""Tests for reasoning tag stripping functionality."""

import pytest

from pulldata.synthesis import strip_reasoning_tags


class TestStripReasoningTags:
    """Test cases for strip_reasoning_tags function."""

    def test_strip_think_tags(self):
        """Test stripping <think> tags."""
        text = "Answer: 42 <think>Let me verify this calculation...</think>"
        result = strip_reasoning_tags(text)
        assert result == "Answer: 42"

    def test_strip_thinking_tags(self):
        """Test stripping <thinking> tags."""
        text = "<thinking>Working through the problem...</thinking>The result is 5"
        result = strip_reasoning_tags(text)
        assert result == "The result is 5"

    def test_strip_multiple_tags(self):
        """Test stripping multiple reasoning tags."""
        text = """<thinking>Let me analyze this...</thinking>
        The answer is correct.
        <think>Double checking...</think>
        Yes, confirmed."""
        result = strip_reasoning_tags(text)
        assert "<thinking>" not in result
        assert "<think>" not in result
        assert "The answer is correct" in result
        assert "Yes, confirmed" in result

    def test_strip_multiline_tags(self):
        """Test stripping tags that span multiple lines."""
        text = """Here is the answer:
        <think>
        Let me work through this step by step:
        1. First step
        2. Second step
        3. Third step
        </think>
        The final result is 42."""
        result = strip_reasoning_tags(text)
        assert "<think>" not in result
        assert "First step" not in result
        assert "The final result is 42" in result

    def test_strip_reflection_tags(self):
        """Test stripping <reflection> tags."""
        text = "Answer: Yes <reflection>This seems correct</reflection>"
        result = strip_reasoning_tags(text)
        assert result == "Answer: Yes"

    def test_strip_analysis_tags(self):
        """Test stripping <analysis> tags."""
        text = "<analysis>Breaking down the problem...</analysis>The solution is simple."
        result = strip_reasoning_tags(text)
        assert result == "The solution is simple."

    def test_strip_scratchpad_tags(self):
        """Test stripping <scratchpad> tags."""
        text = "Final answer: 100 <scratchpad>100 = 10 * 10</scratchpad>"
        result = strip_reasoning_tags(text)
        assert result == "Final answer: 100"

    def test_case_insensitive(self):
        """Test that tag removal is case-insensitive."""
        text = "Answer: Yes <THINK>checking</THINK> <Think>verifying</Think>"
        result = strip_reasoning_tags(text)
        assert result == "Answer: Yes"

    def test_no_tags_unchanged(self):
        """Test that text without tags is unchanged."""
        text = "This is a simple answer with no reasoning tags."
        result = strip_reasoning_tags(text)
        assert result == text

    def test_empty_string(self):
        """Test handling of empty string."""
        result = strip_reasoning_tags("")
        assert result == ""

    def test_none_input(self):
        """Test handling of None input."""
        result = strip_reasoning_tags(None)
        assert result is None

    def test_clean_up_whitespace(self):
        """Test that excessive whitespace is cleaned up."""
        text = """First line.


        <think>removed</think>


        Second line."""
        result = strip_reasoning_tags(text)
        # Should reduce excessive newlines
        assert "\n\n\n" not in result
        assert "First line" in result
        assert "Second line" in result

    def test_nested_tags_not_supported(self):
        """Test behavior with nested tags (not expected in practice)."""
        text = "<think>outer <think>inner</think></think>Answer"
        result = strip_reasoning_tags(text)
        # With non-greedy matching, this should work correctly
        assert "Answer" in result
        assert "<think>" not in result

    def test_real_world_example(self):
        """Test with a realistic LLM response."""
        text = """<thinking>
        Let me analyze the document content:
        - The document discusses revenue trends
        - Key figure is $10.5M
        - This represents a 15% increase
        </thinking>

        Based on the Q3 financial report, total revenue was $10.5M, representing a 15% increase year-over-year.

        <think>This answer looks complete and accurate.</think>

        Key highlights:
        - Revenue: $10.5M
        - Growth: 15% YoY
        - Trend: Positive momentum"""

        result = strip_reasoning_tags(text)

        # Check reasoning is removed
        assert "<thinking>" not in result
        assert "<think>" not in result
        assert "Let me analyze" not in result
        assert "This answer looks complete" not in result

        # Check content is preserved
        assert "Based on the Q3 financial report" in result
        assert "total revenue was $10.5M" in result
        assert "Key highlights" in result
        assert "Revenue: $10.5M" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
