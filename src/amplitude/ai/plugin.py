"""AI observability plugin for Amplitude.

This plugin integrates AI observability events with Amplitude's existing plugin infrastructure,
allowing for preprocessing, enrichment, and filtering of AI events.
"""

from typing import Optional, Dict, Any
from amplitude.plugin import EventPlugin
from amplitude.event import BaseEvent
from amplitude.constants import PluginType
from .events import (
    LLMRunStartedEvent,
    LLMMessageEvent,
    UserMessageEvent,
    ToolCalledEvent,
    LLMRunFinishedEvent
)
from .config import AIConfig


def _is_ai_event(event: BaseEvent) -> bool:
    """Check if an event is an AI observability event."""
    ai_event_types = {
        "llm_run_started", "llm_message", "user_message", 
        "tool_called", "llm_run_finished"
    }
    return getattr(event, 'event_type', None) in ai_event_types


class AIObservabilityPlugin(EventPlugin):
    """Plugin for processing AI observability events.
    
    This plugin can be added to an Amplitude client to:
    - Enrich AI events with additional context
    - Filter sensitive information based on privacy settings
    - Add custom properties to AI events
    - Transform AI event data before sending
    """
    
    def __init__(self, ai_config: Optional[AIConfig] = None):
        """Initialize the AI observability plugin.
        
        Args:
            ai_config: AI observability configuration
        """
        super().__init__(PluginType.ENRICHMENT)
        self.ai_config = ai_config or AIConfig()
    
    def execute(self, event: BaseEvent) -> Optional[BaseEvent]:
        """Process AI observability events.
        
        Args:
            event: The event to process
            
        Returns:
            The processed event, or None to drop the event
        """
        # Only process AI events
        if not _is_ai_event(event):
            return event
        
        # Apply privacy filtering
        event = self._apply_privacy_settings(event)
        if event is None:
            return None
        
        # Enrich with AI-specific context
        event = self._enrich_ai_event(event)
        
        # Apply content truncation
        event = self._apply_content_limits(event)
        
        return event
    
    
    def _apply_privacy_settings(self, event: BaseEvent) -> Optional[BaseEvent]:
        """Apply privacy settings to AI events.
        
        Args:
            event: The event to filter
            
        Returns:
            The filtered event, or None to drop the event
        """
        if not hasattr(event, 'event_properties') or not event.event_properties:
            return event
        
        properties = event.event_properties
        
        # Apply privacy mode (exclude all sensitive content)
        if self.ai_config.privacy_mode:
            properties.pop('input_messages', None)
            properties.pop('output_content', None)
            properties.pop('content', None)
            properties.pop('tool_parameters', None)
            properties.pop('tool_result', None)
            return event
        
        # Apply specific exclusions
        if self.ai_config.should_exclude_content('input'):
            properties.pop('input_messages', None)
            properties.pop('content', None)
        
        if self.ai_config.should_exclude_content('output'):
            properties.pop('output_content', None)
        
        if self.ai_config.should_exclude_content('tool_parameters'):
            properties.pop('tool_parameters', None)
        
        if self.ai_config.should_exclude_content('tool_results'):
            properties.pop('tool_result', None)
        
        return event
    
    def _enrich_ai_event(self, event: BaseEvent) -> BaseEvent:
        """Enrich AI events with additional context.
        
        Args:
            event: The event to enrich
            
        Returns:
            The enriched event
        """
        if not hasattr(event, 'event_properties') or not event.event_properties:
            return event
        
        properties = event.event_properties
        
        # Add SDK version and source
        properties['ai_sdk_version'] = "1.0.0"  # Should be dynamic
        properties['ai_sdk_source'] = "amplitude-python-ai"
        
        # Add cost calculation if not already present
        if (self.ai_config.cost_tracking and
            'cost_usd' not in properties and
            'input_tokens' in properties and
            'output_tokens' in properties and
            'model_provider' in properties and
            'model_name' in properties):
            
            cost = self.ai_config.calculate_cost(
                properties['model_provider'],
                properties['model_name'],
                properties['input_tokens'],
                properties['output_tokens']
            )
            if cost is not None:
                properties['cost_usd'] = cost
        
        # Add derived metrics
        if 'input_tokens' in properties and 'output_tokens' in properties:
            input_tokens = properties.get('input_tokens', 0) or 0
            output_tokens = properties.get('output_tokens', 0) or 0
            properties['total_tokens'] = input_tokens + output_tokens
            
            # Calculate tokens per second if latency is available
            latency_ms = properties.get('latency_ms')
            if latency_ms and latency_ms > 0:
                tokens_per_second = (input_tokens + output_tokens) / (latency_ms / 1000)
                properties['tokens_per_second'] = round(tokens_per_second, 2)
        
        return event
    
    def _apply_content_limits(self, event: BaseEvent) -> BaseEvent:
        """Apply content length limits to AI events.
        
        Args:
            event: The event to limit
            
        Returns:
            The event with content truncated if necessary
        """
        if not hasattr(event, 'event_properties') or not event.event_properties:
            return event
        
        properties = event.event_properties
        
        # Apply content truncation
        content_fields = ['output_content', 'content']
        for field in content_fields:
            if field in properties and isinstance(properties[field], str):
                properties[field] = self.ai_config.truncate_content(properties[field])
        
        # Truncate input messages
        if 'input_messages' in properties and isinstance(properties['input_messages'], list):
            for message in properties['input_messages']:
                if isinstance(message, dict) and 'content' in message and isinstance(message['content'], str):
                    message['content'] = self.ai_config.truncate_content(message['content'])
        
        return event


class AIEventFilterPlugin(EventPlugin):
    """Plugin for filtering AI events based on custom criteria.
    
    This plugin allows filtering AI events based on:
    - Model provider
    - Cost thresholds
    - Token usage
    - Latency thresholds
    - Error conditions
    """
    
    def __init__(self,
                 min_cost_threshold: Optional[float] = None,
                 max_cost_threshold: Optional[float] = None,
                 min_tokens_threshold: Optional[int] = None,
                 max_tokens_threshold: Optional[int] = None,
                 min_latency_threshold: Optional[int] = None,
                 max_latency_threshold: Optional[int] = None,
                 allowed_providers: Optional[list] = None,
                 blocked_providers: Optional[list] = None,
                 include_errors: bool = True,
                 include_successful: bool = True):
        """Initialize the AI event filter plugin.
        
        Args:
            min_cost_threshold: Minimum cost to include event (USD)
            max_cost_threshold: Maximum cost to include event (USD)
            min_tokens_threshold: Minimum total tokens to include event
            max_tokens_threshold: Maximum total tokens to include event
            min_latency_threshold: Minimum latency to include event (ms)
            max_latency_threshold: Maximum latency to include event (ms)
            allowed_providers: List of allowed model providers
            blocked_providers: List of blocked model providers
            include_errors: Whether to include error events
            include_successful: Whether to include successful events
        """
        super().__init__(PluginType.BEFORE)
        self.min_cost_threshold = min_cost_threshold
        self.max_cost_threshold = max_cost_threshold
        self.min_tokens_threshold = min_tokens_threshold
        self.max_tokens_threshold = max_tokens_threshold
        self.min_latency_threshold = min_latency_threshold
        self.max_latency_threshold = max_latency_threshold
        self.allowed_providers = set(allowed_providers) if allowed_providers else None
        self.blocked_providers = set(blocked_providers) if blocked_providers else None
        self.include_errors = include_errors
        self.include_successful = include_successful
    
    def execute(self, event: BaseEvent) -> Optional[BaseEvent]:
        """Filter AI observability events.
        
        Args:
            event: The event to filter
            
        Returns:
            The event if it passes filters, None to drop it
        """
        # Only filter AI events
        if not _is_ai_event(event):
            return event
        
        if not hasattr(event, 'event_properties') or not event.event_properties:
            return event
        
        properties = event.event_properties
        
        # Filter by success/error status
        is_error = properties.get('success') is False or properties.get('error_message') is not None
        if is_error and not self.include_errors:
            return None
        if not is_error and not self.include_successful:
            return None
        
        # Filter by provider
        provider = properties.get('model_provider')
        if provider:
            if self.allowed_providers and provider not in self.allowed_providers:
                return None
            if self.blocked_providers and provider in self.blocked_providers:
                return None
        
        # Filter by cost
        cost = properties.get('cost_usd')
        if cost is not None:
            if self.min_cost_threshold is not None and cost < self.min_cost_threshold:
                return None
            if self.max_cost_threshold is not None and cost > self.max_cost_threshold:
                return None
        
        # Filter by tokens
        total_tokens = properties.get('total_tokens')
        if total_tokens is not None:
            if self.min_tokens_threshold is not None and total_tokens < self.min_tokens_threshold:
                return None
            if self.max_tokens_threshold is not None and total_tokens > self.max_tokens_threshold:
                return None
        
        # Filter by latency
        latency = properties.get('latency_ms')
        if latency is not None:
            if self.min_latency_threshold is not None and latency < self.min_latency_threshold:
                return None
            if self.max_latency_threshold is not None and latency > self.max_latency_threshold:
                return None
        
        return event
    


class AIMetricsPlugin(EventPlugin):
    """Plugin for adding derived metrics to AI events.
    
    This plugin calculates and adds useful metrics like:
    - Cost per token
    - Tokens per second
    - Cost per second
    - Efficiency metrics
    """
    
    def __init__(self):
        """Initialize the AI metrics plugin."""
        super().__init__(PluginType.ENRICHMENT)
    
    def execute(self, event: BaseEvent) -> Optional[BaseEvent]:
        """Add derived metrics to AI events.
        
        Args:
            event: The event to enhance
            
        Returns:
            The enhanced event
        """
        # Only process LLM message events (where metrics are most relevant)
        if not isinstance(event, LLMMessageEvent) and getattr(event, 'event_type', None) != 'llm_message':
            return event
        
        if not hasattr(event, 'event_properties') or not event.event_properties:
            return event
        
        properties = event.event_properties
        
        # Calculate derived metrics
        input_tokens = properties.get('input_tokens', 0) or 0
        output_tokens = properties.get('output_tokens', 0) or 0
        total_tokens = input_tokens + output_tokens
        cost = properties.get('cost_usd')
        latency_ms = properties.get('latency_ms')
        
        # Cost per token
        if cost is not None and total_tokens > 0:
            properties['cost_per_token'] = cost / total_tokens
            
            if input_tokens > 0:
                properties['cost_per_input_token'] = (cost * input_tokens / total_tokens) / input_tokens
            if output_tokens > 0:
                properties['cost_per_output_token'] = (cost * output_tokens / total_tokens) / output_tokens
        
        # Time-based metrics
        if latency_ms is not None and latency_ms > 0:
            latency_seconds = latency_ms / 1000
            
            # Tokens per second
            if total_tokens > 0:
                properties['tokens_per_second'] = total_tokens / latency_seconds
            
            # Output tokens per second (generation speed)
            if output_tokens > 0:
                properties['output_tokens_per_second'] = output_tokens / latency_seconds
            
            # Cost per second
            if cost is not None:
                properties['cost_per_second'] = cost / latency_seconds
        
        # Efficiency metrics
        if input_tokens > 0 and output_tokens > 0:
            properties['output_to_input_ratio'] = output_tokens / input_tokens
        
        return event