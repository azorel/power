"""Package initialization."""

# Shared interfaces for adapter contracts
from .memory_provider import MemoryProvider, MemoryType, MemoryQuery, MemoryItem
from .llm_provider import LLMProvider

__all__ = [
    'MemoryProvider',
    'MemoryType', 
    'MemoryQuery',
    'MemoryItem',
    'LLMProvider'
]
