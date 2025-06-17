#!/usr/bin/env python3
"""
Test script for Gemini API adapter integration.
Tests the complete three-layer architecture with real API calls.
"""

import os
import sys
import traceback
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Set environment variable for Gemini API
os.environ['GEMINI_API_KEY'] = 'AIzaSyD1G1bSOgQzXY0Az71o0D8QMzpPCLRsKCo'

def test_architecture_validation():
    """Test architecture validation works correctly."""
    print("🔍 Testing architecture validation...")

    try:
        from shared.utils.architecture_validator import validate_architecture

        # Validate the Gemini adapter files
        report = validate_architecture(
            project_root="/home/ikino/dev/power",
            file_path="/home/ikino/dev/power/adapters/gemini_api/client.py"
        )

        if report['summary']['total_errors'] == 0:
            print("✅ Architecture validation passed!")
            return True
        else:
            print(f"❌ Architecture validation failed: {report['summary']['total_errors']} errors")
            for result in report['results']:
                if result['errors']:
                    print(f"  - {result['file_path']}: {result['errors']}")
            return False

    except Exception as e:
        print(f"❌ Architecture validation error: {e}")
        traceback.print_exc()
        return False

def test_configuration():
    """Test Gemini configuration setup."""
    print("⚙️  Testing Gemini configuration...")

    try:
        from adapters.gemini_api.config import GeminiConfig

        config = GeminiConfig()
        print(f"✅ Configuration loaded successfully!")
        print(f"  - Model: {config.model}")
        print(f"  - API Key present: {bool(config.api_key)}")
        print(f"  - Rate limit: {config.rate_limit_per_minute}/min")
        print(f"  - Caching enabled: {config.enable_caching}")

        # Test validation
        errors = config.validate()
        if errors:
            print(f"❌ Configuration validation errors: {errors}")
            return False

        print("✅ Configuration validation passed!")
        return True

    except Exception as e:
        print(f"❌ Configuration error: {e}")
        traceback.print_exc()
        return False

def test_shared_interfaces():
    """Test shared interface compatibility."""
    print("🔌 Testing shared interface implementation...")

    try:
        from adapters.gemini_api.client import GeminiClient
        from shared.interfaces.llm_provider import LLMProvider, MultiModalLLMProvider, StreamingLLMProvider

        client = GeminiClient()

        # Check interface implementation
        if not isinstance(client, LLMProvider):
            print("❌ Client does not implement LLMProvider interface")
            return False

        if not isinstance(client, MultiModalLLMProvider):
            print("❌ Client does not implement MultiModalLLMProvider interface")
            return False

        if not isinstance(client, StreamingLLMProvider):
            print("❌ Client does not implement StreamingLLMProvider interface")
            return False

        # Check required methods exist
        required_methods = [
            'generate_text', 'generate_chat_completion', 'get_model_info',
            'validate_credentials', 'get_usage_stats', 'provider_name',
            'supported_features'
        ]

        for method in required_methods:
            if not hasattr(client, method):
                print(f"❌ Client missing required method: {method}")
                return False

        print("✅ Interface implementation verified!")
        print(f"  - Provider name: {client.provider_name}")
        print(f"  - Supported features: {client.supported_features}")

        return True

    except Exception as e:
        print(f"❌ Interface test error: {e}")
        traceback.print_exc()
        return False

def test_data_models():
    """Test shared data model usage."""
    print("📄 Testing shared data models...")

    try:
        from shared.models.llm_request import LLMRequest
        from shared.models.llm_response import LLMResponse, FinishReason, UsageStats

        # Create test request
        request = LLMRequest(
            prompt="Hello, world!",
            max_tokens=100,
            temperature=0.7
        )

        print("✅ LLMRequest created successfully!")
        print(f"  - Prompt: {request.prompt}")
        print(f"  - Max tokens: {request.max_tokens}")
        print(f"  - Temperature: {request.temperature}")

        # Test request validation
        request_dict = request.to_dict()
        restored_request = LLMRequest.from_dict(request_dict)

        if restored_request.prompt != request.prompt:
            print("❌ Request serialization/deserialization failed")
            return False

        print("✅ Data model serialization works!")
        return True

    except Exception as e:
        print(f"❌ Data model test error: {e}")
        traceback.print_exc()
        return False

def test_real_api_call():
    """Test actual Gemini API integration."""
    print("🌐 Testing real Gemini API call...")

    try:
        from adapters.gemini_api.client import GeminiClient
        from shared.models.llm_request import LLMRequest

        client = GeminiClient()

        # Test credentials validation
        print("🔑 Validating credentials...")
        if not client.validate_credentials():
            print("❌ Credential validation failed")
            return False

        print("✅ Credentials validated!")

        # Test simple text generation
        print("💬 Testing text generation...")
        request = LLMRequest(
            prompt="Say 'Hello from Gemini API!' and explain that you are a test.",
            max_tokens=50,
            temperature=0.1
        )

        response = client.generate_text(request)

        print("✅ API call successful!")
        print(f"  - Generated text: {response.content[:100]}...")
        print(f"  - Finish reason: {response.finish_reason}")
        print(f"  - Tokens used: {response.usage.total_tokens}")
        print(f"  - Provider: {response.provider}")
        print(f"  - Model: {response.model}")

        # Verify response structure
        if not response.content:
            print("❌ Empty response content")
            return False

        if response.provider != "gemini":
            print(f"❌ Wrong provider: {response.provider}")
            return False

        print("✅ Response validation passed!")
        return True

    except Exception as e:
        print(f"❌ API call error: {e}")
        traceback.print_exc()
        return False

def test_error_handling():
    """Test error handling and exception translation."""
    print("⚠️  Testing error handling...")

    try:
        from adapters.gemini_api.client import GeminiClient
        from shared.models.llm_request import LLMRequest
        from shared.exceptions import InvalidRequestError

        client = GeminiClient()

        # Test invalid request (empty prompt)
        try:
            invalid_request = LLMRequest(
                prompt="",  # Empty prompt should fail
                max_tokens=100
            )
            print("❌ Invalid request should have failed validation")
            return False
        except ValueError:
            print("✅ Invalid request properly rejected!")

        # Test request with invalid parameters
        try:
            invalid_request = LLMRequest(
                prompt="Test",
                max_tokens=-1  # Negative tokens should fail
            )
            print("❌ Invalid max_tokens should have failed validation")
            return False
        except ValueError:
            print("✅ Invalid parameters properly rejected!")

        return True

    except Exception as e:
        print(f"❌ Error handling test error: {e}")
        traceback.print_exc()
        return False

def test_rate_limiting():
    """Test rate limiting functionality."""
    print("🚦 Testing rate limiting...")

    try:
        from adapters.gemini_api.rate_limiter import GeminiRateLimiter
        from adapters.gemini_api.config import GeminiConfig

        config = GeminiConfig()
        rate_limiter = GeminiRateLimiter(config)

        # Test rate limit checking
        can_call = rate_limiter.can_make_request()
        print(f"✅ Rate limiter initialized! Can make request: {can_call}")

        # Test quota checking if implemented
        if hasattr(rate_limiter, 'check_quota'):
            quota_ok = rate_limiter.check_quota()
            print(f"✅ Quota check: {quota_ok}")

        return True

    except Exception as e:
        print(f"❌ Rate limiting test error: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🚀 Starting Gemini API Adapter Integration Tests")
    print("=" * 60)

    tests = [
        ("Architecture Validation", test_architecture_validation),
        ("Configuration", test_configuration),
        ("Shared Interfaces", test_shared_interfaces),
        ("Data Models", test_data_models),
        ("Real API Call", test_real_api_call),
        ("Error Handling", test_error_handling),
        ("Rate Limiting", test_rate_limiting),
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
    print(f"🏁 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED! Gemini adapter is working correctly.")
        print("✅ Three-layer architecture validated!")
        print("✅ Standards enforcement working!")
        print("✅ Real API integration successful!")
        return True
    else:
        print(f"❌ {total - passed} tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
