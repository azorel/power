"""
Tests for Gemini API adapter configuration.
"""

import pytest
import os
from unittest.mock import patch

from adapters.gemini_api.config import GeminiConfig
from shared.exceptions import MissingConfigurationError, InvalidConfigurationError


class TestGeminiConfig:
    """Test cases for GeminiConfig class."""

    def test_config_with_valid_api_key(self):
        """Test configuration with valid API key."""
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test_api_key_12345'}):
            config = GeminiConfig()
            assert config.api_key == 'test_api_key_12345'
            assert config.model == 'gemini-2.0-flash'
            assert config.timeout == 30
            assert config.rate_limit_per_minute == 10  # Test environment sets this to 10

    def test_config_missing_api_key(self):
        """Test configuration fails without API key."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(MissingConfigurationError) as exc_info:
                GeminiConfig()

            assert 'GEMINI_API_KEY' in str(exc_info.value)
            assert exc_info.value.config_key == 'api_key'

    def test_config_custom_values(self):
        """Test configuration with custom environment variables."""
        env_vars = {
            'GEMINI_API_KEY': 'custom_key',
            'GEMINI_MODEL': 'gemini-1.5-pro',
            'GEMINI_TIMEOUT': '45',
            'GEMINI_RATE_LIMIT_PER_MINUTE': '120',
            'GEMINI_DEFAULT_TEMPERATURE': '0.5',
            'GEMINI_ENABLE_CACHING': 'false'
        }

        with patch.dict(os.environ, env_vars):
            config = GeminiConfig()

            assert config.api_key == 'custom_key'
            assert config.model == 'gemini-1.5-pro'
            assert config.timeout == 45
            assert config.rate_limit_per_minute == 120
            assert config.default_temperature == 0.5
            assert config.enable_caching is False

    def test_config_validation_invalid_temperature(self):
        """Test configuration validation with invalid temperature."""
        env_vars = {
            'GEMINI_API_KEY': 'test_key',
            'GEMINI_DEFAULT_TEMPERATURE': '3.0'  # Invalid: > 2.0
        }

        with patch.dict(os.environ, env_vars):
            with pytest.raises(InvalidConfigurationError) as exc_info:
                GeminiConfig()

            assert 'temperature' in str(exc_info.value)

    def test_config_validation_invalid_model(self):
        """Test configuration validation with invalid model."""
        env_vars = {
            'GEMINI_API_KEY': 'test_key',
            'GEMINI_MODEL': 'invalid-model'
        }

        with patch.dict(os.environ, env_vars):
            with pytest.raises(InvalidConfigurationError) as exc_info:
                GeminiConfig()

            assert 'model' in str(exc_info.value)
            assert 'invalid-model' in str(exc_info.value)

    def test_config_validation_invalid_rate_limit(self):
        """Test configuration validation with invalid rate limit."""
        env_vars = {
            'GEMINI_API_KEY': 'test_key',
            'GEMINI_RATE_LIMIT_PER_MINUTE': '0'  # Invalid: must be positive
        }

        with patch.dict(os.environ, env_vars):
            with pytest.raises(InvalidConfigurationError) as exc_info:
                GeminiConfig()

            assert 'rate_limit_per_minute' in str(exc_info.value)

    def test_get_generation_config(self):
        """Test generation config creation."""
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test_key'}):
            config = GeminiConfig()
            gen_config = config.get_generation_config()

            assert 'max_output_tokens' in gen_config
            assert 'temperature' in gen_config
            assert 'top_p' in gen_config
            assert 'top_k' in gen_config

            assert gen_config['temperature'] == config.default_temperature

    def test_get_safety_settings(self):
        """Test safety settings creation."""
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test_key'}):
            config = GeminiConfig()
            safety_settings = config.get_safety_settings()

            assert isinstance(safety_settings, list)
            assert len(safety_settings) == 4  # Four safety categories

            for setting in safety_settings:
                assert 'category' in setting
                assert 'threshold' in setting
                assert setting['threshold'] == config.safety_threshold

    def test_get_safety_settings_disabled(self):
        """Test safety settings when disabled."""
        env_vars = {
            'GEMINI_API_KEY': 'test_key',
            'GEMINI_ENABLE_SAFETY_FILTERING': 'false'
        }

        with patch.dict(os.environ, env_vars):
            config = GeminiConfig()
            safety_settings = config.get_safety_settings()

            assert safety_settings == []

    def test_is_vision_supported(self):
        """Test vision support detection."""
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test_key'}):
            # Default model (gemini-2.0-flash) supports vision
            config = GeminiConfig()
            assert config.is_vision_supported()

        with patch.dict(os.environ, {
            'GEMINI_API_KEY': 'test_key',
            'GEMINI_MODEL': 'gemini-pro-vision'
        }):
            config = GeminiConfig()
            assert config.is_vision_supported()

        with patch.dict(os.environ, {
            'GEMINI_API_KEY': 'test_key',
            'GEMINI_MODEL': 'gemini-1.5-pro'
        }):
            config = GeminiConfig()
            assert config.is_vision_supported()

    def test_get_model_for_request(self):
        """Test model selection for requests."""
        with patch.dict(os.environ, {
            'GEMINI_API_KEY': 'test_key',
            'GEMINI_MODEL': 'gemini-pro',
            'GEMINI_VISION_MODEL': 'gemini-pro-vision'
        }):
            config = GeminiConfig()

            # Text-only request
            assert config.get_model_for_request(has_images=False) == 'gemini-pro'

            # Request with images
            assert config.get_model_for_request(has_images=True) == 'gemini-pro-vision'

    def test_is_image_format_supported(self):
        """Test image format support checking."""
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test_key'}):
            config = GeminiConfig()

            assert config.is_image_format_supported('jpeg')
            assert config.is_image_format_supported('png')
            assert config.is_image_format_supported('webp')
            assert not config.is_image_format_supported('gif')
            assert not config.is_image_format_supported('bmp')

    def test_to_dict(self):
        """Test configuration serialization."""
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test_key'}):
            config = GeminiConfig()
            config_dict = config.to_dict()

            # Should contain configuration values
            assert 'model' in config_dict
            assert 'timeout' in config_dict
            assert 'rate_limit_per_minute' in config_dict
            assert 'is_vision_supported' in config_dict

            # Should not contain sensitive data
            assert 'api_key' not in config_dict or config_dict.get('has_api_key') is True

    def test_validate_method(self):
        """Test validate method returns errors."""
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test_key'}):
            config = GeminiConfig()
            errors = config.validate()
            assert errors == []  # No errors for valid config

        # Test with invalid config
        with patch.dict(os.environ, {
            'GEMINI_API_KEY': 'test_key',
            'GEMINI_DEFAULT_TEMPERATURE': '5.0'  # Invalid
        }):
            with pytest.raises(InvalidConfigurationError):
                GeminiConfig()

    def test_config_boolean_parsing(self):
        """Test boolean configuration parsing."""
        test_cases = [
            ('true', True),
            ('True', True),
            ('1', True),
            ('yes', True),
            ('on', True),
            ('false', False),
            ('False', False),
            ('0', False),
            ('no', False),
            ('off', False),
            ('anything_else', False)
        ]

        for value, expected in test_cases:
            env_vars = {
                'GEMINI_API_KEY': 'test_key',
                'GEMINI_ENABLE_CACHING': value
            }

            with patch.dict(os.environ, env_vars):
                config = GeminiConfig()
                assert config.enable_caching is expected

    def test_config_list_parsing(self):
        """Test list configuration parsing."""
        env_vars = {
            'GEMINI_API_KEY': 'test_key',
            'GEMINI_SUPPORTED_IMAGE_FORMATS': 'jpeg, png, webp, heic'
        }

        with patch.dict(os.environ, env_vars):
            config = GeminiConfig()
            expected_formats = ['jpeg', 'png', 'webp', 'heic']
            assert config.supported_image_formats == expected_formats
