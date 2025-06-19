"""
Reasoning Engine

Core business logic for hybrid reasoning operations. This module orchestrates
different reasoning modes and manages the reasoning workflow.
"""

import logging
import time
from typing import AsyncIterator

from shared.interfaces.reasoning_provider import ReasoningProvider
from shared.models.reasoning_models import (
    ReasoningRequest,
    ReasoningResponse,
    ReasoningStep,
    ReasoningMode,
    ThinkingChain,
    ComplexityAnalysis,
    ReasoningMetrics,
    ConfidenceLevel,
    StepType
)
from .mode_manager import ModeManager
from .step_processor import StepProcessor
from .context_manager import ReasoningContextManager


class ReasoningEngine:
    """
    Core reasoning engine that orchestrates hybrid reasoning operations.

    This engine manages different reasoning modes, processes step-by-step thinking,
    and coordinates between rapid and thoughtful responses.
    """

    def __init__(self, reasoning_provider: ReasoningProvider):
        """
        Initialize the reasoning engine.

        Args:
            reasoning_provider: The reasoning provider implementation
        """
        self.provider = reasoning_provider
        self.mode_manager = ModeManager()
        self.step_processor = StepProcessor()
        self.context_manager = ReasoningContextManager()
        self.metrics = ReasoningMetrics()
        self.logger = logging.getLogger(__name__)

    async def process_request(self, request: ReasoningRequest) -> ReasoningResponse:
        """
        Process a reasoning request using the appropriate mode.

        Args:
            request: The reasoning request to process

        Returns:
            ReasoningResponse: The processed response
        """
        start_time = time.time()

        try:
            # Update metrics
            self.metrics.total_requests += 1

            # Analyze complexity if adaptive mode
            if request.mode == ReasoningMode.ADAPTIVE:
                analysis = await self._analyze_complexity(request.prompt)
                request.mode = analysis.recommended_mode
                request.metadata['complexity_analysis'] = analysis.to_dict()

            # Process based on mode
            response = await self._process_by_mode(request)

            # Calculate processing time
            processing_time = time.time() - start_time
            response.processing_time = processing_time
            response.request_id = request.id

            # Update metrics
            self.metrics.successful_requests += 1
            self._update_mode_usage(request.mode)
            self._update_processing_time(processing_time)

            self.logger.info(
                "Reasoning request processed successfully in %.2fs using %s mode",
                processing_time, request.mode.value
            )

            return response

        except Exception as e:
            self.metrics.failed_requests += 1
            processing_time = time.time() - start_time

            self.logger.error("Reasoning request failed: %s", e)

            return ReasoningResponse(
                request_id=request.id,
                success=False,
                error_message=str(e),
                processing_time=processing_time,
                provider=self.provider.get_provider_info()['name']
            )

    async def _process_by_mode(self, request: ReasoningRequest) -> ReasoningResponse:
        """Process request based on the specified reasoning mode."""

        if request.mode == ReasoningMode.RAPID:
            return await self._process_rapid(request)
        if request.mode == ReasoningMode.THOUGHTFUL:
            return await self._process_thoughtful(request)
        if request.mode == ReasoningMode.CHAIN_OF_THOUGHT:
            return await self._process_chain_of_thought(request)
        if request.mode == ReasoningMode.STEP_BY_STEP:
            return await self._process_step_by_step(request)

        # Default to thoughtful mode
        return await self._process_thoughtful(request)

    async def _process_rapid(self, request: ReasoningRequest) -> ReasoningResponse:
        """Process request in rapid mode."""
        rapid_answer = await self.provider.rapid_response(request.prompt)

        return ReasoningResponse(
            rapid_answer=rapid_answer,
            mode_used=ReasoningMode.RAPID,
            complexity_score=0.2,  # Low complexity for rapid mode
            provider=self.provider.get_provider_info()['name']
        )

    async def _process_thoughtful(self, request: ReasoningRequest) -> ReasoningResponse:
        """Process request in thoughtful mode."""
        thinking_chain = await self.provider.thoughtful_response(request.prompt)

        return ReasoningResponse(
            thinking_chain=thinking_chain,
            mode_used=ReasoningMode.THOUGHTFUL,
            complexity_score=0.7,  # High complexity for thoughtful mode
            provider=self.provider.get_provider_info()['name']
        )

    async def _process_chain_of_thought(self, request: ReasoningRequest) -> ReasoningResponse:
        """Process request with explicit chain of thought reasoning."""

        # Create thinking chain
        thinking_chain = ThinkingChain()

        # Process step by step through provider
        async for step in self.provider.think_step_by_step(request):
            thinking_chain.add_step(step)

            # Stop if max steps reached
            if len(thinking_chain.steps) >= request.max_steps:
                break

        # Generate final answer based on steps
        if thinking_chain.steps:
            final_step = thinking_chain.steps[-1]
            thinking_chain.final_answer = final_step.content
            thinking_chain.overall_confidence = final_step.confidence

        return ReasoningResponse(
            thinking_chain=thinking_chain,
            mode_used=ReasoningMode.CHAIN_OF_THOUGHT,
            complexity_score=0.8,
            provider=self.provider.get_provider_info()['name']
        )

    async def _process_step_by_step(self, request: ReasoningRequest) -> ReasoningResponse:
        """Process request with detailed step-by-step analysis."""

        # Create comprehensive thinking chain
        thinking_chain = ThinkingChain()

        # Add analysis step
        analysis_step = ReasoningStep(
            step_type=StepType.ANALYSIS,
            description="Initial problem analysis",
            content=f"Analyzing the problem: {request.prompt}",
            reasoning="Breaking down the problem into components",
            confidence=ConfidenceLevel.HIGH
        )
        thinking_chain.add_step(analysis_step)

        # Process through provider for detailed reasoning
        async for step in self.provider.think_step_by_step(request):
            thinking_chain.add_step(step)

            if len(thinking_chain.steps) >= request.max_steps:
                break

        # Add conclusion step
        if thinking_chain.steps:
            conclusion_step = ReasoningStep(
                step_type=StepType.CONCLUSION,
                description="Final conclusion",
                content="Based on the analysis above, here is my conclusion:",
                reasoning="Synthesizing all reasoning steps into final answer",
                confidence=ConfidenceLevel.HIGH
            )
            thinking_chain.add_step(conclusion_step)

            # Set final answer
            thinking_chain.final_answer = conclusion_step.content
            thinking_chain.overall_confidence = ConfidenceLevel.HIGH

        return ReasoningResponse(
            thinking_chain=thinking_chain,
            mode_used=ReasoningMode.STEP_BY_STEP,
            complexity_score=0.9,  # Very high complexity
            provider=self.provider.get_provider_info()['name']
        )

    async def _analyze_complexity(self, prompt: str) -> ComplexityAnalysis:
        """Analyze prompt complexity to determine optimal reasoning mode."""

        analysis_data = await self.provider.analyze_complexity(prompt)

        return ComplexityAnalysis(
            prompt=prompt,
            complexity_score=analysis_data.get('complexity_score', 0.5),
            recommended_mode=ReasoningMode(analysis_data.get('recommended_mode', 'thoughtful')),
            reasoning_factors=analysis_data.get('reasoning_factors', []),
            estimated_time=analysis_data.get('reasoning_time_estimate', 5.0),
            confidence=analysis_data.get('confidence', 0.8)
        )

    def _update_mode_usage(self, mode: ReasoningMode) -> None:
        """Update mode usage statistics."""
        mode_key = mode.value
        self.metrics.mode_usage[mode_key] = self.metrics.mode_usage.get(mode_key, 0) + 1

    def _update_processing_time(self, processing_time: float) -> None:
        """Update average processing time."""
        current_avg = self.metrics.average_processing_time
        total_requests = self.metrics.successful_requests

        if total_requests <= 1:
            self.metrics.average_processing_time = processing_time
        else:
            # Calculate running average
            self.metrics.average_processing_time = (
                (current_avg * (total_requests - 1) + processing_time) / total_requests
            )

    async def stream_reasoning(
        self,
        request: ReasoningRequest
    ) -> AsyncIterator[ReasoningStep]:
        """
        Stream reasoning steps as they are generated.

        Args:
            request: The reasoning request

        Yields:
            ReasoningStep: Each step in the reasoning process
        """
        async for step in self.provider.think_step_by_step(request):
            yield step

    def get_metrics(self) -> ReasoningMetrics:
        """Get current reasoning metrics."""
        return self.metrics

    async def health_check(self) -> bool:
        """Check if the reasoning engine is healthy."""
        try:
            return await self.provider.health_check()
        except Exception as e:
            self.logger.error("Health check failed: %s", e)
            return False
