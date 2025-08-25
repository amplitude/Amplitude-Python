"""LLM model pricing data for cost calculations.

This module contains pricing information for various LLM providers and models.
Prices are per 1 million tokens unless otherwise specified.
"""

from typing import Dict

# OpenAI model pricing (per 1M tokens)
OPENAI_PRICING = {
    # GPT-4 models
    "gpt-4": {"input": 30.0, "output": 60.0},
    "gpt-4-0613": {"input": 30.0, "output": 60.0},
    "gpt-4-32k": {"input": 60.0, "output": 120.0},
    "gpt-4-turbo": {"input": 10.0, "output": 30.0},
    "gpt-4o": {"input": 5.0, "output": 15.0},
    "gpt-4o-mini": {"input": 0.15, "output": 0.6},
    # GPT-3.5 models
    "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
    "gpt-3.5-turbo-instruct": {"input": 1.5, "output": 2.0},
}

# Anthropic Claude model pricing (per 1M tokens)  
ANTHROPIC_PRICING = {
    # Claude 3 models
    "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
    "claude-3-5-sonnet-20240620": {"input": 3.0, "output": 15.0},
    "claude-3-5-haiku-20241022": {"input": 0.25, "output": 1.25},
    "claude-3-opus-20240229": {"input": 15.0, "output": 75.0},
    "claude-3-sonnet-20240229": {"input": 3.0, "output": 15.0},
    "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
}

# Google Gemini model pricing (per 1M tokens)
GOOGLE_PRICING = {
    "gemini-pro": {"input": 0.5, "output": 1.5},
    "gemini-pro-vision": {"input": 0.5, "output": 1.5},
    "gemini-1.5-pro": {"input": 3.5, "output": 10.5},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.3},
}

# Default pricing configuration
DEFAULT_PRICING = {
    "openai": OPENAI_PRICING,
    "anthropic": ANTHROPIC_PRICING, 
    "google": GOOGLE_PRICING,
}


def get_model_pricing(provider: str, model: str) -> Dict[str, float]:
    """Get pricing information for a specific model.
    
    Args:
        provider: LLM provider name
        model: Model name
        
    Returns:
        Dictionary with 'input' and 'output' pricing per 1M tokens
        
    Raises:
        KeyError: If provider or model not found
    """
    provider_pricing = DEFAULT_PRICING[provider.lower()]
    return provider_pricing[model]


def calculate_cost(provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate estimated cost for a model call.
    
    Args:
        provider: LLM provider name
        model: Model name  
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        
    Returns:
        Estimated cost in USD
        
    Raises:
        KeyError: If provider or model not found
    """
    pricing = get_model_pricing(provider, model)
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    return input_cost + output_cost