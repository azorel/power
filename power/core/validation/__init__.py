"""
Core validation module.
Provides comprehensive code validation and quality assurance.
"""

from .integration_worker import IntegrationWorker, ValidationResult, WorkSubmission

__all__ = ['IntegrationWorker', 'ValidationResult', 'WorkSubmission']