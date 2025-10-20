# tests/test_prompt_processor.py
"""
Unit tests for the Enhanced Prompt Processor.
Tests contextual prompt generation, edit type classification, and target element identification.
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any

from app.core.prompt_processor import EnhancedPromptProcessor
from app.core.models import (
    DesignState, EditContext, EditType, EditIntent, ProcessedEdit
)


@pytest.fixture
def sample_design_state():
    """Create a sample design state for testing."""
    return DesignState(
        wireframe_json={
            "componentName": "AppContainer",
            "type": "Frame",
            "props": {
                "layoutMode": "VERTICAL",
                "backgroundColor": "#FFFFFF",
                "padding": "16px"
            },
            "children": [
                {
                    "componentName": "Header",
                    "type": "Frame",
                    "props": {
                        "layoutMode": "HORIZONTAL",
                        "backgroundColor": "#F0F0F0"
                    },
                    "children": [
                        {
                            "componentName": "Title",
                            "type": "Text",
                            "props": {
                                "text": "Welcome",
                                "fontSize": "24px",
                                "fontWeight": 700
                            },
                            "children": []
                        }
                    ]
                },
                {
                    "componentName": "SubmitButton",
                    "type": "Button",
                    "props": {
                        "text": "Submit",
                        "backgroundColor": "#007BFF",
                        "color": "#FFFFFF"
                    },
                    "children": []
                }
            ]
        },
        metadata={"created_by": "test_user"},
        version=1
    )


@pytest.fixture
def sample_context_history():
    """Create sample context history for testing."""
    return [
        EditContext(
            prompt="Add a button",
            edit_type=EditType.ADD,
            target_elements=["SubmitButton"],
            timestamp=datetime.utcnow(),
            processing_time_ms=150
        ),
        EditContext(
            prompt="Change the title text",
            edit_type=EditType.MODIFY,
            target_elements=["Title"],
            timestamp=datetime.utcnow(),
            processing_time_ms=120
        )
    ]


@pytest.fixture
def mock_genai_model():
    """Create a mock Gemini AI model."""
    with patch('app.core.prompt_processor.genai') as mock_genai:
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "componentName": "AppContainer",
            "type": "Frame",
            "props": {"backgroundColor": "#FFFFFF"},
            "children": []
        })
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.configure = MagicMock()
        mock_genai.types.GenerationConfig = MagicMock()
        yield mock_genai


class TestEnhancedPromptProcessor:
    """Test suite for EnhancedPromptProcessor."""
    
    def test_initialization(self, mock_genai_model):
        """Test that the processor initializes correctly."""
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'}):
            processor = EnhancedPromptProcessor()
            assert processor.context_engine is not None
            assert processor.model is not None
    
    def test_initialization_without_api_key(self):
        """Test that initialization fails without API key."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(KeyError):
                EnhancedPromptProcessor()
    
    def test_classify_edit_type_color_change(self, mock_genai_model):
        """Test edit type classification for color changes."""
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'}):
            processor = EnhancedPromptProcessor()
            
            edit_type = processor.classify_edit_type("change the color to blue")
            assert edit_type == EditType.STYLE
            
            edit_type = processor.classify_edit_type("make it red")
            assert edit_type == EditType.STYLE
    
    def test_classify_edit_type_size_change(self, mock_genai_model):
        """Test edit type classification for size changes."""
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'}):
            processor = EnhancedPromptProcessor()
            
            edit_type = processor.classify_edit_type("make it bigger")
            assert edit_type == EditType.STYLE
            
            edit_type = processor.classify_edit_type("increase the size")
            assert edit_type == EditType.STYLE
    
    def test_classify_edit_type_add_element(self, mock_genai_model):
        """Test edit type classification for adding elements."""
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'}):
            processor = EnhancedPromptProcessor()
            
            edit_type = processor.classify_edit_type("add a button")
            assert edit_type == EditType.ADD
            
            edit_type = processor.classify_edit_type("create a new header")
            assert edit_type == EditType.ADD
    
    def test_classify_edit_type_remove_element(self, mock_genai_model):
        """Test edit type classification for removing elements."""
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'}):
            processor = EnhancedPromptProcessor()
            
            edit_type = processor.classify_edit_type("remove the button")
            assert edit_type == EditType.REMOVE
            
            edit_type = processor.classify_edit_type("delete the header")
            assert edit_type == EditType.REMOVE
    
    def test_classify_edit_type_position_change(self, mock_genai_model):
        """Test edit type classification for position changes."""
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'}):
            processor = EnhancedPromptProcessor()
            
            edit_type = processor.classify_edit_type("move it to the left")
            assert edit_type == EditType.LAYOUT
            
            edit_type = processor.classify_edit_type("align it to the center")
            assert edit_type == EditType.LAYOUT
    
    @pytest.mark.asyncio
    async def test_identify_target_elements_explicit(
        self, mock_genai_model, sample_design_state, sample_context_history
    ):
        """Test target element identification with explicit references."""
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'}):
            processor = EnhancedPromptProcessor()
            
            elements, confidence = await processor.identify_target_elements(
                "change the button color",
                sample_design_state,
                sample_context_history
            )
            
            assert len(elements) > 0
            assert confidence > 0.0
    
    @pytest.mark.asyncio
    async def test_identify_target_elements_pronoun(
        self, mock_genai_model, sample_design_state, sample_context_history
    ):
        """Test target element identification with pronoun references."""
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'}):
            processor = EnhancedPromptProcessor()
            
            elements, confidence = await processor.identify_target_elements(
                "make it bigger",
                sample_design_state,
                sample_context_history
            )
            
            # Should resolve to the most recent target element
            assert len(elements) > 0
            # Confidence should be lower for pronoun resolution
            assert confidence < 1.0
    
    def test_enhance_prompt_with_context(
        self, mock_genai_model, sample_design_state, sample_context_history
    ):
        """Test prompt enhancement with design context."""
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'}):
            processor = EnhancedPromptProcessor()
            
            enhanced = processor.enhance_prompt_with_context(
                "change the color to blue",
                sample_design_state.wireframe_json,
                sample_context_history
            )
            
            # Enhanced prompt should contain context information
            assert "Current Design Context" in enhanced
            assert "Recent Changes" in enhanced
            assert "change the color to blue" in enhanced
    
    def test_build_gemini_prompt(self, mock_genai_model, sample_design_state):
        """Test building the Gemini API prompt."""
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'}):
            processor = EnhancedPromptProcessor()
            
            processed_edit = ProcessedEdit(
                original_prompt="make it blue",
                enhanced_prompt="change the button color to blue",
                edit_intent=EditIntent.CHANGE_COLOR,
                edit_type=EditType.STYLE,
                target_elements=["SubmitButton"],
                confidence_score=0.9,
                needs_clarification=False
            )
            
            prompt = processor._build_gemini_prompt(
                processed_edit,
                sample_design_state.wireframe_json
            )
            
            # Prompt should contain all necessary information
            assert "CURRENT DESIGN STATE" in prompt
            assert "EDIT CONTEXT" in prompt
            assert "USER REQUEST" in prompt
            assert "SubmitButton" in prompt
            assert "style" in prompt.lower()
    
    def test_validate_design_structure_valid(self, mock_genai_model):
        """Test design structure validation with valid design."""
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'}):
            processor = EnhancedPromptProcessor()
            
            valid_design = {
                "componentName": "Test",
                "type": "Frame",
                "props": {},
                "children": []
            }
            
            # Should not raise any exception
            processor._validate_design_structure(valid_design)
    
    def test_validate_design_structure_missing_fields(self, mock_genai_model):
        """Test design structure validation with missing fields."""
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'}):
            processor = EnhancedPromptProcessor()
            
            invalid_design = {
                "componentName": "Test"
                # Missing type and props
            }
            
            with pytest.raises(ValueError, match="missing required field"):
                processor._validate_design_structure(invalid_design)
    
    def test_validate_design_structure_invalid_children(self, mock_genai_model):
        """Test design structure validation with invalid children."""
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'}):
            processor = EnhancedPromptProcessor()
            
            invalid_design = {
                "componentName": "Test",
                "type": "Frame",
                "props": {},
                "children": "not an array"  # Should be an array
            }
            
            with pytest.raises(ValueError, match="must be an array"):
                processor._validate_design_structure(invalid_design)
    
    @pytest.mark.asyncio
    async def test_process_contextual_edit_success(
        self, mock_genai_model, sample_design_state, sample_context_history
    ):
        """Test successful contextual edit processing."""
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'}):
            processor = EnhancedPromptProcessor()
            
            updated_wireframe, processed_edit = await processor.process_contextual_edit(
                sample_design_state,
                "change the button color to blue",
                sample_context_history
            )
            
            # Should return updated wireframe
            assert updated_wireframe is not None
            assert isinstance(updated_wireframe, dict)
            
            # Should return processed edit metadata
            assert processed_edit.original_prompt == "change the button color to blue"
            assert processed_edit.edit_type == EditType.STYLE
            assert not processed_edit.needs_clarification
    
    @pytest.mark.asyncio
    async def test_process_contextual_edit_needs_clarification(
        self, mock_genai_model, sample_design_state, sample_context_history
    ):
        """Test contextual edit processing when clarification is needed."""
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'}):
            processor = EnhancedPromptProcessor()
            
            # Mock the context engine to return low confidence
            with patch.object(
                processor.context_engine,
                'process_edit_with_context',
                return_value=ProcessedEdit(
                    original_prompt="change it",
                    enhanced_prompt="change it",
                    edit_intent=EditIntent.UNCLEAR,
                    edit_type=EditType.MODIFY,
                    target_elements=[],
                    confidence_score=0.3,
                    needs_clarification=True,
                    clarification_options=["What would you like to change?"]
                )
            ):
                updated_wireframe, processed_edit = await processor.process_contextual_edit(
                    sample_design_state,
                    "change it",
                    sample_context_history
                )
                
                # Should return current state unchanged
                assert updated_wireframe == sample_design_state.wireframe_json
                
                # Should indicate clarification is needed
                assert processed_edit.needs_clarification
                assert processed_edit.clarification_options is not None
    
    @pytest.mark.asyncio
    async def test_process_contextual_edit_invalid_json_response(
        self, mock_genai_model, sample_design_state, sample_context_history
    ):
        """Test handling of invalid JSON response from Gemini."""
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'}):
            processor = EnhancedPromptProcessor()
            
            # Mock the context engine to return high confidence (so it proceeds to Gemini call)
            with patch.object(
                processor.context_engine,
                'process_edit_with_context',
                return_value=ProcessedEdit(
                    original_prompt="change the color",
                    enhanced_prompt="change the button color to red",
                    edit_intent=EditIntent.CHANGE_COLOR,
                    edit_type=EditType.STYLE,
                    target_elements=["SubmitButton"],
                    confidence_score=0.9,
                    needs_clarification=False
                )
            ):
                # Mock the model to return invalid JSON
                processor.model.generate_content = MagicMock(
                    return_value=MagicMock(text="not valid json")
                )
                
                with pytest.raises(ValueError, match="Invalid JSON response"):
                    await processor.process_contextual_edit(
                        sample_design_state,
                        "change the color",
                        sample_context_history
                    )


class TestPromptEnhancementIntegration:
    """Integration tests for prompt enhancement with context engine."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_color_change(
        self, mock_genai_model, sample_design_state, sample_context_history
    ):
        """Test end-to-end processing of a color change request."""
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'}):
            processor = EnhancedPromptProcessor()
            
            # Mock successful Gemini response
            updated_design = sample_design_state.wireframe_json.copy()
            updated_design["children"][1]["props"]["backgroundColor"] = "#0000FF"
            
            processor.model.generate_content = MagicMock(
                return_value=MagicMock(text=json.dumps(updated_design))
            )
            
            updated_wireframe, processed_edit = await processor.process_contextual_edit(
                sample_design_state,
                "change the button color to blue",
                sample_context_history
            )
            
            # Verify the edit was processed correctly
            assert processed_edit.edit_type == EditType.STYLE
            assert processed_edit.edit_intent == EditIntent.CHANGE_COLOR
            assert not processed_edit.needs_clarification
            
            # Verify the wireframe was updated
            assert updated_wireframe["children"][1]["props"]["backgroundColor"] == "#0000FF"
    
    @pytest.mark.asyncio
    async def test_end_to_end_contextual_reference(
        self, mock_genai_model, sample_design_state, sample_context_history
    ):
        """Test end-to-end processing with contextual reference (it)."""
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'}):
            processor = EnhancedPromptProcessor()
            
            # Mock successful Gemini response
            updated_design = sample_design_state.wireframe_json.copy()
            updated_design["children"][0]["children"][0]["props"]["fontSize"] = "32px"
            
            processor.model.generate_content = MagicMock(
                return_value=MagicMock(text=json.dumps(updated_design))
            )
            
            updated_wireframe, processed_edit = await processor.process_contextual_edit(
                sample_design_state,
                "make it bigger",
                sample_context_history
            )
            
            # Verify the edit was processed
            assert processed_edit.edit_type == EditType.STYLE
            assert processed_edit.edit_intent == EditIntent.CHANGE_SIZE
            
            # Should have resolved "it" to a target element
            assert len(processed_edit.target_elements) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
