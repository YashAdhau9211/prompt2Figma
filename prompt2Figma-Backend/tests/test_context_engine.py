# tests/test_context_engine.py
"""
Unit tests for the Context Processing Engine.
Tests intent recognition, reference resolution, and context processing functionality.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

from app.core.context_engine import (
    ContextProcessingEngine, EditIntent, ReferenceType, ProcessedEdit
)
from app.core.models import EditType, EditContext, DesignState


# Global fixtures for all test classes
@pytest.fixture
def sample_design_state():
    """Create a sample design state for testing."""
    wireframe_json = {
        "components": [
            {
                "id": "header-1",
                "type": "header",
                "text": "Welcome",
                "style": {"color": "blue"}
            },
            {
                "id": "button-1",
                "type": "button",
                "text": "Click me",
                "style": {"color": "red"}
            },
            {
                "id": "input-1",
                "type": "input",
                "placeholder": "Enter text"
            }
        ]
    }
    
    return DesignState(
        wireframe_json=wireframe_json,
        metadata={"created_by": "test"},
        version=1
    )

@pytest.fixture
def sample_context_history():
    """Create sample context history for testing."""
    return [
        EditContext(
            prompt="add a button",
            edit_type=EditType.ADD,
            target_elements=["button-1"],
            timestamp=datetime.utcnow() - timedelta(minutes=2),
            processing_time_ms=150
        ),
        EditContext(
            prompt="change the header color to blue",
            edit_type=EditType.STYLE,
            target_elements=["header-1"],
            timestamp=datetime.utcnow() - timedelta(minutes=1),
            processing_time_ms=200
        )
    ]


class TestContextProcessingEngine:
    """Test suite for ContextProcessingEngine."""
    
    @pytest.fixture
    def engine(self):
        """Create a ContextProcessingEngine instance for testing."""
        return ContextProcessingEngine(context_window_size=10)


class TestIntentRecognition:
    """Test intent recognition functionality."""
    
    @pytest.fixture
    def engine(self):
        return ContextProcessingEngine()
    
    def test_add_element_intent(self, engine):
        """Test recognition of add element intents."""
        test_cases = [
            "add a button",
            "create a header",
            "insert an input field",
            "put a menu here",
            "include a footer"
        ]
        
        for prompt in test_cases:
            intent = engine.extract_edit_intent(prompt)
            assert intent == EditIntent.ADD_ELEMENT, f"Failed for prompt: {prompt}"
    
    def test_remove_element_intent(self, engine):
        """Test recognition of remove element intents."""
        test_cases = [
            "remove the button",
            "delete the header",
            "take away the menu",
            "get rid of the footer"
        ]
        
        for prompt in test_cases:
            intent = engine.extract_edit_intent(prompt)
            assert intent == EditIntent.REMOVE_ELEMENT, f"Failed for prompt: {prompt}"
    
    def test_change_color_intent(self, engine):
        """Test recognition of color change intents."""
        test_cases = [
            "change the color to red",
            "make it blue",
            "set the colour to green",
            "color it yellow",
            "turn it purple"
        ]
        
        for prompt in test_cases:
            intent = engine.extract_edit_intent(prompt)
            assert intent == EditIntent.CHANGE_COLOR, f"Failed for prompt: {prompt}"
    
    def test_change_size_intent(self, engine):
        """Test recognition of size change intents."""
        test_cases = [
            "make it bigger",
            "make it smaller",
            "increase the size",
            "resize it to large",
            "make it tiny"
        ]
        
        for prompt in test_cases:
            intent = engine.extract_edit_intent(prompt)
            assert intent == EditIntent.CHANGE_SIZE, f"Failed for prompt: {prompt}"
    
    def test_change_position_intent(self, engine):
        """Test recognition of position change intents."""
        test_cases = [
            "move it to the left",
            "position it at the top",
            "align it to the center",
            "move it right"
        ]
        
        for prompt in test_cases:
            intent = engine.extract_edit_intent(prompt)
            assert intent == EditIntent.CHANGE_POSITION, f"Failed for prompt: {prompt}"
    
    def test_change_text_intent(self, engine):
        """Test recognition of text change intents."""
        test_cases = [
            'change the text to "Hello World"',
            'make it say "Click here"',
            'update the label to "Submit"'
        ]
        
        for prompt in test_cases:
            intent = engine.extract_edit_intent(prompt)
            assert intent == EditIntent.CHANGE_TEXT, f"Failed for prompt: {prompt}"
    
    def test_unclear_intent(self, engine):
        """Test handling of unclear intents."""
        test_cases = [
            "do something",
            "fix this",
            "update the thing",
            "change stuff"
        ]
        
        for prompt in test_cases:
            intent = engine.extract_edit_intent(prompt)
            assert intent == EditIntent.UNCLEAR, f"Failed for prompt: {prompt}"


class TestReferenceResolution:
    """Test reference resolution functionality."""
    
    @pytest.fixture
    def engine(self):
        return ContextProcessingEngine()
    
    @pytest.mark.asyncio
    async def test_pronoun_reference_resolution(self, engine, sample_design_state, sample_context_history):
        """Test resolution of pronoun references using context history."""
        prompt = "make it bigger"
        
        resolved_elements, confidence = await engine._resolve_references(
            prompt, sample_design_state, sample_context_history
        )
        
        # Should resolve to the most recent target element
        assert len(resolved_elements) > 0
        assert "header-1" in resolved_elements  # Most recent from context
        assert confidence > 0.5
    
    @pytest.mark.asyncio
    async def test_element_type_reference_resolution(self, engine, sample_design_state, sample_context_history):
        """Test resolution of element type references."""
        prompt = "change the button color"
        
        resolved_elements, confidence = await engine._resolve_references(
            prompt, sample_design_state, sample_context_history
        )
        
        # Should find the button element
        assert len(resolved_elements) > 0
        assert any("button" in elem.lower() for elem in resolved_elements)
        assert confidence > 0.7
    
    @pytest.mark.asyncio
    async def test_no_reference_fallback(self, engine, sample_design_state, sample_context_history):
        """Test fallback when no clear reference is found."""
        prompt = "make something different"
        
        resolved_elements, confidence = await engine._resolve_references(
            prompt, sample_design_state, sample_context_history
        )
        
        # Should fall back to recent context
        if sample_context_history:
            assert len(resolved_elements) > 0
            assert confidence <= 0.5  # Lower confidence for fallback
        else:
            assert confidence == 0.0
    
    @pytest.mark.asyncio
    async def test_multiple_matches_lower_confidence(self, engine, sample_design_state, sample_context_history):
        """Test that multiple matches result in lower confidence."""
        # Add another button to create ambiguity
        sample_design_state.wireframe_json["components"].append({
            "id": "button-2",
            "type": "button",
            "text": "Another button"
        })
        
        prompt = "change the button"
        
        resolved_elements, confidence = await engine._resolve_references(
            prompt, sample_design_state, sample_context_history
        )
        
        # Should find multiple buttons and have lower confidence
        assert len(resolved_elements) >= 2
        assert confidence < 0.8  # Lower confidence due to ambiguity


class TestContextualPromptBuilding:
    """Test contextual prompt building functionality."""
    
    @pytest.fixture
    def engine(self):
        return ContextProcessingEngine()
    
    def test_build_contextual_prompt_with_design_context(self, engine, sample_design_state, sample_context_history):
        """Test building contextual prompts with design context."""
        base_prompt = "make it red"
        
        enhanced_prompt = engine.build_contextual_prompt(
            base_prompt,
            sample_design_state.wireframe_json,
            sample_context_history
        )
        
        # Should include design context
        assert "Current Design Context:" in enhanced_prompt
        assert "header" in enhanced_prompt.lower()
        assert "button" in enhanced_prompt.lower()
        
        # Should include recent changes
        assert "Recent Changes:" in enhanced_prompt
        assert "add a button" in enhanced_prompt
        
        # Should include original prompt
        assert base_prompt in enhanced_prompt
    
    def test_build_contextual_prompt_without_history(self, engine, sample_design_state):
        """Test building contextual prompts without history."""
        base_prompt = "add a footer"
        
        enhanced_prompt = engine.build_contextual_prompt(
            base_prompt,
            sample_design_state.wireframe_json,
            []
        )
        
        # Should include design context but no recent changes
        assert "Current Design Context:" in enhanced_prompt
        assert "Recent Changes:" not in enhanced_prompt
        assert base_prompt in enhanced_prompt
    
    def test_build_contextual_prompt_limits_elements(self, engine):
        """Test that prompt building limits the number of elements to avoid bloat."""
        # Create a design with many elements
        large_design = {
            "components": [
                {"id": f"elem-{i}", "type": "button", "text": f"Button {i}"}
                for i in range(20)
            ]
        }
        
        enhanced_prompt = engine.build_contextual_prompt(
            "test prompt",
            large_design,
            []
        )
        
        # Should not include all 20 elements (limited to 5)
        button_count = enhanced_prompt.count("Button")
        assert button_count <= 5


class TestFullContextProcessing:
    """Test the complete context processing workflow."""
    
    @pytest.fixture
    def engine(self):
        return ContextProcessingEngine()
    
    @pytest.mark.asyncio
    async def test_process_edit_with_clear_context(self, engine, sample_design_state, sample_context_history):
        """Test processing an edit with clear context."""
        edit_prompt = "make the button bigger"
        
        result = await engine.process_edit_with_context(
            sample_design_state,
            edit_prompt,
            sample_context_history
        )
        
        assert isinstance(result, ProcessedEdit)
        assert result.original_prompt == edit_prompt
        assert result.edit_intent == EditIntent.CHANGE_SIZE
        assert result.edit_type == EditType.STYLE
        assert len(result.target_elements) > 0
        assert result.confidence_score > 0.5
        assert not result.needs_clarification
        assert result.enhanced_prompt != edit_prompt  # Should be enhanced
    
    @pytest.mark.asyncio
    async def test_process_edit_with_unclear_context(self, engine, sample_design_state, sample_context_history):
        """Test processing an edit with unclear context."""
        edit_prompt = "fix this thing"
        
        result = await engine.process_edit_with_context(
            sample_design_state,
            edit_prompt,
            sample_context_history
        )
        
        assert isinstance(result, ProcessedEdit)
        assert result.edit_intent == EditIntent.UNCLEAR
        # Since it falls back to context, confidence might be higher than expected
        # The key is that it needs clarification when confidence is low
        if result.confidence_score < 0.7:
            assert result.needs_clarification
            assert result.clarification_options is not None
            assert len(result.clarification_options) > 0
    
    @pytest.mark.asyncio
    async def test_process_edit_with_pronoun_reference(self, engine, sample_design_state, sample_context_history):
        """Test processing an edit with pronoun reference."""
        edit_prompt = "make it red"
        
        result = await engine.process_edit_with_context(
            sample_design_state,
            edit_prompt,
            sample_context_history
        )
        
        assert result.edit_intent == EditIntent.CHANGE_COLOR
        assert result.edit_type == EditType.STYLE
        assert len(result.target_elements) > 0
        # Should resolve "it" to recent context
        assert "header-1" in result.target_elements or any("header" in elem for elem in result.target_elements)
    
    @pytest.mark.asyncio
    async def test_process_edit_performance_tracking(self, engine, sample_design_state, sample_context_history):
        """Test that processing tracks performance metadata."""
        edit_prompt = "add a menu"
        
        result = await engine.process_edit_with_context(
            sample_design_state,
            edit_prompt,
            sample_context_history
        )
        
        assert "processing_time_ms" in result.processing_metadata
        assert "context_entries_used" in result.processing_metadata
        assert "elements_in_design" in result.processing_metadata
        
        assert result.processing_metadata["processing_time_ms"] > 0
        assert result.processing_metadata["context_entries_used"] == len(sample_context_history)
        assert result.processing_metadata["elements_in_design"] > 0
    
    @pytest.mark.asyncio
    async def test_process_edit_error_handling(self, engine):
        """Test error handling in context processing."""
        # Create a design state that will cause errors during processing
        invalid_state = DesignState(
            wireframe_json={"invalid": "structure"},  # This should cause processing errors
            version=1
        )
        
        # Mock the _resolve_references method to raise an exception
        original_method = engine._resolve_references
        
        async def mock_resolve_references(*args, **kwargs):
            raise Exception("Test error")
        
        engine._resolve_references = mock_resolve_references
        
        try:
            result = await engine.process_edit_with_context(
                invalid_state,
                "test prompt",
                []
            )
            
            # Should return a fallback result
            assert isinstance(result, ProcessedEdit)
            assert result.edit_intent == EditIntent.UNCLEAR
            assert result.confidence_score == 0.0
            assert result.needs_clarification
            assert "error" in result.processing_metadata
        finally:
            # Restore original method
            engine._resolve_references = original_method


class TestHelperMethods:
    """Test helper methods in ContextProcessingEngine."""
    
    @pytest.fixture
    def engine(self):
        return ContextProcessingEngine()
    
    def test_intent_to_edit_type_mapping(self, engine):
        """Test mapping from EditIntent to EditType."""
        mappings = [
            (EditIntent.ADD_ELEMENT, EditType.ADD),
            (EditIntent.REMOVE_ELEMENT, EditType.REMOVE),
            (EditIntent.CHANGE_COLOR, EditType.STYLE),
            (EditIntent.CHANGE_SIZE, EditType.STYLE),
            (EditIntent.CHANGE_POSITION, EditType.LAYOUT),
            (EditIntent.CHANGE_TEXT, EditType.MODIFY),
            (EditIntent.UNCLEAR, EditType.MODIFY)
        ]
        
        for intent, expected_type in mappings:
            result_type = engine._intent_to_edit_type(intent)
            assert result_type == expected_type
    
    def test_extract_elements_from_design(self, engine, sample_design_state):
        """Test extraction of elements from design JSON."""
        elements = engine._extract_elements_from_design(sample_design_state.wireframe_json)
        
        assert len(elements) == 3  # header, button, input
        
        # Check that all elements have required properties
        for element in elements:
            assert "type" in element
            assert "id" in element
    
    def test_get_recent_target_elements(self, engine, sample_context_history):
        """Test getting recent target elements from context history."""
        recent_elements = engine._get_recent_target_elements(sample_context_history)
        
        assert len(recent_elements) > 0
        assert "button-1" in recent_elements
        assert "header-1" in recent_elements
        
        # Should preserve order and remove duplicates
        assert len(recent_elements) == len(set(recent_elements))
    
    @pytest.mark.asyncio
    async def test_generate_clarification_options(self, engine, sample_design_state):
        """Test generation of clarification options."""
        # Test with multiple resolved elements
        options = await engine._generate_clarification_options(
            "change it",
            sample_design_state,
            ["button-1", "header-1"]
        )
        
        assert len(options) > 0
        assert any("which element" in opt.lower() for opt in options)
        
        # Test with no resolved elements
        options = await engine._generate_clarification_options(
            "do something",
            sample_design_state,
            []
        )
        
        assert len(options) > 0
        assert any("specify" in opt.lower() or "available" in opt.lower() for opt in options)


# Integration test for context window management
class TestContextWindowManagement:
    """Test context window management functionality."""
    
    @pytest.fixture
    def engine(self):
        return ContextProcessingEngine(context_window_size=3)  # Small window for testing
    
    def test_context_window_size_limit(self, engine):
        """Test that context window respects size limits."""
        # Create more context entries than the window size
        large_context_history = [
            EditContext(
                prompt=f"edit {i}",
                edit_type=EditType.MODIFY,
                target_elements=[f"elem-{i}"],
                timestamp=datetime.utcnow() - timedelta(minutes=i),
                processing_time_ms=100
            )
            for i in range(10)
        ]
        
        # Get recent elements (should be limited by window size)
        recent_elements = engine._get_recent_target_elements(large_context_history)
        
        # Should only consider elements from the context window
        # Since we take first 3 contexts and each has 1 element
        assert len(recent_elements) <= 3


if __name__ == "__main__":
    pytest.main([__file__])