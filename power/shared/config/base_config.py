"""
Base configuration system for adapter isolation and management.
"""

import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class AdapterConfig:  # pylint: disable=too-many-instance-attributes
    """Base configuration for all adapters."""

    adapter_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    rate_limit_per_minute: int = 60
    daily_quota: Optional[int] = None

    # Environment loading
    def __post_init__(self):
        """Load configuration from environment variables."""
        if not self.api_key:
            self.api_key = self._get_env_var('api_key')

        if not self.base_url:
            self.base_url = self._get_env_var('base_url')

        # Load other optional settings
        self.timeout = int(self._get_env_var('timeout', str(self.timeout)))
        self.max_retries = int(self._get_env_var('max_retries', str(self.max_retries)))
        self.rate_limit_per_minute = int(self._get_env_var(
            'rate_limit_per_minute',
            str(self.rate_limit_per_minute)
        ))

        daily_quota_env = self._get_env_var('daily_quota')
        if daily_quota_env:
            self.daily_quota = int(daily_quota_env)

    def _get_env_var(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get environment variable with adapter-specific naming convention."""
        env_key = f"{self.adapter_name.upper()}_{key.upper()}"
        return os.getenv(env_key, default)

    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []

        if not self.api_key:
            errors.append(f"API key required for {self.adapter_name}")

        if self.timeout <= 0:
            errors.append("timeout must be positive")

        if self.max_retries < 0:
            errors.append("max_retries cannot be negative")

        if self.rate_limit_per_minute <= 0:
            errors.append("rate_limit_per_minute must be positive")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary (excluding sensitive data)."""
        return {
            'adapter_name': self.adapter_name,
            'base_url': self.base_url,
            'timeout': self.timeout,
            'max_retries': self.max_retries,
            'rate_limit_per_minute': self.rate_limit_per_minute,
            'daily_quota': self.daily_quota,
            'has_api_key': bool(self.api_key)
        }


class BaseAdapterConfig:
    """Base class for adapter-specific configuration classes."""

    def __init__(self, adapter_name: str):
        self.adapter_name = adapter_name
        self._config = AdapterConfig(adapter_name)

    def get_required(self, key: str) -> str:
        """Get a required configuration value."""
        value = self._get_env_var(key)
        if not value:
            raise ValueError(f"Required configuration '{key}' not found for {self.adapter_name}")
        return value

    def get_optional(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get an optional configuration value."""
        return self._get_env_var(key, default)

    def get_int(self, key: str, default: int) -> int:
        """Get an integer configuration value."""
        value = self._get_env_var(key, str(default))
        try:
            return int(value)
        except ValueError as exc:
            raise ValueError(f"Configuration '{key}' must be an integer") from exc

    def get_float(self, key: str, default: float) -> float:
        """Get a float configuration value."""
        value = self._get_env_var(key, str(default))
        try:
            return float(value)
        except ValueError as exc:
            raise ValueError(f"Configuration '{key}' must be a float") from exc

    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get a boolean configuration value."""
        value = self._get_env_var(key, str(default).lower())
        return value.lower() in ('true', '1', 'yes', 'on')

    def _get_env_var(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get environment variable with adapter-specific naming convention."""
        env_key = f"{self.adapter_name.upper()}_{key.upper()}"
        return os.getenv(env_key, default)

    @property
    def api_key(self) -> str:
        """Get the API key for this adapter."""
        return self._config.api_key

    @property
    def base_url(self) -> Optional[str]:
        """Get the base URL for this adapter."""
        return self._config.base_url

    @property
    def timeout(self) -> int:
        """Get the timeout setting for this adapter."""
        return self._config.timeout

    @property
    def max_retries(self) -> int:
        """Get the max retries setting for this adapter."""
        return self._config.max_retries

    @property
    def rate_limit_per_minute(self) -> int:
        """Get the rate limit setting for this adapter."""
        return self._config.rate_limit_per_minute

    @property
    def daily_quota(self) -> Optional[int]:
        """Get the daily quota setting for this adapter."""
        return self._config.daily_quota

    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        return self._config.validate()

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary (excluding sensitive data)."""
        return self._config.to_dict()


class ConfigManager:
    """Central configuration manager for all adapters."""

    _instance = None
    _configs: Dict[str, BaseAdapterConfig] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register_adapter_config(self, adapter_name: str, config: BaseAdapterConfig):
        """Register a configuration for an adapter."""
        self._configs[adapter_name] = config

    def get_adapter_config(self, adapter_name: str) -> BaseAdapterConfig:
        """Get configuration for a specific adapter."""
        if adapter_name not in self._configs:
            # Create default configuration
            self._configs[adapter_name] = BaseAdapterConfig(adapter_name)

        return self._configs[adapter_name]

    def validate_all_configs(self) -> Dict[str, List[str]]:
        """Validate all registered configurations."""
        validation_results = {}

        for adapter_name, config in self._configs.items():
            errors = config.validate()
            if errors:
                validation_results[adapter_name] = errors

        return validation_results

    def list_adapters(self) -> List[str]:
        """List all registered adapter names."""
        return list(self._configs.keys())

    def get_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get all configurations as dictionaries (excluding sensitive data)."""
        return {
            adapter_name: config.to_dict()
            for adapter_name, config in self._configs.items()
        }


# Global configuration manager instance
config_manager = ConfigManager()


def get_adapter_config(adapter_name: str) -> BaseAdapterConfig:
    """Convenience function to get adapter configuration."""
    return config_manager.get_adapter_config(adapter_name)


def register_adapter_config(adapter_name: str, config: BaseAdapterConfig):
    """Convenience function to register adapter configuration."""
    config_manager.register_adapter_config(adapter_name, config)
