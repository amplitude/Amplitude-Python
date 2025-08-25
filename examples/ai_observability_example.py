"""Example usage of Amplitude AI observability features.

This example demonstrates how to use the Amplitude Python SDK's AI observability
features with automatic instrumentation and manual event tracking.
"""

import asyncio
import time
from amplitude import Amplitude
from amplitude.ai import (
    AIConfig,
    llm_session,
    quick_track_message,
    LLMSessionTracker,
    MessageTimer,
    AIObservabilityPlugin,
    AIEventFilterPlugin
)

# Mock API keys - replace with real ones
AMPLITUDE_API_KEY = "your-amplitude-api-key"
OPENAI_API_KEY = "your-openai-api-key"  
ANTHROPIC_API_KEY = "your-anthropic-api-key"


def main():
    """Main example function."""
    print("Amplitude AI Observability Examples")
    print("=" * 40)
    
    # Initialize Amplitude client
    amplitude_client = Amplitude(AMPLITUDE_API_KEY)
    
    # Add AI plugins for enhanced functionality
    ai_config = AIConfig(
        privacy_mode=False,  # Set to True to exclude sensitive content
        cost_tracking=True,
        max_content_length=500
    )
    
    # Add plugins to the client
    amplitude_client.add(AIObservabilityPlugin(ai_config))
    amplitude_client.add(AIEventFilterPlugin(min_cost_threshold=0.001))  # Only track calls > $0.001
    
    print("\n1. Automatic OpenAI Instrumentation")
    automatic_openai_example(amplitude_client, ai_config)
    
    print("\n2. Manual Event Tracking")
    manual_tracking_example(amplitude_client, ai_config)
    
    print("\n3. Session Context Manager")
    session_context_example(amplitude_client, ai_config)
    
    print("\n4. LangChain Integration")
    langchain_example(amplitude_client, ai_config)
    
    # Flush events before exit
    amplitude_client.flush()
    print("\n✅ All examples completed!")


def automatic_openai_example(amplitude_client, ai_config):
    """Example of automatic OpenAI instrumentation."""
    try:
        from amplitude.ai import get_openai
        OpenAI, AsyncOpenAI = get_openai()
        
        # Create instrumented OpenAI client
        client = OpenAI(
            api_key=OPENAI_API_KEY,
            amplitude_client=amplitude_client,
            ai_config=ai_config
        )
        
        print("   📝 Making OpenAI call with automatic tracking...")
        
        # This call will be automatically tracked
        # Note: This would make a real API call - commented out for example
        """
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "What is the capital of France?"}
            ],
            max_tokens=50,
            temperature=0.7,
            amplitude_user_id="example_user",  # Optional Amplitude parameters
            amplitude_session_id="example_session"
        )
        print(f"   ✅ Response: {response.choices[0].message.content}")
        """
        print("   ✅ OpenAI instrumentation configured (API call commented out)")
        
    except ImportError:
        print("   ⚠️  OpenAI not installed - skipping automatic instrumentation example")


def manual_tracking_example(amplitude_client, ai_config):
    """Example of manual event tracking."""
    print("   📝 Tracking events manually...")
    
    # Quick way to track a single message
    quick_track_message(
        amplitude_client=amplitude_client,
        model_provider="openai",
        model_name="gpt-4",
        input_content="What is machine learning?",
        output_content="Machine learning is a subset of artificial intelligence...",
        input_tokens=20,
        output_tokens=150,
        latency_ms=2500,
        user_id="example_user"
    )
    
    # More detailed tracking with session tracker
    tracker = LLMSessionTracker(
        amplitude_client=amplitude_client,
        ai_config=ai_config,
        user_id="example_user",
        model_provider="anthropic",
        model_name="claude-3-sonnet"
    )
    
    # Start session
    session_id = tracker.start_session()
    
    # Track user message
    tracker.track_user_message(
        content="Explain quantum computing",
        message_type="text"
    )
    
    # Simulate API call with timing
    timer = MessageTimer()
    timer.start()
    time.sleep(0.1)  # Simulate API call
    latency_ms = timer.stop()
    
    # Track LLM response
    tracker.track_message(
        input_tokens=25,
        output_tokens=200,
        latency_ms=latency_ms,
        output_content="Quantum computing uses quantum mechanics principles...",
        temperature=0.8,
        finish_reason="stop"
    )
    
    # Track tool call
    tracker.track_tool_call(
        tool_name="web_search",
        tool_parameters={"query": "quantum computing applications"},
        tool_result={"results": ["IBM Quantum", "Google Quantum AI"]},
        execution_time_ms=500,
        success=True
    )
    
    # Finish session
    tracker.finish_session()
    
    print(f"   ✅ Tracked session: {session_id}")


def session_context_example(amplitude_client, ai_config):
    """Example using session context manager."""
    print("   📝 Using session context manager...")
    
    try:
        with llm_session(
            amplitude_client=amplitude_client,
            ai_config=ai_config,
            user_id="example_user",
            model_provider="google",
            model_name="gemini-pro"
        ) as session:
            
            # Track user message
            session.track_user_message("Write a haiku about AI")
            
            # Simulate processing time
            time.sleep(0.05)
            
            # Track response
            session.track_message(
                input_tokens=15,
                output_tokens=30,
                latency_ms=1200,
                output_content="Silicon minds think\nPatterns in data flowing\nFuture unfolds here",
                finish_reason="stop"
            )
            
        print("   ✅ Session completed automatically")
        
    except Exception as e:
        print(f"   ❌ Session failed: {e}")


def langchain_example(amplitude_client, ai_config):
    """Example of LangChain integration."""
    print("   📝 LangChain callback example...")
    
    try:
        from amplitude.ai import get_langchain
        AmplitudeLangChainCallback = get_langchain()
        
        # Create callback handler
        callback = AmplitudeLangChainCallback(
            amplitude_client=amplitude_client,
            ai_config=ai_config,
            user_id="example_user"
        )
        
        print("   ✅ LangChain callback configured")
        print("   💡 Use this callback in your LangChain chains:")
        print("      llm = ChatOpenAI(callbacks=[callback])")
        
    except ImportError:
        print("   ⚠️  LangChain not installed - skipping integration example")


async def async_example():
    """Example of async AI instrumentation."""
    try:
        from amplitude.ai import get_openai
        OpenAI, AsyncOpenAI = get_openai()
        
        amplitude_client = Amplitude(AMPLITUDE_API_KEY)
        
        # Create async client with instrumentation
        async_client = AsyncOpenAI(
            api_key=OPENAI_API_KEY,
            amplitude_client=amplitude_client
        )
        
        print("📝 Async OpenAI call example...")
        
        # This would make a real async API call - commented out for example
        """
        response = await async_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello!"}],
            max_tokens=10,
            amplitude_user_id="async_user"
        )
        print(f"✅ Async response: {response.choices[0].message.content}")
        """
        print("✅ Async instrumentation configured (API call commented out)")
        
    except ImportError:
        print("⚠️  OpenAI not installed - skipping async example")


if __name__ == "__main__":
    main()
    
    # Uncomment to run async example
    # asyncio.run(async_example())