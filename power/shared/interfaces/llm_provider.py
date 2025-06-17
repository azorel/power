"""
Abstract interface for LLM providers.
All LLM adapters MUST implement this interface to ensure compatibility.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Callable, Generator
from shared.models.llm_request import LLMRequest
from shared.models.llm_response import LLMResponse, StreamingResponse


class LLMProvider(ABC):
    """Abstract base class for all LLM providers."""

    @abstractmethod
    def generate_text(self, request: LLMRequest) -> LLMResponse:
        """
        Generate text based on the provided request.

        Args:
            request: LLM request containing prompt and parameters

        Returns:
            LLM response with generated content and metadata

        Raises:
            LLMProviderError: Base exception for LLM-related errors
            RateLimitError: When rate limits are exceeded
            AuthenticationError: When API credentials are invalid
            QuotaExceededError: When usage quotas are exceeded
        """
        pass

    @abstractmethod
    def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> LLMResponse:
        """
        Generate chat completion from conversation messages.

        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            LLM response with generated content and metadata
        """
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.

        Returns:
            Dictionary containing model name, version, capabilities, etc.
        """
        pass

    @abstractmethod
    def validate_credentials(self) -> bool:
        """
        Validate API credentials without making a generation request.

        Returns:
            True if credentials are valid, False otherwise
        """
        pass

    @abstractmethod
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get current usage statistics and quota information.

        Returns:
            Dictionary with usage stats, quotas, rate limits, etc.
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of the LLM provider (e.g., 'gemini', 'openai')."""
        pass

    @property
    @abstractmethod
    def supported_features(self) -> List[str]:
        """
        Return list of supported features.

        Common features: 'text_generation', 'chat_completion',
                        'image_input', 'function_calling', 'streaming'
        """
        pass

    def is_feature_supported(self, feature: str) -> bool:
        """Check if a specific feature is supported by this provider."""
        return feature in self.supported_features


class MultiModalLLMProvider(LLMProvider):
    """Extended interface for LLM providers that support multimodal inputs."""

    @abstractmethod
    def generate_from_image(
        self,
        image_data: bytes,
        prompt: str,
        **kwargs
    ) -> LLMResponse:
        """
        Generate text based on image input and text prompt.

        Args:
            image_data: Raw image bytes
            prompt: Text prompt to accompany the image
            **kwargs: Additional parameters

        Returns:
            LLM response with generated content
        """
        pass

    @abstractmethod
    def get_supported_image_formats(self) -> List[str]:
        """Return list of supported image formats (e.g., ['jpeg', 'png', 'webp'])."""
        pass


class StreamingLLMProvider(LLMProvider):
    """Extended interface for LLM providers that support streaming responses."""

    @abstractmethod
    def generate_text_stream(self, request: LLMRequest):
        """
        Generate text with streaming response.

        Args:
            request: LLM request containing prompt and parameters

        Yields:
            Partial LLM responses as they become available
        """
        pass

    @abstractmethod
    def generate_chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ):
        """
        Generate chat completion with streaming response.

        Args:
            messages: List of message dicts
            **kwargs: Additional parameters

        Yields:
            Partial LLM responses as they become available
        """
        pass

class FunctionCallingLLMProvider(LLMProvider):
    """Extended interface for LLM providers that support function calling."""

    @abstractmethod
    def generate_with_functions(
        self,
        request: LLMRequest,
        functions: List[Dict[str, Any]],
        **kwargs
    ) -> LLMResponse:
        """
        Generate text with function calling capabilities.

        Args:
            request: LLM request containing prompt and parameters
            functions: List of function definitions available to the model
            **kwargs: Additional parameters (auto_execute, function_choice, etc.)

        Returns:
            LLM response with generated content and function call results
        """
        pass

    @abstractmethod
    def execute_function_call(
        self,
        function_name: str,
        function_args: Dict[str, Any],
        available_functions: Dict[str, Callable]
    ) -> Any:
        """
        Execute a function call requested by the model.

        Args:
            function_name: Name of the function to call
            function_args: Arguments to pass to the function
            available_functions: Dictionary of available functions

        Returns:
            Result of the function execution
        """
        pass


class ImageGenerationLLMProvider(LLMProvider):
    """Extended interface for LLM providers that support image generation."""

    @abstractmethod
    def generate_image(
        self,
        prompt: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate image based on text prompt.

        Args:
            prompt: Text description of the image to generate
            **kwargs: Additional parameters (size, style, quality, etc.)

        Returns:
            Dictionary containing image data and metadata
        """
        pass


class SystemInstructionLLMProvider(LLMProvider):
    """Extended interface for LLM providers that support system instructions."""

    @abstractmethod
    def generate_with_system_instruction(
        self,
        request: LLMRequest,
        system_instruction: str,
        **kwargs
    ) -> LLMResponse:
        """
        Generate text with a system instruction defining behavior.

        Args:
            request: LLM request containing prompt and parameters
            system_instruction: System-level instruction defining AI behavior
            **kwargs: Additional parameters

        Returns:
            LLM response following the system instruction
        """
        pass


class AdvancedLLMProvider(
    MultiModalLLMProvider,
    StreamingLLMProvider,
    FunctionCallingLLMProvider,
    ImageGenerationLLMProvider,
    SystemInstructionLLMProvider
):
    """
    Comprehensive interface for LLM providers with all advanced capabilities.
    Adapters implementing this interface support all available features.
    """

    @abstractmethod
    def get_advanced_capabilities(self) -> Dict[str, bool]:
        """
        Get detailed information about supported advanced capabilities.

        Returns:
            Dictionary mapping capability names to availability status
        """
        pass

    @abstractmethod
    def select_optimal_model(
        self,
        task_type: str,
        complexity: str = "medium",
        **kwargs
    ) -> str:
        """
        Select the optimal model for a specific task.

        Args:
            task_type: Type of task (text, image, function_calling, etc.)
            complexity: Task complexity (simple, medium, complex)
            **kwargs: Additional selection criteria

        Returns:
            Name of the optimal model for the task
        """
        pass
