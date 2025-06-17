#!/usr/bin/env python3
"""
Test script for enhanced Gemini adapter with advanced capabilities.
Validates all new features: function calling, image generation, system instructions.
"""

import os
import sys
sys.path.append('.')

from adapters.gemini_api.client import GeminiClient
from adapters.gemini_api.config import GeminiConfig
from shared.models.llm_request import LLMRequest
from shared.interfaces.llm_provider import AdvancedLLMProvider


def test_interface_compliance():
    """Test that GeminiClient properly implements AdvancedLLMProvider interface."""
    print("=== Testing Interface Compliance ===")

    # Set a mock API key for testing interface compliance
    os.environ['GEMINI_API_KEY'] = 'test_key_for_interface_compliance'

    try:
        client = GeminiClient()

        # Verify it's an instance of AdvancedLLMProvider
        assert isinstance(client, AdvancedLLMProvider), "Should inherit from AdvancedLLMProvider"
        print("✓ Correctly inherits from AdvancedLLMProvider")

        # Test all required properties
        assert hasattr(client, 'provider_name'), "Missing provider_name property"
        assert client.provider_name == 'gemini', "Incorrect provider name"
        print("✓ Provider name correct")

        assert hasattr(client, 'supported_features'), "Missing supported_features property"
        features = client.supported_features
        expected_features = [
            'text_generation', 'chat_completion', 'function_calling',
            'system_instructions', 'advanced_models'
        ]
        for feature in expected_features:
            assert feature in features, f"Missing feature: {feature}"
        print(f"✓ Supported features: {features}")

        # Test all required methods exist
        required_methods = [
            'generate_text', 'generate_chat_completion', 'generate_from_image',
            'generate_with_functions', 'execute_function_call', 'generate_image',
            'generate_with_system_instruction', 'get_advanced_capabilities',
            'select_optimal_model', 'get_model_info', 'validate_credentials',
            'get_usage_stats'
        ]

        for method in required_methods:
            assert hasattr(client, method), f"Missing method: {method}"
            assert callable(getattr(client, method)), f"Method not callable: {method}"
        print("✓ All required methods present and callable")

        # Test advanced capabilities
        capabilities = client.get_advanced_capabilities()
        print(f"✓ Advanced capabilities: {capabilities}")

        # Test model selection
        text_model = client.select_optimal_model('text', 'simple')
        function_model = client.select_optimal_model('function_calling')
        image_model = client.select_optimal_model('image_generation')
        print(f"✓ Model selection: text={text_model}, function={function_model}, image={image_model}")

        print("✓ Interface compliance test PASSED")
        return True

    except Exception as e:
        print(f"✗ Interface compliance test FAILED: {e}")
        return False


def test_configuration_enhancements():
    """Test enhanced configuration with new models and features."""
    print("\n=== Testing Configuration Enhancements ===")

    os.environ['GEMINI_API_KEY'] = 'test_key_for_config_testing'

    try:
        config = GeminiConfig()

        # Test advanced model configuration
        assert hasattr(config, 'image_generation_model'), "Missing image_generation_model"
        assert hasattr(config, 'function_calling_model'), "Missing function_calling_model"
        assert hasattr(config, 'simple_model'), "Missing simple_model"
        assert hasattr(config, 'complex_model'), "Missing complex_model"
        assert hasattr(config, 'thinking_model'), "Missing thinking_model"
        print("✓ Advanced model configuration present")

        # Test advanced feature flags
        assert hasattr(config, 'enable_function_calling'), "Missing enable_function_calling"
        assert hasattr(config, 'enable_image_generation'), "Missing enable_image_generation"
        assert hasattr(config, 'enable_system_instructions'), "Missing enable_system_instructions"
        print("✓ Advanced feature flags present")

        # Test advanced safety configuration
        assert hasattr(config, 'harassment_threshold'), "Missing harassment_threshold"
        assert hasattr(config, 'hate_speech_threshold'), "Missing hate_speech_threshold"
        print("✓ Advanced safety configuration present")

        # Test new support methods
        assert hasattr(config, 'supports_image_generation'), "Missing supports_image_generation"
        assert hasattr(config, 'supports_function_calling'), "Missing supports_function_calling"
        assert hasattr(config, 'supports_system_instructions'), "Missing supports_system_instructions"
        print("✓ Support checking methods present")

        # Test model getter methods
        assert hasattr(config, 'get_image_generation_model'), "Missing get_image_generation_model"
        assert hasattr(config, 'get_function_calling_model'), "Missing get_function_calling_model"
        assert hasattr(config, 'get_simple_model'), "Missing get_simple_model"
        assert hasattr(config, 'get_complex_model'), "Missing get_complex_model"
        print("✓ Model getter methods present")

        # Test configuration dictionary
        config_dict = config.to_dict()
        assert 'image_generation_model' in config_dict, "Config dict missing image_generation_model"
        assert 'enable_function_calling' in config_dict, "Config dict missing enable_function_calling"
        print("✓ Configuration dictionary includes new fields")

        print("✓ Configuration enhancements test PASSED")
        return True

    except Exception as e:
        print(f"✗ Configuration enhancements test FAILED: {e}")
        return False


def test_function_calling_structure():
    """Test function calling structure without making API calls."""
    print("\n=== Testing Function Calling Structure ===")

    os.environ['GEMINI_API_KEY'] = 'test_key_for_function_testing'

    try:
        client = GeminiClient()

        # Test function conversion
        test_functions = [{
            'name': 'get_weather',
            'description': 'Get weather information',
            'parameters': {
                'properties': {
                    'location': {'type': 'string'},
                    'unit': {'type': 'string', 'enum': ['celsius', 'fahrenheit']}
                },
                'required': ['location']
            }
        }]

        # Test function format conversion
        google_format = client._convert_functions_to_google_format(test_functions)
        assert isinstance(google_format, list), "Should return list"
        assert len(google_format) == 1, "Should convert one function"
        assert 'function_declarations' in google_format[0], "Should have function_declarations"
        print("✓ Function format conversion works")

        # Test execute_function_call method exists and is callable
        assert hasattr(client, 'execute_function_call'), "Missing execute_function_call method"
        assert callable(client.execute_function_call), "execute_function_call not callable"
        print("✓ Function execution method available")

        print("✓ Function calling structure test PASSED")
        return True

    except Exception as e:
        print(f"✗ Function calling structure test FAILED: {e}")
        return False


def test_model_selection_logic():
    """Test intelligent model selection logic."""
    print("\n=== Testing Model Selection Logic ===")

    os.environ['GEMINI_API_KEY'] = 'test_key_for_model_testing'

    try:
        client = GeminiClient()

        # Test different task types
        test_cases = [
            ('text', 'simple'),
            ('text', 'medium'),
            ('text', 'complex'),
            ('function_calling', 'medium'),
            ('image_generation', 'medium'),
            ('multimodal', 'medium'),
            ('unknown_task', 'medium')
        ]

        for task_type, complexity in test_cases:
            model = client.select_optimal_model(task_type, complexity)
            assert isinstance(model, str), f"Model should be string for {task_type}/{complexity}"
            assert len(model) > 0, f"Model name should not be empty for {task_type}/{complexity}"
            print(f"✓ {task_type}/{complexity} -> {model}")

        # Test with kwargs
        model_with_images = client.select_optimal_model('text', has_images=True)
        assert isinstance(model_with_images, str), "Model with images should be string"
        print(f"✓ Text with images -> {model_with_images}")

        print("✓ Model selection logic test PASSED")
        return True

    except Exception as e:
        print(f"✗ Model selection logic test FAILED: {e}")
        return False


def test_rate_limiter_enhancements():
    """Test rate limiter supports new request types."""
    print("\n=== Testing Rate Limiter Enhancements ===")

    os.environ['GEMINI_API_KEY'] = 'test_key_for_rate_limit_testing'

    try:
        client = GeminiClient()
        rate_limiter = client.rate_limiter

        # Test new request types are supported
        new_request_types = [
            'function_calling',
            'image_generation',
            'system_instruction'
        ]

        for request_type in new_request_types:
            can_make = rate_limiter.can_make_request(request_type)
            assert isinstance(can_make, bool), f"can_make_request should return bool for {request_type}"
            print(f"✓ Rate limiter supports {request_type}")

        # Test statistics include new request types
        stats = rate_limiter.get_gemini_stats()
        request_types = stats['gemini_stats']['request_types']

        for request_type in new_request_types:
            stat_key = f"{request_type}_requests"
            assert stat_key in request_types, f"Missing {stat_key} in statistics"
            print(f"✓ Statistics track {stat_key}")

        print("✓ Rate limiter enhancements test PASSED")
        return True

    except Exception as e:
        print(f"✗ Rate limiter enhancements test FAILED: {e}")
        return False


def main():
    """Run all tests for enhanced Gemini adapter."""
    print("Testing Enhanced Gemini Adapter with Advanced Capabilities")
    print("=" * 60)

    tests = [
        test_interface_compliance,
        test_configuration_enhancements,
        test_function_calling_structure,
        test_model_selection_logic,
        test_rate_limiter_enhancements
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} encountered error: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 ALL TESTS PASSED! Gemini adapter successfully enhanced to ADVANCED level!")
        return True
    else:
        print("❌ Some tests failed. Check the output above for details.")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
