"""
OpenAI API rate limiter and quota management.
Handles OpenAI-specific rate limits and usage tracking.
"""

import time
import threading
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from shared.utils.rate_limiter import BaseRateLimiter, AdaptiveRateLimiter, RateLimitStats
from shared.exceptions import RateLimitError, QuotaExceededError
from .config import OpenAIConfig


class OpenAIRateLimiter(AdaptiveRateLimiter):
    """
    OpenAI-specific rate limiter with tier-aware limits and token counting.
    Handles both request-based and token-based rate limiting.
    """

    def __init__(self, config: OpenAIConfig):
        """
        Initialize OpenAI rate limiter.
        
        Args:
            config: OpenAI configuration with rate limits
        """
        super().__init__(
            calls_per_minute=config.rate_limit_per_minute,
            calls_per_day=config.rate_limit_per_day,
            min_interval_seconds=1.0  # OpenAI requires some spacing
        )
        
        self.config = config
        
        # Token-based rate limiting (OpenAI measures both requests and tokens)
        self._token_limits = self._get_tier_token_limits()
        self._tokens_per_minute = 0
        self._tokens_per_day = 0
        self._token_minute_window = []
        self._token_day_window = []
        
        # Model-specific limits
        self._model_limits = self._get_model_limits()
        
        # Usage tracking for billing estimation
        self._estimated_cost_today = 0.0
        self._daily_cost_limit = config.get_float('daily_cost_limit', 100.0)
        
        # Advanced tracking
        self._request_sizes = []  # Track request sizes for optimization
        self._lock = threading.RLock()

    def can_make_request(
        self, 
        estimated_tokens: Optional[int] = None,
        model: Optional[str] = None
    ) -> bool:
        """
        Check if request can be made considering tokens and model limits.
        
        Args:
            estimated_tokens: Estimated tokens for this request
            model: Model to be used
            
        Returns:
            True if request is allowed
        """
        with self._lock:
            # Base rate limiting check
            if not super().can_make_request():
                return False
            
            # Token-based rate limiting
            if estimated_tokens and not self._can_use_tokens(estimated_tokens):
                return False
            
            # Model-specific limits
            if model and not self._check_model_limits(model):
                return False
            
            # Cost-based limiting
            if not self._check_cost_limits(estimated_tokens, model):
                return False
            
            return True

    def record_request(
        self, 
        tokens_used: Optional[int] = None,
        cost: Optional[float] = None,
        model: Optional[str] = None
    ) -> None:
        """
        Record completed request with token and cost tracking.
        
        Args:
            tokens_used: Actual tokens consumed
            cost: Actual cost incurred
            model: Model used
        """
        with self._lock:
            super().record_request()
            
            if tokens_used:
                self._record_token_usage(tokens_used)
            
            if cost:
                self._estimated_cost_today += cost
            
            if model:
                self._record_model_usage(model)
            
            # Track request size for optimization
            if tokens_used:
                self._request_sizes.append(tokens_used)
                # Keep only recent requests for analysis
                if len(self._request_sizes) > 100:
                    self._request_sizes = self._request_sizes[-50:]

    def get_wait_time_for_tokens(self, estimated_tokens: int) -> float:
        """
        Get wait time considering token limits.
        
        Args:
            estimated_tokens: Tokens needed
            
        Returns:
            Seconds to wait
        """
        with self._lock:
            base_wait = super().get_wait_time()
            token_wait = self._get_token_wait_time(estimated_tokens)
            
            return max(base_wait, token_wait)

    def get_openai_stats(self) -> Dict[str, Any]:
        """Get OpenAI-specific usage statistics."""
        with self._lock:
            base_stats = super().get_stats()
            
            return {
                **base_stats.to_dict(),
                'tokens_this_minute': self._tokens_per_minute,
                'tokens_this_day': self._tokens_per_day,
                'estimated_cost_today': self._estimated_cost_today,
                'average_request_size': (
                    sum(self._request_sizes) / len(self._request_sizes)
                    if self._request_sizes else 0
                ),
                'token_efficiency': self._calculate_token_efficiency(),
                'tier_limits': self._token_limits,
                'cost_utilization': (
                    self._estimated_cost_today / self._daily_cost_limit
                    if self._daily_cost_limit > 0 else 0
                )
            }

    def estimate_wait_time_for_request(
        self,
        prompt_tokens: int,
        max_completion_tokens: int,
        model: str = 'gpt-4o'
    ) -> float:
        """
        Estimate wait time for a specific request.
        
        Args:
            prompt_tokens: Input tokens
            max_completion_tokens: Expected output tokens
            model: Model to use
            
        Returns:
            Estimated wait time in seconds
        """
        total_tokens = prompt_tokens + max_completion_tokens
        
        return max(
            self.get_wait_time(),
            self.get_wait_time_for_tokens(total_tokens)
        )

    def optimize_for_throughput(self) -> Dict[str, Any]:
        """
        Analyze usage patterns and suggest optimizations.
        
        Returns:
            Dictionary with optimization suggestions
        """
        with self._lock:
            stats = self.get_openai_stats()
            suggestions = []
            
            # Analyze request size efficiency
            if self._request_sizes:
                avg_size = stats['average_request_size']
                if avg_size < 100:
                    suggestions.append("Consider batching small requests for better efficiency")
                elif avg_size > 4000:
                    suggestions.append("Large requests detected - consider splitting for better latency")
            
            # Check rate limit utilization
            if stats['requests_this_minute'] / self.calls_per_minute > 0.8:
                suggestions.append("High rate limit utilization - consider request queuing")
            
            # Cost optimization
            if stats['cost_utilization'] > 0.5:
                suggestions.append("High cost utilization - consider using smaller models for simple tasks")
            
            return {
                'current_stats': stats,
                'optimization_suggestions': suggestions,
                'efficiency_score': self._calculate_efficiency_score()
            }

    def _can_use_tokens(self, tokens: int) -> bool:
        """Check if token usage is within limits."""
        now = time.time()
        self._cleanup_token_windows(now)
        
        # Check per-minute token limit
        if (self._tokens_per_minute + tokens) > self._token_limits['per_minute']:
            return False
        
        # Check per-day token limit
        if (self._tokens_per_day + tokens) > self._token_limits['per_day']:
            return False
        
        return True

    def _record_token_usage(self, tokens: int) -> None:
        """Record token usage with time windows."""
        now = time.time()
        
        # Add to tracking windows
        self._token_minute_window.append((now, tokens))
        self._token_day_window.append((now, tokens))
        
        # Update counters
        self._tokens_per_minute += tokens
        self._tokens_per_day += tokens
        
        # Cleanup old entries
        self._cleanup_token_windows(now)

    def _cleanup_token_windows(self, now: float) -> None:
        """Clean up old token usage entries."""
        # Clean minute window
        minute_ago = now - 60
        while self._token_minute_window and self._token_minute_window[0][0] < minute_ago:
            removed_entry = self._token_minute_window.pop(0)
            self._tokens_per_minute -= removed_entry[1]
        
        # Clean day window
        day_ago = now - 86400
        while self._token_day_window and self._token_day_window[0][0] < day_ago:
            removed_entry = self._token_day_window.pop(0)
            self._tokens_per_day -= removed_entry[1]

    def _get_token_wait_time(self, tokens: int) -> float:
        """Calculate wait time based on token limits."""
        if not self._can_use_tokens(tokens):
            # Need to wait for oldest tokens to expire
            if self._token_minute_window:
                oldest_time = self._token_minute_window[0][0]
                return max(0, 60 - (time.time() - oldest_time))
        
        return 0.0

    def _check_model_limits(self, model: str) -> bool:
        """Check model-specific limits."""
        model_config = self._model_limits.get(model, {})
        
        # Check model-specific rate limits if configured
        if 'requests_per_minute' in model_config:
            # Would need separate tracking per model - simplified for now
            pass
        
        return True

    def _check_cost_limits(
        self, 
        estimated_tokens: Optional[int], 
        model: Optional[str]
    ) -> bool:
        """Check if request would exceed cost limits."""
        if not estimated_tokens or not model:
            return True
        
        # Estimate cost
        model_pricing = self._get_model_pricing(model)
        if not model_pricing:
            return True
        
        estimated_cost = (estimated_tokens / 1000) * model_pricing['completion_cost']
        
        return (self._estimated_cost_today + estimated_cost) <= self._daily_cost_limit

    def _record_model_usage(self, model: str) -> None:
        """Record usage for specific model."""
        # Simplified - could be expanded for per-model tracking
        pass

    def _get_tier_token_limits(self) -> Dict[str, int]:
        """Get token limits based on OpenAI tier."""
        # These are example limits - actual limits depend on your OpenAI tier
        return {
            'per_minute': 90000,  # Tier 2 example
            'per_day': 10000000,  # Daily limit
            'per_request': 4096   # Per-request limit
        }

    def _get_model_limits(self) -> Dict[str, Dict[str, Any]]:
        """Get model-specific limits."""
        return {
            'gpt-4o': {'max_tokens': 4096, 'context_length': 128000},
            'gpt-4o-mini': {'max_tokens': 16384, 'context_length': 128000},
            'gpt-4-turbo': {'max_tokens': 4096, 'context_length': 128000},
            'gpt-4': {'max_tokens': 8192, 'context_length': 8192},
            'gpt-3.5-turbo': {'max_tokens': 4096, 'context_length': 16385}
        }

    def _get_model_pricing(self, model: str) -> Optional[Dict[str, float]]:
        """Get pricing for model."""
        pricing = {
            'gpt-4o': {'prompt_cost': 0.005, 'completion_cost': 0.015},
            'gpt-4o-mini': {'prompt_cost': 0.00015, 'completion_cost': 0.0006},
            'gpt-4-turbo': {'prompt_cost': 0.01, 'completion_cost': 0.03},
            'gpt-4': {'prompt_cost': 0.03, 'completion_cost': 0.06},
            'gpt-3.5-turbo': {'prompt_cost': 0.0005, 'completion_cost': 0.0015}
        }
        
        return pricing.get(model)

    def _calculate_token_efficiency(self) -> float:
        """Calculate token usage efficiency score."""
        if not self._request_sizes:
            return 1.0
        
        # Efficiency based on average request size vs optimal ranges
        avg_size = sum(self._request_sizes) / len(self._request_sizes)
        
        # Optimal range is 500-2000 tokens
        if 500 <= avg_size <= 2000:
            return 1.0
        elif avg_size < 500:
            return avg_size / 500  # Penalty for too small
        else:
            return min(1.0, 2000 / avg_size)  # Penalty for too large

    def _calculate_efficiency_score(self) -> float:
        """Calculate overall efficiency score."""
        token_efficiency = self._calculate_token_efficiency()
        
        # Rate limit utilization (optimal is 60-80%)
        rate_utilization = self._total_requests / (self.calls_per_minute * 60) if self.calls_per_minute > 0 else 0
        rate_efficiency = 1.0 if 0.6 <= rate_utilization <= 0.8 else max(0.5, 1.0 - abs(rate_utilization - 0.7))
        
        # Cost efficiency (optimal is <50% of daily limit)
        cost_utilization = self._estimated_cost_today / self._daily_cost_limit if self._daily_cost_limit > 0 else 0
        cost_efficiency = max(0.5, 1.0 - cost_utilization)
        
        return (token_efficiency + rate_efficiency + cost_efficiency) / 3