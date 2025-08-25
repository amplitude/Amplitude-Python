"""Anthropic wrapper for Amplitude LLM observability."""

import time
from typing import Optional, Dict, Any, List, Union

try:
    from anthropic import Anthropic as OriginalAnthropic
    from anthropic import AsyncAnthropic as OriginalAsyncAnthropic
    _ANTHROPIC_AVAILABLE = True
except ImportError:
    _ANTHROPIC_AVAILABLE = False
    # Create dummy classes for type hints
    class OriginalAnthropic:
        pass
    class OriginalAsyncAnthropic:
        pass

from amplitude.client import Amplitude
from .base import BaseLLMWrapper
from .config import AIConfig
from .events import get_current_session_id


class Anthropic(BaseLLMWrapper):
    """Anthropic wrapper with Amplitude observability.
    
    Drop-in replacement for anthropic.Anthropic that automatically tracks LLM usage.
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 amplitude_client: Optional[Amplitude] = None,
                 ai_config: Optional[AIConfig] = None,
                 auto_start_session: bool = True,
                 **kwargs):
        """Initialize Anthropic wrapper.
        
        Args:
            api_key: Anthropic API key
            amplitude_client: Amplitude client for event tracking
            ai_config: AI observability configuration
            auto_start_session: Whether to automatically start a new session
            **kwargs: Additional Anthropic client parameters
        """
        if not _ANTHROPIC_AVAILABLE:
            raise ImportError("Anthropic not installed. Install with: pip install anthropic")
        
        # Initialize base wrapper
        super().__init__(
            amplitude_client=amplitude_client,
            ai_config=ai_config,
            auto_start_session=auto_start_session
        )
        
        # Initialize Anthropic client
        self._client = OriginalAnthropic(api_key=api_key, **kwargs)
        
        # Store original methods for delegation
        self._original_create = self._client.messages.create
        
        # Replace methods with instrumented versions
        self._client.messages.create = self._instrumented_messages_create
    
    def get_provider_name(self) -> str:
        """Get the provider name."""
        return "anthropic"
    
    def _extract_token_usage(self, response_data: Any) -> tuple[Optional[int], Optional[int], Optional[int]]:
        """Extract token usage from Anthropic response."""
        if hasattr(response_data, 'usage') and response_data.usage:
            input_tokens = getattr(response_data.usage, 'input_tokens', None)
            output_tokens = getattr(response_data.usage, 'output_tokens', None)
            total_tokens = None
            if input_tokens is not None and output_tokens is not None:
                total_tokens = input_tokens + output_tokens
            return input_tokens, output_tokens, total_tokens
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
                # Handle Anthropic message format
                content = msg.content
                if isinstance(content, list):
                    # Handle structured content
                    content_items = []
                    for item in content:
                        if isinstance(item, dict):
                            content_items.append(item)
                        elif hasattr(item, 'type') and hasattr(item, 'text'):
                            content_items.append({"type": item.type, "text": item.text})
                    content = content_items
                result.append({"role": msg.role, "content": content})
        return result if result else None
    
    def _extract_output_content(self, response_data: Any) -> Optional[str]:
        """Extract output content from Anthropic response."""
        if hasattr(response_data, 'content') and response_data.content:
            # Anthropic returns content as a list of content blocks
            content_parts = []
            for content_block in response_data.content:
                if hasattr(content_block, 'text'):
                    content_parts.append(content_block.text)
                elif isinstance(content_block, dict) and 'text' in content_block:
                    content_parts.append(content_block['text'])
            return ' '.join(content_parts) if content_parts else None
        return None
    
    def _extract_finish_reason(self, response_data: Any) -> Optional[str]:
        """Extract finish reason from Anthropic response."""
        if hasattr(response_data, 'stop_reason'):
            return response_data.stop_reason
        return None
    
    def _instrumented_messages_create(self, *args, **kwargs):
        """Instrumented version of messages.create."""
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
            # Make the actual Anthropic call
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
            if hasattr(response, 'content') and response.content:
                for content_block in response.content:
                    if hasattr(content_block, 'type') and content_block.type == 'tool_use':
                        self._capture_tool_call_event(
                            tool_name=getattr(content_block, 'name', 'unknown'),
                            tool_parameters=getattr(content_block, 'input', None),
                            user_id=user_id,
                            device_id=device_id
                        )
            
            return response
            
        except Exception as e:
            # Capture error event
            self._capture_error_event(e, kwargs, user_id, device_id)
            raise
    
    # Delegate all other attributes to the underlying Anthropic client
    def __getattr__(self, name):
        return getattr(self._client, name)


class AsyncAnthropic(BaseLLMWrapper):
    """Async Anthropic wrapper with Amplitude observability.
    
    Drop-in replacement for anthropic.AsyncAnthropic that automatically tracks LLM usage.
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 amplitude_client: Optional[Amplitude] = None,
                 ai_config: Optional[AIConfig] = None,
                 auto_start_session: bool = True,
                 **kwargs):
        """Initialize AsyncAnthropic wrapper.
        
        Args:
            api_key: Anthropic API key
            amplitude_client: Amplitude client for event tracking
            ai_config: AI observability configuration
            auto_start_session: Whether to automatically start a new session
            **kwargs: Additional Anthropic client parameters
        """
        if not _ANTHROPIC_AVAILABLE:
            raise ImportError("Anthropic not installed. Install with: pip install anthropic")
        
        # Initialize base wrapper
        super().__init__(
            amplitude_client=amplitude_client,
            ai_config=ai_config,
            auto_start_session=auto_start_session
        )
        
        # Initialize AsyncAnthropic client
        self._client = OriginalAsyncAnthropic(api_key=api_key, **kwargs)
        
        # Store original methods for delegation
        self._original_create = self._client.messages.create
        
        # Replace methods with instrumented versions
        self._client.messages.create = self._instrumented_messages_create
    
    def get_provider_name(self) -> str:
        """Get the provider name."""
        return "anthropic"
    
    def _extract_token_usage(self, response_data: Any) -> tuple[Optional[int], Optional[int], Optional[int]]:
        """Extract token usage from Anthropic response."""
        if hasattr(response_data, 'usage') and response_data.usage:
            input_tokens = getattr(response_data.usage, 'input_tokens', None)
            output_tokens = getattr(response_data.usage, 'output_tokens', None)
            total_tokens = None
            if input_tokens is not None and output_tokens is not None:
                total_tokens = input_tokens + output_tokens
            return input_tokens, output_tokens, total_tokens
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
                # Handle Anthropic message format
                content = msg.content
                if isinstance(content, list):
                    # Handle structured content
                    content_items = []
                    for item in content:
                        if isinstance(item, dict):
                            content_items.append(item)
                        elif hasattr(item, 'type') and hasattr(item, 'text'):
                            content_items.append({"type": item.type, "text": item.text})
                    content = content_items
                result.append({"role": msg.role, "content": content})
        return result if result else None
    
    def _extract_output_content(self, response_data: Any) -> Optional[str]:
        """Extract output content from Anthropic response."""
        if hasattr(response_data, 'content') and response_data.content:
            # Anthropic returns content as a list of content blocks
            content_parts = []
            for content_block in response_data.content:
                if hasattr(content_block, 'text'):
                    content_parts.append(content_block.text)
                elif isinstance(content_block, dict) and 'text' in content_block:
                    content_parts.append(content_block['text'])
            return ' '.join(content_parts) if content_parts else None
        return None
    
    def _extract_finish_reason(self, response_data: Any) -> Optional[str]:
        """Extract finish reason from Anthropic response."""
        if hasattr(response_data, 'stop_reason'):
            return response_data.stop_reason
        return None
    
    async def _instrumented_messages_create(self, *args, **kwargs):
        """Instrumented version of async messages.create."""
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
            # Make the actual Anthropic call
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
            if hasattr(response, 'content') and response.content:
                for content_block in response.content:
                    if hasattr(content_block, 'type') and content_block.type == 'tool_use':
                        self._capture_tool_call_event(
                            tool_name=getattr(content_block, 'name', 'unknown'),
                            tool_parameters=getattr(content_block, 'input', None),
                            user_id=user_id,
                            device_id=device_id
                        )
            
            return response
            
        except Exception as e:
            # Capture error event
            self._capture_error_event(e, kwargs, user_id, device_id)
            raise
    
    # Delegate all other attributes to the underlying AsyncAnthropic client
    def __getattr__(self, name):
        return getattr(self._client, name)