"""
Interface for integration management functionality.
Defines the contract for managing integrations and workflows.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class WorkflowResult:
    """Result of workflow operation."""
    success: bool
    message: str
    details: Dict[str, Any]


class IntegrationManagerInterface(ABC):
    """
    Interface for managing integration workflows.
    
    Defines the contract for integration management implementations
    that handle GitHub workflows, PR creation, and deployment automation.
    """

    @abstractmethod
    def create_feature_branch(self, branch_name: str, base_branch: str = None) -> WorkflowResult:
        """
        Create feature branch from base branch.

        Args:
            branch_name: Name of the feature branch to create
            base_branch: Base branch to create from

        Returns:
            WorkflowResult with branch creation status
        """

    @abstractmethod
    def commit_changes(self, message: str, files: Optional[List[str]] = None) -> WorkflowResult:
        """
        Commit changes to current branch.

        Args:
            message: Commit message
            files: List of files to commit (None for all changes)

        Returns:
            WorkflowResult with commit status
        """

    @abstractmethod
    def push_branch(self, branch_name: str, set_upstream: bool = True) -> WorkflowResult:
        """
        Push branch to remote repository.

        Args:
            branch_name: Name of the branch to push
            set_upstream: Whether to set upstream tracking

        Returns:
            WorkflowResult with push status
        """

    @abstractmethod
    def create_pull_request(
        self, 
        title: str, 
        body: str, 
        source_branch: str, 
        target_branch: str = None
    ) -> WorkflowResult:
        """
        Create pull request.

        Args:
            title: PR title
            body: PR description
            source_branch: Source branch for PR
            target_branch: Target branch

        Returns:
            WorkflowResult with PR creation status
        """

    @abstractmethod
    def merge_pull_request(self, pr_number: int, merge_method: str = "merge") -> WorkflowResult:
        """
        Merge pull request.

        Args:
            pr_number: Pull request number
            merge_method: Merge method (merge, squash, rebase)

        Returns:
            WorkflowResult with merge status
        """

    @abstractmethod
    def cleanup_branch(self, branch_name: str, remove_remote: bool = True) -> WorkflowResult:
        """
        Clean up feature branch after merge.

        Args:
            branch_name: Name of the branch to clean up
            remove_remote: Whether to remove remote branch

        Returns:
            WorkflowResult with cleanup status
        """