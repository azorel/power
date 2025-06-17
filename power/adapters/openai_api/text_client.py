"""
OpenAI text generation client.
Handles text completion using OpenAI's completion API.
"""

from typing import Optional, Dict, Any

from .base_client import BaseOpenAIClient
from .data_mapper import OpenAIDataMapper
from shared.models.llm_request import LLMRequest
from shared.models.llm_response import LLMResponse


class OpenAITextClient(BaseOpenAIClient):
    """
    OpenAI client for text completion tasks.
    Uses OpenAI's completion API for text generation.
    """

    def generate_text(self, request: LLMRequest) -> LLMResponse:
        """
        Generate text completion using OpenAI's completion API.
        
        Args:
            request: Shared LLM request
            
        Returns:
            Shared LLM response
        """
        self.logger.info(f"Generating text with model: {request.model or self.config.default_model}")
        
        # Map request to OpenAI format
        openai_request = OpenAIDataMapper.map_llm_request_to_openai(request)
        
        # Ensure model is set
        if not openai_request.get('model'):
            openai_request['model'] = self.config.default_model
        
        # Estimate tokens for rate limiting
        estimated_tokens = self.estimate_tokens(request.prompt)
        if request.max_tokens:
            estimated_tokens += request.max_tokens
        
        # Generate cache key if caching is enabled
        cache_key = None
        if self.config.enable_response_cache and not request.provider_params.get('no_cache'):
            cache_key = self._generate_cache_key(openai_request)
        
        # Moderate input if enabled
        if self.config.enable_moderation and self.config.moderate_input:
            self._moderate_content(request.prompt)
        
        self.logger.debug(f"Making text completion request: {openai_request}")
        
        # Make API call
        try:
            response = self._make_api_call(
                api_method=self.client.completions.create,
                request_data=openai_request,
                estimated_tokens=estimated_tokens,
                cache_key=cache_key
            )
        except Exception as e:
            self.logger.error(f"Text generation failed: {e}")
            raise
        
        # Convert response to shared format
        llm_response = OpenAIDataMapper.map_openai_response_to_llm_response(
            response,
            openai_request['model'],
            request.request_id
        )
        
        # Moderate output if enabled
        if self.config.enable_moderation and self.config.moderate_output:
            self._moderate_content(llm_response.content)
        
        self.logger.info(
            f"Text generation completed: {llm_response.usage.total_tokens} tokens, "
            f"finish_reason: {llm_response.finish_reason.value}"
        )
        
        return llm_response

    def generate_text_with_system_instruction(
        self,
        request: LLMRequest,
        system_instruction: str,
        **kwargs
    ) -> LLMResponse:
        """
        Generate text with a system instruction using chat completion.
        
        Args:
            request: Shared LLM request
            system_instruction: System-level instruction
            **kwargs: Additional parameters
            
        Returns:
            Shared LLM response
        """
        # Convert to chat format with system message
        messages = [
            {'role': 'system', 'content': system_instruction},
            {'role': 'user', 'content': request.prompt}
        ]
        
        # Use chat completion for system instructions
        from .chat_client import OpenAIChatClient
        chat_client = OpenAIChatClient(self.config)
        
        return chat_client.generate_chat_completion(
            messages=messages,
            model=request.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            frequency_penalty=request.frequency_penalty,
            presence_penalty=request.presence_penalty,
            stop_sequences=request.stop_sequences,
            seed=request.seed,
            response_format=request.response_format,
            **kwargs
        )

    def batch_generate_text(self, requests: list[LLMRequest]) -> list[LLMResponse]:
        """
        Generate text for multiple requests.
        Note: OpenAI doesn't have native batch API for completions,
        so we process sequentially with rate limiting.
        
        Args:
            requests: List of LLM requests
            
        Returns:
            List of LLM responses
        """
        self.logger.info(f"Processing batch of {len(requests)} text generation requests")
        
        responses = []
        for i, request in enumerate(requests):
            try:
                response = self.generate_text(request)
                responses.append(response)
                
                self.logger.debug(f"Completed batch request {i + 1}/{len(requests)}")
                
            except Exception as e:
                self.logger.error(f"Batch request {i + 1} failed: {e}")
                # Create error response
                from shared.models.llm_response import FinishReason, UsageStats
                error_response = LLMResponse(
                    content="",
                    finish_reason=FinishReason.ERROR,
                    usage=UsageStats(prompt_tokens=0, completion_tokens=0, total_tokens=0),
                    model=request.model or self.config.default_model,
                    provider='openai',
                    request_id=request.request_id,
                    provider_metadata={'error': str(e)}
                )
                responses.append(error_response)
        
        self.logger.info(f"Batch processing completed: {len(responses)} responses")
        return responses

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

    def get_model_info(self, model: Optional[str] = None) -> Dict[str, Any]:
        """
        Get information about a specific model.
        
        Args:
            model: Model name (uses default if None)
            
        Returns:
            Model information dictionary
        """
        model_name = model or self.config.default_model
        model_config = self.config.get_model_config(model_name)
        
        try:
            # Get model details from OpenAI API
            model_info = self.client.models.retrieve(model_name)
            
            return {
                'name': model_name,
                'id': model_info.id,
                'created': model_info.created,
                'owned_by': model_info.owned_by,
                'max_tokens': model_config.get('max_tokens', 4096),
                'supports_completion': True,
                'supports_chat': True,  # Most models support both
                'supports_vision': model_config.get('supports_vision', False),
                'supports_functions': model_config.get('supports_functions', False),
                'cost_per_1k_input_tokens': model_config.get('cost_per_1k_input_tokens'),
                'cost_per_1k_output_tokens': model_config.get('cost_per_1k_output_tokens'),
                'adapter': 'openai',
                'model_config': model_config
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get model info for {model_name}: {e}")
            
            # Return basic info from config
            return {
                'name': model_name,
                'max_tokens': model_config.get('max_tokens', 4096),
                'supports_completion': True,
                'supports_chat': True,
                'adapter': 'openai',
                'error': str(e)
            }

    def select_optimal_model(
        self,
        task_type: str,
        complexity: str = "medium",
        max_cost: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        Select optimal model for a task.
        
        Args:
            task_type: Type of task (text, analysis, etc.)
            complexity: Task complexity (simple, medium, complex)
            max_cost: Maximum cost per 1k tokens
            **kwargs: Additional selection criteria
            
        Returns:
            Optimal model name
        """
        # Model selection logic based on task requirements
        if complexity == "simple" or max_cost and max_cost < 0.001:
            return "gpt-3.5-turbo"
        elif complexity == "complex" or task_type in ["analysis", "reasoning", "code"]:
            return "gpt-4o"
        elif task_type == "creative" or task_type == "writing":
            return "gpt-4o"
        else:
            return "gpt-4o-mini"  # Good balance of cost and performance

    def estimate_cost(
        self, 
        prompt: str, 
        max_tokens: int = 1000, 
        model: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Estimate cost for a text generation request.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum completion tokens
            model: Model to use
            
        Returns:
            Cost estimation dictionary
        """
        model_name = model or self.config.default_model
        model_config = self.config.get_model_config(model_name)
        
        prompt_tokens = self.estimate_tokens(prompt)
        
        prompt_cost = (prompt_tokens / 1000) * model_config.get('cost_per_1k_input_tokens', 0)
        max_completion_cost = (max_tokens / 1000) * model_config.get('cost_per_1k_output_tokens', 0)
        
        return {
            'prompt_tokens': prompt_tokens,
            'max_completion_tokens': max_tokens,
            'estimated_prompt_cost': prompt_cost,
            'max_completion_cost': max_completion_cost,
            'max_total_cost': prompt_cost + max_completion_cost,
            'model': model_name
        }