"""Amplitude AI observability module for LLM tracking.

This module provides automatic instrumentation and manual event emission for LLM observability.
Supports OpenAI, Anthropic, Google/Gemini, LangChain, and Pydantic AI with zero-latency impact.
"""

from .events import (
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

from .config import AIConfig
from .manual import (
    LLMSessionTracker,
    llm_session,
    MessageTimer,
    calculate_cost,
    create_session_id,
    quick_track_message
)
from .plugin import (
    AIObservabilityPlugin,
    AIEventFilterPlugin,
    AIMetricsPlugin
)

# Provider wrappers (imported on-demand)
__all__ = [
    # Event classes
    "LLMRunStartedEvent",
    "LLMMessageEvent", 
    "UserMessageEvent",
    "ToolCalledEvent",
    "LLMRunFinishedEvent",
    
    # Basic emission functions
    "emit_llm_run_started",
    "emit_llm_message",
    "emit_user_message", 
    "emit_tool_called",
    "emit_llm_run_finished",
    
    # Configuration
    "AIConfig",
    
    # Manual tracking APIs
    "LLMSessionTracker",
    "llm_session",
    "MessageTimer",
    "calculate_cost",
    "create_session_id",
    "quick_track_message",
    
    # Plugins
    "AIObservabilityPlugin",
    "AIEventFilterPlugin",
    "AIMetricsPlugin"
]


def get_openai():
    """Import OpenAI wrapper on-demand to avoid unnecessary dependencies."""
    try:
        from .openai import OpenAI, AsyncOpenAI
        return OpenAI, AsyncOpenAI
    except ImportError as e:
        raise ImportError("OpenAI not installed. Install with: pip install openai") from e


def get_anthropic():
    """Import Anthropic wrapper on-demand to avoid unnecessary dependencies."""
    try:
        from .anthropic import Anthropic, AsyncAnthropic
        return Anthropic, AsyncAnthropic
    except ImportError as e:
        raise ImportError("Anthropic not installed. Install with: pip install anthropic") from e


def get_google():
    """Import Google wrapper on-demand to avoid unnecessary dependencies."""
    try:
        from .google import GoogleGenerativeAI
        return GoogleGenerativeAI
    except ImportError as e:
        raise ImportError("Google AI not installed. Install with: pip install google-generativeai") from e


def get_langchain():
    """Import LangChain callback handler on-demand to avoid unnecessary dependencies."""
    try:
        from .langchain import AmplitudeLangChainCallback
        return AmplitudeLangChainCallback
    except ImportError as e:
        raise ImportError("LangChain not installed. Install with: pip install langchain-core") from e


def get_pydantic():
    """Import Pydantic AI wrapper on-demand to avoid unnecessary dependencies."""
    try:
        from .pydantic import PydanticAI
        return PydanticAI
    except ImportError as e:
        raise ImportError("Pydantic AI not installed. Install with: pip install pydantic-ai") from e