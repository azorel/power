"""
Gemini API adapter for Power Builder.
Provides integration with Google Gen AI (2024) through the shared LLM interface.
"""

from .client import GeminiClient
from .config import GeminiConfig
from .data_mapper import GeminiDataMapper
from .rate_limiter import GeminiRateLimiter
from .exceptions import GeminiExceptionMapper, handle_gemini_exception

# Public exports
__all__ = [
    'GeminiClient',
    'GeminiConfig',
    'GeminiDataMapper',
    'GeminiRateLimiter',
    'GeminiExceptionMapper',
    'handle_gemini_exception'
]

# Version info
__version__ = '1.0.0'
__author__ = 'Power Builder Team'
__description__ = 'Google Gemini API adapter for Power Builder LLM system'

# Provider registration information
PROVIDER_INFO = {
    'name': 'gemini',
    'display_name': 'Google Gemini',
    'version': __version__,
    'description': __description__,
    'capabilities': [
        'text_generation',
        'chat_completion',
        'image_input',
        'streaming',
        'safety_filtering'
    ],
    'models': [
        'gemini-2.0-flash',
        'gemini-1.5-pro',
        'gemini-1.5-flash',
        'gemini-pro',
        'gemini-pro-vision'
    ],
    'client_class': GeminiClient,
    'config_class': GeminiConfig
}


def create_client(config: GeminiConfig = None) -> GeminiClient:
    """
    Factory function to create a configured Gemini client.

    Args:
        config: Optional configuration (creates default if None)

    Returns:
        Configured GeminiClient instance
    """
    return GeminiClient(config)


def get_provider_info() -> dict:
    """
    Get information about this adapter provider.

    Returns:
        Dictionary with provider information
    """
    return PROVIDER_INFO.copy()


def check_dependencies() -> bool:
    """
    Check if all required dependencies are available.

    Returns:
        True if dependencies are satisfied, False otherwise
    """
    try:
        import google.generativeai  # pylint: disable=import-outside-toplevel,unused-import
        return True
    except ImportError:
        return False


def get_required_packages() -> list:
    """
    Get list of required packages for this adapter.

    Returns:
        List of package requirements
    """
    return [
        'google-generativeai>=0.8.0',
        'requests>=2.31.0'
    ]
