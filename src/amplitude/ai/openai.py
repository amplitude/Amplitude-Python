"""OpenAI wrapper for Amplitude LLM observability."""

from typing import Optional

try:
    from openai import OpenAI as OriginalOpenAI
    from openai import AsyncOpenAI as OriginalAsyncOpenAI
except ImportError:
    OriginalOpenAI = None
    OriginalAsyncOpenAI = None

from amplitude.client import Amplitude
from .config import AIConfig
from .instrumentation import InstrumentationMixin, import_guard
from .parsers import OpenAIResponseParser


@import_guard("openai", "pip install openai")
class OpenAI(InstrumentationMixin):
    """OpenAI wrapper with Amplitude observability.
    
    Drop-in replacement for openai.OpenAI that automatically tracks LLM usage.
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 amplitude_client: Optional[Amplitude] = None,
                 ai_config: Optional[AIConfig] = None,
                 auto_start_session: bool = True,
                 **kwargs):
        """Initialize OpenAI wrapper."""
        # Initialize mixin
        super().__init__(
            amplitude_client=amplitude_client,
            ai_config=ai_config,
            auto_start_session=auto_start_session
        )
        
        # Initialize OpenAI client
        self._client = OriginalOpenAI(api_key=api_key, **kwargs)
        self._response_parser = OpenAIResponseParser()
        
        # Replace methods with instrumented versions
        self._client.chat.completions.create = self._create_instrumented_method(
            self._client.chat.completions.create, is_async=False
        )
    
    def get_provider_name(self) -> str:
        """Get the provider name."""
        return "openai"
    
    def get_response_parser(self):
        """Get the response parser."""
        return self._response_parser
    
    # Delegate all other attributes to the underlying OpenAI client
    def __getattr__(self, name):
        return getattr(self._client, name)


@import_guard("openai", "pip install openai")
class AsyncOpenAI(InstrumentationMixin):
    """Async OpenAI wrapper with Amplitude observability.
    
    Drop-in replacement for openai.AsyncOpenAI that automatically tracks LLM usage.
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 amplitude_client: Optional[Amplitude] = None,
                 ai_config: Optional[AIConfig] = None,
                 auto_start_session: bool = True,
                 **kwargs):
        """Initialize AsyncOpenAI wrapper."""
        # Initialize mixin
        super().__init__(
            amplitude_client=amplitude_client,
            ai_config=ai_config,
            auto_start_session=auto_start_session
        )
        
        # Initialize AsyncOpenAI client
        self._client = OriginalAsyncOpenAI(api_key=api_key, **kwargs)
        self._response_parser = OpenAIResponseParser()
        
        # Replace methods with instrumented versions
        self._client.chat.completions.create = self._create_instrumented_method(
            self._client.chat.completions.create, is_async=True
        )
    
    def get_provider_name(self) -> str:
        """Get the provider name."""
        return "openai"
    
    def get_response_parser(self):
        """Get the response parser."""
        return self._response_parser
    
    # Delegate all other attributes to the underlying AsyncOpenAI client
    def __getattr__(self, name):
        return getattr(self._client, name)