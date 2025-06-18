"""
Claude API configuration module.
Handles Claude Sonnet 4 & Opus 4 configuration with hybrid reasoning capabilities.
"""

from typing import List, Dict, Any
from shared.config.base_config import BaseAdapterConfig


class ClaudeConfig(BaseAdapterConfig):  # pylint: disable=too-many-instance-attributes
    """Configuration for Claude API adapter with Sonnet 4/Opus 4 capabilities."""

    def __init__(self):
        super().__init__('claude')

        # Claude-specific configuration
        self.organization_id = self.get_optional('organization_id')
        self.workspace_id = self.get_optional('workspace_id')

        # Enhanced rate limiting for Sonnet 4/Opus 4
        self.rate_limit_per_day = self.get_int('rate_limit_per_day', 50000)
        self.rate_limit_per_hour = self.get_int('rate_limit_per_hour', 2000)

        # Request configuration
        self.retry_delay = self.get_float('retry_delay', 2.0)
        self.max_retries_per_request = self.get_int('max_retries_per_request', 3)

        # Model configuration - Enhanced for Sonnet 4/Opus 4
        self.default_model = self.get_optional('default_model', 'claude-sonnet-4-latest')
        self.default_max_tokens = self.get_int('default_max_tokens', 65536)  # 64K tokens
        self.default_temperature = self.get_float('default_temperature', 0.7)
        self.default_top_p = self.get_float('default_top_p', 0.95)
        self.default_top_k = self.get_int('default_top_k', 40)

        # Hybrid reasoning configuration
        self.enable_hybrid_reasoning = self.get_bool('enable_hybrid_reasoning', True)
        # analytical, creative, balanced
        self.reasoning_mode = self.get_optional('reasoning_mode', 'balanced')
        self.reasoning_depth = self.get_int('reasoning_depth', 3)  # 1-5 levels
        self.enable_step_by_step = self.get_bool('enable_step_by_step', True)

        # Enhanced capabilities
        self.enable_function_calling = self.get_bool('enable_function_calling', True)
        self.enable_tool_use = self.get_bool('enable_tool_use', True)
        self.enable_vision = self.get_bool('enable_vision', True)
        self.enable_document_analysis = self.get_bool('enable_document_analysis', True)
        self.enable_code_analysis = self.get_bool('enable_code_analysis', True)

        # Context management for 64K tokens
        self.max_context_tokens = self.get_int('max_context_tokens', 65536)
        self.context_window_management = self.get_optional(
            'context_window_management', 'sliding')
        self.context_preservation_ratio = self.get_float('context_preservation_ratio', 0.85)

        # Safety and moderation
        self.enable_content_filter = self.get_bool('enable_content_filter', True)
        self.safety_level = self.get_optional('safety_level', 'standard')  # low, standard, high
        self.enable_ethical_guidelines = self.get_bool('enable_ethical_guidelines', True)

        # Caching configuration
        self.enable_response_cache = self.get_bool('enable_response_cache', True)
        self.cache_ttl_seconds = self.get_int('cache_ttl_seconds', 7200)  # 2 hours
        self.max_cache_size = self.get_int('max_cache_size', 2000)

        # Performance optimization
        self.enable_streaming = self.get_bool('enable_streaming', True)
        self.chunk_size = self.get_int('chunk_size', 1024)
        self.enable_parallel_processing = self.get_bool('enable_parallel_processing', True)

    def get_model_config(self, model_name: str) -> Dict[str, Any]:
        """Get configuration for a specific Claude model."""
        model_configs = {
            'claude-sonnet-4-latest': {
                'max_tokens': 65536,
                'knowledge_cutoff': '2025-03-01',
                'supports_vision': True,
                'supports_functions': True,
                'supports_tool_use': True,
                'supports_hybrid_reasoning': True,
                'reasoning_capabilities': ['analytical', 'creative', 'logical', 'intuitive'],
                'cost_per_1k_input_tokens': 0.003,
                'cost_per_1k_output_tokens': 0.015,
                'api_version': 'v1',
                'model_type': 'sonnet-4'
            },
            'claude-opus-4-latest': {
                'max_tokens': 65536,
                'knowledge_cutoff': '2025-03-01',
                'supports_vision': True,
                'supports_functions': True,
                'supports_tool_use': True,
                'supports_hybrid_reasoning': True,
                'reasoning_capabilities': [
                    'analytical', 'creative', 'logical', 'intuitive', 'philosophical'],
                'cost_per_1k_input_tokens': 0.015,
                'cost_per_1k_output_tokens': 0.075,
                'api_version': 'v1',
                'model_type': 'opus-4'
            },
            'claude-sonnet-3.5-latest': {
                'max_tokens': 32768,
                'knowledge_cutoff': '2024-04-01',
                'supports_vision': True,
                'supports_functions': True,
                'supports_tool_use': True,
                'supports_hybrid_reasoning': False,
                'reasoning_capabilities': ['analytical', 'creative'],
                'cost_per_1k_input_tokens': 0.003,
                'cost_per_1k_output_tokens': 0.015,
                'api_version': 'v1',
                'model_type': 'sonnet-3.5'
            },
            'claude-haiku-3.5-latest': {
                'max_tokens': 32768,
                'knowledge_cutoff': '2024-04-01',
                'supports_vision': True,
                'supports_functions': True,
                'supports_tool_use': True,
                'supports_hybrid_reasoning': False,
                'reasoning_capabilities': ['analytical'],
                'cost_per_1k_input_tokens': 0.0008,
                'cost_per_1k_output_tokens': 0.004,
                'api_version': 'v1',
                'model_type': 'haiku-3.5'
            }
        }

        return model_configs.get(model_name, {})

    def get_supported_models(self) -> List[str]:
        """Get list of supported Claude models."""
        return [
            'claude-sonnet-4-latest',
            'claude-opus-4-latest',
            'claude-sonnet-3.5-latest',
            'claude-haiku-3.5-latest'
        ]

    def get_hybrid_reasoning_config(self) -> Dict[str, Any]:
        """Get hybrid reasoning configuration."""
        return {
            'enabled': self.enable_hybrid_reasoning,
            'mode': self.reasoning_mode,
            'depth': self.reasoning_depth,
            'step_by_step': self.enable_step_by_step,
            'capabilities': {
                'analytical': True,
                'creative': True,
                'logical': True,
                'intuitive': self.reasoning_mode in ['balanced', 'creative'],
                'philosophical': self.reasoning_mode == 'creative'
            },
            'parameters': {
                'temperature': self.default_temperature,
                'top_p': self.default_top_p,
                'top_k': self.default_top_k
            }
        }

    def validate(self) -> List[str]:  # pylint: disable=too-many-branches
        """Validate Claude-specific configuration."""
        errors = super().validate()

        # API key validation
        if not self.api_key or not str(self.api_key).startswith('sk-ant-'):
            errors.append("Claude API key must start with 'sk-ant-'")

        # Rate limiting validation
        if self.rate_limit_per_minute <= 0:
            errors.append("rate_limit_per_minute must be positive")
        if self.rate_limit_per_hour <= 0:
            errors.append("rate_limit_per_hour must be positive")
        if self.rate_limit_per_day <= 0:
            errors.append("rate_limit_per_day must be positive")

        # Token validation
        if self.default_max_tokens <= 0:
            errors.append("default_max_tokens must be positive")
        if self.default_max_tokens > 65536:
            errors.append("default_max_tokens cannot exceed 65536 (64K limit)")
        if self.max_context_tokens > 65536:
            errors.append("max_context_tokens cannot exceed 65536 (64K limit)")

        # Temperature validation
        if not 0.0 <= self.default_temperature <= 1.0:
            errors.append("default_temperature must be between 0.0 and 1.0")

        # Top-p validation
        if not 0.0 <= self.default_top_p <= 1.0:
            errors.append("default_top_p must be between 0.0 and 1.0")

        # Top-k validation
        if self.default_top_k <= 0:
            errors.append("default_top_k must be positive")

        # Reasoning configuration validation
        if self.reasoning_mode not in ['analytical', 'creative', 'balanced']:
            errors.append("reasoning_mode must be 'analytical', 'creative', or 'balanced'")
        if not 1 <= self.reasoning_depth <= 5:
            errors.append("reasoning_depth must be between 1 and 5")

        # Context validation
        if not 0.0 <= self.context_preservation_ratio <= 1.0:
            errors.append("context_preservation_ratio must be between 0.0 and 1.0")

        # Safety validation
        if self.safety_level not in ['low', 'standard', 'high']:
            errors.append("safety_level must be 'low', 'standard', or 'high'")

        # Retry validation
        if self.retry_delay < 0:
            errors.append("retry_delay cannot be negative")
        if self.max_retries_per_request < 0:
            errors.append("max_retries_per_request cannot be negative")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary (excluding sensitive data)."""
        base_dict = super().to_dict()
        base_dict.update({
            'organization_id': self.organization_id,
            'workspace_id': self.workspace_id,
            'rate_limit_per_hour': self.rate_limit_per_hour,
            'rate_limit_per_day': self.rate_limit_per_day,
            'retry_delay': self.retry_delay,
            'max_retries_per_request': self.max_retries_per_request,
            'default_model': self.default_model,
            'default_max_tokens': self.default_max_tokens,
            'default_temperature': self.default_temperature,
            'default_top_p': self.default_top_p,
            'default_top_k': self.default_top_k,
            'hybrid_reasoning_config': self.get_hybrid_reasoning_config(),
            'enable_function_calling': self.enable_function_calling,
            'enable_tool_use': self.enable_tool_use,
            'enable_vision': self.enable_vision,
            'enable_document_analysis': self.enable_document_analysis,
            'enable_code_analysis': self.enable_code_analysis,
            'max_context_tokens': self.max_context_tokens,
            'context_window_management': self.context_window_management,
            'context_preservation_ratio': self.context_preservation_ratio,
            'safety_level': self.safety_level,
            'enable_content_filter': self.enable_content_filter,
            'enable_ethical_guidelines': self.enable_ethical_guidelines,
            'enable_response_cache': self.enable_response_cache,
            'cache_ttl_seconds': self.cache_ttl_seconds,
            'max_cache_size': self.max_cache_size,
            'enable_streaming': self.enable_streaming,
            'chunk_size': self.chunk_size,
            'enable_parallel_processing': self.enable_parallel_processing,
            'supported_models': self.get_supported_models()
        })
        return base_dict
