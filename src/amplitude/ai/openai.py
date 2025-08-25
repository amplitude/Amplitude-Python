"""OpenAI wrapper for Amplitude LLM observability."""

import time
from typing import Optional, Dict, Any, List, Union

try:
    from openai import OpenAI as OriginalOpenAI
    from openai import AsyncOpenAI as OriginalAsyncOpenAI
    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False
    # Create dummy classes for type hints
    class OriginalOpenAI:
        pass
    class OriginalAsyncOpenAI:
        pass

from amplitude.client import Amplitude
from .base import BaseLLMWrapper
from .config import AIConfig
from .events import get_current_session_id


class OpenAI(BaseLLMWrapper):
    """OpenAI wrapper with Amplitude observability.
    
    Drop-in replacement for openai.OpenAI that automatically tracks LLM usage.
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 amplitude_client: Optional[Amplitude] = None,
                 ai_config: Optional[AIConfig] = None,
                 auto_start_session: bool = True,
                 **kwargs):
        """Initialize OpenAI wrapper.
        
        Args:
            api_key: OpenAI API key
            amplitude_client: Amplitude client for event tracking
            ai_config: AI observability configuration
            auto_start_session: Whether to automatically start a new session
            **kwargs: Additional OpenAI client parameters
        """
        if not _OPENAI_AVAILABLE:
            raise ImportError("OpenAI not installed. Install with: pip install openai")
        
        # Initialize base wrapper
        super().__init__(
            amplitude_client=amplitude_client,
            ai_config=ai_config,
            auto_start_session=auto_start_session
        )
        
        # Initialize OpenAI client
        self._client = OriginalOpenAI(api_key=api_key, **kwargs)
        
        # Store original methods for delegation
        self._original_create = self._client.chat.completions.create
        
        # Replace methods with instrumented versions
        self._client.chat.completions.create = self._instrumented_chat_create
    
    def get_provider_name(self) -> str:
        """Get the provider name."""
        return "openai"
    
    def _extract_token_usage(self, response_data: Any) -> tuple[Optional[int], Optional[int], Optional[int]]:
        """Extract token usage from OpenAI response."""
        if hasattr(response_data, 'usage') and response_data.usage:
            return (
                getattr(response_data.usage, 'prompt_tokens', None),
                getattr(response_data.usage, 'completion_tokens', None),
                getattr(response_data.usage, 'total_tokens', None)
            )
        return None, None, None
    
    def _extract_model_name(self, request_data: Dict[str, Any], response_data: Any) -> Optional[str]:
        """Extract model name from request or response."""
        if hasattr(response_data, 'model'):
            return response_data.model
        return request_data.get('model')
    
    def _extract_input_messages(self, request_data: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Extract input messages from request."""
        messages = request_data.get('messages')
        if not messages:
            return None
        
        # Convert to serializable format
        result = []
        for msg in messages:
            if isinstance(msg, dict):
                result.append(msg)
            elif hasattr(msg, 'role') and hasattr(msg, 'content'):
                result.append({"role": msg.role, "content": msg.content})
        return result if result else None
    
    def _extract_output_content(self, response_data: Any) -> Optional[str]:
        """Extract output content from OpenAI response."""
        if hasattr(response_data, 'choices') and response_data.choices:
            choice = response_data.choices[0]
            if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                return choice.message.content
        return None
    
    def _extract_finish_reason(self, response_data: Any) -> Optional[str]:
        """Extract finish reason from OpenAI response."""
        if hasattr(response_data, 'choices') and response_data.choices:
            choice = response_data.choices[0]
            if hasattr(choice, 'finish_reason'):
                return choice.finish_reason
        return None
    
    def _instrumented_chat_create(self, *args, **kwargs):
        """Instrumented version of chat.completions.create."""
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
            # Make the actual OpenAI call
            response = self._original_create(*args, **kwargs)
            
            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Capture observability data
            self._capture_message_event(
                request_data=kwargs,
                response_data=response,
                latency_ms=latency_ms,
                user_id=user_id,
                device_id=device_id
            )
            
            # Extract and capture tool calls if present
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                if hasattr(choice, 'message') and hasattr(choice.message, 'tool_calls') and choice.message.tool_calls:
                    for tool_call in choice.message.tool_calls:
                        if hasattr(tool_call, 'function'):
                            self._capture_tool_call_event(
                                tool_name=tool_call.function.name,
                                tool_parameters=tool_call.function.arguments,
                                user_id=user_id,
                                device_id=device_id
                            )
            
            return response
            
        except Exception as e:
            # Capture error event
            self._capture_error_event(e, kwargs, user_id, device_id)
            raise
    
    # Delegate all other attributes to the underlying OpenAI client
    def __getattr__(self, name):
        return getattr(self._client, name)


class AsyncOpenAI(BaseLLMWrapper):
    """Async OpenAI wrapper with Amplitude observability.
    
    Drop-in replacement for openai.AsyncOpenAI that automatically tracks LLM usage.
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 amplitude_client: Optional[Amplitude] = None,
                 ai_config: Optional[AIConfig] = None,
                 auto_start_session: bool = True,
                 **kwargs):
        """Initialize AsyncOpenAI wrapper.
        
        Args:
            api_key: OpenAI API key
            amplitude_client: Amplitude client for event tracking
            ai_config: AI observability configuration
            auto_start_session: Whether to automatically start a new session
            **kwargs: Additional OpenAI client parameters
        """
        if not _OPENAI_AVAILABLE:
            raise ImportError("OpenAI not installed. Install with: pip install openai")
        
        # Initialize base wrapper
        super().__init__(
            amplitude_client=amplitude_client,
            ai_config=ai_config,
            auto_start_session=auto_start_session
        )
        
        # Initialize AsyncOpenAI client
        self._client = OriginalAsyncOpenAI(api_key=api_key, **kwargs)
        
        # Store original methods for delegation
        self._original_create = self._client.chat.completions.create
        
        # Replace methods with instrumented versions
        self._client.chat.completions.create = self._instrumented_chat_create
    
    def get_provider_name(self) -> str:
        """Get the provider name."""
        return "openai"
    
    def _extract_token_usage(self, response_data: Any) -> tuple[Optional[int], Optional[int], Optional[int]]:
        """Extract token usage from OpenAI response."""
        if hasattr(response_data, 'usage') and response_data.usage:
            return (
                getattr(response_data.usage, 'prompt_tokens', None),
                getattr(response_data.usage, 'completion_tokens', None),
                getattr(response_data.usage, 'total_tokens', None)
            )
        return None, None, None
    
    def _extract_model_name(self, request_data: Dict[str, Any], response_data: Any) -> Optional[str]:
        """Extract model name from request or response."""
        if hasattr(response_data, 'model'):
            return response_data.model
        return request_data.get('model')
    
    def _extract_input_messages(self, request_data: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Extract input messages from request."""
        messages = request_data.get('messages')
        if not messages:
            return None
        
        # Convert to serializable format
        result = []
        for msg in messages:
            if isinstance(msg, dict):
                result.append(msg)
            elif hasattr(msg, 'role') and hasattr(msg, 'content'):
                result.append({"role": msg.role, "content": msg.content})
        return result if result else None
    
    def _extract_output_content(self, response_data: Any) -> Optional[str]:
        """Extract output content from OpenAI response."""
        if hasattr(response_data, 'choices') and response_data.choices:
            choice = response_data.choices[0]
            if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                return choice.message.content
        return None
    
    def _extract_finish_reason(self, response_data: Any) -> Optional[str]:
        """Extract finish reason from OpenAI response."""
        if hasattr(response_data, 'choices') and response_data.choices:
            choice = response_data.choices[0]
            if hasattr(choice, 'finish_reason'):
                return choice.finish_reason
        return None
    
    async def _instrumented_chat_create(self, *args, **kwargs):
        """Instrumented version of async chat.completions.create."""
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
            # Make the actual OpenAI call
            response = await self._original_create(*args, **kwargs)
            
            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Capture observability data
            self._capture_message_event(
                request_data=kwargs,
                response_data=response,
                latency_ms=latency_ms,
                user_id=user_id,
                device_id=device_id
            )
            
            # Extract and capture tool calls if present
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                if hasattr(choice, 'message') and hasattr(choice.message, 'tool_calls') and choice.message.tool_calls:
                    for tool_call in choice.message.tool_calls:
                        if hasattr(tool_call, 'function'):
                            self._capture_tool_call_event(
                                tool_name=tool_call.function.name,
                                tool_parameters=tool_call.function.arguments,
                                user_id=user_id,
                                device_id=device_id
                            )
            
            return response
            
        except Exception as e:
            # Capture error event
            self._capture_error_event(e, kwargs, user_id, device_id)
            raise
    
    # Delegate all other attributes to the underlying AsyncOpenAI client
    def __getattr__(self, name):
        return getattr(self._client, name)