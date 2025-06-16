# AGENT ARCHITECTURE

Detailed specifications for agent workspace management and lifecycle in the Power Builder multi-agent system.

## WORKSPACE MANAGEMENT

### Directory Structure:
```
agents/
├── {agent-id}/                    # Unique agent workspace
│   ├── plan.md                   # Execution plan from orchestrator
│   ├── power/                    # Fresh clone of azorel/power
│   │   ├── .git/                 # Independent git repository
│   │   ├── CLAUDE.md             # System guidance
│   │   ├── modules/              # Feature modules
│   │   ├── tests/                # Test suites
│   │   └── requirements.txt      # Dependencies
│   ├── venv/                     # Isolated virtual environment
│   │   ├── bin/                  # Virtual environment binaries
│   │   ├── lib/                  # Python libraries
│   │   └── pyvenv.cfg            # Environment configuration
│   ├── logs/                     # Agent-specific logging
│   │   ├── execution.log         # Task execution logs
│   │   ├── test.log              # Testing logs
│   │   └── error.log             # Error tracking
│   └── output/                   # Work submission area
│       ├── changes.json          # Change summary
│       ├── diff.patch            # Git diff package
│       └── validation.json       # Quality gate results
```

### Agent ID Generation:
```bash
AGENT_ID=$(date +%s)-$(uuidgen | cut -d'-' -f1)
# Format: timestamp-uuid_prefix (e.g., 1703123456-a1b2c3d4)
```

## AGENT LIFECYCLE

### Phase 1: Initialization (Branch-Based)
```bash
# 1. Create workspace
mkdir -p agents/${AGENT_ID}
cd agents/${AGENT_ID}

# 2. Fresh repository clone
git clone https://github.com/azorel/power.git
cd power/

# 3. Create feature branch for agent work
TASK_ID=$(echo "${AGENT_ID}" | cut -d'-' -f1)
git checkout -b feature/agent-${TASK_ID}

# 4. Virtual environment setup
python -m venv ../venv
source ../venv/bin/activate

# 4. Dependency installation
pip install -r requirements.txt

# 5. Logging initialization
mkdir -p ../logs
```

### Phase 2: Plan Execution
1. **Read plan.md**: Understand task requirements and approach
2. **Code Analysis**: Examine existing codebase patterns
3. **Implementation**: Follow plan with infinite agentic capabilities
4. **Testing**: Execute 7-test validation protocol
5. **Documentation**: Update docstrings and comments

### Phase 3: Quality Validation
Execute optimized testing protocol:
1. **Tests 1-2**: Standard development testing
2. **Test 3**: Perplexity research trigger (if needed)
3. **Tests 4-5**: Post-research validation
4. **Tests 6-7**: Final confirmation

### Phase 4: Work Submission
Generate submission package:
```json
{
  "agent_id": "1703123456-a1b2c3d4",
  "task_id": "implement-feature-xyz",
  "branch_name": "feature/agent-1703123456",
  "timestamp": "2024-01-01T12:00:00Z",
  "status": "success",
  "changes": {
    "files_modified": ["module/feature.py", "tests/test_feature.py"],
    "files_added": ["docs/feature_guide.md"],
    "files_deleted": ["deprecated/old_feature.py"]
  },
  "validation_results": {
    "tests_passed": true,
    "test_count": 25,
    "pylint_score": "10.00/10",
    "manual_verification": true,
    "cross_validation_ready": true
  },
  "git_info": {
    "branch_name": "feature/agent-1703123456",
    "commit_hash": "abc123def456",
    "rollback_hash": "def456abc123",
    "pr_ready": true
  },
  "metrics": {
    "execution_time": 1800,
    "test_execution_time": 45,
    "lines_added": 150,
    "lines_removed": 30
  }
}
```

### Phase 5: Cleanup (Branch-Based)
After successful PR merge:
```bash
# 1. Deactivate environment
deactivate

# 2. Remove workspace
cd ../../..
rm -rf agents/${AGENT_ID}

# 3. Integration worker cleans up feature branch
git push origin --delete feature/agent-${TASK_ID}

# 4. Update orchestrator tracking
```

## PLAN.MD STRUCTURE

### Template Format:
```markdown
# Task: {Task Name}

## Overview
Brief description of the task and expected outcomes.

## Requirements
- Specific requirement 1
- Specific requirement 2
- Quality gates and constraints

## Approach
### Phase 1: Analysis
- Understand existing code patterns
- Identify integration points
- Plan implementation strategy

### Phase 2: Implementation
- Step-by-step implementation plan
- File-by-file changes required
- Testing strategy

### Phase 3: Validation
- Testing protocol steps
- Quality assurance checks
- Integration preparation

## Expected Deliverables
- List of files to be modified/created
- Test coverage requirements
- Documentation updates

## Success Criteria
- All tests pass (100% success rate)
- Pylint score 10/10
- Manual verification steps
- Cross-validation compatibility

## Notes
- Special considerations
- Potential challenges
- Fallback strategies
```

## ISOLATION PRINCIPLES

### Environment Isolation:
- **Separate Virtual Environment**: Each agent has independent Python environment
- **Fresh Repository Clone**: Clean starting state for every task
- **Isolated Dependencies**: No cross-contamination between agents
- **Independent Logging**: Separate log files per agent

### Process Isolation:
- **Unique Workspace**: No shared files between concurrent agents
- **Independent Git State**: Each agent works with fresh git history
- **Separate Test Execution**: No interference between parallel test runs
- **Isolated Resource Usage**: Memory and CPU tracking per agent

### Communication Isolation:
- **Structured Reporting**: Standardized JSON communication with orchestrator
- **No Inter-Agent Communication**: Agents cannot directly interact
- **Orchestrator Mediation**: All coordination through central orchestrator
- **Clean Handoffs**: Well-defined submission and cleanup protocols

## ERROR HANDLING

### Workspace Corruption:
- **Automatic Recovery**: Re-create workspace from scratch
- **State Restoration**: Fresh clone and environment setup
- **Progress Tracking**: Resume from last known good state
- **Failure Reporting**: Detailed diagnostics to orchestrator

### Resource Conflicts:
- **Unique Identifiers**: Prevent naming collisions
- **Resource Monitoring**: Track memory and disk usage
- **Cleanup Verification**: Ensure complete resource release
- **Conflict Resolution**: Orchestrator-mediated resource allocation

### Integration Failures:
- **Rollback Capability**: Revert to pre-agent state
- **Diagnostic Capture**: Full error context preservation
- **Alternative Strategies**: Fallback to different implementation approach
- **Learning Integration**: Pattern recognition for future prevention

## PERFORMANCE OPTIMIZATION

### Workspace Efficiency:
- **Lazy Loading**: Only clone necessary repository components
- **Cached Dependencies**: Reuse common Python packages where safe
- **Parallel Setup**: Concurrent workspace initialization
- **Quick Cleanup**: Optimized removal procedures

### Resource Management:
- **Memory Monitoring**: Track agent memory consumption
- **Disk Space Management**: Automatic cleanup of temporary files
- **CPU Allocation**: Fair resource distribution among concurrent agents
- **Network Optimization**: Efficient git operations and package downloads

### Concurrent Operation:
- **Independent Execution**: No blocking between agents
- **Asynchronous Reporting**: Non-blocking communication with orchestrator
- **Parallel Testing**: Simultaneous test execution across agents
- **Load Balancing**: Dynamic agent distribution based on system capacity

This architecture ensures complete isolation, reliable execution, and efficient resource utilization for the Power Builder multi-agent system.