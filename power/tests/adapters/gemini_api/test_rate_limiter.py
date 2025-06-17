"""
Tests for Gemini API rate limiter.
"""

import pytest
import time
from unittest.mock import patch, MagicMock

from adapters.gemini_api.rate_limiter import GeminiRateLimiter
from adapters.gemini_api.config import GeminiConfig


class TestGeminiRateLimiter:
    """Test cases for GeminiRateLimiter class."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock config for testing."""
        config = MagicMock(spec=GeminiConfig)
        config.rate_limit_per_minute = 60
        config.rate_limit_per_hour = 1000
        config.daily_quota = 1000
        config.min_request_interval = 0.0
        config.model = 'gemini-pro'
        config.image_generation_model = 'gemini-2.0-flash-exp-image-generation'
        config.function_calling_model = 'gemini-2.0-flash'
        config.is_vision_supported.return_value = True
        config.supports_function_calling.return_value = True
        config.supports_image_generation.return_value = True
        config.supports_system_instructions.return_value = True
        return config

    @pytest.fixture
    def rate_limiter(self, mock_config):
        """Create a rate limiter for testing."""
        return GeminiRateLimiter(mock_config)

    def test_initialization(self, mock_config):
        """Test rate limiter initialization."""
        limiter = GeminiRateLimiter(mock_config)

        assert limiter.config == mock_config
        assert limiter.calls_per_minute == 60
        assert limiter.calls_per_hour == 1000
        assert limiter._daily_quota_limit == 1000
        assert limiter._input_tokens_used == 0
        assert limiter._output_tokens_used == 0
        assert limiter._total_tokens_used == 0

    def test_can_make_request_basic(self, rate_limiter):
        """Test basic request permission."""
        # Fresh limiter should allow requests
        assert rate_limiter.can_make_request('text')
        assert rate_limiter.can_make_request('vision')
        assert rate_limiter.can_make_request('streaming')

    def test_can_make_request_vision_not_supported(self, rate_limiter):
        """Test vision request when not supported."""
        rate_limiter.config.is_vision_supported.return_value = False

        assert rate_limiter.can_make_request('text')
        assert not rate_limiter.can_make_request('vision')

    def test_record_request(self, rate_limiter):
        """Test request recording."""
        rate_limiter.record_request(
            request_type='text',
            input_tokens=100,
            output_tokens=50,
            cost=0.01
        )

        assert rate_limiter._total_requests == 1
        assert rate_limiter._input_tokens_used == 100
        assert rate_limiter._output_tokens_used == 50
        assert rate_limiter._total_tokens_used == 150
        assert rate_limiter._total_cost == 0.01
        assert rate_limiter._text_requests == 1

    def test_record_different_request_types(self, rate_limiter):
        """Test recording different request types."""
        rate_limiter.record_request(request_type='text')
        rate_limiter.record_request(request_type='vision')
        rate_limiter.record_request(request_type='streaming')

        assert rate_limiter._text_requests == 1
        assert rate_limiter._vision_requests == 1
        assert rate_limiter._streaming_requests == 1
        assert rate_limiter._total_requests == 3

    def test_record_quota_exceeded(self, rate_limiter):
        """Test quota exceeded error recording."""
        rate_limiter.record_quota_exceeded()

        assert rate_limiter._consecutive_quota_errors == 1
        assert rate_limiter._consecutive_429s == 1  # Also records as 429

    def test_can_make_request_after_quota_error(self, rate_limiter):
        """Test request blocking after quota errors."""
        rate_limiter.record_quota_exceeded()

        # Should block requests initially
        assert not rate_limiter.can_make_request('text')

        # Mock time to simulate backoff period passing
        with patch('time.time', return_value=time.time() + 400):
            # Should allow requests after backoff period
            assert rate_limiter.can_make_request('text')

    def test_get_gemini_stats(self, rate_limiter):
        """Test Gemini-specific statistics."""
        # Record some requests
        rate_limiter.record_request('text', 100, 50, 0.01)
        rate_limiter.record_request('vision', 200, 75, 0.02)

        stats = rate_limiter.get_gemini_stats()

        assert 'base_stats' in stats
        assert 'gemini_stats' in stats

        gemini_stats = stats['gemini_stats']
        assert 'token_usage' in gemini_stats
        assert 'cost_tracking' in gemini_stats
        assert 'request_types' in gemini_stats
        assert 'gemini_specific' in gemini_stats
        assert 'rate_limits' in gemini_stats

        # Check token usage
        token_usage = gemini_stats['token_usage']
        assert token_usage['input_tokens'] == 300
        assert token_usage['output_tokens'] == 125
        assert token_usage['total_tokens'] == 425

        # Check cost tracking
        cost_tracking = gemini_stats['cost_tracking']
        assert cost_tracking['total_cost'] == 0.03

        # Check request types
        request_types = gemini_stats['request_types']
        assert request_types['text_requests'] == 1
        assert request_types['vision_requests'] == 1
        assert request_types['streaming_requests'] == 0

    def test_estimate_tokens(self, rate_limiter):
        """Test token estimation."""
        text = "This is a test prompt"
        tokens = rate_limiter.estimate_tokens(text)

        # Should estimate roughly len(text) / 3
        expected = max(1, len(text) // 3)
        assert tokens == expected

    def test_can_handle_tokens(self, rate_limiter):
        """Test token limit checking."""
        # Test with Gemini Pro limits
        rate_limiter.config.model = 'gemini-pro'

        # Should handle reasonable token counts
        assert rate_limiter.can_handle_tokens(1000, 500)

        # Should reject excessive input tokens
        assert not rate_limiter.can_handle_tokens(50000, 500)

        # Should reject excessive output tokens
        assert not rate_limiter.can_handle_tokens(1000, 5000)

    def test_can_handle_tokens_gemini_15(self, rate_limiter):
        """Test token limits for Gemini 1.5 models."""
        rate_limiter.config.model = 'gemini-1.5-pro'

        # Should handle much larger token counts
        assert rate_limiter.can_handle_tokens(100000, 4000)

        # Should still have limits
        assert not rate_limiter.can_handle_tokens(2000000, 4000)
        assert not rate_limiter.can_handle_tokens(100000, 10000)

    def test_get_optimal_batch_size(self, rate_limiter):
        """Test optimal batch size calculation."""
        # Fresh limiter should suggest normal batch size
        assert rate_limiter.get_optimal_batch_size() == 5

        # After many requests, should suggest smaller batches
        for _ in range(50):
            rate_limiter.record_request('text')

        assert rate_limiter.get_optimal_batch_size() == 1

        # Create fresh limiter to test quota error logic without rate limits
        fresh_config = MagicMock(spec=GeminiConfig)
        fresh_config.rate_limit_per_minute = 60
        fresh_config.rate_limit_per_hour = 1000
        fresh_config.daily_quota = 1000
        fresh_config.min_request_interval = 0.0
        fresh_config.model = 'gemini-pro'
        fresh_config.image_generation_model = 'gemini-2.0-flash-exp-image-generation'
        fresh_config.function_calling_model = 'gemini-2.0-flash'
        fresh_config.is_vision_supported.return_value = True
        fresh_config.supports_function_calling.return_value = True
        fresh_config.supports_image_generation.return_value = True
        fresh_config.supports_system_instructions.return_value = True
        fresh_limiter = GeminiRateLimiter(fresh_config)
        
        # After quota errors, should be conservative but not completely blocking
        fresh_limiter._consecutive_quota_errors = 2
        assert fresh_limiter.get_optimal_batch_size() == 3
        
        # With too many errors, should cap at minimum
        fresh_limiter._consecutive_quota_errors = 5
        assert fresh_limiter.get_optimal_batch_size() == 3

    def test_reset_daily_quotas(self, rate_limiter):
        """Test daily quota reset."""
        # Record some usage
        rate_limiter.record_request('text', 100, 50, 0.01)
        rate_limiter.record_request('vision', 200, 75, 0.02)
        rate_limiter._consecutive_quota_errors = 3

        # Reset quotas
        rate_limiter.reset_daily_quotas()

        # Token and cost counters should be reset
        assert rate_limiter._input_tokens_used == 0
        assert rate_limiter._output_tokens_used == 0
        assert rate_limiter._total_tokens_used == 0
        assert rate_limiter._total_cost == 0.0

        # Request type counters should be reset
        assert rate_limiter._text_requests == 0
        assert rate_limiter._vision_requests == 0
        assert rate_limiter._streaming_requests == 0

        # Quota error tracking should be reset
        assert rate_limiter._consecutive_quota_errors == 0

    def test_get_usage_summary(self, rate_limiter):
        """Test usage summary generation."""
        # Record some usage
        rate_limiter.record_request('text', 100, 50, 0.01)
        rate_limiter.record_request('vision', 200, 75, 0.02)

        summary = rate_limiter.get_usage_summary()

        assert 'summary' in summary
        assert 'efficiency' in summary
        assert 'quota_status' in summary
        assert 'request_breakdown' in summary

        # Check summary content
        assert '2 requests' in summary['summary']
        assert '425 tokens used' in summary['summary']

        # Check efficiency metrics
        efficiency = summary['efficiency']
        assert 'cache_hit_rate' in efficiency
        assert 'avg_tokens_per_request' in efficiency
        assert 'total_cost' in efficiency

        # Check quota status
        quota_status = summary['quota_status']
        assert 'daily_quota_used' in quota_status
        assert 'rate_limit_status' in quota_status
        assert 'quota_errors' in quota_status

        # Check request breakdown
        breakdown = summary['request_breakdown']
        assert breakdown['text_requests'] == 1
        assert breakdown['vision_requests'] == 1
        assert breakdown['streaming_requests'] == 0

    def test_rate_limit_enforcement(self, rate_limiter):
        """Test actual rate limit enforcement."""
        # Fill up the rate limit
        for _ in range(60):
            assert rate_limiter.can_make_request('text')
            rate_limiter.record_request('text')

        # Should be blocked now
        assert not rate_limiter.can_make_request('text')

        # Should have a wait time
        wait_time = rate_limiter.get_wait_time()
        assert wait_time > 0

    def test_adaptive_backoff(self, rate_limiter):
        """Test adaptive backoff behavior."""
        # Initial wait time should be minimal
        initial_wait = rate_limiter.get_wait_time()

        # Record 429 errors
        rate_limiter.record_429_error()
        rate_limiter.record_429_error()

        # Wait time should increase due to backoff
        backoff_wait = rate_limiter.get_wait_time()
        assert backoff_wait >= initial_wait

        # Backoff info should reflect the state
        backoff_info = rate_limiter.get_backoff_info()
        assert backoff_info['consecutive_429s'] == 2
        assert backoff_info['backoff_factor'] > 1.0
        assert backoff_info['is_backing_off'] is True
