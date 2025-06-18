"""
Tests for Claude API configuration.
"""

import pytest
from unittest.mock import patch, MagicMock
import os

from adapters.claude_api.config import ClaudeConfig
from adapters.claude_api.exceptions import ClaudeAPIError


class TestClaudeConfig:
    """Test cases for ClaudeConfig class."""

    @patch.dict(os.environ, {
        'CLAUDE_API_KEY': 'sk-ant-test-key-123',
        'CLAUDE_DEFAULT_MODEL': 'claude-sonnet-4-latest',
        'CLAUDE_ENABLE_HYBRID_REASONING': 'true',
        'CLAUDE_REASONING_MODE': 'balanced',
        'CLAUDE_DEFAULT_MAX_TOKENS': '65536'
    })
    def test_config_initialization_with_env_vars(self):
        """Test configuration initialization with environment variables."""
        config = ClaudeConfig()
        
        assert config.api_key == 'sk-ant-test-key-123'
        assert config.default_model == 'claude-sonnet-4-latest'
        assert config.enable_hybrid_reasoning is True
        assert config.reasoning_mode == 'balanced'
        assert config.default_max_tokens == 65536

    def test_config_initialization_with_defaults(self):
        """Test configuration initialization with default values."""
        with patch.dict(os.environ, {}, clear=True):
            config = ClaudeConfig()
            
            assert config.default_model == 'claude-sonnet-4-latest'
            assert config.default_max_tokens == 65536
            assert config.enable_hybrid_reasoning is True
            assert config.reasoning_mode == 'balanced'
            assert config.max_context_tokens == 65536

    def test_get_model_config_sonnet_4(self):
        """Test getting Sonnet 4 model configuration."""
        config = ClaudeConfig()
        model_config = config.get_model_config('claude-sonnet-4-latest')
        
        assert model_config['max_tokens'] == 65536
        assert model_config['knowledge_cutoff'] == '2025-03-01'
        assert model_config['supports_hybrid_reasoning'] is True
        assert model_config['supports_vision'] is True
        assert model_config['supports_functions'] is True
        assert model_config['model_type'] == 'sonnet-4'

    def test_get_model_config_opus_4(self):
        """Test getting Opus 4 model configuration."""
        config = ClaudeConfig()
        model_config = config.get_model_config('claude-opus-4-latest')
        
        assert model_config['max_tokens'] == 65536
        assert model_config['knowledge_cutoff'] == '2025-03-01'
        assert model_config['supports_hybrid_reasoning'] is True
        assert 'philosophical' in model_config['reasoning_capabilities']
        assert model_config['model_type'] == 'opus-4'

    def test_get_model_config_unknown_model(self):
        """Test getting configuration for unknown model."""
        config = ClaudeConfig()
        model_config = config.get_model_config('unknown-model')
        
        assert model_config == {}

    def test_get_supported_models(self):
        """Test getting list of supported models."""
        config = ClaudeConfig()
        supported_models = config.get_supported_models()
        
        assert 'claude-sonnet-4-latest' in supported_models
        assert 'claude-opus-4-latest' in supported_models
        assert 'claude-sonnet-3.5-latest' in supported_models
        assert 'claude-haiku-3.5-latest' in supported_models

    def test_get_hybrid_reasoning_config_analytical(self):
        """Test hybrid reasoning configuration for analytical mode."""
        with patch.dict(os.environ, {'CLAUDE_REASONING_MODE': 'analytical'}):
            config = ClaudeConfig()
            reasoning_config = config.get_hybrid_reasoning_config()
            
            assert reasoning_config['enabled'] is True
            assert reasoning_config['mode'] == 'analytical'
            assert reasoning_config['capabilities']['analytical'] is True
            assert reasoning_config['capabilities']['intuitive'] is False

    def test_get_hybrid_reasoning_config_creative(self):
        """Test hybrid reasoning configuration for creative mode."""
        with patch.dict(os.environ, {'CLAUDE_REASONING_MODE': 'creative'}):
            config = ClaudeConfig()
            reasoning_config = config.get_hybrid_reasoning_config()
            
            assert reasoning_config['mode'] == 'creative'
            assert reasoning_config['capabilities']['creative'] is True
            assert reasoning_config['capabilities']['intuitive'] is True
            assert reasoning_config['capabilities']['philosophical'] is True

    def test_get_hybrid_reasoning_config_balanced(self):
        """Test hybrid reasoning configuration for balanced mode."""
        with patch.dict(os.environ, {'CLAUDE_REASONING_MODE': 'balanced'}):
            config = ClaudeConfig()
            reasoning_config = config.get_hybrid_reasoning_config()
            
            assert reasoning_config['mode'] == 'balanced'
            assert reasoning_config['capabilities']['analytical'] is True
            assert reasoning_config['capabilities']['creative'] is True
            assert reasoning_config['capabilities']['intuitive'] is True

    def test_validate_valid_config(self):
        """Test validation of valid configuration."""
        with patch.dict(os.environ, {
            'CLAUDE_API_KEY': 'sk-ant-valid-key',
            'CLAUDE_DEFAULT_TEMPERATURE': '0.7',
            'CLAUDE_REASONING_MODE': 'balanced'
        }):
            config = ClaudeConfig()
            errors = config.validate()
            
            assert len(errors) == 0

    def test_validate_invalid_api_key(self):
        """Test validation with invalid API key."""
        with patch.dict(os.environ, {'CLAUDE_API_KEY': 'invalid-key'}):
            config = ClaudeConfig()
            errors = config.validate()
            
            assert any("API key must start with 'sk-ant-'" in error for error in errors)

    def test_validate_invalid_temperature(self):
        """Test validation with invalid temperature."""
        with patch.dict(os.environ, {
            'CLAUDE_API_KEY': 'sk-ant-valid-key',
            'CLAUDE_DEFAULT_TEMPERATURE': '2.5'
        }):
            config = ClaudeConfig()
            errors = config.validate()
            
            assert any("temperature must be between 0.0 and 1.0" in error for error in errors)

    def test_validate_invalid_reasoning_mode(self):
        """Test validation with invalid reasoning mode."""
        with patch.dict(os.environ, {
            'CLAUDE_API_KEY': 'sk-ant-valid-key',
            'CLAUDE_REASONING_MODE': 'invalid_mode'
        }):
            config = ClaudeConfig()
            errors = config.validate()
            
            assert any("reasoning_mode must be" in error for error in errors)

    def test_validate_invalid_max_tokens(self):
        """Test validation with invalid max tokens."""
        with patch.dict(os.environ, {
            'CLAUDE_API_KEY': 'sk-ant-valid-key',
            'CLAUDE_DEFAULT_MAX_TOKENS': '100000'  # Exceeds 64K limit
        }):
            config = ClaudeConfig()
            errors = config.validate()
            
            assert any("cannot exceed 65536" in error for error in errors)

    def test_validate_invalid_reasoning_depth(self):
        """Test validation with invalid reasoning depth."""
        with patch.dict(os.environ, {
            'CLAUDE_API_KEY': 'sk-ant-valid-key',
            'CLAUDE_REASONING_DEPTH': '10'  # Exceeds max of 5
        }):
            config = ClaudeConfig()
            errors = config.validate()
            
            assert any("reasoning_depth must be between 1 and 5" in error for error in errors)

    def test_validate_invalid_top_p(self):
        """Test validation with invalid top_p."""
        with patch.dict(os.environ, {
            'CLAUDE_API_KEY': 'sk-ant-valid-key',
            'CLAUDE_DEFAULT_TOP_P': '1.5'  # Exceeds 1.0
        }):
            config = ClaudeConfig()
            errors = config.validate()
            
            assert any("top_p must be between 0.0 and 1.0" in error for error in errors)

    def test_validate_invalid_safety_level(self):
        """Test validation with invalid safety level."""
        with patch.dict(os.environ, {
            'CLAUDE_API_KEY': 'sk-ant-valid-key',
            'CLAUDE_SAFETY_LEVEL': 'extreme'
        }):
            config = ClaudeConfig()
            errors = config.validate()
            
            assert any("safety_level must be" in error for error in errors)

    def test_to_dict_excludes_sensitive_data(self):
        """Test that to_dict excludes sensitive data."""
        with patch.dict(os.environ, {'CLAUDE_API_KEY': 'sk-ant-secret-key'}):
            config = ClaudeConfig()
            config_dict = config.to_dict()
            
            # Sensitive data should not be included
            assert 'api_key' not in config_dict
            
            # Non-sensitive data should be included
            assert 'default_model' in config_dict
            assert 'hybrid_reasoning_config' in config_dict
            assert 'supported_models' in config_dict

    def test_to_dict_includes_hybrid_reasoning_config(self):
        """Test that to_dict includes hybrid reasoning configuration."""
        config = ClaudeConfig()
        config_dict = config.to_dict()
        
        assert 'hybrid_reasoning_config' in config_dict
        reasoning_config = config_dict['hybrid_reasoning_config']
        assert 'enabled' in reasoning_config
        assert 'mode' in reasoning_config
        assert 'capabilities' in reasoning_config

    def test_context_preservation_ratio_validation(self):
        """Test validation of context preservation ratio."""
        with patch.dict(os.environ, {
            'CLAUDE_API_KEY': 'sk-ant-valid-key',
            'CLAUDE_CONTEXT_PRESERVATION_RATIO': '1.5'  # Exceeds 1.0
        }):
            config = ClaudeConfig()
            errors = config.validate()
            
            assert any("context_preservation_ratio must be between 0.0 and 1.0" in error for error in errors)

    @pytest.mark.parametrize("model_name,expected_type", [
        ('claude-sonnet-4-latest', 'sonnet-4'),
        ('claude-opus-4-latest', 'opus-4'),
        ('claude-sonnet-3.5-latest', 'sonnet-3.5'),
        ('claude-haiku-3.5-latest', 'haiku-3.5')
    ])
    def test_model_types(self, model_name, expected_type):
        """Test model type identification."""
        config = ClaudeConfig()
        model_config = config.get_model_config(model_name)
        assert model_config['model_type'] == expected_type

    def test_64k_token_limit_enforcement(self):
        """Test that 64K token limit is properly enforced."""
        config = ClaudeConfig()
        
        # Default should be 64K
        assert config.default_max_tokens <= 65536
        assert config.max_context_tokens <= 65536
        
        # Model configs should respect 64K limit for v4 models
        sonnet4_config = config.get_model_config('claude-sonnet-4-latest')
        opus4_config = config.get_model_config('claude-opus-4-latest')
        
        assert sonnet4_config['max_tokens'] == 65536
        assert opus4_config['max_tokens'] == 65536