"""
OpenAI streaming client for real-time response generation.
Handles streaming text and chat completions.
"""

import json
from typing import Generator, List, Dict, Any, Optional

from .base_client import BaseOpenAIClient
from .data_mapper import OpenAIDataMapper
from shared.models.llm_request import LLMRequest
from shared.models.llm_response import StreamingResponse, LLMResponse, FinishReason, UsageStats


class OpenAIStreamingClient(BaseOpenAIClient):
    """
    OpenAI client for streaming responses.
    Provides real-time streaming for both text and chat completions.
    """

    def generate_text_stream(self, request: LLMRequest) -> Generator[StreamingResponse, None, LLMResponse]:
        """
        Generate streaming text completion.
        
        Args:
            request: Shared LLM request
            
        Yields:
            StreamingResponse objects with incremental content
            
        Returns:
            Final LLMResponse object
        """
        self.logger.info(f"Starting streaming text generation with model: {request.model or self.config.default_model}")
        
        # Map request to OpenAI format with streaming enabled
        openai_request = OpenAIDataMapper.map_llm_request_to_openai(request)
        openai_request['stream'] = True
        
        # Ensure model is set
        if not openai_request.get('model'):
            openai_request['model'] = self.config.default_model
        
        # Estimate tokens for rate limiting
        estimated_tokens = self.estimate_tokens(request.prompt)
        if request.max_tokens:
            estimated_tokens += request.max_tokens
        
        # Check rate limits before starting stream
        model = openai_request['model']
        if not self.rate_limiter.can_make_request(estimated_tokens, model):
            wait_time = self.rate_limiter.get_wait_time_for_tokens(estimated_tokens)
            from shared.exceptions import RateLimitError
            raise RateLimitError(
                f"Rate limit would be exceeded. Wait {wait_time:.1f} seconds.",
                retry_after=int(wait_time)
            )
        
        # Moderate input if enabled
        if self.config.enable_moderation and self.config.moderate_input:
            self._moderate_content(request.prompt)
        
        self.logger.debug("Making streaming text completion request")
        
        # Make streaming API call
        cumulative_content = ""
        chunk_index = 0
        final_response = None
        
        try:
            stream = self.client.completions.create(**openai_request)
            
            for chunk in stream:
                chunk_dict = chunk.model_dump() if hasattr(chunk, 'model_dump') else dict(chunk)
                
                # Extract content delta
                content_delta = ""
                if 'choices' in chunk_dict and chunk_dict['choices']:
                    choice = chunk_dict['choices'][0]
                    content_delta = choice.get('text', '')
                
                # Update cumulative content
                cumulative_content += content_delta
                
                # Check if this is the final chunk
                is_final = False
                if 'choices' in chunk_dict and chunk_dict['choices']:
                    choice = chunk_dict['choices'][0]
                    if choice.get('finish_reason') is not None:
                        is_final = True
                        
                        # Create final response
                        final_response = self._create_final_response_from_stream(
                            chunk_dict,
                            cumulative_content,
                            model,
                            request.request_id
                        )
                
                # Create streaming response
                streaming_response = StreamingResponse(
                    content_delta=content_delta,
                    cumulative_content=cumulative_content,
                    is_final=is_final,
                    chunk_index=chunk_index,
                    final_response=final_response if is_final else None
                )
                
                chunk_index += 1
                yield streaming_response
                
                if is_final:
                    break
            
            # Record usage
            if final_response:
                self._record_stream_usage(final_response, estimated_tokens, model)
            
        except Exception as e:
            self.logger.error(f"Streaming text generation failed: {e}")
            raise
        
        self.logger.info(f"Streaming text generation completed: {len(cumulative_content)} characters")
        return final_response

    def generate_chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Generator[StreamingResponse, None, LLMResponse]:
        """
        Generate streaming chat completion.
        
        Args:
            messages: List of message dictionaries
            **kwargs: Additional parameters
            
        Yields:
            StreamingResponse objects with incremental content
            
        Returns:
            Final LLMResponse object
        """
        model = kwargs.get('model', self.config.default_model)
        self.logger.info(f"Starting streaming chat completion with model: {model}")
        
        # Map request to OpenAI format with streaming enabled
        openai_request = OpenAIDataMapper.map_chat_request_to_openai(messages, stream=True, **kwargs)
        
        # Estimate tokens for rate limiting
        estimated_tokens = self._estimate_chat_tokens(messages)
        if kwargs.get('max_tokens'):
            estimated_tokens += kwargs['max_tokens']
        
        # Check rate limits before starting stream
        if not self.rate_limiter.can_make_request(estimated_tokens, model):
            wait_time = self.rate_limiter.get_wait_time_for_tokens(estimated_tokens)
            from shared.exceptions import RateLimitError
            raise RateLimitError(
                f"Rate limit would be exceeded. Wait {wait_time:.1f} seconds.",
                retry_after=int(wait_time)
            )
        
        # Moderate input if enabled
        if self.config.enable_moderation and self.config.moderate_input:
            self._moderate_messages(messages)
        
        self.logger.debug(f"Making streaming chat completion request: {len(messages)} messages")
        
        # Make streaming API call
        cumulative_content = ""
        chunk_index = 0
        final_response = None
        
        try:
            stream = self.client.chat.completions.create(**openai_request)
            
            for chunk in stream:
                chunk_dict = chunk.model_dump() if hasattr(chunk, 'model_dump') else dict(chunk)
                
                # Extract content delta
                content_delta = ""
                if 'choices' in chunk_dict and chunk_dict['choices']:
                    choice = chunk_dict['choices'][0]
                    if 'delta' in choice and 'content' in choice['delta']:
                        content_delta = choice['delta']['content'] or ""
                
                # Update cumulative content
                cumulative_content += content_delta
                
                # Check if this is the final chunk
                is_final = False
                if 'choices' in chunk_dict and chunk_dict['choices']:
                    choice = chunk_dict['choices'][0]
                    if choice.get('finish_reason') is not None:
                        is_final = True
                        
                        # Create final response
                        final_response = self._create_final_response_from_stream(
                            chunk_dict,
                            cumulative_content,
                            model,
                            kwargs.get('request_id')
                        )
                
                # Create streaming response
                streaming_response = StreamingResponse(
                    content_delta=content_delta,
                    cumulative_content=cumulative_content,
                    is_final=is_final,
                    chunk_index=chunk_index,
                    final_response=final_response if is_final else None
                )
                
                chunk_index += 1
                yield streaming_response
                
                if is_final:
                    break
            
            # Record usage
            if final_response:
                self._record_stream_usage(final_response, estimated_tokens, model)
            
        except Exception as e:
            self.logger.error(f"Streaming chat completion failed: {e}")
            raise
        
        self.logger.info(f"Streaming chat completion completed: {len(cumulative_content)} characters")
        return final_response

    def stream_with_function_calls(
        self,
        messages: List[Dict[str, str]],
        functions: List[Dict[str, Any]],
        **kwargs
    ) -> Generator[StreamingResponse, None, LLMResponse]:
        """
        Generate streaming chat completion with function calling support.
        
        Args:
            messages: List of message dictionaries
            functions: List of function definitions
            **kwargs: Additional parameters
            
        Yields:
            StreamingResponse objects with incremental content
            
        Returns:
            Final LLMResponse object
        """
        kwargs['functions'] = functions
        
        # Use regular streaming with function support
        yield from self.generate_chat_completion_stream(messages, **kwargs)

    def stream_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        **kwargs
    ) -> Generator[StreamingResponse, None, LLMResponse]:
        """
        Generate streaming chat completion with tools (newer function calling format).
        
        Args:
            messages: List of message dictionaries
            tools: List of tool definitions
            **kwargs: Additional parameters
            
        Yields:
            StreamingResponse objects with incremental content
            
        Returns:
            Final LLMResponse object
        """
        kwargs['tools'] = tools
        
        # Use regular streaming with tools support
        yield from self.generate_chat_completion_stream(messages, **kwargs)

    def _create_final_response_from_stream(
        self,
        final_chunk: Dict[str, Any],
        cumulative_content: str,
        model: str,
        request_id: Optional[str]
    ) -> LLMResponse:
        """
        Create final LLMResponse from the last streaming chunk.
        
        Args:
            final_chunk: Final chunk from stream
            cumulative_content: All accumulated content
            model: Model used
            request_id: Request identifier
            
        Returns:
            Final LLMResponse object
        """
        # Extract finish reason
        finish_reason = FinishReason.COMPLETED
        if 'choices' in final_chunk and final_chunk['choices']:
            choice = final_chunk['choices'][0]
            openai_finish_reason = choice.get('finish_reason', 'stop')
            finish_reason = OpenAIDataMapper._map_finish_reason(openai_finish_reason)
        
        # Create usage stats (streaming doesn't always provide these)
        usage_data = final_chunk.get('usage', {})
        if not usage_data:
            # Estimate usage if not provided
            estimated_prompt_tokens = self.estimate_tokens(cumulative_content) // 2  # Rough estimate
            estimated_completion_tokens = self.estimate_tokens(cumulative_content) - estimated_prompt_tokens
            usage_data = {
                'prompt_tokens': estimated_prompt_tokens,
                'completion_tokens': estimated_completion_tokens,
                'total_tokens': estimated_prompt_tokens + estimated_completion_tokens
            }
        
        usage = UsageStats(
            prompt_tokens=usage_data.get('prompt_tokens', 0),
            completion_tokens=usage_data.get('completion_tokens', 0),
            total_tokens=usage_data.get('total_tokens', 0)
        )
        
        # Calculate costs
        model_config = self.config.get_model_config(model)
        if model_config:
            usage.prompt_cost = (usage.prompt_tokens / 1000) * model_config.get('cost_per_1k_input_tokens', 0)
            usage.completion_cost = (usage.completion_tokens / 1000) * model_config.get('cost_per_1k_output_tokens', 0)
            usage.total_cost = usage.prompt_cost + usage.completion_cost
        
        # Create final response
        return LLMResponse(
            content=cumulative_content,
            finish_reason=finish_reason,
            usage=usage,
            model=model,
            provider='openai',
            response_id=final_chunk.get('id'),
            request_id=request_id,
            provider_metadata={
                'openai_response_id': final_chunk.get('id'),
                'openai_object': final_chunk.get('object'),
                'openai_created': final_chunk.get('created'),
                'streaming': True
            }
        )

    def _record_stream_usage(
        self,
        response: LLMResponse,
        estimated_tokens: int,
        model: str
    ) -> None:
        """
        Record usage from streaming response.
        
        Args:
            response: Final response object
            estimated_tokens: Original token estimate
            model: Model used
        """
        # Calculate cost
        cost = response.usage.total_cost if response.usage.total_cost else 0.0
        
        # Record in rate limiter
        self.rate_limiter.record_request(
            tokens_used=response.usage.total_tokens,
            cost=cost,
            model=model
        )
        
        # Update client stats
        self._request_count += 1
        self._total_tokens_used += response.usage.total_tokens
        self._total_cost += cost

    def _estimate_chat_tokens(self, messages: List[Dict[str, str]]) -> int:
        """
        Estimate total tokens for chat messages.
        
        Args:
            messages: List of messages
            
        Returns:
            Estimated token count
        """
        total_tokens = 0
        
        for message in messages:
            # OpenAI chat format has some overhead per message
            total_tokens += 4  # Overhead for role, content structure
            total_tokens += self.estimate_tokens(message.get('content', ''))
            if message.get('name'):
                total_tokens += self.estimate_tokens(message['name'])
        
        # Additional overhead for chat format
        total_tokens += 2
        
        return total_tokens

    def _moderate_messages(self, messages: List[Dict[str, str]]) -> None:
        """
        Moderate all messages in the conversation.
        
        Args:
            messages: List of messages to moderate
            
        Raises:
            ContentFilterError: If any message violates policies
        """
        for i, message in enumerate(messages):
            content = message.get('content', '')
            if content:
                try:
                    self._moderate_content(content)
                except Exception as e:
                    self.logger.error(f"Message {i} failed moderation: {e}")
                    raise

    def _moderate_content(self, content: str) -> None:
        """
        Moderate content using OpenAI's moderation API.
        
        Args:
            content: Content to moderate
            
        Raises:
            ContentFilterError: If content violates policies
        """
        try:
            moderation_response = self.client.moderations.create(input=content)
            
            if moderation_response.results and moderation_response.results[0].flagged:
                categories = moderation_response.results[0].categories
                flagged_categories = [
                    category for category, flagged in categories.__dict__.items()
                    if flagged
                ]
                
                from shared.exceptions import ContentFilterError
                raise ContentFilterError(
                    f"Content flagged by moderation: {', '.join(flagged_categories)}",
                    filter_reason=', '.join(flagged_categories)
                )
                
        except Exception as e:
            if isinstance(e, ContentFilterError):
                raise
            
            self.logger.warning(f"Content moderation failed: {e}")
            # Don't block the request if moderation fails

    def collect_stream_to_response(
        self,
        stream_generator: Generator[StreamingResponse, None, LLMResponse]
    ) -> LLMResponse:
        """
        Collect all streaming chunks into a single response.
        Useful for testing or when streaming isn't needed.
        
        Args:
            stream_generator: Generator from streaming method
            
        Returns:
            Complete LLMResponse
        """
        final_response = None
        
        for chunk in stream_generator:
            if chunk.is_final and chunk.final_response:
                final_response = chunk.final_response
                break
        
        if not final_response:
            raise LLMProviderError("Stream ended without final response")
        
        return final_response

    def get_streaming_stats(self) -> Dict[str, Any]:
        """Get statistics specific to streaming operations."""
        base_stats = self.get_client_stats()
        
        # Add streaming-specific metrics
        base_stats.update({
            'streaming_enabled': self.config.enable_streaming,
            'average_stream_latency': None,  # Would need to track this
            'streaming_efficiency': None     # Would need to calculate this
        })
        
        return base_stats