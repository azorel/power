"""
Interface for workspace management functionality.
Defines the contract for workspace managers across the system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass


@dataclass
class WorkspaceConfig:
    """Configuration for agent workspace."""
    agent_id: str
    task_id: str
    workspace_path: Path
    feature_branch: str
    created_at: Any  # datetime, but avoiding import for interface
    python_version: str = "3.12"
    requirements_file: str = "requirements.txt"
    github_repo: str = "https://github.com/azorel/power.git"
    base_branch: str = "main"


@dataclass
class WorkspaceStatus:
    """Current status of agent workspace."""
    agent_id: str
    task_id: str
    status: str  # creating, active, error, cleaning, cleaned
    branch_name: str
    files_modified: List[str]
    last_commit: Optional[str]
    error_message: Optional[str] = None


class WorkspaceManagerInterface(ABC):
    """
    Interface for managing agent workspaces.
    
    Defines the contract for workspace creation, management, and cleanup
    that ensures consistency across different workspace implementations.
    """

    @abstractmethod
    def create_workspace(self, task_description: str, task_type: str = "development") -> WorkspaceConfig:
        """
        Create isolated workspace for agent task.

        Args:
            task_description: Description of task for this workspace
            task_type: Type of task (development, research, integration)

        Returns:
            WorkspaceConfig for the created workspace

        Raises:
            WorkspaceError: If workspace creation fails
        """

    @abstractmethod
    def get_workspace_status(self, agent_id: str) -> Optional[WorkspaceStatus]:
        """
        Get current status of workspace.

        Args:
            agent_id: Agent identifier

        Returns:
            WorkspaceStatus if workspace exists, None otherwise
        """

    @abstractmethod
    def list_active_workspaces(self) -> List[WorkspaceConfig]:
        """
        List all active workspaces.

        Returns:
            List of active workspace configurations
        """

    @abstractmethod
    def cleanup_workspace(self, agent_id: str, preserve_branch: bool = False) -> bool:
        """
        Clean up workspace after task completion.

        Args:
            agent_id: Agent identifier
            preserve_branch: Whether to preserve the feature branch

        Returns:
            True if cleanup successful, False otherwise
        """

    @abstractmethod
    def get_workspace_logs(self, agent_id: str) -> Optional[List[str]]:
        """
        Get logs for specific workspace.

        Args:
            agent_id: Agent identifier

        Returns:
            List of log entries if workspace exists, None otherwise
        """

    @abstractmethod
    def update_workspace_status(self, agent_id: str, files_modified: List[str], last_commit: Optional[str] = None) -> None:
        """
        Update workspace status with current progress.

        Args:
            agent_id: Agent identifier
            files_modified: List of files that have been modified
            last_commit: Hash of last commit (if any)
        """

    @abstractmethod
    def get_workspace_path(self, agent_id: str) -> Optional[Path]:
        """
        Get workspace path for agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Path to workspace if it exists, None otherwise
        """

    @abstractmethod
    def validate_workspace(self, agent_id: str) -> bool:
        """
        Validate workspace is properly configured and functional.

        Args:
            agent_id: Agent identifier

        Returns:
            True if workspace is valid and functional
        """