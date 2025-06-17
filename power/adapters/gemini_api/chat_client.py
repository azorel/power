"""
Chat completion capabilities for Gemini API client.
"""

import logging
from typing import Dict, Any, List, Optional

from shared.models.llm_request import ChatMessage
from shared.models.llm_response import LLMResponse

from .base_client import GeminiBaseClient
from .exceptions import wrap_gemini_call

logger = logging.getLogger(__name__)


class GeminiChatClient(GeminiBaseClient):
    """
    Gemini client for chat completion operations.
    """

    @wrap_gemini_call
    def generate_chat_completion(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate chat completion based on conversation history.

        Args:
            messages: List of chat messages in conversation
            model: Optional model override
            max_tokens: Optional max tokens override
            temperature: Optional temperature override
            **kwargs: Additional parameters

        Returns:
            LLMResponse with chat completion
        """
        # Use provided model or fall back to config
        selected_model = model or self.config.model

        # Rate limiting
        self.rate_limiter.wait_if_needed()  # pylint: disable=no-member

        try:
            client = self._get_genai_client()

            # Convert messages to Gemini chat format
            gemini_request = self.data_mapper.map_chat_request(
                messages=messages,
                model=selected_model,
                max_tokens=max_tokens or self.config.default_max_tokens,
                temperature=temperature or self.config.default_temperature,
                **kwargs
            )

            # Make API call for chat
            response = client.models.generate_content(
                model=selected_model,
                contents=gemini_request.get('contents', []),
                config=gemini_request.get('generationConfig', {})
            )

            # Convert response
            llm_response = self.data_mapper.map_gemini_response(
                response,
                model=selected_model
            )

            # Update statistics
            self._stats['requests_made'] += 1
            if hasattr(llm_response, 'usage') and llm_response.usage:
                total_tokens = llm_response.usage.total_tokens or 0
                self._stats['total_tokens'] += total_tokens

            return llm_response
        except Exception as e:
            self._stats['errors'] += 1
            logger.error("Chat completion failed: %s", str(e))
            raise

    def _convert_messages_to_gemini_format(
        self,
        messages: List[ChatMessage]
    ) -> List[Dict[str, Any]]:
        """
        Convert ChatMessage objects to Gemini API format.

        Args:
            messages: List of ChatMessage objects

        Returns:
            List of messages in Gemini format
        """
        gemini_messages = []

        for message in messages:
            # Map role to Gemini format
            if message.role == 'user':
                role = 'user'
            elif message.role == 'assistant':
                role = 'model'
            elif message.role == 'system':
                # Gemini doesn't have system role, prepend to first user message
                continue
            else:
                role = 'user'  # Default fallback

            gemini_message = {
                'role': role,
                'parts': [{'text': message.content}]
            }

            # Handle images if present
            if hasattr(message, 'images') and message.images:
                for image in message.images:
                    gemini_message['parts'].append({
                        'inline_data': {
                            'mime_type': image.get('mime_type', 'image/jpeg'),
                            'data': image.get('data', '')
                        }
                    })

            gemini_messages.append(gemini_message)

        return gemini_messages

    def _handle_system_message(self, messages: List[ChatMessage]) -> tuple:
        """
        Extract system message and modify message list.

        Args:
            messages: Original message list

        Returns:
            Tuple of (system_instruction, filtered_messages)
        """
        system_instruction = None
        filtered_messages = []

        for message in messages:
            if message.role == 'system':
                if system_instruction is None:
                    system_instruction = message.content
                else:
                    # Combine multiple system messages
                    system_instruction += f"\n\n{message.content}"
            else:
                filtered_messages.append(message)

        return system_instruction, filtered_messages

    def continue_conversation(
        self,
        _conversation_id: str,
        new_message: ChatMessage,
        **kwargs
    ) -> LLMResponse:
        """
        Continue an existing conversation.

        Args:
            _conversation_id: Unique identifier for the conversation (unused)
            new_message: New message to add to conversation
            **kwargs: Additional parameters

        Returns:
            LLMResponse with continuation
        """
        # This would require conversation state management
        # For now, treat as single message
        return self.generate_chat_completion([new_message], **kwargs)

    def get_conversation_context(self, conversation_id: str) -> List[ChatMessage]:
        """
        Get conversation context by ID.

        Args:
            conversation_id: Unique identifier for the conversation

        Returns:
            List of messages in the conversation
        """
        # Placeholder - would require persistent storage
        logger.warning(
            "Conversation context not implemented for ID: %s",
            conversation_id
        )
        return []
