"""Base wrapper functionality for LLM observability."""

import time
import uuid
import asyncio
import threading
from typing import Optional, Dict, Any, List, Union
from abc import ABC, abstractmethod

from amplitude.client import Amplitude
from .config import AIConfig
from .events import (
    get_current_session_id, 
    set_session_id,
    LLMRunStartedEvent,
    LLMMessageEvent,
    UserMessageEvent,
    ToolCalledEvent,
    LLMRunFinishedEvent
)


class BaseLLMWrapper(ABC):
    """Base class for LLM provider wrappers implementing no-proxy observability."""
    
    def __init__(self, 
                 amplitude_client: Optional[Amplitude] = None,
                 ai_config: Optional[AIConfig] = None,
                 auto_start_session: bool = True,
                 **kwargs):
        """Initialize base LLM wrapper.
        
        Args:
            amplitude_client: Amplitude client for event tracking
            ai_config: AI observability configuration
            auto_start_session: Whether to automatically start a new session
            **kwargs: Additional parameters passed to the underlying client
        """
        self.amplitude_client = amplitude_client
        self.ai_config = ai_config or AIConfig()
        self.session_start_time = None
        self.session_stats = {
            "total_messages": 0,
            "total_tokens": 0,
            "total_cost_usd": 0.0
        }
        
        if auto_start_session:
            self._start_session()
    
    def _start_session(self, session_id: Optional[str] = None) -> str:
        """Start a new LLM session.
        
        Args:
            session_id: Optional custom session ID
            
        Returns:
            The session ID
        """
        if session_id:
            set_session_id(session_id)
        else:
            session_id = get_current_session_id()
        
        self.session_start_time = time.time()
        self.session_stats = {
            "total_messages": 0,
            "total_tokens": 0,
            "total_cost_usd": 0.0
        }
        
        if self.amplitude_client:
            event = LLMRunStartedEvent(
                session_id=session_id,
                model_provider=self.get_provider_name(),
                model_name=getattr(self, '_current_model', None)
            )
            self._emit_event(event)
        
        return session_id
    
    def _finish_session(self, success: bool = True, error_message: Optional[str] = None) -> None:
        """Finish the current LLM session.
        
        Args:
            success: Whether the session completed successfully
            error_message: Error message if session failed
        """
        if not self.session_start_time or not self.amplitude_client:
            return
        
        duration_ms = int((time.time() - self.session_start_time) * 1000)
        
        event = LLMRunFinishedEvent(
            session_id=get_current_session_id(),
            total_messages=self.session_stats["total_messages"],
            total_tokens=self.session_stats["total_tokens"],
            total_cost_usd=self.session_stats["total_cost_usd"],
            duration_ms=duration_ms,
            success=success,
            error_message=error_message
        )
        self._emit_event(event)
    
    def _capture_message_event(self,
                             request_data: Dict[str, Any],
                             response_data: Any,
                             latency_ms: int,
                             user_id: Optional[str] = None,
                             device_id: Optional[str] = None) -> None:
        """Capture an LLM message event.
        
        Args:
            request_data: The request parameters
            response_data: The response from the LLM
            latency_ms: Request latency in milliseconds
            user_id: Optional user ID
            device_id: Optional device ID
        """
        if not self.amplitude_client:
            return
        
        # Extract tokens and cost information
        input_tokens, output_tokens, total_tokens = self._extract_token_usage(response_data)
        cost_usd = self.ai_config.calculate_cost(
            self.get_provider_name(),
            self._extract_model_name(request_data, response_data),
            input_tokens or 0,
            output_tokens or 0
        )
        
        # Update session stats
        self.session_stats["total_messages"] += 1
        if total_tokens:
            self.session_stats["total_tokens"] += total_tokens
        if cost_usd:
            self.session_stats["total_cost_usd"] += cost_usd
        
        # Extract content based on privacy settings
        input_messages = None
        output_content = None
        
        if not self.ai_config.should_exclude_content("input"):
            input_messages = self._extract_input_messages(request_data)
        
        if not self.ai_config.should_exclude_content("output"):
            output_content = self._extract_output_content(response_data)
            if output_content:
                output_content = self.ai_config.truncate_content(output_content)
        
        # Create and emit event
        event = LLMMessageEvent(
            session_id=get_current_session_id(),
            user_id=user_id,
            device_id=device_id,
            model_provider=self.get_provider_name(),
            model_name=self._extract_model_name(request_data, response_data),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            input_messages=input_messages,
            output_content=output_content,
            finish_reason=self._extract_finish_reason(response_data),
            temperature=request_data.get("temperature"),
            max_tokens=request_data.get("max_tokens")
        )
        self._emit_event(event)
    
    def _capture_tool_call_event(self,
                               tool_name: str,
                               tool_parameters: Optional[Dict[str, Any]] = None,
                               tool_result: Optional[Any] = None,
                               execution_time_ms: Optional[int] = None,
                               success: bool = True,
                               error_message: Optional[str] = None,
                               user_id: Optional[str] = None,
                               device_id: Optional[str] = None) -> None:
        """Capture a tool call event.
        
        Args:
            tool_name: Name of the tool/function called
            tool_parameters: Parameters passed to the tool
            tool_result: Result returned by the tool
            execution_time_ms: Tool execution time
            success: Whether the tool call succeeded
            error_message: Error message if tool call failed
            user_id: Optional user ID
            device_id: Optional device ID
        """
        if not self.amplitude_client:
            return
        
        # Apply privacy settings
        if self.ai_config.should_exclude_content("tool_parameters"):
            tool_parameters = None
        if self.ai_config.should_exclude_content("tool_results"):
            tool_result = None
        
        event = ToolCalledEvent(
            session_id=get_current_session_id(),
            user_id=user_id,
            device_id=device_id,
            tool_name=tool_name,
            tool_parameters=tool_parameters,
            tool_result=tool_result,
            execution_time_ms=execution_time_ms,
            success=success,
            error_message=error_message
        )
        self._emit_event(event)
    
    def _capture_user_message_event(self,
                                  content: str,
                                  message_type: str = "text",
                                  user_id: Optional[str] = None,
                                  device_id: Optional[str] = None) -> None:
        """Capture a user message event.
        
        Args:
            content: User message content
            message_type: Type of message (text, image, etc.)
            user_id: Optional user ID
            device_id: Optional device ID
        """
        if not self.amplitude_client:
            return
        
        # Apply privacy settings
        if self.ai_config.should_exclude_content("input"):
            content = None
        elif content:
            content = self.ai_config.truncate_content(content)
        
        event = UserMessageEvent(
            session_id=get_current_session_id(),
            user_id=user_id,
            device_id=device_id,
            content=content,
            message_type=message_type
        )
        self._emit_event(event)
    
    def _capture_error_event(self,
                           error: Exception,
                           request_data: Optional[Dict[str, Any]] = None,
                           user_id: Optional[str] = None,
                           device_id: Optional[str] = None) -> None:
        """Capture an error event.
        
        Args:
            error: The exception that occurred
            request_data: The request parameters that caused the error
            user_id: Optional user ID
            device_id: Optional device ID
        """
        if not self.amplitude_client or not self.ai_config.error_tracking:
            return
        
        # Create an LLM message event with error information
        event = LLMMessageEvent(
            session_id=get_current_session_id(),
            user_id=user_id,
            device_id=device_id,
            model_provider=self.get_provider_name(),
            model_name=request_data.get("model") if request_data else None,
            input_messages=self._extract_input_messages(request_data) if request_data and not self.ai_config.should_exclude_content("input") else None,
            finish_reason="error"
        )
        # Add error details to event properties
        if hasattr(event, 'event_properties'):
            event.event_properties.update({
                "success": False,
                "error_message": str(error),
                "error_type": type(error).__name__
            })
        
        self._emit_event(event)
    
    def _emit_event(self, event) -> None:
        """Emit an event to Amplitude.
        
        Args:
            event: The event to emit
        """
        if not self.amplitude_client:
            return
        
        if self.ai_config.async_event_emission:
            # Emit asynchronously to avoid blocking the LLM call
            def emit():
                try:
                    self.amplitude_client.track(event)
                except Exception:
                    # Silently ignore emission errors to avoid affecting LLM calls
                    pass
            
            thread = threading.Thread(target=emit, daemon=True)
            thread.start()
        else:
            try:
                self.amplitude_client.track(event)
            except Exception:
                # Silently ignore emission errors to avoid affecting LLM calls
                pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the provider name (e.g., 'openai', 'anthropic', 'google')."""
        pass
    
    @abstractmethod
    def _extract_token_usage(self, response_data: Any) -> tuple[Optional[int], Optional[int], Optional[int]]:
        """Extract token usage from response data.
        
        Returns:
            Tuple of (input_tokens, output_tokens, total_tokens)
        """
        pass
    
    @abstractmethod
    def _extract_model_name(self, request_data: Dict[str, Any], response_data: Any) -> Optional[str]:
        """Extract model name from request or response data."""
        pass
    
    @abstractmethod
    def _extract_input_messages(self, request_data: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Extract input messages from request data."""
        pass
    
    @abstractmethod
    def _extract_output_content(self, response_data: Any) -> Optional[str]:
        """Extract output content from response data."""
        pass
    
    @abstractmethod
    def _extract_finish_reason(self, response_data: Any) -> Optional[str]:
        """Extract finish reason from response data."""
        pass