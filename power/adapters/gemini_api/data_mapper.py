"""
Data transformation between Gemini API format and shared Power Builder models.
Handles request/response mapping and format conversion.
"""

import base64
from typing import Dict, Any, List, Optional
from datetime import datetime

from shared.models.llm_request import LLMRequest
from shared.models.llm_response import (
    LLMResponse,
    FinishReason,
    UsageStats,
    StreamingResponse
)
from shared.exceptions import DataMappingError, InvalidRequestError
from .config import GeminiConfig


class GeminiDataMapper:
    """Maps data between shared models and Gemini API format."""

    def __init__(self, config: GeminiConfig):
        """Initialize mapper with configuration."""
        self.config = config

    def map_llm_request(self, request: LLMRequest) -> Dict[str, Any]:
        """
        Convert LLMRequest to Gemini API format.

        Args:
            request: Shared LLM request model

        Returns:
            Dictionary in Gemini API format

        Raises:
            DataMappingError: If mapping fails
        """
        try:
            # Build generation config
            generation_config = {
                'max_output_tokens': request.max_tokens or self.config.default_max_tokens,
                'temperature': request.temperature or self.config.default_temperature,
                'top_p': request.top_p or self.config.default_top_p,
                'top_k': request.top_k or self.config.default_top_k
            }

            # Handle stop sequences
            if request.stop_sequences:
                generation_config['stop_sequences'] = request.stop_sequences

            # Handle seed for reproducibility
            if request.seed is not None:
                generation_config['candidate_count'] = 1  # Required for deterministic output

            # Build request body
            gemini_request = {
                'contents': [
                    {
                        'parts': [{'text': request.prompt}],
                        'role': 'user'
                    }
                ],
                'generationConfig': generation_config,
                'safetySettings': self.config.get_safety_settings()
            }

            # Add provider-specific parameters
            if request.provider_params:
                gemini_params = request.provider_params.get('gemini', {})

                # Override generation config with provider params
                if 'generation_config' in gemini_params:
                    generation_config.update(gemini_params['generation_config'])

                # Add safety settings override
                if 'safety_settings' in gemini_params:
                    gemini_request['safetySettings'] = gemini_params['safety_settings']

                # Add tools/function calling if specified
                if 'tools' in gemini_params:
                    gemini_request['tools'] = gemini_params['tools']

            return gemini_request

        except Exception as e:
            raise DataMappingError(
                f"Failed to map LLM request to Gemini format: {e}",
                source_format='LLMRequest',
                target_format='Gemini API'
            ) from e

    def map_chat_request(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """
        Convert chat messages to Gemini API format.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            Dictionary in Gemini API format

        Raises:
            DataMappingError: If mapping fails
        """
        try:
            # Convert messages to Gemini format
            gemini_contents = []

            for msg in messages:
                # Handle both ChatMessage objects and dictionaries
                if hasattr(msg, 'role'):
                    role = msg.role
                    content = msg.content
                else:
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')

                # Map roles to Gemini format
                if role == 'system':
                    # Gemini doesn't have system role, convert to user message with prefix
                    gemini_role = 'user'
                    content = f"System: {content}"
                elif role == 'assistant':
                    gemini_role = 'model'
                else:  # user
                    gemini_role = 'user'

                gemini_contents.append({
                    'parts': [{'text': content}],
                    'role': gemini_role
                })

            # Build generation config from kwargs
            generation_config = {
                'max_output_tokens': kwargs.get('max_tokens', self.config.default_max_tokens),
                'temperature': kwargs.get('temperature', self.config.default_temperature),
                'top_p': kwargs.get('top_p', self.config.default_top_p),
                'top_k': kwargs.get('top_k', self.config.default_top_k)
            }

            # Handle stop sequences
            if 'stop_sequences' in kwargs:
                generation_config['stop_sequences'] = kwargs['stop_sequences']

            gemini_request = {
                'contents': gemini_contents,
                'generationConfig': generation_config,
                'safetySettings': self.config.get_safety_settings()
            }

            return gemini_request

        except Exception as e:
            raise DataMappingError(
                f"Failed to map chat request to Gemini format: {e}",
                source_format='Chat Messages',
                target_format='Gemini API'
            ) from e

    def map_image_request(
        self,
        image_data: bytes,
        prompt: str,
        image_format: str = 'jpeg',
        **kwargs
    ) -> Dict[str, Any]:
        """
        Convert image + text request to Gemini API format.

        Args:
            image_data: Raw image bytes
            prompt: Text prompt to accompany image
            image_format: Image format (jpeg, png, etc.)
            **kwargs: Additional parameters

        Returns:
            Dictionary in Gemini API format

        Raises:
            DataMappingError: If mapping fails
        """
        try:
            # Validate image format
            if not self.config.is_image_format_supported(image_format):
                raise InvalidRequestError(
                    f"Image format '{image_format}' not supported. "
                    f"Supported formats: {self.config.supported_image_formats}"
                )

            # Check image size
            image_size_mb = len(image_data) / (1024 * 1024)
            if image_size_mb > self.config.max_image_size_mb:
                raise InvalidRequestError(
                    f"Image size {image_size_mb:.1f}MB exceeds limit of "
                    f"{self.config.max_image_size_mb}MB"
                )

            # Encode image to base64
            image_b64 = base64.b64encode(image_data).decode('utf-8')

            # Build request with image and text
            parts = []

            # Add text prompt if provided
            if prompt:
                parts.append({'text': prompt})

            # Add image part
            parts.append({
                'inline_data': {
                    'mime_type': f'image/{image_format}',
                    'data': image_b64
                }
            })

            # Build generation config
            generation_config = {
                'max_output_tokens': kwargs.get('max_tokens', self.config.default_max_tokens),
                'temperature': kwargs.get('temperature', self.config.default_temperature),
                'top_p': kwargs.get('top_p', self.config.default_top_p),
                'top_k': kwargs.get('top_k', self.config.default_top_k)
            }

            gemini_request = {
                'contents': [
                    {
                        'parts': parts,
                        'role': 'user'
                    }
                ],
                'generationConfig': generation_config,
                'safetySettings': self.config.get_safety_settings()
            }

            return gemini_request

        except Exception as e:
            raise DataMappingError(
                f"Failed to map image request to Gemini format: {e}",
                source_format='Image + Text',
                target_format='Gemini API'
            ) from e

    def map_gemini_response(
        self,
        gemini_response: Dict[str, Any],
        request_id: Optional[str] = None,
        model: Optional[str] = None
    ) -> LLMResponse:
        """
        Convert Gemini API response to LLMResponse.

        Args:
            gemini_response: Response from Gemini API
            request_id: Optional request ID for tracking
            model: Model name used for the request

        Returns:
            Shared LLM response model

        Raises:
            DataMappingError: If mapping fails
        """
        try:
            candidates = gemini_response.get('candidates', [])
            if not candidates:
                raise DataMappingError(
                    "No candidates found in Gemini response",
                    source_format='Gemini API',
                    target_format='LLMResponse'
                )

            candidate = candidates[0]
            content = self._extract_content_from_candidate(candidate)
            finish_reason = self._map_finish_reason(candidate)
            usage = self._extract_usage_stats(gemini_response)
            safety_scores = self._extract_safety_scores(candidate)
            provider_metadata = self._build_provider_metadata(candidate, candidates)

            return LLMResponse(
                content=content,
                finish_reason=finish_reason,
                usage=usage,
                model=model or self.config.model,
                provider='gemini',
                response_id=gemini_response.get('modelVersion'),
                request_id=request_id,
                timestamp=datetime.now(),
                provider_metadata=provider_metadata,
                safety_scores=safety_scores if safety_scores else None
            )

        except Exception as e:
            raise DataMappingError(
                f"Failed to map Gemini response to LLMResponse: {e}",
                source_format='Gemini API',
                target_format='LLMResponse'
            ) from e

    def _extract_content_from_candidate(self, candidate: Dict[str, Any]) -> str:
        """Extract text content from a candidate."""
        if 'content' not in candidate:
            return ""

        parts = candidate['content'].get('parts', [])
        content_parts = []

        for part in parts:
            if 'text' in part:
                content_parts.append(part['text'])

        return ''.join(content_parts)

    def _map_finish_reason(self, candidate: Dict[str, Any]) -> FinishReason:
        """Map Gemini finish reason to our FinishReason enum."""
        finish_reason_mapping = {
            'STOP': FinishReason.COMPLETED,
            'MAX_TOKENS': FinishReason.MAX_TOKENS,
            'SAFETY': FinishReason.CONTENT_FILTER,
            'RECITATION': FinishReason.CONTENT_FILTER,
            'OTHER': FinishReason.ERROR
        }

        gemini_finish_reason = candidate.get('finishReason', 'STOP')
        return finish_reason_mapping.get(gemini_finish_reason, FinishReason.ERROR)

    def _extract_usage_stats(self, gemini_response: Dict[str, Any]) -> UsageStats:
        """Extract usage statistics from Gemini response."""
        usage_metadata = gemini_response.get('usageMetadata', {})
        prompt_tokens = usage_metadata.get('promptTokenCount', 0)
        completion_tokens = usage_metadata.get('candidatesTokenCount', 0)
        total_tokens = usage_metadata.get('totalTokenCount', prompt_tokens + completion_tokens)

        return UsageStats(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens
        )

    def _extract_safety_scores(self, candidate: Dict[str, Any]) -> Dict[str, float]:
        """Extract safety scores from candidate."""
        safety_scores = {}
        if 'safetyRatings' not in candidate:
            return safety_scores

        score_mapping = {
            'NEGLIGIBLE': 0.1,
            'LOW': 0.3,
            'MEDIUM': 0.6,
            'HIGH': 0.9,
            'UNKNOWN': 0.5
        }

        for rating in candidate['safetyRatings']:
            category = rating.get('category', 'unknown')
            probability = rating.get('probability', 'UNKNOWN')
            safety_scores[category] = score_mapping.get(probability, 0.5)

        return safety_scores

    def _build_provider_metadata(
        self,
        candidate: Dict[str, Any],
        candidates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build provider metadata from candidate and candidates list."""
        metadata = {
            'gemini_finish_reason': candidate.get('finishReason', 'STOP'),
            'candidate_index': 0,
            'total_candidates': len(candidates)
        }

        if 'safetyRatings' in candidate:
            metadata['safety_ratings'] = candidate['safetyRatings']

        if 'citationMetadata' in candidate:
            metadata['citations'] = candidate['citationMetadata']

        return metadata

    def map_streaming_chunk(
        self,
        chunk: Dict[str, Any],
        cumulative_content: str,
        chunk_index: int
    ) -> StreamingResponse:
        """
        Convert Gemini streaming chunk to StreamingResponse.

        Args:
            chunk: Individual streaming chunk from Gemini
            cumulative_content: All content received so far
            chunk_index: Index of this chunk

        Returns:
            Streaming response model

        Raises:
            DataMappingError: If mapping fails
        """
        try:
            # Extract content delta from chunk
            content_delta = ""

            candidates = chunk.get('candidates', [])
            if candidates:
                candidate = candidates[0]
                if 'content' in candidate:
                    parts = candidate['content'].get('parts', [])
                    for part in parts:
                        if 'text' in part:
                            content_delta += part['text']

            # Check if this is the final chunk
            is_final = False
            final_response = None

            if candidates and 'finishReason' in candidates[0]:
                is_final = True
                # Create final response for the last chunk
                final_response = self.map_gemini_response(chunk)

            return StreamingResponse(
                content_delta=content_delta,
                cumulative_content=cumulative_content + content_delta,
                is_final=is_final,
                chunk_index=chunk_index,
                timestamp=datetime.now(),
                final_response=final_response
            )

        except Exception as e:
            raise DataMappingError(
                f"Failed to map Gemini streaming chunk: {e}",
                source_format='Gemini Streaming',
                target_format='StreamingResponse'
            ) from e

    def extract_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        Extract model information for the get_model_info method.

        Args:
            model_name: Name of the Gemini model

        Returns:
            Dictionary with model information
        """
        model_info = {
            'name': model_name,
            'provider': 'gemini',
            'version': 'latest',
            'capabilities': ['text_generation', 'chat_completion'],
            'input_modalities': ['text'],
            'output_modalities': ['text'],
            'max_tokens': self.config.default_max_tokens,
            'supports_streaming': self.config.enable_streaming,
            'supports_functions': False,  # To be updated when function calling is supported
            'context_window': 30720  # Default for Gemini Pro
        }

        # Model-specific configurations
        # Add vision capabilities for vision models and Gemini 1.5+ models
        if 'vision' in model_name.lower() or '1.5' in model_name or '2.0' in model_name:
            model_info['capabilities'].append('image_input')
            model_info['input_modalities'].append('image')
            model_info['max_image_size_mb'] = self.config.max_image_size_mb
            model_info['supported_image_formats'] = self.config.supported_image_formats

        if '2.0' in model_name:
            model_info['context_window'] = 2097152  # 2M tokens for Gemini 2.0
            model_info['version'] = '2.0'
        elif '1.5' in model_name:
            model_info['context_window'] = 1048576  # 1M tokens for Gemini 1.5
            model_info['version'] = '1.5'

        if 'flash' in model_name.lower():
            model_info['optimized_for'] = 'speed'
        elif 'pro' in model_name.lower():
            model_info['optimized_for'] = 'quality'

        return model_info

    def validate_request_size(self, request_data: Dict[str, Any]) -> bool:
        """
        Validate that request size is within Gemini limits.

        Args:
            request_data: Formatted request data

        Returns:
            True if request is valid, False otherwise
        """
        try:
            # Estimate token count for validation
            total_chars = 0

            for content in request_data.get('contents', []):
                for part in content.get('parts', []):
                    if 'text' in part:
                        total_chars += len(part['text'])

            # Rough estimation: ~3 characters per token for Gemini
            estimated_tokens = total_chars // 3

            # Check against model limits
            if '2.0' in self.config.model:
                max_tokens = 2097152  # 2M tokens for Gemini 2.0
            elif '1.5' in self.config.model:
                max_tokens = 1048576  # 1M tokens for Gemini 1.5
            else:
                max_tokens = 30720    # 30K tokens for older models

            return estimated_tokens <= max_tokens

        except Exception:
            # If validation fails, assume it's valid and let API handle it
            return True
