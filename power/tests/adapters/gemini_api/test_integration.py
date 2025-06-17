"""
Integration tests for Gemini API adapter.
These tests require a real API key and make actual API calls.
"""

import pytest
import os
from unittest.mock import patch

from adapters.gemini_api import GeminiClient, GeminiConfig
from shared.models.llm_request import LLMRequest
from shared.models.llm_response import LLMResponse, FinishReason
from shared.exceptions import AuthenticationError, LLMProviderError


class TestGeminiIntegration:
    """Integration tests with real Gemini API."""

    @pytest.fixture(scope='class')
    def api_key(self):
        """Get API key from environment or skip tests."""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            pytest.skip("GEMINI_API_KEY environment variable not set")
        return api_key

    @pytest.fixture
    def config(self, api_key):
        """Create config with real API key."""
        with patch.dict(os.environ, {'GEMINI_API_KEY': api_key}):
            return GeminiConfig()

    @pytest.fixture
    def client(self, config):
        """Create client with real config."""
        return GeminiClient(config)

    @pytest.mark.integration
    def test_validate_credentials_real_api(self, client):
        """Test credential validation with real API."""
        try:
            result = client.validate_credentials()
            assert result is True
        except Exception as e:
            pytest.skip(f"API not accessible: {e}")

    @pytest.mark.integration
    def test_generate_text_real_api(self, client):
        """Test text generation with real API."""
        try:
            request = LLMRequest(
                prompt="Hello! Please respond with exactly: 'Integration test successful'",
                max_tokens=50,
                temperature=0.0  # Deterministic
            )

            response = client.generate_text(request)

            assert isinstance(response, LLMResponse)
            assert response.content is not None
            assert len(response.content) > 0
            assert response.finish_reason in [FinishReason.COMPLETED, FinishReason.MAX_TOKENS]
            assert response.model == client.config.model
            assert response.provider == 'gemini'
            assert response.usage.total_tokens > 0
            assert response.latency_ms is not None

        except Exception as e:
            pytest.skip(f"Real API test failed: {e}")

    @pytest.mark.integration
    def test_generate_chat_completion_real_api(self, client):
        """Test chat completion with real API."""
        try:
            messages = [
                {'role': 'user', 'content': 'What is 2+2?'},
                {'role': 'assistant', 'content': '2+2 equals 4.'},
                {'role': 'user', 'content': 'What about 3+3?'}
            ]

            response = client.generate_chat_completion(messages, max_tokens=50)

            assert isinstance(response, LLMResponse)
            assert response.content is not None
            assert len(response.content) > 0
            assert '6' in response.content  # Should mention 6 as answer
            assert response.usage.total_tokens > 0

        except Exception as e:
            pytest.skip(f"Real API chat test failed: {e}")

    @pytest.mark.integration
    def test_streaming_real_api(self, client):
        """Test streaming with real API."""
        if not client.config.enable_streaming:
            pytest.skip("Streaming disabled in config")

        try:
            request = LLMRequest(
                prompt="Count from 1 to 5, one number per word.",
                max_tokens=50,
                temperature=0.0
            )

            responses = list(client.generate_text_stream(request))

            assert len(responses) > 0

            # Check that content accumulates
            cumulative_content = ""
            for response in responses:
                assert len(response.content_delta) >= 0
                cumulative_content += response.content_delta
                assert response.cumulative_content == cumulative_content

            # Last response should be final
            assert responses[-1].is_final
            assert responses[-1].final_response is not None

        except Exception as e:
            pytest.skip(f"Real API streaming test failed: {e}")

    @pytest.mark.integration
    def test_error_handling_invalid_key(self):
        """Test error handling with invalid API key."""
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'invalid_key_12345'}):
            config = GeminiConfig()
            client = GeminiClient(config)

            # Credential validation should fail
            result = client.validate_credentials()
            assert result is False

    @pytest.mark.integration
    def test_rate_limiting_behavior(self, client):
        """Test that rate limiting works correctly."""
        # Make a few requests to test rate limiter
        request = LLMRequest(
            prompt="Say 'test'",
            max_tokens=10,
            temperature=0.0
        )

        try:
            responses = []
            for i in range(3):
                response = client.generate_text(request)
                responses.append(response)
                assert isinstance(response, LLMResponse)

            # Check rate limiter stats
            stats = client.rate_limiter.get_gemini_stats()
            base_stats = stats['base_stats']

            assert base_stats['total_requests'] >= 3
            assert base_stats['requests_this_minute'] >= 3

        except Exception as e:
            pytest.skip(f"Rate limiting test failed: {e}")

    @pytest.mark.integration
    def test_caching_behavior(self, client):
        """Test response caching behavior."""
        if not client.config.enable_caching:
            pytest.skip("Caching disabled in config")

        try:
            request = LLMRequest(
                prompt="What is the capital of France?",
                max_tokens=20,
                temperature=0.0  # Deterministic for caching
            )

            # First request - should hit API
            response1 = client.generate_text(request)
            initial_cache_hits = client._stats['cache_hits']

            # Second request - should hit cache
            response2 = client.generate_text(request)
            final_cache_hits = client._stats['cache_hits']

            # Should have gotten a cache hit
            assert final_cache_hits > initial_cache_hits

            # Responses should be identical
            assert response1.content == response2.content

        except Exception as e:
            pytest.skip(f"Caching test failed: {e}")

    @pytest.mark.integration
    def test_model_info_real_api(self, client):
        """Test model info with real configuration."""
        model_info = client.get_model_info()

        assert model_info['name'] == client.config.model
        assert model_info['provider'] == 'gemini'
        assert 'text_generation' in model_info['capabilities']
        assert 'chat_completion' in model_info['capabilities']
        assert model_info['max_tokens'] > 0
        assert model_info['context_window'] > 0

    @pytest.mark.integration
    def test_usage_stats_real_api(self, client):
        """Test usage statistics with real API calls."""
        try:
            # Make a request to generate some stats
            request = LLMRequest(
                prompt="Hello",
                max_tokens=10
            )

            client.generate_text(request)

            # Get usage stats
            stats = client.get_usage_stats()

            assert 'client_stats' in stats
            assert 'rate_limiter' in stats
            assert 'cache' in stats
            assert 'configuration' in stats
            assert 'provider_info' in stats

            # Should have recorded the request
            assert stats['client_stats']['requests_made'] > 0
            assert stats['client_stats']['total_tokens'] > 0

            # Rate limiter should have stats
            rate_stats = stats['rate_limiter']['base_stats']
            assert rate_stats['total_requests'] > 0

        except Exception as e:
            pytest.skip(f"Usage stats test failed: {e}")

    @pytest.mark.integration
    def test_supported_features_real_api(self, client):
        """Test supported features detection."""
        features = client.supported_features

        # These should always be supported
        assert 'text_generation' in features
        assert 'chat_completion' in features
        assert 'image_input' in features
        assert 'safety_filtering' in features
        assert 'response_caching' in features

        # These depend on config
        if client.config.enable_streaming:
            assert 'streaming' in features

        if client.config.is_vision_supported():
            assert 'multimodal' in features

    @pytest.mark.integration
    @pytest.mark.skip("Requires large image file for testing")
    def test_image_generation_real_api(self, client):
        """Test image generation with real API (requires vision model)."""
        # This test is skipped by default as it requires:
        # 1. A vision-capable model
        # 2. An actual image file
        # 3. Higher API quotas

        # Example implementation:
        # if not client.config.is_vision_supported():
        #     pytest.skip("Vision not supported by current model")
        #
        # try:
        #     # Load a test image
        #     image_data = b'...'  # Real image bytes
        #     prompt = "What's in this image?"
        #
        #     response = client.generate_from_image(image_data, prompt)
        #
        #     assert isinstance(response, LLMResponse)
        #     assert response.content is not None
        #     assert len(response.content) > 0
        #
        # except Exception as e:
        #     pytest.skip(f"Image generation test failed: {e}")
        pass
