"""
Email validation utility for Power Builder.

This module provides robust email validation with comprehensive error handling
and detailed validation feedback for email address format verification.
"""

import re
from typing import Dict, Any, Optional

from shared.exceptions import DataValidationError


class EmailValidationError(DataValidationError):
    """Raised when email address validation fails."""

    def __init__(self, message: str, email_address: str = None,
                 validation_errors: list = None, **kwargs):
        super().__init__(message, **kwargs)
        self.email_address = email_address
        self.validation_errors = validation_errors or []


def validate_email_address(email: str, strict_mode: bool = True) -> Dict[str, Any]:
    """
    Validate email address format with comprehensive error reporting.

    Performs multi-layered validation including format checking, domain validation,
    and optional strict mode compliance with RFC 5322 standards.

    Args:
        email: Email address string to validate
        strict_mode: Enable strict RFC 5322 compliance checking

    Returns:
        Dict containing validation results with keys:
        - 'is_valid': Boolean indicating overall validity
        - 'email': Normalized email address
        - 'local_part': Local part of email (before @)
        - 'domain_part': Domain part of email (after @)
        - 'warnings': List of non-critical validation warnings

    Raises:
        EmailValidationError: If email format is invalid
        ValueError: If email parameter is None or empty
    """
    if not email:
        raise ValueError("Email address cannot be None or empty")

    if not isinstance(email, str):
        raise ValueError("Email address must be a string")

    # Normalize email by stripping whitespace and converting to lowercase
    normalized_email = email.strip().lower()

    if not normalized_email:
        raise ValueError("Email address cannot be empty after normalization")

    validation_errors = []
    warnings = []

    # Basic format validation
    if '@' not in normalized_email:
        validation_errors.append("Email must contain '@' symbol")

    if normalized_email.count('@') != 1:
        validation_errors.append("Email must contain exactly one '@' symbol")

    if validation_errors:
        raise EmailValidationError(
            f"Invalid email format: {'; '.join(validation_errors)}",
            email_address=email,
            validation_errors=validation_errors
        )

    # Split into local and domain parts
    local_part, domain_part = normalized_email.split('@')

    # Validate local part
    _validate_local_part(local_part, strict_mode, validation_errors, warnings)

    # Validate domain part
    _validate_domain_part(domain_part, strict_mode, validation_errors, warnings)

    if validation_errors:
        raise EmailValidationError(
            f"Email validation failed: {'; '.join(validation_errors)}",
            email_address=email,
            validation_errors=validation_errors
        )

    return {
        'is_valid': True,
        'email': normalized_email,
        'local_part': local_part,
        'domain_part': domain_part,
        'warnings': warnings
    }


def _validate_local_part(local_part: str, strict_mode: bool,
                        validation_errors: list, warnings: list) -> None:
    """
    Validate the local part of email address (before @).

    Args:
        local_part: Local part of email to validate
        strict_mode: Enable strict validation rules
        validation_errors: List to append validation errors
        warnings: List to append validation warnings

    Raises:
        None: Appends errors to validation_errors list
    """
    if not local_part:
        validation_errors.append("Local part cannot be empty")
        return

    if len(local_part) > 64:
        validation_errors.append("Local part cannot exceed 64 characters")

    # Check for consecutive dots
    if '..' in local_part:
        validation_errors.append("Local part cannot contain consecutive dots")

    # Check for leading/trailing dots
    if local_part.startswith('.') or local_part.endswith('.'):
        validation_errors.append("Local part cannot start or end with a dot")

    # Strict mode additional checks
    if strict_mode:
        # RFC 5322 compliant pattern for local part
        local_pattern = r'^[a-zA-Z0-9!#$%&\'*+/=?^_`{|}~-]+(\.[a-zA-Z0-9!#$%&\'*+/=?^_`{|}~-]+)*$'
        if not re.match(local_pattern, local_part):
            validation_errors.append("Local part contains invalid characters")
    else:
        # Basic alphanumeric and common symbols
        basic_pattern = r'^[a-zA-Z0-9._-]+$'
        if not re.match(basic_pattern, local_part):
            warnings.append("Local part contains uncommon characters")


def _validate_domain_part(domain_part: str, strict_mode: bool,  # pylint: disable=unused-argument
                         validation_errors: list, warnings: list) -> None:  # pylint: disable=unused-argument
    """
    Validate the domain part of email address (after @).

    Args:
        domain_part: Domain part of email to validate
        strict_mode: Enable strict validation rules (reserved for future use)
        validation_errors: List to append validation errors
        warnings: List to append validation warnings (reserved for future use)

    Raises:
        None: Appends errors to validation_errors list
    """
    if not domain_part:
        validation_errors.append("Domain part cannot be empty")
        return

    if len(domain_part) > 253:
        validation_errors.append("Domain part cannot exceed 253 characters")

    # Check for consecutive dots
    if '..' in domain_part:
        validation_errors.append("Domain part cannot contain consecutive dots")

    # Check for leading/trailing dots or hyphens
    if domain_part.startswith('.') or domain_part.endswith('.'):
        validation_errors.append("Domain part cannot start or end with a dot")

    if domain_part.startswith('-') or domain_part.endswith('-'):
        validation_errors.append("Domain part cannot start or end with a hyphen")

    # Must contain at least one dot for TLD
    if '.' not in domain_part:
        validation_errors.append("Domain part must contain at least one dot")

    # Validate domain format
    domain_pattern = r'^[a-zA-Z0-9.-]+$'
    if not re.match(domain_pattern, domain_part):
        validation_errors.append("Domain part contains invalid characters")

    # Validate individual domain labels
    labels = domain_part.split('.')
    for label in labels:
        if not label:
            validation_errors.append("Domain part cannot contain empty labels")
            continue

        if len(label) > 63:
            validation_errors.append("Domain labels cannot exceed 63 characters")

        if label.startswith('-') or label.endswith('-'):
            validation_errors.append("Domain labels cannot start or end with hyphen")

    # TLD validation
    if labels and len(labels[-1]) < 2:
        validation_errors.append("Top-level domain must be at least 2 characters")


def is_valid_email(email: str, strict_mode: bool = True) -> bool:
    """
    Check if email address is valid without raising exceptions.

    Simple boolean check for email validity, useful for quick validation
    without needing detailed error information.

    Args:
        email: Email address string to validate
        strict_mode: Enable strict RFC 5322 compliance checking

    Returns:
        True if email is valid, False otherwise

    Raises:
        None: Returns False for any validation errors
    """
    try:
        result = validate_email_address(email, strict_mode)
        return result['is_valid']
    except (EmailValidationError, ValueError):
        return False


def get_email_domain(email: str) -> Optional[str]:
    """
    Extract domain part from valid email address.

    Args:
        email: Email address to extract domain from

    Returns:
        Domain part of email or None if email is invalid

    Raises:
        None: Returns None for invalid email addresses
    """
    try:
        result = validate_email_address(email, strict_mode=False)
        return result['domain_part']
    except (EmailValidationError, ValueError):
        return None
