#!/usr/bin/env python3
"""
Comprehensive example demonstrating manual AI observability tracking.

This example shows how to use Amplitude's AI observability features without 
automatic instrumentation - giving you full control over what gets tracked.

Run with: python examples/ai_manual_tracking_example.py
"""

import time
import logging
import sys
import os
from typing import Dict, Any, List

# Add src to path for example
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ai_observability_example.log')
    ]
)
logger = logging.getLogger(__name__)

from amplitude import Amplitude
from amplitude.ai import (
    AIConfig, 
    llm_session,
    quick_track_message,
    LLMSessionTracker,
    MessageTimer
)


def demonstrate_quick_tracking():
    """Demonstrate quick message tracking for simple use cases."""
    logger.info("🚀 Demonstrating quick message tracking...")
    
    # Initialize Amplitude client
    amplitude_client = Amplitude("demo-api-key-12345")
    
    # Quick way to track a single LLM interaction
    logger.info("📝 Tracking a quick OpenAI interaction...")
    quick_track_message(
        amplitude_client=amplitude_client,
        model_provider="openai",
        model_name="gpt-4",
        input_content="What are the benefits of renewable energy?",
        output_content="Renewable energy offers several key benefits: 1) Environmental protection...",
        input_tokens=45,
        output_tokens=150,
        latency_ms=2300,
        user_id="demo-user-001"
    )
    logger.info("✅ Quick message tracking completed")
    
    # Track another interaction with different provider
    logger.info("📝 Tracking an Anthropic Claude interaction...")
    quick_track_message(
        amplitude_client=amplitude_client,
        model_provider="anthropic",
        model_name="claude-3-sonnet-20240229",
        input_content="Explain machine learning in simple terms",
        output_content="Machine learning is like teaching computers to learn patterns from examples...",
        input_tokens=38,
        output_tokens=125,
        latency_ms=1800,
        user_id="demo-user-001"
    )
    logger.info("✅ Anthropic interaction tracking completed")


def demonstrate_session_context_manager():
    """Demonstrate session tracking using context manager."""
    logger.info("🔄 Demonstrating session context manager...")
    
    amplitude_client = Amplitude("demo-api-key-12345")
    
    # Configure AI observability settings
    ai_config = AIConfig(
        privacy_mode=False,  # Track full content for this demo
        cost_tracking=True,
        max_content_length=1000,
        async_event_emission=False  # Synchronous for demo visibility
    )
    
    # Use context manager for automatic session management
    logger.info("🎯 Starting LLM session with context manager...")
    try:
        with llm_session(
            amplitude_client=amplitude_client,
            ai_config=ai_config,
            user_id="demo-user-002",
            device_id="demo-device-001",
            model_provider="openai",
            model_name="gpt-4o"
        ) as session:
            logger.info(f"📊 Session started with ID: {session.session_id}")
            
            # Track user input
            logger.info("👤 User asks about AI applications...")
            session.track_user_message(
                content="What are some practical applications of AI in healthcare?",
                message_type="text"
            )
            
            # Simulate processing time and track response
            time.sleep(0.1)  # Simulate API call
            logger.info("🤖 AI responds with healthcare applications...")
            session.track_message(
                input_tokens=58,
                output_tokens=180,
                latency_ms=1400,
                output_content="""AI has numerous practical applications in healthcare:
                
1. **Medical Imaging**: AI can analyze X-rays, MRIs, and CT scans to detect anomalies
2. **Drug Discovery**: Accelerating the identification of new therapeutic compounds
3. **Personalized Treatment**: Tailoring treatments based on patient data and genetics
4. **Predictive Analytics**: Identifying patients at risk for certain conditions
5. **Virtual Health Assistants**: Providing 24/7 patient support and triage""",
                temperature=0.7,
                finish_reason="stop"
            )
            
            # Track a tool call
            logger.info("🔧 AI uses a tool to search for recent research...")
            tool_start_time = time.time()
            time.sleep(0.05)  # Simulate tool execution
            tool_duration = int((time.time() - tool_start_time) * 1000)
            
            session.track_tool_call(
                tool_name="medical_research_search",
                tool_parameters={
                    "query": "AI healthcare applications 2024",
                    "limit": 5,
                    "source": "pubmed"
                },
                tool_result={
                    "papers_found": 127,
                    "relevant_papers": [
                        "AI-powered diagnostic imaging improvements",
                        "Machine learning in drug discovery pipelines", 
                        "Personalized medicine through AI algorithms"
                    ]
                },
                execution_time_ms=tool_duration,
                success=True
            )
            
            # Follow up question
            logger.info("👤 User asks follow-up question...")
            session.track_user_message(
                content="Can you elaborate on AI in medical imaging?",
                message_type="text"
            )
            
            # Another AI response
            logger.info("🤖 AI provides detailed imaging explanation...")
            session.track_message(
                input_tokens=42,
                output_tokens=220,
                latency_ms=1800,
                output_content="""AI in medical imaging has revolutionized diagnostic accuracy:

**Computer Vision Applications:**
- Automated detection of tumors in radiological scans
- Retinal disease identification from fundus photographs
- Skin cancer screening from dermatological images

**Deep Learning Benefits:**
- Pattern recognition beyond human visual capabilities
- Consistent analysis reducing human error
- 24/7 availability for urgent cases

**Clinical Impact:**
- Earlier disease detection leading to better outcomes
- Reduced radiologist workload and faster turnaround
- Cost-effective screening for large populations""",
                temperature=0.7,
                finish_reason="stop"
            )
            
            logger.info(f"📈 Session stats: {session.session_stats}")
            
    except Exception as e:
        logger.error(f"❌ Session failed: {e}")
        raise
    
    logger.info("✅ Session context manager demonstration completed")


def demonstrate_detailed_session_tracking():
    """Demonstrate detailed session tracking with manual control."""
    logger.info("🎯 Demonstrating detailed session tracking...")
    
    amplitude_client = Amplitude("demo-api-key-12345")
    
    # Advanced configuration
    ai_config = AIConfig(
        privacy_mode=False,
        exclude_tool_parameters=False,  # Track tool usage details
        cost_tracking=True,
        latency_tracking=True,
        error_tracking=True,
        max_content_length=2000,
        async_event_emission=True  # Asynchronous event emission
    )
    
    # Create session tracker
    tracker = LLMSessionTracker(
        amplitude_client=amplitude_client,
        ai_config=ai_config,
        user_id="demo-user-003",
        device_id="demo-device-002",
        model_provider="anthropic",
        model_name="claude-3-5-sonnet-20241022"
    )
    
    # Start session manually
    session_id = tracker.start_session()
    logger.info(f"📊 Manual session started: {session_id}")
    
    try:
        # Simulate a coding assistance conversation
        conversation_steps = [
            {
                "user_input": "Help me optimize this Python function for performance",
                "ai_response": """I'd be happy to help optimize your Python function! To provide the best recommendations, could you please share the specific function you'd like to optimize? 

In the meantime, here are some general Python optimization strategies:

1. **Use built-in functions and libraries** (they're implemented in C)
2. **Leverage list comprehensions** instead of explicit loops when possible
3. **Consider NumPy** for numerical operations
4. **Profile your code** to identify actual bottlenecks
5. **Cache expensive computations** with functools.lru_cache

Please share your function and I'll give you specific optimization advice!""",
                "input_tokens": 52,
                "output_tokens": 145,
                "latency_ms": 1600
            },
            {
                "user_input": """def calculate_statistics(data):
    mean = sum(data) / len(data)
    variance = sum((x - mean) ** 2 for x in data) / len(data)
    std_dev = variance ** 0.5
    return mean, variance, std_dev""",
                "ai_response": """Great! I can help optimize this statistics function. Here's an improved version:

```python
import statistics
from typing import List, Tuple

def calculate_statistics(data: List[float]) -> Tuple[float, float, float]:
    if not data:
        raise ValueError("Data list cannot be empty")
    
    # Use built-in statistics module (faster and more accurate)
    mean = statistics.mean(data)
    variance = statistics.variance(data)
    std_dev = statistics.stdev(data)
    
    return mean, variance, std_dev

# Alternative: For very large datasets, use NumPy
def calculate_statistics_numpy(data: np.ndarray) -> Tuple[float, float, float]:
    mean = np.mean(data)
    variance = np.var(data, ddof=1)  # Sample variance
    std_dev = np.std(data, ddof=1)   # Sample standard deviation
    
    return mean, variance, std_dev
```

**Key optimizations:**
1. **Built-in functions**: `statistics` module is implemented in C
2. **Single pass**: Built-in functions are optimized internally
3. **Type hints**: Better code clarity and IDE support
4. **Error handling**: Prevents division by zero
5. **NumPy option**: For large datasets (1000+ elements)

This will be significantly faster, especially for large datasets!""",
                "input_tokens": 89,
                "output_tokens": 285,
                "latency_ms": 2400,
                "tools_used": [
                    {
                        "name": "code_analyzer",
                        "parameters": {"code": "def calculate_statistics(data)...", "language": "python"},
                        "result": {"complexity": "O(n)", "suggestions": ["Use built-in statistics", "Add type hints"]},
                        "duration_ms": 150
                    }
                ]
            },
            {
                "user_input": "Can you show me how to benchmark these two approaches?",
                "ai_response": """Absolutely! Here's how to benchmark both approaches:

```python
import time
import statistics
import numpy as np
from typing import List, Tuple
import random

# Your original function
def original_calculate_statistics(data):
    mean = sum(data) / len(data)
    variance = sum((x - mean) ** 2 for x in data) / len(data)
    std_dev = variance ** 0.5
    return mean, variance, std_dev

# Optimized version
def optimized_calculate_statistics(data: List[float]) -> Tuple[float, float, float]:
    mean = statistics.mean(data)
    variance = statistics.variance(data)
    std_dev = statistics.stdev(data)
    return mean, variance, std_dev

# NumPy version
def numpy_calculate_statistics(data: np.ndarray) -> Tuple[float, float, float]:
    mean = np.mean(data)
    variance = np.var(data, ddof=1)
    std_dev = np.std(data, ddof=1)
    return mean, variance, std_dev

# Benchmark function
def benchmark_functions():
    # Test with different data sizes
    sizes = [100, 1000, 10000, 100000]
    
    for size in sizes:
        # Generate random test data
        data = [random.uniform(0, 100) for _ in range(size)]
        data_np = np.array(data)
        
        print(f"\nBenchmarking with {size} data points:")
        
        # Time original function
        start = time.perf_counter()
        for _ in range(100):  # Run multiple times for accuracy
            original_calculate_statistics(data)
        original_time = time.perf_counter() - start
        
        # Time optimized function
        start = time.perf_counter()
        for _ in range(100):
            optimized_calculate_statistics(data)
        optimized_time = time.perf_counter() - start
        
        # Time NumPy function
        start = time.perf_counter()
        for _ in range(100):
            numpy_calculate_statistics(data_np)
        numpy_time = time.perf_counter() - start
        
        print(f"Original:  {original_time:.4f}s")
        print(f"Optimized: {optimized_time:.4f}s ({original_time/optimized_time:.1f}x faster)")
        print(f"NumPy:     {numpy_time:.4f}s ({original_time/numpy_time:.1f}x faster)")

if __name__ == "__main__":
    benchmark_functions()
```

**Expected Results:**
- For small datasets (< 1000): Built-in `statistics` will be fastest
- For large datasets (> 10000): NumPy will dominate
- The optimized version should be 2-5x faster than original

**Pro tip**: Use `timeit` module for even more precise benchmarking!""",
                "input_tokens": 67,
                "output_tokens": 425,
                "latency_ms": 3200,
                "tools_used": [
                    {
                        "name": "code_generator",
                        "parameters": {"task": "generate_benchmark_code", "language": "python"},
                        "result": {"code_length": 1847, "functions_generated": 4},
                        "duration_ms": 280
                    }
                ]
            }
        ]
        
        # Process each step in the conversation
        for i, step in enumerate(conversation_steps, 1):
            logger.info(f"💬 Processing conversation step {i}...")
            
            # Track user message
            timer = MessageTimer()
            with timer.time():
                tracker.track_user_message(
                    content=step["user_input"],
                    message_type="text"
                )
                
                # Simulate thinking time
                time.sleep(0.02)
                
                # Track AI response
                tracker.track_message(
                    input_tokens=step["input_tokens"],
                    output_tokens=step["output_tokens"], 
                    latency_ms=step["latency_ms"],
                    output_content=step["ai_response"],
                    temperature=0.3,  # Lower temp for coding tasks
                    finish_reason="stop"
                )
                
                # Track any tool usage
                if "tools_used" in step:
                    for tool in step["tools_used"]:
                        tracker.track_tool_call(
                            tool_name=tool["name"],
                            tool_parameters=tool["parameters"],
                            tool_result=tool["result"],
                            execution_time_ms=tool["duration_ms"],
                            success=True
                        )
            
            interaction_time = timer.duration_ms
            logger.info(f"📊 Step {i} completed in {interaction_time}ms")
            logger.info(f"💰 Session cost so far: ${tracker.session_stats['total_cost_usd']:.6f}")
            logger.info(f"🎯 Total tokens used: {tracker.session_stats['total_tokens']}")
            
        # Finish session
        tracker.finish_session(success=True)
        logger.info(f"🏁 Session completed successfully")
        logger.info(f"📊 Final session statistics:")
        logger.info(f"   - Total messages: {tracker.session_stats['total_messages']}")
        logger.info(f"   - Total tokens: {tracker.session_stats['total_tokens']}")
        logger.info(f"   - Total cost: ${tracker.session_stats['total_cost_usd']:.6f}")
        
    except Exception as e:
        logger.error(f"❌ Error during session: {e}")
        tracker.finish_session(success=False, error_message=str(e))
        raise
    
    logger.info("✅ Detailed session tracking demonstration completed")


def demonstrate_privacy_controls():
    """Demonstrate privacy control features."""
    logger.info("🔐 Demonstrating privacy controls...")
    
    amplitude_client = Amplitude("demo-api-key-12345")
    
    # Test different privacy settings
    privacy_configs = [
        ("Full tracking", AIConfig(privacy_mode=False)),
        ("Privacy mode", AIConfig(privacy_mode=True)),
        ("Selective privacy", AIConfig(
            privacy_mode=False,
            exclude_input=True,
            exclude_output=False,
            exclude_tool_parameters=True
        )),
        ("Content truncation", AIConfig(
            privacy_mode=False,
            max_content_length=100
        ))
    ]
    
    for config_name, config in privacy_configs:
        logger.info(f"🔒 Testing {config_name}...")
        
        # Test content exclusion
        input_excluded = config.should_exclude_content("input")
        output_excluded = config.should_exclude_content("output") 
        tool_params_excluded = config.should_exclude_content("tool_parameters")
        
        logger.info(f"   Input excluded: {input_excluded}")
        logger.info(f"   Output excluded: {output_excluded}")
        logger.info(f"   Tool params excluded: {tool_params_excluded}")
        
        # Test content truncation
        long_content = "This is a very long piece of content that would normally exceed the maximum content length limits set in the configuration and should be truncated appropriately to maintain privacy and performance standards while still preserving the essential meaning of the original text."
        truncated = config.truncate_content(long_content)
        
        logger.info(f"   Original length: {len(long_content)} chars")
        logger.info(f"   Truncated length: {len(truncated)} chars")
        
        if len(truncated) < len(long_content):
            logger.info(f"   Truncated content: {truncated[:50]}...")
        
        # Demo tracking with this privacy config
        quick_track_message(
            amplitude_client=amplitude_client,
            model_provider="openai", 
            model_name="gpt-4",
            input_content=long_content if not input_excluded else None,
            output_content="Here's a comprehensive response..." if not output_excluded else None,
            input_tokens=45,
            output_tokens=80,
            latency_ms=1200,
            user_id=f"privacy-demo-user-{config_name.replace(' ', '-')}"
        )
        
        logger.info(f"✅ {config_name} demonstration completed")
    
    logger.info("✅ Privacy controls demonstration completed")


def demonstrate_error_handling():
    """Demonstrate error handling and edge cases."""
    logger.info("⚠️ Demonstrating error handling...")
    
    amplitude_client = Amplitude("demo-api-key-12345")
    config = AIConfig(error_tracking=True)
    
    # Test session error handling
    tracker = LLMSessionTracker(
        amplitude_client=amplitude_client,
        ai_config=config,
        user_id="error-demo-user",
        model_provider="openai",
        model_name="gpt-4"
    )
    
    session_id = tracker.start_session()
    logger.info(f"📊 Error handling session: {session_id}")
    
    try:
        # Normal successful interaction
        logger.info("✅ Tracking successful interaction...")
        tracker.track_message(
            input_tokens=30,
            output_tokens=50,
            latency_ms=1200,
            output_content="This is a successful response.",
            finish_reason="stop"
        )
        
        # Simulate a failed tool call
        logger.info("❌ Simulating failed tool call...")
        tracker.track_tool_call(
            tool_name="web_search",
            tool_parameters={"query": "recent news"},
            tool_result=None,
            execution_time_ms=5000,
            success=False,
            error_message="Request timeout after 5000ms"
        )
        
        # Simulate a partial response (interrupted)
        logger.info("⚠️ Simulating interrupted response...")
        tracker.track_message(
            input_tokens=25,
            output_tokens=15,
            latency_ms=800,
            output_content="This response was cut off due to...",
            finish_reason="length"  # Hit token limit
        )
        
        # Test cost calculation edge cases
        logger.info("🔍 Testing cost calculation edge cases...")
        
        # Unknown model
        unknown_cost = config.calculate_cost("openai", "unknown-model", 1000, 500)
        logger.info(f"Unknown model cost: {unknown_cost}")
        
        # Zero tokens
        zero_cost = config.calculate_cost("openai", "gpt-4", 0, 0)
        logger.info(f"Zero tokens cost: {zero_cost}")
        
        # Very large token count
        large_cost = config.calculate_cost("openai", "gpt-4", 1_000_000, 500_000)
        logger.info(f"Large token count cost: ${large_cost:.2f}")
        
        # Finish session successfully despite errors
        tracker.finish_session(success=True)
        logger.info("✅ Session finished successfully despite errors")
        
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        tracker.finish_session(success=False, error_message=str(e))
    
    logger.info("✅ Error handling demonstration completed")


def main():
    """Run all demonstration functions."""
    logger.info("🎬 Starting comprehensive AI observability demonstration...")
    logger.info("=" * 80)
    
    demonstrations = [
        ("Quick Message Tracking", demonstrate_quick_tracking),
        ("Session Context Manager", demonstrate_session_context_manager), 
        ("Detailed Session Tracking", demonstrate_detailed_session_tracking),
        ("Privacy Controls", demonstrate_privacy_controls),
        ("Error Handling", demonstrate_error_handling)
    ]
    
    for demo_name, demo_func in demonstrations:
        try:
            logger.info(f"\n{'='*20} {demo_name} {'='*20}")
            demo_func()
            logger.info(f"🎉 {demo_name} completed successfully!")
            
        except Exception as e:
            logger.error(f"💥 {demo_name} failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Small pause between demonstrations
        time.sleep(0.5)
    
    logger.info("\n" + "=" * 80)
    logger.info("🏁 All demonstrations completed!")
    logger.info("📋 Summary of what was demonstrated:")
    logger.info("   ✅ Quick message tracking for simple use cases")
    logger.info("   ✅ Session management with context managers") 
    logger.info("   ✅ Detailed manual session tracking with full control")
    logger.info("   ✅ Privacy controls and content filtering")
    logger.info("   ✅ Error handling and edge case management")
    logger.info("\n📄 Check 'ai_observability_example.log' for detailed logs.")


if __name__ == "__main__":
    main()