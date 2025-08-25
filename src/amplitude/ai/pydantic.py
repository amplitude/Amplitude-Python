"""Pydantic AI wrapper for Amplitude LLM observability."""

from typing import Optional, Union, Type, TypeVar

try:
    from pydantic_ai import Agent
    from pydantic_ai.models import Model
except ImportError:
    # Create dummy classes for type hints
    class Agent:
        pass
    class Model:
        pass

from amplitude.client import Amplitude
from .config import AIConfig
from .instrumentation import InstrumentationMixin, import_guard
from .parsers import PydanticAIResponseParser

T = TypeVar('T')


@import_guard("pydantic-ai", "pip install pydantic-ai")
class PydanticAIWrapper(InstrumentationMixin):
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
        """Initialize Pydantic AI wrapper."""
        # Initialize mixin
        super().__init__(
            amplitude_client=amplitude_client,
            ai_config=ai_config,
            auto_start_session=auto_start_session
        )
        
        self._agent = agent
        self._response_parser = PydanticAIResponseParser()
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
        agent.run = self._create_instrumented_method(agent.run, is_async=False)
        agent.run_async = self._create_instrumented_method(agent.run_async, is_async=True)
    
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
    
    def get_response_parser(self):
        """Get the response parser."""
        return self._response_parser
    
    
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