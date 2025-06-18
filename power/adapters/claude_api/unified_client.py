"""
Claude API unified client module.
Comprehensive client for Claude Sonnet 4/Opus 4 with hybrid reasoning capabilities.
"""

import asyncio
import json
import time
from typing import Optional, Dict, Any, List, Union, AsyncGenerator, Callable
from dataclasses import asdict

import aiohttp

from .base_client import ClaudeBaseClient
from .config import ClaudeConfig
from .exceptions import (
    ClaudeAPIError, ClaudeRateLimitError, ClaudeConnectionError,
    ClaudeTimeoutError, ClaudeHybridReasoningError, ClaudeToolUseError,
    ClaudeContentFilterError, handle_claude_api_error
)
from shared.models.llm_request import LLMRequest
from shared.models.llm_response import LLMResponse


class ClaudeUnifiedClient(ClaudeBaseClient):
    """Unified client for all Claude API operations with hybrid reasoning support."""

    def __init__(self, config: Optional[ClaudeConfig] = None):
        self.config = config or ClaudeConfig()
        super().__init__(self.config)
        
        self.base_url = self.config.base_url or "https://api.anthropic.com"
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if not self._session or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers=self._prepare_request_headers()
            )
        return self._session

    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        stream: bool = False,
        **kwargs
    ) -> Union[Dict[str, Any], AsyncGenerator[Dict[str, Any], None]]:
        """Make HTTP request to Claude API."""
        await self._handle_rate_limiting()
        
        session = await self._get_session()
        url = f"{self.base_url}{endpoint}"
        
        try:
            if stream:
                return self._stream_request(session, method, url, data, **kwargs)
            else:
                async with session.request(method, url, json=data, **kwargs) as response:
                    return await self._handle_response(response)
                    
        except asyncio.TimeoutError as e:
            raise ClaudeTimeoutError(f"Request timed out after {self.config.timeout}s") from e
        except aiohttp.ClientConnectionError as e:
            raise ClaudeConnectionError(f"Connection failed: {str(e)}") from e
        except Exception as e:
            raise handle_claude_api_error(e, "API request failed")

    async def _stream_request(
        self,
        session: aiohttp.ClientSession,
        method: str,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream response from Claude API."""
        async with session.request(method, url, json=data, **kwargs) as response:
            if response.status != 200:
                error_data = await response.json() if response.content_type == 'application/json' else {}
                raise self._create_error_from_response(response.status, error_data)

            async for line in response.content:
                if line:
                    try:
                        # Parse SSE format
                        line_str = line.decode('utf-8').strip()
                        if line_str.startswith('data: '):
                            json_str = line_str[6:]  # Remove 'data: ' prefix
                            if json_str == '[DONE]':
                                break
                            yield json.loads(json_str)
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        continue

    async def _handle_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """Handle API response and errors."""
        try:
            response_data = await response.json()
        except json.JSONDecodeError:
            response_data = {'error': 'Invalid JSON response'}

        if response.status == 200:
            return response_data
        else:
            raise self._create_error_from_response(response.status, response_data)

    def _create_error_from_response(self, status_code: int, response_data: Dict[str, Any]) -> ClaudeAPIError:
        """Create appropriate error from API response."""
        error_message = response_data.get('error', {}).get('message', 'Unknown error')
        error_type = response_data.get('error', {}).get('type', 'unknown')

        if status_code == 401:
            return ClaudeAPIError(error_message, status_code, "authentication_error", response_data)
        elif status_code == 429:
            retry_after = response_data.get('error', {}).get('retry_after')
            return ClaudeRateLimitError(error_message, retry_after)
        elif status_code == 400 and 'context_length' in error_message.lower():
            return ClaudeAPIError(error_message, status_code, "context_limit_error", response_data)
        elif status_code == 400 and 'content_filter' in error_message.lower():
            return ClaudeContentFilterError(error_message)
        else:
            return ClaudeAPIError(error_message, status_code, error_type, response_data)

    async def complete_text(
        self,
        request: LLMRequest,
        model: Optional[str] = None,
        reasoning_mode: Optional[str] = None,
        reasoning_depth: Optional[int] = None,
        enable_streaming: Optional[bool] = None
    ) -> Union[LLMResponse, AsyncGenerator[LLMResponse, None]]:
        """Complete text using Claude with hybrid reasoning."""
        model = model or self.config.default_model
        enable_streaming = enable_streaming or self.config.enable_streaming

        # Validate model compatibility
        required_features = []
        if request.images:
            required_features.append('vision')
        if request.tools:
            required_features.append('functions')
        
        self._validate_model_compatibility(model, required_features)

        # Prepare request data
        request_data = await self._prepare_completion_request(
            request, model, reasoning_mode, reasoning_depth
        )

        # Check cache first
        cache_key = self._get_cache_key(request_data) if not enable_streaming else None
        if cache_key:
            cached_response = await self._get_cached_response(cache_key)
            if cached_response:
                return LLMResponse(**cached_response)

        try:
            if enable_streaming:
                return self._stream_completion(request_data)
            else:
                response_data = await self._retry_request(
                    self._make_request,
                    'POST',
                    '/v1/messages',
                    request_data
                )
                
                llm_response = await self._process_completion_response(response_data, request)
                
                # Cache response if caching is enabled
                if cache_key:
                    await self._cache_response(cache_key, asdict(llm_response))
                
                return llm_response

        except Exception as e:
            raise handle_claude_api_error(e, "Text completion failed")

    async def _prepare_completion_request(
        self,
        request: LLMRequest,
        model: str,
        reasoning_mode: Optional[str] = None,
        reasoning_depth: Optional[int] = None
    ) -> Dict[str, Any]:
        """Prepare request data for text completion."""
        request_data = {
            'model': model,
            'messages': self._format_messages(request.messages),
            'max_tokens': min(request.max_tokens or self.config.default_max_tokens, 65536),
            'temperature': request.temperature or self.config.default_temperature,
            'top_p': request.top_p or self.config.default_top_p,
            'top_k': request.top_k or self.config.default_top_k,
            'stream': False  # Will be set by streaming method
        }

        # Add system message if provided
        if request.system_message:
            request_data['system'] = request.system_message

        # Add hybrid reasoning parameters
        if self.config.enable_hybrid_reasoning:
            reasoning_params = self._prepare_hybrid_reasoning_params(
                reasoning_mode, reasoning_depth
            )
            request_data.update(reasoning_params)

        # Add context management parameters
        context_params = self._prepare_context_management_params(
            len(str(request.messages))  # Rough token estimate
        )
        request_data.update(context_params)

        # Add tools if provided
        if request.tools:
            request_data['tools'] = self._format_tools(request.tools)
            if request.tool_choice:
                request_data['tool_choice'] = request.tool_choice

        # Add stop sequences
        if request.stop_sequences:
            request_data['stop_sequences'] = request.stop_sequences

        return request_data

    def _format_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format messages for Claude API."""
        formatted_messages = []
        
        for message in messages:
            formatted_message = {
                'role': message['role'],
                'content': []
            }

            # Handle text content
            if isinstance(message['content'], str):
                formatted_message['content'].append({
                    'type': 'text',
                    'text': message['content']
                })
            elif isinstance(message['content'], list):
                # Handle multimodal content
                for content_item in message['content']:
                    if content_item['type'] == 'text':
                        formatted_message['content'].append(content_item)
                    elif content_item['type'] == 'image':
                        formatted_message['content'].append({
                            'type': 'image',
                            'source': content_item['source']
                        })
                    elif content_item['type'] == 'tool_use':
                        formatted_message['content'].append(content_item)
                    elif content_item['type'] == 'tool_result':
                        formatted_message['content'].append(content_item)

            formatted_messages.append(formatted_message)

        return formatted_messages

    def _format_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format tools for Claude API."""
        formatted_tools = []
        
        for tool in tools:
            formatted_tool = {
                'name': tool['name'],
                'description': tool['description'],
                'input_schema': tool.get('parameters', {})
            }
            formatted_tools.append(formatted_tool)

        return formatted_tools

    async def _stream_completion(
        self, request_data: Dict[str, Any]
    ) -> AsyncGenerator[LLMResponse, None]:
        """Stream completion responses."""
        request_data['stream'] = True
        
        accumulated_content = ""
        accumulated_tool_calls = []
        
        try:
            async for chunk in await self._make_request(
                'POST', '/v1/messages', request_data, stream=True
            ):
                if chunk.get('type') == 'content_block_delta':
                    delta = chunk.get('delta', {})
                    if delta.get('type') == 'text_delta':
                        text_delta = delta.get('text', '')
                        accumulated_content += text_delta
                        
                        yield LLMResponse(
                            content=accumulated_content,
                            model=request_data['model'],
                            usage={
                                'input_tokens': chunk.get('usage', {}).get('input_tokens', 0),
                                'output_tokens': chunk.get('usage', {}).get('output_tokens', 0)
                            },
                            metadata={
                                'stream_chunk': True,
                                'chunk_type': 'text_delta'
                            }
                        )
                
                elif chunk.get('type') == 'content_block_start':
                    block = chunk.get('content_block', {})
                    if block.get('type') == 'tool_use':
                        accumulated_tool_calls.append(block)
                        
                elif chunk.get('type') == 'message_stop':
                    # Final response
                    yield LLMResponse(
                        content=accumulated_content,
                        model=request_data['model'],
                        tool_calls=accumulated_tool_calls,
                        usage=chunk.get('usage', {}),
                        metadata={
                            'stream_chunk': False,
                            'final_response': True
                        }
                    )
                    
        except Exception as e:
            raise handle_claude_api_error(e, "Streaming completion failed")

    async def _process_completion_response(
        self, response_data: Dict[str, Any], original_request: LLMRequest
    ) -> LLMResponse:
        """Process completion response from Claude API."""
        content = ""
        tool_calls = []
        
        # Extract content from response
        for content_block in response_data.get('content', []):
            if content_block['type'] == 'text':
                content += content_block['text']
            elif content_block['type'] == 'tool_use':
                tool_calls.append({
                    'id': content_block['id'],
                    'name': content_block['name'],
                    'arguments': content_block['input']
                })

        # Extract usage information
        usage = response_data.get('usage', {})
        
        # Calculate costs if model config available
        model_config = self.config.get_model_config(response_data.get('model', ''))
        cost_info = {}
        if model_config and usage:
            input_cost = (usage.get('input_tokens', 0) / 1000) * model_config.get('cost_per_1k_input_tokens', 0)
            output_cost = (usage.get('output_tokens', 0) / 1000) * model_config.get('cost_per_1k_output_tokens', 0)
            cost_info = {
                'input_cost': input_cost,
                'output_cost': output_cost,
                'total_cost': input_cost + output_cost
            }

        return LLMResponse(
            content=content,
            model=response_data.get('model', ''),
            tool_calls=tool_calls,
            usage=usage,
            metadata={
                'response_id': response_data.get('id'),
                'stop_reason': response_data.get('stop_reason'),
                'cost_info': cost_info,
                'model_config': model_config,
                'hybrid_reasoning_used': self.config.enable_hybrid_reasoning
            }
        )

    async def analyze_image(
        self,
        image_data: Union[str, bytes],
        prompt: str,
        model: Optional[str] = None,
        detail_level: str = "auto"
    ) -> LLMResponse:
        """Analyze image using Claude's vision capabilities."""
        model = model or self.config.default_model
        self._validate_model_compatibility(model, ['vision'])

        # Create request with image
        request = LLMRequest(
            messages=[{
                'role': 'user',
                'content': [
                    {
                        'type': 'text',
                        'text': prompt
                    },
                    {
                        'type': 'image',
                        'source': {
                            'type': 'base64' if isinstance(image_data, str) else 'bytes',
                            'media_type': 'image/jpeg',  # Auto-detect in real implementation
                            'data': image_data
                        }
                    }
                ]
            }]
        )

        return await self.complete_text(request, model=model)

    async def use_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        model: Optional[str] = None,
        tool_choice: Optional[str] = None
    ) -> LLMResponse:
        """Use tools with Claude API."""
        model = model or self.config.default_model
        self._validate_model_compatibility(model, ['functions'])

        request = LLMRequest(
            messages=messages,
            tools=tools,
            tool_choice=tool_choice
        )

        return await self.complete_text(request, model=model)

    async def get_embeddings(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get embeddings (if supported by Claude API in the future)."""
        raise ClaudeAPIError("Embeddings not yet supported by Claude API")

    async def close(self) -> None:
        """Clean up resources."""
        await super().close()
        if self._session and not self._session.closed:
            await self._session.close()