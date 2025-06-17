"""
OpenAI API adapter for Power Builder.
Provides comprehensive OpenAI integration with full AdvancedLLMProvider support.
"""

import os
from .config import OpenAIConfig
from .unified_client import OpenAIUnifiedClient
from .text_client import OpenAITextClient
from .chat_client import OpenAIChatClient
from .streaming_client import OpenAIStreamingClient
from .multimodal_client import OpenAIMultimodalClient
from .function_client import OpenAIFunctionClient
from .data_mapper import OpenAIDataMapper
from .rate_limiter import OpenAIRateLimiter
from .exceptions import OpenAIExceptionMapper

# Main client class - this is what external code should use
OpenAIClient = OpenAIUnifiedClient

__version__ = "1.0.0"
__author__ = "Power Builder Team"
__description__ = "OpenAI API adapter with comprehensive LLM capabilities"

# Export main interface
__all__ = [
    'OpenAIClient',
    'OpenAIUnifiedClient',
    'OpenAIConfig',
    'OpenAITextClient',
    'OpenAIChatClient',
    'OpenAIStreamingClient',
    'OpenAIMultimodalClient',
    'OpenAIFunctionClient',
    'OpenAIDataMapper',
    'OpenAIRateLimiter',
    'OpenAIExceptionMapper'
]

# Adapter metadata for discovery
ADAPTER_INFO = {
    'name': 'openai',
    'version': __version__,
    'provider': 'OpenAI',
    'description': __description__,
    'capabilities': [
        'text_generation',
        'chat_completion',
        'streaming',
        'function_calling',
        'image_analysis',
        'image_generation',
        'multimodal',
        'system_instructions',
        'batch_processing'
    ],
    'models': [
        'gpt-4o',
        'gpt-4o-mini',
        'gpt-4-turbo',
        'gpt-4',
        'gpt-3.5-turbo',
        'dall-e-3',
        'dall-e-2'
    ],
    'client_class': OpenAIClient,
    'config_class': OpenAIConfig
}


def create_client(config: dict = None) -> OpenAIUnifiedClient:
    """
    Create a new OpenAI client with optional configuration.

    Args:
        config: Optional configuration dictionary

    Returns:
        Configured OpenAI client
    """
    if config:
        # Create config object from dictionary
        openai_config = OpenAIConfig()
        for key, value in config.items():
            if hasattr(openai_config, key):
                setattr(openai_config, key, value)
        return OpenAIUnifiedClient(openai_config)

    return OpenAIUnifiedClient()


def get_adapter_info() -> dict:
    """
    Get information about this adapter.

    Returns:
        Adapter information dictionary
    """
    return ADAPTER_INFO.copy()


def validate_environment() -> dict:
    """
    Validate that the environment is properly configured for OpenAI.

    Returns:
        Validation results dictionary
    """
    results = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'info': {}
    }

    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        results['valid'] = False
        results['errors'].append('OPENAI_API_KEY environment variable not set')
    elif not api_key.startswith('sk-'):
        results['valid'] = False
        results['errors'].append(
            'OPENAI_API_KEY does not appear to be valid (should start with sk-)'
        )
    else:
        results['info']['api_key_format'] = 'valid'

    # Check for optional settings
    org_id = os.getenv('OPENAI_ORGANIZATION_ID')
    if org_id:
        results['info']['organization_id'] = 'configured'

    project_id = os.getenv('OPENAI_PROJECT_ID')
    if project_id:
        results['info']['project_id'] = 'configured'

    # Check rate limit settings
    rate_limit = os.getenv('OPENAI_RATE_LIMIT_PER_MINUTE')
    if rate_limit:
        try:
            int(rate_limit)
            results['info']['rate_limit'] = 'configured'
        except ValueError:
            results['warnings'].append('OPENAI_RATE_LIMIT_PER_MINUTE is not a valid integer')

    return results


# Auto-register with shared registry if available
try:
    from shared.config.base_config import register_adapter_config
    from shared.registry.adapter_registry import register_adapter

    # Register configuration
    register_adapter_config('openai', OpenAIConfig)

    # Register adapter
    register_adapter('llm', 'openai', OpenAIClient)

except ImportError:
    # Registry not available, skip auto-registration
    pass
