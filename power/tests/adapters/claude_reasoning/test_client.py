"""
Test Claude Reasoning Client

Comprehensive tests for Claude reasoning adapter implementation.
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from adapters.claude_reasoning import ClaudeReasoningClient, ClaudeReasoningConfig
from shared.models.reasoning_models import (
    ReasoningRequest,
    ReasoningResponse,
    ReasoningMode,
    ReasoningStep,
    ThinkingChain
)
from shared.interfaces.reasoning_provider import (
    ReasoningProviderError,
    RateLimitError,
    AuthenticationError
)


class TestClaudeReasoningClient:
    """Test cases for Claude reasoning client."""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        config = MagicMock(spec=ClaudeReasoningConfig)
        config.api_key = "test-api-key"
        config.base_url = "https://api.anthropic.com"
        config.model = "claude-3-sonnet-20240229"
        config.rapid_model = "claude-3-haiku-20240307"
        config.thoughtful_model = "claude-3-opus-20240229"
        config.max_tokens = 4096
        config.temperature = 0.7
        config.timeout = 30.0
        config.rate_limit = 50
        config.daily_quota = 10000
        config.cache_enabled = True
        config.cache_ttl = 3600
        
        # Mock methods
        config.get_model_for_mode.return_value = "claude-3-sonnet-20240229"
        config.get_temperature_for_mode.return_value = 0.7
        config.get_max_tokens_for_mode.return_value = 4096
        config.validate_config.return_value = {'is_valid': True, 'errors': []}
        
        return config
    
    @pytest.fixture
    def claude_client(self, mock_config):
        """Create Claude reasoning client with mock config."""
        with patch('adapters.claude_reasoning.client.ClaudeReasoningConfig') as mock_config_class:
            mock_config_class.return_value = mock_config
            client = ClaudeReasoningClient(mock_config)
            return client
    
    @pytest.fixture
    def mock_claude_response(self):
        """Mock Claude API response."""
        return {
            'content': [{'text': 'This is a test response from Claude.'}],
            'usage': {'output_tokens': 50},
            'model': 'claude-3-sonnet-20240229'
        }
    
    @pytest.mark.asyncio
    async def test_rapid_response(self, claude_client, mock_claude_response):
        """Test rapid response functionality."""
        with patch.object(claude_client, '_make_api_call', return_value=mock_claude_response):
            response = await claude_client.rapid_response("What is 2+2?")
            
            assert isinstance(response, str)
            assert len(response) > 0
    
    @pytest.mark.asyncio
    async def test_thoughtful_response(self, claude_client, mock_claude_response):
        """Test thoughtful response functionality."""
        mock_claude_response['content'][0]['text'] = """
        Step 1: Analysis
        Let me analyze this complex problem.
        
        Step 2: Evaluation
        Based on the analysis, I can conclude...
        
        Final Answer: This is my thoughtful conclusion.
        """
        
        with patch.object(claude_client, '_make_api_call', return_value=mock_claude_response):
            thinking_chain = await claude_client.thoughtful_response("Explain quantum computing")
            
            assert isinstance(thinking_chain, ThinkingChain)
            assert len(thinking_chain.steps) > 0
            assert thinking_chain.final_answer is not None
    
    @pytest.mark.asyncio
    async def test_reason_rapid_mode(self, claude_client, mock_claude_response):
        """Test reasoning in rapid mode."""
        request = ReasoningRequest(
            prompt="Simple question",
            mode=ReasoningMode.RAPID
        )
        
        with patch.object(claude_client, '_make_api_call', return_value=mock_claude_response):
            response = await claude_client.reason(request)
            
            assert response.success
            assert response.mode_used == ReasoningMode.RAPID
            assert response.rapid_answer is not None
            assert response.complexity_score == 0.2
    
    @pytest.mark.asyncio
    async def test_reason_thoughtful_mode(self, claude_client, mock_claude_response):
        """Test reasoning in thoughtful mode."""
        request = ReasoningRequest(
            prompt="Complex analysis needed",
            mode=ReasoningMode.THOUGHTFUL
        )
        
        with patch.object(claude_client, '_make_api_call', return_value=mock_claude_response):
            response = await claude_client.reason(request)
            
            assert response.success
            assert response.mode_used == ReasoningMode.THOUGHTFUL
            assert response.thinking_chain is not None
    
    @pytest.mark.asyncio
    async def test_step_by_step_thinking(self, claude_client, mock_claude_response):
        """Test step-by-step thinking."""
        request = ReasoningRequest(
            prompt="Think step by step",
            mode=ReasoningMode.STEP_BY_STEP,
            max_steps=3
        )
        
        mock_claude_response['content'][0]['text'] = """
        Step 1: First step analysis
        Step 2: Second step evaluation  
        Step 3: Final conclusion
        """
        
        with patch.object(claude_client, '_make_api_call', return_value=mock_claude_response):
            steps = []
            async for step in claude_client.think_step_by_step(request):
                steps.append(step)
            
            assert len(steps) > 0
            assert all(isinstance(step, ReasoningStep) for step in steps)
    
    @pytest.mark.asyncio
    async def test_complexity_analysis(self, claude_client):
        """Test complexity analysis functionality."""
        mock_analysis_response = {
            'content': [{'text': '''
            {
                "complexity_score": 0.7,
                "recommended_mode": "thoughtful",
                "reasoning_time_estimate": 15.0,
                "reasoning_factors": ["technical_content", "multiple_steps"],
                "confidence": 0.8
            }
            '''}],
            'usage': {'output_tokens': 30}
        }
        
        with patch.object(claude_client, '_make_api_call', return_value=mock_analysis_response):
            analysis = await claude_client.analyze_complexity("Complex technical question")
            
            assert 'complexity_score' in analysis
            assert 'recommended_mode' in analysis
            assert 0.0 <= analysis['complexity_score'] <= 1.0
            assert analysis['recommended_mode'] in ['rapid', 'thoughtful', 'chain_of_thought', 'step_by_step']
    
    @pytest.mark.asyncio
    async def test_complexity_analysis_fallback(self, claude_client):
        """Test complexity analysis fallback when JSON parsing fails."""
        mock_analysis_response = {
            'content': [{'text': 'Non-JSON response that will trigger fallback'}],
            'usage': {'output_tokens': 20}
        }
        
        with patch.object(claude_client, '_make_api_call', return_value=mock_analysis_response):
            analysis = await claude_client.analyze_complexity("Test prompt")
            
            assert 'complexity_score' in analysis
            assert 'recommended_mode' in analysis
            # Should use fallback heuristics
            assert 0.0 <= analysis['complexity_score'] <= 1.0
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, claude_client):
        """Test rate limiting functionality."""
        # Mock rate limiter to deny requests
        claude_client.rate_limiter.can_make_call = MagicMock(return_value=False)
        
        request = ReasoningRequest(
            prompt="This should be rate limited",
            mode=ReasoningMode.RAPID
        )
        
        with pytest.raises(RateLimitError):
            await claude_client.reason(request)
    
    @pytest.mark.asyncio
    async def test_authentication_error(self, claude_client):
        """Test authentication error handling."""
        with patch.object(claude_client, '_make_api_call', side_effect=AuthenticationError("Invalid API key")):
            request = ReasoningRequest(
                prompt="Test auth error",
                mode=ReasoningMode.RAPID
            )
            
            response = await claude_client.reason(request)
            
            assert not response.success
            assert "Invalid API key" in response.error_message
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self, claude_client):
        """Test general API error handling."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_response.text = AsyncMock(return_value="Internal server error")
            mock_post.return_value.__aenter__.return_value = mock_response
            
            request = ReasoningRequest(
                prompt="This will cause API error",
                mode=ReasoningMode.RAPID
            )
            
            response = await claude_client.reason(request)
            
            assert not response.success
            assert "500" in response.error_message
    
    @pytest.mark.asyncio
    async def test_caching_functionality(self, claude_client, mock_claude_response):
        """Test response caching."""
        # Enable caching
        claude_client.cache = MagicMock()
        claude_client.cache.get.return_value = None  # No cached response
        
        request = ReasoningRequest(
            prompt="Test caching",
            mode=ReasoningMode.RAPID
        )
        
        with patch.object(claude_client, '_make_api_call', return_value=mock_claude_response):
            response = await claude_client.reason(request)
            
            assert response.success
            # Should have attempted to get from cache
            claude_client.cache.get.assert_called_once()
            # Should have cached the response
            claude_client.cache.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cached_response_retrieval(self, claude_client):
        """Test retrieval of cached responses."""
        # Mock cached response
        cached_response = ReasoningResponse(
            rapid_answer="Cached answer",
            mode_used=ReasoningMode.RAPID,
            success=True,
            provider="claude"
        )
        
        claude_client.cache = MagicMock()
        claude_client.cache.get.return_value = cached_response
        
        request = ReasoningRequest(
            prompt="Test cached",
            mode=ReasoningMode.RAPID
        )
        
        response = await claude_client.reason(request)
        
        assert response == cached_response
        assert response.rapid_answer == "Cached answer"
    
    def test_supported_modes(self, claude_client):
        """Test getting supported reasoning modes."""
        modes = claude_client.get_supported_modes()
        
        assert ReasoningMode.RAPID in modes
        assert ReasoningMode.THOUGHTFUL in modes
        assert ReasoningMode.CHAIN_OF_THOUGHT in modes
        assert ReasoningMode.STEP_BY_STEP in modes
        assert ReasoningMode.ADAPTIVE in modes
    
    def test_provider_info(self, claude_client):
        """Test getting provider information."""
        info = claude_client.get_provider_info()
        
        assert info['name'] == 'claude'
        assert 'version' in info
        assert 'capabilities' in info
        assert 'limitations' in info
        assert 'supported_modes' in info
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, claude_client, mock_claude_response):
        """Test successful health check."""
        mock_claude_response['content'][0]['text'] = "4"
        
        with patch.object(claude_client, '_make_api_call', return_value=mock_claude_response):
            is_healthy = await claude_client.health_check()
            
            assert is_healthy
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, claude_client):
        """Test health check failure."""
        with patch.object(claude_client, '_make_api_call', side_effect=Exception("Connection error")):
            is_healthy = await claude_client.health_check()
            
            assert not is_healthy
    
    def test_cache_key_generation(self, claude_client):
        """Test cache key generation."""
        request1 = ReasoningRequest(
            prompt="Test prompt",
            mode=ReasoningMode.RAPID,
            temperature=0.7
        )
        
        request2 = ReasoningRequest(
            prompt="Test prompt",
            mode=ReasoningMode.RAPID,
            temperature=0.7
        )
        
        request3 = ReasoningRequest(
            prompt="Different prompt",
            mode=ReasoningMode.RAPID,
            temperature=0.7
        )
        
        key1 = claude_client._generate_cache_key(request1)
        key2 = claude_client._generate_cache_key(request2)
        key3 = claude_client._generate_cache_key(request3)
        
        # Same requests should have same cache key
        assert key1 == key2
        # Different requests should have different cache keys
        assert key1 != key3
    
    @pytest.mark.asyncio
    async def test_request_timeout(self, claude_client):
        """Test request timeout handling."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.side_effect = asyncio.TimeoutError("Request timeout")
            
            request = ReasoningRequest(
                prompt="This will timeout",
                mode=ReasoningMode.RAPID,
                timeout=1.0
            )
            
            response = await claude_client.reason(request)
            
            assert not response.success
            assert "timeout" in response.error_message.lower()
    
    def test_config_validation(self, mock_config):
        """Test configuration validation."""
        # Test valid config
        mock_config.validate_config.return_value = {'is_valid': True, 'errors': []}
        
        with patch('adapters.claude_reasoning.client.ClaudeReasoningConfig') as mock_config_class:
            mock_config_class.return_value = mock_config
            client = ClaudeReasoningClient(mock_config)
            assert client is not None
        
        # Test invalid config
        mock_config.validate_config.return_value = {'is_valid': False, 'errors': ['Invalid API key']}
        
        with patch('adapters.claude_reasoning.client.ClaudeReasoningConfig') as mock_config_class:
            mock_config_class.return_value = mock_config
            with pytest.raises(ValueError):
                ClaudeReasoningClient(mock_config)