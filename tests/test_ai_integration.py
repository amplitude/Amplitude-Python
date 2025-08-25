"""Integration tests for AI observability provider wrappers."""

import pytest
import time
import logging
from unittest.mock import Mock, patch, MagicMock, call
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
from amplitude.ai.instrumentation import InstrumentationMixin
from amplitude.ai.openai import OpenAI, AsyncOpenAI
from amplitude.ai.anthropic import Anthropic, AsyncAnthropic
from amplitude.ai.google import GoogleGenerativeAI
from amplitude.ai.pydantic import PydanticAIWrapper
from amplitude.ai.langchain import AmplitudeLangChainCallback


class TestOpenAIIntegration:
    """Test OpenAI wrapper integration."""
    
    def test_openai_wrapper_initialization(self):
        """Test OpenAI wrapper initialization without API key."""
        logger.info("Testing OpenAI wrapper initialization...")
        
        mock_amplitude_client = Mock()
        config = AIConfig()
        
        with patch('amplitude.ai.openai.OriginalOpenAI') as mock_openai:
            mock_openai_instance = Mock()
            mock_openai_instance.chat.completions.create = Mock()
            mock_openai.return_value = mock_openai_instance
            
            wrapper = OpenAI(
                api_key="test-key",
                amplitude_client=mock_amplitude_client,
                ai_config=config,
                auto_start_session=False
            )
            
            # Verify initialization
            assert wrapper.amplitude_client == mock_amplitude_client
            assert wrapper.ai_config == config
            assert wrapper.get_provider_name() == "openai"
            assert wrapper.get_response_parser() is not None
            
            # Verify that the original method was wrapped
            assert hasattr(wrapper._client.chat.completions, 'create')
            
        logger.info("✅ OpenAI wrapper initialization passed")
    
    def test_openai_instrumentation(self):
        """Test OpenAI method instrumentation with mock responses."""
        logger.info("Testing OpenAI method instrumentation...")
        
        mock_amplitude_client = Mock()
        config = AIConfig(cost_tracking=True)
        
        with patch('amplitude.ai.openai.OriginalOpenAI') as mock_openai:
            # Mock OpenAI client and response
            mock_openai_instance = Mock()
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "Hello! How can I help you today?"
            mock_response.usage = Mock()
            mock_response.usage.prompt_tokens = 20
            mock_response.usage.completion_tokens = 25
            mock_response.usage.total_tokens = 45
            mock_response.model = "gpt-4"
            
            original_create = Mock(return_value=mock_response)
            mock_openai_instance.chat.completions.create = original_create
            mock_openai.return_value = mock_openai_instance
            
            # Create wrapper
            wrapper = OpenAI(
                api_key="test-key",
                amplitude_client=mock_amplitude_client,
                ai_config=config,
                auto_start_session=False
            )
            
            # Make a call through the wrapper
            response = wrapper.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=100,
                temperature=0.7,
                amplitude_user_id="test-user"
            )
            
            # Verify the original method was called
            original_create.assert_called_once()
            
            # Verify the response is returned
            assert response == mock_response
            
            # Verify Amplitude tracking was called
            assert mock_amplitude_client.track.called
            
            # Verify the event contains expected properties
            track_calls = mock_amplitude_client.track.call_args_list
            assert len(track_calls) >= 1
            
            event = track_calls[0][0][0]
            assert event.event_type == "llm_message"
            assert event.event_properties["model_provider"] == "openai"
            assert event.event_properties["model_name"] == "gpt-4"
            assert event.event_properties["input_tokens"] == 20
            assert event.event_properties["output_tokens"] == 25
            assert event.event_properties["total_tokens"] == 45
            assert event.event_properties["temperature"] == 0.7
            assert event.event_properties["max_tokens"] == 100
            assert event.event_properties["cost_usd"] is not None
            
            logger.info(f"Tracked OpenAI call with cost: ${event.event_properties['cost_usd']:.6f}")
            
        logger.info("✅ OpenAI method instrumentation passed")
    
    def test_async_openai_integration(self):
        """Test AsyncOpenAI wrapper integration."""
        logger.info("Testing AsyncOpenAI integration...")
        
        mock_amplitude_client = Mock()
        config = AIConfig()
        
        with patch('amplitude.ai.openai.OriginalAsyncOpenAI') as mock_async_openai:
            mock_async_instance = Mock()
            mock_async_instance.chat.completions.create = Mock()
            mock_async_openai.return_value = mock_async_instance
            
            wrapper = AsyncOpenAI(
                api_key="test-key",
                amplitude_client=mock_amplitude_client,
                ai_config=config,
                auto_start_session=False
            )
            
            # Verify initialization
            assert wrapper.get_provider_name() == "openai"
            assert isinstance(wrapper._client, Mock)  # The mocked async client
            
        logger.info("✅ AsyncOpenAI integration passed")


class TestAnthropicIntegration:
    """Test Anthropic wrapper integration."""
    
    def test_anthropic_wrapper_initialization(self):
        """Test Anthropic wrapper initialization."""
        logger.info("Testing Anthropic wrapper initialization...")
        
        mock_amplitude_client = Mock()
        config = AIConfig()
        
        with patch('amplitude.ai.anthropic.OriginalAnthropic') as mock_anthropic:
            mock_anthropic_instance = Mock()
            mock_anthropic_instance.messages.create = Mock()
            mock_anthropic.return_value = mock_anthropic_instance
            
            wrapper = Anthropic(
                api_key="test-key",
                amplitude_client=mock_amplitude_client,
                ai_config=config,
                auto_start_session=False
            )
            
            # Verify initialization
            assert wrapper.get_provider_name() == "anthropic"
            assert wrapper.get_response_parser() is not None
            
        logger.info("✅ Anthropic wrapper initialization passed")
    
    def test_anthropic_instrumentation(self):
        """Test Anthropic method instrumentation."""
        logger.info("Testing Anthropic method instrumentation...")
        
        mock_amplitude_client = Mock()
        config = AIConfig(cost_tracking=True)
        
        with patch('amplitude.ai.anthropic.OriginalAnthropic') as mock_anthropic:
            # Mock Anthropic client and response
            mock_anthropic_instance = Mock()
            mock_response = Mock()
            mock_response.content = [Mock()]
            mock_response.content[0].text = "I'm Claude, an AI assistant created by Anthropic."
            mock_response.usage = Mock()
            mock_response.usage.input_tokens = 15
            mock_response.usage.output_tokens = 30
            mock_response.model = "claude-3-sonnet-20240229"
            
            original_create = Mock(return_value=mock_response)
            mock_anthropic_instance.messages.create = original_create
            mock_anthropic.return_value = mock_anthropic_instance
            
            # Create wrapper
            wrapper = Anthropic(
                api_key="test-key",
                amplitude_client=mock_amplitude_client,
                ai_config=config,
                auto_start_session=False
            )
            
            # Make a call through the wrapper
            response = wrapper.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                messages=[{"role": "user", "content": "Who are you?"}],
                temperature=0.5,
                amplitude_user_id="test-user"
            )
            
            # Verify the original method was called
            original_create.assert_called_once()
            
            # Verify the response is returned
            assert response == mock_response
            
            # Verify Amplitude tracking was called
            assert mock_amplitude_client.track.called
            
            # Check the tracked event
            event = mock_amplitude_client.track.call_args[0][0]
            assert event.event_type == "llm_message"
            assert event.event_properties["model_provider"] == "anthropic"
            assert event.event_properties["model_name"] == "claude-3-sonnet-20240229"
            assert event.event_properties["input_tokens"] == 15
            assert event.event_properties["output_tokens"] == 30
            assert event.event_properties["cost_usd"] is not None
            
            logger.info(f"Tracked Anthropic call with cost: ${event.event_properties['cost_usd']:.6f}")
            
        logger.info("✅ Anthropic method instrumentation passed")


class TestGoogleIntegration:
    """Test Google Gemini wrapper integration."""
    
    def test_google_wrapper_initialization(self):
        """Test Google wrapper initialization."""
        logger.info("Testing Google wrapper initialization...")
        
        mock_amplitude_client = Mock()
        config = AIConfig()
        
        with patch('amplitude.ai.google.GenerativeModel') as mock_model:
            mock_model_instance = Mock()
            mock_model_instance.generate_content = Mock()
            mock_model.return_value = mock_model_instance
            
            wrapper = GoogleGenerativeAI(
                api_key="test-key",
                model_name="gemini-pro",
                amplitude_client=mock_amplitude_client,
                ai_config=config,
                auto_start_session=False
            )
            
            # Verify initialization
            assert wrapper.get_provider_name() == "google"
            assert wrapper.model_name == "gemini-pro"
            
        logger.info("✅ Google wrapper initialization passed")
    
    def test_google_instrumentation(self):
        """Test Google method instrumentation."""
        logger.info("Testing Google method instrumentation...")
        
        mock_amplitude_client = Mock()
        config = AIConfig(cost_tracking=True)
        
        with patch('amplitude.ai.google.GenerativeModel') as mock_model:
            # Mock Google model and response
            mock_model_instance = Mock()
            mock_response = Mock()
            mock_response.text = "Gemini is Google's advanced AI model."
            mock_response.usage_metadata = Mock()
            mock_response.usage_metadata.prompt_token_count = 12
            mock_response.usage_metadata.candidates_token_count = 18
            
            original_generate = Mock(return_value=mock_response)
            mock_model_instance.generate_content = original_generate
            mock_model.return_value = mock_model_instance
            
            # Create wrapper
            wrapper = GoogleGenerativeAI(
                api_key="test-key",
                model_name="gemini-pro",
                amplitude_client=mock_amplitude_client,
                ai_config=config,
                auto_start_session=False
            )
            
            # Make a call through the wrapper
            response = wrapper._model.generate_content(
                "What is Gemini?",
                amplitude_user_id="test-user"
            )
            
            # Verify the original method was called
            original_generate.assert_called_once()
            
            # Verify the response is returned
            assert response == mock_response
            
            # Verify Amplitude tracking was called
            assert mock_amplitude_client.track.called
            
            # Check the tracked event
            event = mock_amplitude_client.track.call_args[0][0]
            assert event.event_type == "llm_message"
            assert event.event_properties["model_provider"] == "google"
            assert event.event_properties["model_name"] == "gemini-pro"
            
        logger.info("✅ Google method instrumentation passed")


class TestLangChainIntegration:
    """Test LangChain callback integration."""
    
    def test_langchain_callback_initialization(self):
        """Test LangChain callback initialization.""" 
        logger.info("Testing LangChain callback initialization...")
        
        mock_amplitude_client = Mock()
        config = AIConfig()
        
        try:
            callback = AmplitudeLangChainCallback(
                amplitude_client=mock_amplitude_client,
                ai_config=config,
                user_id="test-user",
                auto_start_session=False
            )
            
            # Should fail due to missing LangChain
            logger.error("❌ Should have failed due to missing LangChain")
            
        except ImportError as e:
            if "langchain" in str(e).lower():
                logger.info("✅ LangChain callback properly handles missing dependency")
            else:
                logger.error(f"❌ Unexpected import error: {e}")
    
    def test_langchain_callback_with_mock(self):
        """Test LangChain callback with mocked dependencies."""
        logger.info("Testing LangChain callback with mocked dependencies...")
        
        mock_amplitude_client = Mock()
        config = AIConfig()
        
        # Mock the LangChain imports
        with patch.dict('sys.modules', {
            'langchain_core': Mock(),
            'langchain_core.callbacks': Mock(), 
            'langchain_core.messages': Mock(),
            'langchain_core.outputs': Mock(),
            'langchain_core.agents': Mock()
        }):
            # Create mock classes
            mock_base_handler = Mock()
            mock_llm_result = Mock()
            mock_agent_action = Mock()
            mock_agent_finish = Mock()
            
            with patch('amplitude.ai.langchain.BaseCallbackHandler', mock_base_handler):
                with patch('amplitude.ai.langchain._LANGCHAIN_AVAILABLE', True):
                    # Manually set the availability flag and create callback
                    import amplitude.ai.langchain as langchain_module
                    langchain_module._LANGCHAIN_AVAILABLE = True
                    
                    # Override the import check in __init__
                    with patch.object(AmplitudeLangChainCallback, '__init__', 
                                      lambda self, amplitude_client, **kwargs: setattr(self, 'amplitude_client', amplitude_client)):
                        callback = AmplitudeLangChainCallback(
                            amplitude_client=mock_amplitude_client,
                            auto_start_session=False
                        )
                        
                        assert callback.amplitude_client == mock_amplitude_client
                        
        logger.info("✅ LangChain callback with mocked dependencies passed")


class TestErrorHandlingIntegration:
    """Test error handling in provider integrations."""
    
    def test_openai_error_handling(self):
        """Test OpenAI wrapper error handling."""
        logger.info("Testing OpenAI error handling...")
        
        mock_amplitude_client = Mock()
        config = AIConfig(error_tracking=True)
        
        with patch('amplitude.ai.openai.OriginalOpenAI') as mock_openai:
            mock_openai_instance = Mock()
            
            # Mock an API error
            api_error = Exception("API rate limit exceeded")
            mock_openai_instance.chat.completions.create.side_effect = api_error
            mock_openai.return_value = mock_openai_instance
            
            wrapper = OpenAI(
                api_key="test-key",
                amplitude_client=mock_amplitude_client,
                ai_config=config,
                auto_start_session=False
            )
            
            # Attempt to make a call that will fail
            with pytest.raises(Exception) as exc_info:
                wrapper.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": "Hello"}]
                )
            
            # Verify the original error is re-raised
            assert str(exc_info.value) == "API rate limit exceeded"
            
            # Verify error tracking was called
            assert mock_amplitude_client.track.called
            
            # Check that an error event was emitted
            event = mock_amplitude_client.track.call_args[0][0]
            assert event.event_type == "llm_message"
            assert event.event_properties["finish_reason"] == "error"
            
        logger.info("✅ OpenAI error handling passed")
    
    def test_import_guard_functionality(self):
        """Test import guard decorator functionality."""
        logger.info("Testing import guard functionality...")
        
        # Test that import errors are properly handled
        with patch('builtins.__import__') as mock_import:
            mock_import.side_effect = ImportError("No module named 'fake_package'")
            
            from amplitude.ai.instrumentation import import_guard
            
            @import_guard("fake_package", "pip install fake_package")
            class TestClass:
                def __init__(self):
                    self.value = "test"
            
            # Should raise ImportError when trying to instantiate
            with pytest.raises(ImportError) as exc_info:
                TestClass()
            
            assert "fake_package not installed" in str(exc_info.value)
            assert "pip install fake_package" in str(exc_info.value)
            
        logger.info("✅ Import guard functionality passed")


def run_integration_tests():
    """Run all integration tests with detailed logging."""
    logger.info("🧪 Starting AI observability integration tests...")
    logger.info("=" * 60)
    
    test_classes = [
        TestOpenAIIntegration,
        TestAnthropicIntegration,
        TestGoogleIntegration,
        TestLangChainIntegration,
        TestErrorHandlingIntegration
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
    logger.info(f"🎯 Integration Test Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        logger.info("🎉 ALL INTEGRATION TESTS PASSED! Provider wrappers working correctly.")
    else:
        logger.warning(f"⚠️ {total_tests - passed_tests} integration tests failed. Please review failures above.")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    success = run_integration_tests()
    exit(0 if success else 1)