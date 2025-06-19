"""
Memory Provider Interface

Defines the contract for memory storage and retrieval systems.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class MemoryType(Enum):
    """Types of memory that can be stored."""
    CONVERSATION = "conversation"
    FACTS = "facts"
    PREFERENCES = "preferences"
    CONTEXT = "context"
    SKILLS = "skills"
    EXPERIENCES = "experiences"


@dataclass
class MemoryQuery:
    """Query parameters for memory retrieval."""
    text: str
    memory_type: Optional[MemoryType] = None
    limit: int = 10
    threshold: float = 0.7
    filters: Optional[Dict[str, Any]] = None


@dataclass
class MemoryItem:
    """Represents a stored memory item."""
    id: str
    content: str
    memory_type: MemoryType
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    relevance_score: float = 0.0


class MemoryProvider(ABC):
    """Abstract base class for memory providers."""

    @abstractmethod
    async def store_memory(
        self,
        content: str,
        memory_type: MemoryType,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store a memory item.
        
        Args:
            content: The content to store
            memory_type: Type of memory
            metadata: Additional metadata
            
        Returns:
            Memory ID
        """

    @abstractmethod
    async def retrieve_memories(self, query: MemoryQuery) -> List[MemoryItem]:
        """
        Retrieve memories based on query.
        
        Args:
            query: Query parameters
            
        Returns:
            List of relevant memory items
        """

    @abstractmethod
    async def update_memory(
        self,
        memory_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update an existing memory.
        
        Args:
            memory_id: ID of memory to update
            content: New content (if provided)
            metadata: New metadata (if provided)
            
        Returns:
            True if updated successfully
        """

    @abstractmethod
    async def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory item.
        
        Args:
            memory_id: ID of memory to delete
            
        Returns:
            True if deleted successfully
        """

    @abstractmethod
    async def search_memories(
        self,
        query_text: str,
        memory_type: Optional[MemoryType] = None,
        limit: int = 10
    ) -> List[MemoryItem]:
        """
        Search memories by text.
        
        Args:
            query_text: Text to search for
            memory_type: Optional memory type filter
            limit: Maximum number of results
            
        Returns:
            List of matching memory items
        """

    @abstractmethod
    async def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get memory provider statistics.
        
        Returns:
            Dictionary containing stats
        """
