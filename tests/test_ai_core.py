"""Comprehensive unit tests for AI observability core functionality."""

import pytest
import time
import logging
from unittest.mock import Mock, patch, call
from dataclasses import dataclass
from typing import Optional, Dict, Any

# Configure logging for tests
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import modules to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from amplitude.ai.config import AIConfig
from amplitude.ai.pricing import (
    calculate_cost, get_model_pricing, DEFAULT_PRICING,
    OPENAI_PRICING, ANTHROPIC_PRICING, GOOGLE_PRICING
)
from amplitude.ai.events import (
    LLMRunStartedEvent, LLMMessageEvent, UserMessageEvent, 
    ToolCalledEvent, LLMRunFinishedEvent,
    get_current_session_id, set_session_id
)
from amplitude.ai.instrumentation import (
    SessionManager, EventEmitter, ResponseParser, InstrumentationMixin
)
from amplitude.ai.manual import (
    LLMSessionTracker, MessageTimer, llm_session, quick_track_message
)


class TestAIConfig:
    """Test AIConfig functionality thoroughly."""
    
    def setup_method(self):
        """Setup for each test method."""
        logger.info("Setting up AIConfig test...")
        
    def test_default_configuration(self):
        """Test default AIConfig initialization."""
        logger.info("Testing default AIConfig initialization...")
        
        config = AIConfig()
        
        # Test default values
        assert config.privacy_mode is False
        assert config.cost_tracking is True
        assert config.token_tracking is True
        assert config.latency_tracking is True
        assert config.error_tracking is True
        assert config.max_content_length == 10000
        assert config.async_event_emission is True
        
        # Test that custom pricing is initialized with defaults
        assert config.custom_pricing is not None
        assert 'openai' in config.custom_pricing
        assert 'anthropic' in config.custom_pricing
        assert 'google' in config.custom_pricing
        
        logger.info("✅ Default AIConfig initialization passed")
        
    def test_custom_configuration(self):
        """Test custom AIConfig values."""
        logger.info("Testing custom AIConfig values...")
        
        custom_pricing = {
            'openai': {'gpt-4': {'input': 25.0, 'output': 50.0}},
            'test-provider': {'test-model': {'input': 1.0, 'output': 2.0}}
        }
        
        config = AIConfig(
            privacy_mode=True,
            cost_tracking=False,
            max_content_length=5000,
            custom_pricing=custom_pricing
        )
        
        assert config.privacy_mode is True
        assert config.cost_tracking is False
        assert config.max_content_length == 5000
        assert config.custom_pricing == custom_pricing
        
        logger.info("✅ Custom AIConfig values passed")
        
    def test_privacy_controls(self):
        """Test privacy control methods."""
        logger.info("Testing privacy control methods...")
        
        # Test privacy mode
        config = AIConfig(privacy_mode=True)
        assert config.should_exclude_content("input") is True
        assert config.should_exclude_content("output") is True
        assert config.should_exclude_content("tool_parameters") is True
        
        # Test specific exclusions
        config = AIConfig(
            privacy_mode=False,
            exclude_input=True,
            exclude_output=False,
            exclude_tool_parameters=True
        )
        assert config.should_exclude_content("input") is True
        assert config.should_exclude_content("output") is False
        assert config.should_exclude_content("tool_parameters") is True
        
        logger.info("✅ Privacy controls passed")
        
    def test_content_truncation(self):
        """Test content truncation functionality."""
        logger.info("Testing content truncation...")
        
        config = AIConfig(max_content_length=50)
        
        short_text = "This is short"
        long_text = "This is a very long text that exceeds the maximum content length limit"
        
        assert config.truncate_content(short_text) == short_text
        truncated = config.truncate_content(long_text)
        assert len(truncated) <= 53  # 50 + "..."
        assert truncated.endswith("...")
        
        logger.info(f"Original: {len(long_text)} chars, Truncated: {len(truncated)} chars")
        logger.info("✅ Content truncation passed")
        
    def test_cost_calculation(self):
        """Test cost calculation with various scenarios."""
        logger.info("Testing cost calculation scenarios...")
        
        config = AIConfig()
        
        # Test OpenAI GPT-4 cost calculation
        cost = config.calculate_cost("openai", "gpt-4", 1000, 500)
        expected_cost = (1000 / 1_000_000) * 30.0 + (500 / 1_000_000) * 60.0
        assert abs(cost - expected_cost) < 0.0001
        logger.info(f"GPT-4 cost for 1000 input, 500 output tokens: ${cost:.6f}")
        
        # Test Anthropic Claude cost calculation
        cost = config.calculate_cost("anthropic", "claude-3-sonnet-20240229", 2000, 1000)
        expected_cost = (2000 / 1_000_000) * 3.0 + (1000 / 1_000_000) * 15.0
        assert abs(cost - expected_cost) < 0.0001
        logger.info(f"Claude-3-Sonnet cost for 2000 input, 1000 output tokens: ${cost:.6f}")
        
        # Test Google Gemini cost calculation
        cost = config.calculate_cost("google", "gemini-1.5-flash", 5000, 2000)
        expected_cost = (5000 / 1_000_000) * 0.075 + (2000 / 1_000_000) * 0.3
        assert abs(cost - expected_cost) < 0.0001
        logger.info(f"Gemini-1.5-Flash cost for 5000 input, 2000 output tokens: ${cost:.6f}")
        
        # Test cost tracking disabled
        config_no_cost = AIConfig(cost_tracking=False)
        assert config_no_cost.calculate_cost("openai", "gpt-4", 1000, 500) is None
        
        # Test unknown model/provider
        assert config.calculate_cost("unknown", "unknown", 1000, 500) is None
        assert config.calculate_cost("openai", "unknown-model", 1000, 500) is None
        
        logger.info("✅ Cost calculation scenarios passed")


class TestPricingModule:
    """Test the separated pricing module."""
    
    def test_pricing_constants(self):
        """Test that pricing constants are properly defined."""
        logger.info("Testing pricing constants...")
        
        # Test OpenAI pricing structure
        assert 'gpt-4' in OPENAI_PRICING
        assert 'input' in OPENAI_PRICING['gpt-4']
        assert 'output' in OPENAI_PRICING['gpt-4']
        assert OPENAI_PRICING['gpt-4']['input'] > 0
        assert OPENAI_PRICING['gpt-4']['output'] > 0
        
        # Test Anthropic pricing structure
        assert 'claude-3-sonnet-20240229' in ANTHROPIC_PRICING
        assert 'input' in ANTHROPIC_PRICING['claude-3-sonnet-20240229']
        assert 'output' in ANTHROPIC_PRICING['claude-3-sonnet-20240229']
        
        # Test Google pricing structure
        assert 'gemini-pro' in GOOGLE_PRICING
        assert 'input' in GOOGLE_PRICING['gemini-pro']
        assert 'output' in GOOGLE_PRICING['gemini-pro']
        
        # Test default pricing structure
        assert 'openai' in DEFAULT_PRICING
        assert 'anthropic' in DEFAULT_PRICING
        assert 'google' in DEFAULT_PRICING
        
        logger.info("✅ Pricing constants validation passed")
        
    def test_get_model_pricing(self):
        """Test get_model_pricing function."""
        logger.info("Testing get_model_pricing function...")
        
        # Test valid model pricing retrieval
        pricing = get_model_pricing("openai", "gpt-4")
        assert pricing == {"input": 30.0, "output": 60.0}
        logger.info(f"GPT-4 pricing: {pricing}")
        
        pricing = get_model_pricing("anthropic", "claude-3-haiku-20240307")
        assert pricing == {"input": 0.25, "output": 1.25}
        logger.info(f"Claude-3-Haiku pricing: {pricing}")
        
        # Test error cases
        with pytest.raises(KeyError):
            get_model_pricing("unknown_provider", "model")
            
        with pytest.raises(KeyError):
            get_model_pricing("openai", "unknown_model")
            
        logger.info("✅ get_model_pricing function passed")
        
    def test_calculate_cost_function(self):
        """Test standalone calculate_cost function."""
        logger.info("Testing standalone calculate_cost function...")
        
        # Test various cost calculations
        test_cases = [
            ("openai", "gpt-4", 1000, 500, 0.06),
            ("openai", "gpt-4o-mini", 10000, 5000, 0.0045),
            ("anthropic", "claude-3-5-sonnet-20241022", 2000, 1000, 0.021),
            ("google", "gemini-1.5-flash", 50000, 10000, 0.00675),
        ]
        
        for provider, model, input_tokens, output_tokens, expected in test_cases:
            cost = calculate_cost(provider, model, input_tokens, output_tokens)
            assert abs(cost - expected) < 0.0001, f"Expected {expected}, got {cost}"
            logger.info(f"{provider}/{model}: {input_tokens}+{output_tokens} tokens = ${cost:.6f}")
            
        logger.info("✅ Standalone calculate_cost function passed")


class TestEventSystem:
    """Test the event system thoroughly."""
    
    def setup_method(self):
        """Setup for each test method."""
        logger.info("Setting up event system test...")
        
    def test_session_id_management(self):
        """Test session ID generation and management."""
        logger.info("Testing session ID management...")
        
        # Test session ID generation through get_current_session_id
        import uuid
        session_id1 = str(uuid.uuid4())
        session_id2 = str(uuid.uuid4())
        assert session_id1 != session_id2
        assert len(session_id1) == 36  # UUID format
        logger.info(f"Generated session IDs: {session_id1}, {session_id2}")
        
        # Test setting and getting current session ID
        set_session_id("test-session-123")
        current = get_current_session_id()
        assert current == "test-session-123"
        
        # Test automatic generation - reset thread local storage first
        from amplitude.ai.events import _local
        if hasattr(_local, 'session_id'):
            delattr(_local, 'session_id')
        
        auto_generated = get_current_session_id()
        assert auto_generated is not None
        assert len(auto_generated) == 36
        logger.info(f"Auto-generated session ID: {auto_generated}")
        
        logger.info("✅ Session ID management passed")
        
    def test_event_creation_and_properties(self):
        """Test event creation with all properties."""
        logger.info("Testing event creation and properties...")
        
        # Test LLMRunStartedEvent
        start_event = LLMRunStartedEvent(
            session_id="test-session",
            user_id="user-123",
            device_id="device-456",
            model_provider="openai",
            model_name="gpt-4"
        )
        assert start_event.event_type == "llm_run_started"
        assert start_event.event_properties["session_id"] == "test-session"
        assert start_event.event_properties["model_provider"] == "openai"
        logger.info(f"Created LLMRunStartedEvent: {start_event.event_type}")
        
        # Test LLMMessageEvent with full properties
        message_event = LLMMessageEvent(
            session_id="test-session",
            user_id="user-123",
            model_provider="openai",
            model_name="gpt-4",
            input_tokens=1000,
            output_tokens=500,
            total_tokens=1500,
            latency_ms=2500,
            cost_usd=0.06,
            input_messages=[{"role": "user", "content": "Hello"}],
            output_content="Hi there!",
            finish_reason="stop",
            temperature=0.7,
            max_tokens=1000
        )
        assert message_event.event_type == "llm_message"
        assert message_event.event_properties["input_tokens"] == 1000
        assert message_event.event_properties["output_tokens"] == 500
        assert message_event.event_properties["cost_usd"] == 0.06
        logger.info(f"Created LLMMessageEvent with cost: ${message_event.event_properties['cost_usd']}")
        
        # Test UserMessageEvent
        user_event = UserMessageEvent(
            session_id="test-session",
            user_id="user-123",
            content="What is AI?",
            message_type="text"
        )
        assert user_event.event_type == "user_message"
        assert user_event.event_properties["content"] == "What is AI?"
        
        # Test ToolCalledEvent
        tool_event = ToolCalledEvent(
            session_id="test-session",
            tool_name="web_search",
            tool_parameters={"query": "Python tutorial"},
            tool_result={"results": ["link1", "link2"]},
            execution_time_ms=1200,
            success=True
        )
        assert tool_event.event_type == "tool_called"
        assert tool_event.event_properties["success"] is True
        assert tool_event.event_properties["execution_time_ms"] == 1200
        
        # Test LLMRunFinishedEvent
        finish_event = LLMRunFinishedEvent(
            session_id="test-session",
            total_messages=5,
            total_tokens=7500,
            total_cost_usd=0.45,
            duration_ms=30000,
            success=True
        )
        assert finish_event.event_type == "llm_run_finished"
        assert finish_event.event_properties["total_messages"] == 5
        assert finish_event.event_properties["success"] is True
        
        logger.info("✅ Event creation and properties passed")


class TestInstrumentationSystem:
    """Test the instrumentation system."""
    
    def test_session_manager(self):
        """Test SessionManager functionality."""
        logger.info("Testing SessionManager functionality...")
        
        # Mock Amplitude client
        mock_client = Mock()
        config = AIConfig()
        
        session_manager = SessionManager(
            amplitude_client=mock_client,
            ai_config=config,
            provider_name="test-provider"
        )
        
        # Test session start
        session_id = session_manager.start_session(model_name="test-model")
        assert session_id is not None
        assert session_manager.session_start_time is not None
        logger.info(f"Started session: {session_id}")
        
        # Test stats update
        session_manager.update_stats(total_tokens=1500, cost_usd=0.075)
        assert session_manager.session_stats["total_messages"] == 1
        assert session_manager.session_stats["total_tokens"] == 1500
        assert session_manager.session_stats["total_cost_usd"] == 0.075
        
        # Test multiple updates
        session_manager.update_stats(total_tokens=800, cost_usd=0.040)
        assert session_manager.session_stats["total_messages"] == 2
        assert session_manager.session_stats["total_tokens"] == 2300
        assert abs(session_manager.session_stats["total_cost_usd"] - 0.115) < 0.001
        
        # Test session finish
        session_manager.finish_session(success=True)
        
        # Verify events were emitted
        assert mock_client.track.call_count >= 2  # start + finish events
        
        logger.info("✅ SessionManager functionality passed")
        
    def test_event_emitter(self):
        """Test EventEmitter with both sync and async modes."""
        logger.info("Testing EventEmitter...")
        
        mock_client = Mock()
        config = AIConfig(async_event_emission=False)
        
        emitter = EventEmitter(mock_client, config)
        
        # Create test event
        test_event = LLMRunStartedEvent(
            session_id="test",
            model_provider="test"
        )
        
        # Test synchronous emission
        emitter.emit_event(test_event)
        mock_client.track.assert_called_once_with(test_event)
        
        # Test asynchronous emission
        config_async = AIConfig(async_event_emission=True)
        emitter_async = EventEmitter(mock_client, config_async)
        
        mock_client.reset_mock()
        emitter_async.emit_event(test_event)
        
        # Give async thread time to complete
        time.sleep(0.1)
        mock_client.track.assert_called_once_with(test_event)
        
        logger.info("✅ EventEmitter functionality passed")


class TestManualTracking:
    """Test manual tracking APIs."""
    
    def test_message_timer(self):
        """Test MessageTimer functionality."""
        logger.info("Testing MessageTimer...")
        
        timer = MessageTimer()
        
        # Test basic timing
        timer.start()
        time.sleep(0.1)  # Sleep for 100ms
        duration = timer.stop()
        
        assert duration >= 90  # Allow some tolerance
        assert duration <= 150
        assert timer.duration_ms >= 90
        logger.info(f"Timer measured: {duration}ms")
        
        # Test context manager
        with timer.time():
            time.sleep(0.05)  # Sleep for 50ms
            
        assert timer.duration_ms >= 45
        assert timer.duration_ms <= 80
        logger.info(f"Context manager measured: {timer.duration_ms}ms")
        
        logger.info("✅ MessageTimer functionality passed")
        
    def test_llm_session_tracker(self):
        """Test LLMSessionTracker functionality."""
        logger.info("Testing LLMSessionTracker...")
        
        mock_client = Mock()
        config = AIConfig()
        
        tracker = LLMSessionTracker(
            amplitude_client=mock_client,
            ai_config=config,
            user_id="test-user",
            model_provider="openai",
            model_name="gpt-4"
        )
        
        # Test session start
        session_id = tracker.start_session()
        assert session_id is not None
        logger.info(f"Started tracking session: {session_id}")
        
        # Test user message tracking
        tracker.track_user_message(
            content="What is machine learning?",
            message_type="text"
        )
        
        # Test LLM message tracking
        tracker.track_message(
            input_tokens=100,
            output_tokens=200,
            latency_ms=1500,
            output_content="Machine learning is...",
            temperature=0.7,
            finish_reason="stop"
        )
        
        # Test tool call tracking
        tracker.track_tool_call(
            tool_name="calculator",
            tool_parameters={"expression": "2+2"},
            tool_result={"result": 4},
            execution_time_ms=50,
            success=True
        )
        
        # Test session finish
        tracker.finish_session(success=True)
        
        # Verify session stats were updated
        assert tracker.session_stats["total_messages"] == 1
        assert tracker.session_stats["total_tokens"] == 300
        assert tracker.session_stats["total_cost_usd"] > 0
        
        # Verify multiple events were emitted
        assert mock_client.track.call_count >= 4  # start, user, message, tool, finish
        
        logger.info(f"Session stats: {tracker.session_stats}")
        logger.info("✅ LLMSessionTracker functionality passed")
        
    def test_llm_session_context_manager(self):
        """Test llm_session context manager."""
        logger.info("Testing llm_session context manager...")
        
        mock_client = Mock()
        config = AIConfig()
        
        # Test successful session
        with llm_session(
            amplitude_client=mock_client,
            ai_config=config,
            user_id="test-user",
            model_provider="anthropic",
            model_name="claude-3-sonnet"
        ) as session:
            assert isinstance(session, LLMSessionTracker)
            
            session.track_user_message("Hello")
            session.track_message(
                input_tokens=50,
                output_tokens=100,
                latency_ms=800,
                output_content="Hi there!"
            )
            
        # Verify session was properly finished
        finish_calls = [call for call in mock_client.track.call_args_list 
                      if hasattr(call[0][0], 'event_type') and 
                      call[0][0].event_type == 'llm_run_finished']
        assert len(finish_calls) >= 1
        
        # Check that the finish event indicates success
        finish_event = finish_calls[0][0][0]
        assert finish_event.event_properties["success"] is True
        
        logger.info("✅ llm_session context manager passed")
        
    def test_quick_track_message(self):
        """Test quick_track_message convenience function."""
        logger.info("Testing quick_track_message...")
        
        mock_client = Mock()
        
        quick_track_message(
            amplitude_client=mock_client,
            model_provider="openai",
            model_name="gpt-3.5-turbo",
            input_content="Hello, world!",
            output_content="Hi there! How can I help?",
            input_tokens=25,
            output_tokens=50,
            latency_ms=1200,
            user_id="test-user"
        )
        
        # Verify an event was emitted
        mock_client.track.assert_called_once()
        
        # Verify the event has correct properties
        event = mock_client.track.call_args[0][0]
        assert event.event_type == "llm_message"
        assert event.event_properties["model_provider"] == "openai"
        assert event.event_properties["model_name"] == "gpt-3.5-turbo"
        assert event.event_properties["input_tokens"] == 25
        assert event.event_properties["output_tokens"] == 50
        assert event.event_properties["total_tokens"] == 75
        assert event.event_properties["latency_ms"] == 1200
        assert event.event_properties["cost_usd"] is not None  # Should calculate cost
        
        logger.info(f"Quick track event cost: ${event.event_properties['cost_usd']:.6f}")
        logger.info("✅ quick_track_message functionality passed")


def run_comprehensive_tests():
    """Run all comprehensive tests with detailed logging."""
    logger.info("🧪 Starting comprehensive AI observability tests...")
    logger.info("=" * 60)
    
    test_classes = [
        TestAIConfig,
        TestPricingModule, 
        TestEventSystem,
        TestInstrumentationSystem,
        TestManualTracking
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for test_class in test_classes:
        logger.info(f"\n📋 Running {test_class.__name__} tests...")
        test_instance = test_class()
        
        # Get all test methods
        test_methods = [method for method in dir(test_instance) 
                       if method.startswith('test_')]
        
        for test_method_name in test_methods:
            total_tests += 1
            try:
                # Setup if exists
                if hasattr(test_instance, 'setup_method'):
                    test_instance.setup_method()
                    
                # Run the test
                test_method = getattr(test_instance, test_method_name)
                test_method()
                passed_tests += 1
                logger.info(f"  ✅ {test_method_name} PASSED")
                
            except Exception as e:
                logger.error(f"  ❌ {test_method_name} FAILED: {e}")
                import traceback
                traceback.print_exc()
    
    logger.info("\n" + "=" * 60)
    logger.info(f"🎯 Test Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        logger.info("🎉 ALL TESTS PASSED! Core functionality is working correctly.")
    else:
        logger.warning(f"⚠️ {total_tests - passed_tests} tests failed. Please review failures above.")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    success = run_comprehensive_tests()
    exit(0 if success else 1)