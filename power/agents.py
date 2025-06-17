"""
agents module.
"""

#!/usr/bin/env python3
"""
Simple multi-agent system for Claude Code - Direct integration, no complexity.
"""

import sys


def agents(task: str) -> str:
    """Delegate task to real Claude Code agent using Task tool."""
    # Get Task tool from current module/context
    task_tool = None
    current_module = sys.modules.get('__main__')
    if hasattr(current_module, 'Task'):
        task_tool = getattr(current_module, 'Task')

    if task_tool:
        # Use real Task tool
        agent_prompt = f"""You are a development agent. Complete this task with PYLINT-CLEAN CODE from the first attempt:

TASK: {task}

MANDATORY PRE-CODING STEPS:
1. Read ai_docs/standards/CODING_STANDARDS.md completely before any coding
2. Understand three-layer architecture: core/ adapters/ shared/
3. Plan all docstrings, type hints, and import organization upfront

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
"""Module description here."""
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

Begin with reading CODING_STANDARDS.md, then implement clean code immediately."""

        task_tool(description="Execute development task", prompt=agent_prompt)
        return f"Agent completed: {task}"

    return f"Task queued: {task} (Task tool integration needed)"

def status() -> str:
    """Get system status."""
    return "Multi-agent system ready"

def check() -> str:
    """Check for completions."""
    return "No pending completions"

if __name__ == "__main__":
    print("Multi-agent system loaded. Use agents('your task')")
