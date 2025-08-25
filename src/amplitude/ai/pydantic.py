"""Pydantic AI wrapper for Amplitude LLM observability."""

import time
import asyncio
from typing import Optional, Dict, Any, List, Union, Type, TypeVar

try:
    from pydantic_ai import Agent, ModelRetry
    from pydantic_ai.models import Model
    from pydantic_ai.result import RunResult
    _PYDANTIC_AI_AVAILABLE = True
except ImportError:
    _PYDANTIC_AI_AVAILABLE = False
    # Create dummy classes for type hints
    class Agent:
        pass
    class ModelRetry:
        pass
    class Model:
        pass
    class RunResult:
        pass

from amplitude.client import Amplitude
from .base import BaseLLMWrapper
from .config import AIConfig
from .events import get_current_session_id

T = TypeVar('T')


class PydanticAIWrapper(BaseLLMWrapper):
    """Pydantic AI wrapper with Amplitude observability.
    
    This wrapper instruments Pydantic AI agents to automatically track LLM usage
    while maintaining the structured output capabilities of Pydantic AI.
    """
    
    def __init__(self, 
                 agent: Optional[Agent] = None,
                 amplitude_client: Optional[Amplitude] = None,
                 ai_config: Optional[AIConfig] = None,
                 auto_start_session: bool = True,
                 **kwargs):
        """Initialize Pydantic AI wrapper.
        
        Args:
            agent: Pydantic AI agent to wrap (can be None if creating agent later)
            amplitude_client: Amplitude client for event tracking
            ai_config: AI observability configuration
            auto_start_session: Whether to automatically start a new session
            **kwargs: Additional parameters
        """
        if not _PYDANTIC_AI_AVAILABLE:
            raise ImportError("Pydantic AI not installed. Install with: pip install pydantic-ai")
        
        # Initialize base wrapper
        super().__init__(
            amplitude_client=amplitude_client,
            ai_config=ai_config,
            auto_start_session=auto_start_session
        )
        
        self._agent = agent
        self._original_run = None
        self._original_run_async = None
        
        if agent:
            self._wrap_agent(agent)
    
    def wrap_agent(self, agent: Agent) -> Agent:
        """Wrap a Pydantic AI agent with observability.
        
        Args:
            agent: The Pydantic AI agent to wrap
            
        Returns:
            The wrapped agent (same instance, but with instrumented methods)
        """
        self._agent = agent
        self._wrap_agent(agent)
        return agent
    
    def _wrap_agent(self, agent: Agent):
        """Internal method to wrap agent methods."""
        # Store original methods
        self._original_run = agent.run
        self._original_run_async = agent.run_async
        
        # Replace with instrumented versions
        agent.run = self._instrumented_run
        agent.run_async = self._instrumented_run_async
    
    def get_provider_name(self) -> str:
        """Get the provider name."""
        if self._agent and hasattr(self._agent, 'model'):
            model = self._agent.model
            if hasattr(model, '__class__'):
                model_class = model.__class__.__name__.lower()
                if 'openai' in model_class:
                    return "openai"
                elif 'anthropic' in model_class:
                    return "anthropic"
                elif 'google' in model_class or 'gemini' in model_class:
                    return "google"
        return "pydantic-ai"
    
    def _extract_token_usage(self, response_data: Any) -> tuple[Optional[int], Optional[int], Optional[int]]:
        """Extract token usage from Pydantic AI response."""
        if hasattr(response_data, 'usage_cost') and response_data.usage_cost:
            usage = response_data.usage_cost
            # Pydantic AI might have different attribute names
            input_tokens = getattr(usage, 'input_tokens', None) or getattr(usage, 'prompt_tokens', None)
            output_tokens = getattr(usage, 'output_tokens', None) or getattr(usage, 'completion_tokens', None)
            total_tokens = getattr(usage, 'total_tokens', None)
            
            if total_tokens is None and input_tokens is not None and output_tokens is not None:
                total_tokens = input_tokens + output_tokens
                
            return input_tokens, output_tokens, total_tokens
        return None, None, None
    
    def _extract_model_name(self, request_data: Dict[str, Any], response_data: Any) -> Optional[str]:
        """Extract model name from request or response."""
        if hasattr(response_data, 'model_name'):
            return response_data.model_name
        
        if self._agent and hasattr(self._agent, 'model'):
            model = self._agent.model
            if hasattr(model, 'name'):
                return model.name
            elif hasattr(model, 'model_name'):
                return model.model_name
        
        return None
    
    def _extract_input_messages(self, request_data: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Extract input messages from request."""
        user_prompt = request_data.get('user_prompt')
        if user_prompt:
            return [{"role": "user", "content": str(user_prompt)}]
        return None
    
    def _extract_output_content(self, response_data: Any) -> Optional[str]:
        """Extract output content from Pydantic AI response."""
        if hasattr(response_data, 'data'):
            # Pydantic AI returns structured data, convert to string
            data = response_data.data
            if isinstance(data, str):
                return data
            else:
                # For structured responses, return JSON representation
                try:
                    import json
                    return json.dumps(data, default=str)
                except Exception:
                    return str(data)
        return None
    
    def _extract_finish_reason(self, response_data: Any) -> Optional[str]:
        """Extract finish reason from Pydantic AI response."""
        # Pydantic AI might not expose finish reasons directly
        return "completed" if hasattr(response_data, 'data') else None
    
    def _instrumented_run(self, user_prompt, *, message_history=None, **kwargs):
        """Instrumented version of agent.run()."""
        # Extract Amplitude-specific parameters
        user_id = kwargs.pop('amplitude_user_id', None)
        device_id = kwargs.pop('amplitude_device_id', None)
        session_id = kwargs.pop('amplitude_session_id', None)
        
        # Set session ID if provided
        if session_id:
            from .events import set_session_id
            set_session_id(session_id)
        
        start_time = time.time()
        
        try:
            # Make the actual Pydantic AI call
            result = self._original_run(user_prompt, message_history=message_history, **kwargs)
            
            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Build request data for observability
            request_data = {
                'user_prompt': user_prompt,
                'message_history': message_history,
                **kwargs
            }
            
            # Capture observability data
            self._capture_message_event(
                request_data=request_data,
                response_data=result,
                latency_ms=latency_ms,
                user_id=user_id,
                device_id=device_id
            )
            
            # Capture tool calls if present (Pydantic AI supports function calling)
            if hasattr(result, 'all_messages'):
                for message in result.all_messages():
                    if hasattr(message, 'tool_calls') and message.tool_calls:
                        for tool_call in message.tool_calls:
                            self._capture_tool_call_event(
                                tool_name=getattr(tool_call, 'name', 'unknown'),
                                tool_parameters=getattr(tool_call, 'arguments', None),
                                user_id=user_id,
                                device_id=device_id
                            )
            
            return result
            
        except Exception as e:
            # Capture error event
            request_data = {
                'user_prompt': user_prompt,
                'message_history': message_history,
                **kwargs
            }
            self._capture_error_event(e, request_data, user_id, device_id)
            raise
    
    async def _instrumented_run_async(self, user_prompt, *, message_history=None, **kwargs):
        """Instrumented version of agent.run_async()."""
        # Extract Amplitude-specific parameters
        user_id = kwargs.pop('amplitude_user_id', None)
        device_id = kwargs.pop('amplitude_device_id', None)
        session_id = kwargs.pop('amplitude_session_id', None)
        
        # Set session ID if provided
        if session_id:
            from .events import set_session_id
            set_session_id(session_id)
        
        start_time = time.time()
        
        try:
            # Make the actual Pydantic AI call
            result = await self._original_run_async(user_prompt, message_history=message_history, **kwargs)
            
            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Build request data for observability
            request_data = {
                'user_prompt': user_prompt,
                'message_history': message_history,
                **kwargs
            }
            
            # Capture observability data
            self._capture_message_event(
                request_data=request_data,
                response_data=result,
                latency_ms=latency_ms,
                user_id=user_id,
                device_id=device_id
            )
            
            # Capture tool calls if present
            if hasattr(result, 'all_messages'):
                for message in result.all_messages():
                    if hasattr(message, 'tool_calls') and message.tool_calls:
                        for tool_call in message.tool_calls:
                            self._capture_tool_call_event(
                                tool_name=getattr(tool_call, 'name', 'unknown'),
                                tool_parameters=getattr(tool_call, 'arguments', None),
                                user_id=user_id,
                                device_id=device_id
                            )
            
            return result
            
        except Exception as e:
            # Capture error event
            request_data = {
                'user_prompt': user_prompt,
                'message_history': message_history,
                **kwargs
            }
            self._capture_error_event(e, request_data, user_id, device_id)
            raise
    
    # Convenience methods for creating and wrapping agents
    @classmethod
    def create_agent(cls,
                    model: Union[Model, str],
                    result_type: Type[T] = str,
                    amplitude_client: Optional[Amplitude] = None,
                    ai_config: Optional[AIConfig] = None,
                    **agent_kwargs) -> 'PydanticAIWrapper':
        """Create a new Pydantic AI agent with Amplitude observability.
        
        Args:
            model: The model to use (Pydantic AI model or model name)
            result_type: The expected result type (Pydantic model or basic type)
            amplitude_client: Amplitude client for event tracking
            ai_config: AI observability configuration
            **agent_kwargs: Additional arguments for Agent constructor
            
        Returns:
            PydanticAIWrapper instance with the created agent
        """
        if not _PYDANTIC_AI_AVAILABLE:
            raise ImportError("Pydantic AI not installed. Install with: pip install pydantic-ai")
        
        # Create the Pydantic AI agent
        agent = Agent(model, result_type=result_type, **agent_kwargs)
        
        # Create and return wrapper
        wrapper = cls(
            agent=agent,
            amplitude_client=amplitude_client,
            ai_config=ai_config
        )
        
        return wrapper
    
    @property
    def agent(self) -> Optional[Agent]:
        """Get the wrapped agent."""
        return self._agent
    
    def __getattr__(self, name):
        """Delegate attributes to the wrapped agent."""
        if self._agent:
            return getattr(self._agent, name)
        raise AttributeError(f"'PydanticAIWrapper' object has no attribute '{name}'")