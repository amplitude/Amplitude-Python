"""
Manual LLM event creation for custom tracking.
"""

from typing import Optional, Dict, Any, List
from amplitude.event import BaseEvent


class LLMEvent(BaseEvent):
    """
    Manual LLM event for tracking custom LLM operations.
    
    Example:
        from amplitude.ai import LLMEvent
        
        event = LLMEvent(
            model="gpt-4",
            provider="openai",
            operation="chat_completion",
            input_tokens=100,
            output_tokens=50,
            latency_ms=1500
        )
        client.track(event)
    """
    
    def __init__(
        self,
        model: str,
        provider: str = "custom",
        operation: str = "completion",
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        latency_ms: Optional[int] = None,
        error: Optional[str] = None,
        input_text: Optional[str] = None,
        output_text: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        cost: Optional[float] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """
        Create a manual LLM tracking event.
        
        Args:
            model: The model name (e.g., "gpt-4", "claude-2")
            provider: The provider name (e.g., "openai", "anthropic")
            operation: The operation type (e.g., "chat_completion", "embedding")
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            latency_ms: Response time in milliseconds
            error: Error message if the operation failed
            input_text: The input prompt (will be truncated)
            output_text: The output response (will be truncated)
            messages: List of message dicts for chat operations
            cost: Estimated cost in USD
            temperature: Temperature parameter
            max_tokens: Max tokens parameter
            **kwargs: Additional event properties
        """
        # Build event properties
        event_properties = {
            'model': model,
            'provider': provider,
            'operation': operation,
        }
        
        # Add optional numeric properties
        if input_tokens is not None:
            event_properties['input_tokens'] = input_tokens
        if output_tokens is not None:
            event_properties['output_tokens'] = output_tokens
        if input_tokens is not None and output_tokens is not None:
            event_properties['total_tokens'] = input_tokens + output_tokens
        if latency_ms is not None:
            event_properties['latency_ms'] = latency_ms
        if cost is not None:
            event_properties['cost'] = cost
        if temperature is not None:
            event_properties['temperature'] = temperature
        if max_tokens is not None:
            event_properties['max_tokens'] = max_tokens
        
        # Add text properties with truncation
        max_text_length = 500
        if input_text:
            if len(input_text) > max_text_length:
                event_properties['input_text'] = input_text[:max_text_length] + '...'
            else:
                event_properties['input_text'] = input_text
        
        if output_text:
            if len(output_text) > max_text_length:
                event_properties['output_text'] = output_text[:max_text_length] + '...'
            else:
                event_properties['output_text'] = output_text
        
        # Add messages with privacy protection
        if messages:
            event_properties['message_count'] = len(messages)
            # Only include last few messages with truncation
            truncated_messages = []
            for msg in messages[-3:]:  # Last 3 messages
                truncated_msg = {'role': msg.get('role', 'unknown')}
                content = msg.get('content', '')
                if len(content) > 200:
                    truncated_msg['content_preview'] = content[:200] + '...'
                else:
                    truncated_msg['content_preview'] = content
                truncated_messages.append(truncated_msg)
            event_properties['recent_messages'] = truncated_messages
        
        # Add error if present
        if error:
            event_properties['error'] = str(error)
        
        # Add any additional properties from kwargs
        event_properties.update(kwargs.get('event_properties', {}))
        
        # Initialize the base event
        super().__init__(
            event_type='llm_operation',
            event_properties=event_properties,
            **{k: v for k, v in kwargs.items() if k != 'event_properties'}
        )


def track_llm(
    client,
    model: str,
    provider: str = "custom",
    operation: str = "completion",
    **kwargs
) -> LLMEvent:
    """
    Convenience function to create and track an LLM event.
    
    Args:
        client: The Amplitude client instance
        model: The model name
        provider: The provider name
        operation: The operation type
        **kwargs: Additional parameters for LLMEvent
    
    Returns:
        The created LLMEvent
    
    Example:
        from amplitude.ai import track_llm
        
        track_llm(
            client,
            model="gpt-4",
            provider="openai",
            operation="chat_completion",
            input_tokens=100,
            output_tokens=50,
            latency_ms=1500,
            input_text="Write a poem",
            output_text="Roses are red..."
        )
    """
    event = LLMEvent(model=model, provider=provider, operation=operation, **kwargs)
    client.track(event)
    return event