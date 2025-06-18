"""
Claude API exceptions module.
Custom exceptions for Claude API integration errors.
"""

from typing import Optional, Any, Dict


class ClaudeAPIError(Exception):
    """Base exception for Claude API errors."""
    
    def __init__(
        self, 
        message: str, 
        status_code: Optional[int] = None,
        error_type: Optional[str] = None,
        response_data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        self.response_data = response_data or {}

    def __str__(self) -> str:
        if self.status_code:
            return f"Claude API Error ({self.status_code}): {self.message}"
        return f"Claude API Error: {self.message}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging."""
        return {
            'error_class': self.__class__.__name__,
            'message': self.message,
            'status_code': self.status_code,
            'error_type': self.error_type,
            'response_data': self.response_data
        }


class ClaudeAuthenticationError(ClaudeAPIError):
    """Authentication failed with Claude API."""
    
    def __init__(self, message: str = "Invalid API key or authentication failed"):
        super().__init__(message, status_code=401, error_type="authentication_error")


class ClaudeRateLimitError(ClaudeAPIError):
    """Rate limit exceeded for Claude API."""
    
    def __init__(
        self, 
        message: str = "Rate limit exceeded", 
        retry_after: Optional[int] = None,
        limit_type: Optional[str] = None
    ):
        super().__init__(message, status_code=429, error_type="rate_limit_error")
        self.retry_after = retry_after
        self.limit_type = limit_type

    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.retry_after:
            base_msg += f" (retry after {self.retry_after} seconds)"
        if self.limit_type:
            base_msg += f" [Limit type: {self.limit_type}]"
        return base_msg


class ClaudeConnectionError(ClaudeAPIError):
    """Connection error when communicating with Claude API."""
    
    def __init__(self, message: str = "Failed to connect to Claude API"):
        super().__init__(message, error_type="connection_error")


class ClaudeTimeoutError(ClaudeAPIError):
    """Request timeout when communicating with Claude API."""
    
    def __init__(self, message: str = "Request timed out", timeout_duration: Optional[float] = None):
        super().__init__(message, error_type="timeout_error")
        self.timeout_duration = timeout_duration

    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.timeout_duration:
            base_msg += f" (timeout: {self.timeout_duration}s)"
        return base_msg


class ClaudeValidationError(ClaudeAPIError):
    """Request validation error for Claude API."""
    
    def __init__(self, message: str, validation_errors: Optional[list] = None):
        super().__init__(message, status_code=400, error_type="validation_error")
        self.validation_errors = validation_errors or []

    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.validation_errors:
            base_msg += f" Validation errors: {', '.join(self.validation_errors)}"
        return base_msg


class ClaudeContextLimitError(ClaudeAPIError):
    """Context limit exceeded for Claude API."""
    
    def __init__(
        self, 
        message: str = "Context limit exceeded", 
        current_tokens: Optional[int] = None,
        max_tokens: Optional[int] = None
    ):
        super().__init__(message, status_code=400, error_type="context_limit_error")
        self.current_tokens = current_tokens
        self.max_tokens = max_tokens

    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.current_tokens and self.max_tokens:
            base_msg += f" ({self.current_tokens}/{self.max_tokens} tokens)"
        return base_msg


class ClaudeModelNotFoundError(ClaudeAPIError):
    """Requested model not found or not available."""
    
    def __init__(self, model_name: str):
        message = f"Model '{model_name}' not found or not available"
        super().__init__(message, status_code=404, error_type="model_not_found")
        self.model_name = model_name


class ClaudeHybridReasoningError(ClaudeAPIError):
    """Error in hybrid reasoning configuration or execution."""
    
    def __init__(self, message: str, reasoning_mode: Optional[str] = None):
        super().__init__(message, error_type="hybrid_reasoning_error")
        self.reasoning_mode = reasoning_mode

    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.reasoning_mode:
            base_msg += f" [Reasoning mode: {self.reasoning_mode}]"
        return base_msg


class ClaudeToolUseError(ClaudeAPIError):
    """Error in tool use or function calling."""
    
    def __init__(self, message: str, tool_name: Optional[str] = None, tool_error: Optional[str] = None):
        super().__init__(message, error_type="tool_use_error")
        self.tool_name = tool_name
        self.tool_error = tool_error

    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.tool_name:
            base_msg += f" [Tool: {self.tool_name}]"
        if self.tool_error:
            base_msg += f" [Tool error: {self.tool_error}]"
        return base_msg


class ClaudeContentFilterError(ClaudeAPIError):
    """Content filtered by Claude's safety systems."""
    
    def __init__(self, message: str = "Content filtered by safety systems", filter_reason: Optional[str] = None):
        super().__init__(message, status_code=400, error_type="content_filter_error")
        self.filter_reason = filter_reason

    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.filter_reason:
            base_msg += f" [Reason: {self.filter_reason}]"
        return base_msg


def handle_claude_api_error(error: Exception, context: Optional[str] = None) -> ClaudeAPIError:
    """
    Convert various exception types to appropriate ClaudeAPIError subclasses.
    
    Args:
        error: The original exception
        context: Optional context information
        
    Returns:
        Appropriate ClaudeAPIError subclass
    """
    error_msg = str(error)
    if context:
        error_msg = f"{context}: {error_msg}"
    
    # Check for specific error patterns
    if "authentication" in error_msg.lower() or "unauthorized" in error_msg.lower():
        return ClaudeAuthenticationError(error_msg)
    elif "rate limit" in error_msg.lower() or "too many requests" in error_msg.lower():
        return ClaudeRateLimitError(error_msg)
    elif "timeout" in error_msg.lower():
        return ClaudeTimeoutError(error_msg)
    elif "connection" in error_msg.lower() or "network" in error_msg.lower():
        return ClaudeConnectionError(error_msg)
    elif "validation" in error_msg.lower() or "invalid" in error_msg.lower():
        return ClaudeValidationError(error_msg)
    elif "context" in error_msg.lower() and "limit" in error_msg.lower():
        return ClaudeContextLimitError(error_msg)
    elif "model" in error_msg.lower() and "not found" in error_msg.lower():
        return ClaudeModelNotFoundError("unknown")
    elif "content filter" in error_msg.lower() or "filtered" in error_msg.lower():
        return ClaudeContentFilterError(error_msg)
    else:
        return ClaudeAPIError(error_msg)