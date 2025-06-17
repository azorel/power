"""
OpenAI API data mapping and transformation.
Converts between shared models and OpenAI API format.
"""

import base64
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from shared.models.llm_request import LLMRequest, ChatMessage, ChatRequest
from shared.models.llm_response import LLMResponse, StreamingResponse, UsageStats, FinishReason


class OpenAIDataMapper:
    """Maps data between shared models and OpenAI API format."""

    @staticmethod
    def map_llm_request_to_openai(request: LLMRequest) -> Dict[str, Any]:
        """
        Convert shared LLMRequest to OpenAI completion format.
        
        Args:
            request: Shared LLM request
            
        Returns:
            Dictionary in OpenAI API format
        """
        openai_request = {
            'model': request.model or 'gpt-4o',
            'prompt': request.prompt,
            'max_tokens': request.max_tokens,
            'temperature': request.temperature,
            'top_p': request.top_p,
            'frequency_penalty': request.frequency_penalty,
            'presence_penalty': request.presence_penalty,
        }
        
        # Add stop sequences if provided
        if request.stop_sequences:
            openai_request['stop'] = request.stop_sequences
        
        # Add seed if provided (for reproducibility)
        if request.seed is not None:
            openai_request['seed'] = request.seed
        
        # Handle response format
        if request.response_format == 'json':
            openai_request['response_format'] = {'type': 'json_object'}
        
        # Add provider-specific parameters
        if request.provider_params:
            openai_request.update(request.provider_params)
        
        # Remove None values
        return {k: v for k, v in openai_request.items() if v is not None}

    @staticmethod
    def map_chat_request_to_openai(
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> Dict[str, Any]:
        """
        Convert chat messages and parameters to OpenAI chat completion format.
        
        Args:
            messages: List of message dictionaries
            **kwargs: Additional parameters
            
        Returns:
            Dictionary in OpenAI chat completion format
        """
        openai_request = {
            'model': kwargs.get('model', 'gpt-4o'),
            'messages': OpenAIDataMapper._format_messages(messages),
            'max_tokens': kwargs.get('max_tokens'),
            'temperature': kwargs.get('temperature'),
            'top_p': kwargs.get('top_p'),
            'frequency_penalty': kwargs.get('frequency_penalty'),
            'presence_penalty': kwargs.get('presence_penalty'),
        }
        
        # Add stop sequences
        if 'stop_sequences' in kwargs and kwargs['stop_sequences']:
            openai_request['stop'] = kwargs['stop_sequences']
        
        # Add seed for reproducibility
        if 'seed' in kwargs and kwargs['seed'] is not None:
            openai_request['seed'] = kwargs['seed']
        
        # Handle response format
        if kwargs.get('response_format') == 'json':
            openai_request['response_format'] = {'type': 'json_object'}
        
        # Add streaming flag
        if kwargs.get('stream', False):
            openai_request['stream'] = True
        
        # Add function calling if provided
        if 'functions' in kwargs and kwargs['functions']:
            openai_request['functions'] = kwargs['functions']
        
        if 'function_call' in kwargs:
            openai_request['function_call'] = kwargs['function_call']
        
        # Add tools if provided (newer function calling format)
        if 'tools' in kwargs and kwargs['tools']:
            openai_request['tools'] = kwargs['tools']
        
        if 'tool_choice' in kwargs:
            openai_request['tool_choice'] = kwargs['tool_choice']
        
        # Add provider-specific parameters
        if 'provider_params' in kwargs and kwargs['provider_params']:
            openai_request.update(kwargs['provider_params'])
        
        # Remove None values
        return {k: v for k, v in openai_request.items() if v is not None}

    @staticmethod
    def _format_messages(messages: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Format messages for OpenAI API."""
        formatted_messages = []
        
        for msg in messages:
            formatted_msg = {
                'role': msg['role'],
                'content': msg['content']
            }
            
            # Add name if provided
            if 'name' in msg and msg['name']:
                formatted_msg['name'] = msg['name']
            
            formatted_messages.append(formatted_msg)
        
        return formatted_messages

    @staticmethod
    def map_image_request_to_openai(
        prompt: str,
        image_data: bytes,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Convert image analysis request to OpenAI vision format.
        
        Args:
            prompt: Text prompt
            image_data: Raw image bytes
            **kwargs: Additional parameters
            
        Returns:
            Dictionary in OpenAI vision format
        """
        # Encode image as base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        image_format = kwargs.get('image_format', 'png')
        
        openai_request = {
            'model': kwargs.get('model', 'gpt-4o'),
            'messages': [
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': prompt
                        },
                        {
                            'type': 'image_url',
                            'image_url': {
                                'url': f'data:image/{image_format};base64,{image_base64}',
                                'detail': kwargs.get('detail', 'auto')
                            }
                        }
                    ]
                }
            ],
            'max_tokens': kwargs.get('max_tokens', 1000),
            'temperature': kwargs.get('temperature', 0.7)
        }
        
        return openai_request

    @staticmethod
    def map_openai_response_to_llm_response(
        openai_response: Dict[str, Any],
        model: str,
        request_id: Optional[str] = None
    ) -> LLMResponse:
        """
        Convert OpenAI response to shared LLMResponse.
        
        Args:
            openai_response: OpenAI API response
            model: Model name used
            request_id: Request identifier
            
        Returns:
            Shared LLMResponse object
        """
        # Extract content
        content = ""
        finish_reason = FinishReason.COMPLETED
        
        if 'choices' in openai_response and openai_response['choices']:
            choice = openai_response['choices'][0]
            
            # Get content from different response formats
            if 'text' in choice:
                content = choice['text']
            elif 'message' in choice:
                content = choice['message'].get('content', '')
            
            # Map finish reason
            openai_finish_reason = choice.get('finish_reason', 'stop')
            finish_reason = OpenAIDataMapper._map_finish_reason(openai_finish_reason)
        
        # Extract usage statistics
        usage_data = openai_response.get('usage', {})
        usage = UsageStats(
            prompt_tokens=usage_data.get('prompt_tokens', 0),
            completion_tokens=usage_data.get('completion_tokens', 0),
            total_tokens=usage_data.get('total_tokens', 0)
        )
        
        # Calculate costs if possible (rough estimates)
        model_config = OpenAIDataMapper._get_model_pricing(model)
        if model_config:
            usage.prompt_cost = (usage.prompt_tokens / 1000) * model_config.get('prompt_cost', 0)
            usage.completion_cost = (usage.completion_tokens / 1000) * model_config.get('completion_cost', 0)
            usage.total_cost = usage.prompt_cost + usage.completion_cost
        
        # Extract metadata
        response_id = openai_response.get('id')
        created_timestamp = openai_response.get('created')
        
        # Create response
        return LLMResponse(
            content=content,
            finish_reason=finish_reason,
            usage=usage,
            model=model,
            provider='openai',
            response_id=response_id,
            request_id=request_id,
            timestamp=datetime.fromtimestamp(created_timestamp) if created_timestamp else datetime.now(),
            provider_metadata={
                'openai_response_id': response_id,
                'openai_object': openai_response.get('object'),
                'openai_created': created_timestamp,
                'openai_model': openai_response.get('model', model)
            }
        )

    @staticmethod
    def map_openai_stream_chunk_to_streaming_response(
        chunk: Dict[str, Any],
        cumulative_content: str,
        chunk_index: int
    ) -> StreamingResponse:
        """
        Convert OpenAI streaming chunk to shared StreamingResponse.
        
        Args:
            chunk: OpenAI streaming chunk
            cumulative_content: Content accumulated so far
            chunk_index: Index of this chunk
            
        Returns:
            Shared StreamingResponse object
        """
        # Extract delta content
        content_delta = ""
        is_final = False
        
        if 'choices' in chunk and chunk['choices']:
            choice = chunk['choices'][0]
            
            # Check if this is the final chunk
            if choice.get('finish_reason') is not None:
                is_final = True
            
            # Extract content delta
            if 'delta' in choice:
                delta = choice['delta']
                content_delta = delta.get('content', '')
        
        return StreamingResponse(
            content_delta=content_delta,
            cumulative_content=cumulative_content,
            is_final=is_final,
            chunk_index=chunk_index,
            timestamp=datetime.now()
        )

    @staticmethod
    def _map_finish_reason(openai_finish_reason: str) -> FinishReason:
        """Map OpenAI finish reason to shared FinishReason."""
        mapping = {
            'stop': FinishReason.COMPLETED,
            'length': FinishReason.MAX_TOKENS,
            'content_filter': FinishReason.CONTENT_FILTER,
            'function_call': FinishReason.COMPLETED,
            'tool_calls': FinishReason.COMPLETED,
            'null': FinishReason.ERROR
        }
        
        return mapping.get(openai_finish_reason, FinishReason.ERROR)

    @staticmethod
    def _get_model_pricing(model: str) -> Optional[Dict[str, float]]:
        """Get pricing information for model (rough estimates)."""
        pricing = {
            'gpt-4o': {'prompt_cost': 0.005, 'completion_cost': 0.015},
            'gpt-4o-mini': {'prompt_cost': 0.00015, 'completion_cost': 0.0006},
            'gpt-4-turbo': {'prompt_cost': 0.01, 'completion_cost': 0.03},
            'gpt-4': {'prompt_cost': 0.03, 'completion_cost': 0.06},
            'gpt-3.5-turbo': {'prompt_cost': 0.0005, 'completion_cost': 0.0015}
        }
        
        return pricing.get(model)

    @staticmethod
    def create_function_schema(
        name: str,
        description: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create OpenAI function schema.
        
        Args:
            name: Function name
            description: Function description
            parameters: JSON schema for parameters
            
        Returns:
            OpenAI function schema
        """
        return {
            'name': name,
            'description': description,
            'parameters': parameters
        }

    @staticmethod
    def create_tool_schema(
        name: str,
        description: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create OpenAI tool schema (newer format).
        
        Args:
            name: Tool name
            description: Tool description
            parameters: JSON schema for parameters
            
        Returns:
            OpenAI tool schema
        """
        return {
            'type': 'function',
            'function': {
                'name': name,
                'description': description,
                'parameters': parameters
            }
        }

    @staticmethod
    def extract_function_calls(openai_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract function calls from OpenAI response.
        
        Args:
            openai_response: OpenAI API response
            
        Returns:
            List of function call dictionaries
        """
        function_calls = []
        
        if 'choices' in openai_response and openai_response['choices']:
            choice = openai_response['choices'][0]
            
            # Check for function_call (legacy format)
            if 'message' in choice and 'function_call' in choice['message']:
                func_call = choice['message']['function_call']
                function_calls.append({
                    'name': func_call.get('name'),
                    'arguments': func_call.get('arguments')
                })
            
            # Check for tool_calls (newer format)
            if 'message' in choice and 'tool_calls' in choice['message']:
                for tool_call in choice['message']['tool_calls']:
                    if tool_call.get('type') == 'function':
                        function = tool_call.get('function', {})
                        function_calls.append({
                            'id': tool_call.get('id'),
                            'name': function.get('name'),
                            'arguments': function.get('arguments')
                        })
        
        return function_calls