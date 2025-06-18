"""
Enhanced multi-agent orchestration system.
Integrates workspace management with Task tool delegation.
"""

import sys
from typing import Optional, Dict, Any, List
from pathlib import Path

# Import workspace management
try:
    from core.workspace.agent_workspace_manager import AgentWorkspaceManager, WorkspaceConfig
    WORKSPACE_AVAILABLE = True
    AgentWorkspaceManagerType = AgentWorkspaceManager
except ImportError:
    WORKSPACE_AVAILABLE = False
    AgentWorkspaceManagerType = None


# Global workspace manager instance
_workspace_manager = None


def get_workspace_manager():
    """Get or create workspace manager instance."""
    global _workspace_manager
    if _workspace_manager is None and WORKSPACE_AVAILABLE:
        _workspace_manager = AgentWorkspaceManager()
    return _workspace_manager


def agents(task: str, use_workspace: bool = True, task_type: str = "development") -> str:
    """
    Delegate task to real Claude Code agent with optional workspace isolation.
    
    Args:
        task: Description of task to be completed
        use_workspace: Whether to create isolated workspace for agent
        task_type: Type of task (development, research, integration, testing)
        
    Returns:
        Status message indicating task delegation result
    """
    # Get Task tool from current module/context
    task_tool = None
    current_module = sys.modules.get('__main__')
    if hasattr(current_module, 'Task'):
        task_tool = getattr(current_module, 'Task')

    if not task_tool:
        return f"Task queued: {task} (Task tool integration needed)"

    # Setup workspace if requested and available
    workspace_info = ""
    if use_workspace and WORKSPACE_AVAILABLE:
        try:
            workspace_manager = get_workspace_manager()
            if workspace_manager:
                workspace_config = workspace_manager.create_workspace(task, task_type)
                workspace_info = f"""
WORKSPACE ENVIRONMENT:
- Agent ID: {workspace_config.agent_id}
- Task ID: {workspace_config.task_id}
- Workspace Path: {workspace_config.workspace_path}
- Feature Branch: {workspace_config.feature_branch}
- Plan File: Available at workspace_path/plan.md

WORKSPACE SETUP COMPLETE:
1. Fresh GitHub clone created in workspace_path/power/
2. Feature branch '{workspace_config.feature_branch}' created
3. Virtual environment available at workspace_path/venv/
4. Task plan documented in workspace_path/plan.md
5. Dependencies installed and ready

WORK IN ISOLATED ENVIRONMENT:
- Use the workspace_path/power/ directory for all development
- Commit changes to feature branch when complete
- Follow the plan.md execution strategy
"""
        except Exception as e:
            workspace_info = f"\nWARNING: Workspace creation failed: {e}\nProceeding without workspace isolation.\n"

    # Determine required standards based on task type
    standards_mapping = {
        'development': ['CODING_STANDARDS.md'],
        'coding': ['CODING_STANDARDS.md'],
        'api_integration': ['CODING_STANDARDS.md', 'API_INTEGRATION_STANDARDS.md'],
        'adapter_development': ['CODING_STANDARDS.md', 'API_INTEGRATION_STANDARDS.md'],
        'research': ['RESEARCH_STANDARDS.md'],
        'testing': ['TESTING_STANDARDS.md', 'CODING_STANDARDS.md'],
        'integration': ['INTEGRATION_STANDARDS.md', 'CODING_STANDARDS.md'],
        'pr_creation': ['INTEGRATION_STANDARDS.md', 'CODING_STANDARDS.md'],
        'deployment': ['INTEGRATION_STANDARDS.md', 'CODING_STANDARDS.md']
    }
    
    required_standards = standards_mapping.get(task_type, ['CODING_STANDARDS.md'])
    standards_instructions = "\n".join([
        f"- Read ai_docs/standards/{standard} completely before starting"
        for standard in required_standards
    ])

    # Create comprehensive agent prompt
    agent_prompt = f"""You are a development agent. Complete this task with PYLINT-CLEAN CODE from the first attempt:

TASK: {task}
TASK TYPE: {task_type}

{workspace_info}

MANDATORY PRE-CODING STEPS:
{standards_instructions}
- Understand three-layer architecture: core/ adapters/ shared/
- Plan all docstrings, type hints, and import organization upfront

PYLINT 10/10 REQUIREMENTS (WRITE CLEAN FROM START):
- Module docstring: Triple-quoted description at file top
- Function docstrings: Args, Returns, Raises for every function
- Type hints: All parameters and return types annotated
- Import organization: stdlib → third-party → local with blank lines
- Variable naming: snake_case, descriptive names, no single letters
- Function length: Keep under 15 lines, extract complex logic
- Error handling: Specific exception types, no bare except
- Code complexity: Simple, readable, well-structured

CLEAN CODE PATTERN EXAMPLES:
```python
\"\"\"Module description here.\"\"\"
from typing import List, Dict, Any
import os
from pathlib import Path

def process_data(input_data: List[str], max_length: int = 100) -> Dict[str, Any]:
    \"\"\"
    Process input data with specified constraints.
    
    Args:
        input_data: List of strings to process
        max_length: Maximum allowed length
        
    Returns:
        Dict containing processed results
        
    Raises:
        ValueError: If input_data is empty
    \"\"\"
    if not input_data:
        raise ValueError("Input data cannot be empty")
    # Implementation here
    return {{"processed": len(input_data)}}
```

ARCHITECTURE COMPLIANCE:
- Place files in correct layer (core/adapters/shared)
- Use shared interfaces for external dependencies
- No cross-layer imports (core ↔ adapters forbidden)
- Follow dependency injection patterns

QUALITY GATES (MUST ACHIEVE):
- Perfect 10/10 pylint score on first attempt
- 100% test coverage with proper test structure
- Zero architecture violations
- Complete documentation

PRE-SUBMISSION CHECKLIST:
□ Module docstring present
□ All functions have complete docstrings with Args/Returns/Raises
□ Type hints on all parameters and returns
□ Imports properly organized (stdlib → third-party → local)
□ Variable names descriptive and snake_case
□ Functions under 15 lines each
□ Specific exception handling
□ Architecture layer compliance verified
□ Tests cover all functionality

CRITICAL: Write pylint-compliant code from the start. NO reactive fixing cycles.

End with: "Task complete and ready for next step"

Begin with reading required standards, then implement clean code immediately."""

    # Delegate to Task tool
    task_tool(description=f"Execute {task_type} task", prompt=agent_prompt)
    
    workspace_status = " (with isolated workspace)" if use_workspace and WORKSPACE_AVAILABLE else ""
    return f"Agent delegated: {task}{workspace_status}"

def status() -> str:
    """Get system status including workspace information."""
    status_info = ["Multi-agent system ready"]
    
    if WORKSPACE_AVAILABLE:
        workspace_manager = get_workspace_manager()
        if workspace_manager:
            active_workspaces = workspace_manager.list_active_workspaces()
            status_info.append(f"Workspace manager available: {len(active_workspaces)} active workspaces")
            
            for config in active_workspaces:
                workspace_status = workspace_manager.get_workspace_status(config.agent_id)
                if workspace_status:
                    status_info.append(f"  - {config.agent_id}: {workspace_status.status} ({workspace_status.branch_name})")
        else:
            status_info.append("Workspace manager not initialized")
    else:
        status_info.append("Workspace management not available")
    
    return "\n".join(status_info)


def check() -> str:
    """Check for completions and workspace status."""
    completions = []
    
    if WORKSPACE_AVAILABLE:
        workspace_manager = get_workspace_manager()
        if workspace_manager:
            active_workspaces = workspace_manager.list_active_workspaces()
            
            for config in active_workspaces:
                workspace_status = workspace_manager.get_workspace_status(config.agent_id)
                if workspace_status:
                    if workspace_status.status == "active" and workspace_status.last_commit:
                        completions.append(f"Agent {config.agent_id}: Task in progress (last commit: {workspace_status.last_commit[:8]})")
                    elif workspace_status.status == "error":
                        completions.append(f"Agent {config.agent_id}: Error - {workspace_status.error_message}")
                    else:
                        completions.append(f"Agent {config.agent_id}: {workspace_status.status}")
    
    if not completions:
        return "No active tasks or completions"
    
    return "\n".join(completions)


def list_workspaces() -> str:
    """List all active workspaces with details."""
    if not WORKSPACE_AVAILABLE:
        return "Workspace management not available"
    
    workspace_manager = get_workspace_manager()
    if not workspace_manager:
        return "Workspace manager not initialized"
    
    active_workspaces = workspace_manager.list_active_workspaces()
    
    if not active_workspaces:
        return "No active workspaces"
    
    workspace_info = ["Active Workspaces:"]
    
    for config in active_workspaces:
        workspace_status = workspace_manager.get_workspace_status(config.agent_id)
        
        info = [
            f"\nAgent ID: {config.agent_id}",
            f"Task ID: {config.task_id}", 
            f"Workspace: {config.workspace_path}",
            f"Branch: {config.feature_branch}",
            f"Created: {config.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
        ]
        
        if workspace_status:
            info.extend([
                f"Status: {workspace_status.status}",
                f"Files Modified: {len(workspace_status.files_modified)}",
                f"Last Commit: {workspace_status.last_commit or 'None'}"
            ])
            
            if workspace_status.error_message:
                info.append(f"Error: {workspace_status.error_message}")
        
        workspace_info.extend(info)
    
    return "\n".join(workspace_info)


def cleanup_workspace(agent_id: str, preserve_branch: bool = False) -> str:
    """
    Clean up specific workspace.
    
    Args:
        agent_id: Agent identifier for workspace to clean up
        preserve_branch: Whether to preserve the feature branch
        
    Returns:
        Status message indicating cleanup result
    """
    if not WORKSPACE_AVAILABLE:
        return "Workspace management not available"
    
    workspace_manager = get_workspace_manager()
    if not workspace_manager:
        return "Workspace manager not initialized"
    
    success = workspace_manager.cleanup_workspace(agent_id, preserve_branch)
    
    if success:
        branch_info = " (branch preserved)" if preserve_branch else " (branch cleaned up)"
        return f"Workspace {agent_id} cleaned up successfully{branch_info}"
    else:
        return f"Failed to clean up workspace {agent_id}"


def cleanup_all_workspaces(preserve_branches: bool = False) -> str:
    """
    Clean up all active workspaces.
    
    Args:
        preserve_branches: Whether to preserve feature branches
        
    Returns:
        Status message indicating cleanup results
    """
    if not WORKSPACE_AVAILABLE:
        return "Workspace management not available"
    
    workspace_manager = get_workspace_manager()
    if not workspace_manager:
        return "Workspace manager not initialized"
    
    active_workspaces = workspace_manager.list_active_workspaces()
    
    if not active_workspaces:
        return "No active workspaces to clean up"
    
    cleanup_results = []
    
    for config in active_workspaces:
        success = workspace_manager.cleanup_workspace(config.agent_id, preserve_branches)
        
        if success:
            cleanup_results.append(f"✓ Cleaned up {config.agent_id}")
        else:
            cleanup_results.append(f"✗ Failed to clean up {config.agent_id}")
    
    branch_info = " (branches preserved)" if preserve_branches else " (branches cleaned up)"
    summary = f"Cleaned up {len(active_workspaces)} workspaces{branch_info}"
    
    return f"{summary}\n" + "\n".join(cleanup_results)


def get_workspace_info(agent_id: str) -> str:
    """
    Get detailed information about specific workspace.
    
    Args:
        agent_id: Agent identifier for workspace
        
    Returns:
        Detailed workspace information
    """
    if not WORKSPACE_AVAILABLE:
        return "Workspace management not available"
    
    workspace_manager = get_workspace_manager()
    if not workspace_manager:
        return "Workspace manager not initialized"
    
    workspace_status = workspace_manager.get_workspace_status(agent_id)
    workspace_path = workspace_manager.get_workspace_path(agent_id)
    
    if not workspace_status or not workspace_path:
        return f"Workspace {agent_id} not found"
    
    info = [
        f"Workspace Information for {agent_id}:",
        f"  Task ID: {workspace_status.task_id}",
        f"  Status: {workspace_status.status}",
        f"  Branch: {workspace_status.branch_name}",
        f"  Workspace Path: {workspace_path}",
        f"  Files Modified: {len(workspace_status.files_modified)}",
        f"  Last Commit: {workspace_status.last_commit or 'None'}"
    ]
    
    if workspace_status.error_message:
        info.append(f"  Error: {workspace_status.error_message}")
    
    if workspace_status.files_modified:
        info.append("  Modified Files:")
        for file_path in workspace_status.files_modified:
            info.append(f"    - {file_path}")
    
    # Check if workspace is valid
    is_valid = workspace_manager.validate_workspace(agent_id)
    info.append(f"  Workspace Valid: {is_valid}")
    
    return "\n".join(info)


if __name__ == "__main__":
    print("Enhanced multi-agent system loaded.")
    print("Available functions:")
    print("  - agents(task, use_workspace=True, task_type='development')")
    print("  - status()")
    print("  - check()")
    print("  - list_workspaces()")
    print("  - cleanup_workspace(agent_id, preserve_branch=False)")
    print("  - cleanup_all_workspaces(preserve_branches=False)")
    print("  - get_workspace_info(agent_id)")
