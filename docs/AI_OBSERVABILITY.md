# Amplitude AI Observability

The Amplitude Python SDK includes comprehensive AI observability capabilities that allow you to track LLM usage, costs, performance, and user interactions with minimal setup.

## Features

- **Zero-Latency Tracking**: Uses no-proxy autopatching - observability data is captured asynchronously without affecting LLM response times
- **Multi-Provider Support**: OpenAI, Anthropic, Google/Gemini, LangChain, and Pydantic AI
- **Automatic Instrumentation**: Drop-in replacement for LLM clients with zero code changes
- **Manual Event Emission**: Full control over what gets tracked when automatic instrumentation isn't sufficient
- **Privacy Controls**: Configurable exclusion of sensitive data (prompts, responses, tool parameters)
- **Cost Tracking**: Automatic cost calculation based on token usage and model pricing
- **Plugin Architecture**: Integrate with Amplitude's existing plugin system for custom processing

## Standard Events

The AI observability module tracks 5 standard events following a consistent schema:

1. **`llm_run_started`** - When an LLM session begins
2. **`llm_message`** - For each LLM response/completion  
3. **`user_message`** - For user inputs
4. **`tool_called`** - When LLM calls functions/tools
5. **`llm_run_finished`** - When an LLM session completes

See [schema.md](../schema.md) for detailed event specifications.

## Quick Start

### 1. Basic Setup

```python
from amplitude import Amplitude
from amplitude.ai import AIConfig

# Initialize Amplitude client
amplitude_client = Amplitude("your-amplitude-api-key")

# Configure AI observability (optional)
ai_config = AIConfig(
    privacy_mode=False,  # Set True to exclude sensitive content
    cost_tracking=True,
    max_content_length=1000
)
```

### 2. Automatic Instrumentation

#### OpenAI

```python
from amplitude.ai import get_openai

# Get instrumented OpenAI client
OpenAI, AsyncOpenAI = get_openai()

# Drop-in replacement - just change the import!
client = OpenAI(
    api_key="your-openai-key",
    amplitude_client=amplitude_client,
    ai_config=ai_config  # optional
)

# Use normally - automatically tracked
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}],
    amplitude_user_id="user123",  # optional Amplitude params
    amplitude_session_id="session456"
)
```

#### Anthropic

```python
from amplitude.ai import get_anthropic

Anthropic, AsyncAnthropic = get_anthropic()

client = Anthropic(
    api_key="your-anthropic-key",
    amplitude_client=amplitude_client,
    ai_config=ai_config
)

response = client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=100,
    messages=[{"role": "user", "content": "Hello Claude!"}]
)
```

#### Google Gemini

```python
from amplitude.ai import get_google

GoogleGenerativeAI = get_google()

client = GoogleGenerativeAI(
    api_key="your-google-key",
    model_name="gemini-pro",
    amplitude_client=amplitude_client,
    ai_config=ai_config
)

response = client.generate_content("What is AI?")
```

#### LangChain

```python
from amplitude.ai import get_langchain
from langchain_openai import ChatOpenAI

AmplitudeLangChainCallback = get_langchain()

callback = AmplitudeLangChainCallback(
    amplitude_client=amplitude_client,
    ai_config=ai_config,
    user_id="user123"
)

# Use with any LangChain component
llm = ChatOpenAI(callbacks=[callback])
response = llm.invoke("Hello LangChain!")
```

#### Pydantic AI

```python
from amplitude.ai import get_pydantic

PydanticAIWrapper = get_pydantic()

# Create agent with automatic tracking
wrapper = PydanticAIWrapper.create_agent(
    model='openai:gpt-4',
    result_type=str,
    amplitude_client=amplitude_client,
    ai_config=ai_config
)

result = wrapper.agent.run("What is the meaning of life?")
```

### 3. Manual Event Tracking

#### Session Context Manager (Recommended)

```python
from amplitude.ai import llm_session

with llm_session(
    amplitude_client=amplitude_client,
    user_id="user123",
    model_provider="openai",
    model_name="gpt-4"
) as session:
    
    # Track user message
    session.track_user_message("What is Python?")
    
    # Track LLM response
    session.track_message(
        input_tokens=10,
        output_tokens=50,
        latency_ms=1500,
        output_content="Python is a programming language..."
    )
    
    # Track tool call
    session.track_tool_call(
        tool_name="web_search",
        tool_parameters={"query": "Python programming"},
        tool_result={"results": ["..."]},
        success=True
    )
```

#### Individual Events

```python
from amplitude.ai import (
    emit_llm_run_started,
    emit_llm_message,
    emit_user_message,
    emit_tool_called,
    emit_llm_run_finished
)

# Start session
emit_llm_run_started(
    amplitude_client,
    session_id="session123",
    user_id="user123",
    model_provider="openai",
    model_name="gpt-4"
)

# Track user input
emit_user_message(
    amplitude_client,
    session_id="session123",
    user_id="user123",
    content="Hello AI!"
)

# Track LLM response
emit_llm_message(
    amplitude_client,
    session_id="session123",
    user_id="user123",
    model_provider="openai",
    model_name="gpt-4",
    input_tokens=5,
    output_tokens=20,
    latency_ms=800,
    cost_usd=0.001,
    output_content="Hello! How can I help?"
)

# Finish session
emit_llm_run_finished(
    amplitude_client,
    session_id="session123",
    user_id="user123",
    total_messages=2,
    total_tokens=25,
    total_cost_usd=0.001,
    duration_ms=5000,
    success=True
)
```

#### Quick Tracking

```python
from amplitude.ai import quick_track_message

# One-liner for simple tracking
quick_track_message(
    amplitude_client=amplitude_client,
    model_provider="anthropic",
    model_name="claude-3-sonnet",
    input_content="Explain quantum physics",
    output_content="Quantum physics is the study of...",
    input_tokens=20,
    output_tokens=100,
    latency_ms=2000,
    user_id="user123"
)
```

## Configuration

### AIConfig Options

```python
from amplitude.ai import AIConfig

ai_config = AIConfig(
    # Privacy controls
    privacy_mode=False,              # Exclude all sensitive content
    exclude_input=False,             # Exclude input prompts
    exclude_output=False,            # Exclude LLM responses  
    exclude_tool_parameters=False,   # Exclude tool parameters
    exclude_tool_results=False,      # Exclude tool results
    
    # Feature flags
    token_tracking=True,             # Track token usage
    cost_tracking=True,              # Calculate costs
    latency_tracking=True,           # Track response times
    error_tracking=True,             # Track errors
    
    # Content limits
    max_content_length=10000,        # Max content length
    
    # Cost tracking (auto-configured with latest pricing)
    openai_cost_per_token={...},     # Custom OpenAI pricing
    anthropic_cost_per_token={...},  # Custom Anthropic pricing
    google_cost_per_token={...},     # Custom Google pricing
    
    # Advanced
    async_event_emission=True,       # Emit events asynchronously
    auto_generate_session_ids=True,  # Auto-generate session IDs
    session_timeout_ms=1800000       # 30 minute session timeout
)
```

### Cost Calculation

The SDK includes built-in pricing for major models:

```python
from amplitude.ai import calculate_cost

cost = calculate_cost(
    provider="openai",
    model="gpt-4",
    input_tokens=1000,
    output_tokens=500,
    ai_config=ai_config  # optional
)
print(f"Estimated cost: ${cost:.4f}")
```

## Plugin Integration

### Add AI Processing Plugins

```python
from amplitude.ai import (
    AIObservabilityPlugin,
    AIEventFilterPlugin, 
    AIMetricsPlugin
)

# Core AI processing plugin
amplitude_client.add(AIObservabilityPlugin(ai_config))

# Filter events by criteria
amplitude_client.add(AIEventFilterPlugin(
    min_cost_threshold=0.001,    # Only track calls > $0.001
    allowed_providers=["openai", "anthropic"],
    include_errors=True
))

# Add derived metrics
amplitude_client.add(AIMetricsPlugin())
```

### Custom Plugin Example

```python
from amplitude.plugin import EventPlugin
from amplitude.constants import PluginType

class CustomAIPlugin(EventPlugin):
    def __init__(self):
        super().__init__(PluginType.ENRICHMENT)
    
    def execute(self, event):
        if hasattr(event, 'event_properties') and event.event_properties:
            # Add custom properties to AI events
            if event.event_type in ['llm_message', 'llm_run_finished']:
                event.event_properties['custom_tag'] = 'production'
                event.event_properties['app_version'] = '1.2.3'
        return event

amplitude_client.add(CustomAIPlugin())
```

## Session Management

### Automatic Sessions

```python
# Sessions are automatically created and managed
from amplitude.ai import get_openai

OpenAI, _ = get_openai()
client = OpenAI(
    api_key="your-key",
    amplitude_client=amplitude_client,
    auto_start_session=True  # default
)

# Each client instance gets its own session
response1 = client.chat.completions.create(...)  # Session auto-started
response2 = client.chat.completions.create(...)  # Same session
```

### Manual Session Control

```python
from amplitude.ai import get_current_session_id, set_session_id

# Get current session ID
current_session = get_current_session_id()

# Set custom session ID
set_session_id("my-custom-session-123")

# Create new session ID
from amplitude.ai import create_session_id
new_session = create_session_id()
set_session_id(new_session)
```

### Session Tracking

```python
from amplitude.ai import LLMSessionTracker

tracker = LLMSessionTracker(
    amplitude_client=amplitude_client,
    session_id="session123",
    user_id="user123",
    model_provider="openai",
    model_name="gpt-4"
)

tracker.start_session()

# ... make LLM calls and track events ...

tracker.finish_session(success=True)

# Session stats are automatically calculated
print(f"Total messages: {tracker.session_stats['total_messages']}")
print(f"Total tokens: {tracker.session_stats['total_tokens']}")
print(f"Total cost: ${tracker.session_stats['total_cost_usd']:.4f}")
```

## Timing and Performance

### Message Timing

```python
from amplitude.ai import MessageTimer

timer = MessageTimer()

# Manual timing
timer.start()
response = make_llm_call()
latency_ms = timer.stop()

# Context manager timing
with timer.time():
    response = make_llm_call()
    
print(f"Request took {timer.duration_ms}ms")
```

### Automatic Timing

All automatic instrumentation includes latency tracking:

```python
# Latency automatically captured
response = instrumented_client.chat.completions.create(...)
# Event includes latency_ms property
```

## Error Handling

### Automatic Error Tracking

```python
try:
    response = instrumented_client.chat.completions.create(
        model="invalid-model",  # This will fail
        messages=[{"role": "user", "content": "Hello"}]
    )
except Exception as e:
    # Error automatically tracked with:
    # - error_message: str(e)
    # - error_type: type(e).__name__
    # - success: False
    # - finish_reason: "error"
    pass
```

### Manual Error Tracking

```python
with llm_session(amplitude_client, model_provider="openai") as session:
    try:
        # Your LLM logic here
        result = some_llm_call()
        session.track_message(...)
    except Exception as e:
        # Session automatically marked as failed
        # Additional error tracking:
        session.track_message(
            finish_reason="error",
            # Event properties automatically include:
            # success=False, error_message=str(e)
        )
        raise
```

## Privacy and Security

### Content Exclusion

```python
# Global privacy mode - excludes all sensitive content
ai_config = AIConfig(privacy_mode=True)

# Granular control
ai_config = AIConfig(
    exclude_input=True,            # No user prompts
    exclude_output=True,           # No LLM responses
    exclude_tool_parameters=True,  # No tool inputs
    exclude_tool_results=True      # No tool outputs
)
```

### Content Truncation

```python
ai_config = AIConfig(max_content_length=500)

# Long content automatically truncated:
# "Very long content..." -> "Very long cont..."
```

### Per-Request Privacy

```python
# Override privacy settings per request
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Sensitive data"}],
    amplitude_privacy_mode=True  # This request excluded from tracking content
)
```

## Advanced Usage

### Batch Processing

```python
from amplitude.ai import llm_session

# Process multiple requests in one session
with llm_session(amplitude_client, model_provider="openai") as session:
    for user_query in user_queries:
        session.track_user_message(user_query)
        
        # Make LLM call
        response = make_llm_call(user_query)
        
        session.track_message(
            input_tokens=count_tokens(user_query),
            output_tokens=count_tokens(response),
            output_content=response
        )
```

### Multi-Model Sessions

```python
# Track interactions across multiple models in one session
with llm_session(amplitude_client, session_id="multi-model-session") as session:
    
    # GPT-4 for initial response
    session.track_message(
        model_provider="openai",
        model_name="gpt-4",
        output_content=gpt4_response
    )
    
    # Claude for refinement
    session.track_message(
        model_provider="anthropic", 
        model_name="claude-3-sonnet",
        output_content=claude_response
    )
```

### Custom Event Properties

```python
# Add custom properties to events
emit_llm_message(
    amplitude_client,
    model_provider="openai",
    model_name="gpt-4",
    # ... standard properties ...
    
    # Custom properties
    custom_properties={
        "user_tier": "premium",
        "feature_flag": "new_ui_enabled",
        "app_version": "1.2.3"
    }
)
```

## Monitoring and Analytics

### Key Metrics to Track

With AI observability enabled, you can analyze:

1. **Usage Patterns**
   - Messages per user/session
   - Most used models
   - Peak usage times

2. **Performance**
   - Average latency by model
   - Tokens per second
   - Error rates

3. **Costs**
   - Cost per user/session
   - Most expensive models
   - Cost trends over time

4. **User Behavior**
   - Common prompts/use cases
   - Session lengths
   - Tool usage patterns

### Sample Amplitude Queries

```sql
-- Average cost per user
SELECT user_id, AVG(cost_usd) as avg_cost
FROM llm_message 
WHERE cost_usd IS NOT NULL
GROUP BY user_id

-- Error rates by model
SELECT model_name, 
       COUNT(*) as total_calls,
       SUM(CASE WHEN success = false THEN 1 ELSE 0 END) as errors,
       SUM(CASE WHEN success = false THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as error_rate
FROM llm_message
GROUP BY model_name

-- Token usage trends
SELECT DATE(time) as date,
       SUM(total_tokens) as daily_tokens,
       SUM(cost_usd) as daily_cost
FROM llm_message
WHERE total_tokens IS NOT NULL
GROUP BY DATE(time)
ORDER BY date
```

## Troubleshooting

### Common Issues

1. **Events not appearing in Amplitude**
   ```python
   # Ensure you're flushing events
   amplitude_client.flush()
   
   # Check if plugins are filtering events
   # Temporarily remove filters to test
   ```

2. **Missing cost data**
   ```python
   # Ensure cost tracking is enabled
   ai_config = AIConfig(cost_tracking=True)
   
   # Check if model is in pricing database
   cost = ai_config.calculate_cost("openai", "your-model", 100, 50)
   if cost is None:
       print("Model not found in pricing database")
   ```

3. **Content not being truncated**
   ```python
   # Check max_content_length setting
   ai_config = AIConfig(max_content_length=1000)
   
   # Verify content is being processed
   truncated = ai_config.truncate_content(long_content)
   ```

4. **Import errors**
   ```python
   # Install optional dependencies
   pip install openai anthropic google-generativeai langchain-core pydantic-ai
   
   # Use try/except for graceful fallbacks
   try:
       from amplitude.ai import get_openai
   except ImportError:
       print("OpenAI not available - using manual tracking")
   ```

### Debug Mode

```python
import logging

# Enable debug logging for AI events
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('amplitude.ai')

# This will show event emissions and any errors
```

## Migration Guide

### From Manual Tracking

If you're currently tracking LLM usage manually:

```python
# Before: Manual tracking
amplitude_client.track({
    "event_type": "llm_call",
    "properties": {
        "model": "gpt-4",
        "tokens": 100,
        "cost": 0.002
    }
})

# After: Use AI observability
quick_track_message(
    amplitude_client=amplitude_client,
    model_provider="openai", 
    model_name="gpt-4",
    input_tokens=75,
    output_tokens=25,
    cost_usd=0.002,
    latency_ms=1500
)
```

### From Other Observability Tools

The AI observability module provides similar functionality to tools like LangSmith, Helicone, or Weights & Biases:

- **Automatic instrumentation** replaces proxy-based solutions
- **Event schema** is comprehensive and standardized
- **Privacy controls** give you fine-grained control over sensitive data
- **Cost tracking** is built-in with up-to-date pricing

## Best Practices

1. **Use automatic instrumentation when possible** - it captures more data with less code
2. **Set up privacy controls early** - decide what content to exclude before going to production
3. **Use session management** - it provides better insights than individual events
4. **Add custom properties** - enrich events with app-specific context
5. **Monitor costs** - set up alerts for unexpected usage spikes
6. **Use plugins for custom logic** - keep core tracking simple and add complexity through plugins
7. **Test thoroughly** - verify events are being sent correctly before deploying

## Support

For questions and issues:

1. Check the [examples](../examples/) directory for more code samples
2. Review the [schema documentation](../schema.md) for event specifications
3. Open an issue on GitHub for bugs or feature requests

The AI observability module is designed to be simple to use but powerful enough for complex use cases. Start with basic automatic instrumentation and gradually add manual tracking and custom plugins as needed.