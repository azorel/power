"""
OpenAI API configuration module.
Handles OpenAI-specific configuration with environment variable support.
"""

from typing import List
from shared.config.base_config import BaseAdapterConfig


class OpenAIConfig(BaseAdapterConfig):
    """Configuration for OpenAI API adapter."""

    def __init__(self):
        super().__init__('openai')

        # OpenAI-specific configuration (api_key, base_url, timeout, max_retries handled by base class)
        self.organization_id = self.get_optional('organization_id')
        self.project_id = self.get_optional('project_id')

        # Rate limiting (rate_limit_per_minute handled by base class)
        self.rate_limit_per_day = self.get_int('rate_limit_per_day', 200000)

        # Request configuration
        self.retry_delay = self.get_float('retry_delay', 1.0)

        # Model configuration
        self.default_model = self.get_optional('default_model', 'gpt-4o')
        self.default_max_tokens = self.get_int('default_max_tokens', 4096)
        self.default_temperature = self.get_float('default_temperature', 0.7)

        # Advanced features
        self.enable_streaming = self.get_bool('enable_streaming', True)
        self.enable_function_calling = self.get_bool('enable_function_calling', True)
        self.enable_vision = self.get_bool('enable_vision', True)
        self.enable_image_generation = self.get_bool('enable_image_generation', True)

        # Safety and moderation
        self.enable_moderation = self.get_bool('enable_moderation', True)
        self.moderate_input = self.get_bool('moderate_input', True)
        self.moderate_output = self.get_bool('moderate_output', False)

        # Caching configuration
        self.enable_response_cache = self.get_bool('enable_response_cache', True)
        self.cache_ttl_seconds = self.get_int('cache_ttl_seconds', 3600)
        self.max_cache_size = self.get_int('max_cache_size', 1000)

    def get_model_config(self, model_name: str) -> dict:
        """Get configuration for a specific model."""
        model_configs = {
            'gpt-4o': {
                'max_tokens': 4096,
                'supports_vision': True,
                'supports_functions': True,
                'cost_per_1k_input_tokens': 0.005,
                'cost_per_1k_output_tokens': 0.015
            },
            'gpt-4o-mini': {
                'max_tokens': 16384,
                'supports_vision': True,
                'supports_functions': True,
                'cost_per_1k_input_tokens': 0.00015,
                'cost_per_1k_output_tokens': 0.0006
            },
            'gpt-4-turbo': {
                'max_tokens': 4096,
                'supports_vision': True,
                'supports_functions': True,
                'cost_per_1k_input_tokens': 0.01,
                'cost_per_1k_output_tokens': 0.03
            },
            'gpt-3.5-turbo': {
                'max_tokens': 4096,
                'supports_vision': False,
                'supports_functions': True,
                'cost_per_1k_input_tokens': 0.0005,
                'cost_per_1k_output_tokens': 0.0015
            },
            'gpt-4': {
                'max_tokens': 8192,
                'supports_vision': False,
                'supports_functions': True,
                'cost_per_1k_input_tokens': 0.03,
                'cost_per_1k_output_tokens': 0.06
            },
            'dall-e-3': {
                'type': 'image_generation',
                'max_size': '1024x1024',
                'cost_per_image': 0.04
            },
            'dall-e-2': {
                'type': 'image_generation',
                'max_size': '1024x1024',
                'cost_per_image': 0.02
            }
        }

        return model_configs.get(model_name, {})

    def get_supported_models(self) -> List[str]:
        """Get list of supported models."""
        return [
            'gpt-4o',
            'gpt-4o-mini',
            'gpt-4-turbo',
            'gpt-4',
            'gpt-3.5-turbo',
            'dall-e-3',
            'dall-e-2'
        ]

    def validate(self) -> List[str]:
        """Validate OpenAI-specific configuration."""
        errors = super().validate()

        if not self.api_key or not str(self.api_key).startswith('sk-'):
            errors.append("OpenAI API key must start with 'sk-'")

        if self.rate_limit_per_minute <= 0:
            errors.append("rate_limit_per_minute must be positive")

        if self.rate_limit_per_day <= 0:
            errors.append("rate_limit_per_day must be positive")

        if self.default_max_tokens <= 0:
            errors.append("default_max_tokens must be positive")

        if not 0.0 <= self.default_temperature <= 2.0:
            errors.append("default_temperature must be between 0.0 and 2.0")

        if self.retry_delay < 0:
            errors.append("retry_delay cannot be negative")

        return errors

    def to_dict(self) -> dict:
        """Convert configuration to dictionary (excluding sensitive data)."""
        base_dict = super().to_dict()
        base_dict.update({
            'organization_id': self.organization_id,
            'project_id': self.project_id,
            'rate_limit_per_day': self.rate_limit_per_day,
            'retry_delay': self.retry_delay,
            'default_model': self.default_model,
            'default_max_tokens': self.default_max_tokens,
            'default_temperature': self.default_temperature,
            'enable_streaming': self.enable_streaming,
            'enable_function_calling': self.enable_function_calling,
            'enable_vision': self.enable_vision,
            'enable_image_generation': self.enable_image_generation,
            'enable_moderation': self.enable_moderation,
            'moderate_input': self.moderate_input,
            'moderate_output': self.moderate_output,
            'enable_response_cache': self.enable_response_cache,
            'cache_ttl_seconds': self.cache_ttl_seconds,
            'max_cache_size': self.max_cache_size,
            'supported_models': self.get_supported_models()
        })
        return base_dict
