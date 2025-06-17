"""
Base OpenAI client with common functionality.
Provides shared utilities for all OpenAI client implementations.
"""

import openai
import time
import logging
from typing import Dict, Any, Optional, Union
from datetime import datetime

from .config import OpenAIConfig
from .rate_limiter import OpenAIRateLimiter
from .exceptions import OpenAIExceptionMapper, is_retriable_openai_error, get_retry_delay_for_openai_error
from shared.exceptions import LLMProviderError, AuthenticationError, RateLimitError
from shared.utils.cache import ResponseCache


class BaseOpenAIClient:
    """
    Base client for OpenAI API interactions.
    Provides common functionality for authentication, rate limiting, caching, and error handling.
    """

    def __init__(self, config: Optional[OpenAIConfig] = None):
        """
        Initialize base OpenAI client.
        
        Args:
            config: OpenAI configuration (creates default if None)
        """
        self.config = config or OpenAIConfig()
        self.rate_limiter = OpenAIRateLimiter(self.config)
        self.logger = logging.getLogger(f'openai_adapter.{self.__class__.__name__}')
        
        # Initialize OpenAI client
        self._init_openai_client()
        
        # Setup caching if enabled
        self.cache = None
        if self.config.enable_response_cache:
            self.cache = ResponseCache(
                default_ttl_seconds=self.config.cache_ttl_seconds,
                max_size=self.config.max_cache_size
            )
        
        # Request tracking
        self._request_count = 0
        self._total_tokens_used = 0
        self._total_cost = 0.0
        
        # Validation
        self._validate_configuration()

    def _init_openai_client(self) -> None:
        """Initialize the OpenAI client with configuration."""
        client_params = {
            'api_key': self.config.api_key,
            'base_url': self.config.base_url,
            'timeout': self.config.timeout,
            'max_retries': 0,  # We handle retries ourselves
        }
        
        # Add organization if provided
        if self.config.organization_id:
            client_params['organization'] = self.config.organization_id
        
        # Add project if provided  
        if self.config.project_id:
            client_params['project'] = self.config.project_id
        
        try:
            self.client = openai.OpenAI(**client_params)
            self.logger.info("OpenAI client initialized successfully")
        except Exception as e:
            error_msg = f"Failed to initialize OpenAI client: {e}"
            self.logger.error(error_msg)
            raise AuthenticationError(error_msg)

    def _validate_configuration(self) -> None:
        """Validate the configuration."""
        validation_errors = self.config.validate()
        if validation_errors:
            error_msg = f"OpenAI configuration validation failed: {', '.join(validation_errors)}"
            self.logger.error(error_msg)
            raise LLMProviderError(error_msg)

    @OpenAIExceptionMapper.handle_openai_error
    def _make_api_call(
        self,
        api_method,
        request_data: Dict[str, Any],
        estimated_tokens: Optional[int] = None,
        cache_key: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make an API call with rate limiting, caching, and error handling.
        
        Args:
            api_method: OpenAI API method to call
            request_data: Request data dictionary
            estimated_tokens: Estimated tokens for rate limiting
            cache_key: Cache key for response caching
            **kwargs: Additional parameters
            
        Returns:
            API response data
        """
        # Check cache first
        if cache_key and self.cache:
            cached_response = self.cache.get(cache_key)
            if cached_response:
                self.logger.debug(f"Cache hit for key: {cache_key}")
                return cached_response
        
        # Check rate limits
        model = request_data.get('model', self.config.default_model)
        if not self.rate_limiter.can_make_request(estimated_tokens, model):
            wait_time = self.rate_limiter.get_wait_time_for_tokens(estimated_tokens or 0)
            raise RateLimitError(
                f"Rate limit would be exceeded. Wait {wait_time:.1f} seconds.",
                retry_after=int(wait_time)
            )
        
        # Make the API call with retries
        response = self._make_request_with_retries(api_method, request_data, **kwargs)
        
        # Record usage
        self._record_request_usage(response, estimated_tokens, model)
        
        # Cache response if applicable
        if cache_key and self.cache and not request_data.get('stream', False):
            self.cache.set(cache_key, response)
            self.logger.debug(f"Cached response for key: {cache_key}")
        
        return response

    def _make_request_with_retries(
        self,
        api_method,
        request_data: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make API request with retry logic.
        
        Args:
            api_method: OpenAI API method
            request_data: Request data
            **kwargs: Additional parameters
            
        Returns:
            API response
        """
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                start_time = time.time()
                
                self.logger.debug(f"Making OpenAI API call (attempt {attempt + 1})")
                
                # Make the actual API call
                response = api_method(**request_data, **kwargs)
                
                # Convert to dict if needed
                if hasattr(response, 'model_dump'):
                    response_dict = response.model_dump()
                elif hasattr(response, 'to_dict'):
                    response_dict = response.to_dict()
                else:
                    response_dict = dict(response)
                
                # Add timing information
                latency_ms = int((time.time() - start_time) * 1000)
                response_dict['_latency_ms'] = latency_ms
                
                self.logger.info(f"OpenAI API call successful in {latency_ms}ms")
                return response_dict
                
            except Exception as e:
                last_exception = e
                
                # Check if error is retriable
                if not is_retriable_openai_error(e) or attempt >= self.config.max_retries:
                    break
                
                # Calculate retry delay
                retry_delay = get_retry_delay_for_openai_error(e)
                retry_delay = max(retry_delay, self.config.retry_delay * (2 ** attempt))
                
                self.logger.warning(
                    f"OpenAI API call failed (attempt {attempt + 1}), "
                    f"retrying in {retry_delay}s: {e}"
                )
                
                # Update rate limiter if it's a 429 error
                if isinstance(e, openai.RateLimitError):
                    self.rate_limiter.record_429_error()
                
                time.sleep(retry_delay)
        
        # All retries exhausted
        if last_exception:
            raise OpenAIExceptionMapper.translate_openai_exception(last_exception)
        else:
            raise LLMProviderError("All retry attempts failed")

    def _record_request_usage(
        self,
        response: Dict[str, Any],
        estimated_tokens: Optional[int],
        model: str
    ) -> None:
        """
        Record request usage for tracking and rate limiting.
        
        Args:
            response: API response
            estimated_tokens: Estimated tokens
            model: Model used
        """
        self._request_count += 1
        
        # Extract actual usage from response
        usage = response.get('usage', {})
        total_tokens = usage.get('total_tokens', estimated_tokens or 0)
        
        # Calculate cost
        cost = self._calculate_request_cost(usage, model)
        
        # Update totals
        if total_tokens:
            self._total_tokens_used += total_tokens
        if cost:
            self._total_cost += cost
        
        # Record in rate limiter
        self.rate_limiter.record_request(
            tokens_used=total_tokens,
            cost=cost,
            model=model
        )
        
        self.logger.debug(
            f"Recorded usage: {total_tokens} tokens, ${cost:.6f} cost, model: {model}"
        )

    def _calculate_request_cost(self, usage: Dict[str, Any], model: str) -> float:
        """
        Calculate cost for a request.
        
        Args:
            usage: Usage data from API response
            model: Model used
            
        Returns:
            Estimated cost in USD
        """
        model_config = self.config.get_model_config(model)
        if not model_config:
            return 0.0
        
        prompt_tokens = usage.get('prompt_tokens', 0)
        completion_tokens = usage.get('completion_tokens', 0)
        
        prompt_cost = (prompt_tokens / 1000) * model_config.get('cost_per_1k_input_tokens', 0)
        completion_cost = (completion_tokens / 1000) * model_config.get('cost_per_1k_output_tokens', 0)
        
        return prompt_cost + completion_cost

    def _generate_cache_key(self, request_data: Dict[str, Any]) -> str:
        """
        Generate cache key for request.
        
        Args:
            request_data: Request data
            
        Returns:
            Cache key string
        """
        # Create key from relevant request parameters
        key_parts = [
            request_data.get('model', ''),
            str(request_data.get('temperature', '')),
            str(request_data.get('max_tokens', '')),
        ]
        
        # Add prompt or messages
        if 'prompt' in request_data:
            key_parts.append(str(hash(request_data['prompt'])))
        elif 'messages' in request_data:
            messages_str = str(request_data['messages'])
            key_parts.append(str(hash(messages_str)))
        
        return 'openai:' + ':'.join(filter(None, key_parts))

    def get_client_stats(self) -> Dict[str, Any]:
        """Get client usage statistics."""
        rate_limit_stats = self.rate_limiter.get_openai_stats()
        
        return {
            'requests_made': self._request_count,
            'total_tokens_used': self._total_tokens_used,
            'total_cost_usd': self._total_cost,
            'average_tokens_per_request': (
                self._total_tokens_used / self._request_count
                if self._request_count > 0 else 0
            ),
            'average_cost_per_request': (
                self._total_cost / self._request_count
                if self._request_count > 0 else 0
            ),
            'rate_limit_stats': rate_limit_stats,
            'cache_stats': self.cache.get_stats() if self.cache else None,
            'configuration': self.config.to_dict()
        }

    def validate_credentials(self) -> bool:
        """
        Validate API credentials without making a generation request.
        
        Returns:
            True if credentials are valid
        """
        try:
            # Make a minimal API call to validate credentials
            response = self.client.models.list()
            self.logger.info("OpenAI credentials validated successfully")
            return True
        except Exception as e:
            self.logger.error(f"OpenAI credential validation failed: {e}")
            return False

    def get_available_models(self) -> list:
        """
        Get list of available models from OpenAI.
        
        Returns:
            List of available model names
        """
        try:
            response = self.client.models.list()
            models = [model.id for model in response.data]
            self.logger.info(f"Retrieved {len(models)} available models")
            return models
        except Exception as e:
            self.logger.error(f"Failed to retrieve available models: {e}")
            raise OpenAIExceptionMapper.translate_openai_exception(e)

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text (rough approximation).
        
        Args:
            text: Input text
            
        Returns:
            Estimated token count
        """
        # Rough estimation: ~4 characters per token for English
        return max(1, len(text) // 4)

    def close(self) -> None:
        """Clean up resources."""
        if self.cache:
            self.cache.clear()
        
        self.logger.info("OpenAI client resources cleaned up")