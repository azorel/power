"""
Claude Reasoning Configuration

Configuration management for Claude reasoning adapter following
API integration standards.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass

from shared.config.base_config import BaseAdapterConfig


@dataclass
class ClaudeReasoningConfig(BaseAdapterConfig):
    """Configuration for Claude reasoning adapter."""
    
    def __init__(self):
        """Initialize Claude reasoning configuration."""
        super().__init__('claude_reasoning')
        
        # Claude API settings
        self.api_key: str = self.get_required('api_key')
        self.base_url: str = self.get_optional('base_url', 'https://api.anthropic.com')
        self.model: str = self.get_optional('model', 'claude-3-sonnet-20240229')
        
        # Reasoning-specific settings
        self.rapid_model: str = self.get_optional('rapid_model', 'claude-3-haiku-20240307')
        self.thoughtful_model: str = self.get_optional('thoughtful_model', 'claude-3-opus-20240229')
        
        # Performance settings
        self.max_tokens: int = int(self.get_optional('max_tokens', '4096'))
        self.temperature: float = float(self.get_optional('temperature', '0.7'))
        self.timeout: float = float(self.get_optional('timeout', '30.0'))
        
        # Rate limiting
        self.rate_limit: int = int(self.get_optional('rate_limit', '50'))  # per minute
        self.daily_quota: int = int(self.get_optional('daily_quota', '10000'))
        
        # Reasoning parameters
        self.max_reasoning_steps: int = int(self.get_optional('max_reasoning_steps', '10'))
        self.step_timeout: float = float(self.get_optional('step_timeout', '5.0'))
        self.complexity_threshold: float = float(self.get_optional('complexity_threshold', '0.5'))
        
        # Cache settings
        self.cache_enabled: bool = self.get_optional('cache_enabled', 'true').lower() == 'true'
        self.cache_ttl: int = int(self.get_optional('cache_ttl', '3600'))  # 1 hour
        
        # Logging
        self.log_requests: bool = self.get_optional('log_requests', 'false').lower() == 'true'
        self.log_responses: bool = self.get_optional('log_responses', 'false').lower() == 'true'
    
    def get_model_for_mode(self, reasoning_mode: str) -> str:
        """
        Get the appropriate model for a reasoning mode.
        
        Args:
            reasoning_mode: The reasoning mode (rapid, thoughtful, etc.)
            
        Returns:
            str: The model to use for this mode
        """
        mode_models = {
            'rapid': self.rapid_model,
            'thoughtful': self.thoughtful_model,
            'chain_of_thought': self.thoughtful_model,
            'step_by_step': self.thoughtful_model,
            'adaptive': self.model
        }
        
        return mode_models.get(reasoning_mode, self.model)
    
    def get_temperature_for_mode(self, reasoning_mode: str) -> float:
        """
        Get the appropriate temperature for a reasoning mode.
        
        Args:
            reasoning_mode: The reasoning mode
            
        Returns:
            float: The temperature to use
        """
        mode_temperatures = {
            'rapid': 0.3,        # Lower temperature for quick, focused responses
            'thoughtful': 0.7,   # Balanced for detailed reasoning
            'chain_of_thought': 0.5,  # Structured thinking
            'step_by_step': 0.4,      # Methodical approach
            'adaptive': self.temperature
        }
        
        return mode_temperatures.get(reasoning_mode, self.temperature)
    
    def get_max_tokens_for_mode(self, reasoning_mode: str) -> int:
        """
        Get the appropriate token limit for a reasoning mode.
        
        Args:
            reasoning_mode: The reasoning mode
            
        Returns:
            int: The max tokens to use
        """
        mode_tokens = {
            'rapid': 1024,       # Shorter responses
            'thoughtful': 4096,  # Detailed responses
            'chain_of_thought': 6144,  # Extended reasoning
            'step_by_step': 8192,      # Comprehensive analysis
            'adaptive': self.max_tokens
        }
        
        return mode_tokens.get(reasoning_mode, self.max_tokens)
    
    def validate_config(self) -> Dict[str, Any]:
        """
        Validate the configuration and return validation results.
        
        Returns:
            Dict[str, Any]: Validation results
        """
        validation = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check required settings
        if not self.api_key:
            validation['errors'].append('API key is required')
            validation['is_valid'] = False
        
        # Check numeric ranges
        if not (0.0 <= self.temperature <= 2.0):
            validation['errors'].append('Temperature must be between 0.0 and 2.0')
            validation['is_valid'] = False
        
        if self.max_tokens <= 0:
            validation['errors'].append('Max tokens must be positive')
            validation['is_valid'] = False
        
        if self.rate_limit <= 0:
            validation['warnings'].append('Rate limit should be positive for production use')
        
        # Check reasoning parameters
        if not (0.0 <= self.complexity_threshold <= 1.0):
            validation['errors'].append('Complexity threshold must be between 0.0 and 1.0')
            validation['is_valid'] = False
        
        if self.max_reasoning_steps <= 0:
            validation['errors'].append('Max reasoning steps must be positive')
            validation['is_valid'] = False
        
        return validation
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'api_key': '***masked***',  # Don't expose API key
            'base_url': self.base_url,
            'model': self.model,
            'rapid_model': self.rapid_model,
            'thoughtful_model': self.thoughtful_model,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'timeout': self.timeout,
            'rate_limit': self.rate_limit,
            'daily_quota': self.daily_quota,
            'max_reasoning_steps': self.max_reasoning_steps,
            'step_timeout': self.step_timeout,
            'complexity_threshold': self.complexity_threshold,
            'cache_enabled': self.cache_enabled,
            'cache_ttl': self.cache_ttl,
            'log_requests': self.log_requests,
            'log_responses': self.log_responses
        }


def get_claude_reasoning_config() -> ClaudeReasoningConfig:
    """Get Claude reasoning configuration instance."""
    return ClaudeReasoningConfig()