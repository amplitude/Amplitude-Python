# LLM Observability Event Schema

This document defines the standard event schema for LLM observability in the Amplitude Python SDK.

## Standard Events

### 1. `llm_run_started`
Emitted when an LLM interaction/session begins.

**Properties:**
- `session_id` (string): Unique identifier for the LLM session
- `user_id` (string, optional): User identifier
- `model_provider` (string): Provider name (openai, anthropic, google, etc.)
- `model_name` (string): Model identifier (gpt-4, claude-3, gemini-pro, etc.)
- `timestamp` (number): Unix timestamp when the run started

### 2. `llm_message` 
Emitted for each LLM response/completion.

**Properties:**
- `session_id` (string): Session identifier
- `message_id` (string): Unique identifier for this message
- `user_id` (string, optional): User identifier
- `model_provider` (string): Provider name
- `model_name` (string): Model identifier
- `input_tokens` (number, optional): Number of input tokens
- `output_tokens` (number, optional): Number of output tokens
- `total_tokens` (number, optional): Total tokens used
- `latency_ms` (number): Response latency in milliseconds
- `cost_usd` (number, optional): Estimated cost in USD
- `input_messages` (array, optional): Input messages/prompts (privacy configurable)
- `output_content` (string, optional): Generated response (privacy configurable)
- `finish_reason` (string, optional): Why the completion finished
- `temperature` (number, optional): Temperature parameter used
- `max_tokens` (number, optional): Max tokens parameter used
- `timestamp` (number): Unix timestamp

### 3. `user_message`
Emitted for user inputs/messages.

**Properties:**
- `session_id` (string): Session identifier
- `message_id` (string): Unique identifier for this message
- `user_id` (string, optional): User identifier
- `content` (string, optional): User message content (privacy configurable)
- `message_type` (string): Type of message (text, image, etc.)
- `timestamp` (number): Unix timestamp

### 4. `tool_called`
Emitted when LLM calls a function/tool.

**Properties:**
- `session_id` (string): Session identifier
- `tool_call_id` (string): Unique identifier for this tool call
- `user_id` (string, optional): User identifier
- `tool_name` (string): Name of the tool/function called
- `tool_parameters` (object, optional): Parameters passed to the tool
- `tool_result` (object, optional): Result returned by the tool
- `execution_time_ms` (number, optional): Tool execution time
- `success` (boolean): Whether the tool call succeeded
- `error_message` (string, optional): Error message if tool call failed
- `timestamp` (number): Unix timestamp

### 5. `llm_run_finished`
Emitted when an LLM interaction/session completes.

**Properties:**
- `session_id` (string): Session identifier
- `user_id` (string, optional): User identifier
- `total_messages` (number): Total number of messages in the session
- `total_tokens` (number, optional): Total tokens used across all messages
- `total_cost_usd` (number, optional): Total estimated cost
- `duration_ms` (number): Total session duration
- `success` (boolean): Whether the session completed successfully
- `error_message` (string, optional): Error message if session failed
- `timestamp` (number): Unix timestamp

## Common Properties

All events share these common Amplitude event properties:
- `event_type` (string): The event name (llm_run_started, etc.)
- `user_id` (string, optional): User identifier
- `device_id` (string, optional): Device identifier
- `session_id` (string): LLM session identifier
- `timestamp` (number): Unix timestamp
- `event_properties` (object): Event-specific properties defined above
- `user_properties` (object, optional): User properties
- `groups` (object, optional): Group identifiers

## Privacy Configuration

The following properties can be excluded based on privacy settings:
- `input_messages` - Exclude user prompts/inputs
- `output_content` - Exclude LLM responses
- `content` - Exclude user message content
- `tool_parameters` - Exclude tool call parameters
- `tool_result` - Exclude tool call results

## Error Events

When errors occur, standard events should include:
- `success: false`
- `error_message` (string): Description of the error
- `error_code` (string, optional): Error code if available
- `error_type` (string, optional): Type/category of error