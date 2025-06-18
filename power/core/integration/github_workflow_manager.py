"""
GitHub workflow automation for agent integration.
Manages branch strategy, PR creation, and automated deployment.
"""

import subprocess
import json
import os
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import logging

from shared.exceptions import WorkspaceError, ValidationError, IntegrationError
from shared.interfaces.integration_manager import IntegrationManagerInterface

logger = logging.getLogger(__name__)


@dataclass
class BranchInfo:
    """Information about a Git branch."""
    name: str
    commit_hash: str
    created_at: datetime
    author: str
    message: str


@dataclass
class PullRequestInfo:
    """Information about a pull request."""
    number: int
    title: str
    body: str
    source_branch: str
    target_branch: str
    state: str
    url: str
    created_at: datetime


@dataclass
class WorkflowResult:
    """Result of workflow operation."""
    success: bool
    message: str
    details: Dict[str, Any]
    pr_info: Optional[PullRequestInfo] = None


class GitHubWorkflowManager(IntegrationManagerInterface):
    """
    Manages GitHub workflow automation for agent integration.
    Implements professional branch strategy and automated PR creation.
    """

    def __init__(self, repo_path: str = ".", github_token: Optional[str] = None):
        """
        Initialize GitHub workflow manager.

        Args:
            repo_path: Path to the Git repository
            github_token: GitHub personal access token for API operations
        """
        self.repo_path = Path(repo_path)
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')
        self.default_branch = "main"
        self.integration_branch = "develop"
        
        # Validate repository
        if not self._is_git_repository():
            raise IntegrationError(f"Not a git repository: {self.repo_path}")

    def create_feature_branch(self, branch_name: str, base_branch: str = None) -> WorkflowResult:
        """
        Create feature branch from base branch.

        Args:
            branch_name: Name of the feature branch to create
            base_branch: Base branch to create from (defaults to main)

        Returns:
            WorkflowResult with branch creation status
        """
        try:
            base = base_branch or self.default_branch
            
            logger.info(f"Creating feature branch {branch_name} from {base}")
            
            # Ensure we're on the base branch and it's up to date
            self._ensure_branch_updated(base)
            
            # Create and checkout feature branch
            result = self._run_git_command(['checkout', '-b', branch_name])
            if not result['success']:
                return WorkflowResult(
                    success=False,
                    message=f"Failed to create branch {branch_name}",
                    details=result
                )
            
            # Get branch info
            branch_info = self._get_branch_info(branch_name)
            
            return WorkflowResult(
                success=True,
                message=f"Feature branch {branch_name} created successfully",
                details={
                    'branch_name': branch_name,
                    'base_branch': base,
                    'commit_hash': branch_info.commit_hash if branch_info else None
                }
            )
            
        except Exception as e:
            error_msg = f"Failed to create feature branch {branch_name}: {e}"
            logger.error(error_msg)
            return WorkflowResult(
                success=False,
                message=error_msg,
                details={'exception': str(e)}
            )

    def commit_changes(self, message: str, files: Optional[List[str]] = None) -> WorkflowResult:
        """
        Commit changes to current branch.

        Args:
            message: Commit message
            files: List of files to commit (None for all changes)

        Returns:
            WorkflowResult with commit status
        """
        try:
            # Check if there are changes to commit
            status_result = self._run_git_command(['status', '--porcelain'])
            if not status_result['success']:
                return WorkflowResult(
                    success=False,
                    message="Failed to check git status",
                    details=status_result
                )
            
            if not status_result['output'].strip():
                return WorkflowResult(
                    success=True,
                    message="No changes to commit",
                    details={'changes': False}
                )
            
            # Add files
            if files:
                for file_path in files:
                    add_result = self._run_git_command(['add', file_path])
                    if not add_result['success']:
                        return WorkflowResult(
                            success=False,
                            message=f"Failed to add file {file_path}",
                            details=add_result
                        )
            else:
                add_result = self._run_git_command(['add', '.'])
                if not add_result['success']:
                    return WorkflowResult(
                        success=False,
                        message="Failed to add changes",
                        details=add_result
                    )
            
            # Create commit with standardized message format
            standardized_message = self._standardize_commit_message(message)
            commit_result = self._run_git_command(['commit', '-m', standardized_message])
            
            if not commit_result['success']:
                return WorkflowResult(
                    success=False,
                    message="Failed to create commit",
                    details=commit_result
                )
            
            # Get commit hash
            hash_result = self._run_git_command(['rev-parse', 'HEAD'])
            commit_hash = hash_result['output'].strip() if hash_result['success'] else None
            
            return WorkflowResult(
                success=True,
                message=f"Changes committed successfully",
                details={
                    'commit_hash': commit_hash,
                    'message': standardized_message,
                    'files_added': len(files) if files else 'all'
                }
            )
            
        except Exception as e:
            error_msg = f"Failed to commit changes: {e}"
            logger.error(error_msg)
            return WorkflowResult(
                success=False,
                message=error_msg,
                details={'exception': str(e)}
            )

    def push_branch(self, branch_name: str, set_upstream: bool = True) -> WorkflowResult:
        """
        Push branch to remote repository.

        Args:
            branch_name: Name of the branch to push
            set_upstream: Whether to set upstream tracking

        Returns:
            WorkflowResult with push status
        """
        try:
            # Build push command
            push_cmd = ['push']
            if set_upstream:
                push_cmd.extend(['-u', 'origin', branch_name])
            else:
                push_cmd.extend(['origin', branch_name])
            
            logger.info(f"Pushing branch {branch_name} to remote")
            
            push_result = self._run_git_command(push_cmd)
            
            if not push_result['success']:
                return WorkflowResult(
                    success=False,
                    message=f"Failed to push branch {branch_name}",
                    details=push_result
                )
            
            return WorkflowResult(
                success=True,
                message=f"Branch {branch_name} pushed successfully",
                details={
                    'branch_name': branch_name,
                    'upstream_set': set_upstream,
                    'remote': 'origin'
                }
            )
            
        except Exception as e:
            error_msg = f"Failed to push branch {branch_name}: {e}"
            logger.error(error_msg)
            return WorkflowResult(
                success=False,
                message=error_msg,
                details={'exception': str(e)}
            )

    def create_pull_request(
        self, 
        title: str, 
        body: str, 
        source_branch: str, 
        target_branch: str = None
    ) -> WorkflowResult:
        """
        Create pull request using GitHub CLI.

        Args:
            title: PR title
            body: PR description
            source_branch: Source branch for PR
            target_branch: Target branch (defaults to main)

        Returns:
            WorkflowResult with PR creation status
        """
        try:
            target = target_branch or self.default_branch
            
            logger.info(f"Creating PR: {source_branch} -> {target}")
            
            # Check if GitHub CLI is available
            if not self._is_gh_cli_available():
                return WorkflowResult(
                    success=False,
                    message="GitHub CLI (gh) not available",
                    details={'gh_cli_required': True}
                )
            
            # Create PR using GitHub CLI
            pr_cmd = [
                'gh', 'pr', 'create',
                '--title', title,
                '--body', body,
                '--base', target,
                '--head', source_branch
            ]
            
            # Set GitHub token if available
            env = os.environ.copy()
            if self.github_token:
                env['GITHUB_TOKEN'] = self.github_token
            
            pr_result = subprocess.run(
                pr_cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                env=env,
                check=False
            )
            
            if pr_result.returncode != 0:
                return WorkflowResult(
                    success=False,
                    message=f"Failed to create PR: {pr_result.stderr}",
                    details={
                        'returncode': pr_result.returncode,
                        'stderr': pr_result.stderr,
                        'stdout': pr_result.stdout
                    }
                )
            
            # Parse PR URL from output
            pr_url = pr_result.stdout.strip()
            
            # Get PR info using GitHub CLI
            pr_info = self._get_pr_info_from_url(pr_url)
            
            return WorkflowResult(
                success=True,
                message=f"Pull request created successfully: {pr_url}",
                details={
                    'pr_url': pr_url,
                    'source_branch': source_branch,
                    'target_branch': target,
                    'title': title
                },
                pr_info=pr_info
            )
            
        except Exception as e:
            error_msg = f"Failed to create pull request: {e}"
            logger.error(error_msg)
            return WorkflowResult(
                success=False,
                message=error_msg,
                details={'exception': str(e)}
            )

    def merge_pull_request(self, pr_number: int, merge_method: str = "merge") -> WorkflowResult:
        """
        Merge pull request using GitHub CLI.

        Args:
            pr_number: Pull request number
            merge_method: Merge method (merge, squash, rebase)

        Returns:
            WorkflowResult with merge status
        """
        try:
            logger.info(f"Merging PR #{pr_number} using {merge_method}")
            
            if not self._is_gh_cli_available():
                return WorkflowResult(
                    success=False,
                    message="GitHub CLI (gh) not available",
                    details={'gh_cli_required': True}
                )
            
            # Merge PR using GitHub CLI
            merge_cmd = ['gh', 'pr', 'merge', str(pr_number)]
            
            if merge_method == "squash":
                merge_cmd.append('--squash')
            elif merge_method == "rebase":
                merge_cmd.append('--rebase')
            else:
                merge_cmd.append('--merge')
            
            # Set GitHub token if available
            env = os.environ.copy()
            if self.github_token:
                env['GITHUB_TOKEN'] = self.github_token
            
            merge_result = subprocess.run(
                merge_cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                env=env,
                check=False
            )
            
            if merge_result.returncode != 0:
                return WorkflowResult(
                    success=False,
                    message=f"Failed to merge PR #{pr_number}: {merge_result.stderr}",
                    details={
                        'returncode': merge_result.returncode,
                        'stderr': merge_result.stderr,
                        'stdout': merge_result.stdout
                    }
                )
            
            return WorkflowResult(
                success=True,
                message=f"PR #{pr_number} merged successfully",
                details={
                    'pr_number': pr_number,
                    'merge_method': merge_method,
                    'output': merge_result.stdout
                }
            )
            
        except Exception as e:
            error_msg = f"Failed to merge PR #{pr_number}: {e}"
            logger.error(error_msg)
            return WorkflowResult(
                success=False,
                message=error_msg,
                details={'exception': str(e)}
            )

    def cleanup_branch(self, branch_name: str, remove_remote: bool = True) -> WorkflowResult:
        """
        Clean up feature branch after merge.

        Args:
            branch_name: Name of the branch to clean up
            remove_remote: Whether to remove remote branch

        Returns:
            WorkflowResult with cleanup status
        """
        try:
            logger.info(f"Cleaning up branch {branch_name}")
            
            results = []
            
            # Switch to default branch first
            checkout_result = self._run_git_command(['checkout', self.default_branch])
            if not checkout_result['success']:
                return WorkflowResult(
                    success=False,
                    message=f"Failed to checkout {self.default_branch}",
                    details=checkout_result
                )
            
            # Delete local branch
            delete_result = self._run_git_command(['branch', '-d', branch_name])
            if delete_result['success']:
                results.append(f"Local branch {branch_name} deleted")
            else:
                # Try force delete if normal delete fails
                force_delete_result = self._run_git_command(['branch', '-D', branch_name])
                if force_delete_result['success']:
                    results.append(f"Local branch {branch_name} force deleted")
                else:
                    results.append(f"Failed to delete local branch {branch_name}")
            
            # Remove remote branch if requested
            if remove_remote:
                remote_delete_result = self._run_git_command(['push', 'origin', '--delete', branch_name])
                if remote_delete_result['success']:
                    results.append(f"Remote branch {branch_name} deleted")
                else:
                    results.append(f"Failed to delete remote branch {branch_name}")
            
            return WorkflowResult(
                success=True,
                message=f"Branch cleanup completed",
                details={
                    'branch_name': branch_name,
                    'results': results,
                    'remote_removed': remove_remote
                }
            )
            
        except Exception as e:
            error_msg = f"Failed to cleanup branch {branch_name}: {e}"
            logger.error(error_msg)
            return WorkflowResult(
                success=False,
                message=error_msg,
                details={'exception': str(e)}
            )

    def get_branch_status(self, branch_name: str) -> Optional[BranchInfo]:
        """
        Get information about a branch.

        Args:
            branch_name: Name of the branch

        Returns:
            BranchInfo if branch exists, None otherwise
        """
        try:
            return self._get_branch_info(branch_name)
        except Exception as e:
            logger.warning(f"Failed to get branch status for {branch_name}: {e}")
            return None

    def validate_branch_protection(self, branch_name: str) -> WorkflowResult:
        """
        Validate branch protection rules are in place.

        Args:
            branch_name: Name of the branch to validate

        Returns:
            WorkflowResult with validation status
        """
        try:
            if not self._is_gh_cli_available():
                return WorkflowResult(
                    success=False,
                    message="GitHub CLI required for branch protection validation",
                    details={'gh_cli_required': True}
                )
            
            # Check branch protection using GitHub CLI
            protection_cmd = ['gh', 'api', f'repos/:owner/:repo/branches/{branch_name}/protection']
            
            env = os.environ.copy()
            if self.github_token:
                env['GITHUB_TOKEN'] = self.github_token
            
            protection_result = subprocess.run(
                protection_cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                env=env,
                check=False
            )
            
            if protection_result.returncode != 0:
                return WorkflowResult(
                    success=False,
                    message=f"Branch {branch_name} has no protection rules",
                    details={
                        'protected': False,
                        'error': protection_result.stderr
                    }
                )
            
            # Parse protection info
            try:
                protection_info = json.loads(protection_result.stdout)
                
                return WorkflowResult(
                    success=True,
                    message=f"Branch {branch_name} is protected",
                    details={
                        'protected': True,
                        'protection_info': protection_info
                    }
                )
                
            except json.JSONDecodeError:
                return WorkflowResult(
                    success=False,
                    message="Failed to parse branch protection information",
                    details={'raw_output': protection_result.stdout}
                )
            
        except Exception as e:
            error_msg = f"Failed to validate branch protection for {branch_name}: {e}"
            logger.error(error_msg)
            return WorkflowResult(
                success=False,
                message=error_msg,
                details={'exception': str(e)}
            )

    def _is_git_repository(self) -> bool:
        """Check if the path is a git repository."""
        git_dir = self.repo_path / '.git'
        return git_dir.exists() or self._run_git_command(['rev-parse', '--git-dir'])['success']

    def _is_gh_cli_available(self) -> bool:
        """Check if GitHub CLI is available."""
        try:
            result = subprocess.run(['gh', '--version'], capture_output=True, check=False)
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def _run_git_command(self, command: List[str]) -> Dict[str, Any]:
        """Run a git command and return the result."""
        try:
            result = subprocess.run(
                ['git'] + command,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False
            )
            
            return {
                'success': result.returncode == 0,
                'returncode': result.returncode,
                'output': result.stdout,
                'error': result.stderr
            }
            
        except Exception as e:
            return {
                'success': False,
                'returncode': -1,
                'output': '',
                'error': str(e)
            }

    def _ensure_branch_updated(self, branch_name: str) -> None:
        """Ensure branch is checked out and up to date."""
        # Fetch latest changes
        self._run_git_command(['fetch', 'origin'])
        
        # Checkout branch
        checkout_result = self._run_git_command(['checkout', branch_name])
        if not checkout_result['success']:
            raise IntegrationError(f"Failed to checkout branch {branch_name}")
        
        # Pull latest changes
        pull_result = self._run_git_command(['pull', 'origin', branch_name])
        if not pull_result['success']:
            logger.warning(f"Failed to pull latest changes for {branch_name}: {pull_result['error']}")

    def _get_branch_info(self, branch_name: str) -> Optional[BranchInfo]:
        """Get detailed information about a branch."""
        try:
            # Get commit hash
            hash_result = self._run_git_command(['rev-parse', branch_name])
            if not hash_result['success']:
                return None
            
            commit_hash = hash_result['output'].strip()
            
            # Get commit info
            log_result = self._run_git_command(['log', '-1', '--format=%an|%at|%s', branch_name])
            if not log_result['success']:
                return None
            
            log_parts = log_result['output'].strip().split('|', 2)
            if len(log_parts) != 3:
                return None
            
            author, timestamp, message = log_parts
            created_at = datetime.fromtimestamp(int(timestamp))
            
            return BranchInfo(
                name=branch_name,
                commit_hash=commit_hash,
                created_at=created_at,
                author=author,
                message=message
            )
            
        except Exception as e:
            logger.warning(f"Failed to get branch info for {branch_name}: {e}")
            return None

    def _standardize_commit_message(self, message: str) -> str:
        """Standardize commit message format."""
        # Add standard footer if not present
        footer = "\n\n🤖 Generated with [Claude Code](https://claude.ai/code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>"
        
        if footer.strip() not in message:
            message = message.rstrip() + footer
        
        return message

    def _get_pr_info_from_url(self, pr_url: str) -> Optional[PullRequestInfo]:
        """Extract PR information from URL."""
        try:
            # Extract PR number from URL
            pr_number = int(pr_url.split('/')[-1])
            
            # Get PR info using GitHub CLI
            if not self._is_gh_cli_available():
                return None
            
            pr_cmd = ['gh', 'pr', 'view', str(pr_number), '--json', 'title,body,headRefName,baseRefName,state,url,createdAt']
            
            env = os.environ.copy()
            if self.github_token:
                env['GITHUB_TOKEN'] = self.github_token
            
            pr_result = subprocess.run(
                pr_cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                env=env,
                check=False
            )
            
            if pr_result.returncode != 0:
                return None
            
            pr_data = json.loads(pr_result.stdout)
            
            return PullRequestInfo(
                number=pr_number,
                title=pr_data['title'],
                body=pr_data['body'],
                source_branch=pr_data['headRefName'],
                target_branch=pr_data['baseRefName'],
                state=pr_data['state'],
                url=pr_data['url'],
                created_at=datetime.fromisoformat(pr_data['createdAt'].replace('Z', '+00:00'))
            )
            
        except Exception as e:
            logger.warning(f"Failed to get PR info from URL {pr_url}: {e}")
            return None