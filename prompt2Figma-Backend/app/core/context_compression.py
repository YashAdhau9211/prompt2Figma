# app/core/context_compression.py
"""
Context window compression utilities for efficient storage and processing.
Implements compression strategies to manage large context histories.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.core.models import EditContext, EditType

logger = logging.getLogger(__name__)


class ContextCompressionStrategy:
    """Base class for context compression strategies."""
    
    def compress(self, contexts: List[EditContext]) -> List[EditContext]:
        """Compress a list of contexts."""
        raise NotImplementedError


class WindowLimitStrategy(ContextCompressionStrategy):
    """Simple strategy that limits context to a fixed window size."""
    
    def __init__(self, max_size: int = 10):
        self.max_size = max_size
    
    def compress(self, contexts: List[EditContext]) -> List[EditContext]:
        """Keep only the most recent N contexts."""
        if len(contexts) <= self.max_size:
            return contexts
        
        # Sort by timestamp and take most recent
        sorted_contexts = sorted(contexts, key=lambda x: x.timestamp, reverse=True)
        return sorted_contexts[:self.max_size]


class SummarizationStrategy(ContextCompressionStrategy):
    """
    Strategy that summarizes older contexts while keeping recent ones detailed.
    Reduces storage while maintaining essential information.
    """
    
    def __init__(self, detailed_window: int = 5, summary_window: int = 20):
        """
        Initialize summarization strategy.
        
        Args:
            detailed_window: Number of recent contexts to keep in full detail
            summary_window: Total number of contexts to maintain (including summaries)
        """
        self.detailed_window = detailed_window
        self.summary_window = summary_window
    
    def compress(self, contexts: List[EditContext]) -> List[EditContext]:
        """
        Compress contexts by summarizing older entries.
        
        Recent contexts are kept in full detail, older ones are summarized.
        """
        if len(contexts) <= self.detailed_window:
            return contexts
        
        # Sort by timestamp (most recent first)
        sorted_contexts = sorted(contexts, key=lambda x: x.timestamp, reverse=True)
        
        # Keep recent contexts in full detail
        detailed = sorted_contexts[:self.detailed_window]
        
        # Summarize older contexts if we have more than summary_window
        if len(sorted_contexts) > self.summary_window:
            older = sorted_contexts[self.detailed_window:self.summary_window]
            
            # Create a summary context that represents the older edits
            if older:
                summary_context = self._create_summary_context(older)
                return detailed + [summary_context]
        else:
            # Keep all contexts if within summary window
            return sorted_contexts[:self.summary_window]
        
        return detailed
    
    def _create_summary_context(self, contexts: List[EditContext]) -> EditContext:
        """Create a summary context from multiple contexts."""
        # Count edit types
        edit_type_counts = {}
        for ctx in contexts:
            edit_type_counts[ctx.edit_type] = edit_type_counts.get(ctx.edit_type, 0) + 1
        
        # Get all unique target elements
        all_targets = set()
        for ctx in contexts:
            all_targets.update(ctx.target_elements)
        
        # Calculate average processing time
        avg_processing_time = sum(ctx.processing_time_ms for ctx in contexts) / len(contexts)
        
        # Create summary prompt
        summary_parts = []
        for edit_type, count in edit_type_counts.items():
            summary_parts.append(f"{count} {edit_type} edit(s)")
        
        summary_prompt = f"[Summary of {len(contexts)} older edits: {', '.join(summary_parts)}]"
        
        # Use the oldest timestamp
        oldest_timestamp = min(ctx.timestamp for ctx in contexts)
        
        return EditContext(
            prompt=summary_prompt,
            edit_type=EditType.MODIFY,  # Generic type for summary
            target_elements=list(all_targets),
            timestamp=oldest_timestamp,
            processing_time_ms=int(avg_processing_time)
        )


class AdaptiveCompressionStrategy(ContextCompressionStrategy):
    """
    Adaptive strategy that adjusts compression based on context importance.
    Keeps important contexts (e.g., major structural changes) while compressing minor edits.
    """
    
    def __init__(
        self,
        max_size: int = 15,
        importance_threshold: float = 0.7
    ):
        """
        Initialize adaptive compression strategy.
        
        Args:
            max_size: Maximum number of contexts to maintain
            importance_threshold: Threshold for determining important contexts
        """
        self.max_size = max_size
        self.importance_threshold = importance_threshold
    
    def compress(self, contexts: List[EditContext]) -> List[EditContext]:
        """
        Compress contexts adaptively based on importance.
        
        Important contexts are always kept, less important ones are compressed.
        """
        if len(contexts) <= self.max_size:
            return contexts
        
        # Sort by timestamp (most recent first)
        sorted_contexts = sorted(contexts, key=lambda x: x.timestamp, reverse=True)
        
        # Separate important and less important contexts
        important = []
        less_important = []
        
        for ctx in sorted_contexts:
            importance = self._calculate_importance(ctx)
            if importance >= self.importance_threshold:
                important.append(ctx)
            else:
                less_important.append(ctx)
        
        # Always keep all important contexts
        result = important
        
        # Add less important contexts until we reach max_size
        remaining_slots = self.max_size - len(important)
        if remaining_slots > 0:
            result.extend(less_important[:remaining_slots])
        
        # Sort result by timestamp again
        return sorted(result, key=lambda x: x.timestamp, reverse=True)
    
    def _calculate_importance(self, context: EditContext) -> float:
        """
        Calculate importance score for a context.
        
        Factors:
        - Edit type (structural changes are more important)
        - Number of target elements
        - Processing time (complex edits are more important)
        """
        importance = 0.5  # Base importance
        
        # Edit type importance
        type_weights = {
            EditType.ADD: 0.3,
            EditType.REMOVE: 0.3,
            EditType.LAYOUT: 0.2,
            EditType.MODIFY: 0.1,
            EditType.STYLE: 0.05
        }
        importance += type_weights.get(context.edit_type, 0.1)
        
        # Number of elements affected
        if len(context.target_elements) > 2:
            importance += 0.1
        
        # Processing time (complex edits)
        if context.processing_time_ms > 3000:
            importance += 0.1
        
        return min(importance, 1.0)


class ContextCompressor:
    """
    Main context compressor that applies compression strategies.
    """
    
    def __init__(self, strategy: Optional[ContextCompressionStrategy] = None):
        """
        Initialize context compressor.
        
        Args:
            strategy: Compression strategy to use (defaults to SummarizationStrategy)
        """
        self.strategy = strategy or SummarizationStrategy()
    
    def compress_contexts(self, contexts: List[EditContext]) -> List[EditContext]:
        """
        Compress a list of contexts using the configured strategy.
        
        Args:
            contexts: List of contexts to compress
            
        Returns:
            Compressed list of contexts
        """
        if not contexts:
            return contexts
        
        try:
            compressed = self.strategy.compress(contexts)
            
            if len(compressed) < len(contexts):
                logger.info(
                    f"Compressed {len(contexts)} contexts to {len(compressed)} "
                    f"using {self.strategy.__class__.__name__}"
                )
            
            return compressed
            
        except Exception as e:
            logger.error(f"Context compression failed: {e}")
            # Fallback to simple window limit
            return contexts[-10:] if len(contexts) > 10 else contexts
    
    def estimate_storage_size(self, contexts: List[EditContext]) -> int:
        """
        Estimate storage size in bytes for a list of contexts.
        
        Args:
            contexts: List of contexts
            
        Returns:
            Estimated size in bytes
        """
        try:
            # Serialize to JSON to estimate size
            serialized = json.dumps([
                {
                    "prompt": ctx.prompt,
                    "edit_type": ctx.edit_type.value,
                    "target_elements": ctx.target_elements,
                    "timestamp": ctx.timestamp.isoformat(),
                    "processing_time_ms": ctx.processing_time_ms
                }
                for ctx in contexts
            ])
            return len(serialized.encode('utf-8'))
        except Exception as e:
            logger.error(f"Failed to estimate storage size: {e}")
            return 0
    
    def get_compression_ratio(
        self,
        original: List[EditContext],
        compressed: List[EditContext]
    ) -> float:
        """
        Calculate compression ratio.
        
        Args:
            original: Original context list
            compressed: Compressed context list
            
        Returns:
            Compression ratio (0.0 to 1.0, where 1.0 means no compression)
        """
        if not original:
            return 1.0
        
        original_size = self.estimate_storage_size(original)
        compressed_size = self.estimate_storage_size(compressed)
        
        if original_size == 0:
            return 1.0
        
        return compressed_size / original_size


# Convenience functions
def compress_context_window(
    contexts: List[EditContext],
    max_size: int = 10
) -> List[EditContext]:
    """
    Compress context window to maximum size using default strategy.
    
    Args:
        contexts: List of contexts to compress
        max_size: Maximum number of contexts to keep
        
    Returns:
        Compressed list of contexts
    """
    compressor = ContextCompressor(WindowLimitStrategy(max_size=max_size))
    return compressor.compress_contexts(contexts)


def compress_with_summarization(
    contexts: List[EditContext],
    detailed_window: int = 5,
    summary_window: int = 20
) -> List[EditContext]:
    """
    Compress contexts with summarization strategy.
    
    Args:
        contexts: List of contexts to compress
        detailed_window: Number of recent contexts to keep in detail
        summary_window: Total window size including summaries
        
    Returns:
        Compressed list of contexts
    """
    compressor = ContextCompressor(
        SummarizationStrategy(detailed_window, summary_window)
    )
    return compressor.compress_contexts(contexts)
