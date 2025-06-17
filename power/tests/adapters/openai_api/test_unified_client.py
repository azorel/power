"""
Tests for OpenAI unified client.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from adapters.openai_api.config import OpenAIConfig
from adapters.openai_api.unified_client import OpenAIUnifiedClient


class TestOpenAIUnifiedClient:
    """Test OpenAI unified client functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.original_env = os.environ.copy()
        os.environ['OPENAI_API_KEY'] = 'sk-test-key-for-validation'

    def teardown_method(self):
        """Clean up test environment."""
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_client_creation(self):
        """Test basic client creation."""
        config = OpenAIConfig()
        client = OpenAIUnifiedClient(config)
        
        assert client.provider_name == 'openai'
        assert len(client.supported_features) > 0

    def test_supported_features(self):
        """Test supported features list."""
        config = OpenAIConfig()
        client = OpenAIUnifiedClient(config)
        
        features = client.supported_features
        assert 'text_generation' in features
        assert 'chat_completion' in features
        assert 'streaming' in features
        assert 'function_calling' in features
        assert 'image_input' in features

    def test_advanced_capabilities(self):
        """Test advanced capabilities."""
        config = OpenAIConfig()
        client = OpenAIUnifiedClient(config)
        
        capabilities = client.get_advanced_capabilities()
        assert isinstance(capabilities, dict)
        assert 'text_generation' in capabilities
        assert 'chat_completion' in capabilities
        assert capabilities['text_generation'] is True

    def test_comprehensive_capabilities(self):
        """Test comprehensive capabilities info."""
        config = OpenAIConfig()
        client = OpenAIUnifiedClient(config)
        
        info = client.get_comprehensive_capabilities()
        assert 'provider' in info
        assert 'supported_features' in info
        assert 'advanced_capabilities' in info
        assert 'supported_models' in info

    def test_feature_support_check(self):
        """Test feature support checking."""
        config = OpenAIConfig()
        client = OpenAIUnifiedClient(config)
        
        assert client.is_feature_supported('text_generation') is True
        assert client.is_feature_supported('chat_completion') is True
        assert client.is_feature_supported('unknown_feature') is False

    @patch('adapters.openai_api.text_client.OpenAITextClient.get_model_info')
    def test_get_model_info(self, mock_get_model_info):
        """Test model info retrieval."""
        mock_get_model_info.return_value = {
            'name': 'gpt-4o',
            'max_tokens': 4096,
            'supports_vision': True
        }
        
        config = OpenAIConfig()
        client = OpenAIUnifiedClient(config)
        
        model_info = client.get_model_info()
        assert model_info['name'] == 'gpt-4o'
        assert model_info['max_tokens'] == 4096

    def test_select_optimal_model(self):
        """Test optimal model selection."""
        config = OpenAIConfig()
        client = OpenAIUnifiedClient(config)
        
        # Test simple task
        model = client.select_optimal_model('text', 'simple')
        assert model in config.get_supported_models()
        
        # Test complex task
        model = client.select_optimal_model('analysis', 'complex')
        assert model in config.get_supported_models()

    def test_context_manager(self):
        """Test client as context manager."""
        config = OpenAIConfig()
        
        with OpenAIUnifiedClient(config) as client:
            assert client.provider_name == 'openai'
        
        # Should not raise exception after context exit

    def test_client_string_representation(self):
        """Test client string representation."""
        config = OpenAIConfig()
        client = OpenAIUnifiedClient(config)
        
        repr_str = repr(client)
        assert 'OpenAIUnifiedClient' in repr_str
        assert 'openai' in repr_str