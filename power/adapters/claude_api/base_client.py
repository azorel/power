"""
Claude API base client module.
Base functionality for Claude API interactions with hybrid reasoning support.
"""

import asyncio
import time
from typing import Optional, Dict, Any, List, Union, AsyncGenerator
from abc import ABC, abstractmethod

from .config import ClaudeConfig
from .exceptions import (
    ClaudeAPIError, ClaudeRateLimitError, ClaudeConnectionError,
    ClaudeTimeoutError, ClaudeHybridReasoningError, handle_claude_api_error
)
from shared.utils.rate_limiter import BaseRateLimiter
from shared.utils.cache import ResponseCache


class ClaudeBaseClient(ABC):
    """Base client for Claude API interactions."""

    def __init__(self, config: ClaudeConfig):
        self.config = config
        self.rate_limiter = BaseRateLimiter(
            calls_per_minute=config.rate_limit_per_minute,
            calls_per_hour=config.rate_limit_per_hour,
            calls_per_day=config.rate_limit_per_day
        )
        
        if config.enable_response_cache:
            self.cache = ResponseCache(
                max_size=config.max_cache_size,
                ttl_seconds=config.cache_ttl_seconds
            )
        else:
            self.cache = None

        self._session = None
        self._last_request_time = 0
        self._request_count = 0

    @abstractmethod
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Make HTTP request to Claude API."""
        pass

    async def _handle_rate_limiting(self) -> None:
        """Handle rate limiting with exponential backoff."""
        if not self.rate_limiter.can_make_request():
            wait_time = self.rate_limiter.get_wait_time()
            if wait_time > 0:
                await asyncio.sleep(wait_time)

        # Additional delay between requests
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < self.config.retry_delay:
            await asyncio.sleep(self.config.retry_delay - time_since_last)

        self._last_request_time = time.time()

    def _prepare_hybrid_reasoning_params(
        self, 
        reasoning_mode: Optional[str] = None,
        reasoning_depth: Optional[int] = None,
        enable_step_by_step: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Prepare hybrid reasoning parameters for requests."""
        if not self.config.enable_hybrid_reasoning:
            return {}

        reasoning_config = self.config.get_hybrid_reasoning_config()
        
        params = {
            'hybrid_reasoning': {
                'enabled': True,
                'mode': reasoning_mode or reasoning_config['mode'],
                'depth': reasoning_depth or reasoning_config['depth'],
                'step_by_step': enable_step_by_step if enable_step_by_step is not None else reasoning_config['step_by_step'],
                'capabilities': reasoning_config['capabilities']
            }
        }

        # Adjust model parameters based on reasoning mode
        mode = params['hybrid_reasoning']['mode']
        if mode == 'analytical':
            params['temperature'] = min(self.config.default_temperature, 0.3)
            params['top_p'] = 0.9
        elif mode == 'creative':
            params['temperature'] = max(self.config.default_temperature, 0.8)
            params['top_p'] = 0.95
        else:  # balanced
            params['temperature'] = self.config.default_temperature
            params['top_p'] = self.config.default_top_p

        return params

    def _prepare_context_management_params(self, context_tokens: Optional[int] = None) -> Dict[str, Any]:
        """Prepare context management parameters for 64K token handling."""
        params = {
            'max_tokens': min(
                self.config.default_max_tokens,
                context_tokens or self.config.max_context_tokens
            ),
            'context_window_management': self.config.context_window_management,
            'context_preservation_ratio': self.config.context_preservation_ratio
        }

        # Enable smart context windowing for large contexts
        if params['max_tokens'] > 32768:
            params['enable_smart_windowing'] = True
            params['priority_sections'] = ['system', 'recent_messages', 'tool_results']

        return params

    def _get_cache_key(self, request_data: Dict[str, Any]) -> str:
        """Generate cache key for request."""
        if not self.cache:
            return ""

        # Create deterministic cache key from request parameters
        import hashlib
        import json
        
        # Remove non-deterministic fields
        cache_data = request_data.copy()
        cache_data.pop('timestamp', None)
        cache_data.pop('request_id', None)
        
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()

    async def _get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached response if available."""
        if not self.cache or not cache_key:
            return None
        return self.cache.get(cache_key)

    async def _cache_response(self, cache_key: str, response: Dict[str, Any]) -> None:
        """Cache response if caching is enabled."""
        if self.cache and cache_key:
            self.cache.set(cache_key, response)

    def _validate_model_compatibility(self, model_name: str, features: List[str]) -> None:
        """Validate that the model supports requested features."""
        model_config = self.config.get_model_config(model_name)
        if not model_config:
            raise ClaudeAPIError(f"Unknown model: {model_name}")

        # Check feature compatibility
        for feature in features:
            feature_key = f"supports_{feature}"
            if feature_key in model_config and not model_config[feature_key]:
                raise ClaudeAPIError(f"Model {model_name} does not support {feature}")

    def _prepare_request_headers(self) -> Dict[str, str]:
        """Prepare headers for API requests."""
        headers = {
            'Authorization': f'Bearer {self.config.api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'PowerBuilder-Claude-Client/1.0.0',
            'X-API-Version': '2024-03-01'  # Latest API version
        }

        if self.config.organization_id:
            headers['X-Organization-ID'] = self.config.organization_id
        if self.config.workspace_id:
            headers['X-Workspace-ID'] = self.config.workspace_id

        return headers

    async def _retry_request(
        self,
        request_func,
        max_retries: Optional[int] = None,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """Retry request with exponential backoff."""
        max_retries = max_retries or self.config.max_retries_per_request
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                return await request_func(*args, **kwargs)
            except ClaudeRateLimitError as e:
                if attempt == max_retries:
                    raise
                
                # Wait for rate limit reset
                wait_time = e.retry_after or (2 ** attempt * self.config.retry_delay)
                await asyncio.sleep(wait_time)
                last_exception = e
                
            except (ClaudeConnectionError, ClaudeTimeoutError) as e:
                if attempt == max_retries:
                    raise
                
                # Exponential backoff for connection issues
                wait_time = 2 ** attempt * self.config.retry_delay
                await asyncio.sleep(wait_time)
                last_exception = e
                
            except ClaudeAPIError as e:
                # Don't retry on authentication, validation, or content filter errors
                if e.error_type in ['authentication_error', 'validation_error', 'content_filter_error']:
                    raise
                
                if attempt == max_retries:
                    raise
                
                last_exception = e
                await asyncio.sleep(self.config.retry_delay)

        # This should never be reached, but just in case
        if last_exception:
            raise last_exception
        raise ClaudeAPIError("Request failed after all retry attempts")

    async def get_model_info(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Get information about a specific model or all supported models."""
        model_name = model_name or self.config.default_model
        
        if model_name:
            model_config = self.config.get_model_config(model_name)
            if not model_config:
                raise ClaudeAPIError(f"Unknown model: {model_name}")
            return model_config
        else:
            return {
                'supported_models': self.config.get_supported_models(),
                'default_model': self.config.default_model,
                'hybrid_reasoning_enabled': self.config.enable_hybrid_reasoning
            }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of the Claude API connection."""
        try:
            # Simple API call to check connectivity
            response = await self._make_request('GET', '/v1/models')
            return {
                'status': 'healthy',
                'api_version': response.get('api_version', 'unknown'),
                'rate_limit_stats': self.rate_limiter.get_stats().to_dict(),
                'timestamp': time.time()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': time.time()
            }

    async def close(self) -> None:
        """Clean up resources."""
        if self._session:
            await self._session.close()
        if self.cache:
            self.cache.clear()