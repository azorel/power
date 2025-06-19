"""
Reasoning Models

This module defines the shared data models for reasoning operations following
the three-layer architecture standards.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional, Union
from uuid import uuid4, UUID


class ReasoningMode(Enum):
    """Enumeration of reasoning modes."""
    RAPID = "rapid"
    THOUGHTFUL = "thoughtful"
    ADAPTIVE = "adaptive"
    CHAIN_OF_THOUGHT = "chain_of_thought"
    STEP_BY_STEP = "step_by_step"


class StepType(Enum):
    """Enumeration of reasoning step types."""
    ANALYSIS = "analysis"
    INFERENCE = "inference"
    SYNTHESIS = "synthesis"
    EVALUATION = "evaluation"
    CONCLUSION = "conclusion"


class ConfidenceLevel(Enum):
    """Enumeration of confidence levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class ReasoningStep:
    """Represents a single step in the reasoning process."""
    
    id: UUID = field(default_factory=uuid4)
    step_number: int = 0
    step_type: StepType = StepType.ANALYSIS
    description: str = ""
    content: str = ""
    reasoning: str = ""
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert reasoning step to dictionary."""
        return {
            'id': str(self.id),
            'step_number': self.step_number,
            'step_type': self.step_type.value,
            'description': self.description,
            'content': self.content,
            'reasoning': self.reasoning,
            'confidence': self.confidence.value,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class ThinkingChain:
    """Represents a complete chain of reasoning steps."""
    
    id: UUID = field(default_factory=uuid4)
    steps: List[ReasoningStep] = field(default_factory=list)
    final_answer: str = ""
    overall_confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    reasoning_time: float = 0.0  # seconds
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def add_step(self, step: ReasoningStep) -> None:
        """Add a reasoning step to the chain."""
        step.step_number = len(self.steps) + 1
        self.steps.append(step)
    
    def get_step_by_type(self, step_type: StepType) -> Optional[ReasoningStep]:
        """Get the first step of a specific type."""
        for step in self.steps:
            if step.step_type == step_type:
                return step
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert thinking chain to dictionary."""
        return {
            'id': str(self.id),
            'steps': [step.to_dict() for step in self.steps],
            'final_answer': self.final_answer,
            'overall_confidence': self.overall_confidence.value,
            'reasoning_time': self.reasoning_time,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class ReasoningRequest:
    """Represents a request for reasoning services."""
    
    id: UUID = field(default_factory=uuid4)
    prompt: str = ""
    mode: ReasoningMode = ReasoningMode.ADAPTIVE
    max_steps: int = 10
    timeout: float = 30.0  # seconds
    temperature: float = 0.7
    include_confidence: bool = True
    stream_steps: bool = False
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert reasoning request to dictionary."""
        return {
            'id': str(self.id),
            'prompt': self.prompt,
            'mode': self.mode.value,
            'max_steps': self.max_steps,
            'timeout': self.timeout,
            'temperature': self.temperature,
            'include_confidence': self.include_confidence,
            'stream_steps': self.stream_steps,
            'context': self.context,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class ReasoningResponse:
    """Represents a response from reasoning services."""
    
    id: UUID = field(default_factory=uuid4)
    request_id: UUID = field(default_factory=uuid4)
    thinking_chain: Optional[ThinkingChain] = None
    rapid_answer: str = ""
    mode_used: ReasoningMode = ReasoningMode.ADAPTIVE
    processing_time: float = 0.0  # seconds
    tokens_used: int = 0
    complexity_score: float = 0.0  # 0-1 scale
    provider: str = ""
    success: bool = True
    error_message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def get_final_answer(self) -> str:
        """Get the final answer from either rapid or thoughtful response."""
        if self.thinking_chain and self.thinking_chain.final_answer:
            return self.thinking_chain.final_answer
        return self.rapid_answer
    
    def get_confidence(self) -> ConfidenceLevel:
        """Get overall confidence level."""
        if self.thinking_chain:
            return self.thinking_chain.overall_confidence
        return ConfidenceLevel.MEDIUM
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert reasoning response to dictionary."""
        return {
            'id': str(self.id),
            'request_id': str(self.request_id),
            'thinking_chain': self.thinking_chain.to_dict() if self.thinking_chain else None,
            'rapid_answer': self.rapid_answer,
            'mode_used': self.mode_used.value,
            'processing_time': self.processing_time,
            'tokens_used': self.tokens_used,
            'complexity_score': self.complexity_score,
            'provider': self.provider,
            'success': self.success,
            'error_message': self.error_message,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class ComplexityAnalysis:
    """Represents complexity analysis of a prompt."""
    
    prompt: str = ""
    complexity_score: float = 0.0  # 0-1 scale
    recommended_mode: ReasoningMode = ReasoningMode.ADAPTIVE
    reasoning_factors: List[str] = field(default_factory=list)
    estimated_time: float = 0.0  # seconds
    confidence: float = 0.0  # 0-1 scale
    metadata: Dict[str, Any] = field(default_factory=dict)
    analyzed_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert complexity analysis to dictionary."""
        return {
            'prompt': self.prompt,
            'complexity_score': self.complexity_score,
            'recommended_mode': self.recommended_mode.value,
            'reasoning_factors': self.reasoning_factors,
            'estimated_time': self.estimated_time,
            'confidence': self.confidence,
            'metadata': self.metadata,
            'analyzed_at': self.analyzed_at.isoformat()
        }


@dataclass
class ReasoningMetrics:
    """Represents metrics for reasoning operations."""
    
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_processing_time: float = 0.0
    mode_usage: Dict[str, int] = field(default_factory=dict)
    complexity_distribution: Dict[str, int] = field(default_factory=dict)
    confidence_distribution: Dict[str, int] = field(default_factory=dict)
    total_tokens_used: int = 0
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert reasoning metrics to dictionary."""
        return {
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'success_rate': self.success_rate(),
            'average_processing_time': self.average_processing_time,
            'mode_usage': self.mode_usage,
            'complexity_distribution': self.complexity_distribution,
            'confidence_distribution': self.confidence_distribution,
            'total_tokens_used': self.total_tokens_used,
            'last_updated': self.last_updated.isoformat()
        }


# Type aliases for better code readability
ReasoningChain = ThinkingChain
ReasoningAnalysis = ComplexityAnalysis