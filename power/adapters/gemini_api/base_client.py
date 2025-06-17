"""
Base Gemini API client with core functionality and initialization.
"""

import logging
from typing import Dict, Any, Optional

from shared.utils.cache import ResponseCache
from shared.exceptions import LLMProviderError

from .config import GeminiConfig
from .rate_limiter import GeminiRateLimiter
from .data_mapper import GeminiDataMapper
from .exceptions import handle_gemini_exception

logger = logging.getLogger(__name__)


class GeminiBaseClient:
    """
    Base Gemini client with initialization and common functionality.
    """

    def __init__(self, config: Optional[GeminiConfig] = None):
        """
        Initialize Gemini base client.

        Args:
            config: Optional configuration (creates default if None)
        """
        self.config = config or GeminiConfig()
        self.rate_limiter = GeminiRateLimiter(self.config)
        self.data_mapper = GeminiDataMapper(self.config)

        # Initialize caching if enabled
        if self.config.enable_caching:
            self.cache = ResponseCache(
                max_size=self.config.cache_max_size,
                default_ttl_seconds=self.config.cache_ttl_seconds
            )
        else:
            self.cache = None

        # Initialize Google Gen AI client (lazy loaded) - NEW SDK 2024
        self._genai_client = None
        self._client_initialized = False

        # Statistics tracking
        self._stats = {
            'requests_made': 0,
            'cache_hits': 0,
            'errors': 0,
            'total_tokens': 0
        }

    def _get_genai_client(self):
        """Lazy load and configure Google Gen AI client - NEW SDK 2024."""
        if not self._client_initialized:
            try:
                from google import genai  # pylint: disable=import-outside-toplevel

                # Initialize client with API key - NEW SDK format
                self._genai_client = genai.Client(api_key=self.config.api_key)
                self._client_initialized = True

                logger.info("Initialized Gemini client with model: %s", self.config.model)

            except ImportError as e:
                raise LLMProviderError(
                    "google-genai package not installed. "
                    "Install with: pip install google-genai"
                ) from e
            except Exception as e:
                raise handle_gemini_exception(e, {
                    'operation': 'client_initialization',
                    'model': self.config.model
                }) from e

        return self._genai_client

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        return {
            'model': self.config.model,
            'provider': 'Google Gemini',
            'max_tokens': self.config.max_output_tokens,
            'temperature': self.config.temperature,
            'supports_streaming': True,
            'supports_functions': True,
            'supports_images': True
        }

    def validate_credentials(self) -> bool:
        """
        Validate API credentials.

        Returns:
            True if credentials are valid
        """
        try:
            client = self._get_genai_client()
            # Try a minimal operation to validate credentials
            # This is a placeholder - adjust based on actual SDK
            return client is not None
        except LLMProviderError as e:
            logger.warning("Credential validation failed: %s", e)
            return False

    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics.

        Returns:
            Dictionary containing usage stats
        """
        stats = self._stats.copy()

        # Add rate limiter stats if available
        if hasattr(self.rate_limiter, 'get_stats'):
            rate_stats = self.rate_limiter.get_stats()
            if hasattr(rate_stats, 'to_dict'):
                stats.update(rate_stats.to_dict())
            else:
                stats.update(rate_stats)

        # Add cache stats if caching is enabled
        if self.cache:
            cache_stats = self.cache.get_stats()
            stats.update({
                'cache_size': cache_stats.get('current_size', 0),  # pylint: disable=no-member
                'cache_max_size': cache_stats.get('max_size', 0),  # pylint: disable=no-member
                'cache_hit_rate': (
                    self._stats['cache_hits'] / max(1, self._stats['requests_made'])
                )
            })
        return stats

    @property
    def provider_name(self) -> str:
        """Get the provider name."""
        return "gemini"

    @property
    def supported_features(self) -> list:
        """Get list of supported features."""
        features = [
            "text_generation",
            "chat_completion",
            "image_input",
            "safety_filtering",
            "response_caching",
            "function_calling",
            "multimodal",
            "system_instructions"
        ]

        # Add streaming only if enabled in config
        if getattr(self.config, 'enable_streaming', True):
            features.append("streaming")

        return features

    def get_advanced_capabilities(self) -> Dict[str, bool]:
        """
        Get advanced capabilities of the client.

        Returns:
            Dictionary of capability flags
        """
        return {
            'streaming': True,
            'function_calling': True,
            'image_processing': True,
            'chat_completion': True,
            'system_instructions': True,
            'multimodal': True,
            'batch_processing': False,  # Not implemented yet
            'fine_tuning': False,  # Not available in API
            'embeddings': False,  # Different API endpoint
            'audio_processing': False,  # Not implemented yet
            'video_processing': False,  # Not implemented yet
        }
