"""
Simple tracker module for enabling/disabling LLM tracing.
"""

from typing import Optional
import logging

logger = logging.getLogger('amplitude')

# Global reference to the active client
_active_client = None


def track(amplitude_client):
    """
    Enable LLM tracing for the given Amplitude client.
    
    Args:
        amplitude_client: The Amplitude client instance to use for tracking
    
    Example:
        from amplitude import Amplitude
        import amplitude.ai
        
        client = Amplitude('api-key')
        amplitude.ai.track(client)
    """
    global _active_client
    
    # Import here to trigger auto-patching
    from amplitude.ai import openai as _openai_module
    
    # Set the active client
    _openai_module.set_active_client(amplitude_client)
    _active_client = amplitude_client
    
    logger.info("LLM tracing enabled for Amplitude client")


def untrack():
    """
    Disable LLM tracing.
    
    Example:
        import amplitude.ai
        amplitude.ai.untrack()
    """
    global _active_client
    
    from amplitude.ai import openai as _openai_module
    
    # Clear the active client
    _openai_module.set_active_client(None)
    _active_client = None
    
    logger.info("LLM tracing disabled")


def get_active_client():
    """Get the currently active Amplitude client."""
    return _active_client


def is_tracking():
    """Check if LLM tracing is currently enabled."""
    return _active_client is not None