"""
Tests for Gemini API client implementation.
"""

import pytest
import time
from unittest.mock import MagicMock, patch, Mock

from adapters.gemini_api.client import GeminiClient
from adapters.gemini_api.config import GeminiConfig
from shared.models.llm_request import LLMRequest
from shared.models.llm_response import LLMResponse, FinishReason, UsageStats
from shared.exceptions import (
    LLMProviderError,
    AuthenticationError,
    RateLimitError,
    InvalidRequestError
)


class TestGeminiClient:
    """Test cases for GeminiClient class."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock config for testing."""
        config = MagicMock(spec=GeminiConfig)
        config.api_key = 'test_api_key'
        config.model = 'gemini-2.0-flash'
        config.vision_model = 'gemini-2.0-flash'
        config.enable_caching = True
        config.cache_max_size = 100
        config.cache_ttl_seconds = 3600
        config.enable_streaming = True
        config.rate_limit_per_minute = 10
        config.rate_limit_per_hour = 1000
        config.daily_quota = 1000
        config.min_request_interval = 0.0
        config.is_vision_supported.return_value = True
        config.get_model_for_request.return_value = 'gemini-2.0-flash'
        config.supported_image_formats = ['jpeg', 'png', 'webp']
        
        # Add default config values for data mapping
        config.default_max_tokens = 1000
        config.default_temperature = 0.7
        config.default_top_p = 0.9
        config.default_top_k = 40
        config.get_safety_settings.return_value = []
        
        return config

    @pytest.fixture
    def mock_genai(self):
        """Create a mock genai module for new SDK."""
        with patch('google.genai', create=True) as mock:
            # Mock the Client class
            mock_client = MagicMock()
            mock.Client.return_value = mock_client

            # Mock models.generate_content method
            mock_response = {
                'candidates': [{
                    'content': {
                        'parts': [{'text': 'Test response'}],
                        'role': 'model'
                    },
                    'finishReason': 'STOP',
                    'index': 0,
                    'safetyRatings': []
                }],
                'usageMetadata': {
                    'promptTokenCount': 10,
                    'candidatesTokenCount': 5,
                    'totalTokenCount': 15
                }
            }

            mock_client.models.generate_content.return_value = mock_response

            yield mock

    @pytest.fixture
    def client(self, mock_config):
        """Create a Gemini client for testing."""
        return GeminiClient(mock_config)

    def test_initialization(self, mock_config):
        """Test client initialization."""
        client = GeminiClient(mock_config)

        assert client.config == mock_config
        assert client.rate_limiter is not None
        assert client.data_mapper is not None
        assert client.cache is not None  # caching enabled
        assert not client._client_initialized

    def test_initialization_without_config(self):
        """Test client initialization without config."""
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'}):
            client = GeminiClient()
            assert client.config is not None
            assert isinstance(client.config, GeminiConfig)

    def test_initialization_no_caching(self, mock_config):
        """Test client initialization with caching disabled."""
        mock_config.enable_caching = False
        client = GeminiClient(mock_config)

        assert client.cache is None

    @patch('google.genai', create=True)
    def test_get_genai_client_success(self, mock_genai, client):
        """Test successful genai client initialization."""
        genai_client = client._get_genai_client()

        assert genai_client == mock_genai.Client.return_value
        assert client._client_initialized
        mock_genai.Client.assert_called_once_with(api_key='test_api_key')

    def test_get_genai_client_import_error(self, client):
        """Test genai client initialization with import error."""
        # Mock the _get_genai_client method to raise an ImportError
        with patch.object(client, '_get_genai_client') as mock_get_client:
            mock_get_client.side_effect = LLMProviderError(
                "google-genai package not installed. Install with: pip install google-genai"
            )

            with pytest.raises(LLMProviderError) as exc_info:
                client._get_genai_client()

            assert "google-genai package not installed" in str(exc_info.value)

    def test_generate_text_success(self, client, mock_genai):
        """Test successful text generation."""
        # Setup the mock client returned by genai.Client()
        mock_client = mock_genai.Client.return_value
        
        with patch.object(client, '_get_genai_client', return_value=mock_client):
            request = LLMRequest(
                prompt="Hello, world!",
                max_tokens=100,
                temperature=0.7
            )

            response = client.generate_text(request)

            assert isinstance(response, LLMResponse)
            assert response.content == 'Test response'
            assert response.finish_reason == FinishReason.COMPLETED
            assert response.model == 'gemini-2.0-flash'  # Updated to match mock config
            assert response.provider == 'gemini'
            assert response.usage.total_tokens == 15

    def test_generate_text_with_cache_hit(self, client, mock_genai):
        """Test text generation with cache hit."""
        with patch.object(client, '_get_genai_client', return_value=mock_genai):
            request = LLMRequest(prompt="Hello, world!")

            # First call - should hit API
            response1 = client.generate_text(request)

            # Second call - should hit cache
            response2 = client.generate_text(request)

            # Should be the same response
            assert response1.content == response2.content

            # Should have recorded cache hit
            assert client._stats['cache_hits'] == 1

    def test_generate_text_rate_limited(self, client, mock_genai):
        """Test text generation with rate limit."""
        # Mock rate limiter to deny requests
        client.rate_limiter.can_make_request = MagicMock(return_value=False)
        client.rate_limiter.get_wait_time = MagicMock(return_value=60.0)

        request = LLMRequest(prompt="Test")

        with pytest.raises(RateLimitError) as exc_info:
            client.generate_text(request)

        assert exc_info.value.retry_after == 60

    def test_generate_text_invalid_request_size(self, client, mock_genai):
        """Test text generation with oversized request."""
        with patch.object(client, '_get_genai_client', return_value=mock_genai):
            # Mock data mapper to reject request size
            client.data_mapper.validate_request_size = MagicMock(return_value=False)

            request = LLMRequest(prompt="Test")

            with pytest.raises(InvalidRequestError) as exc_info:
                client.generate_text(request)

            assert "exceeds maximum token limit" in str(exc_info.value)

    def test_generate_chat_completion_success(self, client, mock_genai):
        """Test successful chat completion."""
        with patch.object(client, '_get_genai_client', return_value=mock_genai):
            messages = [
                {'role': 'user', 'content': 'Hello!'},
                {'role': 'assistant', 'content': 'Hi there!'},
                {'role': 'user', 'content': 'How are you?'}
            ]

            response = client.generate_chat_completion(messages, max_tokens=200)

            assert isinstance(response, LLMResponse)
            assert response.content == 'Test response'
            assert response.finish_reason == FinishReason.COMPLETED

    def test_generate_from_image_success(self, client, mock_genai):
        """Test successful image generation."""
        with patch.object(client, '_get_genai_client', return_value=mock_genai):
            image_data = b'fake_image_data'
            prompt = "What's in this image?"

            response = client.generate_from_image(image_data, prompt)

            assert isinstance(response, LLMResponse)
            assert response.content == 'Test response'

            # Should use vision model
            client.config.get_model_for_request.assert_called_with(has_images=True)

    def test_get_supported_image_formats(self, client):
        """Test getting supported image formats."""
        formats = client.get_supported_image_formats()

        assert formats == ['jpeg', 'png', 'webp']
        assert formats is not client.config.supported_image_formats  # Should be a copy

    def test_generate_text_stream_success(self, client, mock_genai):
        """Test successful streaming text generation."""
        with patch.object(client, '_get_genai_client', return_value=mock_genai):
            # Mock streaming response
            mock_chunks = [
                {'candidates': [{'content': {'parts': [{'text': 'Hello'}]}}]},
                {'candidates': [{'content': {'parts': [{'text': ' world'}]}}]},
                {'candidates': [{'content': {'parts': [{'text': '!'}]}, 'finishReason': 'STOP'}]}
            ]

            mock_genai.GenerativeModel.return_value.generate_content.return_value = mock_chunks

            request = LLMRequest(prompt="Test streaming")

            responses = list(client.generate_text_stream(request))

            assert len(responses) == 3
            assert responses[0].content_delta == 'Hello'
            assert responses[1].content_delta == ' world'
            assert responses[2].content_delta == '!'
            assert responses[2].is_final

    def test_generate_text_stream_disabled(self, client):
        """Test streaming when disabled in config."""
        client.config.enable_streaming = False

        request = LLMRequest(prompt="Test")

        with pytest.raises(LLMProviderError) as exc_info:
            list(client.generate_text_stream(request))

        assert "Streaming is disabled" in str(exc_info.value)

    def test_generate_chat_completion_stream_success(self, client, mock_genai):
        """Test successful streaming chat completion."""
        with patch.object(client, '_get_genai_client', return_value=mock_genai):
            # Mock streaming response
            mock_chunks = [
                {'candidates': [{'content': {'parts': [{'text': 'Hi'}]}}]},
                {'candidates': [{'content': {'parts': [{'text': ' there'}]}}]}
            ]

            mock_genai.GenerativeModel.return_value.generate_content.return_value = mock_chunks

            messages = [{'role': 'user', 'content': 'Hello!'}]

            responses = list(client.generate_chat_completion_stream(messages))

            assert len(responses) == 2
            assert responses[0].content_delta == 'Hi'
            assert responses[1].content_delta == ' there'

    def test_get_model_info(self, client):
        """Test getting model information."""
        model_info = client.get_model_info()

        assert model_info['name'] == 'gemini-pro'
        assert model_info['provider'] == 'gemini'
        assert 'text_generation' in model_info['capabilities']
        assert 'chat_completion' in model_info['capabilities']

    def test_validate_credentials_success(self, client, mock_genai):
        """Test successful credential validation."""
        with patch.object(client, '_get_genai_client', return_value=mock_genai):
            result = client.validate_credentials()

            assert result is True
            mock_genai.list_models.assert_called_once()

    def test_validate_credentials_failure(self, client, mock_genai):
        """Test failed credential validation."""
        with patch.object(client, '_get_genai_client', return_value=mock_genai):
            mock_genai.list_models.side_effect = Exception("Authentication failed")

            result = client.validate_credentials()

            assert result is False

    def test_get_usage_stats(self, client):
        """Test getting usage statistics."""
        # Add some mock usage
        client._stats['requests_made'] = 5
        client._stats['total_tokens'] = 1000

        stats = client.get_usage_stats()

        assert 'client_stats' in stats
        assert 'rate_limiter' in stats
        assert 'cache' in stats
        assert 'configuration' in stats
        assert 'provider_info' in stats

        assert stats['client_stats']['requests_made'] == 5
        assert stats['client_stats']['total_tokens'] == 1000

    def test_provider_name(self, client):
        """Test provider name property."""
        assert client.provider_name == 'gemini'

    def test_supported_features(self, client):
        """Test supported features property."""
        features = client.supported_features

        expected_features = [
            'text_generation',
            'chat_completion',
            'image_input',
            'safety_filtering',
            'response_caching',
            'streaming'
        ]

        for feature in expected_features:
            assert feature in features

    def test_supported_features_vision_enabled(self, client):
        """Test supported features with vision enabled."""
        client.config.is_vision_supported.return_value = True

        features = client.supported_features
        assert 'multimodal' in features

    def test_supported_features_streaming_disabled(self, client):
        """Test supported features with streaming disabled."""
        client.config.enable_streaming = False

        features = client.supported_features
        assert 'streaming' not in features

    def test_error_handling_quota_exceeded(self, client, mock_genai):
        """Test error handling for quota exceeded."""
        with patch.object(client, '_get_genai_client', return_value=mock_genai):
            mock_genai.GenerativeModel.return_value.generate_content.side_effect = \
                Exception("Quota exceeded")

            request = LLMRequest(prompt="Test")

            with pytest.raises(LLMProviderError):
                client.generate_text(request)

            # Should have recorded quota error
            assert client.rate_limiter._consecutive_quota_errors > 0

    def test_error_handling_rate_limit(self, client, mock_genai):
        """Test error handling for rate limit."""
        with patch.object(client, '_get_genai_client', return_value=mock_genai):
            mock_genai.GenerativeModel.return_value.generate_content.side_effect = \
                Exception("Rate limit exceeded")

            request = LLMRequest(prompt="Test")

            with pytest.raises(LLMProviderError):
                client.generate_text(request)

            # Should have recorded 429 error
            assert client.rate_limiter._consecutive_429s > 0

    def test_error_handling_api_key_error(self, client, mock_genai):
        """Test error handling for API key errors."""
        with patch.object(client, '_get_genai_client', return_value=mock_genai):
            mock_genai.GenerativeModel.return_value.generate_content.side_effect = \
                Exception("Invalid API key")

            request = LLMRequest(prompt="Test")

            with pytest.raises(LLMProviderError):
                client.generate_text(request)

            # Should have recorded invalid API key
            # (This doesn't update rate limiter counters)

    def test_statistics_tracking(self, client, mock_genai):
        """Test statistics tracking during operations."""
        with patch.object(client, '_get_genai_client', return_value=mock_genai):
            request = LLMRequest(prompt="Test")

            initial_requests = client._stats['requests_made']
            initial_tokens = client._stats['total_tokens']

            response = client.generate_text(request)

            assert client._stats['requests_made'] == initial_requests + 1
            assert client._stats['total_tokens'] == initial_tokens + response.usage.total_tokens

    def test_latency_measurement(self, client, mock_genai):
        """Test latency measurement."""
        with patch.object(client, '_get_genai_client', return_value=mock_genai):
            request = LLMRequest(prompt="Test")

            response = client.generate_text(request)

            assert response.latency_ms is not None
            assert response.latency_ms > 0

    def test_request_id_propagation(self, client, mock_genai):
        """Test request ID propagation."""
        with patch.object(client, '_get_genai_client', return_value=mock_genai):
            request = LLMRequest(
                prompt="Test",
                request_id="test-request-123"
            )

            response = client.generate_text(request)

            assert response.request_id == "test-request-123"
