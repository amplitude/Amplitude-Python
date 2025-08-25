# Amplitude AI Observability

🤖 Comprehensive LLM observability for the Amplitude Python SDK.

## Features

- **Zero-latency autopatching** - No proxy, no slowdown
- **Multi-provider support** - OpenAI, Anthropic, Google, LangChain, Pydantic AI
- **Automatic + manual tracking** - Drop-in replacement or full control
- **Privacy-first** - Configurable content exclusion
- **Cost tracking** - Built-in token-based cost calculation

## Quick Start

### Automatic Instrumentation

```python
from amplitude import Amplitude
from amplitude.ai import get_openai

# Initialize Amplitude
amplitude = Amplitude("your-api-key")

# Get instrumented OpenAI client
OpenAI, _ = get_openai()
client = OpenAI(
    api_key="your-openai-key",
    amplitude_client=amplitude
)

# Use normally - automatically tracked!
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Manual Tracking

```python
from amplitude.ai import llm_session

with llm_session(amplitude, model_provider="openai") as session:
    session.track_user_message("What is AI?")
    session.track_message(
        input_tokens=10,
        output_tokens=50,
        output_content="AI is...",
        latency_ms=1200
    )
```

## Supported Providers

| Provider | Automatic | Manual | Async |
|----------|-----------|---------|-------|
| OpenAI | ✅ | ✅ | ✅ |
| Anthropic | ✅ | ✅ | ✅ |
| Google/Gemini | ✅ | ✅ | ✅ |
| LangChain | ✅ (callback) | ✅ | ✅ |
| Pydantic AI | ✅ | ✅ | ✅ |

## Installation

The AI observability module is included with the Amplitude Python SDK. Optional dependencies:

```bash
# For specific providers
pip install openai anthropic google-generativeai
pip install langchain-core pydantic-ai

# Or install all at once
pip install openai anthropic google-generativeai langchain-core pydantic-ai
```

## Privacy & Security

```python
from amplitude.ai import AIConfig

# Configure privacy settings
ai_config = AIConfig(
    privacy_mode=True,      # Exclude all sensitive content
    exclude_input=True,     # No user prompts
    exclude_output=True,    # No LLM responses
    max_content_length=500  # Truncate long content
)
```

## Documentation

- 📖 [Full Documentation](../../docs/AI_OBSERVABILITY.md)
- 🔧 [API Reference](../../docs/AI_API_REFERENCE.md)
- 🎯 [Examples](../../examples/ai_observability_example.py)
- 📋 [Event Schema](../../schema.md)

## Architecture

The AI observability module follows PostHog's no-proxy approach:

1. **Wrapper Composition** - Extends original clients without inheritance
2. **Async Event Capture** - Zero-latency impact on LLM calls
3. **Schema Standardization** - Consistent events across all providers
4. **Plugin Integration** - Works with Amplitude's plugin system

## Event Types

| Event | Description | Automatic | Manual |
|-------|-------------|-----------|--------|
| `llm_run_started` | Session begins | ✅ | ✅ |
| `llm_message` | LLM response | ✅ | ✅ |
| `user_message` | User input | ✅ | ✅ |
| `tool_called` | Function call | ✅ | ✅ |
| `llm_run_finished` | Session ends | ✅ | ✅ |

## Contributing

1. Follow existing patterns in provider wrappers
2. Add tests for new providers
3. Update documentation
4. Ensure privacy controls work correctly

## License

Same as Amplitude Python SDK.