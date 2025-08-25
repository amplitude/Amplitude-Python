"""Google Gemini wrapper for Amplitude LLM observability."""

from typing import Optional

try:
    import google.generativeai as genai
    from google.generativeai import GenerativeModel
except ImportError:
    GenerativeModel = None

from amplitude.client import Amplitude
from .config import AIConfig
from .instrumentation import InstrumentationMixin, import_guard
from .parsers import GoogleResponseParser


@import_guard("google-generativeai", "pip install google-generativeai")
class GoogleGenerativeAI(InstrumentationMixin):
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
        """Initialize Google Gemini wrapper."""
        # Initialize mixin
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
        self._response_parser = GoogleResponseParser()
        
        # Replace methods with instrumented versions
        self._model.generate_content = self._create_instrumented_method(
            self._model.generate_content, is_async=False
        )
        
        if hasattr(self._model, 'generate_content_async'):
            self._model.generate_content_async = self._create_instrumented_method(
                self._model.generate_content_async, is_async=True
            )
    
    def get_provider_name(self) -> str:
        """Get the provider name."""
        return "google"
    
    def get_response_parser(self):
        """Get the response parser."""
        return self._response_parser
    
    # Override instrumentation to add model name to request data
    def _instrument_call(self, original_method, is_async, *args, **kwargs):
        """Override to add model name to request data."""
        # Add model name to kwargs for proper tracking
        kwargs['model'] = self.model_name
        return super()._instrument_call(original_method, is_async, *args, **kwargs)
    
    # Convenience methods
    def chat(self, message: str, **kwargs):
        """Send a chat message (convenience method)."""
        return self._model.generate_content(message, **kwargs)
    
    async def achat(self, message: str, **kwargs):
        """Send a chat message asynchronously (convenience method)."""
        if hasattr(self._model, 'generate_content_async'):
            return await self._model.generate_content_async(message, **kwargs)
        else:
            raise NotImplementedError("Async generation not available for this model")
    
    # Delegate all other attributes to the underlying model
    def __getattr__(self, name):
        return getattr(self._model, name)