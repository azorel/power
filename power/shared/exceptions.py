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


class ProviderError(AdapterError):
    """Base exception for provider-related errors."""


class LLMProviderError(AdapterError):
    """Base exception for LLM provider errors."""


class AuthenticationError(LLMProviderError):
    """Raised when API credentials are invalid or missing."""


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


class MemoryProviderError(AdapterError):
    """Base exception for memory provider errors."""


class ModelNotFoundError(LLMProviderError):
    """Raised when the requested model is not available."""

    def __init__(self, message: str, model_name: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.model_name = model_name


class InvalidRequestError(LLMProviderError):
    """Raised when the request format or parameters are invalid."""


class ContentFilterError(LLMProviderError):
    """Raised when content is filtered by safety policies."""

    def __init__(self, message: str, filter_reason: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.filter_reason = filter_reason


class RequestTimeoutError(LLMProviderError):
    """Raised when API requests time out."""

    def __init__(self, message: str, timeout_seconds: int = None, **kwargs):
        super().__init__(message, **kwargs)
        self.timeout_seconds = timeout_seconds


class NetworkError(LLMProviderError):
    """Raised when network connectivity issues occur."""


# Social Media Provider exceptions
class SocialMediaProviderError(AdapterError):
    """Base exception for social media provider errors."""


class ContentViolationError(SocialMediaProviderError):
    """Raised when content violates platform policies."""

    def __init__(self, message: str, violation_type: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.violation_type = violation_type


class MediaUploadError(SocialMediaProviderError):
    """Raised when media upload fails."""

    def __init__(self, message: str, media_type: str = None, file_size: int = None, **kwargs):
        super().__init__(message, **kwargs)
        self.media_type = media_type
        self.file_size = file_size


class PostNotFoundError(SocialMediaProviderError):
    """Raised when a requested post is not found."""

    def __init__(self, message: str, post_id: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.post_id = post_id


class UserNotFoundError(SocialMediaProviderError):
    """Raised when a requested user is not found."""

    def __init__(self, message: str, user_id: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.user_id = user_id


class SchedulingError(SocialMediaProviderError):
    """Raised when post scheduling fails."""

    def __init__(self, message: str, scheduled_time: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.scheduled_time = scheduled_time


class PermissionError(SocialMediaProviderError):
    """Raised when user lacks required permissions."""

    def __init__(self, message: str, required_permission: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.required_permission = required_permission


# Configuration exceptions
class ConfigurationError(PowerBuilderError):
    """Base exception for configuration-related errors."""


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

    def __init__(self, message: str, expected_layer: str = None,
                 actual_layer: str = None, **kwargs):
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
class ValidationError(PowerBuilderError):
    """Raised when validation fails."""


class DataValidationError(PowerBuilderError):
    """Base exception for data validation errors."""


class DatabaseError(PowerBuilderError):
    """Base exception for database-related errors."""


class WebSocketError(PowerBuilderError):
    """Base exception for WebSocket-related errors."""


class DataRetrievalError(PowerBuilderError):
    """Raised when data retrieval fails."""


# Automation exceptions
class AutomationError(PowerBuilderError):
    """Base exception for automation-related errors."""


class WorkflowExecutionError(AutomationError):
    """Raised when workflow execution fails."""

    def __init__(self, message: str, workflow_id: str = None, execution_id: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.workflow_id = workflow_id
        self.execution_id = execution_id


class DecisionEngineError(AutomationError):
    """Raised when decision engine fails."""

    def __init__(self, message: str, decision_type: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.decision_type = decision_type


class RuleEvaluationError(AutomationError):
    """Raised when rule evaluation fails."""

    def __init__(self, message: str, rule_id: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.rule_id = rule_id


class TriggerError(AutomationError):
    """Raised when trigger processing fails."""

    def __init__(self, message: str, trigger_id: str = None, trigger_type: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.trigger_id = trigger_id
        self.trigger_type = trigger_type


class ActionExecutionError(AutomationError):
    """Raised when action execution fails."""

    def __init__(self, message: str, action_id: str = None, action_type: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.action_id = action_id
        self.action_type = action_type


class LifeOptimizationError(AutomationError):
    """Raised when life optimization fails."""

    def __init__(self, message: str, optimization_type: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.optimization_type = optimization_type


class InvalidModelError(DataValidationError):
    """Raised when data models fail validation."""

    def __init__(self, message: str, model_type: str = None,
                 validation_errors: list = None, **kwargs):
        super().__init__(message, **kwargs)
        self.model_type = model_type
        self.validation_errors = validation_errors or []


class DataMappingError(DataValidationError):
    """Raised when data mapping between formats fails."""

    def __init__(self, message: str, source_format: str = None,
                 target_format: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.source_format = source_format
        self.target_format = target_format


# Cache exceptions
class CacheError(PowerBuilderError):
    """Base exception for cache-related errors."""


class CacheMissError(CacheError):
    """Raised when requested data is not found in cache."""


class CacheCorruptionError(CacheError):
    """Raised when cached data is corrupted or invalid."""


# Workspace exceptions
class WorkspaceError(PowerBuilderError):
    """Base exception for workspace-related errors."""


# Integration exceptions
class IntegrationError(PowerBuilderError):
    """Base exception for integration-related errors."""


# Communication exceptions
class CommunicationError(PowerBuilderError):
    """Base exception for agent communication errors."""


class MessageDeliveryError(CommunicationError):
    """Raised when message delivery fails."""

    def __init__(self, message: str, recipient_id: str = None,
                 message_id: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.recipient_id = recipient_id
        self.message_id = message_id


class MessageTimeoutError(CommunicationError):
    """Raised when message response times out."""

    def __init__(self, message: str, message_id: str = None,
                 timeout_seconds: int = None, **kwargs):
        super().__init__(message, **kwargs)
        self.message_id = message_id
        self.timeout_seconds = timeout_seconds


class AgentNotFoundError(CommunicationError):
    """Raised when target agent is not found."""

    def __init__(self, message: str, agent_id: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.agent_id = agent_id


class MessageQueueFullError(CommunicationError):
    """Raised when message queue is at capacity."""

    def __init__(self, message: str, queue_name: str = None,
                 max_capacity: int = None, **kwargs):
        super().__init__(message, **kwargs)
        self.queue_name = queue_name
        self.max_capacity = max_capacity


class ConflictResolutionError(CommunicationError):
    """Raised when conflict resolution fails."""

    def __init__(self, message: str, conflict_type: str = None,
                 involved_agents: list = None, **kwargs):
        super().__init__(message, **kwargs)
        self.conflict_type = conflict_type
        self.involved_agents = involved_agents or []


class TaskDelegationError(CommunicationError):
    """Raised when task delegation fails."""

    def __init__(self, message: str, task_id: str = None,
                 target_agent: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.task_id = task_id
        self.target_agent = target_agent


# Google Workspace Provider exceptions
class WorkspaceProviderError(AdapterError):
    """Base exception for Google Workspace provider errors."""


class CalendarError(WorkspaceProviderError):
    """Base exception for calendar-related errors."""


class EventNotFoundError(CalendarError):
    """Raised when a requested calendar event is not found."""

    def __init__(self, message: str, event_id: str = None, calendar_id: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.event_id = event_id
        self.calendar_id = calendar_id


class CalendarNotFoundError(CalendarError):
    """Raised when a requested calendar is not found."""

    def __init__(self, message: str, calendar_id: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.calendar_id = calendar_id


class EventConflictError(CalendarError):
    """Raised when there's a conflict with calendar events."""

    def __init__(self, message: str, conflicting_events: list = None, **kwargs):
        super().__init__(message, **kwargs)
        self.conflicting_events = conflicting_events or []


class GmailError(WorkspaceProviderError):
    """Base exception for Gmail-related errors."""


class MessageNotFoundError(GmailError):
    """Raised when a requested email message is not found."""

    def __init__(self, message: str, message_id: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.message_id = message_id


class EmailSendError(GmailError):
    """Raised when email sending fails."""

    def __init__(self, message: str, recipient: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.recipient = recipient


class AttachmentError(GmailError):
    """Raised when email attachment operations fail."""

    def __init__(self, message: str, attachment_name: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.attachment_name = attachment_name


class DriveError(WorkspaceProviderError):
    """Base exception for Google Drive-related errors."""


class FileNotFoundError(DriveError):
    """Raised when a requested Drive file is not found."""

    def __init__(self, message: str, file_id: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.file_id = file_id


class UploadError(DriveError):
    """Raised when file upload fails."""

    def __init__(self, message: str, file_name: str = None, file_size: int = None, **kwargs):
        super().__init__(message, **kwargs)
        self.file_name = file_name
        self.file_size = file_size


class StorageQuotaError(DriveError):
    """Raised when storage quota is exceeded."""

    def __init__(self, message: str, quota_used: int = None, quota_limit: int = None, **kwargs):
        super().__init__(message, **kwargs)
        self.quota_used = quota_used
        self.quota_limit = quota_limit


class SharingError(DriveError):
    """Raised when file sharing operations fail."""

    def __init__(self, message: str, file_id: str = None, share_email: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.file_id = file_id
        self.share_email = share_email


class TasksError(WorkspaceProviderError):
    """Base exception for Google Tasks-related errors."""


class TaskNotFoundError(TasksError):
    """Raised when a requested task is not found."""

    def __init__(self, message: str, task_id: str = None, task_list_id: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.task_id = task_id
        self.task_list_id = task_list_id


class TaskListNotFoundError(TasksError):
    """Raised when a requested task list is not found."""

    def __init__(self, message: str, task_list_id: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.task_list_id = task_list_id


class OAuthError(WorkspaceProviderError):
    """Raised when OAuth authentication fails."""

    def __init__(self, message: str, oauth_error: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.oauth_error = oauth_error


class PermissionDeniedError(WorkspaceProviderError):
    """Raised when user lacks required permissions for Workspace operations."""

    def __init__(self, message: str, required_scope: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.required_scope = required_scope


# Registry exceptions
class RegistryError(PowerBuilderError):
    """Base exception for registry-related errors."""


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
            target_exception_class = RequestTimeoutError
        elif 'network' in exception_name or 'connection' in exception_name:
            target_exception_class = NetworkError
        elif 'invalid' in exception_name:
            target_exception_class = InvalidRequestError
        elif 'content' in exception_name and 'violation' in exception_name:
            target_exception_class = ContentViolationError
        elif 'media' in exception_name and 'upload' in exception_name:
            target_exception_class = MediaUploadError
        elif 'post' in exception_name and 'not' in exception_name:
            target_exception_class = PostNotFoundError
        elif 'user' in exception_name and 'not' in exception_name:
            target_exception_class = UserNotFoundError
        elif 'schedul' in exception_name:
            target_exception_class = SchedulingError
        elif 'permission' in exception_name or 'forbidden' in exception_name:
            target_exception_class = PermissionError
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
        RequestTimeoutError,
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

    if isinstance(exception, RequestTimeoutError):
        return 5  # 5 second delay for timeouts

    if isinstance(exception, NetworkError):
        return 3  # 3 second delay for network errors

    return 1  # Default 1 second delay
