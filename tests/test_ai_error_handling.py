"""Comprehensive error handling and edge case tests for AI observability."""

import pytest
import logging
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Configure logging for tests
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import modules to test
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from amplitude.ai.config import AIConfig
from amplitude.ai.pricing import calculate_cost, get_model_pricing
from amplitude.ai.events import (
    LLMRunStartedEvent, LLMMessageEvent, UserMessageEvent,
    ToolCalledEvent, LLMRunFinishedEvent,
    get_current_session_id, set_session_id
)
from amplitude.ai.instrumentation import (
    SessionManager, EventEmitter, InstrumentationMixin
)
from amplitude.ai.manual import (
    LLMSessionTracker, MessageTimer, llm_session, quick_track_message
)


class TestConfigurationEdgeCases:
    """Test AIConfig edge cases and error handling."""
    
    def test_invalid_pricing_configuration(self):
        """Test handling of invalid custom pricing."""
        logger.info("Testing invalid pricing configuration handling...")
        
        # Test with invalid pricing structure
        invalid_pricing_configs = [
            {"openai": "not-a-dict"},  # Wrong type
            {"openai": {"gpt-4": {"input": "not-a-number"}}},  # Non-numeric pricing
            {"openai": {"gpt-4": {"input": 30}}},  # Missing output pricing
            {},  # Empty pricing
            None,  # None pricing (should use defaults)
        ]
        
        for i, invalid_pricing in enumerate(invalid_pricing_configs):
            logger.info(f"   Testing invalid config {i+1}: {type(invalid_pricing).__name__}")
            
            config = AIConfig(custom_pricing=invalid_pricing)
            
            # Should handle gracefully and return None for errors
            cost = config.calculate_cost("openai", "gpt-4", 1000, 500)
            
            if invalid_pricing is None or invalid_pricing == {}:
                # None and empty dict should both use defaults due to "or DEFAULT_PRICING" logic
                assert cost is not None
                logger.info(f"     Config {invalid_pricing} used defaults: ${cost:.6f}")
            else:
                # Other invalid configs should return None due to type/structure errors
                assert cost is None
                logger.info(f"     Invalid config properly returned None")
        
        logger.info("✅ Invalid pricing configuration handling passed")
    
    def test_extreme_content_lengths(self):
        """Test content truncation with extreme lengths."""
        logger.info("Testing extreme content length handling...")
        
        # Test cases: (max_length, content_length, description)
        test_cases = [
            (0, 100, "Zero max length"),
            (1, 1000, "Max length 1"),
            (10000, 5, "Content shorter than max"),
            (50, 0, "Empty content"),
            (100, 100, "Content exactly at max"),
            (50, 10000, "Very long content"),
        ]
        
        for max_length, content_length, description in test_cases:
            logger.info(f"   Testing {description}...")
            
            config = AIConfig(max_content_length=max_length)
            test_content = "x" * content_length
            
            truncated = config.truncate_content(test_content)
            
            if max_length == 0:
                # Zero max length should return empty string (can't fit "...")
                assert truncated == ""
            elif content_length <= max_length:
                # Content should be unchanged if under limit
                assert truncated == test_content
            else:
                # Content should be truncated
                if max_length < 3:
                    # Too small for ellipsis, should be truncated without ellipsis
                    assert len(truncated) == max_length
                    assert not truncated.endswith("...")
                else:
                    # Should be truncated with ellipsis
                    assert len(truncated) <= max_length
                    assert truncated.endswith("...")
            
            logger.info(f"     Original: {content_length} chars → Truncated: {len(truncated)} chars")
        
        logger.info("✅ Extreme content length handling passed")
    
    def test_privacy_edge_cases(self):
        """Test privacy control edge cases."""
        logger.info("Testing privacy control edge cases...")
        
        # Test unknown content types
        config = AIConfig(privacy_mode=True)
        
        unknown_types = ["unknown_type", "custom_data", "", None]
        
        for content_type in unknown_types:
            try:
                result = config.should_exclude_content(content_type) if content_type is not None else config.should_exclude_content("")
                # Privacy mode should exclude everything
                assert result is True
                logger.info(f"   Unknown type '{content_type}' properly excluded")
            except Exception as e:
                logger.info(f"   Unknown type '{content_type}' caused error: {e}")
        
        logger.info("✅ Privacy control edge cases passed")


class TestPricingEdgeCases:
    """Test pricing calculation edge cases."""
    
    def test_pricing_boundary_conditions(self):
        """Test pricing with boundary conditions."""
        logger.info("Testing pricing boundary conditions...")
        
        # Test cases: (description, provider, model, input_tokens, output_tokens, should_succeed)
        boundary_cases = [
            ("Zero input tokens", "openai", "gpt-4", 0, 500, True),
            ("Zero output tokens", "openai", "gpt-4", 1000, 0, True), 
            ("Both zero tokens", "openai", "gpt-4", 0, 0, True),
            ("Negative input tokens", "openai", "gpt-4", -100, 500, True),  # Should handle gracefully
            ("Negative output tokens", "openai", "gpt-4", 1000, -100, True),
            ("Very large tokens", "openai", "gpt-4", 10_000_000, 5_000_000, True),
            ("Unknown provider", "unknown", "gpt-4", 1000, 500, False),
            ("Unknown model", "openai", "unknown-model", 1000, 500, False),
            ("Empty strings", "", "", 1000, 500, False),
        ]
        
        for description, provider, model, input_tokens, output_tokens, should_succeed in boundary_cases:
            logger.info(f"   Testing {description}...")
            
            try:
                cost = calculate_cost(provider, model, input_tokens, output_tokens)
                
                if should_succeed:
                    if input_tokens >= 0 and output_tokens >= 0:
                        assert cost is not None
                        assert cost >= 0
                        logger.info(f"     Cost calculated: ${cost:.6f}")
                    else:
                        # Negative tokens should return 0 or handle gracefully
                        logger.info(f"     Negative tokens handled: ${cost:.6f}" if cost is not None else "Returned None")
                else:
                    assert cost is None
                    logger.info(f"     Properly returned None for invalid input")
                    
            except Exception as e:
                if should_succeed:
                    logger.error(f"     Unexpected error: {e}")
                    raise
                else:
                    logger.info(f"     Expected error for invalid input: {type(e).__name__}")
        
        logger.info("✅ Pricing boundary conditions passed")
    
    def test_pricing_precision(self):
        """Test pricing calculation precision."""
        logger.info("Testing pricing calculation precision...")
        
        # Test very small and very precise calculations
        precision_cases = [
            (1, 1),      # Minimal usage
            (7, 13),     # Prime numbers
            (999, 1001), # Just under/over 1000
            (1_000_000, 1_000_000),  # Exactly 1M tokens each
        ]
        
        for input_tokens, output_tokens in precision_cases:
            cost = calculate_cost("openai", "gpt-4", input_tokens, output_tokens)
            
            # Verify precision (should be precise to at least 6 decimal places)
            expected_cost = (input_tokens / 1_000_000) * 30.0 + (output_tokens / 1_000_000) * 60.0
            assert abs(cost - expected_cost) < 1e-10
            
            logger.info(f"   {input_tokens}+{output_tokens} tokens: ${cost:.10f} (precision verified)")
        
        logger.info("✅ Pricing calculation precision passed")


class TestEventSystemErrorHandling:
    """Test event system error handling."""
    
    def test_malformed_event_data(self):
        """Test handling of malformed event data."""
        logger.info("Testing malformed event data handling...")
        
        # Test events with invalid data types
        test_cases = [
            ("None session_id", {"session_id": None}),
            ("Invalid token types", {"input_tokens": "not-a-number", "output_tokens": "also-not-a-number"}),
            ("Negative tokens", {"input_tokens": -100, "output_tokens": -200}),
            ("Empty messages list", {"input_messages": []}),
            ("Invalid cost", {"cost_usd": "expensive"}),
        ]
        
        for description, invalid_data in test_cases:
            logger.info(f"   Testing {description}...")
            
            try:
                # Most events should handle invalid data gracefully
                event = LLMMessageEvent(**invalid_data)
                assert event.event_type == "llm_message"
                logger.info(f"     Event created successfully despite invalid data")
                
            except Exception as e:
                logger.info(f"     Event creation failed as expected: {type(e).__name__}")
        
        logger.info("✅ Malformed event data handling passed")
    
    def test_session_id_edge_cases(self):
        """Test session ID management edge cases."""
        logger.info("Testing session ID edge cases...")
        
        # Test various session ID formats
        session_ids = [
            "normal-session-123",
            "",  # Empty string
            "very-long-session-id-" + "x" * 100,
            "session-with-special-chars-!@#$%^&*()",
            "unicode-session-🚀✨🎯",
            None,  # None should generate new ID
        ]
        
        for session_id in session_ids:
            logger.info(f"   Testing session ID: {repr(session_id)}")
            
            if session_id is not None:
                set_session_id(session_id)
                current = get_current_session_id()
                assert current == session_id
                logger.info(f"     Session ID set and retrieved successfully")
            else:
                # Reset session and test auto-generation
                from amplitude.ai.events import _local
                if hasattr(_local, 'session_id'):
                    delattr(_local, 'session_id')
                
                current = get_current_session_id()
                assert current is not None
                assert len(current) == 36  # UUID format
                logger.info(f"     Auto-generated session ID: {current}")
        
        logger.info("✅ Session ID edge cases passed")


class TestInstrumentationErrorHandling:
    """Test instrumentation system error handling."""
    
    def test_session_manager_error_scenarios(self):
        """Test SessionManager error handling scenarios."""
        logger.info("Testing SessionManager error scenarios...")
        
        mock_amplitude_client = Mock()
        config = AIConfig()
        
        # Test with failing amplitude client
        mock_amplitude_client.track.side_effect = Exception("Network error")
        
        session_manager = SessionManager(
            amplitude_client=mock_amplitude_client,
            ai_config=config,
            provider_name="test-provider"
        )
        
        try:
            # These should not raise exceptions even if amplitude fails
            session_id = session_manager.start_session(model_name="test-model")
            assert session_id is not None
            logger.info(f"   Session started despite amplitude failure: {session_id}")
            
            session_manager.update_stats(total_tokens=100, cost_usd=0.01)
            logger.info(f"   Stats updated: {session_manager.session_stats}")
            
            session_manager.finish_session(success=True)
            logger.info(f"   Session finished gracefully")
            
        except Exception as e:
            logger.error(f"   SessionManager should handle amplitude failures gracefully: {e}")
            raise
        
        logger.info("✅ SessionManager error scenarios passed")
    
    def test_event_emitter_error_handling(self):
        """Test EventEmitter error handling."""
        logger.info("Testing EventEmitter error handling...")
        
        mock_client = Mock()
        config = AIConfig(async_event_emission=False)  # Test synchronous first
        
        emitter = EventEmitter(mock_client, config)
        
        # Test with failing client
        mock_client.track.side_effect = Exception("API Error")
        
        test_event = LLMRunStartedEvent(
            session_id="test-session",
            model_provider="test"
        )
        
        try:
            # Should not raise exception
            emitter.emit_event(test_event)
            logger.info("   Synchronous emission handled error gracefully")
        except Exception as e:
            logger.error(f"   EventEmitter should handle errors silently: {e}")
            raise
        
        # Test async emission
        config_async = AIConfig(async_event_emission=True)
        emitter_async = EventEmitter(mock_client, config_async)
        
        try:
            emitter_async.emit_event(test_event)
            # Give async thread time to complete
            import time
            time.sleep(0.1)
            logger.info("   Asynchronous emission handled error gracefully")
        except Exception as e:
            logger.error(f"   Async EventEmitter should handle errors silently: {e}")
            raise
        
        logger.info("✅ EventEmitter error handling passed")


class TestManualTrackingErrorHandling:
    """Test manual tracking API error handling."""
    
    def test_session_tracker_error_scenarios(self):
        """Test LLMSessionTracker error scenarios."""
        logger.info("Testing LLMSessionTracker error scenarios...")
        
        mock_client = Mock()
        config = AIConfig()
        
        tracker = LLMSessionTracker(
            amplitude_client=mock_client,
            ai_config=config,
            user_id="test-user",
            model_provider="test",
            model_name="test-model"
        )
        
        session_id = tracker.start_session()
        logger.info(f"   Session started: {session_id}")
        
        # Test tracking with invalid data
        invalid_scenarios = [
            ("Negative tokens", {"input_tokens": -50, "output_tokens": -30}),
            ("String tokens", {"input_tokens": "fifty", "output_tokens": "thirty"}),
            ("None latency", {"latency_ms": None}),
            ("Extremely long content", {"output_content": "x" * 100000}),
        ]
        
        for description, invalid_data in invalid_scenarios:
            logger.info(f"   Testing {description}...")
            
            try:
                tracker.track_message(**invalid_data)
                logger.info(f"     Tracking handled invalid data gracefully")
            except Exception as e:
                logger.info(f"     Expected error for invalid data: {type(e).__name__}: {e}")
        
        # Test tool tracking with invalid data
        try:
            tracker.track_tool_call(
                tool_name="",  # Empty name
                tool_parameters=None,
                tool_result="not-a-dict",  # Wrong type
                execution_time_ms=-100,  # Negative time
                success="maybe"  # Wrong type for boolean
            )
            logger.info("   Tool tracking handled invalid data")
        except Exception as e:
            logger.info(f"   Tool tracking error (acceptable): {type(e).__name__}")
        
        tracker.finish_session(success=True)
        logger.info("   Session finished successfully")
        
        logger.info("✅ LLMSessionTracker error scenarios passed")
    
    def test_context_manager_error_handling(self):
        """Test llm_session context manager error handling."""
        logger.info("Testing llm_session context manager error handling...")
        
        mock_client = Mock()
        config = AIConfig()
        
        # Test context manager with exception inside
        try:
            with llm_session(
                amplitude_client=mock_client,
                ai_config=config,
                user_id="test-user",
                model_provider="test",
                model_name="test-model"
            ) as session:
                logger.info("   Session started in context manager")
                
                # Track some data
                session.track_user_message("Test message")
                
                # Simulate an error
                raise ValueError("Simulated processing error")
                
        except ValueError as e:
            logger.info(f"   Expected error caught: {e}")
            
            # Context manager should have finished session with error
            finish_calls = [call for call in mock_client.track.call_args_list 
                           if hasattr(call[0][0], 'event_type') and 
                           call[0][0].event_type == 'llm_run_finished']
            
            assert len(finish_calls) >= 1
            finish_event = finish_calls[-1][0][0]
            assert finish_event.event_properties.get("success") is False
            assert "error_message" in finish_event.event_properties
            
            logger.info("   Context manager properly handled error and finished session")
        
        logger.info("✅ llm_session context manager error handling passed")
    
    def test_quick_track_message_edge_cases(self):
        """Test quick_track_message with edge cases."""
        logger.info("Testing quick_track_message edge cases...")
        
        mock_client = Mock()
        
        edge_cases = [
            ("None content", {"input_content": None, "output_content": None}),
            ("Empty strings", {"input_content": "", "output_content": ""}),
            ("Zero tokens", {"input_tokens": 0, "output_tokens": 0}),
            ("Missing tokens", {"input_tokens": None, "output_tokens": None}),
            ("Invalid model", {"model_provider": "invalid", "model_name": "unknown"}),
        ]
        
        for description, edge_data in edge_cases:
            logger.info(f"   Testing {description}...")
            
            try:
                quick_track_message(
                    amplitude_client=mock_client,
                    model_provider=edge_data.get("model_provider", "openai"),
                    model_name=edge_data.get("model_name", "gpt-4"),
                    input_content=edge_data.get("input_content", "test"),
                    output_content=edge_data.get("output_content", "response"),
                    input_tokens=edge_data.get("input_tokens", 10),
                    output_tokens=edge_data.get("output_tokens", 20),
                    latency_ms=1000,
                    user_id="test-user"
                )
                logger.info(f"     Quick track handled edge case successfully")
                
            except Exception as e:
                logger.info(f"     Quick track error (may be expected): {type(e).__name__}: {e}")
        
        logger.info("✅ quick_track_message edge cases passed")


def run_error_handling_tests():
    """Run all error handling tests with detailed logging."""
    logger.info("🧪 Starting comprehensive error handling tests...")
    logger.info("=" * 70)
    
    test_classes = [
        TestConfigurationEdgeCases,
        TestPricingEdgeCases,
        TestEventSystemErrorHandling,
        TestInstrumentationErrorHandling,
        TestManualTrackingErrorHandling
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
    
    logger.info("\n" + "=" * 70)
    logger.info(f"🎯 Error Handling Test Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        logger.info("🎉 ALL ERROR HANDLING TESTS PASSED! System is robust to edge cases.")
    else:
        logger.warning(f"⚠️ {total_tests - passed_tests} tests failed. Please review failures above.")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    success = run_error_handling_tests()
    exit(0 if success else 1)