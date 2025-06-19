"""
Memory Models

Enhanced data models for memory storage and retrieval.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum

from shared.interfaces.memory_provider import MemoryType


class MemoryImportance(Enum):
    """Memory importance levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class MemoryContext:
    """Context information for memory storage."""
    agent_id: str
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    task_id: Optional[str] = None
    workspace_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    additional_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EnhancedMemoryItem:
    """Enhanced memory item with additional metadata."""
    id: str
    content: str
    memory_type: MemoryType
    importance: MemoryImportance
    context: MemoryContext
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    accessed_at: Optional[datetime] = None
    access_count: int = 0
    relevance_score: float = 0.0
    embedding_vector: Optional[List[float]] = None
    related_memories: List[str] = field(default_factory=list)
    expires_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'id': self.id,
            'content': self.content,
            'memory_type': self.memory_type.value,
            'importance': self.importance.value,
            'context': {
                'agent_id': self.context.agent_id,
                'session_id': self.context.session_id,
                'conversation_id': self.context.conversation_id,
                'task_id': self.context.task_id,
                'workspace_id': self.context.workspace_id,
                'tags': self.context.tags,
                'additional_context': self.context.additional_context
            },
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'accessed_at': self.accessed_at.isoformat() if self.accessed_at else None,
            'access_count': self.access_count,
            'relevance_score': self.relevance_score,
            'embedding_vector': self.embedding_vector,
            'related_memories': self.related_memories,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnhancedMemoryItem':
        """Create from dictionary format."""
        context_data = data.get('context', {})
        context = MemoryContext(
            agent_id=context_data.get('agent_id', ''),
            session_id=context_data.get('session_id'),
            conversation_id=context_data.get('conversation_id'),
            task_id=context_data.get('task_id'),
            workspace_id=context_data.get('workspace_id'),
            tags=context_data.get('tags', []),
            additional_context=context_data.get('additional_context', {})
        )

        return cls(
            id=data['id'],
            content=data['content'],
            memory_type=MemoryType(data['memory_type']),
            importance=MemoryImportance(data['importance']),
            context=context,
            metadata=data.get('metadata', {}),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            accessed_at=datetime.fromisoformat(data['accessed_at']) if data.get(
                'accessed_at') else None,
            access_count=data.get('access_count', 0),
            relevance_score=data.get('relevance_score', 0.0),
            embedding_vector=data.get('embedding_vector'),
            related_memories=data.get('related_memories', []),
            expires_at=datetime.fromisoformat(data['expires_at']) if data.get(
                'expires_at') else None
        )


@dataclass
class MemorySearchResult:
    """Result from memory search operation."""
    memories: List[EnhancedMemoryItem]
    total_count: int
    search_time_ms: float
    query_embedding: Optional[List[float]] = None
    search_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryStats:
    """Memory provider statistics."""
    total_memories: int
    memories_by_type: Dict[str, int]
    memories_by_importance: Dict[str, int]
    average_relevance: float
    oldest_memory: Optional[datetime]
    newest_memory: Optional[datetime]
    storage_size_bytes: int
    access_patterns: Dict[str, int] = field(default_factory=dict)
