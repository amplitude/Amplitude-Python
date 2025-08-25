"""Google Gemini wrapper for Amplitude LLM observability."""

import time
from typing import Optional, Dict, Any, List, Union

try:
    import google.generativeai as genai
    from google.generativeai import GenerativeModel
    _GOOGLE_AVAILABLE = True
except ImportError:
    _GOOGLE_AVAILABLE = False
    # Create dummy classes for type hints
    class GenerativeModel:
        pass

from amplitude.client import Amplitude
from .base import BaseLLMWrapper
from .config import AIConfig
from .events import get_current_session_id


class GoogleGenerativeAI(BaseLLMWrapper):
    """Google Gemini wrapper with Amplitude observability.
    
    Wrapper for google.generativeai that automatically tracks LLM usage.
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 model_name: str = "gemini-pro",
                 amplitude_client: Optional[Amplitude] = None,
                 ai_config: Optional[AIConfig] = None,
                 auto_start_session: bool = True,
                 **kwargs):
        """Initialize Google Gemini wrapper.
        
        Args:
            api_key: Google API key
            model_name: Gemini model name (gemini-pro, gemini-1.5-pro, etc.)
            amplitude_client: Amplitude client for event tracking
            ai_config: AI observability configuration
            auto_start_session: Whether to automatically start a new session
            **kwargs: Additional model configuration parameters
        """
        if not _GOOGLE_AVAILABLE:
            raise ImportError("Google AI not installed. Install with: pip install google-generativeai")
        
        # Initialize base wrapper
        super().__init__(
            amplitude_client=amplitude_client,
            ai_config=ai_config,
            auto_start_session=auto_start_session
        )
        
        # Configure Google AI
        if api_key:
            genai.configure(api_key=api_key)
        
        # Initialize model
        self.model_name = model_name
        self._model = GenerativeModel(model_name, **kwargs)
        
        # Store original methods for delegation
        self._original_generate_content = self._model.generate_content
        self._original_generate_content_async = getattr(self._model, 'generate_content_async', None)
        
        # Replace methods with instrumented versions
        self._model.generate_content = self._instrumented_generate_content
        if self._original_generate_content_async:
            self._model.generate_content_async = self._instrumented_generate_content_async
    
    def get_provider_name(self) -> str:
        """Get the provider name."""
        return "google"
    
    def _extract_token_usage(self, response_data: Any) -> tuple[Optional[int], Optional[int], Optional[int]]:
        """Extract token usage from Google response."""
        if hasattr(response_data, 'usage_metadata') and response_data.usage_metadata:
            usage = response_data.usage_metadata
            input_tokens = getattr(usage, 'prompt_token_count', None)
            output_tokens = getattr(usage, 'candidates_token_count', None)
            total_tokens = getattr(usage, 'total_token_count', None)
            
            # Calculate total if not provided
            if total_tokens is None and input_tokens is not None and output_tokens is not None:
                total_tokens = input_tokens + output_tokens
                
            return input_tokens, output_tokens, total_tokens
        return None, None, None
    
    def _extract_model_name(self, request_data: Dict[str, Any], response_data: Any) -> Optional[str]:
        """Extract model name from request or response."""
        return self.model_name
    
    def _extract_input_messages(self, request_data: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Extract input messages from request."""
        contents = request_data.get('contents')
        if not contents:
            return None
        
        # Handle different input formats
        result = []
        
        if isinstance(contents, str):
            # Simple string input
            result.append({"role": "user", "content": contents})
        elif isinstance(contents, list):
            # List of content items
            for content in contents:
                if isinstance(content, str):
                    result.append({"role": "user", "content": content})
                elif isinstance(content, dict):
                    result.append(content)
                elif hasattr(content, 'role') and hasattr(content, 'parts'):
                    # Google Content object
                    parts_text = []
                    for part in content.parts:
                        if hasattr(part, 'text'):
                            parts_text.append(part.text)
                    result.append({
                        "role": content.role,
                        "content": ' '.join(parts_text) if parts_text else str(content.parts)
                    })
        
        return result if result else None
    
    def _extract_output_content(self, response_data: Any) -> Optional[str]:
        """Extract output content from Google response."""
        if hasattr(response_data, 'text'):
            return response_data.text
        
        if hasattr(response_data, 'candidates') and response_data.candidates:
            candidate = response_data.candidates[0]
            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                parts_text = []
                for part in candidate.content.parts:
                    if hasattr(part, 'text'):
                        parts_text.append(part.text)
                return ' '.join(parts_text) if parts_text else None
        
        return None
    
    def _extract_finish_reason(self, response_data: Any) -> Optional[str]:
        """Extract finish reason from Google response."""
        if hasattr(response_data, 'candidates') and response_data.candidates:
            candidate = response_data.candidates[0]
            if hasattr(candidate, 'finish_reason'):
                return str(candidate.finish_reason)
        return None
    
    def _instrumented_generate_content(self, *args, **kwargs):
        """Instrumented version of generate_content."""
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
            # Make the actual Google AI call
            response = self._original_generate_content(*args, **kwargs)
            
            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Build request data for observability
            request_data = {
                'contents': args[0] if args else kwargs.get('contents'),
                'model': self.model_name,
                **kwargs
            }
            
            # Capture observability data
            self._capture_message_event(
                request_data=request_data,
                response_data=response,
                latency_ms=latency_ms,
                user_id=user_id,
                device_id=device_id
            )
            
            # Google Gemini doesn't have function calling in the same way as OpenAI/Anthropic
            # but we could extend this to handle function calls if they're added to the API
            
            return response
            
        except Exception as e:
            # Capture error event
            request_data = {
                'contents': args[0] if args else kwargs.get('contents'),
                'model': self.model_name,
                **kwargs
            }
            self._capture_error_event(e, request_data, user_id, device_id)
            raise
    
    async def _instrumented_generate_content_async(self, *args, **kwargs):
        """Instrumented version of async generate_content."""
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
            # Make the actual Google AI call
            response = await self._original_generate_content_async(*args, **kwargs)
            
            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Build request data for observability
            request_data = {
                'contents': args[0] if args else kwargs.get('contents'),
                'model': self.model_name,
                **kwargs
            }
            
            # Capture observability data
            self._capture_message_event(
                request_data=request_data,
                response_data=response,
                latency_ms=latency_ms,
                user_id=user_id,
                device_id=device_id
            )
            
            return response
            
        except Exception as e:
            # Capture error event
            request_data = {
                'contents': args[0] if args else kwargs.get('contents'),
                'model': self.model_name,
                **kwargs
            }
            self._capture_error_event(e, request_data, user_id, device_id)
            raise
    
    # Convenience methods that match common LLM patterns
    def chat(self, message: str, **kwargs):
        """Send a chat message (convenience method)."""
        return self._model.generate_content(message, **kwargs)
    
    async def achat(self, message: str, **kwargs):
        """Send a chat message asynchronously (convenience method)."""
        if self._original_generate_content_async:
            return await self._model.generate_content_async(message, **kwargs)
        else:
            raise NotImplementedError("Async generation not available for this model")
    
    # Delegate all other attributes to the underlying model
    def __getattr__(self, name):
        return getattr(self._model, name)