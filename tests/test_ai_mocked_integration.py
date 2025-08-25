"""Integration tests with proper mocking to bypass import guards."""

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


class TestProviderWrapperIntegration:
    """Test provider wrapper integration with proper mocking."""
    
    def test_openai_wrapper_with_mocking(self):
        """Test OpenAI wrapper with proper mocking."""
        logger.info("Testing OpenAI wrapper integration with mocking...")
        
        # Mock the OpenAI package at import time
        mock_openai_module = Mock()
        mock_openai_client = Mock()
        mock_async_openai_client = Mock()
        
        mock_openai_module.OpenAI = Mock(return_value=mock_openai_client)
        mock_openai_module.AsyncOpenAI = Mock(return_value=mock_async_openai_client)
        
        with patch.dict('sys.modules', {'openai': mock_openai_module}):
            # Now import and test the OpenAI wrapper
            from amplitude.ai.openai import OpenAI, AsyncOpenAI
            
            mock_amplitude_client = Mock()
            config = AIConfig(cost_tracking=True)
            
            # Create wrapper - should now succeed with mocked OpenAI
            wrapper = OpenAI(
                api_key="test-key",
                amplitude_client=mock_amplitude_client,
                ai_config=config,
                auto_start_session=False
            )
            
            # Verify basic properties
            assert wrapper.get_provider_name() == "openai"
            assert wrapper.amplitude_client == mock_amplitude_client
            assert wrapper.ai_config == config
            
            # Mock a response for testing instrumentation
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "Hello there!"
            mock_response.usage = Mock()
            mock_response.usage.prompt_tokens = 15
            mock_response.usage.completion_tokens = 20
            mock_response.usage.total_tokens = 35
            mock_response.model = "gpt-4"
            
            # Configure the mock client's method
            mock_openai_client.chat.completions.create.return_value = mock_response
            
            # Test the instrumented method
            response = wrapper._client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=100,
                temperature=0.7
            )
            
            # Verify response
            assert response == mock_response
            
            # Verify the original method was called
            mock_openai_client.chat.completions.create.assert_called_once()
            
            logger.info("✅ OpenAI wrapper integration with mocking passed")
    
    def test_anthropic_wrapper_with_mocking(self):
        """Test Anthropic wrapper with proper mocking."""
        logger.info("Testing Anthropic wrapper integration with mocking...")
        
        # Mock the Anthropic package
        mock_anthropic_module = Mock()
        mock_anthropic_client = Mock()
        mock_async_anthropic_client = Mock()
        
        mock_anthropic_module.Anthropic = Mock(return_value=mock_anthropic_client)
        mock_anthropic_module.AsyncAnthropic = Mock(return_value=mock_async_anthropic_client)
        
        with patch.dict('sys.modules', {'anthropic': mock_anthropic_module}):
            from amplitude.ai.anthropic import Anthropic, AsyncAnthropic
            
            mock_amplitude_client = Mock()
            config = AIConfig(cost_tracking=True)
            
            # Create wrapper
            wrapper = Anthropic(
                api_key="test-key",
                amplitude_client=mock_amplitude_client,
                ai_config=config,
                auto_start_session=False
            )
            
            # Verify basic properties
            assert wrapper.get_provider_name() == "anthropic"
            assert wrapper.amplitude_client == mock_amplitude_client
            
            # Mock a response
            mock_response = Mock()
            mock_response.content = [Mock()]
            mock_response.content[0].text = "I'm Claude, nice to meet you!"
            mock_response.usage = Mock()
            mock_response.usage.input_tokens = 12
            mock_response.usage.output_tokens = 25
            mock_response.model = "claude-3-sonnet-20240229"
            
            # Configure the mock client's method
            mock_anthropic_client.messages.create.return_value = mock_response
            
            # Test the instrumented method
            response = wrapper._client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                messages=[{"role": "user", "content": "Hello"}]
            )
            
            # Verify response
            assert response == mock_response
            
            # Verify the original method was called
            mock_anthropic_client.messages.create.assert_called_once()
            
            logger.info("✅ Anthropic wrapper integration with mocking passed")
    
    def test_google_wrapper_with_mocking(self):
        """Test Google wrapper with proper mocking."""
        logger.info("Testing Google wrapper integration with mocking...")
        
        # Mock the Google AI package
        mock_google_module = Mock()
        mock_genai_module = Mock()
        mock_model_class = Mock()
        mock_model_instance = Mock()
        
        mock_model_class.return_value = mock_model_instance
        mock_genai_module.configure = Mock()
        mock_google_module.generativeai = mock_genai_module
        
        with patch.dict('sys.modules', {
            'google': mock_google_module,
            'google.generativeai': mock_genai_module
        }):
            with patch('amplitude.ai.google.genai', mock_genai_module):
                with patch('amplitude.ai.google.GenerativeModel', mock_model_class):
                    from amplitude.ai.google import GoogleGenerativeAI
                    
                    mock_amplitude_client = Mock()
                    config = AIConfig()
                    
                    # Create wrapper
                    wrapper = GoogleGenerativeAI(
                        api_key="test-key",
                        model_name="gemini-pro",
                        amplitude_client=mock_amplitude_client,
                        ai_config=config,
                        auto_start_session=False
                    )
                    
                    # Verify basic properties
                    assert wrapper.get_provider_name() == "google"
                    assert wrapper.model_name == "gemini-pro"
                    
                    # Mock a response
                    mock_response = Mock()
                    mock_response.text = "I'm Gemini, Google's AI assistant."
                    mock_response.usage_metadata = Mock()
                    mock_response.usage_metadata.prompt_token_count = 10
                    mock_response.usage_metadata.candidates_token_count = 15
                    
                    # Configure the mock model's method
                    mock_model_instance.generate_content.return_value = mock_response
                    
                    # Test the method
                    response = wrapper._model.generate_content("Hello")
                    
                    # Verify response
                    assert response == mock_response
                    
                    logger.info("✅ Google wrapper integration with mocking passed")
    
    def test_session_management_integration(self):
        """Test session management across multiple calls."""
        logger.info("Testing session management integration...")
        
        # Mock OpenAI for this test
        mock_openai_module = Mock()
        mock_openai_client = Mock()
        mock_openai_module.OpenAI = Mock(return_value=mock_openai_client)
        
        with patch.dict('sys.modules', {'openai': mock_openai_module}):
            from amplitude.ai.openai import OpenAI
            
            mock_amplitude_client = Mock()
            config = AIConfig()
            
            # Create wrapper with session tracking
            wrapper = OpenAI(
                api_key="test-key",
                amplitude_client=mock_amplitude_client,
                ai_config=config,
                auto_start_session=True  # Enable automatic session tracking
            )
            
            # Verify session manager was created
            assert wrapper.session_manager is not None
            assert wrapper.session_manager.amplitude_client == mock_amplitude_client
            
            # Mock responses for multiple calls
            responses = []
            for i in range(3):
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message.content = f"Response {i+1}"
                mock_response.usage = Mock()
                mock_response.usage.prompt_tokens = 10 + i
                mock_response.usage.completion_tokens = 15 + i
                mock_response.usage.total_tokens = 25 + (i*2)
                mock_response.model = "gpt-4"
                responses.append(mock_response)
            
            # Configure the mock to return different responses
            mock_openai_client.chat.completions.create.side_effect = responses
            
            # Make multiple calls
            for i in range(3):
                response = wrapper._client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": f"Message {i+1}"}]
                )
                assert response == responses[i]
            
            # Verify session stats were updated
            session_stats = wrapper.session_manager.session_stats
            assert session_stats["total_messages"] == 3
            assert session_stats["total_tokens"] > 0
            assert session_stats["total_cost_usd"] > 0
            
            logger.info(f"Session stats after 3 calls: {session_stats}")
            logger.info("✅ Session management integration passed")
    
    def test_privacy_controls_integration(self):
        """Test privacy controls in real usage scenarios.""" 
        logger.info("Testing privacy controls integration...")
        
        # Test with privacy mode enabled
        config_private = AIConfig(
            privacy_mode=True,
            cost_tracking=True
        )
        
        # Test content exclusion
        assert config_private.should_exclude_content("input") is True
        assert config_private.should_exclude_content("output") is True
        assert config_private.should_exclude_content("tool_parameters") is True
        
        # Test with specific exclusions
        config_selective = AIConfig(
            privacy_mode=False,
            exclude_input=True,
            exclude_output=False,
            exclude_tool_parameters=True,
            cost_tracking=True
        )
        
        assert config_selective.should_exclude_content("input") is True
        assert config_selective.should_exclude_content("output") is False
        assert config_selective.should_exclude_content("tool_parameters") is True
        
        # Test content truncation
        long_content = "This is a very long piece of content that exceeds the maximum length limit and should be truncated to ensure privacy and performance."
        
        config_truncate = AIConfig(max_content_length=50)
        truncated = config_truncate.truncate_content(long_content)
        
        assert len(truncated) <= 53  # 50 + "..."
        assert truncated.endswith("...")
        
        logger.info(f"Original content length: {len(long_content)}")
        logger.info(f"Truncated content length: {len(truncated)}")
        logger.info("✅ Privacy controls integration passed")
    
    def test_cost_calculation_accuracy(self):
        """Test cost calculation accuracy across different models and providers."""
        logger.info("Testing cost calculation accuracy...")
        
        config = AIConfig(cost_tracking=True)
        
        # Test cases: (provider, model, input_tokens, output_tokens, expected_cost)
        test_cases = [
            # OpenAI models
            ("openai", "gpt-4", 1000, 500, 0.06),  # $30/1M input + $30/1M output
            ("openai", "gpt-4o-mini", 10000, 5000, 0.0045),  # Cheaper model
            ("openai", "gpt-3.5-turbo", 2000, 1000, 0.0025),  # Budget model
            
            # Anthropic models  
            ("anthropic", "claude-3-sonnet-20240229", 1000, 1000, 0.018),  # $3/1M + $15/1M
            ("anthropic", "claude-3-haiku-20240307", 4000, 2000, 0.0035),  # Cheaper Claude
            ("anthropic", "claude-3-opus-20240229", 1000, 1000, 0.09),  # Premium Claude
            
            # Google models
            ("google", "gemini-pro", 2000, 1000, 0.0025),  # $0.5/1M + $1.5/1M  
            ("google", "gemini-1.5-flash", 10000, 5000, 0.00225),  # Fast model
            ("google", "gemini-1.5-pro", 1000, 1000, 0.014),  # Pro model
        ]
        
        for provider, model, input_tokens, output_tokens, expected_cost in test_cases:
            calculated_cost = config.calculate_cost(provider, model, input_tokens, output_tokens)
            
            assert calculated_cost is not None, f"Cost calculation failed for {provider}/{model}"
            
            # Allow small floating point differences
            assert abs(calculated_cost - expected_cost) < 0.0001, \
                f"Cost mismatch for {provider}/{model}: expected {expected_cost}, got {calculated_cost}"
            
            logger.info(f"✅ {provider}/{model}: {input_tokens}+{output_tokens} tokens = ${calculated_cost:.6f}")
        
        # Test cost tracking disabled
        config_no_cost = AIConfig(cost_tracking=False)
        no_cost_result = config_no_cost.calculate_cost("openai", "gpt-4", 1000, 500)
        assert no_cost_result is None
        
        # Test unknown models
        unknown_cost = config.calculate_cost("unknown_provider", "unknown_model", 1000, 500)
        assert unknown_cost is None
        
        logger.info("✅ Cost calculation accuracy passed")
    
    def test_event_emission_flow(self):
        """Test the complete event emission flow."""
        logger.info("Testing event emission flow...")
        
        from amplitude.ai.instrumentation import EventEmitter
        from amplitude.ai.events import LLMMessageEvent, LLMRunStartedEvent
        
        mock_amplitude_client = Mock()
        config = AIConfig(async_event_emission=False)  # Synchronous for testing
        
        emitter = EventEmitter(mock_amplitude_client, config)
        
        # Test emitting different types of events
        events = [
            LLMRunStartedEvent(
                session_id="test-session",
                model_provider="openai",
                model_name="gpt-4"
            ),
            LLMMessageEvent(
                session_id="test-session",
                model_provider="openai",
                model_name="gpt-4",
                input_tokens=50,
                output_tokens=75,
                total_tokens=125,
                latency_ms=1500,
                cost_usd=0.0075
            )
        ]
        
        for event in events:
            emitter.emit_event(event)
        
        # Verify all events were emitted
        assert mock_amplitude_client.track.call_count == len(events)
        
        # Verify event details
        calls = mock_amplitude_client.track.call_args_list
        start_event = calls[0][0][0]
        message_event = calls[1][0][0]
        
        assert start_event.event_type == "llm_run_started"
        assert start_event.event_properties["model_provider"] == "openai"
        
        assert message_event.event_type == "llm_message"
        assert message_event.event_properties["total_tokens"] == 125
        assert message_event.event_properties["cost_usd"] == 0.0075
        
        logger.info("✅ Event emission flow passed")


def run_mocked_integration_tests():
    """Run all mocked integration tests with detailed logging."""
    logger.info("🧪 Starting mocked AI observability integration tests...")
    logger.info("=" * 70)
    
    test_instance = TestProviderWrapperIntegration()
    test_methods = [method for method in dir(test_instance) if method.startswith('test_')]
    
    total_tests = 0
    passed_tests = 0
    
    for test_method_name in test_methods:
        total_tests += 1
        try:
            test_method = getattr(test_instance, test_method_name)
            test_method()
            passed_tests += 1
            logger.info(f"  ✅ {test_method_name} PASSED")
            
        except Exception as e:
            logger.error(f"  ❌ {test_method_name} FAILED: {e}")
            import traceback
            traceback.print_exc()
    
    logger.info("\n" + "=" * 70)
    logger.info(f"🎯 Mocked Integration Test Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        logger.info("🎉 ALL MOCKED INTEGRATION TESTS PASSED! Provider wrapper logic working correctly.")
    else:
        logger.warning(f"⚠️ {total_tests - passed_tests} tests failed. Please review failures above.")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    success = run_mocked_integration_tests()
    exit(0 if success else 1)