"""AI observability configuration for Amplitude SDK."""

from typing import Optional, Set
from dataclasses import dataclass


@dataclass
class AIConfig:
    """Configuration for AI observability features.
    
    This configuration controls privacy, cost tracking, and other AI-specific settings.
    """
    
    # Privacy controls
    privacy_mode: bool = False
    exclude_input: bool = False
    exclude_output: bool = False
    exclude_tool_parameters: bool = False
    exclude_tool_results: bool = False
    
    # Feature flags
    token_tracking: bool = True
    cost_tracking: bool = True
    latency_tracking: bool = True
    error_tracking: bool = True
    
    # Provider-specific settings
    openai_cost_per_token: Optional[dict] = None
    anthropic_cost_per_token: Optional[dict] = None
    google_cost_per_token: Optional[dict] = None
    
    # Session management
    auto_generate_session_ids: bool = True
    session_timeout_ms: int = 30 * 60 * 1000  # 30 minutes
    
    # Advanced settings
    async_event_emission: bool = True
    max_content_length: int = 10000  # Max length for input/output content
    
    def __post_init__(self):
        """Initialize default cost tracking if not provided."""
        if self.openai_cost_per_token is None:
            self.openai_cost_per_token = {
                # GPT-4 models (per 1M tokens)
                "gpt-4": {"input": 30.0, "output": 60.0},
                "gpt-4-0613": {"input": 30.0, "output": 60.0},
                "gpt-4-32k": {"input": 60.0, "output": 120.0},
                "gpt-4-turbo": {"input": 10.0, "output": 30.0},
                "gpt-4o": {"input": 5.0, "output": 15.0},
                "gpt-4o-mini": {"input": 0.15, "output": 0.6},
                # GPT-3.5 models (per 1M tokens)
                "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
                "gpt-3.5-turbo-instruct": {"input": 1.5, "output": 2.0},
            }
            
        if self.anthropic_cost_per_token is None:
            self.anthropic_cost_per_token = {
                # Claude 3 models (per 1M tokens)
                "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
                "claude-3-5-sonnet-20240620": {"input": 3.0, "output": 15.0},
                "claude-3-5-haiku-20241022": {"input": 0.25, "output": 1.25},
                "claude-3-opus-20240229": {"input": 15.0, "output": 75.0},
                "claude-3-sonnet-20240229": {"input": 3.0, "output": 15.0},
                "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
            }
            
        if self.google_cost_per_token is None:
            self.google_cost_per_token = {
                # Gemini models (per 1M tokens)
                "gemini-pro": {"input": 0.5, "output": 1.5},
                "gemini-pro-vision": {"input": 0.5, "output": 1.5},
                "gemini-1.5-pro": {"input": 3.5, "output": 10.5},
                "gemini-1.5-flash": {"input": 0.075, "output": 0.3},
            }
    
    def calculate_cost(self, provider: str, model: str, input_tokens: int, output_tokens: int) -> Optional[float]:
        """Calculate the estimated cost for a model call.
        
        Args:
            provider: The LLM provider (openai, anthropic, google)
            model: The model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Estimated cost in USD, or None if cost tracking is disabled or model not found
        """
        if not self.cost_tracking:
            return None
            
        cost_map = {
            "openai": self.openai_cost_per_token,
            "anthropic": self.anthropic_cost_per_token,
            "google": self.google_cost_per_token,
        }.get(provider.lower())
        
        if not cost_map or model not in cost_map:
            return None
            
        model_costs = cost_map[model]
        input_cost = (input_tokens / 1_000_000) * model_costs["input"]
        output_cost = (output_tokens / 1_000_000) * model_costs["output"]
        
        return input_cost + output_cost
    
    def should_exclude_content(self, content_type: str) -> bool:
        """Check if content should be excluded based on privacy settings.
        
        Args:
            content_type: Type of content (input, output, tool_parameters, tool_results)
            
        Returns:
            True if content should be excluded
        """
        if self.privacy_mode:
            return True
            
        exclusions = {
            "input": self.exclude_input,
            "output": self.exclude_output,
            "tool_parameters": self.exclude_tool_parameters,
            "tool_results": self.exclude_tool_results,
        }
        
        return exclusions.get(content_type, False)
    
    def truncate_content(self, content: str) -> str:
        """Truncate content to max_content_length if needed.
        
        Args:
            content: The content to potentially truncate
            
        Returns:
            Truncated content with ellipsis if needed
        """
        if len(content) <= self.max_content_length:
            return content
        return content[:self.max_content_length - 3] + "..."