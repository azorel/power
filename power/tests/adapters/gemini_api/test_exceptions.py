"""
Tests for Gemini API exception handling and translation.
"""

import pytest
from unittest.mock import MagicMock

from adapters.gemini_api.exceptions import GeminiExceptionMapper, handle_gemini_exception, wrap_gemini_call
from shared.exceptions import (
    LLMProviderError,
    AuthenticationError,
    RateLimitError,
    QuotaExceededError,
    ModelNotFoundError,
    InvalidRequestError,
    ContentFilterError,
    TimeoutError,
    NetworkError
)


class TestGeminiExceptionMapper:
    """Test cases for GeminiExceptionMapper class."""

    def test_translate_authentication_error(self):
        """Test translation of authentication errors."""
        # Test by status code
        auth_error = Exception("Invalid API key")
        auth_error.status_code = 401

        translated = GeminiExceptionMapper.translate_exception(auth_error)

        assert isinstance(translated, AuthenticationError)
        assert "authentication failed" in translated.message.lower()
        assert translated.details['original_exception'] == 'Exception'

    def test_translate_rate_limit_error(self):
        """Test translation of rate limit errors."""
        # Test by status code
        rate_error = Exception("Too many requests")
        rate_error.status_code = 429

        translated = GeminiExceptionMapper.translate_exception(rate_error)

        assert isinstance(translated, RateLimitError)
        assert "rate limit exceeded" in translated.message.lower()

    def test_translate_quota_exceeded_error(self):
        """Test translation of quota exceeded errors."""
        # Test by status code
        quota_error = Exception("Quota exceeded")
        quota_error.status_code = 403

        translated = GeminiExceptionMapper.translate_exception(quota_error)

        assert isinstance(translated, QuotaExceededError)
        assert "quota exceeded" in translated.message.lower()

    def test_translate_model_not_found_error(self):
        """Test translation of model not found errors."""
        # Test by status code
        model_error = Exception("Model not found")
        model_error.status_code = 404

        translated = GeminiExceptionMapper.translate_exception(model_error)

        assert isinstance(translated, ModelNotFoundError)
        assert "not found" in translated.message.lower()

    def test_translate_timeout_error(self):
        """Test translation of timeout errors."""
        # Test by status code
        timeout_error = Exception("Request timed out")
        timeout_error.status_code = 504

        translated = GeminiExceptionMapper.translate_exception(timeout_error)

        assert isinstance(translated, TimeoutError)
        assert "timed out" in translated.message.lower()

    def test_translate_by_message_pattern(self):
        """Test translation by error message patterns."""
        test_cases = [
            ("Invalid API key", AuthenticationError),
            ("API key not valid", AuthenticationError),
            ("Quota exceeded for this project", QuotaExceededError),
            ("Rate limit exceeded", RateLimitError),
            ("Too many requests", RateLimitError),
            ("Model gemini-invalid not found", ModelNotFoundError),
            ("Content filtered by safety policies", ContentFilterError),
            ("Request timeout", TimeoutError),
            ("Connection failed", NetworkError),
            ("Invalid request format", InvalidRequestError)
        ]

        for message, expected_type in test_cases:
            error = Exception(message)
            translated = GeminiExceptionMapper.translate_exception(error)
            assert isinstance(translated, expected_type)

    def test_translate_with_context(self):
        """Test translation with additional context."""
        error = Exception("Model not found")
        context = {
            'model': 'gemini-invalid',
            'operation': 'generate_text'
        }

        translated = GeminiExceptionMapper.translate_exception(error, context)

        assert isinstance(translated, ModelNotFoundError)
        assert translated.model_name == 'gemini-invalid'
        assert translated.details['operation'] == 'generate_text'

    def test_extract_status_code(self):
        """Test status code extraction from exceptions."""
        # Test with status_code attribute
        error1 = Exception("Test error")
        error1.status_code = 429

        status = GeminiExceptionMapper._extract_status_code(error1)
        assert status == 429

        # Test with response object
        error2 = Exception("Test error")
        error2.response = MagicMock()
        error2.response.status_code = 403

        status = GeminiExceptionMapper._extract_status_code(error2)
        assert status == 403

        # Test with no status code
        error3 = Exception("Test error")
        status = GeminiExceptionMapper._extract_status_code(error3)
        assert status is None

    def test_extract_retry_after(self):
        """Test retry-after value extraction."""
        # Test with retry_after attribute
        error1 = Exception("Rate limited")
        error1.retry_after = 60

        retry_after = GeminiExceptionMapper._extract_retry_after(error1)
        assert retry_after == 60

        # Test with response headers
        error2 = Exception("Rate limited")
        error2.response = MagicMock()
        error2.response.headers = {'retry-after': '120'}

        retry_after = GeminiExceptionMapper._extract_retry_after(error2)
        assert retry_after == 120

        # Test with no retry-after
        error3 = Exception("Rate limited")
        retry_after = GeminiExceptionMapper._extract_retry_after(error3)
        assert retry_after is None

    def test_extract_quota_type(self):
        """Test quota type extraction."""
        test_cases = [
            ("Daily quota exceeded", "daily"),
            ("Monthly limit reached", "monthly"),
            ("Per minute rate limit", "per_minute"),
            ("Hourly quota exceeded", "per_hour"),
            ("Quota exceeded", "unknown")
        ]

        for message, expected_type in test_cases:
            error = Exception(message)
            quota_type = GeminiExceptionMapper._extract_quota_type(error)
            assert quota_type == expected_type

    def test_extract_filter_reason(self):
        """Test content filter reason extraction."""
        test_cases = [
            ("Content blocked due to harassment", "harassment"),
            ("Hate speech detected", "hate_speech"),
            ("Sexual content filtered", "sexual_content"),
            ("Dangerous content blocked", "dangerous_content"),
            ("Violence detected", "violence"),
            ("Safety filter activated", "safety_filter")
        ]

        for message, expected_reason in test_cases:
            error = Exception(message)
            reason = GeminiExceptionMapper._extract_filter_reason(error)
            assert reason == expected_reason

    def test_handle_google_api_error(self):
        """Test handling of Google API specific errors."""
        # Mock Google API error with details
        class GoogleAPIError(Exception):
            pass
        
        error = GoogleAPIError("Google API error")

        translated = GeminiExceptionMapper._handle_google_api_error(error, {})

        assert isinstance(translated, LLMProviderError)
        assert "google api error" in translated.message.lower()

    def test_handle_generative_ai_error(self):
        """Test handling of Generative AI specific errors."""
        class GenerativeAIError(Exception):
            pass
        
        error = GenerativeAIError("Generative AI error")

        translated = GeminiExceptionMapper._handle_generative_ai_error(error, {})

        assert isinstance(translated, LLMProviderError)
        assert "generative ai error" in translated.message.lower()

    def test_fallback_translation(self):
        """Test fallback translation for unknown errors."""
        error = Exception("Unknown error type")

        translated = GeminiExceptionMapper.translate_exception(error)

        assert isinstance(translated, LLMProviderError)
        assert "unknown error type" in translated.message.lower()
        assert translated.details['fallback'] is True

    def test_preserve_original_exception(self):
        """Test that original exception is preserved."""
        original_error = ValueError("Original error")

        translated = GeminiExceptionMapper.translate_exception(original_error)

        assert translated.__cause__ is original_error
        assert translated.details['original_exception'] == 'ValueError'
        assert translated.details['original_message'] == 'Original error'

    def test_already_translated_exception(self):
        """Test that already translated exceptions are returned as-is."""
        already_translated = AuthenticationError("Already translated")

        result = GeminiExceptionMapper.translate_exception(already_translated)

        assert result is already_translated


class TestConvenienceFunctions:
    """Test convenience functions for exception handling."""

    def test_handle_gemini_exception(self):
        """Test handle_gemini_exception convenience function."""
        error = Exception("Test error")

        translated = handle_gemini_exception(error)

        assert isinstance(translated, LLMProviderError)
        assert "test error" in translated.message.lower()

    def test_handle_gemini_exception_with_context(self):
        """Test handle_gemini_exception with context."""
        error = Exception("Model not found")
        context = {'model': 'test-model'}

        translated = handle_gemini_exception(error, context)

        assert isinstance(translated, ModelNotFoundError)
        assert translated.details['model'] == 'test-model'

    def test_wrap_gemini_call_decorator(self):
        """Test wrap_gemini_call decorator."""
        @wrap_gemini_call
        def test_function():
            raise Exception("Test error")

        with pytest.raises(LLMProviderError) as exc_info:
            test_function()

        assert "test error" in str(exc_info.value).lower()
        assert exc_info.value.details['function'] == 'test_function'

    def test_wrap_gemini_call_success(self):
        """Test wrap_gemini_call decorator with successful function."""
        @wrap_gemini_call
        def test_function():
            return "success"

        result = test_function()
        assert result == "success"

    def test_wrap_gemini_call_with_args(self):
        """Test wrap_gemini_call decorator with function arguments."""
        @wrap_gemini_call
        def test_function(arg1, arg2, kwarg1=None):
            raise Exception("Test error")

        with pytest.raises(LLMProviderError) as exc_info:
            test_function("test", "args", kwarg1="test")

        exception = exc_info.value
        assert exception.details['function'] == 'test_function'
        assert exception.details['args_count'] == 2
        assert 'kwarg1' in exception.details['kwargs']


class TestSpecificErrorTypes:
    """Test specific error type handling."""

    def test_rate_limit_error_with_retry_after(self):
        """Test RateLimitError creation with retry_after."""
        error = Exception("Rate limit exceeded")
        error.status_code = 429
        error.retry_after = 60

        translated = GeminiExceptionMapper.translate_exception(error)

        assert isinstance(translated, RateLimitError)
        assert translated.retry_after == 60

    def test_quota_exceeded_error_with_details(self):
        """Test QuotaExceededError creation with quota details."""
        error = Exception("Daily quota exceeded")
        error.status_code = 403

        translated = GeminiExceptionMapper.translate_exception(error)

        assert isinstance(translated, QuotaExceededError)
        assert translated.quota_type == "daily"

    def test_model_not_found_error_with_model_name(self):
        """Test ModelNotFoundError creation with model name."""
        error = Exception("Model not found")
        context = {'model': 'gemini-invalid'}

        translated = GeminiExceptionMapper.translate_exception(error, context)

        assert isinstance(translated, ModelNotFoundError)
        assert translated.model_name == 'gemini-invalid'

    def test_content_filter_error_with_reason(self):
        """Test ContentFilterError creation with filter reason."""
        error = Exception("Content blocked due to harassment")

        translated = GeminiExceptionMapper.translate_exception(error)

        assert isinstance(translated, ContentFilterError)
        assert translated.filter_reason == "harassment"

    def test_timeout_error_with_timeout_seconds(self):
        """Test TimeoutError creation with timeout value."""
        error = Exception("Request timeout")
        context = {'timeout': 30}

        translated = GeminiExceptionMapper.translate_exception(error, context)

        assert isinstance(translated, TimeoutError)
        assert translated.timeout_seconds == 30
