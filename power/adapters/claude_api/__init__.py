"""
Claude API Adapter - Anthropic Claude Sonnet 4 & Opus 4 Integration
Enhanced with hybrid reasoning, 64K context, and March 2025 knowledge cutoff.
"""

from .config import ClaudeConfig
from .unified_client import ClaudeUnifiedClient
from .exceptions import ClaudeAPIError, ClaudeRateLimitError, ClaudeConnectionError

__all__ = [
    'ClaudeConfig',
    'ClaudeUnifiedClient',
    'ClaudeAPIError',
    'ClaudeRateLimitError',
    'ClaudeConnectionError'
]

__version__ = "1.0.0"
__author__ = "Power Builder - Claude Config Specialist"
__description__ = "Claude API adapter with Sonnet 4/Opus 4 hybrid reasoning capabilities"