"""
Text generation capabilities for Gemini API client.
"""

import logging
import time
from typing import Dict, Any, Optional

from shared.models.llm_request import LLMRequest
from shared.models.llm_response import LLMResponse
from shared.utils.cache import generate_cache_key

from .base_client import GeminiBaseClient
from .exceptions import wrap_gemini_call

logger = logging.getLogger(__name__)


class GeminiTextClient(GeminiBaseClient):
    """
    Gemini client for text generation operations.
    """

    @wrap_gemini_call
    def generate_text(self, request: LLMRequest) -> LLMResponse:
        """
        Generate text based on the provided request.

        Args:
            request: LLM request containing prompt and parameters

        Returns:
            LLMResponse with generated text
        """
        # Check cache first if enabled
        if self.cache:
            cache_key = generate_cache_key(request.prompt, request.provider_params)
            cached_response = self.cache.get(cache_key)
            if cached_response:
                self._stats['cache_hits'] += 1
                logger.debug("Cache hit for request: %s", request.request_id)
                return cached_response

        # Rate limiting
        self.rate_limiter.wait_if_needed()

        try:
            client = self._get_genai_client()

            # Map request to Gemini format
            gemini_request = self.data_mapper.map_llm_request(request)

            # Validate request size
            if not self.data_mapper.validate_request_size(gemini_request):
                from shared.exceptions import InvalidRequestError
                raise InvalidRequestError(
                    "Request exceeds maximum token limit for Gemini API",
                    error_code="REQUEST_TOO_LARGE"
                )

            # Measure latency
            start_time = time.time()

            # Make API call - NEW SDK 2024 format
            response = client.models.generate_content(
                model=self.config.model,
                contents=gemini_request.get('contents', []),
                config=gemini_request.get('config', {})
            )

            # Calculate latency
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000

            # Convert response back to our format
            llm_response = self.data_mapper.map_gemini_response(
                response,
                request_id=request.request_id,
                model=self.config.model
            )

            # Set latency
            llm_response.latency_ms = latency_ms

            # Update statistics
            self._stats['requests_made'] += 1
            if hasattr(llm_response, 'usage') and llm_response.usage:
                self._stats['total_tokens'] += llm_response.usage.total_tokens

            # Cache the response if caching is enabled
            if self.cache:
                cache_key = generate_cache_key(request.prompt, request.provider_params)
                self.cache.set(cache_key, llm_response)

            return llm_response

        except Exception as e:
            self._stats['errors'] += 1
            logger.error(
                "Text generation failed for request %s: %s",
                request.request_id, str(e)
            )
            raise

    @wrap_gemini_call
    def generate_with_system_instruction(
        self,
        request: LLMRequest,
        system_instruction: str
    ) -> LLMResponse:
        """
        Generate text with a system instruction.

        Args:
            request: LLM request containing prompt and parameters
            system_instruction: System instruction for the model

        Returns:
            LLMResponse with generated text
        """
        try:
            client = self._get_genai_client()

            # Map request with system instruction
            gemini_request = self.data_mapper.map_llm_request(request)

            # Add system instruction to the request
            if 'config' not in gemini_request:
                gemini_request['config'] = {}
            gemini_request['config']['system_instruction'] = system_instruction

            # Make API call with system instruction
            response = client.models.generate_content(
                model=self.config.model,
                contents=gemini_request.get('contents', []),
                config=gemini_request.get('config', {})
            )

            # Convert response
            llm_response = self.data_mapper.map_gemini_response(
                response,
                request_id=request.request_id,
                model=self.config.model
            )

            # Update statistics
            self._stats['requests_made'] += 1
            if hasattr(llm_response, 'usage') and llm_response.usage:
                self._stats['total_tokens'] += llm_response.usage.total_tokens

            return llm_response

        except Exception as e:
            self._stats['errors'] += 1
            logger.error(
                "System instruction generation failed for request %s: %s",
                request.request_id, str(e)
            )
            raise

    def select_optimal_model(
        self,
        request: LLMRequest,
        available_models: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Select the optimal model for the given request.

        Args:
            request: The LLM request
            available_models: Optional dict of available models and their specs

        Returns:
            The name of the optimal model
        """
        if available_models is None:
            available_models = {
                'gemini-pro': {
                    'context_window': 32768,
                    'cost_per_token': 0.00025,
                    'supports_functions': True
                },
                'gemini-pro-vision': {
                    'context_window': 16384,
                    'cost_per_token': 0.00025,
                    'supports_functions': True,
                    'supports_images': True
                }
            }

        # Simple model selection logic
        prompt_length = len(request.prompt)

        # If request includes images, use vision model
        if hasattr(request, 'images') and request.images:
            return 'gemini-pro-vision'

        # For very long prompts, check context window
        if prompt_length > 20000:
            for model, specs in available_models.items():
                if specs.get('context_window', 0) >= prompt_length * 2:  # Safety margin
                    return model

        # Default to the configured model or gemini-pro
        return self.config.model if self.config.model else 'gemini-pro'
