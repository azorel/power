"""
OpenAI API exception handling and translation.
Translates OpenAI-specific exceptions to shared exception hierarchy.
"""

import openai
from typing import Optional, Dict, Any
from shared.exceptions import (
    LLMProviderError,
    AuthenticationError,
    RateLimitError,
    QuotaExceededError,
    ModelNotFoundError,
    InvalidRequestError,
    ContentFilterError,
    TimeoutError,
    NetworkError,
    translate_exception
)


class OpenAIExceptionMapper:
    """Maps OpenAI exceptions to shared exception hierarchy."""

    @staticmethod
    def translate_openai_exception(openai_error: Exception) -> LLMProviderError:
        """
        Translate OpenAI exceptions to shared exceptions.
        
        Args:
            openai_error: The original OpenAI exception
            
        Returns:
            Translated shared exception
        """
        error_message = str(openai_error)
        error_details = {}
        
        # Extract error details if available
        if hasattr(openai_error, 'response') and openai_error.response:
            error_details['status_code'] = getattr(openai_error.response, 'status_code', None)
            error_details['headers'] = dict(getattr(openai_error.response, 'headers', {}))
        
        if hasattr(openai_error, 'body'):
            error_details['response_body'] = openai_error.body
        
        # Authentication errors
        if isinstance(openai_error, openai.AuthenticationError):
            return AuthenticationError(
                f"OpenAI authentication failed: {error_message}",
                details=error_details
            )
        
        # Rate limiting errors
        if isinstance(openai_error, openai.RateLimitError):
            retry_after = None
            if hasattr(openai_error, 'response') and openai_error.response:
                retry_after = openai_error.response.headers.get('retry-after')
                if retry_after:
                    try:
                        retry_after = int(retry_after)
                    except ValueError:
                        retry_after = None
            
            return RateLimitError(
                f"OpenAI rate limit exceeded: {error_message}",
                retry_after=retry_after,
                details=error_details
            )
        
        # Permission/quota errors  
        if isinstance(openai_error, openai.PermissionDeniedError):
            # Check if it's a quota issue
            if 'quota' in error_message.lower() or 'billing' in error_message.lower():
                return QuotaExceededError(
                    f"OpenAI quota exceeded: {error_message}",
                    quota_type='billing',
                    details=error_details
                )
            return AuthenticationError(
                f"OpenAI permission denied: {error_message}",
                details=error_details
            )
        
        # Model not found errors
        if isinstance(openai_error, openai.NotFoundError):
            # Check if it's a model not found error
            if 'model' in error_message.lower():
                model_name = OpenAIExceptionMapper._extract_model_name(error_message)
                return ModelNotFoundError(
                    f"OpenAI model not found: {error_message}",
                    model_name=model_name,
                    details=error_details
                )
            return LLMProviderError(
                f"OpenAI resource not found: {error_message}",
                details=error_details
            )
        
        # Bad request errors
        if isinstance(openai_error, openai.BadRequestError):
            # Check for content filter
            if 'content_policy' in error_message.lower() or 'safety' in error_message.lower():
                filter_reason = OpenAIExceptionMapper._extract_filter_reason(error_message)
                return ContentFilterError(
                    f"OpenAI content filtered: {error_message}",
                    filter_reason=filter_reason,
                    details=error_details
                )
            
            return InvalidRequestError(
                f"OpenAI bad request: {error_message}",
                details=error_details
            )
        
        # Timeout errors
        if isinstance(openai_error, (openai.APITimeoutError, openai.Timeout)):
            timeout_seconds = None
            if hasattr(openai_error, 'timeout'):
                timeout_seconds = openai_error.timeout
            
            return TimeoutError(
                f"OpenAI request timeout: {error_message}",
                timeout_seconds=timeout_seconds,
                details=error_details
            )
        
        # Connection errors
        if isinstance(openai_error, openai.APIConnectionError):
            return NetworkError(
                f"OpenAI connection error: {error_message}",
                details=error_details
            )
        
        # Generic API errors
        if isinstance(openai_error, openai.APIError):
            return LLMProviderError(
                f"OpenAI API error: {error_message}",
                details=error_details
            )
        
        # Internal server errors
        if isinstance(openai_error, openai.InternalServerError):
            return LLMProviderError(
                f"OpenAI internal server error: {error_message}",
                details=error_details
            )
        
        # Unhandled exceptions
        if isinstance(openai_error, openai.OpenAIError):
            return LLMProviderError(
                f"OpenAI error: {error_message}",
                details=error_details
            )
        
        # Fall back to generic translation
        return translate_exception(
            openai_error,
            LLMProviderError,
            f"OpenAI adapter error: {error_message}"
        )

    @staticmethod
    def _extract_model_name(error_message: str) -> Optional[str]:
        """Extract model name from error message."""
        # Common patterns in OpenAI error messages
        patterns = [
            "model '",
            'model "',
            "model: ",
            "The model `",
        ]
        
        for pattern in patterns:
            if pattern in error_message:
                start = error_message.find(pattern) + len(pattern)
                end = error_message.find("'", start)
                if end == -1:
                    end = error_message.find('"', start)
                if end == -1:
                    end = error_message.find('`', start)
                if end == -1:
                    end = error_message.find(' ', start)
                if end > start:
                    return error_message[start:end]
        
        return None

    @staticmethod
    def _extract_filter_reason(error_message: str) -> Optional[str]:
        """Extract content filter reason from error message."""
        # Look for common filter reasons
        filter_reasons = [
            'violence',
            'harassment',
            'hate',
            'self-harm',
            'sexual',
            'dangerous',
            'inappropriate'
        ]
        
        error_lower = error_message.lower()
        for reason in filter_reasons:
            if reason in error_lower:
                return reason
        
        return 'content_policy_violation'

    @staticmethod
    def handle_openai_error(func):
        """
        Decorator to automatically translate OpenAI exceptions.
        
        Usage:
            @OpenAIExceptionMapper.handle_openai_error
            def api_method(self):
                # OpenAI API call
                pass
        """
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if isinstance(e, (openai.OpenAIError, openai.APIError)):
                    raise OpenAIExceptionMapper.translate_openai_exception(e)
                raise
        
        return wrapper


def create_error_context(
    operation: str,
    model: Optional[str] = None,
    request_id: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create error context dictionary for better error tracking.
    
    Args:
        operation: The operation being performed
        model: Model being used
        request_id: Request identifier
        **kwargs: Additional context
        
    Returns:
        Dictionary with error context
    """
    context = {
        'operation': operation,
        'adapter': 'openai',
        **kwargs
    }
    
    if model:
        context['model'] = model
    
    if request_id:
        context['request_id'] = request_id
    
    return context


def is_retriable_openai_error(error: Exception) -> bool:
    """
    Determine if an OpenAI error is retriable.
    
    Args:
        error: The exception to check
        
    Returns:
        True if the error is retriable
    """
    # Rate limit errors are retriable
    if isinstance(error, (openai.RateLimitError, RateLimitError)):
        return True
    
    # Timeout errors are retriable
    if isinstance(error, (openai.APITimeoutError, openai.Timeout, TimeoutError)):
        return True
    
    # Connection errors are retriable
    if isinstance(error, (openai.APIConnectionError, NetworkError)):
        return True
    
    # Internal server errors are retriable
    if isinstance(error, openai.InternalServerError):
        return True
    
    # Temporary service unavailable
    if isinstance(error, openai.APIError):
        if hasattr(error, 'response') and error.response:
            status_code = getattr(error.response, 'status_code', None)
            if status_code in [502, 503, 504]:  # Bad Gateway, Service Unavailable, Gateway Timeout
                return True
    
    return False


def get_retry_delay_for_openai_error(error: Exception) -> float:
    """
    Get appropriate retry delay for OpenAI error.
    
    Args:
        error: The exception to get delay for
        
    Returns:
        Delay in seconds
    """
    # Rate limit errors may have retry-after header
    if isinstance(error, (openai.RateLimitError, RateLimitError)):
        if hasattr(error, 'retry_after') and error.retry_after:
            return float(error.retry_after)
        return 60.0  # Default 1 minute for rate limits
    
    # Timeout errors - short delay
    if isinstance(error, (openai.APITimeoutError, openai.Timeout, TimeoutError)):
        return 5.0
    
    # Connection errors - medium delay
    if isinstance(error, (openai.APIConnectionError, NetworkError)):
        return 10.0
    
    # Server errors - longer delay
    if isinstance(error, openai.InternalServerError):
        return 30.0
    
    # Default delay
    return 1.0