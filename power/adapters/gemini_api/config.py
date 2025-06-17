"""
Gemini API adapter configuration.
Handles environment variables and settings specific to Google Generative AI.
"""

from typing import List, Dict, Any
from shared.config.base_config import BaseAdapterConfig
from shared.exceptions import MissingConfigurationError, InvalidConfigurationError


class GeminiConfig(BaseAdapterConfig):  # pylint: disable=too-many-instance-attributes
    """Configuration class for Gemini API adapter."""

    def __init__(self):
        """Initialize Gemini configuration."""
        super().__init__('gemini')

        # API Configuration - validate that API key exists
        try:
            api_key = self.get_required('api_key')
            # Store it in the base config
            self._config.api_key = api_key
        except ValueError as e:
            raise MissingConfigurationError(
                "GEMINI_API_KEY environment variable is required",
                config_key='api_key'
            ) from e

        # Model Configuration - Updated for new Google Gen AI SDK 2024
        self.model = self.get_optional('model', 'gemini-2.0-flash')
        self.vision_model = self.get_optional('vision_model', 'gemini-2.0-flash')

        # Advanced Model Configuration
        self.image_generation_model = self.get_optional(
            'image_generation_model',
            'gemini-2.0-flash-exp-image-generation'
        )
        self.function_calling_model = self.get_optional(
            'function_calling_model', 'gemini-2.0-flash'
        )
        self.simple_model = self.get_optional('simple_model', 'gemini-1.5-flash')
        self.complex_model = self.get_optional(
            'complex_model', 'gemini-2.5-pro-exp-03-25'
        )
        self.thinking_model = self.get_optional(
            'thinking_model', 'gemini-2.0-flash-thinking-exp'
        )

        # API Endpoints - store in base config
        base_url = self.get_optional(
            'base_url',
            'https://generativelanguage.googleapis.com'
        )
        self._config.base_url = base_url

        # Request Configuration - store in base config
        timeout = self.get_int('timeout', 30)
        max_retries = self.get_int('max_retries', 3)
        self._config.timeout = timeout
        self._config.max_retries = max_retries
        self.retry_delay = self.get_float('retry_delay', 1.0)

        # Rate Limiting - store in base config
        rate_limit_per_minute = self.get_int('rate_limit_per_minute', 60)
        daily_quota = self.get_int('daily_quota', 1000)
        self._config.rate_limit_per_minute = rate_limit_per_minute
        self._config.daily_quota = daily_quota

        # Store additional rate limiting for Gemini
        self.rate_limit_per_hour = self.get_int('rate_limit_per_hour', 1000)

        # Response Configuration
        self.default_max_tokens = self.get_int('default_max_tokens', 1000)
        self.default_temperature = self.get_float('default_temperature', 0.7)
        self.default_top_p = self.get_float('default_top_p', 0.9)
        self.default_top_k = self.get_int('default_top_k', 40)

        # Caching Configuration
        self.enable_caching = self.get_bool('enable_caching', True)
        self.cache_ttl_seconds = self.get_int('cache_ttl_seconds', 3600)
        self.cache_max_size = self.get_int('cache_max_size', 1000)

        # Safety and Content Configuration
        self.safety_threshold = self.get_optional(
            'safety_threshold', 'BLOCK_MEDIUM_AND_ABOVE'
        )
        self.enable_safety_filtering = self.get_bool('enable_safety_filtering', True)

        # Advanced Safety Configuration
        self.harassment_threshold = self.get_optional(
            'harassment_threshold', 'BLOCK_MEDIUM_AND_ABOVE'
        )
        self.hate_speech_threshold = self.get_optional(
            'hate_speech_threshold', 'BLOCK_MEDIUM_AND_ABOVE'
        )
        self.sexually_explicit_threshold = self.get_optional(
            'sexually_explicit_threshold', 'BLOCK_MEDIUM_AND_ABOVE'
        )
        self.dangerous_content_threshold = self.get_optional(
            'dangerous_content_threshold', 'BLOCK_MEDIUM_AND_ABOVE'
        )

        # Advanced Feature Configuration
        self.enable_function_calling = self.get_bool('enable_function_calling', True)
        self.enable_image_generation = self.get_bool('enable_image_generation', True)
        self.enable_system_instructions = self.get_bool('enable_system_instructions', True)
        self.enable_advanced_models = self.get_bool('enable_advanced_models', True)

        # Multimodal Configuration
        self.max_image_size_mb = self.get_int('max_image_size_mb', 20)
        self.supported_image_formats = self._parse_list(
            self.get_optional('supported_image_formats', 'jpeg,png,webp,heic,heif')
        )

        # Advanced Configuration
        self.enable_streaming = self.get_bool('enable_streaming', True)
        self.min_request_interval = self.get_float('min_request_interval', 0.0)

        # Validate configuration
        self._validate_config()

    def _parse_list(self, value: str) -> List[str]:
        """Parse comma-separated string into list."""
        if not value:
            return []
        return [item.strip().lower() for item in value.split(',')]

    def _validate_config(self) -> None:
        """Validate configuration values."""
        errors = []

        # Use validator methods to reduce complexity
        errors.extend(self._validate_api_key())
        errors.extend(self._validate_models())
        errors.extend(self._validate_numeric_ranges())
        errors.extend(self._validate_rate_limits())
        errors.extend(self._validate_timeout_settings())
        errors.extend(self._validate_safety_settings())
        errors.extend(self._validate_image_settings())

        if errors:
            raise InvalidConfigurationError(
                f"Configuration validation failed: {'; '.join(errors)}"
            )

    def _validate_api_key(self) -> List[str]:
        """Validate API key format."""
        errors = []
        if not self.api_key or len(self.api_key) < 5:
            errors.append("API key appears to be invalid or too short")
        return errors

    def _validate_models(self) -> List[str]:
        """Validate all model configurations."""
        errors = []
        valid_models = [
            'gemini-2.0-flash', 'gemini-1.5-pro', 'gemini-1.5-flash',
            'gemini-1.0-pro', 'gemini-pro', 'gemini-pro-vision',
            'gemini-2.5-pro-exp-03-25', 'gemini-2.0-flash-thinking-exp',
            'gemini-2.0-flash-exp-image-generation'
        ]

        models_to_validate = [
            ('model', self.model),
            ('image_generation_model', self.image_generation_model),
            ('function_calling_model', self.function_calling_model),
            ('simple_model', self.simple_model),
            ('complex_model', self.complex_model),
            ('thinking_model', self.thinking_model)
        ]

        for model_name, model_value in models_to_validate:
            if model_value not in valid_models:
                errors.append(f"{model_name} '{model_value}' not in supported models")

        return errors

    def _validate_numeric_ranges(self) -> List[str]:
        """Validate numeric parameter ranges."""
        errors = []

        numeric_validations = [
            ('default_temperature', self.default_temperature, 0.0, 2.0, 'between 0.0 and 2.0'),
            ('default_top_p', self.default_top_p, 0.0, 1.0, 'between 0.0 and 1.0')
        ]

        for name, value, min_val, max_val, description in numeric_validations:
            if not min_val <= value <= max_val:
                errors.append(f"{name} must be {description}")

        positive_validations = [
            ('default_top_k', self.default_top_k),
            ('default_max_tokens', self.default_max_tokens)
        ]

        for name, value in positive_validations:
            if value <= 0:
                errors.append(f"{name} must be positive")

        return errors

    def _validate_rate_limits(self) -> List[str]:
        """Validate rate limit settings."""
        errors = []

        rate_limit_fields = [
            ('rate_limit_per_minute', self.rate_limit_per_minute),
            ('rate_limit_per_hour', self.rate_limit_per_hour),
            ('daily_quota', self.daily_quota)
        ]

        for name, value in rate_limit_fields:
            if value <= 0:
                errors.append(f"{name} must be positive")

        return errors

    def _validate_timeout_settings(self) -> List[str]:
        """Validate timeout and retry settings."""
        errors = []

        if self.timeout <= 0:
            errors.append("timeout must be positive")

        if self.max_retries < 0:
            errors.append("max_retries cannot be negative")

        if self.retry_delay < 0:
            errors.append("retry_delay cannot be negative")

        return errors

    def _validate_safety_settings(self) -> List[str]:
        """Validate safety threshold settings."""
        errors = []

        valid_thresholds = [
            'BLOCK_NONE', 'BLOCK_ONLY_HIGH', 'BLOCK_MEDIUM_AND_ABOVE',
            'BLOCK_LOW_AND_ABOVE'
        ]

        if self.safety_threshold not in valid_thresholds:
            errors.append(f"safety_threshold must be one of: {valid_thresholds}")

        return errors

    def _validate_image_settings(self) -> List[str]:
        """Validate image-related settings."""
        errors = []

        if self.max_image_size_mb <= 0:
            errors.append("max_image_size_mb must be positive")

        if not self.supported_image_formats:
            errors.append("supported_image_formats cannot be empty")

        return errors

    def get_generation_config(self) -> Dict[str, Any]:
        """Get generation configuration for API calls."""
        return {
            'max_output_tokens': self.default_max_tokens,
            'temperature': self.default_temperature,
            'top_p': self.default_top_p,
            'top_k': self.default_top_k
        }

    def get_safety_settings(self) -> List[Dict[str, str]]:
        """Get safety settings for API calls."""
        if not self.enable_safety_filtering:
            return []

        # Gemini safety categories with individual thresholds
        safety_config = [
            {
                'category': 'HARM_CATEGORY_HARASSMENT',
                'threshold': self.harassment_threshold
            },
            {
                'category': 'HARM_CATEGORY_HATE_SPEECH',
                'threshold': self.hate_speech_threshold
            },
            {
                'category': 'HARM_CATEGORY_SEXUALLY_EXPLICIT',
                'threshold': self.sexually_explicit_threshold
            },
            {
                'category': 'HARM_CATEGORY_DANGEROUS_CONTENT',
                'threshold': self.dangerous_content_threshold
            }
        ]

        return safety_config

    def get_advanced_safety_settings(self) -> Dict[str, Any]:
        """Get advanced safety configuration with fine-grained control."""
        return {
            'harassment': {
                'threshold': self.harassment_threshold,
                'enabled': self.enable_safety_filtering
            },
            'hate_speech': {
                'threshold': self.hate_speech_threshold,
                'enabled': self.enable_safety_filtering
            },
            'sexually_explicit': {
                'threshold': self.sexually_explicit_threshold,
                'enabled': self.enable_safety_filtering
            },
            'dangerous_content': {
                'threshold': self.dangerous_content_threshold,
                'enabled': self.enable_safety_filtering
            }
        }

    def supports_image_generation(self) -> bool:
        """Check if image generation is supported and enabled."""
        return (
            self.enable_image_generation and
            'image-generation' in self.image_generation_model
        )

    def supports_function_calling(self) -> bool:
        """Check if function calling is supported and enabled."""
        return self.enable_function_calling

    def supports_system_instructions(self) -> bool:
        """Check if system instructions are supported and enabled."""
        return self.enable_system_instructions

    def get_image_generation_model(self) -> str:
        """Get the model for image generation tasks."""
        return self.image_generation_model

    def get_function_calling_model(self) -> str:
        """Get the model for function calling tasks."""
        return self.function_calling_model

    def get_simple_model(self) -> str:
        """Get the model for simple tasks."""
        return self.simple_model

    def get_complex_model(self) -> str:
        """Get the model for complex tasks."""
        return self.complex_model

    def get_thinking_model(self) -> str:
        """Get the model for reasoning/thinking tasks."""
        return self.thinking_model

    def is_vision_supported(self) -> bool:
        """Check if current model supports vision/multimodal input."""
        return (
            'vision' in self.model.lower() or
            '1.5' in self.model or
            '2.0' in self.model
        )

    def get_model_for_request(self, has_images: bool = False) -> str:
        """Get appropriate model based on request type."""
        if has_images and not self.is_vision_supported():
            return self.vision_model
        return self.model

    def is_image_format_supported(self, format_name: str) -> bool:
        """Check if image format is supported."""
        return format_name.lower() in self.supported_image_formats

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary (excluding sensitive data)."""
        base_dict = super().to_dict()

        gemini_dict = {
            'model': self.model,
            'vision_model': self.vision_model,
            'image_generation_model': self.image_generation_model,
            'function_calling_model': self.function_calling_model,
            'simple_model': self.simple_model,
            'complex_model': self.complex_model,
            'thinking_model': self.thinking_model,
            'base_url': self.base_url,
            'timeout': self.timeout,
            'max_retries': self.max_retries,
            'retry_delay': self.retry_delay,
            'rate_limit_per_minute': self.rate_limit_per_minute,
            'rate_limit_per_hour': self.rate_limit_per_hour,
            'daily_quota': self.daily_quota,
            'default_max_tokens': self.default_max_tokens,
            'default_temperature': self.default_temperature,
            'default_top_p': self.default_top_p,
            'default_top_k': self.default_top_k,
            'enable_caching': self.enable_caching,
            'cache_ttl_seconds': self.cache_ttl_seconds,
            'cache_max_size': self.cache_max_size,
            'safety_threshold': self.safety_threshold,
            'enable_safety_filtering': self.enable_safety_filtering,
            'harassment_threshold': self.harassment_threshold,
            'hate_speech_threshold': self.hate_speech_threshold,
            'sexually_explicit_threshold': self.sexually_explicit_threshold,
            'dangerous_content_threshold': self.dangerous_content_threshold,
            'enable_function_calling': self.enable_function_calling,
            'enable_image_generation': self.enable_image_generation,
            'enable_system_instructions': self.enable_system_instructions,
            'enable_advanced_models': self.enable_advanced_models,
            'max_image_size_mb': self.max_image_size_mb,
            'supported_image_formats': self.supported_image_formats,
            'enable_streaming': self.enable_streaming,
            'min_request_interval': self.min_request_interval,
            'is_vision_supported': self.is_vision_supported(),
            'supports_image_generation': self.supports_image_generation(),
            'supports_function_calling': self.supports_function_calling(),
            'supports_system_instructions': self.supports_system_instructions()
        }

        return {**base_dict, **gemini_dict}

    @property
    def rate_limit_per_minute(self) -> int:
        """Get rate limit per minute from base config."""
        return self._config.rate_limit_per_minute

    @property
    def daily_quota(self) -> int:
        """Get daily quota from base config."""
        return self._config.daily_quota

    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        try:
            self._validate_config()
            return []
        except InvalidConfigurationError as e:
            return [e.message]
