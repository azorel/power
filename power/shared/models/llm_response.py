"""
Shared data model for LLM responses.
All adapters must convert their API responses to this format.
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class FinishReason(Enum):
    """Standardized finish reasons across LLM providers."""
    COMPLETED = "completed"
    MAX_TOKENS = "max_tokens"
    STOP_SEQUENCE = "stop_sequence"
    CONTENT_FILTER = "content_filter"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class UsageStats:
    """Token usage statistics for the LLM request."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    # Cost information (if available)
    prompt_cost: Optional[float] = None
    completion_cost: Optional[float] = None
    total_cost: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert usage stats to dictionary format."""
        result = {
            'prompt_tokens': self.prompt_tokens,
            'completion_tokens': self.completion_tokens,
            'total_tokens': self.total_tokens
        }

        if self.prompt_cost is not None:
            result['prompt_cost'] = self.prompt_cost
        if self.completion_cost is not None:
            result['completion_cost'] = self.completion_cost
        if self.total_cost is not None:
            result['total_cost'] = self.total_cost

        return result


@dataclass
class LLMResponse:  # pylint: disable=too-many-instance-attributes
    """Standardized response format for all LLM providers."""

    content: str
    finish_reason: FinishReason
    usage: UsageStats

    # Model information
    model: str
    provider: str

    # Response metadata
    response_id: Optional[str] = None
    request_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    # Performance metrics
    latency_ms: Optional[int] = None
    processing_time_ms: Optional[int] = None

    # Additional provider-specific data
    provider_metadata: Dict[str, Any] = field(default_factory=dict)

    # Safety and quality scores (if available)
    safety_scores: Optional[Dict[str, float]] = None
    quality_score: Optional[float] = None

    def __post_init__(self):
        """Validate response parameters."""
        if not self.content:
            # Allow empty content for some finish reasons
            if self.finish_reason not in [FinishReason.CONTENT_FILTER, FinishReason.ERROR]:
                raise ValueError("content cannot be empty unless filtered or error")

        if not self.model:
            raise ValueError("model cannot be empty")

        if not self.provider:
            raise ValueError("provider cannot be empty")

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary format."""
        result = {
            'content': self.content,
            'finish_reason': self.finish_reason.value,
            'usage': self.usage.to_dict(),
            'model': self.model,
            'provider': self.provider,
            'timestamp': self.timestamp.isoformat(),
            'provider_metadata': self.provider_metadata
        }

        # Add optional fields if present
        optional_fields = [
            'response_id', 'request_id', 'latency_ms',
            'processing_time_ms', 'safety_scores', 'quality_score'
        ]

        for field_name in optional_fields:
            value = getattr(self, field_name)
            if value is not None:
                result[field_name] = value

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LLMResponse':
        """Create response from dictionary format."""
        # Convert timestamp string back to datetime
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])

        # Convert finish_reason string to enum
        if 'finish_reason' in data:
            data['finish_reason'] = FinishReason(data['finish_reason'])

        # Convert usage dict to UsageStats object
        if 'usage' in data and isinstance(data['usage'], dict):
            data['usage'] = UsageStats(**data['usage'])

        return cls(**data)

    @property
    def is_successful(self) -> bool:
        """Check if the response was successful."""
        return self.finish_reason in [FinishReason.COMPLETED, FinishReason.MAX_TOKENS]

    @property
    def is_complete(self) -> bool:
        """Check if the response completed naturally (not truncated)."""
        return self.finish_reason == FinishReason.COMPLETED

    @property
    def was_truncated(self) -> bool:
        """Check if the response was truncated due to token limits."""
        return self.finish_reason == FinishReason.MAX_TOKENS

    @property
    def was_filtered(self) -> bool:
        """Check if the response was filtered by content policies."""
        return self.finish_reason == FinishReason.CONTENT_FILTER

    @property
    def had_error(self) -> bool:
        """Check if the response had an error."""
        return self.finish_reason == FinishReason.ERROR


@dataclass
class StreamingResponse:
    """Individual chunk in a streaming LLM response."""

    content_delta: str  # New content since last chunk
    cumulative_content: str  # All content so far
    is_final: bool = False

    # Chunk metadata
    chunk_index: int = 0
    timestamp: datetime = field(default_factory=datetime.now)

    # Final response data (only present in final chunk)
    final_response: Optional[LLMResponse] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert streaming response to dictionary format."""
        result = {
            'content_delta': self.content_delta,
            'cumulative_content': self.cumulative_content,
            'is_final': self.is_final,
            'chunk_index': self.chunk_index,
            'timestamp': self.timestamp.isoformat()
        }

        if self.final_response:
            result['final_response'] = self.final_response.to_dict()

        return result


@dataclass
class BatchResponse:  # pylint: disable=too-many-instance-attributes
    """Response for batch processing of multiple LLM requests."""

    responses: List[LLMResponse]
    batch_id: str
    total_requests: int
    successful_requests: int
    failed_requests: int

    # Batch timing
    start_time: datetime
    end_time: datetime

    # Aggregate usage statistics
    total_usage: UsageStats

    def __post_init__(self):
        """Validate batch response."""
        if len(self.responses) != self.total_requests:
            raise ValueError("Number of responses must match total_requests")

        if self.successful_requests + self.failed_requests != self.total_requests:
            raise ValueError("successful + failed requests must equal total")

    @property
    def success_rate(self) -> float:
        """Calculate the success rate of the batch."""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests

    @property
    def processing_time_seconds(self) -> float:
        """Calculate total processing time in seconds."""
        return (self.end_time - self.start_time).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """Convert batch response to dictionary format."""
        return {
            'responses': [resp.to_dict() for resp in self.responses],
            'batch_id': self.batch_id,
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'total_usage': self.total_usage.to_dict(),
            'success_rate': self.success_rate,
            'processing_time_seconds': self.processing_time_seconds
        }
