"""
Base rate limiter utility for adapter quota and rate management.
Shared utility that all adapters can use for consistent rate limiting behavior.
"""

import time
import threading
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from collections import deque


@dataclass
class RateLimitStats:  # pylint: disable=too-many-instance-attributes
    """Statistics for rate limiting and quota usage."""

    requests_this_minute: int = 0
    requests_this_hour: int = 0
    requests_today: int = 0
    total_requests: int = 0

    quota_remaining_daily: Optional[int] = None
    quota_remaining_monthly: Optional[int] = None

    last_request_time: Optional[datetime] = None
    next_allowed_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary format."""
        return {
            'requests_this_minute': self.requests_this_minute,
            'requests_this_hour': self.requests_this_hour,
            'requests_today': self.requests_today,
            'total_requests': self.total_requests,
            'quota_remaining_daily': self.quota_remaining_daily,
            'quota_remaining_monthly': self.quota_remaining_monthly,
            'last_request_time': (
                self.last_request_time.isoformat() if self.last_request_time else None
            ),
            'next_allowed_time': (
                self.next_allowed_time.isoformat() if self.next_allowed_time else None
            )
        }


class BaseRateLimiter:  # pylint: disable=too-many-instance-attributes
    """
    Base rate limiter class that adapters can extend.
    Provides thread-safe request throttling and quota management.
    """

    def __init__(
        self,
        calls_per_minute: int = 60,
        calls_per_hour: Optional[int] = None,
        calls_per_day: Optional[int] = None,
        min_interval_seconds: float = 0.0
    ):
        """
        Initialize rate limiter.

        Args:
            calls_per_minute: Maximum calls allowed per minute
            calls_per_hour: Maximum calls allowed per hour (optional)
            calls_per_day: Maximum calls allowed per day (optional)
            min_interval_seconds: Minimum seconds between requests
        """
        self.calls_per_minute = calls_per_minute
        self.calls_per_hour = calls_per_hour
        self.calls_per_day = calls_per_day
        self.min_interval_seconds = min_interval_seconds

        # Thread-safe tracking
        self._lock = threading.RLock()

        # Request timestamps for sliding window
        self._minute_requests: deque = deque()
        self._hour_requests: deque = deque()
        self._day_requests: deque = deque()

        # Last request time for minimum interval
        self._last_request_time: Optional[float] = None

        # Total counters
        self._total_requests = 0
        self._daily_quota_used = 0
        self._monthly_quota_used = 0

        # Quota limits
        self._daily_quota_limit: Optional[int] = calls_per_day
        self._monthly_quota_limit: Optional[int] = None

        # Day tracking for quota reset
        self._current_day = datetime.now().date()
        self._current_month = datetime.now().month

    def can_make_request(self) -> bool:
        """
        Check if a request can be made without violating rate limits.
        Optimized for performance under concurrent access.

        Returns:
            True if request is allowed, False otherwise
        """
        with self._lock:
            now = time.time()
            current_date = datetime.now().date()
            current_month = datetime.now().month

            # Reset daily counters if day changed (optimized check)
            if current_date != self._current_day:
                self._current_day = current_date
                self._daily_quota_used = 0
                self._day_requests.clear()

            # Reset monthly counters if month changed (optimized check)
            if current_month != self._current_month:
                self._current_month = current_month
                self._monthly_quota_used = 0

            # Clean up old timestamps (optimized)
            self._cleanup_old_timestamps(now)

            # Fast path: Check minimum interval first (most common failure)
            if (self._last_request_time is not None and
                now - self._last_request_time < self.min_interval_seconds):
                return False

            # Fast path: Check per-minute limit (second most common)
            if len(self._minute_requests) >= self.calls_per_minute:
                return False

            # Check per-hour limit if configured
            if (self.calls_per_hour is not None and
                len(self._hour_requests) >= self.calls_per_hour):
                return False

            # Check daily quota if configured
            if (self._daily_quota_limit is not None and
                self._daily_quota_used >= self._daily_quota_limit):
                return False

            # Check monthly quota if configured
            if (self._monthly_quota_limit is not None and
                self._monthly_quota_used >= self._monthly_quota_limit):
                return False

            return True

    def record_request(self) -> None:
        """Record that a request was made. Call this after successful API call."""
        with self._lock:
            now = time.time()

            # Add timestamps
            self._minute_requests.append(now)
            self._hour_requests.append(now)
            self._day_requests.append(now)

            # Update counters
            self._last_request_time = now
            self._total_requests += 1
            self._daily_quota_used += 1
            self._monthly_quota_used += 1

    def get_wait_time(self) -> float:
        """
        Get the number of seconds to wait before next request is allowed.

        Returns:
            Seconds to wait, or 0.0 if request can be made immediately
        """
        with self._lock:
            if self.can_make_request():
                return 0.0

            now = time.time()
            wait_times = []

            # Minimum interval wait
            if (self._last_request_time is not None and
                now - self._last_request_time < self.min_interval_seconds):
                wait_times.append(
                    self.min_interval_seconds - (now - self._last_request_time)
                )

            # Per-minute rate limit wait
            if len(self._minute_requests) >= self.calls_per_minute:
                oldest_request = self._minute_requests[0]
                wait_times.append(60.0 - (now - oldest_request))

            # Per-hour rate limit wait
            if (self.calls_per_hour is not None and
                len(self._hour_requests) >= self.calls_per_hour):
                oldest_request = self._hour_requests[0]
                wait_times.append(3600.0 - (now - oldest_request))

            return max(wait_times) if wait_times else 0.0

    def get_stats(self) -> RateLimitStats:
        """Get current rate limiting statistics."""
        with self._lock:
            now = time.time()
            self._cleanup_old_timestamps(now)

            return RateLimitStats(
                requests_this_minute=len(self._minute_requests),
                requests_this_hour=len(self._hour_requests),
                requests_today=len(self._day_requests),
                total_requests=self._total_requests,
                quota_remaining_daily=(
                    self._daily_quota_limit - self._daily_quota_used
                    if self._daily_quota_limit else None
                ),
                quota_remaining_monthly=(
                    self._monthly_quota_limit - self._monthly_quota_used
                    if self._monthly_quota_limit else None
                ),
                last_request_time=(
                    datetime.fromtimestamp(self._last_request_time)
                    if self._last_request_time else None
                ),
                next_allowed_time=(
                    datetime.fromtimestamp(now + self.get_wait_time())
                    if self.get_wait_time() > 0 else None
                )
            )

    def reset_quotas(self, daily: bool = True, monthly: bool = False) -> None:
        """Reset quota counters. Useful for testing or manual resets."""
        with self._lock:
            if daily:
                self._daily_quota_used = 0
                self._day_requests.clear()

            if monthly:
                self._monthly_quota_used = 0

    def update_quota_limits(
        self,
        daily_limit: Optional[int] = None,
        monthly_limit: Optional[int] = None
    ) -> None:
        """Update quota limits dynamically."""
        with self._lock:
            if daily_limit is not None:
                self._daily_quota_limit = daily_limit

            if monthly_limit is not None:
                self._monthly_quota_limit = monthly_limit
    def get_memory_usage(self) -> Dict[str, int]:
        """Get current memory usage statistics for optimization."""
        with self._lock:
            return {
                'minute_requests_count': len(self._minute_requests),
                'hour_requests_count': len(self._hour_requests),
                'day_requests_count': len(self._day_requests),
                'total_tracked_requests': (
                    len(self._minute_requests) +
                    len(self._hour_requests) +
                    len(self._day_requests)
                )
            }
    def optimize_memory(self) -> Dict[str, int]:
        """Optimize memory usage by cleaning up old data."""
        with self._lock:
            before_stats = self.get_memory_usage()

            # Force cleanup of all old timestamps
            now = time.time()
            self._cleanup_old_timestamps(now)

            after_stats = self.get_memory_usage()

            return {
                'requests_cleaned': (
                    before_stats['total_tracked_requests'] -
                    after_stats['total_tracked_requests']
                ),
                'memory_before': before_stats['total_tracked_requests'],
                'memory_after': after_stats['total_tracked_requests']
            }

    def _cleanup_old_timestamps(self, now: float) -> None:
        """Remove timestamps outside of tracking windows with optimized performance."""
        # Optimize: Use more efficient batch cleanup approach
        # Remove requests older than 1 minute
        if self._minute_requests:
            cutoff_time = now - 60.0
            while self._minute_requests and self._minute_requests[0] < cutoff_time:
                self._minute_requests.popleft()

        # Remove requests older than 1 hour
        if self._hour_requests:
            cutoff_time = now - 3600.0
            while self._hour_requests and self._hour_requests[0] < cutoff_time:
                self._hour_requests.popleft()

        # Remove requests older than 1 day
        if self._day_requests:
            cutoff_time = now - 86400.0
            while self._day_requests and self._day_requests[0] < cutoff_time:
                self._day_requests.popleft()


class AdaptiveRateLimiter(BaseRateLimiter):  # pylint: disable=too-many-instance-attributes
    """
    Rate limiter that adapts to API response patterns.
    Automatically adjusts rates based on 429 errors and server load.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._consecutive_429s = 0
        self._backoff_factor = 1.0
        self._max_backoff_factor = 10.0
        self._recovery_requests = 0
        self._recovery_threshold = 10

    def record_429_error(self) -> None:
        """Record a 429 (rate limit) error to trigger adaptive behavior."""
        with self._lock:
            self._consecutive_429s += 1
            self._backoff_factor = min(
                self._backoff_factor * 1.5,
                self._max_backoff_factor
            )
            self._recovery_requests = 0

    def record_successful_request(self) -> None:
        """Record successful request for rate limit recovery."""
        with self._lock:
            self.record_request()

            if self._consecutive_429s > 0:
                self._recovery_requests += 1

                # Recover from backoff after successful requests
                if self._recovery_requests >= self._recovery_threshold:
                    self._consecutive_429s = max(0, self._consecutive_429s - 1)
                    self._backoff_factor = max(1.0, self._backoff_factor * 0.8)
                    self._recovery_requests = 0

    def get_wait_time(self) -> float:
        """Get wait time including adaptive backoff."""
        base_wait = super().get_wait_time()
        return base_wait * self._backoff_factor

    def get_backoff_info(self) -> Dict[str, Any]:
        """Get information about current backoff state."""
        with self._lock:
            return {
                'consecutive_429s': self._consecutive_429s,
                'backoff_factor': self._backoff_factor,
                'recovery_requests': self._recovery_requests,
                'is_backing_off': self._backoff_factor > 1.0,
                'memory_usage': self.get_memory_usage()
            }
