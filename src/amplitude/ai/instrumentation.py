"""Common instrumentation patterns for LLM providers."""

import time
from typing import Optional, Dict, Any, List, Callable, Tuple
from abc import ABC, abstractmethod

from amplitude.client import Amplitude
from .config import AIConfig
from .events import get_current_session_id, set_session_id


class SessionManager:
    """Centralized session management for LLM observability."""
    
    def __init__(self, amplitude_client: Optional[Amplitude], ai_config: AIConfig, provider_name: str):
        self.amplitude_client = amplitude_client
        self.ai_config = ai_config
        self.provider_name = provider_name
        self.session_start_time = None
        self.session_stats = {
            "total_messages": 0,
            "total_tokens": 0,
            "total_cost_usd": 0.0
        }
    
    def start_session(self, session_id: Optional[str] = None, model_name: Optional[str] = None) -> str:
        """Start a new LLM session."""
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
            from .events import LLMRunStartedEvent
            event = LLMRunStartedEvent(
                session_id=session_id,
                model_provider=self.provider_name,
                model_name=model_name
            )
            EventEmitter(self.amplitude_client, self.ai_config).emit_event(event)
        
        return session_id
    
    def finish_session(self, success: bool = True, error_message: Optional[str] = None) -> None:
        """Finish the current LLM session."""
        if not self.session_start_time or not self.amplitude_client:
            return
        
        duration_ms = int((time.time() - self.session_start_time) * 1000)
        
        from .events import LLMRunFinishedEvent
        event = LLMRunFinishedEvent(
            session_id=get_current_session_id(),
            total_messages=self.session_stats["total_messages"],
            total_tokens=self.session_stats["total_tokens"],
            total_cost_usd=self.session_stats["total_cost_usd"],
            duration_ms=duration_ms,
            success=success,
            error_message=error_message
        )
        EventEmitter(self.amplitude_client, self.ai_config).emit_event(event)
    
    def update_stats(self, total_tokens: Optional[int], cost_usd: Optional[float]) -> None:
        """Update session statistics."""
        self.session_stats["total_messages"] += 1
        if total_tokens:
            self.session_stats["total_tokens"] += total_tokens
        if cost_usd:
            self.session_stats["total_cost_usd"] += cost_usd


class ResponseParser(ABC):
    """Abstract base class for parsing provider-specific responses."""
    
    @abstractmethod
    def extract_token_usage(self, response_data: Any) -> Tuple[Optional[int], Optional[int], Optional[int]]:
        """Extract token usage from response.
        
        Returns:
            Tuple of (input_tokens, output_tokens, total_tokens)
        """
        pass
    
    @abstractmethod
    def extract_model_name(self, request_data: Dict[str, Any], response_data: Any) -> Optional[str]:
        """Extract model name from request or response data."""
        pass
    
    @abstractmethod
    def extract_input_messages(self, request_data: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Extract input messages from request data."""
        pass
    
    @abstractmethod
    def extract_output_content(self, response_data: Any) -> Optional[str]:
        """Extract output content from response data."""
        pass
    
    @abstractmethod
    def extract_finish_reason(self, response_data: Any) -> Optional[str]:
        """Extract finish reason from response data."""
        pass
    
    def extract_tool_calls(self, response_data: Any) -> List[Dict[str, Any]]:
        """Extract tool calls from response data.
        
        Returns:
            List of tool call dictionaries with 'name' and 'parameters' keys
        """
        return []


class EventEmitter:
    """Centralized event emission with async support."""
    
    def __init__(self, amplitude_client: Optional[Amplitude], ai_config: AIConfig):
        self.amplitude_client = amplitude_client
        self.ai_config = ai_config
    
    def emit_event(self, event) -> None:
        """Emit an event to Amplitude."""
        if not self.amplitude_client:
            return
        
        if self.ai_config.async_event_emission:
            self._emit_async(event)
        else:
            self._emit_sync(event)
    
    def _emit_sync(self, event) -> None:
        """Emit event synchronously."""
        try:
            self.amplitude_client.track(event)
        except Exception:
            # Silently ignore emission errors to avoid affecting LLM calls
            pass
    
    def _emit_async(self, event) -> None:
        """Emit event asynchronously."""
        import threading
        
        def emit():
            try:
                self.amplitude_client.track(event)
            except Exception:
                # Silently ignore emission errors
                pass
        
        thread = threading.Thread(target=emit, daemon=True)
        thread.start()


class InstrumentationMixin:
    """Mixin class providing common instrumentation functionality."""
    
    def __init__(self, 
                 amplitude_client: Optional[Amplitude] = None,
                 ai_config: Optional[AIConfig] = None,
                 auto_start_session: bool = True,
                 **kwargs):
        """Initialize instrumentation mixin."""
        self.amplitude_client = amplitude_client
        self.ai_config = ai_config or AIConfig()
        self.event_emitter = EventEmitter(amplitude_client, self.ai_config)
        
        # Session management
        self.session_manager = SessionManager(
            amplitude_client=amplitude_client,
            ai_config=self.ai_config,
            provider_name=self.get_provider_name()
        )
        
        if auto_start_session and amplitude_client:
            self._start_session()
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the provider name (must be implemented by subclass)."""
        pass
    
    @abstractmethod
    def get_response_parser(self) -> ResponseParser:
        """Get the response parser (must be implemented by subclass)."""
        pass
    
    def _start_session(self, session_id: Optional[str] = None) -> str:
        """Start a new LLM session."""
        return self.session_manager.start_session(
            session_id=session_id,
            model_name=getattr(self, '_current_model', None)
        )
    
    def _finish_session(self, success: bool = True, error_message: Optional[str] = None) -> None:
        """Finish the current LLM session."""
        self.session_manager.finish_session(success=success, error_message=error_message)
    
    def _capture_message_event(self,
                             request_data: Dict[str, Any],
                             response_data: Any,
                             latency_ms: int,
                             user_id: Optional[str] = None,
                             device_id: Optional[str] = None) -> None:
        """Capture an LLM message event using the response parser."""
        if not self.amplitude_client:
            return
        
        parser = self.get_response_parser()
        
        # Extract data using parser
        input_tokens, output_tokens, total_tokens = parser.extract_token_usage(response_data)
        model_name = parser.extract_model_name(request_data, response_data)
        
        # Calculate cost
        cost_usd = None
        if input_tokens and output_tokens and self.ai_config.cost_tracking:
            cost_usd = self.ai_config.calculate_cost(
                self.get_provider_name(),
                model_name or "unknown",
                input_tokens,
                output_tokens
            )
        
        # Update session stats
        self.session_manager.update_stats(total_tokens, cost_usd)
        
        # Extract content based on privacy settings
        input_messages = None
        output_content = None
        
        if not self.ai_config.should_exclude_content("input"):
            input_messages = parser.extract_input_messages(request_data)
        
        if not self.ai_config.should_exclude_content("output"):
            output_content = parser.extract_output_content(response_data)
            if output_content:
                output_content = self.ai_config.truncate_content(output_content)
        
        # Create and emit event
        from .events import LLMMessageEvent
        event = LLMMessageEvent(
            session_id=get_current_session_id(),
            user_id=user_id,
            device_id=device_id,
            model_provider=self.get_provider_name(),
            model_name=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            input_messages=input_messages,
            output_content=output_content,
            finish_reason=parser.extract_finish_reason(response_data),
            temperature=request_data.get("temperature"),
            max_tokens=request_data.get("max_tokens")
        )
        self.event_emitter.emit_event(event)
        
        # Capture tool calls
        tool_calls = parser.extract_tool_calls(response_data)
        for tool_call in tool_calls:
            self._capture_tool_call_event(
                tool_name=tool_call.get('name', 'unknown'),
                tool_parameters=tool_call.get('parameters'),
                user_id=user_id,
                device_id=device_id
            )
    
    def _capture_tool_call_event(self,
                               tool_name: str,
                               tool_parameters: Optional[Dict[str, Any]] = None,
                               tool_result: Optional[Any] = None,
                               execution_time_ms: Optional[int] = None,
                               success: bool = True,
                               error_message: Optional[str] = None,
                               user_id: Optional[str] = None,
                               device_id: Optional[str] = None) -> None:
        """Capture a tool call event."""
        if not self.amplitude_client:
            return
        
        # Apply privacy settings
        if tool_parameters and self.ai_config.should_exclude_content("tool_parameters"):
            tool_parameters = None
        if tool_result and self.ai_config.should_exclude_content("tool_results"):
            tool_result = None
        
        from .events import ToolCalledEvent
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
        self.event_emitter.emit_event(event)
    
    def _capture_error_event(self,
                           error: Exception,
                           request_data: Optional[Dict[str, Any]] = None,
                           user_id: Optional[str] = None,
                           device_id: Optional[str] = None) -> None:
        """Capture an error event."""
        if not self.amplitude_client or not self.ai_config.error_tracking:
            return
        
        parser = self.get_response_parser()
        model_name = None
        input_messages = None
        
        if request_data:
            model_name = request_data.get("model")
            if not self.ai_config.should_exclude_content("input"):
                input_messages = parser.extract_input_messages(request_data)
        
        from .events import LLMMessageEvent
        event = LLMMessageEvent(
            session_id=get_current_session_id(),
            user_id=user_id,
            device_id=device_id,
            model_provider=self.get_provider_name(),
            model_name=model_name,
            input_messages=input_messages,
            finish_reason="error"
        )
        
        # Add error details to event properties
        if hasattr(event, 'event_properties'):
            event.event_properties.update({
                "success": False,
                "error_message": str(error),
                "error_type": type(error).__name__
            })
        
        self.event_emitter.emit_event(event)
    
    def _create_instrumented_method(self, 
                                  original_method: Callable,
                                  is_async: bool = False) -> Callable:
        """Create an instrumented version of a method."""
        
        def sync_wrapper(*args, **kwargs):
            return self._instrument_call(original_method, False, *args, **kwargs)
        
        async def async_wrapper(*args, **kwargs):
            return await self._instrument_call(original_method, True, *args, **kwargs)
        
        return async_wrapper if is_async else sync_wrapper
    
    def _instrument_call(self, original_method: Callable, is_async: bool, *args, **kwargs):
        """Common instrumentation logic for method calls."""
        # Extract Amplitude-specific parameters
        user_id = kwargs.pop('amplitude_user_id', None)
        device_id = kwargs.pop('amplitude_device_id', None)
        session_id = kwargs.pop('amplitude_session_id', None)
        
        # Set session ID if provided
        if session_id:
            set_session_id(session_id)
        
        start_time = time.time()
        
        async def async_call():
            try:
                response = await original_method(*args, **kwargs)
                latency_ms = int((time.time() - start_time) * 1000)
                
                self._capture_message_event(
                    request_data=kwargs,
                    response_data=response,
                    latency_ms=latency_ms,
                    user_id=user_id,
                    device_id=device_id
                )
                return response
            except Exception as e:
                self._capture_error_event(e, kwargs, user_id, device_id)
                raise
        
        def sync_call():
            try:
                response = original_method(*args, **kwargs)
                latency_ms = int((time.time() - start_time) * 1000)
                
                self._capture_message_event(
                    request_data=kwargs,
                    response_data=response,
                    latency_ms=latency_ms,
                    user_id=user_id,
                    device_id=device_id
                )
                return response
            except Exception as e:
                self._capture_error_event(e, kwargs, user_id, device_id)
                raise
        
        return async_call() if is_async else sync_call()


def import_guard(package_name: str, install_command: str = None):
    """Decorator for handling optional dependencies."""
    def decorator(cls):
        def __init__(self, *args, **kwargs):
            try:
                __import__(package_name)
            except ImportError:
                install_cmd = install_command or f"pip install {package_name}"
                raise ImportError(f"{package_name} not installed. Install with: {install_cmd}")
            cls.__original_init__(self, *args, **kwargs)
        
        cls.__original_init__ = cls.__init__
        cls.__init__ = __init__
        return cls
    return decorator