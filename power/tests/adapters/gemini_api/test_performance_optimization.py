"""
Tests for performance optimization features in Gemini rate limiter and cache.
"""

import pytest
import time
import threading
from unittest.mock import MagicMock

from adapters.gemini_api.rate_limiter import GeminiRateLimiter
from adapters.gemini_api.config import GeminiConfig
from shared.utils.cache import ResponseCache
from shared.utils.rate_limiter import BaseRateLimiter


class TestPerformanceOptimizations:
    """Test performance optimization features."""

    def create_mock_config(self):
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
    def rate_limiter(self):
        """Create a rate limiter for testing."""
        config = self.create_mock_config()
        return GeminiRateLimiter(config)

    @pytest.fixture
    def cache(self):
        """Create a cache for testing."""
        return ResponseCache(max_size=100, default_ttl_seconds=300)

    def test_performance_tracking(self, rate_limiter):
        """Test performance metric tracking."""
        # Record requests with latency
        rate_limiter.record_request('text', 100, 50, 0.01, 150.0)
        rate_limiter.record_request('vision', 200, 75, 0.02, 250.0)
        rate_limiter.record_request('text', 50, 25, 0.005, 100.0)

        # Get performance stats
        perf_stats = rate_limiter.get_performance_stats()

        assert perf_stats['sample_count'] == 3
        assert perf_stats['min_latency_ms'] == 100.0
        assert perf_stats['max_latency_ms'] == 250.0
        assert perf_stats['average_latency_ms'] == (150.0 + 250.0 + 100.0) / 3
        assert perf_stats['p95_latency_ms'] > 0

    def test_comprehensive_stats(self, rate_limiter):
        """Test comprehensive statistics including performance."""
        # Record requests with various metrics
        rate_limiter.record_request('text', 100, 50, 0.01, 150.0)
        rate_limiter.record_request('vision', 200, 75, 0.02, 250.0)

        # Get comprehensive stats
        stats = rate_limiter.get_comprehensive_stats()

        assert 'base_stats' in stats
        assert 'gemini_stats' in stats
        assert 'performance' in stats
        assert 'memory_optimization' in stats

        # Check performance section
        assert stats['performance']['sample_count'] == 2
        assert stats['performance']['average_latency_ms'] == 200.0

        # Check memory optimization info
        assert 'latency_samples_tracked' in stats['memory_optimization']
        assert 'last_cleanup' in stats['memory_optimization']

    def test_latency_memory_management(self, rate_limiter):
        """Test that latency tracking doesn't consume excessive memory."""
        # Record exactly 101 requests to trigger one cleanup
        for i in range(101):
            rate_limiter.record_request('text', 10, 5, 0.001, 100.0 + i)

        # After 101 requests, should have been trimmed to 50 at request 101
        perf_stats = rate_limiter.get_performance_stats()
        assert perf_stats['sample_count'] == 50  # Should be trimmed to 50
        
        # Test that it doesn't grow unbounded
        for i in range(100):
            rate_limiter.record_request('text', 10, 5, 0.001, 200.0 + i)
        
        # Should never exceed 100 total latencies
        perf_stats = rate_limiter.get_performance_stats()
        assert perf_stats['sample_count'] <= 100

    def test_optimal_batch_size_accuracy(self, rate_limiter):
        """Test that optimal batch size calculation is accurate."""
        # Fresh limiter should suggest normal batch size
        assert rate_limiter.get_optimal_batch_size() == 5

        # Simulate approaching rate limit
        for _ in range(48):  # 80% of 60 per minute
            rate_limiter.record_request('text')

        assert rate_limiter.get_optimal_batch_size() == 1

        # Test quota error scenarios with fresh limiter
        fresh_limiter = GeminiRateLimiter(self.create_mock_config())
        fresh_limiter._consecutive_quota_errors = 1
        assert fresh_limiter.get_optimal_batch_size() == 4

        fresh_limiter._consecutive_quota_errors = 2
        assert fresh_limiter.get_optimal_batch_size() == 3

        fresh_limiter._consecutive_quota_errors = 5  # Should cap at minimum
        assert fresh_limiter.get_optimal_batch_size() == 3


    def test_cache_performance_optimization(self, cache):
        """Test cache performance optimizations."""
        # Fill cache with some entries
        for i in range(50):
            cache.set(f"key_{i}", f"value_{i}", 300)

        # Add some expired entries
        for i in range(10):
            cache.set(f"expired_{i}", f"value_{i}", 1)

        time.sleep(2)  # Let some entries expire

        # Get initial stats
        initial_stats = cache.get_stats()

        # Force cleanup
        cleaned = cache.cleanup_expired()

        # Verify cleanup happened
        assert cleaned >= 10  # Should have cleaned expired entries

        # Check memory usage improved
        final_stats = cache.get_stats()
        assert final_stats.current_size < initial_stats.current_size

    def test_cache_memory_efficiency(self, cache):
        """Test cache memory efficiency under load."""
        # Fill cache beyond capacity to test LRU eviction
        for i in range(150):  # More than max_size of 100
            cache.set(f"key_{i}", f"value_{i}")

        stats = cache.get_stats()
        assert stats.current_size <= 100  # Should not exceed max size
        assert stats.evictions > 0  # Should have evicted some entries

    def test_rate_limiter_memory_optimization(self):
        """Test rate limiter memory optimization features."""
        config = MagicMock(spec=GeminiConfig)
        config.rate_limit_per_minute = 60
        config.rate_limit_per_hour = 1000
        config.daily_quota = 1000
        config.min_request_interval = 0.0

        limiter = BaseRateLimiter(
            calls_per_minute=60,
            calls_per_hour=1000,
            min_interval_seconds=0.0
        )

        # Record many requests
        for _ in range(100):
            limiter.record_request()

        # Get memory usage
        memory_stats = limiter.get_memory_usage()
        assert 'minute_requests_count' in memory_stats
        assert 'hour_requests_count' in memory_stats
        assert 'total_tracked_requests' in memory_stats

        # Optimize memory
        optimization_result = limiter.optimize_memory()
        assert 'requests_cleaned' in optimization_result
        assert 'memory_before' in optimization_result
        assert 'memory_after' in optimization_result

    def test_concurrent_performance(self, rate_limiter):
        """Test performance under concurrent access."""
        results = []
        errors = []

        def worker():
            try:
                for i in range(10):
                    if rate_limiter.can_make_request():
                        start_time = time.time()
                        rate_limiter.record_request('text', 50, 25, 0.01, 100.0)
                        end_time = time.time()
                        results.append(end_time - start_time)
            except Exception as e:
                errors.append(e)

        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Verify no errors and reasonable performance
        assert len(errors) == 0
        assert len(results) > 0
        assert all(result < 0.1 for result in results)  # Should be fast

        # Verify stats are consistent
        stats = rate_limiter.get_gemini_stats()
        assert stats['base_stats']['total_requests'] > 0

    def test_adaptive_backoff_performance(self, rate_limiter):
        """Test adaptive backoff doesn't impact performance excessively."""
        # Simulate 429 errors
        rate_limiter.record_429_error()
        rate_limiter.record_429_error()

        # Check backoff state
        backoff_info = rate_limiter.get_backoff_info()
        assert backoff_info['consecutive_429s'] == 2
        assert backoff_info['backoff_factor'] > 1.0
        assert backoff_info['is_backing_off'] is True

        # Check memory usage is included
        assert 'memory_usage' in backoff_info

        # Wait time might be 0 if no rate limits are actually hit
        # The backoff affects the multiplier but doesn't create wait time if no limits reached
        wait_time = rate_limiter.get_wait_time()
        assert wait_time >= 0  # Should be non-negative

    def test_performance_cleanup_efficiency(self, rate_limiter):
        """Test that performance data cleanup is efficient."""
        # Record initial timestamp
        initial_cleanup = rate_limiter._last_performance_cleanup

        # Record some requests (under the cleanup threshold)
        for i in range(10):
            rate_limiter.record_request('text', 50, 25, 0.01, 100.0 + i)

        # Should have 10 latencies
        assert len(rate_limiter._request_latencies) == 10

        # Force cleanup by recording requests to exceed 100 threshold
        for i in range(95):  # 10 + 95 = 105 total
            rate_limiter.record_request('text', 10, 5, 0.001, 50.0)

        # Should have trimmed latencies due to size limit
        perf_stats = rate_limiter.get_performance_stats()
        assert perf_stats['sample_count'] <= 100  # Should be controlled
        assert perf_stats['sample_count'] >= 50   # But not too aggressive