# app/core/prompt_processor.py
"""
Enhanced Prompt Processor for Contextual Edits.
Integrates with Gemini AI to handle contextual prompts with design state awareness.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import google.generativeai as genai

from app.core.models import (
    EditType, EditContext, DesignState, ProcessedEdit
)
from app.core.context_engine import ContextProcessingEngine, EditIntent

logger = logging.getLogger(__name__)


class EnhancedPromptProcessor:
    """
    Enhanced prompt processor that integrates context-aware processing with Gemini AI.
    
    This class bridges the gap between the ContextProcessingEngine and the Gemini AI model,
    providing specialized prompt enhancement for iterative design edits.
    """
    
    def __init__(self):
        """Initialize the enhanced prompt processor."""
        try:
            genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        except KeyError:
            logger.error("GEMINI_API_KEY environment variable not set.")
            raise
        
        self.context_engine = ContextProcessingEngine()
        self.model = self._initialize_model()
    
    def _initialize_model(self) -> genai.GenerativeModel:
        """Initialize the Gemini model with system instructions for contextual edits."""
        system_prompt = """You are an expert UI/UX designer specializing in iterative design modifications.
Your task is to apply contextual edits to existing Figma wireframe designs based on user requests.

CRITICAL RULES:
1. You will receive the CURRENT design state as JSON and a user's edit request
2. Apply ONLY the requested changes - preserve all other elements unchanged
3. Maintain the existing structure and hierarchy unless explicitly asked to change it
4. When references like "it", "that", or "the button" are used, they refer to elements identified in the context
5. Your output MUST be the complete updated design JSON (not just the changes)
6. Ensure all components maintain proper Figma structure with required fields

RESPONSE FORMAT:
- Output ONLY the raw JSON object representing the updated design
- Do not include explanations, markdown formatting, or any other text
- Ensure the JSON is valid and complete

EDIT TYPES YOU HANDLE:
- MODIFY: Change properties of existing elements (text, size, position, etc.)
- ADD: Insert new elements into the design
- REMOVE: Delete elements from the design
- STYLE: Change visual styling (colors, fonts, borders, etc.)
- LAYOUT: Modify layout properties (spacing, alignment, positioning)

When applying edits:
- For color changes: Update backgroundColor, color, or fill properties
- For size changes: Update width, height, fontSize, or padding properties
- For position changes: Update layout properties, alignment, or positioning
- For text changes: Update text, label, or content properties in props
- For additions: Insert new components in appropriate locations
- For removals: Remove specified components while maintaining structure
"""
        
        return genai.GenerativeModel(
            'gemini-2.5-flash',
            system_instruction=system_prompt,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json"
            )
        )
    
    async def process_contextual_edit(
        self,
        current_state: DesignState,
        edit_prompt: str,
        context_history: List[EditContext]
    ) -> Tuple[Dict[str, Any], ProcessedEdit]:
        """
        Process a contextual edit and generate updated design.
        
        Args:
            current_state: Current design state
            edit_prompt: User's edit prompt
            context_history: Recent edit context history
            
        Returns:
            Tuple of (updated_wireframe_json, processed_edit_metadata)
        """
        start_time = datetime.utcnow()
        
        try:
            # Step 1: Process the edit with context engine
            processed_edit = await self.context_engine.process_edit_with_context(
                current_state, edit_prompt, context_history
            )
            
            # Step 2: Check if clarification is needed
            if processed_edit.needs_clarification:
                logger.warning(f"Edit requires clarification: {processed_edit.clarification_options}")
                # Return current state unchanged with clarification request
                return current_state.wireframe_json, processed_edit
            
            # Step 3: Build enhanced prompt for Gemini
            enhanced_prompt = self._build_gemini_prompt(
                processed_edit, current_state.wireframe_json
            )
            
            # Step 4: Call Gemini API with enhanced prompt
            logger.info(f"Calling Gemini API for contextual edit: {edit_prompt}")
            response = self.model.generate_content(enhanced_prompt)
            
            # Step 5: Parse and validate response
            updated_wireframe = json.loads(response.text)
            
            # Step 6: Validate the updated design structure
            self._validate_design_structure(updated_wireframe)
            
            # Step 7: Update processing metadata
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            processed_edit.processing_metadata["total_processing_time_ms"] = processing_time
            processed_edit.processing_metadata["gemini_call_success"] = True
            
            logger.info(f"Successfully processed contextual edit in {processing_time}ms")
            
            return updated_wireframe, processed_edit
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            raise ValueError(f"Invalid JSON response from AI model: {e}")
        except Exception as e:
            logger.error(f"Error processing contextual edit: {e}")
            raise
    
    def _build_gemini_prompt(
        self,
        processed_edit: ProcessedEdit,
        current_design: Dict[str, Any]
    ) -> str:
        """
        Build the final prompt for Gemini API with all context.
        
        Args:
            processed_edit: Processed edit with context
            current_design: Current design state JSON
            
        Returns:
            Enhanced prompt string
        """
        # Serialize current design
        current_design_str = json.dumps(current_design, indent=2)
        
        # Build context information
        context_info = []
        
        if processed_edit.target_elements:
            context_info.append(f"Target Elements: {', '.join(processed_edit.target_elements)}")
        
        context_info.append(f"Edit Type: {processed_edit.edit_type.value}")
        context_info.append(f"Edit Intent: {processed_edit.edit_intent.value}")
        
        context_str = "\n".join(context_info)
        
        # Build the complete prompt
        prompt = f"""CURRENT DESIGN STATE:
{current_design_str}

EDIT CONTEXT:
{context_str}

USER REQUEST:
{processed_edit.enhanced_prompt}

Please apply the requested edit to the design and return the complete updated design JSON.
Remember to:
1. Apply ONLY the requested changes
2. Preserve all other elements unchanged
3. Maintain proper Figma component structure
4. Ensure all required fields are present
5. Return ONLY the JSON (no explanations or markdown)
"""
        
        return prompt
    
    def _validate_design_structure(self, design: Dict[str, Any]) -> None:
        """
        Validate that the design structure is valid.
        
        Args:
            design: Design JSON to validate
            
        Raises:
            ValueError: If design structure is invalid
        """
        if not isinstance(design, dict):
            raise ValueError("Design must be a dictionary")
        
        required_fields = ["componentName", "type", "props"]
        for field in required_fields:
            if field not in design:
                raise ValueError(f"Design missing required field: {field}")
        
        # Ensure children is an array if present
        if "children" in design:
            if not isinstance(design["children"], list):
                raise ValueError("Children field must be an array")
    
    def classify_edit_type(self, prompt: str) -> EditType:
        """
        Classify the edit type from a prompt.
        
        Args:
            prompt: User's edit prompt
            
        Returns:
            EditType enum value
        """
        intent = self.context_engine.extract_edit_intent(prompt)
        return self.context_engine._intent_to_edit_type(intent)
    
    async def identify_target_elements(
        self,
        prompt: str,
        current_state: DesignState,
        context_history: List[EditContext]
    ) -> Tuple[List[str], float]:
        """
        Identify target elements from a prompt with context.
        
        Args:
            prompt: User's edit prompt
            current_state: Current design state
            context_history: Recent edit context history
            
        Returns:
            Tuple of (target_elements, confidence_score)
        """
        return await self.context_engine._resolve_references(
            prompt, current_state, context_history
        )
    
    def enhance_prompt_with_context(
        self,
        base_prompt: str,
        design_state: Dict[str, Any],
        recent_changes: List[EditContext]
    ) -> str:
        """
        Enhance a prompt with design context.
        
        Args:
            base_prompt: Original user prompt
            design_state: Current design state JSON
            recent_changes: Recent edit context history
            
        Returns:
            Enhanced prompt string
        """
        return self.context_engine.build_contextual_prompt(
            base_prompt, design_state, recent_changes
        )
