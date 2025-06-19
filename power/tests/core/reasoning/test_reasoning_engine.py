"""
Test Reasoning Engine

Comprehensive tests for the core reasoning engine functionality.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from typing import List

from core.reasoning.reasoning_engine import ReasoningEngine
from shared.interfaces.reasoning_provider import ReasoningProvider
from shared.models.reasoning_models import (
    ReasoningRequest,
    ReasoningResponse,
    ReasoningMode,
    ReasoningStep,
    ThinkingChain,
    StepType,
    ConfidenceLevel
)


class MockReasoningProvider(ReasoningProvider):
    """Mock reasoning provider for testing."""
    
    def __init__(self):
        self.rapid_responses = {}
        self.thoughtful_responses = {}
        self.complexity_analyses = {}
        self.health_status = True
    
    async def reason(self, request: ReasoningRequest) -> ReasoningResponse:
        """Mock reason implementation."""
        if request.mode == ReasoningMode.RAPID:
            return ReasoningResponse(
                request_id=request.id,
                rapid_answer="Mock rapid answer",
                mode_used=ReasoningMode.RAPID,
                complexity_score=0.2,
                provider="mock",
                success=True
            )
        else:
            chain = ThinkingChain()
            step = ReasoningStep(
                step_number=1,
                step_type=StepType.ANALYSIS,
                description="Mock analysis",
                content="Mock reasoning step",
                confidence=ConfidenceLevel.HIGH
            )
            chain.add_step(step)
            chain.final_answer = "Mock thoughtful answer"
            
            return ReasoningResponse(
                request_id=request.id,
                thinking_chain=chain,
                mode_used=request.mode,
                complexity_score=0.7,
                provider="mock",
                success=True
            )
    
    async def think_step_by_step(self, request: ReasoningRequest):
        """Mock step-by-step thinking."""
        for i in range(min(3, request.max_steps)):
            yield ReasoningStep(
                step_number=i + 1,
                step_type=StepType.ANALYSIS,
                description=f"Step {i + 1}",
                content=f"Mock step {i + 1} content",
                confidence=ConfidenceLevel.MEDIUM
            )
    
    async def rapid_response(self, prompt: str) -> str:
        """Mock rapid response."""
        return "Mock rapid answer"
    
    async def thoughtful_response(self, prompt: str) -> ThinkingChain:
        """Mock thoughtful response."""
        chain = ThinkingChain()
        step = ReasoningStep(
            step_number=1,
            step_type=StepType.ANALYSIS,
            description="Thoughtful analysis",
            content="Mock thoughtful content",
            confidence=ConfidenceLevel.HIGH
        )
        chain.add_step(step)
        chain.final_answer = "Mock thoughtful answer"
        return chain
    
    def get_supported_modes(self) -> List[ReasoningMode]:
        """Mock supported modes."""
        return [ReasoningMode.RAPID, ReasoningMode.THOUGHTFUL]
    
    async def analyze_complexity(self, prompt: str) -> dict:
        """Mock complexity analysis."""
        return {
            'complexity_score': 0.5,
            'recommended_mode': 'thoughtful',
            'reasoning_time_estimate': 10.0,
            'reasoning_factors': ['mock_factor'],
            'confidence': 0.8
        }
    
    def get_provider_info(self) -> dict:
        """Mock provider info."""
        return {
            'name': 'mock',
            'version': '1.0.0',
            'capabilities': ['rapid', 'thoughtful']
        }
    
    async def health_check(self) -> bool:
        """Mock health check."""
        return self.health_status


class TestReasoningEngine:
    """Test cases for reasoning engine."""
    
    @pytest.fixture
    def mock_provider(self):
        """Create mock reasoning provider."""
        return MockReasoningProvider()
    
    @pytest.fixture
    def reasoning_engine(self, mock_provider):
        """Create reasoning engine with mock provider."""
        return ReasoningEngine(mock_provider)
    
    @pytest.mark.asyncio
    async def test_rapid_mode_processing(self, reasoning_engine):
        """Test rapid mode processing."""
        request = ReasoningRequest(
            prompt="What is 2+2?",
            mode=ReasoningMode.RAPID
        )
        
        response = await reasoning_engine.process_request(request)
        
        assert response.success
        assert response.mode_used == ReasoningMode.RAPID
        assert response.rapid_answer == "Mock rapid answer"
        assert response.complexity_score == 0.2
        assert response.processing_time > 0
    
    @pytest.mark.asyncio
    async def test_thoughtful_mode_processing(self, reasoning_engine):
        """Test thoughtful mode processing."""
        request = ReasoningRequest(
            prompt="Explain quantum computing",
            mode=ReasoningMode.THOUGHTFUL
        )
        
        response = await reasoning_engine.process_request(request)
        
        assert response.success
        assert response.mode_used == ReasoningMode.THOUGHTFUL
        assert response.thinking_chain is not None
        assert len(response.thinking_chain.steps) > 0
        assert response.thinking_chain.final_answer == "Mock thoughtful answer"
    
    @pytest.mark.asyncio
    async def test_adaptive_mode_selection(self, reasoning_engine):
        """Test adaptive mode automatically selects appropriate mode."""
        request = ReasoningRequest(
            prompt="Simple question",
            mode=ReasoningMode.ADAPTIVE
        )
        
        response = await reasoning_engine.process_request(request)
        
        assert response.success
        # Mode should be selected based on complexity analysis (will be 'thoughtful' from mock)
        assert response.mode_used == ReasoningMode.THOUGHTFUL
        # The request should have metadata added about complexity analysis
        assert request.metadata is not None
    
    @pytest.mark.asyncio
    async def test_step_by_step_mode(self, reasoning_engine):
        """Test step-by-step reasoning mode."""
        request = ReasoningRequest(
            prompt="Solve complex problem step by step",
            mode=ReasoningMode.STEP_BY_STEP,
            max_steps=5
        )
        
        response = await reasoning_engine.process_request(request)
        
        assert response.success
        assert response.mode_used == ReasoningMode.STEP_BY_STEP
        assert response.thinking_chain is not None
        # Should have analysis step, provider steps, and conclusion
        assert len(response.thinking_chain.steps) >= 2
    
    @pytest.mark.asyncio
    async def test_chain_of_thought_mode(self, reasoning_engine):
        """Test chain of thought reasoning mode."""
        request = ReasoningRequest(
            prompt="Think through this problem",
            mode=ReasoningMode.CHAIN_OF_THOUGHT,
            max_steps=3
        )
        
        response = await reasoning_engine.process_request(request)
        
        assert response.success
        assert response.mode_used == ReasoningMode.CHAIN_OF_THOUGHT
        assert response.thinking_chain is not None
        assert len(response.thinking_chain.steps) <= 3
    
    @pytest.mark.asyncio
    async def test_streaming_reasoning(self, reasoning_engine):
        """Test streaming reasoning steps."""
        request = ReasoningRequest(
            prompt="Stream reasoning steps",
            mode=ReasoningMode.STEP_BY_STEP,
            max_steps=3
        )
        
        steps = []
        async for step in reasoning_engine.stream_reasoning(request):
            steps.append(step)
        
        assert len(steps) <= 3
        assert all(isinstance(step, ReasoningStep) for step in steps)
        assert all(step.step_number > 0 for step in steps)
    
    @pytest.mark.asyncio
    async def test_metrics_tracking(self, reasoning_engine):
        """Test that metrics are properly tracked."""
        initial_metrics = reasoning_engine.get_metrics()
        assert initial_metrics.total_requests == 0
        
        request = ReasoningRequest(
            prompt="Test metrics",
            mode=ReasoningMode.RAPID
        )
        
        await reasoning_engine.process_request(request)
        
        updated_metrics = reasoning_engine.get_metrics()
        assert updated_metrics.total_requests == 1
        assert updated_metrics.successful_requests == 1
        assert ReasoningMode.RAPID.value in updated_metrics.mode_usage
    
    @pytest.mark.asyncio
    async def test_error_handling(self, reasoning_engine):
        """Test error handling in reasoning engine."""
        # Mock the provider to raise an exception during processing
        original_analyze = reasoning_engine.provider.analyze_complexity
        reasoning_engine.provider.analyze_complexity = AsyncMock(side_effect=Exception("Test error"))
        
        request = ReasoningRequest(
            prompt="This will fail",
            mode=ReasoningMode.ADAPTIVE  # Use adaptive to trigger complexity analysis
        )
        
        response = await reasoning_engine.process_request(request)
        
        assert not response.success
        assert "Test error" in response.error_message
        assert response.processing_time > 0
        
        # Check metrics reflect the failure
        metrics = reasoning_engine.get_metrics()
        assert metrics.failed_requests == 1
        
        # Restore original method
        reasoning_engine.provider.analyze_complexity = original_analyze
    
    @pytest.mark.asyncio
    async def test_health_check(self, reasoning_engine):
        """Test health check functionality."""
        # Provider is healthy
        is_healthy = await reasoning_engine.health_check()
        assert is_healthy
        
        # Make provider unhealthy
        reasoning_engine.provider.health_status = False
        is_healthy = await reasoning_engine.health_check()
        assert not is_healthy
    
    def test_mode_usage_tracking(self, reasoning_engine):
        """Test mode usage statistics tracking."""
        # Test private method for mode usage
        reasoning_engine._update_mode_usage(ReasoningMode.RAPID)
        reasoning_engine._update_mode_usage(ReasoningMode.RAPID)
        reasoning_engine._update_mode_usage(ReasoningMode.THOUGHTFUL)
        
        metrics = reasoning_engine.get_metrics()
        assert metrics.mode_usage[ReasoningMode.RAPID.value] == 2
        assert metrics.mode_usage[ReasoningMode.THOUGHTFUL.value] == 1
    
    def test_processing_time_tracking(self, reasoning_engine):
        """Test processing time tracking."""
        # Set up metrics for testing
        reasoning_engine.metrics.successful_requests = 1
        reasoning_engine.metrics.average_processing_time = 0.0
        
        # First request
        reasoning_engine._update_processing_time(5.0)
        assert reasoning_engine.metrics.average_processing_time == 5.0
        
        # Second request  
        reasoning_engine.metrics.successful_requests = 2
        reasoning_engine._update_processing_time(3.0)
        assert reasoning_engine.metrics.average_processing_time == 4.0
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, reasoning_engine):
        """Test request timeout handling."""
        request = ReasoningRequest(
            prompt="Test timeout",
            mode=ReasoningMode.RAPID,
            timeout=0.001  # Very short timeout
        )
        
        # This should complete quickly in mock, but tests timeout parameter passing
        response = await reasoning_engine.process_request(request)
        assert response.success  # Mock completes quickly
    
    @pytest.mark.asyncio
    async def test_max_steps_limit(self, reasoning_engine):
        """Test max steps limitation."""
        request = ReasoningRequest(
            prompt="Test max steps",
            mode=ReasoningMode.CHAIN_OF_THOUGHT,
            max_steps=2
        )
        
        response = await reasoning_engine.process_request(request)
        
        assert response.success
        if response.thinking_chain:
            assert len(response.thinking_chain.steps) <= 2