"""
Core integration management module.
Provides GitHub workflow automation and integration management.
"""

from .github_workflow_manager import GitHubWorkflowManager, WorkflowResult, BranchInfo, PullRequestInfo

__all__ = ['GitHubWorkflowManager', 'WorkflowResult', 'BranchInfo', 'PullRequestInfo']