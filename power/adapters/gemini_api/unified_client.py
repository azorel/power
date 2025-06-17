"""
Unified Gemini API client combining all capabilities.
"""

from shared.interfaces.llm_provider import AdvancedLLMProvider

from .text_client import GeminiTextClient
from .chat_client import GeminiChatClient
from .streaming_client import GeminiStreamingClient
from .multimodal_client import GeminiMultimodalClient
from .function_client import GeminiFunctionClient


class GeminiClient(
    GeminiTextClient,
    GeminiChatClient,
    GeminiStreamingClient,
    GeminiMultimodalClient,
    GeminiFunctionClient,
    AdvancedLLMProvider
):
    """
    Unified Gemini API client implementing all advanced LLM provider interfaces.
    Combines text generation, chat, multimodal, streaming, and function calling capabilities.
    """

    def __init__(self, config=None):
        """Initialize unified client."""
        # Initialize all parent classes with the same config
        super().__init__(config)
