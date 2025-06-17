"""
Exception handling and translation for Gemini API.
Maps Google Generative AI exceptions to shared Power Builder exceptions.
"""

from typing import Dict, Any, Optional, Type
import logging
from shared.exceptions import (
    LLMProviderError,
    AuthenticationError,
    RateLimitError,
    QuotaExceededError,
    ModelNotFoundError,
    InvalidRequestError,
    ContentFilterError,
    TimeoutError as LLMTimeoutError,
    NetworkError
)

logger = logging.getLogger(__name__)


class GeminiExceptionMapper:  # pylint: disable=too-few-public-methods
    """Maps Gemini API exceptions to shared Power Builder exceptions."""

    # Google API error codes to exception mapping
    ERROR_CODE_MAPPING: Dict[int, Type[LLMProviderError]] = {
        400: InvalidRequestError,
        401: AuthenticationError,
        403: QuotaExceededError,
        404: ModelNotFoundError,
        429: RateLimitError,
        500: LLMProviderError,
        502: NetworkError,
        503: LLMProviderError,
        504: LLMTimeoutError
    }

    # Google error message patterns
    ERROR_MESSAGE_PATTERNS: Dict[str, Type[LLMProviderError]] = {
        'invalid api key': AuthenticationError,
        'api key not valid': AuthenticationError,
        'authentication failed': AuthenticationError,
        'quota exceeded': QuotaExceededError,
        'rate limit': RateLimitError,
        'too many requests': RateLimitError,
        'model not found': ModelNotFoundError,
        'model not available': ModelNotFoundError,
        'content filtered': ContentFilterError,
        'safety filter': ContentFilterError,
        'blocked by safety': ContentFilterError,
        'timeout': LLMTimeoutError,
        'connection': NetworkError,
        'network': NetworkError,
        'invalid request': InvalidRequestError,
        'malformed request': InvalidRequestError,
        'invalid parameter': InvalidRequestError
    }

    @classmethod
    def translate_exception(
        cls,
        original_exception: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> LLMProviderError:
        """
        Translate a Gemini API exception to a shared exception.

        Args:
            original_exception: The original exception from Gemini API
            context: Additional context about the request

        Returns:
            Translated Power Builder exception
        """
        if isinstance(original_exception, LLMProviderError):
            return original_exception

        exception_name = original_exception.__class__.__name__.lower()
        error_message = str(original_exception).lower()
        context = context or {}

        # Log the original exception for debugging
        logger.debug(
            "Translating Gemini exception: %s - %s",
            exception_name, error_message,
            extra={'context': context}
        )

        # Try to extract status code from Google API exceptions
        status_code = cls._extract_status_code(original_exception)

        # Map by status code first
        if status_code and status_code in cls.ERROR_CODE_MAPPING:
            exception_class = cls.ERROR_CODE_MAPPING[status_code]
            return cls._create_exception(
                exception_class,
                original_exception,
                context,
                status_code=status_code
            )

        # Map by error message patterns
        for pattern, exception_class in cls.ERROR_MESSAGE_PATTERNS.items():
            if pattern in error_message:
                return cls._create_exception(
                    exception_class,
                    original_exception,
                    context,
                    matched_pattern=pattern
                )

        # Handle compound patterns for model errors
        if ('model' in error_message and
            ('not found' in error_message or 'not available' in error_message)):
            return cls._create_exception(
                ModelNotFoundError,
                original_exception,
                context,
                matched_pattern='model not found/available'
            )

        # Handle compound patterns for content filtering
        if ('content' in error_message and
            ('blocked' in error_message or 'filtered' in error_message)):
            return cls._create_exception(
                ContentFilterError,
                original_exception,
                context,
                matched_pattern='content blocked/filtered'
            )

        # Handle specific Google API exception types
        if 'googleapierror' in exception_name:
            return cls._handle_google_api_error(original_exception, context)

        if 'generativeaierror' in exception_name:
            return cls._handle_generative_ai_error(original_exception, context)

        # Handle common network/connection errors
        if any(term in exception_name for term in ['connection', 'timeout', 'network']):
            return cls._create_exception(
                NetworkError,
                original_exception,
                context
            )

        # Handle HTTP errors
        if 'http' in exception_name:
            return cls._handle_http_error(original_exception, context)

        # Default fallback
        return cls._create_exception(
            LLMProviderError,
            original_exception,
            context,
            fallback=True
        )

    @classmethod
    def _extract_status_code(cls, exception: Exception) -> Optional[int]:
        """Extract HTTP status code from exception."""
        # Try common attributes where status codes are stored
        for attr in ['status_code', 'code', 'status', 'response_code']:
            if hasattr(exception, attr):
                try:
                    return int(getattr(exception, attr))
                except (ValueError, TypeError):
                    continue

        # Try to extract from response object
        if hasattr(exception, 'response'):
            response = getattr(exception, 'response')
            if hasattr(response, 'status_code'):
                try:
                    return int(response.status_code)
                except (ValueError, TypeError):
                    pass

        return None

    @classmethod
    def _create_exception(
        cls,
        exception_class: Type[LLMProviderError],
        original_exception: Exception,
        context: Dict[str, Any],
        **extra_details
    ) -> LLMProviderError:
        """Create a translated exception with proper context."""
        original_message = str(original_exception)

        # Create appropriate message
        if exception_class == AuthenticationError:
            message = "Gemini API authentication failed. Please check your API key."
        elif exception_class == RateLimitError:
            retry_after = cls._extract_retry_after(original_exception)
            message = f"Gemini API rate limit exceeded. {original_message}"
            if retry_after:
                return RateLimitError(message, retry_after=retry_after)
        elif exception_class == QuotaExceededError:
            quota_type = cls._extract_quota_type(original_exception)
            reset_time = cls._extract_reset_time(original_exception)
            message = f"Gemini API quota exceeded. {original_message}"
            return QuotaExceededError(
                message,
                quota_type=quota_type,
                reset_time=reset_time
            )
        elif exception_class == ModelNotFoundError:
            model_name = context.get('model', 'unknown')
            message = f"Gemini model '{model_name}' not found or not available."
            # Add extra context details
            details = {
                'original_exception': original_exception.__class__.__name__,
                'original_message': original_message,
                'provider': 'gemini',
                **context,
                **extra_details
            }
            translated = ModelNotFoundError(message, model_name=model_name, details=details)
            translated.__cause__ = original_exception
            return translated
        elif exception_class == ContentFilterError:
            filter_reason = cls._extract_filter_reason(original_exception)
            message = f"Content filtered by Gemini safety policies. {original_message}"
            details = {
                'original_exception': original_exception.__class__.__name__,
                'original_message': original_message,
                'provider': 'gemini',
                **context,
                **extra_details
            }
            translated = ContentFilterError(message, filter_reason=filter_reason, details=details)
            translated.__cause__ = original_exception
            return translated
        elif exception_class == LLMTimeoutError:
            timeout_seconds = context.get('timeout', None)
            message = f"Gemini API request timed out. {original_message}"
            details = {
                'original_exception': original_exception.__class__.__name__,
                'original_message': original_message,
                'provider': 'gemini',
                **context,
                **extra_details
            }
            translated = LLMTimeoutError(
                message,
                timeout_seconds=timeout_seconds,
                details=details
            )
            translated.__cause__ = original_exception
            return translated
        else:
            message = f"Gemini API error: {original_message}"

        # Add extra context details
        details = {
            'original_exception': original_exception.__class__.__name__,
            'original_message': original_message,
            'provider': 'gemini',
            **context,
            **extra_details
        }

        translated = exception_class(message, details=details)

        # Preserve the original traceback
        translated.__cause__ = original_exception

        return translated

    @classmethod
    def _handle_google_api_error(
        cls,
        exception: Exception,
        context: Dict[str, Any]
    ) -> LLMProviderError:
        """Handle Google API specific errors."""
        # Google API errors often have detailed error info
        error_details = cls._extract_google_error_details(exception)

        if error_details:
            context.update(error_details)

            # Check for specific Google error reasons
            if 'reason' in error_details:
                reason = error_details['reason'].lower()

                if reason in ['quotaexceeded', 'rateLimitExceeded']:
                    return cls._create_exception(
                        QuotaExceededError,
                        exception,
                        context
                    )
                elif reason in ['invalidApiKey', 'authError']:
                    return cls._create_exception(
                        AuthenticationError,
                        exception,
                        context
                    )

        return cls._create_exception(LLMProviderError, exception, context)

    @classmethod
    def _handle_generative_ai_error(
        cls,
        exception: Exception,
        context: Dict[str, Any]
    ) -> LLMProviderError:
        """Handle Generative AI specific errors."""
        # Generative AI SDK specific error handling
        return cls._create_exception(LLMProviderError, exception, context)

    @classmethod
    def _handle_http_error(
        cls,
        exception: Exception,
        context: Dict[str, Any]
    ) -> LLMProviderError:
        """Handle HTTP errors."""
        status_code = cls._extract_status_code(exception)

        if status_code:
            if status_code in cls.ERROR_CODE_MAPPING:
                exception_class = cls.ERROR_CODE_MAPPING[status_code]
                return cls._create_exception(
                    exception_class,
                    exception,
                    context,
                    status_code=status_code
                )

        return cls._create_exception(NetworkError, exception, context)

    @classmethod
    def _extract_retry_after(cls, exception: Exception) -> Optional[int]:
        """Extract retry-after value from rate limit error."""
        # Check for retry-after header or attribute
        for attr in ['retry_after', 'retryAfter']:
            if hasattr(exception, attr):
                try:
                    return int(getattr(exception, attr))
                except (ValueError, TypeError):
                    continue

        # Check response headers
        if hasattr(exception, 'response') and hasattr(exception.response, 'headers'):
            headers = exception.response.headers
            if 'retry-after' in headers:
                try:
                    return int(headers['retry-after'])
                except (ValueError, TypeError):
                    pass

        return None

    @classmethod
    def _extract_quota_type(cls, exception: Exception) -> Optional[str]:
        """Extract quota type from quota exceeded error."""
        error_message = str(exception).lower()

        if 'daily' in error_message:
            return 'daily'
        elif 'monthly' in error_message:
            return 'monthly'
        elif 'minute' in error_message:
            return 'per_minute'
        elif 'hour' in error_message:
            return 'per_hour'

        return 'unknown'

    @classmethod
    def _extract_reset_time(cls, exception: Exception) -> Optional[str]:
        """Extract quota reset time from error."""
        # This would need to be implemented based on actual Gemini error format
        return None

    @classmethod
    def _extract_filter_reason(cls, exception: Exception) -> Optional[str]:
        """Extract content filter reason from error."""
        error_message = str(exception).lower()

        if 'harassment' in error_message:
            return 'harassment'
        elif 'hate' in error_message:
            return 'hate_speech'
        elif 'sexual' in error_message:
            return 'sexual_content'
        elif 'dangerous' in error_message:
            return 'dangerous_content'
        elif 'violence' in error_message:
            return 'violence'

        return 'safety_filter'

    @classmethod
    def _extract_google_error_details(cls, exception: Exception) -> Optional[Dict[str, Any]]:
        """Extract detailed error information from Google API exception."""
        details = {}

        # Try to get error details from common attributes
        for attr in ['error', 'details', 'error_details']:
            if hasattr(exception, attr):
                error_info = getattr(exception, attr)
                if isinstance(error_info, dict):
                    details.update(error_info)
                elif hasattr(error_info, '__dict__'):
                    details.update(error_info.__dict__)

        return details if details else None


def handle_gemini_exception(
    exception: Exception,
    context: Optional[Dict[str, Any]] = None
) -> LLMProviderError:
    """
    Convenience function to handle and translate Gemini exceptions.

    Args:
        exception: Original exception from Gemini API
        context: Additional context about the request

    Returns:
        Translated Power Builder exception
    """
    return GeminiExceptionMapper.translate_exception(exception, context)


def wrap_gemini_call(func):
    """
    Decorator to automatically handle and translate Gemini API exceptions.

    Args:
        func: Function that makes Gemini API calls

    Returns:
        Wrapped function with exception translation
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Create context from function arguments if possible
            context = {
                'function': func.__name__,
                'args_count': len(args),
                'kwargs': list(kwargs.keys())
            }

            # Try to extract useful context from arguments
            if args and hasattr(args[0], '__class__'):
                context['instance_class'] = args[0].__class__.__name__

            raise handle_gemini_exception(e, context)

    return wrapper
