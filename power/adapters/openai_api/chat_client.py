"""
OpenAI chat completion client.
Handles chat-based interactions using OpenAI's chat completion API.
"""

from typing import List, Dict, Any, Optional

from .base_client import BaseOpenAIClient
from .data_mapper import OpenAIDataMapper
from shared.models.llm_response import LLMResponse


class OpenAIChatClient(BaseOpenAIClient):
    """
    OpenAI client for chat completion tasks.
    Uses OpenAI's chat completion API for conversational interactions.
    """

    def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> LLMResponse:
        """
        Generate chat completion using OpenAI's chat completion API.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            Shared LLM response
        """
        model = kwargs.get('model', self.config.default_model)
        self.logger.info(f"Generating chat completion with model: {model}")
        
        # Map request to OpenAI format
        openai_request = OpenAIDataMapper.map_chat_request_to_openai(messages, **kwargs)
        
        # Estimate tokens for rate limiting
        estimated_tokens = self._estimate_chat_tokens(messages)
        if kwargs.get('max_tokens'):
            estimated_tokens += kwargs['max_tokens']
        
        # Generate cache key if caching is enabled
        cache_key = None
        if (self.config.enable_response_cache and 
            not kwargs.get('stream', False) and 
            not kwargs.get('no_cache', False)):
            cache_key = self._generate_cache_key(openai_request)
        
        # Moderate input if enabled
        if self.config.enable_moderation and self.config.moderate_input:
            self._moderate_messages(messages)
        
        self.logger.debug(f"Making chat completion request: {len(messages)} messages")
        
        # Make API call
        try:
            response = self._make_api_call(
                api_method=self.client.chat.completions.create,
                request_data=openai_request,
                estimated_tokens=estimated_tokens,
                cache_key=cache_key
            )
        except Exception as e:
            self.logger.error(f"Chat completion failed: {e}")
            raise
        
        # Convert response to shared format
        llm_response = OpenAIDataMapper.map_openai_response_to_llm_response(
            response,
            openai_request['model'],
            kwargs.get('request_id')
        )
        
        # Moderate output if enabled
        if self.config.enable_moderation and self.config.moderate_output:
            self._moderate_content(llm_response.content)
        
        self.logger.info(
            f"Chat completion completed: {llm_response.usage.total_tokens} tokens, "
            f"finish_reason: {llm_response.finish_reason.value}"
        )
        
        return llm_response

    def generate_chat_completion_with_system(
        self,
        user_message: str,
        system_message: str,
        **kwargs
    ) -> LLMResponse:
        """
        Generate chat completion with system and user message.
        
        Args:
            user_message: User's message
            system_message: System instruction
            **kwargs: Additional parameters
            
        Returns:
            Shared LLM response
        """
        messages = [
            {'role': 'system', 'content': system_message},
            {'role': 'user', 'content': user_message}
        ]
        
        return self.generate_chat_completion(messages, **kwargs)

    def continue_conversation(
        self,
        conversation_history: List[Dict[str, str]],
        new_message: str,
        **kwargs
    ) -> LLMResponse:
        """
        Continue an existing conversation with a new message.
        
        Args:
            conversation_history: Previous messages in conversation
            new_message: New user message to add
            **kwargs: Additional parameters
            
        Returns:
            Shared LLM response
        """
        # Add new user message to conversation
        messages = conversation_history + [
            {'role': 'user', 'content': new_message}
        ]
        
        return self.generate_chat_completion(messages, **kwargs)

    def multi_turn_conversation(
        self,
        messages: List[Dict[str, str]],
        max_turns: int = 10,
        **kwargs
    ) -> List[LLMResponse]:
        """
        Handle multi-turn conversation with automatic turn management.
        
        Args:
            messages: Initial messages
            max_turns: Maximum number of turns
            **kwargs: Additional parameters
            
        Returns:
            List of LLM responses for each turn
        """
        responses = []
        current_messages = messages.copy()
        
        for turn in range(max_turns):
            try:
                response = self.generate_chat_completion(current_messages, **kwargs)
                responses.append(response)
                
                # Add assistant response to conversation
                current_messages.append({
                    'role': 'assistant',
                    'content': response.content
                })
                
                self.logger.debug(f"Completed turn {turn + 1}/{max_turns}")
                
                # Check if conversation should end
                if response.finish_reason.value in ['stop', 'function_call']:
                    break
                    
            except Exception as e:
                self.logger.error(f"Multi-turn conversation failed at turn {turn + 1}: {e}")
                break
        
        return responses

    def generate_with_context_window_management(
        self,
        messages: List[Dict[str, str]],
        max_context_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate chat completion with automatic context window management.
        
        Args:
            messages: Input messages
            max_context_tokens: Maximum tokens to use for context
            **kwargs: Additional parameters
            
        Returns:
            Shared LLM response
        """
        model = kwargs.get('model', self.config.default_model)
        model_config = self.config.get_model_config(model)
        
        if not max_context_tokens:
            max_context_tokens = model_config.get('context_length', 8192) // 2
        
        # Estimate tokens and truncate if needed
        truncated_messages = self._truncate_messages_to_fit(messages, max_context_tokens)
        
        if len(truncated_messages) < len(messages):
            self.logger.warning(
                f"Truncated conversation from {len(messages)} to {len(truncated_messages)} messages "
                f"to fit context window"
            )
        
        return self.generate_chat_completion(truncated_messages, **kwargs)

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

    def _truncate_messages_to_fit(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int
    ) -> List[Dict[str, str]]:
        """
        Truncate message list to fit within token limit.
        
        Args:
            messages: Original messages
            max_tokens: Maximum tokens allowed
            
        Returns:
            Truncated message list
        """
        if not messages:
            return messages
        
        # Always keep system message if present
        system_messages = [msg for msg in messages if msg.get('role') == 'system']
        other_messages = [msg for msg in messages if msg.get('role') != 'system']
        
        # Start with system messages
        result_messages = system_messages.copy()
        current_tokens = self._estimate_chat_tokens(system_messages)
        
        # Add other messages from the end (most recent first)
        for message in reversed(other_messages):
            message_tokens = self._estimate_chat_tokens([message])
            
            if current_tokens + message_tokens <= max_tokens:
                result_messages.insert(-len(system_messages) if system_messages else 0, message)
                current_tokens += message_tokens
            else:
                break
        
        return result_messages

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

    def get_conversation_summary(
        self,
        messages: List[Dict[str, str]],
        summary_length: str = "medium"
    ) -> str:
        """
        Generate a summary of the conversation.
        
        Args:
            messages: Conversation messages
            summary_length: Length of summary (short, medium, long)
            
        Returns:
            Conversation summary
        """
        if not messages:
            return "Empty conversation"
        
        # Create summarization prompt
        conversation_text = "\n".join([
            f"{msg['role']}: {msg['content']}" for msg in messages
        ])
        
        length_instruction = {
            "short": "in 1-2 sentences",
            "medium": "in 1-2 paragraphs", 
            "long": "in detail with key points"
        }.get(summary_length, "in 1-2 paragraphs")
        
        summary_prompt = f"""Please summarize the following conversation {length_instruction}:

{conversation_text}

Summary:"""
        
        try:
            response = self.generate_chat_completion([
                {'role': 'user', 'content': summary_prompt}
            ], max_tokens=500, temperature=0.3)
            
            return response.content.strip()
            
        except Exception as e:
            self.logger.error(f"Failed to generate conversation summary: {e}")
            return f"Error generating summary: {e}"

    def extract_key_points(self, messages: List[Dict[str, str]]) -> List[str]:
        """
        Extract key points from conversation.
        
        Args:
            messages: Conversation messages
            
        Returns:
            List of key points
        """
        if not messages:
            return []
        
        conversation_text = "\n".join([
            f"{msg['role']}: {msg['content']}" for msg in messages
        ])
        
        extraction_prompt = f"""Extract the key points from this conversation as a bulleted list:

{conversation_text}

Key points:"""
        
        try:
            response = self.generate_chat_completion([
                {'role': 'user', 'content': extraction_prompt}
            ], max_tokens=300, temperature=0.2)
            
            # Parse bullet points
            content = response.content.strip()
            lines = content.split('\n')
            key_points = []
            
            for line in lines:
                line = line.strip()
                if line.startswith(('•', '-', '*', '1.', '2.', '3.')):
                    key_points.append(line.lstrip('•-*123456789. ').strip())
            
            return key_points
            
        except Exception as e:
            self.logger.error(f"Failed to extract key points: {e}")
            return []