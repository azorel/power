"""
Interface for validation worker functionality.
Defines the contract for comprehensive code validation.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of validation process."""
    passed: bool
    message: str
    details: Dict[str, Any]


class ValidationWorkerInterface(ABC):
    """
    Interface for validation workers.
    
    Defines the contract for validation implementations that ensure
    code quality, architecture compliance, and integration compatibility.
    """

    @abstractmethod
    def validate_submission(self, submission: Any) -> ValidationResult:
        """
        Validate a work submission against all quality standards.

        Args:
            submission: Work submission to validate

        Returns:
            ValidationResult with detailed validation information
        """

    @abstractmethod
    def get_validation_summary(self) -> Dict[str, Any]:
        """
        Get summary of validation history and statistics.

        Returns:
            Summary dictionary with validation metrics
        """