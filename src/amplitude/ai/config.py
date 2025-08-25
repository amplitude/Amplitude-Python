"""AI observability configuration for Amplitude SDK."""

from typing import Optional, Set
from dataclasses import dataclass
from .pricing import DEFAULT_PRICING, calculate_cost as calculate_model_cost


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
    custom_pricing: Optional[dict] = None
    
    # Session management
    auto_generate_session_ids: bool = True
    session_timeout_ms: int = 30 * 60 * 1000  # 30 minutes
    
    # Advanced settings
    async_event_emission: bool = True
    max_content_length: int = 10000  # Max length for input/output content
    
    def __post_init__(self):
        """Initialize default pricing if custom pricing not provided."""
        if self.custom_pricing is None:
            self.custom_pricing = DEFAULT_PRICING
    
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
            
        try:
            # Use custom pricing if available, otherwise use default pricing
            pricing_data = self.custom_pricing or DEFAULT_PRICING
            provider_pricing = pricing_data.get(provider.lower())
            
            if not provider_pricing or model not in provider_pricing:
                return None
                
            model_costs = provider_pricing[model]
            input_cost = (input_tokens / 1_000_000) * model_costs["input"]
            output_cost = (output_tokens / 1_000_000) * model_costs["output"]
            
            return input_cost + output_cost
        except (KeyError, TypeError):
            return None
    
    def should_exclude_content(self, content_type: str) -> bool:
        """Check if content should be excluded based on privacy settings."""
        if self.privacy_mode:
            return True
            
        return getattr(self, f"exclude_{content_type}", False)
    
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