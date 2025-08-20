# LLM Tracking for Amplitude Python SDK

Automatic instrumentation for tracking LLM API calls (OpenAI, etc.) with zero code changes.

## Quick Start

```python
from amplitude import Amplitude
import amplitude.ai  # Auto-patches OpenAI on import

# Initialize and enable tracking
client = Amplitude('your-api-key')
amplitude.ai.track(client)

# Use OpenAI normally - automatically tracked!
import openai
response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello!"}]
)

# Disable when done
amplitude.ai.untrack()
```

## How It Works

1. **Auto-patching**: When you import `amplitude.ai`, it automatically patches OpenAI SDK methods
2. **Zero code changes**: Your existing OpenAI code works without modification
3. **Automatic tracking**: Every API call is tracked with timing, tokens, model, and more
4. **Thread-safe**: Each thread can have its own Amplitude client

## What Gets Tracked

Each LLM operation is tracked as an `llm_operation` event with:

- `model` - The model used (e.g., "gpt-3.5-turbo")
- `provider` - The LLM provider (e.g., "openai")
- `operation` - The operation type (e.g., "chat_completion")
- `latency_ms` - Response time in milliseconds
- `input_tokens` - Number of input tokens
- `output_tokens` - Number of output tokens
- `total_tokens` - Sum of input and output tokens
- `message_count` - Number of messages in the conversation
- `error` - Error message if the call failed
- `response_preview` - Truncated response (max 500 chars)
- Additional parameters like `temperature`, `max_tokens`

## Supported Providers

### OpenAI ✅
- **Legacy SDK** (pre-v1.0): `openai.ChatCompletion.create()`, `openai.Completion.create()`
- **v1+ SDK**: `client.chat.completions.create()`
- Automatic token counting from API response
- Error tracking and retry handling

### Coming Soon
- Anthropic (Claude)
- Google (Gemini)
- Cohere
- Custom providers via manual API

## API Reference

### `amplitude.ai.track(client)`
Enable LLM tracking for the specified Amplitude client.

```python
client = Amplitude('api-key')
amplitude.ai.track(client)
```

### `amplitude.ai.untrack()`
Disable LLM tracking.

```python
amplitude.ai.untrack()
```

### `amplitude.ai.is_tracking()`
Check if tracking is currently enabled.

```python
if amplitude.ai.is_tracking():
    print("Tracking is enabled")
```

### `amplitude.ai.get_active_client()`
Get the currently active Amplitude client.

```python
client = amplitude.ai.get_active_client()
```

## Privacy & Security

- **No API keys logged**: OpenAI API keys are never captured
- **Response truncation**: Responses are truncated to 500 characters
- **Message privacy**: Only message count and last role are tracked, not content
- **Error safety**: Tracking failures never break your application

## Examples

### Basic Usage

```python
from amplitude import Amplitude
import amplitude.ai

# Setup
client = Amplitude('amplitude-api-key')
amplitude.ai.track(client)

# Your existing code works unchanged
import openai
openai.api_key = 'sk-...'

response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Tell me a joke"}]
)
```

### With Error Handling

```python
import amplitude.ai

try:
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hello"}]
    )
except Exception as e:
    # Error is automatically tracked
    print(f"OpenAI failed: {e}")
```

### Context Manager (Coming Soon)

```python
with amplitude.ai.tracking(client):
    # Tracking enabled only in this block
    response = openai.ChatCompletion.create(...)
# Tracking automatically disabled
```

## Performance

- **Minimal overhead**: < 1ms added latency
- **Async-safe**: Non-blocking event dispatch
- **Thread-safe**: Each thread tracks independently
- **Graceful degradation**: Failures don't affect API calls

## Troubleshooting

**OpenAI calls not being tracked?**
- Ensure `amplitude.ai` is imported before making OpenAI calls
- Call `amplitude.ai.track(client)` before using OpenAI
- Check logs for patching confirmation

**Events not showing in Amplitude?**
- Verify your Amplitude API key is correct
- Call `client.flush()` to send events immediately
- Check network connectivity

**Import errors?**
- LLM tracking works even without OpenAI installed
- Install OpenAI: `pip install openai`

## Implementation Details

The tracking works by:
1. Monkey-patching OpenAI SDK methods at import time
2. Wrapping API calls with timing and tracking logic
3. Extracting metadata from requests and responses
4. Sending events asynchronously to Amplitude

This approach ensures:
- Zero code changes required
- Works with existing code
- No proxy objects or wrappers to manage
- Clean enable/disable semantics