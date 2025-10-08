# app/core/context_engine.py
"""
Context Processing Engine for the Stateful Iterative Design Engine.
Handles intent recognition, reference resolution, and contextual prompt processing.
"""

import re
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
import logging
from pydantic import BaseModel, Field

from app.core.models import (
    EditType, EditContext, DesignState, IterativeDesignError
)

logger = logging.getLogger(__name__)


class EditIntent(str, Enum):
    """Specific intents that can be extracted from edit prompts."""
    MODIFY_ELEMENT = "modify_element"
    ADD_ELEMENT = "add_element"
    REMOVE_ELEMENT = "remove_element"
    CHANGE_STYLE = "change_style"
    CHANGE_LAYOUT = "change_layout"
    CHANGE_COLOR = "change_color"
    CHANGE_SIZE = "change_size"
    CHANGE_POSITION = "change_position"
    CHANGE_TEXT = "change_text"
    UNCLEAR = "unclear"


class ReferenceType(str, Enum):
    """Types of references that can appear in prompts."""
    PRONOUN = "pronoun"  # "it", "that", "this"
    ELEMENT_TYPE = "element_type"  # "the button", "the header"
    POSITIONAL = "positional"  # "the top one", "the first button"
    RECENT = "recent"  # "the last added element"


class ProcessedEdit(BaseModel):
    """Result of processing an edit prompt with context."""
    original_prompt: str
    enhanced_prompt: str
    edit_intent: EditIntent
    edit_type: EditType
    target_elements: List[str]
    confidence_score: float
    needs_clarification: bool
    clarification_options: Optional[List[str]] = None
    processing_metadata: Dict[str, Any] = Field(default_factory=dict)


class ContextProcessingEngine:
    """
    Engine for processing edit prompts with design context and conversation history.
    
    Responsibilities:
    - Intent recognition and classification
    - Reference resolution for contextual prompts
    - Context window management
    - Prompt enhancement for AI models
    """
    
    def __init__(self, context_window_size: int = 10):
        self.context_window_size = context_window_size
        self.confidence_threshold = 0.7
        
        # Intent recognition patterns
        self._intent_patterns = self._build_intent_patterns()
        
        # Reference resolution patterns
        self._reference_patterns = self._build_reference_patterns()
        
        # Element type mappings
        self._element_types = {
            "button", "btn", "link", "header", "title", "text", "input", "field",
            "image", "img", "icon", "menu", "nav", "navigation", "sidebar", "footer",
            "card", "container", "box", "div", "section", "form", "table", "list"
        }
    
    def _build_intent_patterns(self) -> Dict[EditIntent, List[str]]:
        """Build regex patterns for intent recognition."""
        return {
            EditIntent.ADD_ELEMENT: [
                r"add\s+(?:a\s+)?(\w+)",
                r"create\s+(?:a\s+)?(\w+)",
                r"insert\s+(?:a\s+)?(\w+)",
                r"put\s+(?:a\s+)?(\w+)",
                r"include\s+(?:a\s+)?(\w+)"
            ],
            EditIntent.REMOVE_ELEMENT: [
                r"remove\s+(?:the\s+)?(\w+)",
                r"delete\s+(?:the\s+)?(\w+)",
                r"take\s+(?:away|out)\s+(?:the\s+)?(\w+)",
                r"get\s+rid\s+of\s+(?:the\s+)?(\w+)"
            ],
            EditIntent.CHANGE_COLOR: [
                r"(?:change|set)\s+(?:the\s+)?(?:color|colour)\s+(?:to\s+)?(\w+)",
                r"(?:color|colour)\s+(?:it\s+)?(\w+)",
                r"make\s+(?:it\s+)?(?:color|colour|red|blue|green|yellow|purple|orange|black|white|gray|grey)",
                r"turn\s+(?:it\s+)?(?:red|blue|green|yellow|purple|orange|black|white|gray|grey)"
            ],
            EditIntent.CHANGE_SIZE: [
                r"make\s+(?:it\s+)?(bigger|larger|smaller|tiny|huge|large|small)",
                r"(?:increase|decrease)\s+(?:the\s+)?size",
                r"resize\s+(?:it\s+)?(?:to\s+)?(\w+)"
            ],
            EditIntent.CHANGE_POSITION: [
                r"move\s+(?:it\s+)?(?:to\s+)?(?:the\s+)?(left|right|top|bottom|center|centre)",
                r"position\s+(?:it\s+)?(?:at\s+)?(?:the\s+)?(left|right|top|bottom|center|centre)",
                r"align\s+(?:it\s+)?(?:to\s+)?(?:the\s+)?(left|right|center|centre)"
            ],
            EditIntent.CHANGE_TEXT: [
                r"(?:change|update|set)\s+(?:the\s+)?text\s+to\s+[\"']([^\"']+)[\"']",
                r"make\s+(?:it\s+)?say\s+[\"']([^\"']+)[\"']",
                r"update\s+(?:the\s+)?(?:label|title|heading)\s+to\s+[\"']([^\"']+)[\"']"
            ],
            EditIntent.CHANGE_STYLE: [
                r"style\s+(?:it\s+)?(?:as\s+)?(\w+)",
                r"make\s+(?:it\s+)?(?:look\s+)?(?:more\s+)?(modern|elegant|simple|clean|fancy|professional|casual)",
                r"apply\s+(\w+)\s+style"
            ]
        }
    
    def _build_reference_patterns(self) -> Dict[ReferenceType, List[str]]:
        """Build regex patterns for reference resolution."""
        return {
            ReferenceType.PRONOUN: [
                r"\b(it|that|this)\b",
                r"\b(them|those|these)\b"
            ],
            ReferenceType.ELEMENT_TYPE: [
                r"the\s+(\w+)",
                r"that\s+(\w+)",
                r"this\s+(\w+)"
            ],
            ReferenceType.POSITIONAL: [
                r"the\s+(first|last|top|bottom|left|right)\s+(\w+)",
                r"the\s+(\w+)\s+(?:on\s+)?(?:the\s+)?(top|bottom|left|right)"
            ],
            ReferenceType.RECENT: [
                r"the\s+(?:last|latest|most\s+recent)\s+(\w+)",
                r"the\s+(\w+)\s+(?:I\s+)?(?:just\s+)?(?:added|created)"
            ]
        }
    
    async def process_edit_with_context(
        self,
        current_state: DesignState,
        edit_prompt: str,
        context_history: List[EditContext]
    ) -> ProcessedEdit:
        """
        Process an edit prompt with full context awareness.
        
        Args:
            current_state: Current design state
            edit_prompt: User's edit prompt
            context_history: Recent edit context history
            
        Returns:
            ProcessedEdit with enhanced prompt and metadata
        """
        start_time = datetime.utcnow()
        
        try:
            # Step 1: Extract basic intent
            edit_intent = self.extract_edit_intent(edit_prompt)
            edit_type = self._intent_to_edit_type(edit_intent)
            
            # Step 2: Resolve references in the prompt
            resolved_elements, confidence = await self._resolve_references(
                edit_prompt, current_state, context_history
            )
            
            # Step 3: Build enhanced prompt for AI model
            enhanced_prompt = self.build_contextual_prompt(
                edit_prompt, current_state.wireframe_json, context_history
            )
            
            # Step 4: Determine if clarification is needed
            needs_clarification = confidence < self.confidence_threshold
            clarification_options = None
            
            if needs_clarification:
                clarification_options = await self._generate_clarification_options(
                    edit_prompt, current_state, resolved_elements
                )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return ProcessedEdit(
                original_prompt=edit_prompt,
                enhanced_prompt=enhanced_prompt,
                edit_intent=edit_intent,
                edit_type=edit_type,
                target_elements=resolved_elements,
                confidence_score=confidence,
                needs_clarification=needs_clarification,
                clarification_options=clarification_options,
                processing_metadata={
                    "processing_time_ms": processing_time,
                    "context_entries_used": len(context_history),
                    "elements_in_design": len(self._extract_elements_from_design(current_state.wireframe_json))
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing edit with context: {e}")
            # Return a fallback result
            return ProcessedEdit(
                original_prompt=edit_prompt,
                enhanced_prompt=edit_prompt,
                edit_intent=EditIntent.UNCLEAR,
                edit_type=EditType.MODIFY,
                target_elements=[],
                confidence_score=0.0,
                needs_clarification=True,
                clarification_options=["Please specify which element you want to modify"],
                processing_metadata={"error": str(e)}
            )
    
    def extract_edit_intent(self, prompt: str) -> EditIntent:
        """
        Extract the primary intent from an edit prompt.
        
        Args:
            prompt: User's edit prompt
            
        Returns:
            EditIntent enum value
        """
        prompt_lower = prompt.lower().strip()
        
        # Check each intent pattern
        for intent, patterns in self._intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, prompt_lower):
                    logger.debug(f"Matched intent {intent} with pattern: {pattern}")
                    return intent
        
        # Fallback: try to infer from keywords (order matters - more specific first)
        # Check for size changes first (most specific)
        if any(word in prompt_lower for word in ["bigger", "smaller", "large", "small", "tiny", "huge"]) or "size" in prompt_lower:
            return EditIntent.CHANGE_SIZE
        # Check for text changes with quotes
        elif (any(word in prompt_lower for word in ["say", "text", "label", "title"]) and '"' in prompt) or \
             ("text" in prompt_lower and "to" in prompt_lower):
            return EditIntent.CHANGE_TEXT
        # Check for position/movement
        elif any(word in prompt_lower for word in ["move", "position", "align"]):
            return EditIntent.CHANGE_POSITION
        # Check for color changes
        elif any(word in prompt_lower for word in ["color", "colour"]):
            return EditIntent.CHANGE_COLOR
        # Check for add operations
        elif any(word in prompt_lower for word in ["add", "create", "insert", "new"]):
            return EditIntent.ADD_ELEMENT
        # Check for remove operations
        elif any(word in prompt_lower for word in ["remove", "delete", "hide"]):
            return EditIntent.REMOVE_ELEMENT
        # Check for style changes
        elif any(word in prompt_lower for word in ["style", "look", "appearance"]):
            return EditIntent.CHANGE_STYLE
        else:
            return EditIntent.UNCLEAR
    
    async def _resolve_references(
        self,
        prompt: str,
        current_state: DesignState,
        context_history: List[EditContext]
    ) -> Tuple[List[str], float]:
        """
        Resolve contextual references in the prompt to specific elements.
        
        Returns:
            Tuple of (resolved_elements, confidence_score)
        """
        prompt_lower = prompt.lower()
        resolved_elements = []
        confidence_scores = []
        
        # Extract elements from current design
        design_elements = self._extract_elements_from_design(current_state.wireframe_json)
        
        # Check for pronoun references
        pronoun_matches = []
        for ref_type, patterns in self._reference_patterns.items():
            if ref_type == ReferenceType.PRONOUN:
                for pattern in patterns:
                    matches = re.findall(pattern, prompt_lower)
                    pronoun_matches.extend(matches)
        
        if pronoun_matches:
            # Resolve pronouns using context history
            recent_elements = self._get_recent_target_elements(context_history)
            if recent_elements:
                resolved_elements.extend(recent_elements[:1])  # Take most recent
                confidence_scores.append(0.6)  # Lower confidence for pronoun resolution
        
        # Check for explicit element type references
        element_matches = []
        for ref_type, patterns in self._reference_patterns.items():
            if ref_type == ReferenceType.ELEMENT_TYPE:
                for pattern in patterns:
                    matches = re.findall(pattern, prompt_lower)
                    element_matches.extend(matches)
        
        for element_type in element_matches:
            if element_type in self._element_types:
                # Find matching elements in design
                matching_elements = [
                    elem for elem in design_elements
                    if element_type in elem.get("type", "").lower() or
                       element_type in elem.get("id", "").lower() or
                       element_type in elem.get("class", "").lower()
                ]
                
                if matching_elements:
                    # If multiple matches, prefer the most recently modified
                    if len(matching_elements) == 1:
                        resolved_elements.append(matching_elements[0].get("id", element_type))
                        confidence_scores.append(0.9)
                    else:
                        # Multiple matches - lower confidence
                        resolved_elements.extend([elem.get("id", element_type) for elem in matching_elements])
                        confidence_scores.append(0.6)
                else:
                    # Element type mentioned but not found in design
                    resolved_elements.append(element_type)
                    confidence_scores.append(0.3)
        
        # If no specific references found, try to infer from context
        if not resolved_elements and context_history:
            recent_elements = self._get_recent_target_elements(context_history)
            if recent_elements:
                resolved_elements.extend(recent_elements[:1])
                confidence_scores.append(0.4)  # Lower confidence for inference
        
        # Calculate overall confidence
        if confidence_scores:
            avg_confidence = sum(confidence_scores) / len(confidence_scores)
        else:
            avg_confidence = 0.0
        
        return resolved_elements, avg_confidence
    
    def build_contextual_prompt(
        self,
        base_prompt: str,
        design_state: Dict[str, Any],
        recent_changes: List[EditContext]
    ) -> str:
        """
        Build an enhanced prompt that includes design context for the AI model.
        
        Args:
            base_prompt: Original user prompt
            design_state: Current design state JSON
            recent_changes: Recent edit context history
            
        Returns:
            Enhanced prompt with context
        """
        context_parts = []
        
        # Add current design context
        context_parts.append("Current Design Context:")
        
        # Summarize current design elements
        elements = self._extract_elements_from_design(design_state)
        if elements:
            element_summary = []
            for elem in elements[:5]:  # Limit to avoid prompt bloat
                elem_type = elem.get("type", "element")
                elem_id = elem.get("id", "")
                elem_text = elem.get("text", elem.get("label", ""))
                
                summary = f"- {elem_type}"
                if elem_id:
                    summary += f" (id: {elem_id})"
                if elem_text:
                    summary += f": '{elem_text}'"
                
                element_summary.append(summary)
            
            context_parts.append("Elements in design:")
            context_parts.extend(element_summary)
        
        # Add recent changes context
        if recent_changes:
            context_parts.append("\nRecent Changes:")
            for i, change in enumerate(recent_changes[:3]):  # Last 3 changes
                context_parts.append(f"{i+1}. {change.prompt} (type: {change.edit_type})")
        
        # Combine context with user prompt
        context_str = "\n".join(context_parts)
        
        enhanced_prompt = f"""
{context_str}

User Request: {base_prompt}

Please apply the requested change to the design, taking into account the current elements and recent modifications. If the request refers to "it", "that", or "the [element]", use the context above to identify the correct target element.
"""
        
        return enhanced_prompt.strip()
    
    def _intent_to_edit_type(self, intent: EditIntent) -> EditType:
        """Convert EditIntent to EditType."""
        intent_mapping = {
            EditIntent.ADD_ELEMENT: EditType.ADD,
            EditIntent.REMOVE_ELEMENT: EditType.REMOVE,
            EditIntent.MODIFY_ELEMENT: EditType.MODIFY,
            EditIntent.CHANGE_STYLE: EditType.STYLE,
            EditIntent.CHANGE_COLOR: EditType.STYLE,
            EditIntent.CHANGE_SIZE: EditType.STYLE,
            EditIntent.CHANGE_TEXT: EditType.MODIFY,
            EditIntent.CHANGE_POSITION: EditType.LAYOUT,
            EditIntent.CHANGE_LAYOUT: EditType.LAYOUT,
            EditIntent.UNCLEAR: EditType.MODIFY
        }
        return intent_mapping.get(intent, EditType.MODIFY)
    
    def _extract_elements_from_design(self, design_json: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract all elements from a design JSON structure.
        
        This is a simplified implementation - in practice, you'd need to handle
        the specific structure of your wireframe JSON format.
        """
        elements = []
        
        def extract_recursive(obj, path=""):
            if isinstance(obj, dict):
                # Check if this looks like a UI element
                if any(key in obj for key in ["type", "component", "element"]):
                    elements.append(obj)
                
                # Recurse into nested structures
                for key, value in obj.items():
                    if key in ["children", "components", "elements"]:
                        if isinstance(value, list):
                            for item in value:
                                extract_recursive(item, f"{path}.{key}")
                        else:
                            extract_recursive(value, f"{path}.{key}")
            elif isinstance(obj, list):
                for item in obj:
                    extract_recursive(item, path)
        
        extract_recursive(design_json)
        return elements
    
    def _get_recent_target_elements(self, context_history: List[EditContext]) -> List[str]:
        """Get target elements from recent context history, most recent first."""
        recent_elements = []
        
        # Sort by timestamp (most recent first) and take elements
        sorted_contexts = sorted(context_history, key=lambda x: x.timestamp, reverse=True)
        
        for context in sorted_contexts[:3]:  # Last 3 contexts
            recent_elements.extend(context.target_elements)
        
        # Remove duplicates while preserving order (most recent first)
        seen = set()
        unique_elements = []
        for elem in recent_elements:
            if elem not in seen:
                seen.add(elem)
                unique_elements.append(elem)
        
        return unique_elements
    
    async def _generate_clarification_options(
        self,
        prompt: str,
        current_state: DesignState,
        resolved_elements: List[str]
    ) -> List[str]:
        """Generate clarification options when confidence is low."""
        options = []
        
        # If we found multiple potential targets
        if len(resolved_elements) > 1:
            options.append(f"Which element do you want to modify: {', '.join(resolved_elements)}?")
        
        # If no clear target found
        elif not resolved_elements:
            design_elements = self._extract_elements_from_design(current_state.wireframe_json)
            if design_elements:
                element_types = list(set(elem.get("type", "element") for elem in design_elements[:5]))
                options.append(f"Which element do you want to modify? Available: {', '.join(element_types)}")
            else:
                options.append("Please specify which element you want to modify.")
        
        # If intent is unclear
        intent = self.extract_edit_intent(prompt)
        if intent == EditIntent.UNCLEAR:
            options.append("What would you like to do? (add, remove, modify, change style, etc.)")
        
        return options if options else ["Please provide more specific details about what you want to change."]


