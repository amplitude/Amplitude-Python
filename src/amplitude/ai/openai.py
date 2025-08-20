"""
Auto-patching module for OpenAI SDK to enable LLM tracing.
This module automatically patches OpenAI methods when imported.
"""

import time
import threading
import logging
from typing import Any, Optional, Dict
from functools import wraps

logger = logging.getLogger('amplitude')

# Thread-local storage for the active Amplitude client
_local = threading.local()

# Store original methods for restoration
_original_methods = {}
_patched = False


def get_active_client():
    """Get the currently active Amplitude client for this thread."""
    return getattr(_local, 'amplitude_client', None)


def set_active_client(client):
    """Set the active Amplitude client for this thread."""
    _local.amplitude_client = client


def track_llm_event(
    model: str,
    provider: str,
    operation: str,
    latency_ms: int,
    input_tokens: Optional[int] = None,
    output_tokens: Optional[int] = None,
    error: Optional[str] = None,
    messages: Optional[list] = None,
    response_text: Optional[str] = None,
    **kwargs
):
    """Send an LLM tracking event to Amplitude."""
    client = get_active_client()
    if not client:
        return
    
    try:
        from amplitude.event import BaseEvent
        
        # Prepare event properties
        event_properties = {
            'model': model,
            'provider': provider,
            'operation': operation,
            'latency_ms': latency_ms,
        }
        
        # Add token counts if available
        if input_tokens is not None:
            event_properties['input_tokens'] = input_tokens
        if output_tokens is not None:
            event_properties['output_tokens'] = output_tokens
        if input_tokens is not None and output_tokens is not None:
            event_properties['total_tokens'] = input_tokens + output_tokens
        
        # Add error if present
        if error:
            event_properties['error'] = error
        
        # Add message count (privacy-preserving)
        if messages:
            event_properties['message_count'] = len(messages)
            # Optionally include last message role
            if messages and isinstance(messages[-1], dict):
                event_properties['last_message_role'] = messages[-1].get('role', 'unknown')
        
        # Add truncated response (privacy-preserving)
        if response_text:
            max_length = 500
            if len(response_text) > max_length:
                event_properties['response_preview'] = response_text[:max_length] + '...'
            else:
                event_properties['response_preview'] = response_text
        
        # Add any additional kwargs
        event_properties.update(kwargs)
        
        # Create and send event
        event = BaseEvent(
            event_type='llm_operation',
            event_properties=event_properties
        )
        
        client.track(event)
        
    except Exception as e:
        logger.debug(f"Failed to track LLM event: {e}")


def wrap_chat_completion_create(original_method):
    """Wrap OpenAI ChatCompletion.create method."""
    @wraps(original_method)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        error = None
        response = None
        
        try:
            response = original_method(*args, **kwargs)
            return response
        except Exception as e:
            error = str(e)
            raise
        finally:
            try:
                latency_ms = int((time.time() - start_time) * 1000)
                
                # Extract tracking data
                model = kwargs.get('model', 'unknown')
                messages = kwargs.get('messages', [])
                
                # Extract response data
                response_text = None
                input_tokens = None
                output_tokens = None
                
                if response:
                    # Handle response content
                    if hasattr(response, 'choices') and response.choices:
                        choice = response.choices[0]
                        if hasattr(choice, 'message'):
                            # Legacy SDK structure
                            if hasattr(choice.message, 'content'):
                                response_text = choice.message.content
                            elif isinstance(choice.message, dict):
                                response_text = choice.message.get('content')
                    
                    # Handle usage data
                    if hasattr(response, 'usage'):
                        usage = response.usage
                        if hasattr(usage, 'prompt_tokens'):
                            input_tokens = usage.prompt_tokens
                        elif isinstance(usage, dict):
                            input_tokens = usage.get('prompt_tokens')
                        
                        if hasattr(usage, 'completion_tokens'):
                            output_tokens = usage.completion_tokens
                        elif isinstance(usage, dict):
                            output_tokens = usage.get('completion_tokens')
                
                # Extract additional parameters
                temperature = kwargs.get('temperature')
                max_tokens = kwargs.get('max_tokens')
                
                additional_props = {}
                if temperature is not None:
                    additional_props['temperature'] = temperature
                if max_tokens is not None:
                    additional_props['max_tokens'] = max_tokens
                
                # Track the event
                track_llm_event(
                    model=model,
                    provider='openai',
                    operation='chat_completion',
                    latency_ms=latency_ms,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    error=error,
                    messages=messages,
                    response_text=response_text,
                    **additional_props
                )
            except Exception as e:
                logger.debug(f"Failed to track OpenAI call: {e}")
    
    return wrapper


def wrap_completion_create(original_method):
    """Wrap OpenAI Completion.create method."""
    @wraps(original_method)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        error = None
        response = None
        
        try:
            response = original_method(*args, **kwargs)
            return response
        except Exception as e:
            error = str(e)
            raise
        finally:
            try:
                latency_ms = int((time.time() - start_time) * 1000)
                
                # Extract tracking data
                model = kwargs.get('model', 'unknown')
                prompt = kwargs.get('prompt', '')
                
                # Extract response data
                response_text = None
                input_tokens = None
                output_tokens = None
                
                if response:
                    # Handle response content
                    if hasattr(response, 'choices') and response.choices:
                        choice = response.choices[0]
                        if hasattr(choice, 'text'):
                            response_text = choice.text
                        elif isinstance(choice, dict):
                            response_text = choice.get('text')
                    
                    # Handle usage data
                    if hasattr(response, 'usage'):
                        usage = response.usage
                        if hasattr(usage, 'prompt_tokens'):
                            input_tokens = usage.prompt_tokens
                        elif isinstance(usage, dict):
                            input_tokens = usage.get('prompt_tokens')
                        
                        if hasattr(usage, 'completion_tokens'):
                            output_tokens = usage.completion_tokens
                        elif isinstance(usage, dict):
                            output_tokens = usage.get('completion_tokens')
                
                # Track the event
                track_llm_event(
                    model=model,
                    provider='openai',
                    operation='completion',
                    latency_ms=latency_ms,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    error=error,
                    response_text=response_text,
                    prompt_length=len(str(prompt)) if prompt else 0
                )
            except Exception as e:
                logger.debug(f"Failed to track OpenAI call: {e}")
    
    return wrapper


def wrap_client_chat_completions_create(original_method):
    """Wrap OpenAI v1+ client.chat.completions.create method."""
    @wraps(original_method)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        error = None
        response = None
        
        try:
            response = original_method(*args, **kwargs)
            return response
        except Exception as e:
            error = str(e)
            raise
        finally:
            try:
                latency_ms = int((time.time() - start_time) * 1000)
                
                # Extract tracking data
                model = kwargs.get('model', 'unknown')
                messages = kwargs.get('messages', [])
                
                # Extract response data
                response_text = None
                input_tokens = None
                output_tokens = None
                
                if response:
                    # Handle response content (v1 SDK structure)
                    if hasattr(response, 'choices') and response.choices:
                        choice = response.choices[0]
                        if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                            response_text = choice.message.content
                    
                    # Handle usage data
                    if hasattr(response, 'usage'):
                        if hasattr(response.usage, 'prompt_tokens'):
                            input_tokens = response.usage.prompt_tokens
                        if hasattr(response.usage, 'completion_tokens'):
                            output_tokens = response.usage.completion_tokens
                
                # Track the event
                track_llm_event(
                    model=model,
                    provider='openai',
                    operation='chat_completion',
                    latency_ms=latency_ms,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    error=error,
                    messages=messages,
                    response_text=response_text,
                    sdk_version='openai_v1'
                )
            except Exception as e:
                logger.debug(f"Failed to track OpenAI v1 call: {e}")
    
    return wrapper


def patch_openai():
    """Patch OpenAI SDK methods to enable tracking."""
    global _patched, _original_methods
    
    if _patched:
        return
    
    try:
        import openai
        
        # Try to patch legacy SDK (pre v1.0)
        if hasattr(openai, 'ChatCompletion') and hasattr(openai.ChatCompletion, 'create'):
            _original_methods['ChatCompletion.create'] = openai.ChatCompletion.create
            openai.ChatCompletion.create = wrap_chat_completion_create(openai.ChatCompletion.create)
            logger.debug("Patched OpenAI ChatCompletion.create (legacy SDK)")
        
        if hasattr(openai, 'Completion') and hasattr(openai.Completion, 'create'):
            _original_methods['Completion.create'] = openai.Completion.create
            openai.Completion.create = wrap_completion_create(openai.Completion.create)
            logger.debug("Patched OpenAI Completion.create (legacy SDK)")
        
        # Try to patch v1+ SDK
        if hasattr(openai, 'OpenAI'):
            # Patch the class methods
            original_init = openai.OpenAI.__init__
            
            def patched_init(self, *args, **kwargs):
                original_init(self, *args, **kwargs)
                # Patch instance methods after initialization
                if hasattr(self, 'chat') and hasattr(self.chat, 'completions'):
                    if hasattr(self.chat.completions, 'create'):
                        if 'client.chat.completions.create' not in _original_methods:
                            _original_methods['client.chat.completions.create'] = self.chat.completions.create
                        self.chat.completions.create = wrap_client_chat_completions_create(self.chat.completions.create)
            
            openai.OpenAI.__init__ = patched_init
            logger.debug("Patched OpenAI client (v1+ SDK)")
        
        _patched = True
        logger.info("OpenAI SDK patched for LLM tracing")
        
    except ImportError:
        logger.debug("OpenAI SDK not installed, skipping patching")
    except Exception as e:
        logger.warning(f"Failed to patch OpenAI SDK: {e}")


def unpatch_openai():
    """Remove OpenAI SDK patches."""
    global _patched, _original_methods
    
    if not _patched:
        return
    
    try:
        import openai
        
        # Restore legacy SDK methods
        if 'ChatCompletion.create' in _original_methods:
            openai.ChatCompletion.create = _original_methods['ChatCompletion.create']
        
        if 'Completion.create' in _original_methods:
            openai.Completion.create = _original_methods['Completion.create']
        
        # Note: Restoring instance methods for v1+ SDK is more complex
        # and would require tracking all instances
        
        _original_methods.clear()
        _patched = False
        logger.info("OpenAI SDK patches removed")
        
    except Exception as e:
        logger.warning(f"Failed to unpatch OpenAI SDK: {e}")


# Auto-patch on import
patch_openai()