# PostHog LLM Observability: No-Proxy Patching Approach

## Overview

This document provides a comprehensive analysis of PostHog's LLM observability implementation and how it could be adapted for the Amplitude Python SDK. PostHog uses a "no-proxy patching" approach that provides observability without intercepting API calls.

## PostHog's Architecture

### Key Principle: Composition Over Proxy

PostHog's LLM observability SDKs **do not proxy your calls** - they only fire off an async call to PostHog in the background to send observability data. This is a fundamental architectural decision that provides several benefits:

1. **No Added Latency**: Since observability calls are asynchronous, they don't impact API response times
2. **No Single Point of Failure**: The observability layer cannot break your LLM calls
3. **Transparent Integration**: The wrapper maintains the original OpenAI SDK interface

### Implementation Pattern: Wrapper Composition

PostHog uses a wrapper composition pattern rather than traditional monkey patching. Here's how it works:

#### Basic Integration Pattern
```python
import posthog
from openai import OpenAI
from posthog.ai.openai import OpenAI as PostHogOpenAI

# Initialize PostHog client
posthog.project_api_key = '<your_project_api_key>'
posthog.host = '<your_posthog_host>'

# Wrap the OpenAI client with PostHog's wrapper
client = PostHogOpenAI(
    api_key="your-openai-api-key",
    posthog_client=posthog  # Optional - uses default client if not provided
)

# Use normally - observability happens automatically
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}],
    distinct_id="user-123",  # Optional - for user tracking
    posthog_trace_id="trace-456",  # Optional - for trace tracking
)
```

#### Key Implementation Features

1. **Drop-in Replacement**: Users only need to change the import statement
2. **Automatic Instrumentation**: All relevant properties are captured automatically
3. **Optional Parameters**: Additional tracking parameters can be added to requests
4. **Privacy Controls**: Sensitive data can be excluded via privacy mode

### Captured Properties

PostHog's wrapper automatically captures these properties:
- `$ai_input` - The input prompt/messages
- `$ai_input_tokens` - Number of input tokens
- `$ai_cache_read_input_tokens` - Cached input tokens (if applicable)
- `$ai_latency` - Request latency
- `$ai_model` - Model used
- `$ai_model_parameters` - Model configuration parameters
- `$ai_reasoning_tokens` - Reasoning tokens (for models that support it)
- `$ai_tools` - Tools/functions used
- `$ai_output_choices` - Generated responses
- `$ai_output_tokens` - Number of output tokens

### Privacy Mode

To protect sensitive data, PostHog implements privacy mode:

```python
# Global privacy mode
client = PostHogOpenAI(
    api_key="your-openai-api-key",
    privacy_mode=True  # Excludes $ai_input and $ai_output_choices
)

# Per-request privacy mode
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Sensitive data"}],
    privacy_mode=True
)
```

### AsyncOpenAI Support

PostHog's wrapper also supports asynchronous operations:

```python
from posthog.ai.openai import AsyncOpenAI as PostHogAsyncOpenAI

async_client = PostHogAsyncOpenAI(
    api_key="your-openai-api-key",
    posthog_client=posthog
)

# Async calls work transparently
response = await async_client.chat.completions.create(...)
```

## Comparison with Other Observability Tools

### Langfuse Approach

Langfuse uses a similar wrapper composition pattern:

```python
from langfuse.openai import openai  # Drop-in replacement
```

Key features:
- Drop-in replacement by changing only the import
- Automatic instrumentation using SDK replacement
- `@observe()` decorator for manual instrumentation
- Support for manual SDK wrapping

### LiteLLM Integration

LiteLLM provides a proxy-based approach but also supports non-proxy observability:
- Standardizes 100+ models on OpenAI API schema
- Can send logs to observability platforms via environment variables
- Supports both proxy and SDK-based integration

## Technical Implementation Details

### Wrapper Composition Pattern

The wrapper composition pattern works by:

1. **Inheriting from Original SDK**: The wrapper extends or wraps the original OpenAI client
2. **Method Interception**: Overrides key methods (like `chat.completions.create`)
3. **Async Data Capture**: Captures observability data without blocking the original call
4. **Background Transmission**: Sends data to the observability platform asynchronously

### Benefits of This Approach

1. **Performance**: No proxy latency or blocking operations
2. **Reliability**: Observability failures don't affect LLM calls
3. **Compatibility**: Maintains full compatibility with the original SDK
4. **Flexibility**: Allows per-request configuration and privacy controls

### PostHog's Evolution

Based on PostHog's changelog, their approach has evolved:

- **Version 4.1.0**: Transitioned to "composition approach over inheritance"
- **Version 4.2.0**: Added support for Google Gemini
- **Version 4.9.0**: Added reasoning and cache token tracking in LangChain callback

This shows a deliberate move toward composition patterns for better flexibility and maintainability.

## Adaptation Strategy for Amplitude Python SDK

### 1. Module Structure

Create an AI observability module following PostHog's pattern:

```
src/amplitude/ai/
├── __init__.py
├── openai.py          # OpenAI wrapper
├── anthropic.py       # Anthropic wrapper
├── base.py           # Base wrapper functionality
└── events.py         # AI-specific event definitions
```

### 2. Core Wrapper Implementation

```python
# amplitude/ai/openai.py
from openai import OpenAI as OriginalOpenAI
from amplitude import Amplitude

class OpenAI(OriginalOpenAI):
    def __init__(self, *args, amplitude_client=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.amplitude_client = amplitude_client or Amplitude.get_default_client()
    
    def chat_completions_create(self, *args, **kwargs):
        # Extract amplitude-specific parameters
        user_id = kwargs.pop('user_id', None)
        session_id = kwargs.pop('session_id', None)
        privacy_mode = kwargs.pop('privacy_mode', False)
        
        start_time = time.time()
        
        try:
            # Make the actual OpenAI call
            response = super().chat.completions.create(*args, **kwargs)
            
            # Capture observability data asynchronously
            self._capture_ai_event(
                request_data=kwargs,
                response_data=response,
                latency=time.time() - start_time,
                user_id=user_id,
                session_id=session_id,
                privacy_mode=privacy_mode
            )
            
            return response
            
        except Exception as e:
            # Capture error events
            self._capture_ai_error(e, kwargs, user_id, session_id)
            raise
```

### 3. Event Schema

Define AI-specific events that align with Amplitude's event structure:

```python
# amplitude/ai/events.py
class AIEvent:
    AI_GENERATION = "ai_generation"
    AI_EMBEDDING = "ai_embedding"
    AI_ERROR = "ai_error"

class AIProperties:
    MODEL = "ai_model"
    INPUT_TOKENS = "ai_input_tokens"
    OUTPUT_TOKENS = "ai_output_tokens"
    LATENCY = "ai_latency"
    COST = "ai_cost"
    PROVIDER = "ai_provider"
    # Privacy-controlled properties
    INPUT = "ai_input"
    OUTPUT = "ai_output"
```

### 4. Integration Points

The wrapper should integrate with Amplitude's existing infrastructure:

1. **Client Integration**: Use existing Amplitude client for event tracking
2. **Plugin System**: Leverage Amplitude's plugin architecture for AI events
3. **Configuration**: Use Amplitude's configuration system for AI settings
4. **Error Handling**: Integrate with Amplitude's error handling

### 5. Privacy and Compliance

Implement privacy controls similar to PostHog:

```python
class AIConfig:
    def __init__(self):
        self.privacy_mode = False
        self.exclude_input = False
        self.exclude_output = False
        self.token_tracking = True
        self.cost_tracking = True
```

### 6. Async Support

Ensure both sync and async OpenAI clients are supported:

```python
from openai import AsyncOpenAI as OriginalAsyncOpenAI

class AsyncOpenAI(OriginalAsyncOpenAI):
    # Similar implementation but with async methods
    async def chat_completions_create(self, *args, **kwargs):
        # Async implementation
        pass
```

## Conclusion

PostHog's no-proxy patching approach provides a robust, performant solution for LLM observability. By using wrapper composition instead of proxying, it maintains the original SDK's behavior while adding observability capabilities asynchronously.

The key insights for Amplitude's implementation:

1. Use wrapper composition over inheritance or proxying
2. Make observability calls asynchronous to avoid performance impact
3. Provide privacy controls for sensitive data
4. Maintain full compatibility with the original SDK interface
5. Support both sync and async operations
6. Integrate with existing analytics infrastructure

This approach ensures that observability doesn't interfere with core LLM functionality while providing comprehensive insights into AI usage patterns.