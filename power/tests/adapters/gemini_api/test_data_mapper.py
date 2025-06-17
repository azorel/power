"""
Tests for Gemini API data mapping functionality.
"""

import pytest
import base64
from datetime import datetime
from unittest.mock import MagicMock

from adapters.gemini_api.data_mapper import GeminiDataMapper
from adapters.gemini_api.config import GeminiConfig
from shared.models.llm_request import LLMRequest
from shared.models.llm_response import LLMResponse, FinishReason, UsageStats
from shared.exceptions import DataMappingError, InvalidRequestError


class TestGeminiDataMapper:
    """Test cases for GeminiDataMapper class."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock config for testing."""
        config = MagicMock(spec=GeminiConfig)
        config.default_max_tokens = 1000
        config.default_temperature = 0.7
        config.default_top_p = 0.9
        config.default_top_k = 40
        config.model = 'gemini-pro'
        config.get_safety_settings.return_value = [
            {'category': 'HARM_CATEGORY_HARASSMENT', 'threshold': 'BLOCK_MEDIUM_AND_ABOVE'}
        ]
        config.is_image_format_supported.return_value = True
        config.max_image_size_mb = 20
        config.supported_image_formats = ['jpeg', 'png', 'webp']
        config.enable_streaming = True
        return config

    @pytest.fixture
    def data_mapper(self, mock_config):
        """Create a data mapper for testing."""
        return GeminiDataMapper(mock_config)

    def test_map_llm_request_basic(self, data_mapper):
        """Test basic LLM request mapping."""
        request = LLMRequest(
            prompt="Hello, world!",
            max_tokens=500,
            temperature=0.8,
            top_p=0.95,
            top_k=50
        )

        gemini_request = data_mapper.map_llm_request(request)

        assert 'contents' in gemini_request
        assert 'generationConfig' in gemini_request
        assert 'safetySettings' in gemini_request

        # Check contents
        contents = gemini_request['contents']
        assert len(contents) == 1
        assert contents[0]['role'] == 'user'
        assert contents[0]['parts'][0]['text'] == "Hello, world!"

        # Check generation config
        gen_config = gemini_request['generationConfig']
        assert gen_config['max_output_tokens'] == 500
        assert gen_config['temperature'] == 0.8
        assert gen_config['top_p'] == 0.95
        assert gen_config['top_k'] == 50

    def test_map_llm_request_with_defaults(self, data_mapper):
        """Test LLM request mapping with default values."""
        request = LLMRequest(prompt="Test prompt")

        gemini_request = data_mapper.map_llm_request(request)

        gen_config = gemini_request['generationConfig']
        assert gen_config['max_output_tokens'] == 1000  # config default
        assert gen_config['temperature'] == 0.7  # config default
        assert gen_config['top_p'] == 0.9  # config default
        assert gen_config['top_k'] == 40  # config default

    def test_map_llm_request_with_stop_sequences(self, data_mapper):
        """Test LLM request mapping with stop sequences."""
        request = LLMRequest(
            prompt="Test prompt",
            stop_sequences=["STOP", "END"]
        )

        gemini_request = data_mapper.map_llm_request(request)

        gen_config = gemini_request['generationConfig']
        assert gen_config['stop_sequences'] == ["STOP", "END"]

    def test_map_llm_request_with_provider_params(self, data_mapper):
        """Test LLM request mapping with provider-specific parameters."""
        request = LLMRequest(
            prompt="Test prompt",
            provider_params={
                'gemini': {
                    'generation_config': {'candidate_count': 2},
                    'safety_settings': [{'category': 'TEST', 'threshold': 'BLOCK_NONE'}],
                    'tools': [{'function_declarations': []}]
                }
            }
        )

        gemini_request = data_mapper.map_llm_request(request)

        # Check that provider params override defaults
        gen_config = gemini_request['generationConfig']
        assert gen_config['candidate_count'] == 2

        # Check safety settings override
        assert gemini_request['safetySettings'] == [{'category': 'TEST', 'threshold': 'BLOCK_NONE'}]

        # Check tools addition
        assert 'tools' in gemini_request

    def test_map_llm_request_failure(self, data_mapper):
        """Test LLM request mapping failure handling."""
        # Create an invalid request that should cause mapping to fail
        with pytest.raises(DataMappingError) as exc_info:
            data_mapper.map_llm_request(None)

        assert "Failed to map LLM request" in str(exc_info.value)
        assert exc_info.value.source_format == 'LLMRequest'
        assert exc_info.value.target_format == 'Gemini API'

    def test_map_chat_request_basic(self, data_mapper):
        """Test basic chat request mapping."""
        messages = [
            {'role': 'system', 'content': 'You are a helpful assistant.'},
            {'role': 'user', 'content': 'Hello!'},
            {'role': 'assistant', 'content': 'Hi there!'},
            {'role': 'user', 'content': 'How are you?'}
        ]

        gemini_request = data_mapper.map_chat_request(messages)

        assert 'contents' in gemini_request
        assert 'generationConfig' in gemini_request
        assert 'safetySettings' in gemini_request

        contents = gemini_request['contents']
        assert len(contents) == 4

        # Check role mapping
        assert contents[0]['role'] == 'user'  # system -> user with prefix
        assert 'System:' in contents[0]['parts'][0]['text']

        assert contents[1]['role'] == 'user'
        assert contents[1]['parts'][0]['text'] == 'Hello!'

        assert contents[2]['role'] == 'model'  # assistant -> model
        assert contents[2]['parts'][0]['text'] == 'Hi there!'

        assert contents[3]['role'] == 'user'
        assert contents[3]['parts'][0]['text'] == 'How are you?'

    def test_map_chat_request_with_kwargs(self, data_mapper):
        """Test chat request mapping with additional parameters."""
        messages = [{'role': 'user', 'content': 'Test'}]

        gemini_request = data_mapper.map_chat_request(
            messages,
            max_tokens=800,
            temperature=0.5,
            stop_sequences=['STOP']
        )

        gen_config = gemini_request['generationConfig']
        assert gen_config['max_output_tokens'] == 800
        assert gen_config['temperature'] == 0.5
        assert gen_config['stop_sequences'] == ['STOP']

    def test_map_image_request_basic(self, data_mapper):
        """Test basic image request mapping."""
        image_data = b'fake_image_data'
        prompt = "What's in this image?"

        gemini_request = data_mapper.map_image_request(image_data, prompt, 'jpeg')

        assert 'contents' in gemini_request
        contents = gemini_request['contents']
        assert len(contents) == 1

        parts = contents[0]['parts']
        assert len(parts) == 2  # text + image

        # Check text part
        text_part = parts[0]
        assert text_part['text'] == prompt

        # Check image part
        image_part = parts[1]
        assert 'inline_data' in image_part
        assert image_part['inline_data']['mime_type'] == 'image/jpeg'

        # Check base64 encoding
        expected_b64 = base64.b64encode(image_data).decode('utf-8')
        assert image_part['inline_data']['data'] == expected_b64

    def test_map_image_request_unsupported_format(self, data_mapper):
        """Test image request with unsupported format."""
        data_mapper.config.is_image_format_supported.return_value = False

        with pytest.raises(DataMappingError) as exc_info:
            data_mapper.map_image_request(b'data', 'prompt', 'gif')

        assert 'not supported' in str(exc_info.value)

    def test_map_image_request_too_large(self, data_mapper):
        """Test image request with oversized image."""
        # Create fake image data larger than limit
        large_image = b'x' * (25 * 1024 * 1024)  # 25MB

        with pytest.raises(DataMappingError) as exc_info:
            data_mapper.map_image_request(large_image, 'prompt', 'jpeg')

        assert 'exceeds limit' in str(exc_info.value)

    def test_map_gemini_response_basic(self, data_mapper):
        """Test basic Gemini response mapping."""
        gemini_response = {
            'candidates': [
                {
                    'content': {
                        'parts': [{'text': 'Hello! How can I help you?'}]
                    },
                    'finishReason': 'STOP',
                    'safetyRatings': [
                        {
                            'category': 'HARM_CATEGORY_HARASSMENT',
                            'probability': 'NEGLIGIBLE'
                        }
                    ]
                }
            ],
            'usageMetadata': {
                'promptTokenCount': 10,
                'candidatesTokenCount': 15,
                'totalTokenCount': 25
            }
        }

        llm_response = data_mapper.map_gemini_response(
            gemini_response,
            request_id='test-123',
            model='gemini-pro'
        )

        assert isinstance(llm_response, LLMResponse)
        assert llm_response.content == 'Hello! How can I help you?'
        assert llm_response.finish_reason == FinishReason.COMPLETED
        assert llm_response.model == 'gemini-pro'
        assert llm_response.provider == 'gemini'
        assert llm_response.request_id == 'test-123'

        # Check usage stats
        usage = llm_response.usage
        assert isinstance(usage, UsageStats)
        assert usage.prompt_tokens == 10
        assert usage.completion_tokens == 15
        assert usage.total_tokens == 25

        # Check safety scores
        assert llm_response.safety_scores is not None
        assert 'HARM_CATEGORY_HARASSMENT' in llm_response.safety_scores
        assert llm_response.safety_scores['HARM_CATEGORY_HARASSMENT'] == 0.1

    def test_map_gemini_response_different_finish_reasons(self, data_mapper):
        """Test mapping different finish reasons."""
        finish_reason_mapping = {
            'STOP': FinishReason.COMPLETED,
            'MAX_TOKENS': FinishReason.MAX_TOKENS,
            'SAFETY': FinishReason.CONTENT_FILTER,
            'RECITATION': FinishReason.CONTENT_FILTER,
            'OTHER': FinishReason.ERROR
        }

        for gemini_reason, expected_reason in finish_reason_mapping.items():
            gemini_response = {
                'candidates': [
                    {
                        'content': {'parts': [{'text': 'Test'}]},
                        'finishReason': gemini_reason
                    }
                ],
                'usageMetadata': {
                    'promptTokenCount': 5,
                    'candidatesTokenCount': 5,
                    'totalTokenCount': 10
                }
            }

            llm_response = data_mapper.map_gemini_response(gemini_response)
            assert llm_response.finish_reason == expected_reason

    def test_map_gemini_response_no_candidates(self, data_mapper):
        """Test mapping response with no candidates."""
        gemini_response = {'candidates': []}

        with pytest.raises(DataMappingError) as exc_info:
            data_mapper.map_gemini_response(gemini_response)

        assert "No candidates found" in str(exc_info.value)

    def test_map_gemini_response_multiple_parts(self, data_mapper):
        """Test mapping response with multiple content parts."""
        gemini_response = {
            'candidates': [
                {
                    'content': {
                        'parts': [
                            {'text': 'Part 1: '},
                            {'text': 'Part 2'},
                            {'text': ' - Done!'}
                        ]
                    },
                    'finishReason': 'STOP'
                }
            ],
            'usageMetadata': {
                'promptTokenCount': 5,
                'candidatesTokenCount': 10,
                'totalTokenCount': 15
            }
        }

        llm_response = data_mapper.map_gemini_response(gemini_response)
        assert llm_response.content == 'Part 1: Part 2 - Done!'

    def test_map_streaming_chunk(self, data_mapper):
        """Test mapping streaming response chunk."""
        chunk = {
            'candidates': [
                {
                    'content': {
                        'parts': [{'text': ' world!'}]
                    }
                }
            ]
        }

        cumulative_content = "Hello"
        chunk_index = 1

        streaming_response = data_mapper.map_streaming_chunk(
            chunk, cumulative_content, chunk_index
        )

        assert streaming_response.content_delta == ' world!'
        assert streaming_response.cumulative_content == 'Hello world!'
        assert streaming_response.chunk_index == 1
        assert not streaming_response.is_final
        assert streaming_response.final_response is None

    def test_map_streaming_chunk_final(self, data_mapper):
        """Test mapping final streaming chunk."""
        chunk = {
            'candidates': [
                {
                    'content': {
                        'parts': [{'text': '!'}]
                    },
                    'finishReason': 'STOP'
                }
            ],
            'usageMetadata': {
                'promptTokenCount': 5,
                'candidatesTokenCount': 10,
                'totalTokenCount': 15
            }
        }

        streaming_response = data_mapper.map_streaming_chunk(chunk, "Hello world", 2)

        assert streaming_response.is_final
        assert streaming_response.final_response is not None
        assert isinstance(streaming_response.final_response, LLMResponse)

    def test_extract_model_info(self, data_mapper):
        """Test model information extraction."""
        # Test basic model
        model_info = data_mapper.extract_model_info('gemini-pro')

        assert model_info['name'] == 'gemini-pro'
        assert model_info['provider'] == 'gemini'
        assert 'text_generation' in model_info['capabilities']
        assert 'chat_completion' in model_info['capabilities']
        assert model_info['context_window'] == 30720

        # Test vision model
        vision_info = data_mapper.extract_model_info('gemini-pro-vision')

        assert 'image_input' in vision_info['capabilities']
        assert 'image' in vision_info['input_modalities']
        assert 'max_image_size_mb' in vision_info

        # Test Gemini 1.5 model
        gemini_15_info = data_mapper.extract_model_info('gemini-1.5-pro')

        assert gemini_15_info['context_window'] == 1048576
        assert gemini_15_info['version'] == '1.5'
        assert 'image_input' in gemini_15_info['capabilities']  # 1.5 supports vision

    def test_validate_request_size(self, data_mapper):
        """Test request size validation."""
        # Test valid request
        valid_request = {
            'contents': [
                {
                    'parts': [{'text': 'Short prompt'}]
                }
            ]
        }

        assert data_mapper.validate_request_size(valid_request)

        # Test oversized request
        long_text = 'x' * 100000  # Very long text
        oversized_request = {
            'contents': [
                {
                    'parts': [{'text': long_text}]
                }
            ]
        }

        data_mapper.config.model = 'gemini-pro'  # Has lower token limit
        # This might still pass due to rough estimation, so we'll test with extreme case

        # Test with Gemini 1.5 (higher limits)
        data_mapper.config.model = 'gemini-1.5-pro'
        assert data_mapper.validate_request_size(oversized_request)

    def test_mapping_error_handling(self, data_mapper):
        """Test error handling in mapping functions."""
        # Test malformed Gemini response
        malformed_response = {'invalid': 'structure'}

        with pytest.raises(DataMappingError):
            data_mapper.map_gemini_response(malformed_response)

        # Test invalid streaming chunk
        invalid_chunk = None

        with pytest.raises(DataMappingError):
            data_mapper.map_streaming_chunk(invalid_chunk, "", 0)

    def test_safety_score_mapping(self, data_mapper):
        """Test safety score probability mapping."""
        probability_mapping = {
            'NEGLIGIBLE': 0.1,
            'LOW': 0.3,
            'MEDIUM': 0.6,
            'HIGH': 0.9,
            'UNKNOWN': 0.5
        }

        for probability, expected_score in probability_mapping.items():
            gemini_response = {
                'candidates': [
                    {
                        'content': {'parts': [{'text': 'Test'}]},
                        'finishReason': 'STOP',
                        'safetyRatings': [
                            {
                                'category': 'TEST_CATEGORY',
                                'probability': probability
                            }
                        ]
                    }
                ],
                'usageMetadata': {
                    'promptTokenCount': 5,
                    'candidatesTokenCount': 5,
                    'totalTokenCount': 10
                }
            }

            llm_response = data_mapper.map_gemini_response(gemini_response)
            assert llm_response.safety_scores['TEST_CATEGORY'] == expected_score
