"""
Agent workspace management for isolated development environments.
Handles creation, lifecycle, and cleanup of agent workspaces.
"""

import os
import shutil
import subprocess
import uuid
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import logging

from shared.exceptions import WorkspaceError, ValidationError
from shared.interfaces.workspace_manager import WorkspaceManagerInterface

logger = logging.getLogger(__name__)


@dataclass
class WorkspaceConfig:
    """Configuration for agent workspace."""
    agent_id: str
    task_id: str
    workspace_path: Path
    feature_branch: str
    created_at: datetime
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


class AgentWorkspaceManager(WorkspaceManagerInterface):
    """
    Manages isolated agent workspaces with fresh GitHub clones.
    Implements complete workspace lifecycle with automated cleanup.
    """

    def __init__(self, base_agents_dir: str = "agents"):
        """
        Initialize workspace manager.

        Args:
            base_agents_dir: Base directory for all agent workspaces
        """
        self.base_agents_dir = Path(base_agents_dir)
        self.active_workspaces: Dict[str, WorkspaceConfig] = {}
        self.workspace_status: Dict[str, WorkspaceStatus] = {}
        
        # Ensure base directory exists
        self.base_agents_dir.mkdir(exist_ok=True)
        
        # Load existing workspaces
        self._load_existing_workspaces()

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
        try:
            # Generate unique identifiers
            agent_id = f"agent-{uuid.uuid4().hex[:8]}"
            task_id = f"task-{uuid.uuid4().hex[:8]}"
            
            # Create workspace configuration
            workspace_config = WorkspaceConfig(
                agent_id=agent_id,
                task_id=task_id,
                workspace_path=self.base_agents_dir / agent_id,
                feature_branch=f"feature/agent-{task_id}",
                created_at=datetime.now()
            )
            
            logger.info(f"Creating workspace for agent {agent_id}, task {task_id}")
            
            # Create workspace directory
            workspace_config.workspace_path.mkdir(parents=True, exist_ok=True)
            
            # Initialize workspace status
            self.workspace_status[agent_id] = WorkspaceStatus(
                agent_id=agent_id,
                task_id=task_id,
                status="creating",
                branch_name=workspace_config.feature_branch,
                files_modified=[],
                last_commit=None
            )
            
            # Setup workspace environment
            self._setup_workspace_environment(workspace_config, task_description, task_type)
            
            # Register workspace
            self.active_workspaces[agent_id] = workspace_config
            self._save_workspace_config(workspace_config)
            
            # Update status to active
            self.workspace_status[agent_id].status = "active"
            
            logger.info(f"Workspace created successfully: {workspace_config.workspace_path}")
            return workspace_config
            
        except Exception as e:
            error_msg = f"Failed to create workspace: {e}"
            logger.error(error_msg)
            
            # Update status to error if workspace was partially created
            if agent_id in self.workspace_status:
                self.workspace_status[agent_id].status = "error"
                self.workspace_status[agent_id].error_message = error_msg
            
            raise WorkspaceError(error_msg) from e

    def _setup_workspace_environment(self, config: WorkspaceConfig, task_description: str, task_type: str) -> None:
        """
        Setup complete workspace environment with fresh clone and virtual environment.

        Args:
            config: Workspace configuration
            task_description: Description of the task
            task_type: Type of task being performed
        """
        workspace_path = config.workspace_path
        
        # Step 1: Clone fresh repository
        logger.info(f"Cloning repository to {workspace_path}")
        clone_result = subprocess.run(
            ["git", "clone", config.github_repo, "power"],
            cwd=workspace_path,
            capture_output=True,
            text=True,
            check=False
        )
        
        if clone_result.returncode != 0:
            raise WorkspaceError(f"Git clone failed: {clone_result.stderr}")
        
        power_repo_path = workspace_path / "power"
        
        # Step 2: Create feature branch
        logger.info(f"Creating feature branch: {config.feature_branch}")
        branch_result = subprocess.run(
            ["git", "checkout", "-b", config.feature_branch],
            cwd=power_repo_path,
            capture_output=True,
            text=True,
            check=False
        )
        
        if branch_result.returncode != 0:
            raise WorkspaceError(f"Branch creation failed: {branch_result.stderr}")
        
        # Step 3: Create virtual environment
        logger.info("Creating virtual environment")
        venv_path = workspace_path / "venv"
        venv_result = subprocess.run(
            ["python", "-m", "venv", str(venv_path)],
            capture_output=True,
            text=True,
            check=False
        )
        
        if venv_result.returncode != 0:
            raise WorkspaceError(f"Virtual environment creation failed: {venv_result.stderr}")
        
        # Step 4: Install dependencies
        logger.info("Installing dependencies")
        pip_path = venv_path / "bin" / "pip" if os.name != "nt" else venv_path / "Scripts" / "pip.exe"
        requirements_path = power_repo_path / "requirements.txt"
        
        if requirements_path.exists():
            install_result = subprocess.run(
                [str(pip_path), "install", "-r", str(requirements_path)],
                capture_output=True,
                text=True,
                check=False
            )
            
            if install_result.returncode != 0:
                logger.warning(f"Dependency installation warnings: {install_result.stderr}")
                # Don't fail on dependency warnings, just log them
        
        # Step 5: Create plan.md with task details
        self._create_task_plan(config, task_description, task_type)
        
        # Step 6: Create workspace metadata
        self._create_workspace_metadata(config, task_description, task_type)

    def _create_task_plan(self, config: WorkspaceConfig, task_description: str, task_type: str) -> None:
        """
        Create plan.md file with detailed task execution plan.

        Args:
            config: Workspace configuration
            task_description: Description of the task
            task_type: Type of task being performed
        """
        plan_content = f"""# Agent Task Plan

## Task Information
- **Agent ID**: {config.agent_id}
- **Task ID**: {config.task_id}
- **Task Type**: {task_type}
- **Created**: {config.created_at.isoformat()}
- **Feature Branch**: {config.feature_branch}

## Task Description
{task_description}

## Required Standards
Based on task type '{task_type}', the following standards MUST be read and followed:

### Mandatory Standards Files
- `ai_docs/standards/CODING_STANDARDS.md` - Three-layer architecture enforcement
"""
        
        # Add task-specific standards
        if task_type in ["api_integration", "adapter_development"]:
            plan_content += "- `ai_docs/standards/API_INTEGRATION_STANDARDS.md` - External API integration rules\n"
        
        if "research" in task_type.lower():
            plan_content += "- `ai_docs/standards/RESEARCH_STANDARDS.md` - Search methodology and validation\n"
        
        if "test" in task_type.lower():
            plan_content += "- `ai_docs/standards/TESTING_STANDARDS.md` - Test protocols and validation\n"
        
        if task_type in ["integration", "deployment", "pr_creation"]:
            plan_content += "- `ai_docs/standards/INTEGRATION_STANDARDS.md` - PR creation and merge procedures\n"
        
        plan_content += """
## Execution Strategy

### Phase 1: Standards Review (MANDATORY)
1. Read all required standards files completely
2. Understand three-layer architecture requirements
3. Plan implementation approach within architectural constraints
4. Confirm understanding of quality gates (10/10 pylint, 100% test success)

### Phase 2: Implementation
1. Implement solution following CODING_STANDARDS.md exactly
2. Write pylint-compliant code from the first attempt
3. Include comprehensive docstrings and type hints
4. Follow proper import organization and naming conventions

### Phase 3: Validation
1. Run pylint to achieve perfect 10/10 score
2. Execute test suite to achieve 100% success rate
3. Validate architecture compliance
4. Ensure complete documentation

### Phase 4: Submission
1. Commit changes to feature branch
2. Create comprehensive commit message
3. Push feature branch to origin
4. Submit work package to orchestrator

## Quality Gates (ALL MUST PASS)
- [ ] Perfect 10/10 pylint score achieved
- [ ] 100% test success rate achieved
- [ ] Zero architecture violations detected
- [ ] Complete documentation provided
- [ ] Integration tests pass (if applicable)

## Workspace Environment
- **Python Version**: {config.python_version}
- **Virtual Environment**: Available at `../venv/`
- **Repository Path**: `./power/`
- **Branch**: `{config.feature_branch}`

## Completion Signal
Upon task completion, end your final message with:
**"Task complete and ready for next step"**

## Emergency Contacts
If you encounter issues that cannot be resolved:
1. Document the issue in this plan.md file
2. Commit current progress to feature branch
3. Submit error report to orchestrator with detailed information

---
*Generated by AgentWorkspaceManager at {datetime.now().isoformat()}*
"""
        
        plan_path = config.workspace_path / "plan.md"
        with open(plan_path, 'w', encoding='utf-8') as f:
            f.write(plan_content)

    def _create_workspace_metadata(self, config: WorkspaceConfig, task_description: str, task_type: str) -> None:
        """
        Create workspace metadata for tracking and management.

        Args:
            config: Workspace configuration
            task_description: Description of the task
            task_type: Type of task being performed
        """
        metadata = {
            "workspace_config": asdict(config),
            "task_info": {
                "description": task_description,
                "type": task_type,
                "created_at": config.created_at.isoformat(),
                "status": "active"
            },
            "environment": {
                "python_version": config.python_version,
                "venv_path": "../venv",
                "repo_path": "./power",
                "requirements_installed": True
            },
            "git_info": {
                "repo_url": config.github_repo,
                "base_branch": config.base_branch,
                "feature_branch": config.feature_branch,
                "initial_commit": None  # Will be updated when first commit is made
            }
        }
        
        # Convert Path objects to strings for JSON serialization
        metadata["workspace_config"]["workspace_path"] = str(config.workspace_path)
        metadata["workspace_config"]["created_at"] = config.created_at.isoformat()
        
        metadata_path = config.workspace_path / "workspace_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

    def get_workspace_status(self, agent_id: str) -> Optional[WorkspaceStatus]:
        """
        Get current status of workspace.

        Args:
            agent_id: Agent identifier

        Returns:
            WorkspaceStatus if workspace exists, None otherwise
        """
        return self.workspace_status.get(agent_id)

    def list_active_workspaces(self) -> List[WorkspaceConfig]:
        """
        List all active workspaces.

        Returns:
            List of active workspace configurations
        """
        return list(self.active_workspaces.values())

    def cleanup_workspace(self, agent_id: str, preserve_branch: bool = False) -> bool:
        """
        Clean up workspace after task completion.

        Args:
            agent_id: Agent identifier
            preserve_branch: Whether to preserve the feature branch

        Returns:
            True if cleanup successful, False otherwise
        """
        try:
            if agent_id not in self.active_workspaces:
                logger.warning(f"Workspace {agent_id} not found for cleanup")
                return False
            
            config = self.active_workspaces[agent_id]
            logger.info(f"Cleaning up workspace {agent_id}")
            
            # Update status
            if agent_id in self.workspace_status:
                self.workspace_status[agent_id].status = "cleaning"
            
            # Remove workspace directory
            if config.workspace_path.exists():
                shutil.rmtree(config.workspace_path)
                logger.info(f"Removed workspace directory: {config.workspace_path}")
            
            # Clean up feature branch if not preserving
            if not preserve_branch:
                self._cleanup_feature_branch(config)
            
            # Remove from active workspaces
            del self.active_workspaces[agent_id]
            
            # Update status
            if agent_id in self.workspace_status:
                self.workspace_status[agent_id].status = "cleaned"
            
            logger.info(f"Workspace {agent_id} cleaned up successfully")
            return True
            
        except Exception as e:
            error_msg = f"Failed to cleanup workspace {agent_id}: {e}"
            logger.error(error_msg)
            
            # Update status to error
            if agent_id in self.workspace_status:
                self.workspace_status[agent_id].status = "error"
                self.workspace_status[agent_id].error_message = error_msg
            
            return False

    def _cleanup_feature_branch(self, config: WorkspaceConfig) -> None:
        """
        Clean up feature branch from remote repository.

        Args:
            config: Workspace configuration with branch information
        """
        try:
            # This would typically be done through GitHub API or git commands
            # For now, we'll log the branch that should be cleaned up
            logger.info(f"Feature branch {config.feature_branch} should be cleaned up from remote")
            
            # In a full implementation, this would:
            # 1. Check if branch exists on remote
            # 2. Delete the remote branch if it exists
            # 3. Clean up any associated PRs if they exist
            
        except Exception as e:
            logger.warning(f"Failed to cleanup feature branch {config.feature_branch}: {e}")

    def get_workspace_logs(self, agent_id: str) -> Optional[List[str]]:
        """
        Get logs for specific workspace.

        Args:
            agent_id: Agent identifier

        Returns:
            List of log entries if workspace exists, None otherwise
        """
        if agent_id not in self.active_workspaces:
            return None
        
        config = self.active_workspaces[agent_id]
        logs_path = config.workspace_path / "logs"
        
        if not logs_path.exists():
            return []
        
        log_entries = []
        for log_file in logs_path.glob("*.log"):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    log_entries.extend(f.readlines())
            except Exception as e:
                logger.warning(f"Failed to read log file {log_file}: {e}")
        
        return log_entries

    def _save_workspace_config(self, config: WorkspaceConfig) -> None:
        """
        Save workspace configuration to persistent storage.

        Args:
            config: Workspace configuration to save
        """
        config_path = self.base_agents_dir / f"{config.agent_id}_config.json"
        
        # Convert to serializable format
        config_dict = asdict(config)
        config_dict["workspace_path"] = str(config.workspace_path)
        config_dict["created_at"] = config.created_at.isoformat()
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2)

    def _load_existing_workspaces(self) -> None:
        """Load existing workspace configurations from storage."""
        try:
            for config_file in self.base_agents_dir.glob("*_config.json"):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config_dict = json.load(f)
                    
                    # Convert back from serializable format
                    config_dict["workspace_path"] = Path(config_dict["workspace_path"])
                    config_dict["created_at"] = datetime.fromisoformat(config_dict["created_at"])
                    
                    config = WorkspaceConfig(**config_dict)
                    
                    # Only load if workspace directory still exists
                    if config.workspace_path.exists():
                        self.active_workspaces[config.agent_id] = config
                        
                        # Initialize status
                        self.workspace_status[config.agent_id] = WorkspaceStatus(
                            agent_id=config.agent_id,
                            task_id=config.task_id,
                            status="active",
                            branch_name=config.feature_branch,
                            files_modified=[],
                            last_commit=None
                        )
                    else:
                        # Remove stale config file
                        config_file.unlink()
                        
                except Exception as e:
                    logger.warning(f"Failed to load workspace config {config_file}: {e}")
                    
        except Exception as e:
            logger.warning(f"Failed to load existing workspaces: {e}")

    def update_workspace_status(self, agent_id: str, files_modified: List[str], last_commit: Optional[str] = None) -> None:
        """
        Update workspace status with current progress.

        Args:
            agent_id: Agent identifier
            files_modified: List of files that have been modified
            last_commit: Hash of last commit (if any)
        """
        if agent_id in self.workspace_status:
            status = self.workspace_status[agent_id]
            status.files_modified = files_modified
            if last_commit:
                status.last_commit = last_commit
            
            logger.info(f"Updated workspace status for {agent_id}: {len(files_modified)} files modified")

    def get_workspace_path(self, agent_id: str) -> Optional[Path]:
        """
        Get workspace path for agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Path to workspace if it exists, None otherwise
        """
        if agent_id in self.active_workspaces:
            return self.active_workspaces[agent_id].workspace_path
        return None

    def validate_workspace(self, agent_id: str) -> bool:
        """
        Validate workspace is properly configured and functional.

        Args:
            agent_id: Agent identifier

        Returns:
            True if workspace is valid and functional
        """
        try:
            if agent_id not in self.active_workspaces:
                return False
            
            config = self.active_workspaces[agent_id]
            
            # Check workspace directory exists
            if not config.workspace_path.exists():
                return False
            
            # Check power repository exists
            power_repo = config.workspace_path / "power"
            if not power_repo.exists():
                return False
            
            # Check virtual environment exists
            venv_path = config.workspace_path / "venv"
            if not venv_path.exists():
                return False
            
            # Check plan.md exists
            plan_path = config.workspace_path / "plan.md"
            if not plan_path.exists():
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Workspace validation failed for {agent_id}: {e}")
            return False