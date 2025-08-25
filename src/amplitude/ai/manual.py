"""Manual event emission APIs for Amplitude LLM observability.

This module provides comprehensive manual APIs for emitting LLM observability events
when automatic instrumentation is not sufficient or desired.
"""

import time
import uuid
from typing import Optional, Dict, Any, List, Union
from contextlib import contextmanager

from amplitude.client import Amplitude
from .config import AIConfig
from .events import (
    get_current_session_id,
    set_session_id,
    LLMRunStartedEvent,
    LLMMessageEvent,
    UserMessageEvent,
    ToolCalledEvent,
    LLMRunFinishedEvent,
    emit_llm_run_started,
    emit_llm_message,
    emit_user_message,
    emit_tool_called,
    emit_llm_run_finished
)


class LLMSessionTracker:
    """Helper class for tracking LLM sessions and automatically emitting events."""
    
    def __init__(self, 
                 amplitude_client: Amplitude,
                 ai_config: Optional[AIConfig] = None,
                 session_id: Optional[str] = None,
                 user_id: Optional[str] = None,
                 device_id: Optional[str] = None,
                 model_provider: Optional[str] = None,
                 model_name: Optional[str] = None):
        """Initialize session tracker.
        
        Args:
            amplitude_client: Amplitude client for event tracking
            ai_config: AI observability configuration
            session_id: Optional session ID (will generate if not provided)
            user_id: User identifier
            device_id: Device identifier
            model_provider: LLM provider name
            model_name: Model name
        """
        self.amplitude_client = amplitude_client
        self.ai_config = ai_config or AIConfig()
        self.user_id = user_id
        self.device_id = device_id
        self.model_provider = model_provider
        self.model_name = model_name
        
        # Set session ID
        if session_id:
            set_session_id(session_id)
        self.session_id = get_current_session_id()
        
        # Session tracking
        self.session_start_time = None
        self.session_stats = {
            "total_messages": 0,
            "total_tokens": 0,
            "total_cost_usd": 0.0
        }
    
    def start_session(self) -> str:
        """Start a new LLM session.
        
        Returns:
            The session ID
        """
        self.session_start_time = time.time()
        
        emit_llm_run_started(
            self.amplitude_client,
            session_id=self.session_id,
            user_id=self.user_id,
            device_id=self.device_id,
            model_provider=self.model_provider,
            model_name=self.model_name
        )
        
        return self.session_id
    
    def finish_session(self, success: bool = True, error_message: Optional[str] = None) -> None:
        """Finish the current LLM session.
        
        Args:
            success: Whether the session completed successfully
            error_message: Error message if session failed
        """
        if not self.session_start_time:
            return
        
        duration_ms = int((time.time() - self.session_start_time) * 1000)
        
        emit_llm_run_finished(
            self.amplitude_client,
            session_id=self.session_id,
            user_id=self.user_id,
            device_id=self.device_id,
            total_messages=self.session_stats["total_messages"],
            total_tokens=self.session_stats["total_tokens"],
            total_cost_usd=self.session_stats["total_cost_usd"],
            duration_ms=duration_ms,
            success=success,
            error_message=error_message
        )
    
    def track_message(self,
                     input_messages: Optional[List[Dict[str, Any]]] = None,
                     output_content: Optional[str] = None,
                     input_tokens: Optional[int] = None,
                     output_tokens: Optional[int] = None,
                     latency_ms: Optional[int] = None,
                     finish_reason: Optional[str] = None,
                     temperature: Optional[float] = None,
                     max_tokens: Optional[int] = None,
                     **kwargs) -> None:
        """Track an LLM message interaction.
        
        Args:
            input_messages: Input messages/prompts
            output_content: Generated response
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            latency_ms: Response latency in milliseconds
            finish_reason: Why the completion finished
            temperature: Temperature parameter used
            max_tokens: Max tokens parameter used
            **kwargs: Additional parameters
        """
        total_tokens = None
        if input_tokens is not None and output_tokens is not None:
            total_tokens = input_tokens + output_tokens
        
        # Calculate cost if possible
        cost_usd = None
        if input_tokens and output_tokens and self.ai_config.cost_tracking:
            cost_usd = self.ai_config.calculate_cost(
                self.model_provider or "unknown",
                self.model_name or "unknown", 
                input_tokens,
                output_tokens
            )
        
        # Update session stats
        self.session_stats["total_messages"] += 1
        if total_tokens:
            self.session_stats["total_tokens"] += total_tokens
        if cost_usd:
            self.session_stats["total_cost_usd"] += cost_usd
        
        # Apply privacy settings
        if input_messages and self.ai_config.should_exclude_content("input"):
            input_messages = None
        if output_content and self.ai_config.should_exclude_content("output"):
            output_content = None
        elif output_content:
            output_content = self.ai_config.truncate_content(output_content)
        
        emit_llm_message(
            self.amplitude_client,
            session_id=self.session_id,
            user_id=self.user_id,
            device_id=self.device_id,
            model_provider=self.model_provider,
            model_name=self.model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            input_messages=input_messages,
            output_content=output_content,
            finish_reason=finish_reason,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
    
    def track_user_message(self,
                          content: str,
                          message_type: str = "text",
                          **kwargs) -> None:
        """Track a user message.
        
        Args:
            content: User message content
            message_type: Type of message (text, image, etc.)
            **kwargs: Additional parameters
        """
        # Apply privacy settings
        if self.ai_config.should_exclude_content("input"):
            content = None
        elif content:
            content = self.ai_config.truncate_content(content)
        
        emit_user_message(
            self.amplitude_client,
            session_id=self.session_id,
            user_id=self.user_id,
            device_id=self.device_id,
            content=content,
            message_type=message_type,
            **kwargs
        )
    
    def track_tool_call(self,
                       tool_name: str,
                       tool_parameters: Optional[Dict[str, Any]] = None,
                       tool_result: Optional[Dict[str, Any]] = None,
                       execution_time_ms: Optional[int] = None,
                       success: bool = True,
                       error_message: Optional[str] = None,
                       **kwargs) -> None:
        """Track a tool call.
        
        Args:
            tool_name: Name of the tool/function called
            tool_parameters: Parameters passed to the tool
            tool_result: Result returned by the tool
            execution_time_ms: Tool execution time
            success: Whether the tool call succeeded
            error_message: Error message if tool call failed
            **kwargs: Additional parameters
        """
        # Apply privacy settings
        if tool_parameters and self.ai_config.should_exclude_content("tool_parameters"):
            tool_parameters = None
        if tool_result and self.ai_config.should_exclude_content("tool_results"):
            tool_result = None
        
        emit_tool_called(
            self.amplitude_client,
            session_id=self.session_id,
            user_id=self.user_id,
            device_id=self.device_id,
            tool_name=tool_name,
            tool_parameters=tool_parameters,
            tool_result=tool_result,
            execution_time_ms=execution_time_ms,
            success=success,
            error_message=error_message,
            **kwargs
        )


@contextmanager
def llm_session(amplitude_client: Amplitude,
               ai_config: Optional[AIConfig] = None,
               session_id: Optional[str] = None,
               user_id: Optional[str] = None,
               device_id: Optional[str] = None,
               model_provider: Optional[str] = None,
               model_name: Optional[str] = None):
    """Context manager for tracking an LLM session.
    
    Usage:
        with llm_session(amplitude_client, model_provider="openai", model_name="gpt-4") as session:
            session.track_user_message("Hello")
            session.track_message(output_content="Hi there!", output_tokens=10)
    
    Args:
        amplitude_client: Amplitude client for event tracking
        ai_config: AI observability configuration
        session_id: Optional session ID
        user_id: User identifier
        device_id: Device identifier
        model_provider: LLM provider name
        model_name: Model name
    
    Yields:
        LLMSessionTracker instance
    """
    tracker = LLMSessionTracker(
        amplitude_client=amplitude_client,
        ai_config=ai_config,
        session_id=session_id,
        user_id=user_id,
        device_id=device_id,
        model_provider=model_provider,
        model_name=model_name
    )
    
    tracker.start_session()
    
    try:
        yield tracker
        tracker.finish_session(success=True)
    except Exception as e:
        tracker.finish_session(success=False, error_message=str(e))
        raise


class MessageTimer:
    """Helper class for timing LLM message interactions."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
    
    def start(self) -> None:
        """Start timing."""
        self.start_time = time.time()
    
    def stop(self) -> int:
        """Stop timing and return duration in milliseconds.
        
        Returns:
            Duration in milliseconds
        """
        if not self.start_time:
            return 0
        
        self.end_time = time.time()
        return int((self.end_time - self.start_time) * 1000)
    
    @contextmanager
    def time(self):
        """Context manager for timing.
        
        Usage:
            timer = MessageTimer()
            with timer.time():
                # Make LLM call
                response = llm.call(...)
            latency_ms = timer.duration_ms
        """
        self.start()
        try:
            yield
        finally:
            self.stop()
    
    @property
    def duration_ms(self) -> int:
        """Get duration in milliseconds."""
        if not self.start_time or not self.end_time:
            return 0
        return int((self.end_time - self.start_time) * 1000)


def calculate_cost(provider: str,
                  model: str,
                  input_tokens: int,
                  output_tokens: int,
                  ai_config: Optional[AIConfig] = None) -> Optional[float]:
    """Calculate the estimated cost for a model call.
    
    Args:
        provider: The LLM provider (openai, anthropic, google)
        model: The model name
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        ai_config: AI config with cost data (uses defaults if not provided)
    
    Returns:
        Estimated cost in USD, or None if model not found
    """
    config = ai_config or AIConfig()
    return config.calculate_cost(provider, model, input_tokens, output_tokens)


def create_session_id() -> str:
    """Create a new session ID.
    
    Returns:
        A new unique session ID
    """
    return str(uuid.uuid4())


# Convenience functions for one-off event emission
def quick_track_message(amplitude_client: Amplitude,
                       model_provider: str,
                       model_name: str,
                       input_content: Optional[str] = None,
                       output_content: Optional[str] = None,
                       input_tokens: Optional[int] = None,
                       output_tokens: Optional[int] = None,
                       latency_ms: Optional[int] = None,
                       user_id: Optional[str] = None,
                       device_id: Optional[str] = None,
                       **kwargs) -> None:
    """Quick way to track a single LLM message without session management.
    
    Args:
        amplitude_client: Amplitude client
        model_provider: LLM provider name
        model_name: Model name
        input_content: Input content
        output_content: Output content
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        latency_ms: Response latency in milliseconds
        user_id: User identifier
        device_id: Device identifier
        **kwargs: Additional parameters
    """
    input_messages = None
    if input_content:
        input_messages = [{"role": "user", "content": input_content}]
    
    total_tokens = None
    if input_tokens is not None and output_tokens is not None:
        total_tokens = input_tokens + output_tokens
    
    # Calculate cost
    ai_config = AIConfig()
    cost_usd = None
    if input_tokens and output_tokens:
        cost_usd = ai_config.calculate_cost(model_provider, model_name, input_tokens, output_tokens)
    
    emit_llm_message(
        amplitude_client,
        user_id=user_id,
        device_id=device_id,
        model_provider=model_provider,
        model_name=model_name,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        latency_ms=latency_ms,
        cost_usd=cost_usd,
        input_messages=input_messages,
        output_content=output_content,
        **kwargs
    )