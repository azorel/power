"""
Gemini API rate limiter with Google-specific quota management.
Extends shared rate limiter with Gemini-specific features.
"""

import time
from typing import Dict, Any
from shared.utils.rate_limiter import AdaptiveRateLimiter, BaseRateLimiter
from .config import GeminiConfig


class GeminiRateLimiter(AdaptiveRateLimiter):
    """
    Rate limiter specifically designed for Google Gemini API.
    Handles Google's specific rate limiting and quota patterns.
    """

    def __init__(self, config: GeminiConfig):
        """
        Initialize Gemini rate limiter.

        Args:
            config: Gemini configuration instance
        """
        super().__init__(
            calls_per_minute=config.rate_limit_per_minute,
            calls_per_hour=config.rate_limit_per_hour,
            calls_per_day=config.daily_quota,
            min_interval_seconds=config.min_request_interval
        )

        self.config = config

        # Token usage tracking
        self._input_tokens_used = 0
        self._output_tokens_used = 0
        self._total_tokens_used = 0

        # Cost tracking (if pricing available)
        self._total_cost = 0.0

        # Request categorization
        self._text_requests = 0
        self._vision_requests = 0
        self._streaming_requests = 0
        self._function_calling_requests = 0
        self._image_generation_requests = 0
        self._system_instruction_requests = 0

        # Google-specific rate limit patterns
        self._consecutive_quota_errors = 0
        self._last_quota_reset = time.time()

        # Performance tracking
        self._request_latencies = []
        self._last_performance_cleanup = time.time()

    def can_make_request(self, request_type: str = 'text') -> bool:
        """
        Check if request can be made considering Gemini-specific limits.

        Args:
            request_type: Type of request ('text', 'vision', 'streaming',
                         'function_calling', 'image_generation', 'system_instruction')

        Returns:
            True if request is allowed, False otherwise
        """
        # Check base rate limits first
        if not super().can_make_request():
            return False

        # Gemini-specific feature checks
        if request_type == 'vision' and not self.config.is_vision_supported():
            return False
        elif (request_type == 'function_calling' and
              not self.config.supports_function_calling()):
            return False
        elif (request_type == 'image_generation' and
              not self.config.supports_image_generation()):
            return False
        elif (request_type == 'system_instruction' and
              not self.config.supports_system_instructions()):
            return False

        # Check if we're in a backoff period due to quota errors
        if self._consecutive_quota_errors > 0:
            backoff_time = min(300, self._consecutive_quota_errors * 30)  # Max 5 min
            if time.time() - self._last_quota_reset < backoff_time:
                return False

        return True

    def record_request(
        self,
        request_type: str = 'text',
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost: float = 0.0,
        latency_ms: float = 0.0
    ) -> None:
        """
        Record a successful request with Gemini-specific metrics and performance tracking.

        Args:
            request_type: Type of request made
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens generated
            cost: Cost of the request (if available)
            latency_ms: Request latency in milliseconds
        """
        # Call the base class record_request method directly from BaseRateLimiter
        BaseRateLimiter.record_request(self)

        # Update token usage
        self._input_tokens_used += input_tokens
        self._output_tokens_used += output_tokens
        self._total_tokens_used += input_tokens + output_tokens

        # Update cost tracking
        self._total_cost += cost

        # Track performance metrics
        if latency_ms > 0:
            self._request_latencies.append(latency_ms)
            # Keep only recent latencies for memory efficiency
            if len(self._request_latencies) > 100:
                self._request_latencies = self._request_latencies[-50:]

        # Update request type counters
        if request_type == 'text':
            self._text_requests += 1
        elif request_type == 'vision':
            self._vision_requests += 1
        elif request_type == 'streaming':
            self._streaming_requests += 1
        elif request_type == 'function_calling':
            self._function_calling_requests += 1
        elif request_type == 'image_generation':
            self._image_generation_requests += 1
        elif request_type == 'system_instruction':
            self._system_instruction_requests += 1

        # Reset quota error tracking on successful request
        if self._consecutive_quota_errors > 0:
            self._consecutive_quota_errors = max(0, self._consecutive_quota_errors - 1)

        # Periodic performance cleanup
        self._maybe_cleanup_performance_data()

    def record_quota_exceeded(self) -> None:
        """Record a quota exceeded error from Gemini API."""
        self._consecutive_quota_errors += 1
        self._last_quota_reset = time.time()

        # Also record as 429 for adaptive behavior
        self.record_429_error()

    def record_invalid_api_key(self) -> None:
        """Record an invalid API key error (non-retryable)."""
        # Don't update request counters for auth errors
        pass

    def get_gemini_stats(self) -> Dict[str, Any]:
        """Get Gemini-specific statistics."""
        base_stats = self.get_stats()
        backoff_info = self.get_backoff_info()

        gemini_stats = {
            'token_usage': {
                'input_tokens': self._input_tokens_used,
                'output_tokens': self._output_tokens_used,
                'total_tokens': self._total_tokens_used,
                'average_tokens_per_request': (
                    self._total_tokens_used / max(1, base_stats.total_requests)
                )
            },
            'cost_tracking': {
                'total_cost': self._total_cost,
                'average_cost_per_request': (
                    self._total_cost / max(1, base_stats.total_requests)
                )
            },
            'request_types': {
                'text_requests': self._text_requests,
                'vision_requests': self._vision_requests,
                'streaming_requests': self._streaming_requests,
                'function_calling_requests': self._function_calling_requests,
                'image_generation_requests': self._image_generation_requests,
                'system_instruction_requests': self._system_instruction_requests
            },
            'gemini_specific': {
                'consecutive_quota_errors': self._consecutive_quota_errors,
                'quota_backoff_active': (
                    self._consecutive_quota_errors > 0 and
                    time.time() - self._last_quota_reset < 300
                ),
                'supports_vision': self.config.is_vision_supported(),
                'supports_function_calling': self.config.supports_function_calling(),
                'supports_image_generation': self.config.supports_image_generation(),
                'supports_system_instructions': self.config.supports_system_instructions(),
                'current_model': self.config.model,
                'image_generation_model': getattr(self.config, 'image_generation_model', 'N/A'),
                'function_calling_model': getattr(self.config, 'function_calling_model', 'N/A')
            },
            'rate_limits': {
                'requests_per_minute_limit': self.calls_per_minute,
                'requests_per_hour_limit': self.calls_per_hour,
                'daily_quota_limit': self._daily_quota_limit,
                'backoff_factor': backoff_info['backoff_factor'],
                'is_backing_off': backoff_info['is_backing_off']
            }
        }

        return {
            'base_stats': base_stats.to_dict(),
            'gemini_stats': gemini_stats
        }

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text (rough approximation).

        Args:
            text: Text to estimate tokens for

        Returns:
            Estimated token count
        """
        # Very rough estimation: ~4 characters per token for English
        # Gemini uses SentencePiece tokenization which is more efficient
        return max(1, len(text) // 3)

    def can_handle_tokens(self, estimated_input_tokens: int, estimated_output_tokens: int) -> bool:
        """
        Check if request can be handled within token limits.

        Args:
            estimated_input_tokens: Estimated input token count
            estimated_output_tokens: Estimated output token count

        Returns:
            True if request is within limits, False otherwise
        """
        # Gemini Pro has different limits based on model
        if 'gemini-2.0' in self.config.model:
            max_input_tokens = 2097152  # 2M tokens for Gemini 2.0
            max_output_tokens = 8192
        elif 'gemini-1.5' in self.config.model:
            max_input_tokens = 1048576  # 1M tokens for Gemini 1.5
            max_output_tokens = 8192
        else:
            max_input_tokens = 30720  # 30K tokens for older models
            max_output_tokens = 2048

        return (
            estimated_input_tokens <= max_input_tokens and
            estimated_output_tokens <= max_output_tokens
        )

    def get_optimal_batch_size(self) -> int:
        """
        Get optimal batch size for current rate limit state.

        Returns:
            Recommended batch size
        """
        current_stats = self.get_stats()

        # If we're hitting rate limits, reduce batch size significantly
        if current_stats.requests_this_minute >= self.calls_per_minute * 0.8:
            return 1

        # If we have quota errors, be more conservative but not completely blocking
        if self._consecutive_quota_errors > 0:
            # Scale down based on error count but ensure minimum of 1
            return max(1, 5 - min(self._consecutive_quota_errors, 2))

        # Normal batch size for good conditions
        return 5

    def reset_daily_quotas(self) -> None:
        """Reset daily quota tracking (for new day)."""
        super().reset_quotas(daily=True)

        # Reset Gemini-specific daily counters
        self._input_tokens_used = 0
        self._output_tokens_used = 0
        self._total_tokens_used = 0
        self._total_cost = 0.0

        self._text_requests = 0
        self._vision_requests = 0
        self._streaming_requests = 0

        # Reset quota error tracking
        self._consecutive_quota_errors = 0

        # Reset performance tracking
        self._request_latencies.clear()
        self._last_performance_cleanup = time.time()

    def get_usage_summary(self) -> Dict[str, Any]:
        """Get human-readable usage summary."""
        stats = self.get_gemini_stats()
        base_stats = stats['base_stats']
        gemini_stats = stats['gemini_stats']

        # Handle cache stats safely (may not be present in rate limiter)
        cache_hits = base_stats.get('cache_hits', 0)
        hit_rate = base_stats.get('hit_rate', 0.0)

        return {
            'summary': f"Made {base_stats['total_requests']} requests "
                      f"({cache_hits} cached, "
                      f"{gemini_stats['token_usage']['total_tokens']} tokens used)",
            'efficiency': {
                'cache_hit_rate': f"{hit_rate:.1%}",
                'avg_tokens_per_request': f"{gemini_stats['token_usage']['average_tokens_per_request']:.1f}",
                'total_cost': f"${gemini_stats['cost_tracking']['total_cost']:.4f}"
            },
            'quota_status': {
                'daily_quota_used': f"{base_stats['requests_today']}/{base_stats.get('daily_quota_limit', 'unlimited')}",
                'rate_limit_status': f"{base_stats['requests_this_minute']}/{self.calls_per_minute} per minute",
                'quota_errors': gemini_stats['gemini_specific']['consecutive_quota_errors']
            },
            'request_breakdown': {
                'text_requests': gemini_stats['request_types']['text_requests'],
                'vision_requests': gemini_stats['request_types']['vision_requests'],
                'streaming_requests': gemini_stats['request_types']['streaming_requests']
            }
        }

    def _maybe_cleanup_performance_data(self) -> None:
        """Cleanup performance data periodically to manage memory."""
        current_time = time.time()
        if current_time - self._last_performance_cleanup > 300:  # 5 minutes
            # Keep only recent latencies
            if len(self._request_latencies) > 50:
                self._request_latencies = self._request_latencies[-25:]
            self._last_performance_cleanup = current_time

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get detailed performance statistics."""
        if not self._request_latencies:
            return {
                'average_latency_ms': 0.0,
                'min_latency_ms': 0.0,
                'max_latency_ms': 0.0,
                'p95_latency_ms': 0.0,
                'sample_count': 0
            }

        sorted_latencies = sorted(self._request_latencies)
        count = len(sorted_latencies)

        return {
            'average_latency_ms': sum(sorted_latencies) / count,
            'min_latency_ms': sorted_latencies[0],
            'max_latency_ms': sorted_latencies[-1],
            'p95_latency_ms': sorted_latencies[int(count * 0.95)] if count > 0 else 0.0,
            'sample_count': count
        }

    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics including performance metrics."""
        base_stats = self.get_gemini_stats()
        performance_stats = self.get_performance_stats()

        return {
            **base_stats,
            'performance': performance_stats,
            'memory_optimization': {
                'latency_samples_tracked': len(self._request_latencies),
                'last_cleanup': self._last_performance_cleanup
            }
        }

    def wait_if_needed(self, request_type: str = 'text') -> None:
        """
        Wait if necessary before making a request to respect rate limits.
        Args:
            request_type: Type of request for Gemini-specific rate limiting

        Raises:
            RateLimitError: If wait time is too long or rate limit is exceeded
        """
        from shared.exceptions import RateLimitError

        wait_time = self.get_wait_time()
        if wait_time > 0:
            # If rate limiter says we can't make a request, raise error
            if not self.can_make_request():
                raise RateLimitError(
                    f"Rate limit exceeded for {request_type} requests",
                    retry_after=int(wait_time)
                )
            time.sleep(wait_time)
