"""
Shared data model for LLM requests.
All adapters must accept this format and convert to their specific API format.
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class LLMRequest:  # pylint: disable=too-many-instance-attributes
    """Standardized request format for all LLM providers."""

    prompt: str
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9
    top_k: Optional[int] = None
    frequency_penalty: Optional[float] = 0.0
    presence_penalty: Optional[float] = 0.0
    stop_sequences: Optional[List[str]] = None

    # Model selection
    model: Optional[str] = None

    # Advanced parameters
    seed: Optional[int] = None
    response_format: Optional[str] = "text"  # "text", "json"

    # Metadata
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    # Custom parameters for specific providers
    provider_params: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate request parameters."""
        if not self.prompt or not self.prompt.strip():
            raise ValueError("Prompt cannot be empty")

        if self.max_tokens is not None and self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")

        if self.temperature is not None and not 0.0 <= self.temperature <= 2.0:
            raise ValueError("temperature must be between 0.0 and 2.0")

        if self.top_p is not None and not 0.0 <= self.top_p <= 1.0:
            raise ValueError("top_p must be between 0.0 and 1.0")

    def to_dict(self) -> Dict[str, Any]:
        """Convert request to dictionary format."""
        result = {
            'prompt': self.prompt,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'top_p': self.top_p,
            'top_k': self.top_k,
            'frequency_penalty': self.frequency_penalty,
            'presence_penalty': self.presence_penalty,
            'stop_sequences': self.stop_sequences,
            'model': self.model,
            'seed': self.seed,
            'response_format': self.response_format,
            'request_id': self.request_id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'timestamp': self.timestamp.isoformat(),
            'provider_params': self.provider_params
        }

        # Remove None values for cleaner serialization
        return {k: v for k, v in result.items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LLMRequest':
        """Create request from dictionary format."""
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])

        return cls(**data)

    def with_provider_params(self, **params) -> 'LLMRequest':
        """Create a copy with additional provider-specific parameters."""
        new_request = LLMRequest(
            prompt=self.prompt,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            top_p=self.top_p,
            top_k=self.top_k,
            frequency_penalty=self.frequency_penalty,
            presence_penalty=self.presence_penalty,
            stop_sequences=self.stop_sequences,
            model=self.model,
            seed=self.seed,
            response_format=self.response_format,
            request_id=self.request_id,
            user_id=self.user_id,
            session_id=self.session_id,
            timestamp=self.timestamp,
            provider_params={**self.provider_params, **params}
        )
        return new_request


@dataclass
class ChatMessage:
    """Individual message in a chat conversation."""

    role: str  # "system", "user", "assistant"
    content: str
    name: Optional[str] = None  # Optional name for the message author
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate message parameters."""
        if self.role not in ["system", "user", "assistant"]:
            raise ValueError("role must be 'system', 'user', or 'assistant'")

        if not self.content or not self.content.strip():
            raise ValueError("content cannot be empty")

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary format."""
        result = {
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat()
        }

        if self.name:
            result['name'] = self.name

        return result


@dataclass
class ChatRequest:  # pylint: disable=too-many-instance-attributes
    """Request format for chat-based LLM interactions."""

    messages: List[ChatMessage]
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9
    frequency_penalty: Optional[float] = 0.0
    presence_penalty: Optional[float] = 0.0
    stop_sequences: Optional[List[str]] = None

    # Model selection
    model: Optional[str] = None

    # Metadata
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    # Custom parameters
    provider_params: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate chat request parameters."""
        if not self.messages:
            raise ValueError("messages cannot be empty")

        if self.max_tokens is not None and self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")

    def to_dict(self) -> Dict[str, Any]:
        """Convert chat request to dictionary format."""
        result = {
            'messages': [msg.to_dict() for msg in self.messages],
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'top_p': self.top_p,
            'frequency_penalty': self.frequency_penalty,
            'presence_penalty': self.presence_penalty,
            'stop_sequences': self.stop_sequences,
            'model': self.model,
            'request_id': self.request_id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'timestamp': self.timestamp.isoformat(),
            'provider_params': self.provider_params
        }

        return {k: v for k, v in result.items() if v is not None}
