"""
Unified OpenAI client implementing the complete AdvancedLLMProvider interface.
Combines all OpenAI capabilities into a single comprehensive client.
"""

from typing import List, Dict, Any, Optional, Callable, Generator
import logging

from .config import OpenAIConfig
from .text_client import OpenAITextClient
from .chat_client import OpenAIChatClient
from .streaming_client import OpenAIStreamingClient
from .multimodal_client import OpenAIMultimodalClient
from .function_client import OpenAIFunctionClient

from shared.interfaces.llm_provider import AdvancedLLMProvider
from shared.models.llm_request import LLMRequest
from shared.models.llm_response import LLMResponse, StreamingResponse
from shared.exceptions import LLMProviderError


class OpenAIUnifiedClient(AdvancedLLMProvider):
    """
    Unified OpenAI client implementing the complete AdvancedLLMProvider interface.
    Provides all OpenAI capabilities through a single, comprehensive interface.
    """

    def __init__(self, config: Optional[OpenAIConfig] = None):
        """
        Initialize the unified OpenAI client.
        
        Args:
            config: OpenAI configuration (creates default if None)
        """
        self.config = config or OpenAIConfig()
        self.logger = logging.getLogger('openai_adapter.unified_client')
        
        # Initialize specialized clients
        self._text_client = OpenAITextClient(self.config)
        self._chat_client = OpenAIChatClient(self.config)
        self._streaming_client = OpenAIStreamingClient(self.config)
        self._multimodal_client = OpenAIMultimodalClient(self.config)
        self._function_client = OpenAIFunctionClient(self.config)
        
        self.logger.info("OpenAI unified client initialized")

    # Core LLMProvider interface methods
    
    def generate_text(self, request: LLMRequest) -> LLMResponse:
        """Generate text based on the provided request."""
        return self._text_client.generate_text(request)

    def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> LLMResponse:
        """Generate chat completion from conversation messages."""
        return self._chat_client.generate_chat_completion(messages, **kwargs)

    def get_model_info(self, model: Optional[str] = None) -> Dict[str, Any]:
        """Get information about the current model."""
        return self._text_client.get_model_info(model)

    def validate_credentials(self) -> bool:
        """Validate API credentials without making a generation request."""
        return self._text_client.validate_credentials()

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics and quota information."""
        # Combine stats from all clients
        stats = {
            'provider': 'openai',
            'total_requests': 0,
            'total_tokens': 0,
            'total_cost': 0.0,
            'rate_limit_stats': None,
            'client_stats': {}
        }
        
        # Aggregate from all clients
        for client_name, client in [
            ('text', self._text_client),
            ('chat', self._chat_client),
            ('streaming', self._streaming_client),
            ('multimodal', self._multimodal_client),
            ('function', self._function_client)
        ]:
            client_stats = client.get_client_stats()
            stats['client_stats'][client_name] = client_stats
            
            stats['total_requests'] += client_stats.get('requests_made', 0)
            stats['total_tokens'] += client_stats.get('total_tokens_used', 0)
            stats['total_cost'] += client_stats.get('total_cost_usd', 0.0)
        
        # Use rate limit stats from primary client
        stats['rate_limit_stats'] = self._text_client.rate_limiter.get_openai_stats()
        
        return stats

    @property
    def provider_name(self) -> str:
        """Return the name of the LLM provider."""
        return 'openai'

    @property
    def supported_features(self) -> List[str]:
        """Return list of supported features."""
        return [
            'text_generation',
            'chat_completion',
            'image_input',
            'image_generation',
            'function_calling',
            'streaming',
            'system_instructions',
            'multimodal',
            'batch_processing'
        ]

    # MultiModalLLMProvider interface methods
    
    def generate_from_image(
        self,
        image_data: bytes,
        prompt: str,
        **kwargs
    ) -> LLMResponse:
        """Generate text based on image input and text prompt."""
        return self._multimodal_client.generate_from_image(image_data, prompt, **kwargs)

    def get_supported_image_formats(self) -> List[str]:
        """Return list of supported image formats."""
        return self._multimodal_client.get_supported_image_formats()

    # StreamingLLMProvider interface methods
    
    def generate_text_stream(self, request: LLMRequest):
        """Generate text with streaming response."""
        yield from self._streaming_client.generate_text_stream(request)

    def generate_chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ):
        """Generate chat completion with streaming response."""
        yield from self._streaming_client.generate_chat_completion_stream(messages, **kwargs)

    # FunctionCallingLLMProvider interface methods
    
    def generate_with_functions(
        self,
        request: LLMRequest,
        functions: List[Dict[str, Any]],
        **kwargs
    ) -> LLMResponse:
        """Generate text with function calling capabilities."""
        return self._function_client.generate_with_functions(request, functions, **kwargs)

    def execute_function_call(
        self,
        function_name: str,
        function_args: Dict[str, Any],
        available_functions: Dict[str, Callable]
    ) -> Any:
        """Execute a function call requested by the model."""
        return self._function_client.execute_function_call(
            function_name, function_args, available_functions
        )

    # ImageGenerationLLMProvider interface methods
    
    def generate_image(
        self,
        prompt: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate image based on text prompt."""
        return self._multimodal_client.generate_image(prompt, **kwargs)

    # SystemInstructionLLMProvider interface methods
    
    def generate_with_system_instruction(
        self,
        request: LLMRequest,
        system_instruction: str,
        **kwargs
    ) -> LLMResponse:
        """Generate text with a system instruction defining behavior."""
        return self._text_client.generate_text_with_system_instruction(
            request, system_instruction, **kwargs
        )

    # AdvancedLLMProvider interface methods
    
    def get_advanced_capabilities(self) -> Dict[str, bool]:
        """Get detailed information about supported advanced capabilities."""
        return {
            'text_generation': True,
            'chat_completion': True,
            'streaming': self.config.enable_streaming,
            'function_calling': self.config.enable_function_calling,
            'image_analysis': self.config.enable_vision,
            'image_generation': self.config.enable_image_generation,
            'multimodal': self.config.enable_vision,
            'system_instructions': True,
            'batch_processing': True,
            'fine_tuning': False,  # Not implemented in this adapter
            'embedding_generation': False,  # Would need separate implementation
            'moderation': self.config.enable_moderation,
            'audio_processing': False,  # Not implemented
            'code_execution': False,  # Not implemented
            'web_browsing': False,  # Not implemented
            'file_search': False  # Not implemented
        }

    def select_optimal_model(
        self,
        task_type: str,
        complexity: str = "medium",
        **kwargs
    ) -> str:
        """Select the optimal model for a specific task."""
        return self._text_client.select_optimal_model(task_type, complexity, **kwargs)

    # Extended functionality methods
    
    def generate_with_tools(
        self,
        request: LLMRequest,
        tools: List[Dict[str, Any]],
        **kwargs
    ) -> LLMResponse:
        """Generate text with tool calling capabilities (newer format)."""
        return self._function_client.generate_with_tools(request, tools, **kwargs)

    def generate_from_multiple_images(
        self,
        images: List[bytes],
        prompt: str,
        **kwargs
    ) -> LLMResponse:
        """Analyze multiple images in a single request."""
        return self._multimodal_client.generate_from_multiple_images(images, prompt, **kwargs)

    def edit_image(
        self,
        image_data: bytes,
        mask_data: Optional[bytes],
        prompt: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Edit an existing image using DALL-E."""
        return self._multimodal_client.edit_image(image_data, mask_data, prompt, **kwargs)

    def create_image_variation(
        self,
        image_data: bytes,
        **kwargs
    ) -> Dict[str, Any]:
        """Create variations of an existing image."""
        return self._multimodal_client.create_image_variation(image_data, **kwargs)

    def continue_conversation(
        self,
        conversation_history: List[Dict[str, str]],
        new_message: str,
        **kwargs
    ) -> LLMResponse:
        """Continue an existing conversation with a new message."""
        return self._chat_client.continue_conversation(conversation_history, new_message, **kwargs)

    def multi_turn_conversation(
        self,
        messages: List[Dict[str, str]],
        max_turns: int = 10,
        **kwargs
    ) -> List[LLMResponse]:
        """Handle multi-turn conversation with automatic turn management."""
        return self._chat_client.multi_turn_conversation(messages, max_turns, **kwargs)

    def multi_step_function_calling(
        self,
        initial_prompt: str,
        functions: List[Dict[str, Any]],
        available_functions: Dict[str, Callable],
        max_steps: int = 5,
        **kwargs
    ) -> List[LLMResponse]:
        """Perform multi-step function calling conversation."""
        return self._function_client.multi_step_function_calling(
            initial_prompt, functions, available_functions, max_steps, **kwargs
        )

    def batch_generate_text(self, requests: List[LLMRequest]) -> List[LLMResponse]:
        """Generate text for multiple requests."""
        return self._text_client.batch_generate_text(requests)

    def get_conversation_summary(
        self,
        messages: List[Dict[str, str]],
        summary_length: str = "medium"
    ) -> str:
        """Generate a summary of the conversation."""
        return self._chat_client.get_conversation_summary(messages, summary_length)

    def extract_key_points(self, messages: List[Dict[str, str]]) -> List[str]:
        """Extract key points from conversation."""
        return self._chat_client.extract_key_points(messages)

    def estimate_cost(
        self,
        prompt: str,
        max_tokens: int = 1000,
        model: Optional[str] = None
    ) -> Dict[str, float]:
        """Estimate cost for a text generation request."""
        return self._text_client.estimate_cost(prompt, max_tokens, model)

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        return self._text_client.estimate_tokens(text)

    def get_available_models(self) -> List[str]:
        """Get list of available models from OpenAI."""
        return self._text_client.get_available_models()

    def validate_image_data(self, image_data: bytes) -> Dict[str, Any]:
        """Validate image data and get metadata."""
        return self._multimodal_client.validate_image_data(image_data)

    def create_function_schema(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        required: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a function schema for OpenAI function calling."""
        return self._function_client.create_function_schema(name, description, parameters, required)

    def create_tool_schema(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        required: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a tool schema for OpenAI tool calling."""
        return self._function_client.create_tool_schema(name, description, parameters, required)

    # Client management methods
    
    def get_comprehensive_capabilities(self) -> Dict[str, Any]:
        """Get comprehensive information about all capabilities."""
        return {
            'provider': self.provider_name,
            'supported_features': self.supported_features,
            'advanced_capabilities': self.get_advanced_capabilities(),
            'vision_capabilities': self._multimodal_client.get_vision_capabilities(),
            'image_generation_capabilities': self._multimodal_client.get_image_generation_capabilities(),
            'function_calling_capabilities': self._function_client.get_function_calling_capabilities(),
            'supported_models': self.config.get_supported_models(),
            'configuration': self.config.to_dict()
        }

    def optimize_performance(self) -> Dict[str, Any]:
        """Analyze and optimize performance across all clients."""
        optimization_results = {
            'rate_limiter_optimization': self._text_client.rate_limiter.optimize_for_throughput(),
            'memory_optimization': {},
            'suggestions': []
        }
        
        # Memory optimization for all clients
        for client_name, client in [
            ('text', self._text_client),
            ('chat', self._chat_client),
            ('streaming', self._streaming_client),
            ('multimodal', self._multimodal_client),
            ('function', self._function_client)
        ]:
            if hasattr(client, 'cache') and client.cache:
                cache_stats = client.cache.get_stats()
                optimization_results['memory_optimization'][client_name] = cache_stats
        
        return optimization_results

    def close(self) -> None:
        """Clean up resources for all clients."""
        for client in [
            self._text_client,
            self._chat_client, 
            self._streaming_client,
            self._multimodal_client,
            self._function_client
        ]:
            if hasattr(client, 'close'):
                client.close()
        
        self.logger.info("OpenAI unified client closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def __repr__(self) -> str:
        """String representation of the client."""
        return f"OpenAIUnifiedClient(provider='{self.provider_name}', features={len(self.supported_features)})"