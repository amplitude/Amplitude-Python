"""
Amplitude AI module for LLM tracing.

This module provides automatic instrumentation for LLM providers like OpenAI,
as well as manual tracking APIs for custom providers.

Example - Automatic tracking:
    from amplitude import Amplitude
    import amplitude.ai  # Auto-patches OpenAI
    
    client = Amplitude('api-key')
    amplitude.ai.track(client)  # Enable tracking
    
    # Use OpenAI normally - calls are automatically tracked
    import openai
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hello!"}]
    )
    
    amplitude.ai.untrack()  # Disable tracking when done

Example - Manual tracking:
    from amplitude import Amplitude
    from amplitude.ai import LLMEvent, track_llm
    
    client = Amplitude('api-key')
    
    # Option 1: Create and track event manually
    event = LLMEvent(
        model="claude-2",
        provider="anthropic",
        operation="chat_completion",
        input_tokens=100,
        output_tokens=50
    )
    client.track(event)
    
    # Option 2: Use convenience function
    track_llm(
        client,
        model="custom-model",
        provider="custom",
        latency_ms=500
    )
"""

# Import openai module to trigger auto-patching
try:
    from amplitude.ai import openai as _openai_patch
except ImportError:
    pass

# Import tracker functions
from amplitude.ai.tracker import track, untrack, is_tracking, get_active_client

# Import manual tracking APIs
from amplitude.ai.events import LLMEvent, track_llm

__all__ = [
    'track', 
    'untrack', 
    'is_tracking', 
    'get_active_client',
    'LLMEvent',
    'track_llm'
]