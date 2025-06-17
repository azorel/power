"""
Tests for OpenAI configuration module.
"""

import os
import pytest
from adapters.openai_api.config import OpenAIConfig


class TestOpenAIConfig:
    """Test OpenAI configuration functionality."""

    def setup_method(self):
        """Set up test environment."""
        # Save original env vars
        self.original_env = os.environ.copy()
        
        # Set test environment variables
        os.environ['OPENAI_API_KEY'] = 'sk-test-key-for-validation'
        os.environ['OPENAI_BASE_URL'] = 'https://api.test.com'
        os.environ['OPENAI_TIMEOUT'] = '30'

    def teardown_method(self):
        """Clean up test environment."""
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_config_creation(self):
        """Test basic config creation."""
        config = OpenAIConfig()
        
        assert config.adapter_name == 'openai'
        assert config.api_key == 'sk-test-key-for-validation'
        assert config.timeout == 30

    def test_supported_models(self):
        """Test supported models list."""
        config = OpenAIConfig()
        models = config.get_supported_models()
        
        assert len(models) > 0
        assert 'gpt-4o' in models
        assert 'gpt-3.5-turbo' in models

    def test_model_config(self):
        """Test model configuration retrieval."""
        config = OpenAIConfig()
        
        gpt4_config = config.get_model_config('gpt-4o')
        assert gpt4_config['max_tokens'] > 0
        assert gpt4_config['supports_vision'] is True
        
        unknown_config = config.get_model_config('unknown-model')
        assert unknown_config == {}

    def test_validation_success(self):
        """Test successful validation."""
        config = OpenAIConfig()
        errors = config.validate()
        
        assert len(errors) == 0

    def test_validation_invalid_api_key(self):
        """Test validation with invalid API key."""
        os.environ['OPENAI_API_KEY'] = 'invalid-key'
        config = OpenAIConfig()
        errors = config.validate()
        
        assert len(errors) > 0
        assert any('API key must start with' in error for error in errors)

    def test_to_dict(self):
        """Test configuration serialization."""
        config = OpenAIConfig()
        config_dict = config.to_dict()
        
        assert 'adapter_name' in config_dict
        assert 'supported_models' in config_dict
        assert 'has_api_key' in config_dict
        # API key should not be in dict (security)
        assert 'api_key' not in config_dict

    def test_advanced_features(self):
        """Test advanced feature configuration."""
        config = OpenAIConfig()
        
        assert config.enable_streaming is True
        assert config.enable_function_calling is True
        assert config.enable_vision is True
        assert config.enable_image_generation is True

    def test_custom_model_defaults(self):
        """Test custom model and parameter defaults."""
        config = OpenAIConfig()
        
        assert config.default_model == 'gpt-4o'
        assert config.default_max_tokens == 4096
        assert config.default_temperature == 0.7