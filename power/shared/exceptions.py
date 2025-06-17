"""
Shared exception hierarchy for Power Builder.
All adapters must translate their specific exceptions to these shared exceptions.
"""


class PowerBuilderError(Exception):
    """Base exception for all Power Builder errors."""

    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}

    def to_dict(self) -> dict:
        """Convert exception to dictionary format."""
        return {
            'error_type': self.__class__.__name__,
            'error_code': self.error_code,
            'message': self.message,
            'details': self.details
        }


# Adapter-related exceptions
class AdapterError(PowerBuilderError):
    """Base exception for adapter-related errors."""
    pass


class LLMProviderError(AdapterError):
    """Base exception for LLM provider errors."""
    pass


class AuthenticationError(LLMProviderError):
    """Raised when API credentials are invalid or missing."""
    pass


class RateLimitError(LLMProviderError):
    """Raised when API rate limits are exceeded."""

    def __init__(self, message: str, retry_after: int = None, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class QuotaExceededError(LLMProviderError):
    """Raised when API usage quotas are exceeded."""

    def __init__(self, message: str, quota_type: str = None, reset_time: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.quota_type = quota_type
        self.reset_time = reset_time


class ModelNotFoundError(LLMProviderError):
    """Raised when the requested model is not available."""

    def __init__(self, message: str, model_name: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.model_name = model_name


class InvalidRequestError(LLMProviderError):
    """Raised when the request format or parameters are invalid."""
    pass


class ContentFilterError(LLMProviderError):
    """Raised when content is filtered by safety policies."""

    def __init__(self, message: str, filter_reason: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.filter_reason = filter_reason


class TimeoutError(LLMProviderError):
    """Raised when API requests time out."""

    def __init__(self, message: str, timeout_seconds: int = None, **kwargs):
        super().__init__(message, **kwargs)
        self.timeout_seconds = timeout_seconds


class NetworkError(LLMProviderError):
    """Raised when network connectivity issues occur."""
    pass


# Configuration exceptions
class ConfigurationError(PowerBuilderError):
    """Base exception for configuration-related errors."""
    pass


class MissingConfigurationError(ConfigurationError):
    """Raised when required configuration is missing."""

    def __init__(self, message: str, config_key: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.config_key = config_key


class InvalidConfigurationError(ConfigurationError):
    """Raised when configuration values are invalid."""

    def __init__(self, message: str, config_key: str = None, config_value: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.config_key = config_key
        self.config_value = config_value


# Architecture violations
class ArchitectureViolationError(PowerBuilderError):
    """Raised when code violates the three-layer architecture."""

    def __init__(self, message: str, violation_type: str = None, file_path: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.violation_type = violation_type
        self.file_path = file_path


class LayerViolationError(ArchitectureViolationError):
    """Raised when code is placed in the wrong layer."""

    def __init__(self, message: str, expected_layer: str = None, actual_layer: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.expected_layer = expected_layer
        self.actual_layer = actual_layer


class CrossLayerImportError(ArchitectureViolationError):
    """Raised when code imports across forbidden layer boundaries."""

    def __init__(self, message: str, from_layer: str = None, to_layer: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.from_layer = from_layer
        self.to_layer = to_layer


# Data validation exceptions
class DataValidationError(PowerBuilderError):
    """Base exception for data validation errors."""
    pass


class InvalidModelError(DataValidationError):
    """Raised when data models fail validation."""

    def __init__(self, message: str, model_type: str = None, validation_errors: list = None, **kwargs):
        super().__init__(message, **kwargs)
        self.model_type = model_type
        self.validation_errors = validation_errors or []


class DataMappingError(DataValidationError):
    """Raised when data mapping between formats fails."""

    def __init__(self, message: str, source_format: str = None, target_format: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.source_format = source_format
        self.target_format = target_format


# Cache exceptions
class CacheError(PowerBuilderError):
    """Base exception for cache-related errors."""
    pass


class CacheMissError(CacheError):
    """Raised when requested data is not found in cache."""
    pass


class CacheCorruptionError(CacheError):
    """Raised when cached data is corrupted or invalid."""
    pass


# Registry exceptions
class RegistryError(PowerBuilderError):
    """Base exception for registry-related errors."""
    pass


class AdapterNotFoundError(RegistryError):
    """Raised when a requested adapter is not registered."""

    def __init__(self, message: str, adapter_name: str = None, adapter_type: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.adapter_name = adapter_name
        self.adapter_type = adapter_type


class AdapterRegistrationError(RegistryError):
    """Raised when adapter registration fails."""

    def __init__(self, message: str, adapter_name: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.adapter_name = adapter_name


# Utility functions for exception handling
def translate_exception(original_exception: Exception,
                       target_exception_class: type = None,
                       message: str = None,
                       **kwargs) -> PowerBuilderError:
    """
    Translate external exceptions to Power Builder exceptions.

    Args:
        original_exception: The original exception to translate
        target_exception_class: Target exception class (auto-detected if None)
        message: Custom message (uses original message if None)
        **kwargs: Additional parameters for the target exception

    Returns:
        Translated Power Builder exception
    """
    if isinstance(original_exception, PowerBuilderError):
        return original_exception

    original_message = str(original_exception)
    final_message = message or f"External error: {original_message}"

    # Auto-detect target exception class if not provided
    if target_exception_class is None:
        exception_name = original_exception.__class__.__name__.lower()

        if 'auth' in exception_name:
            target_exception_class = AuthenticationError
        elif 'rate' in exception_name or 'limit' in exception_name:
            target_exception_class = RateLimitError
        elif 'quota' in exception_name:
            target_exception_class = QuotaExceededError
        elif 'timeout' in exception_name:
            target_exception_class = TimeoutError
        elif 'network' in exception_name or 'connection' in exception_name:
            target_exception_class = NetworkError
        elif 'invalid' in exception_name:
            target_exception_class = InvalidRequestError
        else:
            target_exception_class = AdapterError

    # Create translated exception
    translated = target_exception_class(
        final_message,
        details={
            'original_exception': original_exception.__class__.__name__,
            'original_message': original_message,
            **kwargs
        }
    )

    # Preserve the original traceback
    translated.__cause__ = original_exception

    return translated


def is_retryable_error(exception: Exception) -> bool:
    """
    Determine if an exception is retryable.

    Args:
        exception: The exception to check

    Returns:
        True if the exception is retryable, False otherwise
    """
    retryable_types = (
        RateLimitError,
        TimeoutError,
        NetworkError
    )

    return isinstance(exception, retryable_types)


def get_retry_delay(exception: Exception) -> int:
    """
    Get the recommended retry delay for an exception.

    Args:
        exception: The exception to get retry delay for

    Returns:
        Recommended delay in seconds
    """
    if isinstance(exception, RateLimitError) and exception.retry_after:
        return exception.retry_after

    if isinstance(exception, TimeoutError):
        return 5  # 5 second delay for timeouts

    if isinstance(exception, NetworkError):
        return 3  # 3 second delay for network errors

    return 1  # Default 1 second delay
