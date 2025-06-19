"""
Claude Reasoning Client

Main client implementation for Claude reasoning provider following
API integration standards and the ReasoningProvider interface.
"""

import asyncio
import logging
import time
import json
from typing import Dict, Any, List, Optional, AsyncIterator
import aiohttp

from shared.interfaces.reasoning_provider import (
    ReasoningProvider,
    ReasoningProviderError,
    RateLimitError,
    AuthenticationError,
    ComplexityAnalysisError,
    ReasoningModeError
)
from shared.models.reasoning_models import (
    ReasoningRequest,
    ReasoningResponse,
    ReasoningStep,
    ReasoningMode,
    ThinkingChain,
    StepType,
    ConfidenceLevel,
    ComplexityAnalysis
)
from shared.utils.rate_limiter import BaseRateLimiter
from shared.utils.cache import ResponseCache

from .config import ClaudeReasoningConfig
from .data_mapper import ClaudeReasoningDataMapper


class ClaudeRateLimiter(BaseRateLimiter):
    """Rate limiter for Claude API calls."""
    
    def __init__(self, config: ClaudeReasoningConfig):
        super().__init__(
            calls_per_minute=config.rate_limit,
            quota_per_day=config.daily_quota
        )


class ClaudeReasoningClient(ReasoningProvider):
    """
    Claude reasoning client implementing the ReasoningProvider interface.
    
    Provides hybrid reasoning capabilities using Claude's language models
    with support for rapid responses, thoughtful analysis, and step-by-step reasoning.
    """
    
    def __init__(self, config: Optional[ClaudeReasoningConfig] = None):
        """
        Initialize the Claude reasoning client.
        
        Args:
            config: Optional configuration, will create default if not provided
        """
        self.config = config or ClaudeReasoningConfig()
        self.data_mapper = ClaudeReasoningDataMapper()
        self.rate_limiter = ClaudeRateLimiter(self.config)
        self.logger = logging.getLogger(__name__)
        
        # Initialize cache if enabled
        if self.config.cache_enabled:
            self.cache = ResponseCache(
                ttl_seconds=self.config.cache_ttl,
                max_size=1000
            )
        else:
            self.cache = None
        
        # Validate configuration
        validation = self.config.validate_config()
        if not validation['is_valid']:
            raise ValueError(f"Invalid configuration: {validation['errors']}")
        
        self.logger.info("Claude reasoning client initialized")
    
    async def reason(self, request: ReasoningRequest) -> ReasoningResponse:
        """
        Process a reasoning request using Claude.
        
        Args:
            request: The reasoning request to process
            
        Returns:
            ReasoningResponse: The reasoning response
        """
        start_time = time.time()
        
        try:
            # Check rate limits
            if not self.rate_limiter.can_make_call():
                raise RateLimitError("Claude API rate limit exceeded")
            
            # Check cache if enabled
            if self.cache:
                cache_key = self._generate_cache_key(request)
                if cached_response := self.cache.get(cache_key):
                    self.logger.debug("Returning cached response")
                    return cached_response
            
            # Map request to Claude format
            api_config = {
                'model': self.config.get_model_for_mode(request.mode.value),
                'max_tokens': self.config.get_max_tokens_for_mode(request.mode.value),
                'temperature': self.config.get_temperature_for_mode(request.mode.value)
            }
            
            claude_request = self.data_mapper.map_request_to_claude(request, api_config)
            
            # Make API call
            claude_response = await self._make_api_call(claude_request)
            
            # Map response back to shared format
            response = self.data_mapper.map_response_from_claude(claude_response, request)
            response.processing_time = time.time() - start_time
            
            # Cache response if enabled
            if self.cache and response.success:
                self.cache.set(cache_key, response)
            
            # Record rate limiter usage
            self.rate_limiter.record_call()
            
            self.logger.info(
                f"Claude reasoning completed in {response.processing_time:.2f}s "
                f"using {request.mode.value} mode"
            )
            
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"Claude reasoning failed: {e}")
            
            return ReasoningResponse(
                request_id=request.id,
                success=False,
                error_message=str(e),
                processing_time=processing_time,
                provider="claude"
            )
    
    async def think_step_by_step(self, request: ReasoningRequest) -> AsyncIterator[ReasoningStep]:
        """
        Process request with step-by-step thinking, yielding each step.
        
        Args:
            request: The reasoning request
            
        Yields:
            ReasoningStep: Each step in the reasoning process
        """
        # For Claude, we need to simulate streaming steps since the API doesn't
        # natively support step-by-step streaming. We'll make a request and
        # parse the response into steps.
        
        try:
            # Create a modified request for step-by-step processing
            step_request = ReasoningRequest(
                prompt=request.prompt,
                mode=ReasoningMode.STEP_BY_STEP,
                max_steps=request.max_steps,
                timeout=request.timeout,
                temperature=request.temperature,
                context=request.context
            )
            
            # Get the full response
            response = await self.reason(step_request)
            
            if response.success and response.thinking_chain:
                # Yield each step with a small delay to simulate streaming
                for step in response.thinking_chain.steps:
                    yield step
                    await asyncio.sleep(0.1)  # Small delay for streaming effect
            else:
                # If no thinking chain, create a single step
                step = ReasoningStep(
                    step_number=1,
                    step_type=StepType.ANALYSIS,
                    description="Analysis",
                    content=response.get_final_answer(),
                    confidence=ConfidenceLevel.MEDIUM
                )
                yield step
                
        except Exception as e:
            self.logger.error(f"Step-by-step thinking failed: {e}")
            # Yield an error step
            error_step = ReasoningStep(
                step_number=1,
                step_type=StepType.ANALYSIS,
                description="Error",
                content=f"Step-by-step processing failed: {e}",
                confidence=ConfidenceLevel.LOW
            )
            yield error_step
    
    async def rapid_response(self, prompt: str) -> str:
        """
        Generate a rapid response with minimal processing.
        
        Args:
            prompt: The input prompt
            
        Returns:
            str: Quick response
        """
        request = ReasoningRequest(
            prompt=prompt,
            mode=ReasoningMode.RAPID,
            max_steps=1,
            timeout=10.0,
            temperature=0.3
        )
        
        response = await self.reason(request)
        return response.get_final_answer()
    
    async def thoughtful_response(self, prompt: str) -> ThinkingChain:
        """
        Generate a thoughtful response with detailed reasoning chain.
        
        Args:
            prompt: The input prompt
            
        Returns:
            ThinkingChain: Detailed reasoning chain
        """
        request = ReasoningRequest(
            prompt=prompt,
            mode=ReasoningMode.THOUGHTFUL,
            max_steps=8,
            timeout=30.0,
            temperature=0.7
        )
        
        response = await self.reason(request)
        
        if response.success and response.thinking_chain:
            return response.thinking_chain
        else:
            # Create a basic thinking chain if none was generated
            chain = ThinkingChain()
            step = ReasoningStep(
                step_number=1,
                step_type=StepType.ANALYSIS,
                description="Thoughtful analysis",
                content=response.get_final_answer(),
                confidence=ConfidenceLevel.MEDIUM
            )
            chain.add_step(step)
            chain.final_answer = response.get_final_answer()
            return chain
    
    def get_supported_modes(self) -> List[ReasoningMode]:
        """Get list of reasoning modes supported by Claude."""
        return [
            ReasoningMode.RAPID,
            ReasoningMode.THOUGHTFUL,
            ReasoningMode.CHAIN_OF_THOUGHT,
            ReasoningMode.STEP_BY_STEP,
            ReasoningMode.ADAPTIVE
        ]
    
    async def analyze_complexity(self, prompt: str) -> Dict[str, Any]:
        """
        Analyze the complexity of a prompt to determine optimal reasoning mode.
        
        Args:
            prompt: The input prompt to analyze
            
        Returns:
            Dict[str, Any]: Complexity analysis results
        """
        try:
            # Use Claude to analyze the complexity
            analysis_prompt = f"""
Analyze the complexity of this question and recommend the best reasoning approach:

Question: {prompt}

Consider:
1. How complex is this question? (0.0 = very simple, 1.0 = very complex)
2. What reasoning mode would be best? (rapid, thoughtful, chain_of_thought, step_by_step)
3. How long might it take to answer well? (in seconds)
4. What factors make this question complex or simple?

Respond in JSON format:
{{
    "complexity_score": 0.0-1.0,
    "recommended_mode": "mode_name",
    "reasoning_time_estimate": seconds,
    "reasoning_factors": ["factor1", "factor2"],
    "confidence": 0.0-1.0
}}
"""
            
            # Make a rapid analysis request
            analysis_request = ReasoningRequest(
                prompt=analysis_prompt,
                mode=ReasoningMode.RAPID,
                max_steps=1,
                timeout=10.0,
                temperature=0.1  # Low temperature for consistent analysis
            )
            
            response = await self.reason(analysis_request)
            
            if response.success:
                try:
                    # Try to parse JSON from response
                    analysis_text = response.get_final_answer()
                    
                    # Extract JSON if it's embedded in text
                    import re
                    json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
                    if json_match:
                        analysis_data = json.loads(json_match.group())
                    else:
                        raise ValueError("No JSON found in response")
                    
                    # Validate and normalize the analysis
                    return self._normalize_complexity_analysis(analysis_data)
                    
                except (json.JSONDecodeError, ValueError) as e:
                    self.logger.warning(f"Failed to parse complexity analysis: {e}")
                    return self._fallback_complexity_analysis(prompt)
            else:
                return self._fallback_complexity_analysis(prompt)
                
        except Exception as e:
            self.logger.error(f"Complexity analysis failed: {e}")
            raise ComplexityAnalysisError(f"Failed to analyze complexity: {e}")
    
    def _normalize_complexity_analysis(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize and validate complexity analysis data."""
        
        # Ensure complexity score is in valid range
        complexity_score = max(0.0, min(1.0, float(analysis_data.get('complexity_score', 0.5))))
        
        # Validate recommended mode
        recommended_mode = analysis_data.get('recommended_mode', 'thoughtful')
        if recommended_mode not in [mode.value for mode in ReasoningMode]:
            recommended_mode = 'thoughtful'
        
        # Ensure reasonable time estimate
        time_estimate = max(1.0, min(60.0, float(analysis_data.get('reasoning_time_estimate', 5.0))))
        
        # Ensure confidence is in valid range
        confidence = max(0.0, min(1.0, float(analysis_data.get('confidence', 0.8))))
        
        return {
            'complexity_score': complexity_score,
            'recommended_mode': recommended_mode,
            'reasoning_time_estimate': time_estimate,
            'reasoning_factors': analysis_data.get('reasoning_factors', []),
            'confidence': confidence
        }
    
    def _fallback_complexity_analysis(self, prompt: str) -> Dict[str, Any]:
        """Provide fallback complexity analysis using simple heuristics."""
        
        # Simple heuristic-based analysis
        complexity_score = 0.5
        
        # Length factor
        if len(prompt) > 500:
            complexity_score += 0.2
        elif len(prompt) < 50:
            complexity_score -= 0.2
        
        # Question complexity
        import re
        question_words = len(re.findall(r'\b(what|why|how|when|where|which|who)\b', prompt.lower()))
        complexity_score += min(question_words * 0.1, 0.2)
        
        # Technical terms
        technical_terms = ['algorithm', 'implementation', 'analysis', 'system', 'complex']
        if any(term in prompt.lower() for term in technical_terms):
            complexity_score += 0.2
        
        # Normalize
        complexity_score = max(0.0, min(1.0, complexity_score))
        
        # Recommend mode based on complexity
        if complexity_score < 0.3:
            recommended_mode = 'rapid'
        elif complexity_score < 0.7:
            recommended_mode = 'thoughtful'
        else:
            recommended_mode = 'step_by_step'
        
        return {
            'complexity_score': complexity_score,
            'recommended_mode': recommended_mode,
            'reasoning_time_estimate': complexity_score * 20 + 5,
            'reasoning_factors': ['length', 'question_complexity', 'technical_content'],
            'confidence': 0.6
        }
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the Claude reasoning provider."""
        return {
            'name': 'claude',
            'version': '1.0.0',
            'capabilities': [
                'rapid_response',
                'thoughtful_analysis',
                'chain_of_thought',
                'step_by_step_reasoning',
                'adaptive_mode_selection',
                'complexity_analysis'
            ],
            'limitations': [
                'No true streaming step generation',
                'Rate limits apply',
                'Requires API key'
            ],
            'supported_modes': [mode.value for mode in self.get_supported_modes()],
            'models': {
                'rapid': self.config.rapid_model,
                'thoughtful': self.config.thoughtful_model,
                'default': self.config.model
            }
        }
    
    async def health_check(self) -> bool:
        """Check if Claude reasoning provider is healthy and available."""
        try:
            # Make a simple test request
            test_response = await self.rapid_response("What is 2+2?")
            
            # Check if we got a reasonable response
            if test_response and len(test_response.strip()) > 0:
                self.logger.info("Claude reasoning health check passed")
                return True
            else:
                self.logger.warning("Claude reasoning health check failed - empty response")
                return False
                
        except Exception as e:
            self.logger.error(f"Claude reasoning health check failed: {e}")
            return False
    
    async def _make_api_call(self, claude_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make API call to Claude.
        
        Args:
            claude_request: The Claude API request
            
        Returns:
            Dict[str, Any]: Claude API response
        """
        headers = {
            'x-api-key': self.config.api_key,
            'content-type': 'application/json',
            'anthropic-version': '2023-06-01'
        }
        
        url = f"{self.config.base_url}/v1/messages"
        
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=claude_request, headers=headers) as response:
                    
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 401:
                        raise AuthenticationError("Invalid Claude API key")
                    elif response.status == 429:
                        raise RateLimitError("Claude API rate limit exceeded")
                    else:
                        error_text = await response.text()
                        raise ReasoningProviderError(
                            f"Claude API error {response.status}: {error_text}"
                        )
                        
        except aiohttp.ClientError as e:
            raise ReasoningProviderError(f"Claude API connection error: {e}")
    
    def _generate_cache_key(self, request: ReasoningRequest) -> str:
        """Generate cache key for a reasoning request."""
        import hashlib
        
        key_data = f"{request.prompt}:{request.mode.value}:{request.temperature}:{request.max_steps}"
        return hashlib.md5(key_data.encode()).hexdigest()