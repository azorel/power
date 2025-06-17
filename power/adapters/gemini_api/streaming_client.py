"""
Streaming capabilities for Gemini API client.
"""

import logging
from typing import Iterator, List, Optional

from shared.models.llm_request import LLMRequest, ChatMessage
from shared.models.llm_response import StreamingResponse

from .base_client import GeminiBaseClient
from .exceptions import wrap_gemini_call

logger = logging.getLogger(__name__)


class GeminiStreamingClient(GeminiBaseClient):
    """
    Gemini client for streaming operations.
    """

    @wrap_gemini_call
    def generate_text_stream(self, request: LLMRequest) -> Iterator[StreamingResponse]:
        """
        Generate streaming text response.

        Args:
            request: LLM request containing prompt and parameters

        Yields:
            StreamingResponse objects with partial content
        """
        # Rate limiting
        self.rate_limiter.wait_if_needed()

        try:
            client = self._get_genai_client()

            # Map request to Gemini format
            gemini_request = self.data_mapper.map_llm_request(request)

            # Enable streaming in config
            if 'config' not in gemini_request:
                gemini_request['config'] = {}
            gemini_request['config']['stream'] = True

            # Make streaming API call
            stream = client.models.generate_content_stream(
                model=self.config.model,
                contents=gemini_request.get('contents', []),
                config=gemini_request.get('config', {})
            )

            # Process streaming responses
            for chunk in stream:
                streaming_response = self._process_stream_chunk(
                    chunk,
                    request.request_id
                )
                if streaming_response:
                    yield streaming_response

            # Update statistics
            self._stats['requests_made'] += 1

        except Exception as e:
            self._stats['errors'] += 1
            logger.error(
                "Streaming text generation failed for request %s: %s",
                request.request_id, str(e)
            )
            raise

    @wrap_gemini_call
    def generate_chat_completion_stream(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        **kwargs
    ) -> Iterator[StreamingResponse]:
        """
        Generate streaming chat completion.

        Args:
            messages: List of chat messages
            model: Optional model override
            **kwargs: Additional parameters

        Yields:
            StreamingResponse objects with partial chat content
        """
        selected_model = model or self.config.model

        # Rate limiting
        self.rate_limiter.wait_if_needed()

        try:
            client = self._get_genai_client()

            # Convert messages to Gemini format
            gemini_request = self.data_mapper.map_chat_request(
                messages=messages,
                model=selected_model,
                **kwargs
            )

            # Enable streaming
            if 'config' not in gemini_request:
                gemini_request['config'] = {}
            gemini_request['config']['stream'] = True

            # Make streaming API call
            stream = client.models.generate_content_stream(
                model=selected_model,
                contents=gemini_request.get('contents', []),
                config=gemini_request.get('config', {})
            )

            # Process streaming responses
            for chunk in stream:
                streaming_response = self._process_stream_chunk(chunk)
                if streaming_response:
                    yield streaming_response

            # Update statistics
            self._stats['requests_made'] += 1

        except Exception as e:
            self._stats['errors'] += 1
            logger.error("Streaming chat completion failed: %s", str(e))
            raise

    def _process_stream_chunk(
        self,
        chunk,
        request_id: Optional[str] = None
    ) -> Optional[StreamingResponse]:
        """
        Process a single streaming chunk from Gemini API.

        Args:
            chunk: Raw chunk from Gemini streaming API
            request_id: Optional request ID for tracking

        Returns:
            StreamingResponse or None if chunk should be skipped
        """
        try:
            # Extract content from chunk - adjust based on actual API format
            if hasattr(chunk, 'candidates') and chunk.candidates:
                candidate = chunk.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    content = candidate.content.parts[0].text if candidate.content.parts else ""

                    # Determine if this is the final chunk
                    is_final = (
                        hasattr(chunk, 'finish_reason') and
                        chunk.finish_reason is not None
                    )

                    return StreamingResponse(
                        content=content,
                        is_final=is_final,
                        request_id=request_id,
                        model=self.config.model,
                        usage=self._extract_usage_from_chunk(chunk) if is_final else None
                    )

            return None

        except Exception as e:
            logger.warning("Failed to process stream chunk: %s", e)
            return None

    def _extract_usage_from_chunk(self, chunk) -> Optional[dict]:
        """
        Extract usage information from a streaming chunk.

        Args:
            chunk: Raw chunk from API

        Returns:
            Usage dictionary or None
        """
        try:
            if hasattr(chunk, 'usage_metadata'):
                usage = chunk.usage_metadata
                return {
                    'prompt_tokens': getattr(usage, 'prompt_token_count', 0),
                    'completion_tokens': getattr(usage, 'candidates_token_count', 0),
                    'total_tokens': getattr(usage, 'total_token_count', 0)
                }
        except Exception as e:
            logger.debug("Could not extract usage from chunk: %s", e)

        return None

    def stream_with_callback(
        self,
        request: LLMRequest,
        callback: callable,
        **kwargs
    ) -> None:
        """
        Stream text generation with callback for each chunk.

        Args:
            request: LLM request
            callback: Function to call with each StreamingResponse
            **kwargs: Additional parameters
        """
        try:
            for chunk in self.generate_text_stream(request, **kwargs):
                callback(chunk)
        except Exception as e:
            logger.error("Streaming with callback failed: %s", e)
            raise
