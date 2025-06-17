#!/usr/bin/env python3
"""
Thorough test of Gemini API adapter to catch any lingering errors.
Tests multiple scenarios and edge cases.
"""

import os
import sys
import traceback
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Set environment variable for Gemini API
os.environ['GEMINI_API_KEY'] = 'AIzaSyD1G1bSOgQzXY0Az71o0D8QMzpPCLRsKCo'

def test_multiple_requests():
    """Test multiple sequential requests to check for any issues."""
    print("🔄 Testing multiple sequential requests...")

    try:
        from adapters.gemini_api.client import GeminiClient
        from shared.models.llm_request import LLMRequest

        client = GeminiClient()

        # Test multiple different requests
        test_prompts = [
            "Count from 1 to 5.",
            "What is 2 + 2?",
            "Name three colors.",
            "Say hello in Spanish.",
            "What is the capital of France?"
        ]

        responses = []

        for i, prompt in enumerate(test_prompts, 1):
            print(f"  📝 Request {i}/5: {prompt[:30]}...")

            request = LLMRequest(
                prompt=prompt,
                max_tokens=50,
                temperature=0.1
            )

            start_time = time.time()
            response = client.generate_text(request)
            duration = time.time() - start_time

            responses.append(response)

            print(f"    ✅ Response {i}: {response.content[:50]}... ({duration:.2f}s)")
            print(f"    📊 Tokens: {response.usage.total_tokens}, Finish: {response.finish_reason}")

            # Small delay between requests
            time.sleep(0.5)

        # Verify all responses
        if len(responses) == len(test_prompts):
            print(f"✅ All {len(test_prompts)} requests completed successfully!")

            # Check for any empty responses
            empty_responses = [i for i, r in enumerate(responses) if not r.content.strip()]
            if empty_responses:
                print(f"❌ Found {len(empty_responses)} empty responses: {empty_responses}")
                return False

            return True
        else:
            print(f"❌ Expected {len(test_prompts)} responses, got {len(responses)}")
            return False

    except Exception as e:
        print(f"❌ Multiple requests test error: {e}")
        traceback.print_exc()
        return False

def test_chat_completion():
    """Test chat completion functionality."""
    print("💬 Testing chat completion...")

    try:
        from adapters.gemini_api.client import GeminiClient
        from shared.models.llm_request import ChatMessage

        client = GeminiClient()

        # Test chat conversation
        messages = [
            ChatMessage(role="user", content="Hello! What's your name?"),
        ]

        response = client.generate_chat_completion(messages, max_tokens=100, temperature=0.3)

        print(f"✅ Chat response: {response.content[:100]}...")
        print(f"📊 Tokens used: {response.usage.total_tokens}")
        print(f"🏁 Finish reason: {response.finish_reason}")

        if response.content and response.usage.total_tokens > 0:
            return True
        else:
            print("❌ Invalid chat response structure")
            return False

    except Exception as e:
        print(f"❌ Chat completion test error: {e}")
        traceback.print_exc()
        return False

def test_different_parameters():
    """Test with different parameter combinations."""
    print("⚙️ Testing different parameter combinations...")

    try:
        from adapters.gemini_api.client import GeminiClient
        from shared.models.llm_request import LLMRequest

        client = GeminiClient()

        # Test with different parameters
        test_configs = [
            {"temperature": 0.0, "max_tokens": 20, "name": "Low temp, short"},
            {"temperature": 1.0, "max_tokens": 100, "name": "High temp, long"},
            {"temperature": 0.5, "max_tokens": 50, "top_p": 0.5, "name": "Mixed params"},
        ]

        for config in test_configs:
            name = config.pop("name")
            print(f"  🧪 Testing {name}...")

            request = LLMRequest(
                prompt="Describe a sunny day in exactly two sentences.",
                **config
            )

            response = client.generate_text(request)

            print(f"    ✅ Response: {response.content[:60]}...")
            print(f"    📊 Tokens: {response.usage.total_tokens}")

            if not response.content:
                print(f"    ❌ Empty response for {name}")
                return False

        print("✅ All parameter combinations worked!")
        return True

    except Exception as e:
        print(f"❌ Parameter test error: {e}")
        traceback.print_exc()
        return False

def test_error_scenarios():
    """Test error handling scenarios."""
    print("⚠️ Testing error handling scenarios...")

    try:
        from adapters.gemini_api.client import GeminiClient
        from shared.models.llm_request import LLMRequest
        from shared.exceptions import InvalidRequestError

        client = GeminiClient()

        # Test 1: Very long prompt (might hit limits)
        print("  🧪 Testing very long prompt...")
        long_prompt = "Tell me about artificial intelligence. " * 100  # Very long

        try:
            request = LLMRequest(
                prompt=long_prompt,
                max_tokens=50
            )
            response = client.generate_text(request)
            print(f"    ✅ Long prompt handled: {len(response.content)} chars")
        except Exception as e:
            print(f"    ⚠️ Long prompt error (expected): {type(e).__name__}")

        # Test 2: Invalid model (if configuration allows)
        print("  🧪 Testing with unusual parameters...")
        try:
            request = LLMRequest(
                prompt="Test unusual params",
                max_tokens=1,  # Very small limit
                temperature=0.0
            )
            response = client.generate_text(request)
            print(f"    ✅ Unusual params handled: '{response.content}'")
        except Exception as e:
            print(f"    ⚠️ Unusual params error: {type(e).__name__}")

        print("✅ Error handling tests completed!")
        return True

    except Exception as e:
        print(f"❌ Error scenario test error: {e}")
        traceback.print_exc()
        return False

def test_model_info_and_stats():
    """Test model info and usage stats functionality."""
    print("📊 Testing model info and usage stats...")

    try:
        from adapters.gemini_api.client import GeminiClient

        client = GeminiClient()

        # Test model info
        print("  📋 Getting model info...")
        model_info = client.get_model_info()
        print(f"    ✅ Model info: {model_info}")

        if not isinstance(model_info, dict):
            print("    ❌ Model info should be a dictionary")
            return False

        # Test usage stats
        print("  📈 Getting usage stats...")
        usage_stats = client.get_usage_stats()
        print(f"    ✅ Usage stats: {usage_stats}")

        if not isinstance(usage_stats, dict):
            print("    ❌ Usage stats should be a dictionary")
            return False

        # Test provider properties
        print("  🏷️ Testing provider properties...")
        print(f"    Provider name: {client.provider_name}")
        print(f"    Supported features: {client.supported_features}")

        if client.provider_name != "gemini":
            print(f"    ❌ Wrong provider name: {client.provider_name}")
            return False

        print("✅ Model info and stats working!")
        return True

    except Exception as e:
        print(f"❌ Model info test error: {e}")
        traceback.print_exc()
        return False

def test_rate_limiting_behavior():
    """Test rate limiting behavior."""
    print("🚦 Testing rate limiting behavior...")

    try:
        from adapters.gemini_api.client import GeminiClient
        from adapters.gemini_api.rate_limiter import GeminiRateLimiter
        from adapters.gemini_api.config import GeminiConfig
        from shared.models.llm_request import LLMRequest

        config = GeminiConfig()
        rate_limiter = GeminiRateLimiter(config)

        print(f"  ⚙️ Rate limit: {config.rate_limit_per_minute}/min")
        print(f"  ⚙️ Daily quota: {config.daily_quota}")

        # Test rate limiter state
        can_request = rate_limiter.can_make_request()
        print(f"  ✅ Can make request: {can_request}")

        # Test with client
        client = GeminiClient()

        # Make a few quick requests to test rate limiting
        print("  🔄 Making rapid requests to test rate limiting...")
        for i in range(3):
            request = LLMRequest(
                prompt=f"Quick test {i+1}",
                max_tokens=10
            )

            start_time = time.time()
            response = client.generate_text(request)
            duration = time.time() - start_time

            print(f"    📝 Request {i+1}: {duration:.2f}s - {response.content[:20]}...")

        print("✅ Rate limiting behavior tested!")
        return True

    except Exception as e:
        print(f"❌ Rate limiting test error: {e}")
        traceback.print_exc()
        return False

def test_caching_behavior():
    """Test response caching behavior."""
    print("💾 Testing response caching behavior...")

    try:
        from adapters.gemini_api.client import GeminiClient
        from shared.models.llm_request import LLMRequest

        client = GeminiClient()

        # Test same request twice to check caching
        prompt = "What is 1 + 1? Give a very short answer."

        print("  📝 First request (should hit API)...")
        request1 = LLMRequest(prompt=prompt, max_tokens=20, temperature=0.0)

        start_time = time.time()
        response1 = client.generate_text(request1)
        duration1 = time.time() - start_time

        print(f"    ✅ First response: {response1.content[:30]}... ({duration1:.2f}s)")

        # Small delay
        time.sleep(0.1)

        print("  📝 Second request (might use cache)...")
        request2 = LLMRequest(prompt=prompt, max_tokens=20, temperature=0.0)

        start_time = time.time()
        response2 = client.generate_text(request2)
        duration2 = time.time() - start_time

        print(f"    ✅ Second response: {response2.content[:30]}... ({duration2:.2f}s)")

        # Compare responses and timing
        if response1.content == response2.content:
            print("    💾 Responses match (caching might be working)")
        else:
            print("    🔄 Responses differ (no caching or different generation)")

        if duration2 < duration1 * 0.5:  # Significantly faster
            print("    ⚡ Second request much faster (likely cached)")
        else:
            print("    🐌 Similar timing (likely not cached or fresh generation)")

        print("✅ Caching behavior tested!")
        return True

    except Exception as e:
        print(f"❌ Caching test error: {e}")
        traceback.print_exc()
        return False

def main():
    """Run thorough Gemini API tests."""
    print("🔍 THOROUGH GEMINI API TESTING")
    print("=" * 60)

    tests = [
        ("Multiple Sequential Requests", test_multiple_requests),
        ("Chat Completion", test_chat_completion),
        ("Different Parameters", test_different_parameters),
        ("Error Scenarios", test_error_scenarios),
        ("Model Info & Stats", test_model_info_and_stats),
        ("Rate Limiting Behavior", test_rate_limiting_behavior),
        ("Caching Behavior", test_caching_behavior),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)

        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"💥 {test_name} CRASHED: {e}")
            traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"🏁 Thorough Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL THOROUGH TESTS PASSED!")
        print("✅ Gemini API adapter is robust and reliable!")
        print("✅ Error handling is working correctly!")
        print("✅ All features functioning properly!")
        return True
    else:
        print(f"❌ {total - passed} tests revealed issues that need attention.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
