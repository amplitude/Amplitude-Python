"""Anthropic wrapper for Amplitude LLM observability."""

from typing import Optional

try:
    from anthropic import Anthropic as OriginalAnthropic
    from anthropic import AsyncAnthropic as OriginalAsyncAnthropic
except ImportError:
    OriginalAnthropic = None
    OriginalAsyncAnthropic = None

from amplitude.client import Amplitude
from .config import AIConfig
from .instrumentation import InstrumentationMixin, import_guard
from .parsers import AnthropicResponseParser


@import_guard("anthropic", "pip install anthropic")
class Anthropic(InstrumentationMixin):
    """Anthropic wrapper with Amplitude observability.
    
    Drop-in replacement for anthropic.Anthropic that automatically tracks LLM usage.
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 amplitude_client: Optional[Amplitude] = None,
                 ai_config: Optional[AIConfig] = None,
                 auto_start_session: bool = True,
                 **kwargs):
        """Initialize Anthropic wrapper."""
        # Initialize mixin
        super().__init__(
            amplitude_client=amplitude_client,
            ai_config=ai_config,
            auto_start_session=auto_start_session
        )
        
        # Initialize Anthropic client
        self._client = OriginalAnthropic(api_key=api_key, **kwargs)
        self._response_parser = AnthropicResponseParser()
        
        # Replace methods with instrumented versions
        self._client.messages.create = self._create_instrumented_method(
            self._client.messages.create, is_async=False
        )
    
    def get_provider_name(self) -> str:
        """Get the provider name."""
        return "anthropic"
    
    def get_response_parser(self):
        """Get the response parser."""
        return self._response_parser
    
    # Delegate all other attributes to the underlying Anthropic client
    def __getattr__(self, name):
        return getattr(self._client, name)


@import_guard("anthropic", "pip install anthropic")
class AsyncAnthropic(InstrumentationMixin):
    """Async Anthropic wrapper with Amplitude observability.
    
    Drop-in replacement for anthropic.AsyncAnthropic that automatically tracks LLM usage.
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 amplitude_client: Optional[Amplitude] = None,
                 ai_config: Optional[AIConfig] = None,
                 auto_start_session: bool = True,
                 **kwargs):
        """Initialize AsyncAnthropic wrapper."""
        # Initialize mixin
        super().__init__(
            amplitude_client=amplitude_client,
            ai_config=ai_config,
            auto_start_session=auto_start_session
        )
        
        # Initialize AsyncAnthropic client
        self._client = OriginalAsyncAnthropic(api_key=api_key, **kwargs)
        self._response_parser = AnthropicResponseParser()
        
        # Replace methods with instrumented versions
        self._client.messages.create = self._create_instrumented_method(
            self._client.messages.create, is_async=True
        )
    
    def get_provider_name(self) -> str:
        """Get the provider name."""
        return "anthropic"
    
    def get_response_parser(self):
        """Get the response parser."""
        return self._response_parser
    
    # Delegate all other attributes to the underlying AsyncAnthropic client
    def __getattr__(self, name):
        return getattr(self._client, name)