"""
OpenAI function calling client.
Handles function/tool calling capabilities with OpenAI models.
"""

import json
from typing import List, Dict, Any, Optional, Callable, Union

from .base_client import BaseOpenAIClient
from .data_mapper import OpenAIDataMapper
from shared.models.llm_request import LLMRequest
from shared.models.llm_response import LLMResponse


class OpenAIFunctionClient(BaseOpenAIClient):
    """
    OpenAI client for function calling capabilities.
    Supports both legacy 'functions' and new 'tools' format.
    """

    def generate_with_functions(
        self,
        request: LLMRequest,
        functions: List[Dict[str, Any]],
        **kwargs
    ) -> LLMResponse:
        """
        Generate text with function calling capabilities (legacy format).
        
        Args:
            request: Shared LLM request
            functions: List of function definitions
            **kwargs: Additional parameters
            
        Returns:
            Shared LLM response with function call results
        """
        model = request.model or self.config.default_model
        
        self.logger.info(f"Generating with functions using model: {model}")
        
        # Validate model supports function calling
        if not self._model_supports_functions(model):
            raise ValueError(f"Model {model} does not support function calling")
        
        # Convert LLMRequest to chat format for function calling
        messages = [{'role': 'user', 'content': request.prompt}]
        
        # Map to OpenAI format with functions
        openai_request = OpenAIDataMapper.map_chat_request_to_openai(
            messages=messages,
            model=model,
            functions=functions,
            function_call=kwargs.get('function_call', 'auto'),
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            frequency_penalty=request.frequency_penalty,
            presence_penalty=request.presence_penalty,
            **kwargs
        )
        
        # Estimate tokens
        estimated_tokens = self._estimate_function_tokens(messages, functions)
        if request.max_tokens:
            estimated_tokens += request.max_tokens
        
        self.logger.debug(f"Making function calling request with {len(functions)} functions")
        
        # Make API call
        try:
            response = self._make_api_call(
                api_method=self.client.chat.completions.create,
                request_data=openai_request,
                estimated_tokens=estimated_tokens
            )
        except Exception as e:
            self.logger.error(f"Function calling request failed: {e}")
            raise
        
        # Process function calls if present
        function_calls = OpenAIDataMapper.extract_function_calls(response)
        
        if function_calls and kwargs.get('auto_execute', False):
            available_functions = kwargs.get('available_functions', {})
            response = self._execute_function_calls_and_continue(
                response, function_calls, available_functions, messages, openai_request
            )
        
        # Convert to shared format
        llm_response = OpenAIDataMapper.map_openai_response_to_llm_response(
            response,
            model,
            request.request_id
        )
        
        # Add function call metadata
        if function_calls:
            llm_response.provider_metadata['function_calls'] = function_calls
        
        self.logger.info(
            f"Function calling completed: {llm_response.usage.total_tokens} tokens, "
            f"{len(function_calls)} function calls"
        )
        
        return llm_response

    def generate_with_tools(
        self,
        request: LLMRequest,
        tools: List[Dict[str, Any]],
        **kwargs
    ) -> LLMResponse:
        """
        Generate text with tool calling capabilities (new format).
        
        Args:
            request: Shared LLM request
            tools: List of tool definitions
            **kwargs: Additional parameters
            
        Returns:
            Shared LLM response with tool call results
        """
        model = request.model or self.config.default_model
        
        self.logger.info(f"Generating with tools using model: {model}")
        
        # Validate model supports tool calling
        if not self._model_supports_functions(model):
            raise ValueError(f"Model {model} does not support tool calling")
        
        # Convert LLMRequest to chat format
        messages = [{'role': 'user', 'content': request.prompt}]
        
        # Map to OpenAI format with tools
        openai_request = OpenAIDataMapper.map_chat_request_to_openai(
            messages=messages,
            model=model,
            tools=tools,
            tool_choice=kwargs.get('tool_choice', 'auto'),
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            frequency_penalty=request.frequency_penalty,
            presence_penalty=request.presence_penalty,
            **kwargs
        )
        
        # Estimate tokens
        estimated_tokens = self._estimate_tool_tokens(messages, tools)
        if request.max_tokens:
            estimated_tokens += request.max_tokens
        
        self.logger.debug(f"Making tool calling request with {len(tools)} tools")
        
        # Make API call
        try:
            response = self._make_api_call(
                api_method=self.client.chat.completions.create,
                request_data=openai_request,
                estimated_tokens=estimated_tokens
            )
        except Exception as e:
            self.logger.error(f"Tool calling request failed: {e}")
            raise
        
        # Process tool calls if present
        tool_calls = self._extract_tool_calls(response)
        
        if tool_calls and kwargs.get('auto_execute', False):
            available_functions = kwargs.get('available_functions', {})
            response = self._execute_tool_calls_and_continue(
                response, tool_calls, available_functions, messages, openai_request
            )
        
        # Convert to shared format
        llm_response = OpenAIDataMapper.map_openai_response_to_llm_response(
            response,
            model,
            request.request_id
        )
        
        # Add tool call metadata
        if tool_calls:
            llm_response.provider_metadata['tool_calls'] = tool_calls
        
        self.logger.info(
            f"Tool calling completed: {llm_response.usage.total_tokens} tokens, "
            f"{len(tool_calls)} tool calls"
        )
        
        return llm_response

    def execute_function_call(
        self,
        function_name: str,
        function_args: Dict[str, Any],
        available_functions: Dict[str, Callable]
    ) -> Any:
        """
        Execute a function call requested by the model.
        
        Args:
            function_name: Name of function to call
            function_args: Arguments for the function
            available_functions: Dictionary of available functions
            
        Returns:
            Result of function execution
        """
        self.logger.info(f"Executing function: {function_name}")
        
        if function_name not in available_functions:
            raise ValueError(f"Function '{function_name}' is not available")
        
        function = available_functions[function_name]
        
        try:
            # Parse arguments if they're JSON string
            if isinstance(function_args, str):
                function_args = json.loads(function_args)
            
            # Execute function
            result = function(**function_args)
            
            self.logger.debug(f"Function {function_name} executed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Function {function_name} execution failed: {e}")
            return {'error': str(e)}

    def create_function_schema(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        required: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a function schema for OpenAI function calling.
        
        Args:
            name: Function name
            description: Function description
            parameters: Parameter schema (JSON Schema format)
            required: List of required parameter names
            
        Returns:
            OpenAI function schema
        """
        schema = {
            'name': name,
            'description': description,
            'parameters': {
                'type': 'object',
                'properties': parameters
            }
        }
        
        if required:
            schema['parameters']['required'] = required
        
        return schema

    def create_tool_schema(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        required: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a tool schema for OpenAI tool calling.
        
        Args:
            name: Tool name
            description: Tool description
            parameters: Parameter schema (JSON Schema format)
            required: List of required parameter names
            
        Returns:
            OpenAI tool schema
        """
        return {
            'type': 'function',
            'function': self.create_function_schema(name, description, parameters, required)
        }

    def multi_step_function_calling(
        self,
        initial_prompt: str,
        functions: List[Dict[str, Any]],
        available_functions: Dict[str, Callable],
        max_steps: int = 5,
        **kwargs
    ) -> List[LLMResponse]:
        """
        Perform multi-step function calling conversation.
        
        Args:
            initial_prompt: Initial user prompt
            functions: Available function definitions
            available_functions: Callable functions
            max_steps: Maximum conversation steps
            **kwargs: Additional parameters
            
        Returns:
            List of responses for each step
        """
        model = kwargs.get('model', self.config.default_model)
        
        self.logger.info(f"Starting multi-step function calling with {len(functions)} functions")
        
        messages = [{'role': 'user', 'content': initial_prompt}]
        responses = []
        
        for step in range(max_steps):
            # Make request with current conversation
            openai_request = OpenAIDataMapper.map_chat_request_to_openai(
                messages=messages,
                model=model,
                functions=functions,
                function_call='auto',
                **kwargs
            )
            
            try:
                response = self._make_api_call(
                    api_method=self.client.chat.completions.create,
                    request_data=openai_request,
                    estimated_tokens=self._estimate_function_tokens(messages, functions)
                )
                
                # Convert to shared format
                llm_response = OpenAIDataMapper.map_openai_response_to_llm_response(
                    response, model
                )
                responses.append(llm_response)
                
                # Add assistant message to conversation
                if 'choices' in response and response['choices']:
                    choice = response['choices'][0]
                    if 'message' in choice:
                        messages.append(choice['message'])
                
                # Check for function calls
                function_calls = OpenAIDataMapper.extract_function_calls(response)
                
                if function_calls:
                    # Execute function calls and add results
                    for func_call in function_calls:
                        try:
                            result = self.execute_function_call(
                                func_call['name'],
                                func_call.get('arguments', '{}'),
                                available_functions
                            )
                            
                            # Add function result to conversation
                            messages.append({
                                'role': 'function',
                                'name': func_call['name'],
                                'content': json.dumps(result)
                            })
                            
                        except Exception as e:
                            self.logger.error(f"Function execution failed: {e}")
                            messages.append({
                                'role': 'function',
                                'name': func_call['name'],
                                'content': json.dumps({'error': str(e)})
                            })
                else:
                    # No more function calls, conversation complete
                    break
                    
            except Exception as e:
                self.logger.error(f"Multi-step function calling failed at step {step + 1}: {e}")
                break
        
        self.logger.info(f"Multi-step function calling completed in {len(responses)} steps")
        return responses

    def _execute_function_calls_and_continue(
        self,
        response: Dict[str, Any],
        function_calls: List[Dict[str, Any]],
        available_functions: Dict[str, Callable],
        messages: List[Dict[str, str]],
        original_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute function calls and continue the conversation."""
        # Add assistant message with function call
        if 'choices' in response and response['choices']:
            choice = response['choices'][0]
            if 'message' in choice:
                messages.append(choice['message'])
        
        # Execute each function call
        for func_call in function_calls:
            try:
                result = self.execute_function_call(
                    func_call['name'],
                    func_call.get('arguments', '{}'),
                    available_functions
                )
                
                # Add function result to conversation
                messages.append({
                    'role': 'function',
                    'name': func_call['name'],
                    'content': json.dumps(result)
                })
                
            except Exception as e:
                self.logger.error(f"Function execution failed: {e}")
                messages.append({
                    'role': 'function',
                    'name': func_call['name'],
                    'content': json.dumps({'error': str(e)})
                })
        
        # Continue conversation with function results
        original_request['messages'] = messages
        continued_response = self._make_api_call(
            api_method=self.client.chat.completions.create,
            request_data=original_request,
            estimated_tokens=self._estimate_function_tokens(messages, [])
        )
        
        return continued_response

    def _execute_tool_calls_and_continue(
        self,
        response: Dict[str, Any],
        tool_calls: List[Dict[str, Any]],
        available_functions: Dict[str, Callable],
        messages: List[Dict[str, str]],
        original_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute tool calls and continue the conversation."""
        # Add assistant message with tool calls
        if 'choices' in response and response['choices']:
            choice = response['choices'][0]
            if 'message' in choice:
                messages.append(choice['message'])
        
        # Execute each tool call
        for tool_call in tool_calls:
            try:
                function_name = tool_call['function']['name']
                function_args = tool_call['function']['arguments']
                
                result = self.execute_function_call(
                    function_name,
                    function_args,
                    available_functions
                )
                
                # Add tool result to conversation
                messages.append({
                    'role': 'tool',
                    'tool_call_id': tool_call['id'],
                    'content': json.dumps(result)
                })
                
            except Exception as e:
                self.logger.error(f"Tool execution failed: {e}")
                messages.append({
                    'role': 'tool',
                    'tool_call_id': tool_call['id'],
                    'content': json.dumps({'error': str(e)})
                })
        
        # Continue conversation with tool results
        original_request['messages'] = messages
        continued_response = self._make_api_call(
            api_method=self.client.chat.completions.create,
            request_data=original_request,
            estimated_tokens=self._estimate_function_tokens(messages, [])
        )
        
        return continued_response

    def _extract_tool_calls(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract tool calls from response."""
        tool_calls = []
        
        if 'choices' in response and response['choices']:
            choice = response['choices'][0]
            if 'message' in choice and 'tool_calls' in choice['message']:
                for tool_call in choice['message']['tool_calls']:
                    if tool_call.get('type') == 'function':
                        tool_calls.append(tool_call)
        
        return tool_calls

    def _model_supports_functions(self, model: str) -> bool:
        """Check if model supports function calling."""
        function_models = [
            'gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-4', 
            'gpt-3.5-turbo', 'gpt-3.5-turbo-16k'
        ]
        return model in function_models

    def _estimate_function_tokens(
        self,
        messages: List[Dict[str, str]],
        functions: List[Dict[str, Any]]
    ) -> int:
        """Estimate tokens for function calling request."""
        # Base message tokens
        message_tokens = sum(self.estimate_tokens(msg.get('content', '')) for msg in messages)
        
        # Function definition tokens (rough estimate)
        function_tokens = 0
        for func in functions:
            func_str = json.dumps(func)
            function_tokens += self.estimate_tokens(func_str)
        
        # Add overhead for function calling format
        overhead = 20 + (5 * len(functions))
        
        return message_tokens + function_tokens + overhead

    def _estimate_tool_tokens(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]]
    ) -> int:
        """Estimate tokens for tool calling request."""
        # Similar to function tokens but with tool format overhead
        return self._estimate_function_tokens(messages, tools) + 10

    def get_function_calling_capabilities(self) -> Dict[str, Any]:
        """Get information about function calling capabilities."""
        return {
            'supported_models': [
                'gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-4',
                'gpt-3.5-turbo', 'gpt-3.5-turbo-16k'
            ],
            'formats': ['functions', 'tools'],
            'max_functions_per_request': 100,  # OpenAI limit
            'features': [
                'function_calling',
                'tool_calling',
                'auto_execution',
                'multi_step_calling',
                'parallel_function_calls'
            ],
            'parameter_types': [
                'string', 'number', 'integer', 'boolean',
                'object', 'array', 'null'
            ]
        }