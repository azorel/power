"""
Function calling capabilities for Gemini API client.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Callable

from shared.models.llm_request import LLMRequest
from shared.models.llm_response import LLMResponse

from .base_client import GeminiBaseClient
from .exceptions import wrap_gemini_call

logger = logging.getLogger(__name__)


class GeminiFunctionClient(GeminiBaseClient):
    """
    Gemini client for function calling operations.
    """

    @wrap_gemini_call
    def generate_with_functions(
        self,
        request: LLMRequest,
        functions: List[Dict[str, Any]],
        function_choice: str = "auto"
    ) -> LLMResponse:
        """
        Generate response with function calling capability.

        Args:
            request: LLM request containing prompt and parameters
            functions: List of available functions
            function_choice: How to choose functions ("auto", "none", or specific name)

        Returns:
            LLLResponse with potential function calls
        """
        # Rate limiting
        self.rate_limiter.wait_if_needed()

        try:
            client = self._get_genai_client()

            # Map request to Gemini format
            gemini_request = self.data_mapper.map_llm_request(request)

            # Convert functions to Google format
            google_functions = self._convert_functions_to_google_format(functions)

            # Add function calling configuration
            if 'config' not in gemini_request:
                gemini_request['config'] = {}

            gemini_request['config']['tools'] = [
                {'function_declarations': google_functions}
            ]

            # Set function calling mode
            if function_choice != "auto":
                gemini_request['config']['tool_config'] = {
                    'function_calling_config': {
                        'mode': 'NONE' if function_choice == "none" else 'ANY',
                        'allowed_function_names': (
                            [function_choice] if function_choice not in ["auto", "none"]
                            else None
                        )
                    }
                }

            # Make API call
            response = client.models.generate_content(
                model=self.config.model,
                contents=gemini_request.get('contents', []),
                config=gemini_request.get('config', {})
            )

            # Convert response
            llm_response = self.data_mapper.map_gemini_response(
                response,
                request_id=request.request_id,
                model=self.config.model
            )

            # Update statistics
            self._stats['requests_made'] += 1
            if hasattr(llm_response, 'usage'):
                self._stats['total_tokens'] += llm_response.usage.get('total_tokens', 0)

            return llm_response

        except Exception as e:
            self._stats['errors'] += 1
            logger.error(
                "Function calling failed for request %s: %s",
                request.request_id, str(e)
            )
            raise

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
            function_args: Arguments for the function
            available_functions: Dictionary of available functions

        Returns:
            Result of the function execution
        """
        if function_name not in available_functions:
            raise ValueError(f"Function '{function_name}' not available")

        try:
            function = available_functions[function_name]
            result = function(**function_args)

            logger.info(
                "Successfully executed function '%s' with args: %s",
                function_name, function_args
            )

            return result

        except Exception as e:
            logger.error(
                "Function execution failed for '%s': %s",
                function_name, str(e)
            )
            raise

    def _convert_functions_to_google_format(
        self,
        functions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Convert function definitions to Google's expected format.

        Args:
            functions: List of function definitions

        Returns:
            List of functions in Google format
        """
        google_functions = []

        for func in functions:
            google_func = {
                'name': func['name'],
                'description': func.get('description', ''),
                'parameters': {
                    'type': 'object',
                    'properties': {},
                    'required': []
                }
            }

            # Process parameters
            if 'parameters' in func:
                parameters = func['parameters']

                # Handle OpenAI-style parameters
                if 'properties' in parameters:
                    google_func['parameters']['properties'] = parameters['properties']
                    google_func['parameters']['required'] = parameters.get('required', [])
                else:
                    # Handle other parameter formats
                    for param_name, param_info in parameters.items():
                        if isinstance(param_info, dict):
                            google_func['parameters']['properties'][param_name] = param_info
                            if param_info.get('required', False):
                                google_func['parameters']['required'].append(param_name)

            google_functions.append(google_func)

        return google_functions

    def generate_with_function_response(
        self,
        original_request: LLMRequest,
        function_name: str,
        function_result: Any,
        functions: List[Dict[str, Any]]
    ) -> LLMResponse:
        """
        Generate follow-up response after function execution.

        Args:
            original_request: Original request that triggered function call
            function_name: Name of the executed function
            function_result: Result from function execution
            functions: Available functions list

        Returns:
            LLMResponse with final answer incorporating function result
        """
        try:
            # Create a new request with function result
            function_response_text = (
                f"Function '{function_name}' returned: {json.dumps(function_result)}"
            )

            # Append function result to original prompt
            updated_prompt = (
                f"{original_request.prompt}\n\n"
                f"[Function Result] {function_response_text}\n\n"
                f"Please provide a final response based on this function result."
            )

            updated_request = LLMRequest(
                prompt=updated_prompt,
                parameters=original_request.provider_params,
                request_id=original_request.request_id
            )

            # Generate response without function calling
            return self.generate_with_functions(
                updated_request,
                functions=functions,
                function_choice="none"  # Disable further function calls
            )

        except Exception as e:
            logger.error("Function response generation failed: %s", str(e))
            raise

    def validate_function_schema(self, functions: List[Dict[str, Any]]) -> bool:
        """
        Validate function schemas for Gemini compatibility.

        Args:
            functions: List of function definitions

        Returns:
            True if all functions are valid
        """
        required_fields = ['name', 'description']

        for func in functions:
            # Check required fields
            for field in required_fields:
                if field not in func:
                    logger.error("Function missing required field '%s': %s", field, func)
                    return False

            # Validate parameters if present
            if 'parameters' in func:
                params = func['parameters']
                if not isinstance(params, dict):
                    logger.error("Function parameters must be a dictionary: %s", func)
                    return False

        return True
