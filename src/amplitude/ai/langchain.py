"""LangChain callback handler for Amplitude LLM observability."""

import time
import uuid
from typing import Optional, Dict, Any, List, Union

try:
    from langchain_core.callbacks import BaseCallbackHandler
    from langchain_core.messages import BaseMessage
    from langchain_core.outputs import LLMResult
    from langchain_core.agents import AgentAction, AgentFinish
    _LANGCHAIN_AVAILABLE = True
except ImportError:
    _LANGCHAIN_AVAILABLE = False
    # Create dummy classes for type hints
    class BaseCallbackHandler:
        pass
    class BaseMessage:
        pass
    class LLMResult:
        pass
    class AgentAction:
        pass
    class AgentFinish:
        pass

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


class AmplitudeLangChainCallback(BaseCallbackHandler):
    """LangChain callback handler that sends observability events to Amplitude.
    
    This handler automatically captures LLM interactions when using LangChain
    and emits appropriate events following the schema.md specification.
    """
    
    def __init__(self, 
                 amplitude_client: Amplitude,
                 ai_config: Optional[AIConfig] = None,
                 session_id: Optional[str] = None,
                 user_id: Optional[str] = None,
                 device_id: Optional[str] = None,
                 auto_start_session: bool = True):
        """Initialize the Amplitude LangChain callback handler.
        
        Args:
            amplitude_client: Amplitude client for event tracking
            ai_config: AI observability configuration
            session_id: Optional session ID (will generate if not provided)
            user_id: Optional user ID for events
            device_id: Optional device ID for events
            auto_start_session: Whether to automatically emit run_started event
        """
        if not _LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain not installed. Install with: pip install langchain-core")
        
        super().__init__()
        
        self.amplitude_client = amplitude_client
        self.ai_config = ai_config or AIConfig()
        self.user_id = user_id
        self.device_id = device_id
        
        # Session management
        if session_id:
            set_session_id(session_id)
        self.session_id = get_current_session_id()
        self.session_start_time = time.time()
        
        # Track session stats
        self.session_stats = {
            "total_messages": 0,
            "total_tokens": 0,
            "total_cost_usd": 0.0,
            "chain_runs": 0,
            "tool_calls": 0
        }
        
        # Track ongoing operations
        self._run_start_times = {}
        self._llm_start_times = {}
        self._tool_start_times = {}
        
        if auto_start_session:
            self._emit_run_started()
    
    def _emit_event(self, event) -> None:
        """Emit an event to Amplitude."""
        if self.ai_config.async_event_emission:
            # Emit asynchronously to avoid blocking
            import threading
            def emit():
                try:
                    self.amplitude_client.track(event)
                except Exception:
                    pass  # Silently ignore emission errors
            thread = threading.Thread(target=emit, daemon=True)
            thread.start()
        else:
            try:
                self.amplitude_client.track(event)
            except Exception:
                pass  # Silently ignore emission errors
    
    def _emit_run_started(self):
        """Emit run started event."""
        event = LLMRunStartedEvent(
            session_id=self.session_id,
            user_id=self.user_id,
            device_id=self.device_id,
            model_provider="langchain"
        )
        self._emit_event(event)
    
    def _emit_run_finished(self, success: bool = True, error_message: Optional[str] = None):
        """Emit run finished event."""
        duration_ms = int((time.time() - self.session_start_time) * 1000)
        
        event = LLMRunFinishedEvent(
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
        self._emit_event(event)
    
    def _calculate_cost(self, provider: str, model: str, input_tokens: int, output_tokens: int) -> Optional[float]:
        """Calculate cost using AI config."""
        return self.ai_config.calculate_cost(provider, model, input_tokens, output_tokens)
    
    def _extract_provider_and_model(self, serialized: Dict[str, Any]) -> tuple[str, str]:
        """Extract provider and model name from serialized LLM info."""
        # Try to extract provider from the class name or module
        class_name = serialized.get("name", "")
        module_name = serialized.get("id", [""])[-1] if serialized.get("id") else ""
        
        provider = "unknown"
        model = "unknown"
        
        # Common patterns for different providers
        if "openai" in class_name.lower() or "openai" in module_name.lower():
            provider = "openai"
        elif "anthropic" in class_name.lower() or "anthropic" in module_name.lower():
            provider = "anthropic"
        elif "google" in class_name.lower() or "gemini" in class_name.lower():
            provider = "google"
        elif "cohere" in class_name.lower():
            provider = "cohere"
        elif "huggingface" in class_name.lower() or "transformers" in class_name.lower():
            provider = "huggingface"
        
        # Try to extract model from kwargs
        kwargs = serialized.get("kwargs", {})
        model_candidates = [
            kwargs.get("model"),
            kwargs.get("model_name"),
            kwargs.get("model_id"),
        ]
        
        for candidate in model_candidates:
            if candidate:
                model = candidate
                break
        
        return provider, model
    
    # Chain callbacks
    def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], *, run_id: uuid.UUID, **kwargs) -> None:
        """Called when a chain starts running."""
        self._run_start_times[str(run_id)] = time.time()
        self.session_stats["chain_runs"] += 1
    
    def on_chain_end(self, outputs: Dict[str, Any], *, run_id: uuid.UUID, **kwargs) -> None:
        """Called when a chain ends successfully."""
        run_id_str = str(run_id)
        if run_id_str in self._run_start_times:
            del self._run_start_times[run_id_str]
    
    def on_chain_error(self, error: Exception, *, run_id: uuid.UUID, **kwargs) -> None:
        """Called when a chain encounters an error."""
        run_id_str = str(run_id)
        if run_id_str in self._run_start_times:
            del self._run_start_times[run_id_str]
    
    # LLM callbacks
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], *, run_id: uuid.UUID, **kwargs) -> None:
        """Called when LLM starts generating."""
        self._llm_start_times[str(run_id)] = time.time()
        
        # Emit user message events for prompts if not in privacy mode
        if not self.ai_config.should_exclude_content("input"):
            for prompt in prompts:
                if prompt:
                    content = self.ai_config.truncate_content(prompt)
                    event = UserMessageEvent(
                        session_id=self.session_id,
                        user_id=self.user_id,
                        device_id=self.device_id,
                        content=content,
                        message_type="text"
                    )
                    self._emit_event(event)
    
    def on_llm_end(self, response: LLMResult, *, run_id: uuid.UUID, **kwargs) -> None:
        """Called when LLM ends successfully."""
        run_id_str = str(run_id)
        start_time = self._llm_start_times.get(run_id_str)
        
        if start_time:
            latency_ms = int((time.time() - start_time) * 1000)
            del self._llm_start_times[run_id_str]
        else:
            latency_ms = None
        
        # Extract token usage from response
        input_tokens = None
        output_tokens = None
        total_tokens = None
        
        if hasattr(response, 'llm_output') and response.llm_output:
            token_usage = response.llm_output.get('token_usage', {})
            input_tokens = token_usage.get('prompt_tokens')
            output_tokens = token_usage.get('completion_tokens')
            total_tokens = token_usage.get('total_tokens')
        
        # Update session stats
        self.session_stats["total_messages"] += 1
        if total_tokens:
            self.session_stats["total_tokens"] += total_tokens
        
        # Extract provider and model info
        provider, model = self._extract_provider_and_model(kwargs.get('invocation_params', {}))
        
        # Calculate cost
        cost_usd = None
        if input_tokens and output_tokens and self.ai_config.cost_tracking:
            cost_usd = self._calculate_cost(provider, model, input_tokens, output_tokens)
            if cost_usd:
                self.session_stats["total_cost_usd"] += cost_usd
        
        # Extract output content
        output_content = None
        if response.generations and not self.ai_config.should_exclude_content("output"):
            # Get text from first generation
            if response.generations[0]:
                generation = response.generations[0][0]
                if hasattr(generation, 'text'):
                    output_content = self.ai_config.truncate_content(generation.text)
        
        # Emit LLM message event
        event = LLMMessageEvent(
            session_id=self.session_id,
            user_id=self.user_id,
            device_id=self.device_id,
            model_provider=provider,
            model_name=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            output_content=output_content
        )
        self._emit_event(event)
    
    def on_llm_error(self, error: Exception, *, run_id: uuid.UUID, **kwargs) -> None:
        """Called when LLM encounters an error."""
        run_id_str = str(run_id)
        start_time = self._llm_start_times.get(run_id_str)
        
        if start_time:
            latency_ms = int((time.time() - start_time) * 1000)
            del self._llm_start_times[run_id_str]
        else:
            latency_ms = None
        
        # Emit error event
        provider, model = self._extract_provider_and_model(kwargs.get('invocation_params', {}))
        
        event = LLMMessageEvent(
            session_id=self.session_id,
            user_id=self.user_id,
            device_id=self.device_id,
            model_provider=provider,
            model_name=model,
            latency_ms=latency_ms,
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
    
    # Tool/Agent callbacks
    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, *, run_id: uuid.UUID, **kwargs) -> None:
        """Called when a tool starts running."""
        self._tool_start_times[str(run_id)] = time.time()
        self.session_stats["tool_calls"] += 1
    
    def on_tool_end(self, output: str, *, run_id: uuid.UUID, **kwargs) -> None:
        """Called when a tool ends successfully."""
        run_id_str = str(run_id)
        start_time = self._tool_start_times.get(run_id_str)
        
        execution_time_ms = None
        if start_time:
            execution_time_ms = int((time.time() - start_time) * 1000)
            del self._tool_start_times[run_id_str]
        
        # Emit tool called event
        event = ToolCalledEvent(
            session_id=self.session_id,
            user_id=self.user_id,
            device_id=self.device_id,
            tool_name=kwargs.get('name', 'unknown'),
            tool_result={"output": output} if not self.ai_config.should_exclude_content("tool_results") else None,
            execution_time_ms=execution_time_ms,
            success=True
        )
        self._emit_event(event)
    
    def on_tool_error(self, error: Exception, *, run_id: uuid.UUID, **kwargs) -> None:
        """Called when a tool encounters an error."""
        run_id_str = str(run_id)
        start_time = self._tool_start_times.get(run_id_str)
        
        execution_time_ms = None
        if start_time:
            execution_time_ms = int((time.time() - start_time) * 1000)
            del self._tool_start_times[run_id_str]
        
        # Emit tool error event
        event = ToolCalledEvent(
            session_id=self.session_id,
            user_id=self.user_id,
            device_id=self.device_id,
            tool_name=kwargs.get('name', 'unknown'),
            execution_time_ms=execution_time_ms,
            success=False,
            error_message=str(error)
        )
        self._emit_event(event)
    
    def on_agent_action(self, action: AgentAction, *, run_id: uuid.UUID, **kwargs) -> None:
        """Called when an agent takes an action."""
        # This is handled by on_tool_start/end
        pass
    
    def on_agent_finish(self, finish: AgentFinish, *, run_id: uuid.UUID, **kwargs) -> None:
        """Called when an agent finishes."""
        # Mark successful completion
        self._emit_run_finished(success=True)
    
    def __del__(self):
        """Cleanup when handler is destroyed."""
        try:
            self._emit_run_finished(success=True)
        except Exception:
            pass  # Ignore errors during cleanup