"""
Reasoning Provider Interface

This module defines the abstract interface for reasoning providers following the
three-layer architecture standards. All reasoning adapters must implement this interface.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncIterator

from shared.models.reasoning_models import (
    ReasoningRequest,
    ReasoningResponse,
    ReasoningStep,
    ReasoningMode,
    ThinkingChain
)


class ReasoningProvider(ABC):
    """
    Abstract base class for reasoning providers.
    
    This interface defines the contract that all reasoning adapters must implement
    to ensure consistent behavior across different reasoning engines.
    """

    @abstractmethod
    async def reason(self, request: ReasoningRequest) -> ReasoningResponse:
        """
        Process a reasoning request and return a structured response.
        
        Args:
            request: The reasoning request containing prompt and configuration
            
        Returns:
            ReasoningResponse: Structured response with reasoning steps and result
            
        Raises:
            ReasoningProviderError: For provider-specific errors
            RateLimitError: When rate limits are exceeded
            AuthenticationError: For authentication failures
        """
        pass

    @abstractmethod
    async def think_step_by_step(self, request: ReasoningRequest) -> AsyncIterator[ReasoningStep]:
        """
        Process request with step-by-step thinking, yielding each step.
        
        Args:
            request: The reasoning request
            
        Yields:
            ReasoningStep: Each step in the reasoning process
            
        Raises:
            ReasoningProviderError: For provider-specific errors
        """
        pass

    @abstractmethod
    async def rapid_response(self, prompt: str) -> str:
        """
        Generate a rapid response with minimal processing.
        
        Args:
            prompt: The input prompt
            
        Returns:
            str: Quick response without detailed reasoning
            
        Raises:
            ReasoningProviderError: For provider-specific errors
        """
        pass

    @abstractmethod
    async def thoughtful_response(self, prompt: str) -> ThinkingChain:
        """
        Generate a thoughtful response with detailed reasoning chain.
        
        Args:
            prompt: The input prompt
            
        Returns:
            ThinkingChain: Detailed reasoning chain with final answer
            
        Raises:
            ReasoningProviderError: For provider-specific errors
        """
        pass

    @abstractmethod
    def get_supported_modes(self) -> List[ReasoningMode]:
        """
        Get list of reasoning modes supported by this provider.
        
        Returns:
            List[ReasoningMode]: Supported reasoning modes
        """
        pass

    @abstractmethod
    async def analyze_complexity(self, prompt: str) -> Dict[str, Any]:
        """
        Analyze the complexity of a prompt to determine optimal reasoning mode.
        
        Args:
            prompt: The input prompt to analyze
            
        Returns:
            Dict[str, Any]: Complexity analysis results including:
                - complexity_score: float (0-1)
                - recommended_mode: ReasoningMode
                - reasoning_time_estimate: float (seconds)
                - confidence: float (0-1)
        """
        pass

    @abstractmethod
    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get information about the reasoning provider.
        
        Returns:
            Dict[str, Any]: Provider information including:
                - name: str
                - version: str
                - capabilities: List[str]
                - limitations: List[str]
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the reasoning provider is healthy and available.
        
        Returns:
            bool: True if provider is healthy, False otherwise
        """
        pass


class ReasoningProviderError(Exception):
    """Base exception for reasoning provider errors."""
    pass


class RateLimitError(ReasoningProviderError):
    """Raised when rate limits are exceeded."""
    pass


class AuthenticationError(ReasoningProviderError):
    """Raised when authentication fails."""
    pass


class ComplexityAnalysisError(ReasoningProviderError):
    """Raised when complexity analysis fails."""
    pass


class ReasoningModeError(ReasoningProviderError):
    """Raised when an unsupported reasoning mode is requested."""
    pass