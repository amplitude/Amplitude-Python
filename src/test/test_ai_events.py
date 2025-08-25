"""Tests for AI observability events."""

import unittest
import time
from unittest.mock import Mock, patch

from amplitude.client import Amplitude
from amplitude.ai.events import (
    LLMRunStartedEvent,
    LLMMessageEvent,
    UserMessageEvent,
    ToolCalledEvent,
    LLMRunFinishedEvent,
    get_current_session_id,
    set_session_id
)
from amplitude.ai.config import AIConfig
from amplitude.ai.manual import LLMSessionTracker, llm_session, MessageTimer


class TestAIEvents(unittest.TestCase):
    """Test AI event classes."""
    
    def test_llm_run_started_event(self):
        """Test LLMRunStartedEvent creation and properties."""
        event = LLMRunStartedEvent(
            user_id="test_user",
            model_provider="openai",
            model_name="gpt-4"
        )
        
        self.assertEqual(event.event_type, "llm_run_started")
        self.assertEqual(event.user_id, "test_user")
        self.assertIn("model_provider", event.event_properties)
        self.assertEqual(event.event_properties["model_provider"], "openai")
        self.assertEqual(event.event_properties["model_name"], "gpt-4")
        self.assertIn("session_id", event.event_properties)
    
    def test_llm_message_event(self):
        """Test LLMMessageEvent creation and properties."""
        event = LLMMessageEvent(
            user_id="test_user",
            model_provider="anthropic",
            model_name="claude-3",
            input_tokens=100,
            output_tokens=50,
            latency_ms=1500,
            cost_usd=0.05
        )
        
        self.assertEqual(event.event_type, "llm_message")
        self.assertEqual(event.user_id, "test_user")
        self.assertEqual(event.event_properties["input_tokens"], 100)
        self.assertEqual(event.event_properties["output_tokens"], 50)
        self.assertEqual(event.event_properties["total_tokens"], 150)
        self.assertEqual(event.event_properties["latency_ms"], 1500)
        self.assertEqual(event.event_properties["cost_usd"], 0.05)
    
    def test_user_message_event(self):
        """Test UserMessageEvent creation and properties."""
        event = UserMessageEvent(
            user_id="test_user",
            content="Hello, how are you?",
            message_type="text"
        )
        
        self.assertEqual(event.event_type, "user_message")
        self.assertEqual(event.user_id, "test_user")
        self.assertEqual(event.event_properties["content"], "Hello, how are you?")
        self.assertEqual(event.event_properties["message_type"], "text")
    
    def test_tool_called_event(self):
        """Test ToolCalledEvent creation and properties."""
        event = ToolCalledEvent(
            user_id="test_user",
            tool_name="calculator",
            tool_parameters={"operation": "add", "a": 1, "b": 2},
            tool_result={"result": 3},
            execution_time_ms=100,
            success=True
        )
        
        self.assertEqual(event.event_type, "tool_called")
        self.assertEqual(event.user_id, "test_user")
        self.assertEqual(event.event_properties["tool_name"], "calculator")
        self.assertEqual(event.event_properties["success"], True)
    
    def test_llm_run_finished_event(self):
        """Test LLMRunFinishedEvent creation and properties."""
        event = LLMRunFinishedEvent(
            user_id="test_user",
            total_messages=5,
            total_tokens=1000,
            total_cost_usd=0.25,
            duration_ms=30000,
            success=True
        )
        
        self.assertEqual(event.event_type, "llm_run_finished")
        self.assertEqual(event.user_id, "test_user")
        self.assertEqual(event.event_properties["total_messages"], 5)
        self.assertEqual(event.event_properties["total_tokens"], 1000)
        self.assertEqual(event.event_properties["success"], True)
    
    def test_session_id_management(self):
        """Test session ID management."""
        original_session_id = get_current_session_id()
        
        # Set custom session ID
        custom_session_id = "custom-session-123"
        set_session_id(custom_session_id)
        
        self.assertEqual(get_current_session_id(), custom_session_id)
        
        # Create event with custom session ID
        event = LLMRunStartedEvent(model_provider="test")
        self.assertEqual(event.event_properties["session_id"], custom_session_id)


class TestAIConfig(unittest.TestCase):
    """Test AI configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = AIConfig()
        
        self.assertFalse(config.privacy_mode)
        self.assertTrue(config.token_tracking)
        self.assertTrue(config.cost_tracking)
        self.assertIsNotNone(config.openai_cost_per_token)
        self.assertIn("gpt-4", config.openai_cost_per_token)
    
    def test_cost_calculation(self):
        """Test cost calculation."""
        config = AIConfig()
        
        # Test OpenAI cost calculation
        cost = config.calculate_cost("openai", "gpt-4", 1000, 500)
        self.assertIsNotNone(cost)
        self.assertGreater(cost, 0)
        
        # Test unknown model
        cost = config.calculate_cost("openai", "unknown-model", 1000, 500)
        self.assertIsNone(cost)
        
        # Test with cost tracking disabled
        config.cost_tracking = False
        cost = config.calculate_cost("openai", "gpt-4", 1000, 500)
        self.assertIsNone(cost)
    
    def test_privacy_settings(self):
        """Test privacy settings."""
        config = AIConfig()
        
        # Test default settings
        self.assertFalse(config.should_exclude_content("input"))
        self.assertFalse(config.should_exclude_content("output"))
        
        # Test privacy mode
        config.privacy_mode = True
        self.assertTrue(config.should_exclude_content("input"))
        self.assertTrue(config.should_exclude_content("output"))
        
        # Test specific exclusions
        config.privacy_mode = False
        config.exclude_input = True
        config.exclude_output = True
        self.assertTrue(config.should_exclude_content("input"))
        self.assertTrue(config.should_exclude_content("output"))
    
    def test_content_truncation(self):
        """Test content truncation."""
        config = AIConfig()
        config.max_content_length = 10
        
        short_content = "Hello"
        self.assertEqual(config.truncate_content(short_content), "Hello")
        
        long_content = "This is a very long content that should be truncated"
        truncated = config.truncate_content(long_content)
        self.assertEqual(len(truncated), 10)
        self.assertTrue(truncated.endswith("..."))


class TestLLMSessionTracker(unittest.TestCase):
    """Test LLM session tracking."""
    
    def setUp(self):
        """Set up test client."""
        self.mock_client = Mock(spec=Amplitude)
    
    def test_session_tracker_basic(self):
        """Test basic session tracking."""
        tracker = LLMSessionTracker(
            amplitude_client=self.mock_client,
            user_id="test_user",
            model_provider="openai",
            model_name="gpt-4"
        )
        
        # Start session
        session_id = tracker.start_session()
        self.assertIsNotNone(session_id)
        self.mock_client.track.assert_called()
        
        # Track message
        tracker.track_message(
            input_tokens=100,
            output_tokens=50,
            latency_ms=1000
        )
        self.assertEqual(tracker.session_stats["total_messages"], 1)
        self.assertEqual(tracker.session_stats["total_tokens"], 150)
        
        # Finish session
        tracker.finish_session()
        self.assertGreaterEqual(self.mock_client.track.call_count, 3)  # start + message + finish
    
    def test_session_context_manager(self):
        """Test session context manager."""
        with patch('amplitude.ai.manual.emit_llm_run_started') as mock_start, \
             patch('amplitude.ai.manual.emit_llm_run_finished') as mock_finish:
            
            with llm_session(self.mock_client, model_provider="test") as session:
                self.assertIsInstance(session, LLMSessionTracker)
                session.track_message(output_tokens=10)
            
            mock_start.assert_called_once()
            mock_finish.assert_called_once()
    
    def test_session_error_handling(self):
        """Test session error handling."""
        with patch('amplitude.ai.manual.emit_llm_run_started') as mock_start, \
             patch('amplitude.ai.manual.emit_llm_run_finished') as mock_finish:
            
            try:
                with llm_session(self.mock_client, model_provider="test") as session:
                    raise ValueError("Test error")
            except ValueError:
                pass
            
            mock_start.assert_called_once()
            mock_finish.assert_called_once()
            # Check that error was recorded
            call_args = mock_finish.call_args[1]
            self.assertFalse(call_args.get('success', True))
            self.assertIsNotNone(call_args.get('error_message'))


class TestMessageTimer(unittest.TestCase):
    """Test message timer."""
    
    def test_manual_timing(self):
        """Test manual timing."""
        timer = MessageTimer()
        
        timer.start()
        time.sleep(0.01)  # Sleep 10ms
        duration = timer.stop()
        
        self.assertGreater(duration, 5)  # Should be at least 5ms
        self.assertLess(duration, 50)    # Should be less than 50ms
    
    def test_context_manager_timing(self):
        """Test context manager timing."""
        timer = MessageTimer()
        
        with timer.time():
            time.sleep(0.01)  # Sleep 10ms
        
        self.assertGreater(timer.duration_ms, 5)
        self.assertLess(timer.duration_ms, 50)


if __name__ == '__main__':
    unittest.main()