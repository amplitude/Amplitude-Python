"""AI observability event definitions following the schema.md specification."""

import time
import uuid
from typing import Optional, Dict, Any, List, Union
import threading

from amplitude.event import BaseEvent
from amplitude.client import Amplitude
from .config import AIConfig


# Thread-local storage for session context
_local = threading.local()


def get_current_session_id() -> str:
    """Get or create a session ID for the current thread."""
    if not hasattr(_local, 'session_id'):
        _local.session_id = str(uuid.uuid4())
    return _local.session_id


def set_session_id(session_id: str) -> None:
    """Set the session ID for the current thread."""
    _local.session_id = session_id


class LLMRunStartedEvent(BaseEvent):
    """Event emitted when an LLM interaction/session begins."""
    
    def __init__(self, 
                 session_id: Optional[str] = None,
                 user_id: Optional[str] = None,
                 device_id: Optional[str] = None,
                 model_provider: Optional[str] = None,
                 model_name: Optional[str] = None,
                 **kwargs):
        """Initialize LLM run started event.
        
        Args:
            session_id: Unique identifier for the LLM session
            user_id: User identifier
            device_id: Device identifier  
            model_provider: Provider name (openai, anthropic, google, etc.)
            model_name: Model identifier (gpt-4, claude-3, gemini-pro, etc.)
            **kwargs: Additional BaseEvent parameters
        """
        event_properties = {
            "session_id": session_id or get_current_session_id(),
            "model_provider": model_provider,
            "model_name": model_name,
        }
        
        # Remove None values
        event_properties = {k: v for k, v in event_properties.items() if v is not None}
        
        super().__init__(
            event_type="llm_run_started",
            user_id=user_id,
            device_id=device_id,
            time=kwargs.get('time', int(time.time() * 1000)),
            event_properties=event_properties,
            **{k: v for k, v in kwargs.items() if k not in ['time', 'event_properties']}
        )


class LLMMessageEvent(BaseEvent):
    """Event emitted for each LLM response/completion."""
    
    def __init__(self,
                 session_id: Optional[str] = None,
                 message_id: Optional[str] = None,
                 user_id: Optional[str] = None,
                 device_id: Optional[str] = None,
                 model_provider: Optional[str] = None,
                 model_name: Optional[str] = None,
                 input_tokens: Optional[int] = None,
                 output_tokens: Optional[int] = None,
                 total_tokens: Optional[int] = None,
                 latency_ms: Optional[int] = None,
                 cost_usd: Optional[float] = None,
                 input_messages: Optional[List[Dict[str, Any]]] = None,
                 output_content: Optional[str] = None,
                 finish_reason: Optional[str] = None,
                 temperature: Optional[float] = None,
                 max_tokens: Optional[int] = None,
                 **kwargs):
        """Initialize LLM message event.
        
        Args:
            session_id: Session identifier
            message_id: Unique identifier for this message
            user_id: User identifier
            device_id: Device identifier
            model_provider: Provider name
            model_name: Model identifier
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            total_tokens: Total tokens used
            latency_ms: Response latency in milliseconds
            cost_usd: Estimated cost in USD
            input_messages: Input messages/prompts (privacy configurable)
            output_content: Generated response (privacy configurable)
            finish_reason: Why the completion finished
            temperature: Temperature parameter used
            max_tokens: Max tokens parameter used
            **kwargs: Additional BaseEvent parameters
        """
        event_properties = {
            "session_id": session_id or get_current_session_id(),
            "message_id": message_id or str(uuid.uuid4()),
            "model_provider": model_provider,
            "model_name": model_name,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "latency_ms": latency_ms,
            "cost_usd": cost_usd,
            "input_messages": input_messages,
            "output_content": output_content,
            "finish_reason": finish_reason,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        # Remove None values
        event_properties = {k: v for k, v in event_properties.items() if v is not None}
        
        super().__init__(
            event_type="llm_message",
            user_id=user_id,
            device_id=device_id,
            time=kwargs.get('time', int(time.time() * 1000)),
            event_properties=event_properties,
            **{k: v for k, v in kwargs.items() if k not in ['time', 'event_properties']}
        )


class UserMessageEvent(BaseEvent):
    """Event emitted for user inputs/messages."""
    
    def __init__(self,
                 session_id: Optional[str] = None,
                 message_id: Optional[str] = None,
                 user_id: Optional[str] = None,
                 device_id: Optional[str] = None,
                 content: Optional[str] = None,
                 message_type: str = "text",
                 **kwargs):
        """Initialize user message event.
        
        Args:
            session_id: Session identifier
            message_id: Unique identifier for this message
            user_id: User identifier
            device_id: Device identifier
            content: User message content (privacy configurable)
            message_type: Type of message (text, image, etc.)
            **kwargs: Additional BaseEvent parameters
        """
        event_properties = {
            "session_id": session_id or get_current_session_id(),
            "message_id": message_id or str(uuid.uuid4()),
            "content": content,
            "message_type": message_type,
        }
        
        # Remove None values
        event_properties = {k: v for k, v in event_properties.items() if v is not None}
        
        super().__init__(
            event_type="user_message",
            user_id=user_id,
            device_id=device_id,
            time=kwargs.get('time', int(time.time() * 1000)),
            event_properties=event_properties,
            **{k: v for k, v in kwargs.items() if k not in ['time', 'event_properties']}
        )


class ToolCalledEvent(BaseEvent):
    """Event emitted when LLM calls a function/tool."""
    
    def __init__(self,
                 session_id: Optional[str] = None,
                 tool_call_id: Optional[str] = None,
                 user_id: Optional[str] = None,
                 device_id: Optional[str] = None,
                 tool_name: Optional[str] = None,
                 tool_parameters: Optional[Dict[str, Any]] = None,
                 tool_result: Optional[Dict[str, Any]] = None,
                 execution_time_ms: Optional[int] = None,
                 success: bool = True,
                 error_message: Optional[str] = None,
                 **kwargs):
        """Initialize tool called event.
        
        Args:
            session_id: Session identifier
            tool_call_id: Unique identifier for this tool call
            user_id: User identifier
            device_id: Device identifier
            tool_name: Name of the tool/function called
            tool_parameters: Parameters passed to the tool
            tool_result: Result returned by the tool
            execution_time_ms: Tool execution time
            success: Whether the tool call succeeded
            error_message: Error message if tool call failed
            **kwargs: Additional BaseEvent parameters
        """
        event_properties = {
            "session_id": session_id or get_current_session_id(),
            "tool_call_id": tool_call_id or str(uuid.uuid4()),
            "tool_name": tool_name,
            "tool_parameters": tool_parameters,
            "tool_result": tool_result,
            "execution_time_ms": execution_time_ms,
            "success": success,
            "error_message": error_message,
        }
        
        # Remove None values
        event_properties = {k: v for k, v in event_properties.items() if v is not None}
        
        super().__init__(
            event_type="tool_called",
            user_id=user_id,
            device_id=device_id,
            time=kwargs.get('time', int(time.time() * 1000)),
            event_properties=event_properties,
            **{k: v for k, v in kwargs.items() if k not in ['time', 'event_properties']}
        )


class LLMRunFinishedEvent(BaseEvent):
    """Event emitted when an LLM interaction/session completes."""
    
    def __init__(self,
                 session_id: Optional[str] = None,
                 user_id: Optional[str] = None,
                 device_id: Optional[str] = None,
                 total_messages: Optional[int] = None,
                 total_tokens: Optional[int] = None,
                 total_cost_usd: Optional[float] = None,
                 duration_ms: Optional[int] = None,
                 success: bool = True,
                 error_message: Optional[str] = None,
                 **kwargs):
        """Initialize LLM run finished event.
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            device_id: Device identifier
            total_messages: Total number of messages in the session
            total_tokens: Total tokens used across all messages
            total_cost_usd: Total estimated cost
            duration_ms: Total session duration
            success: Whether the session completed successfully
            error_message: Error message if session failed
            **kwargs: Additional BaseEvent parameters
        """
        event_properties = {
            "session_id": session_id or get_current_session_id(),
            "total_messages": total_messages,
            "total_tokens": total_tokens,
            "total_cost_usd": total_cost_usd,
            "duration_ms": duration_ms,
            "success": success,
            "error_message": error_message,
        }
        
        # Remove None values
        event_properties = {k: v for k, v in event_properties.items() if v is not None}
        
        super().__init__(
            event_type="llm_run_finished",
            user_id=user_id,
            device_id=device_id,
            time=kwargs.get('time', int(time.time() * 1000)),
            event_properties=event_properties,
            **{k: v for k, v in kwargs.items() if k not in ['time', 'event_properties']}
        )


# Manual event emission functions

def emit_llm_run_started(amplitude_client: Amplitude, **kwargs) -> None:
    """Emit an LLM run started event.
    
    Args:
        amplitude_client: The Amplitude client instance
        **kwargs: Event parameters (see LLMRunStartedEvent)
    """
    event = LLMRunStartedEvent(**kwargs)
    amplitude_client.track(event)


def emit_llm_message(amplitude_client: Amplitude, **kwargs) -> None:
    """Emit an LLM message event.
    
    Args:
        amplitude_client: The Amplitude client instance
        **kwargs: Event parameters (see LLMMessageEvent)
    """
    event = LLMMessageEvent(**kwargs)
    amplitude_client.track(event)


def emit_user_message(amplitude_client: Amplitude, **kwargs) -> None:
    """Emit a user message event.
    
    Args:
        amplitude_client: The Amplitude client instance
        **kwargs: Event parameters (see UserMessageEvent)
    """
    event = UserMessageEvent(**kwargs)
    amplitude_client.track(event)


def emit_tool_called(amplitude_client: Amplitude, **kwargs) -> None:
    """Emit a tool called event.
    
    Args:
        amplitude_client: The Amplitude client instance
        **kwargs: Event parameters (see ToolCalledEvent)
    """
    event = ToolCalledEvent(**kwargs)
    amplitude_client.track(event)


def emit_llm_run_finished(amplitude_client: Amplitude, **kwargs) -> None:
    """Emit an LLM run finished event.
    
    Args:
        amplitude_client: The Amplitude client instance
        **kwargs: Event parameters (see LLMRunFinishedEvent)
    """
    event = LLMRunFinishedEvent(**kwargs)
    amplitude_client.track(event)