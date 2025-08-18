# AI Tracking for Amplitude Python SDK

**⚠️ @experimental** - This feature is experimental and may change in future versions.

The Amplitude Python SDK now includes experimental AI/LLM tracking capabilities that automatically instrument popular AI providers to track usage, performance, and costs.

## Quick Start

### 1. Install Dependencies

```bash
pip install amplitude-analytics
pip install openai  # For OpenAI tracking
```

### 2. Basic Usage

```python
from amplitude import Amplitude
import amplitude.ai as ai

# Initialize Amplitude
client = Amplitude('your-amplitude-api-key')

# Enable AI tracking
tracker = ai.track(client, providers=['openai'])

# Use OpenAI normally - calls are now automatically tracked
import openai
openai.api_key = 'your-openai-api-key'

response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello!"}]
)

# Stop tracking when done
tracker.stop()
```

## Features

### 🤖 Automatic Instrumentation
- **OpenAI**: Tracks ChatCompletion and Completion API calls
- **Anthropic**: Placeholder implementation (coming soon)
- Monkey-patches existing code - no changes required

### 📊 Rich Event Data
Events include:
- Model used (e.g., "gpt-3.5-turbo")
- Provider (e.g., "openai") 
- Operation type (e.g., "chat_completion")
- Latency in milliseconds
- Token usage (input/output/total)
- Input/output content (with privacy controls)
- Error messages
- API parameters (temperature, max_tokens, etc.)

### 🔒 Privacy Controls
- Content truncation (configurable limits)
- Option to exclude inputs/outputs entirely
- Automatic PII filtering

### ⚡ Performance
- Minimal overhead
- Non-blocking event sending
- Graceful error handling

## API Reference

### `ai.track(client, **options)`

Enable AI tracking for an Amplitude client.

**Parameters:**
- `amplitude_client` (Amplitude): Amplitude client instance
- `providers` (List[str], optional): Providers to enable. Default: `['openai']`
- `include_inputs` (bool, optional): Include input content. Default: `True`
- `include_outputs` (bool, optional): Include output content. Default: `True`
- `track_errors` (bool, optional): Track failed operations. Default: `True`

**Returns:** `AITracker` instance

### `ai.create_event(model, provider, operation, **kwargs)`

Create an AI event manually.

**Parameters:**
- `model` (str): Model name
- `provider` (str): AI provider
- `operation` (str): Operation type
- `input_data` (Any, optional): Input data
- `output_data` (Any, optional): Output data
- `latency_ms` (int, optional): Latency in milliseconds
- `input_tokens` (int, optional): Input token count
- `output_tokens` (int, optional): Output token count
- `cost` (float, optional): Estimated cost in USD
- `error` (str, optional): Error message
- `metadata` (dict, optional): Additional metadata

**Returns:** `AIEvent` instance

### `AITracker.stop()`

Stop AI tracking and restore original methods.

## Examples

### Automatic Tracking

```python
import amplitude.ai as ai
from amplitude import Amplitude

client = Amplitude('your-api-key')
tracker = ai.track(client)

# OpenAI calls automatically tracked
import openai
response = openai.ChatCompletion.create(...)

tracker.stop()
```

### Manual Event Creation

```python
import amplitude.ai as ai
from amplitude import Amplitude, EventOptions

client = Amplitude('your-api-key')

# Create custom AI event
event = ai.create_event(
    model='custom-model',
    provider='custom-provider',
    operation='text_generation',
    input_data='Generate a story',
    output_data='Once upon a time...',
    latency_ms=1200,
    input_tokens=10,
    output_tokens=50,
    cost=0.001
)

# Add user context
event.load_event_options(EventOptions(user_id='user123'))

# Track event
client.track(event)
```

### Privacy-Focused Tracking

```python
# Track only metadata, no content
tracker = ai.track(
    client,
    include_inputs=False,
    include_outputs=False,
    track_errors=True
)
```

## Event Schema

AI events are sent with `event_type: "ai_operation"` and these properties:

```json
{
  "model": "gpt-3.5-turbo",
  "provider": "openai",
  "operation": "chat_completion",
  "latency_ms": 1250,
  "input_tokens": 25,
  "output_tokens": 15,
  "total_tokens": 40,
  "cost": 0.00006,
  "error": null,
  "input_text": "Hello, how are you?",
  "output_text": "I'm doing well, thank you!",
  "ai_temperature": 0.7,
  "ai_max_tokens": 100,
  "ai_sdk_version": "amplitude-python-ai-experimental"
}
```

## Supported Providers

### OpenAI ✅
- ChatCompletion API (legacy SDK)
- Completion API (legacy SDK)
- Automatic token counting
- Error tracking
- Parameter capture

### Anthropic 🚧
- Coming soon
- Claude API support planned

### Custom Providers ✅
- Use `ai.create_event()` for manual tracking
- Full control over event properties

## Privacy & Security

### Content Handling
- Input/output content is truncated to prevent large payloads
- Chat messages limited to last 3 exchanges
- Text truncated at 500 characters by default
- Full content exclusion available via settings

### Sensitive Data
- No automatic PII detection (implement your own filtering)
- Consider excluding inputs/outputs in sensitive environments
- API keys never logged or tracked

### Production Recommendations
```python
# Conservative production settings
tracker = ai.track(
    client,
    include_inputs=False,    # Don't log prompts
    include_outputs=False,   # Don't log responses
    track_errors=True        # Still track failures
)
```

## Troubleshooting

### Common Issues

**ImportError: No module named 'openai'**
```bash
pip install openai
```

**Warning: "@experimental: OpenAI not available"**
- Install OpenAI package or check import issues

**No events in Amplitude dashboard**
- Verify Amplitude API key
- Check network connectivity
- Call `client.flush()` to send events immediately

**High event volume**
- Consider excluding content with `include_inputs=False, include_outputs=False`
- Implement sampling for high-volume applications

### Debug Mode

Enable debug logging:
```python
import logging
logging.getLogger('amplitude').setLevel(logging.DEBUG)
```

## Best Practices

1. **Production Use**: Always use `include_inputs=False, include_outputs=False` in production
2. **Error Handling**: Keep `track_errors=True` to monitor AI reliability  
3. **Cleanup**: Always call `tracker.stop()` when done
4. **User Context**: Add user IDs to events for better analytics
5. **Cost Monitoring**: Use the `cost` field for budget tracking
6. **Sampling**: For high-volume apps, implement event sampling

## Limitations

- **Experimental**: API may change in future versions
- **Legacy OpenAI**: Currently supports OpenAI legacy SDK only
- **Instance Methods**: New OpenAI v1+ SDK not fully supported yet
- **Async**: Async operations not yet supported
- **Streaming**: Streaming responses not yet supported

## Support

Since this is an experimental feature:
- Expect breaking changes in future versions
- Test thoroughly before production use
- Provide feedback on usage patterns and issues

For technical support, please refer to the main Amplitude Python SDK documentation.
