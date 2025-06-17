"""
Gemini API client - backward compatibility wrapper.
Imports the unified client for existing code compatibility.
"""

# Import the new unified client
from .unified_client import GeminiClient as _UnifiedGeminiClient

# Export for backward compatibility
GeminiClient = _UnifiedGeminiClient

# Re-export commonly used classes for backward compatibility
__all__ = ['GeminiClient']
