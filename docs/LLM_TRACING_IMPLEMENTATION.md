# LLM Tracing Implementation Guide for Amplitude Python SDK

## Overview

This document outlines how to implement LLM (Large Language Model) tracing in the Amplitude Python SDK, similar to PostHog's approach with monkey-patched client wrappers. The implementation provides automatic instrumentation for popular LLM providers to track usage, performance, and costs.

**All LLM features should be marked as `@experimental`** since this is a new feature that may change in future versions.

## Table of Contents

1. [Simple Solution - Basic Monkey Patching](#simple-solution---basic-monkey-patching)
2. [Plugin-Based Solution](#plugin-based-solution) 
3. [Complete Implementation](#complete-implementation)
4. [Usage Examples](#usage-examples)
5. [Best Practices](#best-practices)

---

## Simple Solution - Basic Monkey Patching

### 1. Create Experimental Decorator

First, add an experimental decorator to `src/amplitude/utils.py`:

```python
import warnings
import functools

def experimental(func=None, *, message=None):
    """Decorator to mark functions, classes, or methods as experimental."""
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            warning_msg = message or f"{f.__name__} is an experimental feature and may change in future versions."
            warnings.warn(f"@experimental: {warning_msg}", UserWarning, stacklevel=2)
            return f(*args, **kwargs)
        wrapper._is_experimental = True
        return wrapper
    
    if func is None:
        return decorator
    else:
        return decorator(func)
```

### 2. Simple LLM Event Class

Create a basic LLM event in a new file `src/amplitude/llm_simple.py`:

```python
"""
Simple LLM tracking for Amplitude SDK.
@experimental - This module is experimental and may change.
"""

import time
from typing import Optional, Dict, Any
from amplitude.event import BaseEvent
from amplitude.utils import experimental


@experimental
class SimpleLLMEvent(BaseEvent):
    """Simple LLM event for tracking LLM operations."""
    
    def __init__(self, model: str, provider: str, operation: str, **kwargs):
        event_properties = kwargs.get('event_properties', {})
        event_properties.update({
            'model': model,
            'provider': provider,
            'operation': operation,
            'llm_sdk_version': 'amplitude-python-llm-experimental'
        })
        
        kwargs['event_properties'] = event_properties
        super().__init__(event_type='llm_operation', **kwargs)


@experimental
def track_openai_call(amplitude_client, model: str, operation: str, 
                      input_data: Any = None, response_data: Any = None,
                      latency_ms: Optional[int] = None, error: Optional[str] = None):
    """Simple function to track OpenAI API calls."""
    
    event_properties = {
        'latency_ms': latency_ms,
        'error': error
    }
    
    # Add input/output data with privacy controls
    if input_data:
        if isinstance(input_data, str):
            event_properties['input'] = input_data[:500] + '...' if len(input_data) > 500 else input_data
        elif isinstance(input_data, list):  # For chat messages
            event_properties['message_count'] = len(input_data)
            
    if response_data:
        if isinstance(response_data, str):
            event_properties['output'] = response_data[:500] + '...' if len(response_data) > 500 else response_data
    
    event = SimpleLLMEvent(
        model=model,
        provider='openai',
        operation=operation,
        event_properties=event_properties
    )
    
    amplitude_client.track(event)


@experimental
def simple_openai_wrapper(amplitude_client):
    """Simple OpenAI wrapper that monkey patches the OpenAI client."""
    try:
        import openai
        
        # Store original methods
        if hasattr(openai, 'ChatCompletion'):
            original_chat_create = openai.ChatCompletion.create
            
            def wrapped_chat_create(*args, **kwargs):
                start_time = time.time()
                error = None
                response = None
                
                try:
                    response = original_chat_create(*args, **kwargs)
                    return response
                except Exception as e:
                    error = str(e)
                    raise
                finally:
                    latency_ms = int((time.time() - start_time) * 1000)
                    
                    # Extract data for tracking
                    model = kwargs.get('model', 'unknown')
                    messages = kwargs.get('messages', [])
                    response_text = None
                    
                    if response and hasattr(response, 'choices') and response.choices:
                        choice = response.choices[0]
                        if hasattr(choice, 'message'):
                            response_text = choice.message.get('content')
                    
                    track_openai_call(
                        amplitude_client=amplitude_client,
                        model=model,
                        operation='chat_completion',
                        input_data=messages,
                        response_data=response_text,
                        latency_ms=latency_ms,
                        error=error
                    )
            
            openai.ChatCompletion.create = wrapped_chat_create
            return True
            
    except ImportError:
        warnings.warn("@experimental: OpenAI not available for instrumentation", UserWarning)
        return False
    except Exception as e:
        warnings.warn(f"@experimental: Failed to instrument OpenAI: {e}", UserWarning)
        return False


@experimental
def enable_simple_llm_tracing(amplitude_client):
    """Enable simple LLM tracing."""
    simple_openai_wrapper(amplitude_client)
```

### 3. Simple Usage Example

```python
from amplitude import Amplitude
from amplitude.llm_simple import enable_simple_llm_tracing
import openai

# Initialize Amplitude
client = Amplitude('your-api-key')

# Enable LLM tracing
enable_simple_llm_tracing(client)

# Use OpenAI normally - calls will be automatically tracked
openai.api_key = 'your-openai-key'
response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

---

## Plugin-Based Solution

### 1. Create LLM Plugin

Create `src/amplitude/llm_plugin.py`:

```python
"""
LLM Observability Plugin for Amplitude.
@experimental - This plugin is experimental and may change.
"""

from typing import Optional
import logging
from amplitude.plugin import EventPlugin
from amplitude.constants import PluginType
from amplitude.event import BaseEvent
from amplitude.utils import experimental

logger = logging.getLogger('amplitude')


@experimental
class LLMObservabilityPlugin(EventPlugin):
    """Plugin to enable LLM observability in Amplitude."""
    
    def __init__(self, include_prompts: bool = True, include_responses: bool = True):
        super().__init__(PluginType.ENRICHMENT)
        self.include_prompts = include_prompts
        self.include_responses = include_responses
        
    def setup(self, client):
        self.configuration = client.configuration
        logger.info("@experimental LLM Observability Plugin enabled")
        
    def execute(self, event: BaseEvent) -> Optional[BaseEvent]:
        """Process events, with special handling for LLM events."""
        if event.event_type != 'llm_operation':
            return event
            
        # Process LLM-specific events
        return self._process_llm_event(event)
    
    def _process_llm_event(self, event: BaseEvent) -> Optional[BaseEvent]:
        """Process LLM events with privacy and size controls."""
        if not event.event_properties:
            return event
            
        properties = event.event_properties.copy()
        
        # Handle content privacy
        if not self.include_prompts:
            properties.pop('input', None)
            properties.pop('messages', None)
            
        if not self.include_responses:
            properties.pop('output', None)
            properties.pop('response', None)
        
        # Add metadata
        properties['llm_observability_enabled'] = True
        
        event.event_properties = properties
        return event
```

### 2. Enhanced LLM Events

Create `src/amplitude/llm_events.py`:

```python
"""
LLM-specific event types for tracking different types of LLM operations.
@experimental - All classes in this module are experimental and may change.
"""

from typing import Optional, Dict, List
from amplitude.event import BaseEvent
from amplitude.utils import experimental


@experimental
class LLMEvent(BaseEvent):
    """Base event class for LLM operations."""
    
    def __init__(self, model: str, provider: str, operation: str, **kwargs):
        event_properties = kwargs.get('event_properties', {})
        event_properties.update({
            'model': model,
            'provider': provider,
            'operation': operation,
            'sdk_version': 'amplitude-python-llm-experimental'
        })
        
        event_properties = {k: v for k, v in event_properties.items() if v is not None}
        kwargs['event_properties'] = event_properties
        super().__init__(event_type='llm_operation', **kwargs)


@experimental 
class LLMChatEvent(LLMEvent):
    """Event for chat completion operations."""
    
    def __init__(self, model: str, provider: str, 
                 messages: Optional[List[Dict[str, str]]] = None,
                 response: Optional[str] = None,
                 input_tokens: Optional[int] = None,
                 output_tokens: Optional[int] = None,
                 latency_ms: Optional[int] = None,
                 error: Optional[str] = None,
                 **kwargs):
        
        event_properties = kwargs.get('event_properties', {})
        
        if messages:
            # Truncate messages for privacy and size
            truncated_messages = []
            for msg in messages[-5:]:  # Keep last 5 messages
                truncated_msg = dict(msg)
                if 'content' in truncated_msg and len(truncated_msg['content']) > 200:
                    truncated_msg['content'] = truncated_msg['content'][:200] + '...'
                truncated_messages.append(truncated_msg)
            event_properties['messages'] = truncated_messages
            event_properties['message_count'] = len(messages)
            
        if response and len(response) > 500:
            response = response[:500] + '...'
            
        event_properties.update({
            'response': response,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': (input_tokens + output_tokens) if (input_tokens and output_tokens) else None,
            'latency_ms': latency_ms,
            'error': error
        })
            
        kwargs['event_properties'] = event_properties
        super().__init__(model=model, provider=provider, operation='chat_completion', **kwargs)
```

### 3. OpenAI Instrumentation

Create `src/amplitude/openai_instrumentation.py`:

```python
"""
OpenAI instrumentation for LLM observability.
@experimental - This instrumentation is experimental and may change.
"""

import time
import logging
from typing import Any, Optional
from amplitude.utils import experimental
from amplitude.llm_events import LLMChatEvent

logger = logging.getLogger('amplitude')


@experimental
class OpenAIInstrumentation:
    """Instrumentation for OpenAI API calls."""
    
    def __init__(self, amplitude_client):
        self.amplitude_client = amplitude_client
        self._original_methods = {}
        self.enabled = False
        
    def instrument(self):
        """Monkey patch OpenAI client methods."""
        try:
            import openai
            
            # Patch chat completions
            if hasattr(openai, 'ChatCompletion'):
                original_create = openai.ChatCompletion.create
                self._original_methods['ChatCompletion.create'] = original_create
                openai.ChatCompletion.create = self._wrap_chat_completion(original_create)
                
            # Patch newer API structure if available
            elif hasattr(openai, 'chat') and hasattr(openai.chat, 'completions'):
                original_create = openai.chat.completions.create
                self._original_methods['chat.completions.create'] = original_create
                openai.chat.completions.create = self._wrap_chat_completion_v1(original_create)
                
            self.enabled = True
            logger.info("@experimental: OpenAI instrumentation enabled")
            
        except ImportError:
            logger.warning("@experimental: OpenAI not available for instrumentation")
            raise
    
    def uninstrument(self):
        """Remove OpenAI monkey patches."""
        try:
            import openai
            
            # Restore original methods
            if 'ChatCompletion.create' in self._original_methods:
                openai.ChatCompletion.create = self._original_methods['ChatCompletion.create']
            if 'chat.completions.create' in self._original_methods:
                openai.chat.completions.create = self._original_methods['chat.completions.create']
                
            self.enabled = False
            logger.info("@experimental: OpenAI instrumentation disabled")
            
        except Exception as e:
            logger.error(f"@experimental: Failed to uninstrument OpenAI: {e}")
    
    def _wrap_chat_completion(self, original_method):
        """Wrapper for legacy OpenAI chat completions."""
        def wrapped(*args, **kwargs):
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
                latency_ms = int((time.time() - start_time) * 1000)
                self._track_chat_completion_legacy(args, kwargs, response, error, latency_ms)
        
        return wrapped
    
    def _wrap_chat_completion_v1(self, original_method):
        """Wrapper for OpenAI v1 chat completions."""
        def wrapped(*args, **kwargs):
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
                latency_ms = int((time.time() - start_time) * 1000)
                self._track_chat_completion_v1(args, kwargs, response, error, latency_ms)
        
        return wrapped
    
    def _track_chat_completion_legacy(self, args, kwargs, response, error, latency_ms):
        """Track legacy OpenAI chat completion event."""
        model = kwargs.get('model', 'unknown')
        messages = kwargs.get('messages', [])
        
        response_text = None
        input_tokens = None
        output_tokens = None
        
        if response and hasattr(response, 'choices') and response.choices:
            choice = response.choices[0]
            if hasattr(choice, 'message'):
                response_text = choice.message.get('content')
                
        if response and hasattr(response, 'usage'):
            input_tokens = response.usage.get('prompt_tokens')
            output_tokens = response.usage.get('completion_tokens')
        
        event = LLMChatEvent(
            model=model,
            provider='openai',
            messages=messages,
            response=response_text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            error=error
        )
        
        if self.amplitude_client and hasattr(self.amplitude_client, 'track'):
            self.amplitude_client.track(event)
    
    def _track_chat_completion_v1(self, args, kwargs, response, error, latency_ms):
        """Track OpenAI v1 chat completion event.""" 
        model = kwargs.get('model', 'unknown')
        messages = kwargs.get('messages', [])
        
        response_text = None
        input_tokens = None
        output_tokens = None
        
        if response and hasattr(response, 'choices') and response.choices:
            choice = response.choices[0]
            if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                response_text = choice.message.content
                
        if response and hasattr(response, 'usage'):
            input_tokens = getattr(response.usage, 'prompt_tokens', None)
            output_tokens = getattr(response.usage, 'completion_tokens', None)
        
        event = LLMChatEvent(
            model=model,
            provider='openai',
            messages=messages,
            response=response_text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            error=error
        )
        
        if self.amplitude_client and hasattr(self.amplitude_client, 'track'):
            self.amplitude_client.track(event)


@experimental
def enable_openai_tracing(amplitude_client):
    """Enable OpenAI tracing."""
    instrumentation = OpenAIInstrumentation(amplitude_client)
    instrumentation.instrument()
    return instrumentation
```

---

## Complete Implementation

### 1. Directory Structure

```
src/amplitude/
├── llm_observability/
│   ├── __init__.py
│   ├── plugin.py
│   ├── events.py
│   ├── instrumentation.py
│   └── providers/
│       ├── __init__.py
│       ├── openai.py
│       └── anthropic.py
├── client.py
├── config.py
└── utils.py
```

### 2. Configuration Integration

Update `src/amplitude/config.py` to include LLM settings:

```python
def __init__(self, api_key: str = None,
             # ... existing parameters ...
             ingestion_metadata: IngestionMetadata = None,
             # @experimental LLM tracking options
             llm_tracking_enabled: bool = False,
             llm_include_prompts: bool = True,
             llm_include_responses: bool = True,
             llm_max_prompt_length: int = 500,
             llm_max_response_length: int = 500):
    # ... existing initialization ...
    
    # @experimental LLM tracking configuration
    self.llm_tracking_enabled = llm_tracking_enabled
    self.llm_include_prompts = llm_include_prompts
    self.llm_include_responses = llm_include_responses
    self.llm_max_prompt_length = llm_max_prompt_length
    self.llm_max_response_length = llm_max_response_length
```

### 3. Client Integration

Update `src/amplitude/client.py` to add LLM methods:

```python
@experimental
def enable_llm_tracing(self, providers: Optional[List[str]] = None):
    """@experimental Enable LLM tracing for specified providers."""
    try:
        from amplitude.llm_observability import LLMObservabilityPlugin
        from amplitude.llm_observability.instrumentation import enable_llm_tracing
        
        # Add LLM plugin if not already added
        if not hasattr(self, '_llm_plugin') or not self._llm_plugin:
            self._llm_plugin = LLMObservabilityPlugin(
                include_prompts=self.configuration.llm_include_prompts,
                include_responses=self.configuration.llm_include_responses
            )
            self.add(self._llm_plugin)
        
        # Enable instrumentation
        enable_llm_tracing(self, providers)
        
        self.configuration.logger.info("@experimental: LLM tracing enabled")
        
    except ImportError as e:
        self.configuration.logger.warning(f"@experimental: Could not enable LLM tracing: {e}")

@experimental 
def disable_llm_tracing(self):
    """@experimental Disable LLM tracing."""
    try:
        from amplitude.llm_observability.instrumentation import disable_llm_tracing
        
        disable_llm_tracing()
        
        if hasattr(self, '_llm_plugin') and self._llm_plugin:
            self.remove(self._llm_plugin)
            self._llm_plugin = None
            
        self.configuration.logger.info("@experimental: LLM tracing disabled")
        
    except Exception as e:
        self.configuration.logger.error(f"@experimental: Failed to disable LLM tracing: {e}")
```

---

## Usage Examples

### Simple Usage

```python
from amplitude import Amplitude
from amplitude.llm_simple import enable_simple_llm_tracing

# Initialize and enable LLM tracing
client = Amplitude('your-api-key')
enable_simple_llm_tracing(client)

# Use LLM providers normally - automatically tracked
import openai
openai.api_key = 'your-openai-key'

response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Plugin-Based Usage

```python
from amplitude import Amplitude, Config
from amplitude.llm_plugin import LLMObservabilityPlugin
from amplitude.openai_instrumentation import enable_openai_tracing

# Configure with LLM settings
config = Config(llm_tracking_enabled=True)
client = Amplitude('your-api-key', configuration=config)

# Add LLM plugin
llm_plugin = LLMObservabilityPlugin(include_prompts=True, include_responses=True)
client.add(llm_plugin)

# Enable tracing
openai_instrumentation = enable_openai_tracing(client)

# Use normally
import openai
response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo", 
    messages=[{"role": "user", "content": "Hello!"}]
)

# Cleanup
openai_instrumentation.uninstrument()
```

### Complete Usage

```python
from amplitude import Amplitude, Config, EventOptions

# Initialize with full LLM configuration
config = Config(
    llm_tracking_enabled=True,
    llm_include_prompts=True,
    llm_include_responses=True,
    llm_max_prompt_length=500,
    llm_max_response_length=500
)

client = Amplitude('your-api-key', configuration=config)

# Set user context
event_options = EventOptions(user_id="user123", device_id="device456")

# Enable LLM tracing (includes OpenAI, Anthropic)
client.enable_llm_tracing(providers=['openai', 'anthropic'])

# Use LLM providers - automatically tracked
import openai
response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "What is machine learning?"}]
)

# Manual tracking if needed
from amplitude.llm_observability import LLMChatEvent
manual_event = LLMChatEvent(
    model="custom-model",
    provider="custom-provider", 
    messages=[{"role": "user", "content": "Hello"}],
    response="Hi there!",
    input_tokens=5,
    output_tokens=3,
    latency_ms=250
)
manual_event.load_event_options(event_options)
client.track(manual_event)

# Cleanup
client.disable_llm_tracing()
```

---

## Best Practices

### 1. Privacy and Security

- **Content Filtering**: Always truncate prompts and responses to reasonable lengths
- **Sensitive Data**: Avoid logging sensitive information in prompts/responses
- **Configuration**: Provide options to disable content logging entirely

```python
# Example privacy configuration
config = Config(
    llm_include_prompts=False,  # Don't log prompts for privacy
    llm_include_responses=True,
    llm_max_response_length=200  # Limit response content
)
```

### 2. Error Handling

- **Graceful Degradation**: LLM tracing should never break existing functionality
- **Logging**: Use appropriate log levels for debugging vs production
- **Fallbacks**: Handle cases where LLM providers are not available

```python
try:
    client.enable_llm_tracing(['openai'])
except ImportError:
    logger.info("OpenAI not available, skipping LLM tracing")
except Exception as e:
    logger.warning(f"LLM tracing failed: {e}")
```

### 3. Performance

- **Minimal Overhead**: Instrumentation should add minimal latency
- **Async Safety**: Ensure compatibility with async LLM calls
- **Memory Usage**: Avoid storing large response objects

### 4. Experimental Feature Management

- **Clear Warnings**: Always mark experimental features with appropriate warnings
- **Documentation**: Clearly document that features may change
- **Versioning**: Consider separate versioning for experimental features

### 5. Event Properties

Standard LLM event properties to include:

```python
{
    'model': 'gpt-3.5-turbo',
    'provider': 'openai', 
    'operation': 'chat_completion',
    'input_tokens': 25,
    'output_tokens': 15,
    'total_tokens': 40,
    'latency_ms': 1500,
    'cost': 0.00004,  # If available
    'error': None,
    'streaming': False,
    'temperature': 0.7,
    'max_tokens': 100
}
```

### 6. Testing

- **Unit Tests**: Test instrumentation with mocked LLM providers
- **Integration Tests**: Test with actual LLM APIs in controlled environments  
- **Error Cases**: Test error handling and edge cases

---

## Implementation Priority

1. **Start Simple**: Implement basic monkey patching for OpenAI
2. **Add Plugin Support**: Create plugin-based architecture
3. **Expand Providers**: Add support for Anthropic, other providers
4. **Advanced Features**: Add streaming support, cost tracking, etc.
5. **Configuration**: Add comprehensive configuration options

This approach allows for incremental development and testing while providing immediate value with the simplest solution.
