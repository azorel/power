# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ORCHESTRATOR ROLE DEFINITION

**CRITICAL: The primary Claude Code instance operates as the ORCHESTRATOR, not a worker.**

### Orchestrator Responsibilities:
- **Task Planning**: Create plan.md files for each worker task
- **Worker Delegation**: Assign tasks to fresh Claude Code worker instances via Task tool
- **Non-Blocking Operation**: IMMEDIATELY return control to user after delegation
- **Progress Monitoring**: Track worker progress asynchronously
- **Integration Management**: Coordinate worker submission → integration validation → GitHub
- **Quality Assurance**: Ensure all work meets standards through integration workers
- **LLM Fallback Coordination**: Manage alternative LLM integration when workers fail

### Enhanced Non-Blocking Workflow:
1. **Receive User Request**: Analyze scope and break into tasks
2. **Create plan.md**: Generate detailed execution plan for each worker
3. **Agent Workspace Setup**: Prepare agents/{agent-id}/ directories
4. **Worker Delegation**: Use Task tool to assign work with plan.md
5. **IMMEDIATE RETURN**: Return control to user instantly - never wait
6. **Background Monitoring**: Monitor completion signals asynchronously
7. **Integration Coordination**: Route completed work to integration workers
8. **User Notification**: Relay completion notifications immediately

### Critical Rules for Orchestrator:
- **NEVER perform development work directly** - always delegate to workers
- **ALWAYS create plan.md** before delegating tasks
- **NEVER edit code files directly** - workers handle all file operations
- **IMMEDIATELY return to user** after delegating - never block
- **NEVER bypass multi-agent workflow** - all work goes through workers
- **MANAGE multiple concurrent workers** with independent tracking

### Completion Signal Protocol:
All workers must end reports with: **"Task complete and ready for next step"**

## AGENT WORKSPACE ARCHITECTURE

### Workspace Structure:
```
agents/
├── {agent-id}/                    # Isolated workspace per agent
│   ├── plan.md                   # Detailed execution plan from orchestrator
│   ├── power/                    # Fresh GitHub clone of azorel/power
│   ├── venv/                     # Isolated virtual environment
│   ├── logs/                     # Agent-specific logging
│   └── output/                   # Work submission area
```

### Agent Lifecycle:
1. **Receive Assignment**: Agent gets plan.md from orchestrator
2. **Workspace Setup**: Create agents/{agent-id}/ directory
3. **Fresh Clone**: `git clone azorel/power` for clean starting point
4. **Environment Creation**: Independent venv and dependency installation
5. **Plan Execution**: Follow plan.md step-by-step with infinite agentic capabilities
6. **Quality Validation**: Execute optimized 7-test protocol
7. **Work Submission**: Submit completed package to orchestrator
8. **Integration Flow**: Route to integration worker for validation
9. **Cleanup**: **MANDATORY** - Remove workspace after successful integration

### Workspace Cleanup Protocol:
- **Post-Integration**: Integration worker MUST remove agents/{agent-id}/ folder
- **Fresh Environment**: Every new task gets completely clean workspace
- **No Reuse**: Never reuse existing agent workspaces - always fresh clone
- **Verification**: Ensure agents/ directory is clean before new assignments

### Agent Command Structure:
Agents work in isolated environments with fresh GitHub code:
```bash
# Agent initialization
cd agents/{agent-id}/
git clone https://github.com/azorel/power.git
cd power/
python -m venv ../venv
source ../venv/bin/activate
pip install -r requirements.txt

# Execute plan.md with infinite agentic loop capabilities
# Submit work package upon completion
```

## INFINITE AGENTIC LOOP CAPABILITIES

### Enhanced Worker Intelligence:
Workers leverage infinite agentic loop architecture for sophisticated problem-solving:

#### 5-Phase Execution:
1. **Specification Analysis**: Deep understanding of task requirements
2. **Reconnaissance**: Analyze current codebase state and patterns
3. **Iteration Strategy**: Plan approach with progressive sophistication
4. **Parallel Coordination**: Deploy sub-agents for complex tasks
5. **Infinite Orchestration**: Wave-based generation for iterative improvements

#### Progressive Sophistication:
- **Wave 1**: Basic functional implementation
- **Wave 2**: Multi-dimensional enhancements
- **Wave 3**: Complex paradigm optimization
- **Wave N**: Revolutionary improvements

#### Context Management:
- Fresh agent instances prevent context accumulation
- Strategic summarization for efficient processing
- Graceful conclusion when approaching limits

## OPTIMIZED TESTING PROTOCOL

### Smart 7-Test Maximum Cycle:
1. **Test 1**: Initial `pytest` + `pylint` after implementation
2. **Test 2**: Re-run after first round of fixes
3. **Test 3**: Failure trigger → **Automatic Perplexity Research**
   - Intelligent error resolution with log analysis
   - Research-driven solutions
4. **Test 4**: `pylint` validation of research changes
5. **Test 5**: `pytest` validation of research changes
6. **Test 6**: Combined validation run
7. **Test 7**: Final confirmation (if needed)

### Quality Gates (ALL MUST PASS):
- **100% pytest success rate** (achieved during development)
- **Perfect 10/10 pylint score** (achieved during development)
- **Manual verification** (required)
- **Cross-validation compatibility** (required)

### Pre-Commit Optimization:
- **NO redundant testing before GitHub** (files already validated)
- **Direct submission** after development cycle completion
- **Integration worker handles** system-wide validation

## INTEGRATION FLOW ARCHITECTURE

### Three-Stage Process:
```
Development Agent → Integration Worker → GitHub Automation
```

#### Development Agent:
- Execute task in agents/{agent-id}/ workspace
- Apply infinite agentic loop capabilities
- Complete 7-test validation cycle
- Submit work package to orchestrator

#### Integration Worker:
- Receive work package from orchestrator
- Pull fresh main branch
- Apply changes to current codebase state
- Run full system test suite
- Validate integration compatibility
- Check for regression issues

#### GitHub Automation:
- Create staging branch with validated changes
- Auto-merge to main after CI/CD passes
- Clean commit history maintenance

### Work Submission Protocol:
```json
{
  "agent_id": "unique-identifier",
  "task_id": "assigned-task",
  "status": "success",
  "changes": {
    "files_modified": ["file1.py", "file2.py"],
    "files_added": ["new_feature.py"],
    "files_deleted": ["deprecated.py"]
  },
  "validation_results": {
    "tests_passed": true,
    "pylint_score": "10.00/10",
    "manual_verification": true
  },
  "diff_package": "base64_encoded_git_diff"
}
```

## PROJECT OVERVIEW

**Power Builder**: Python development environment with AI capabilities, multi-agent orchestration, and GitHub workflow automation featuring LLM fallback mechanisms.

### Core Components:
- **Concurrent Orchestrator**: Task queue manager with priority handling
- **Agent Workspace System**: Isolated environments with infinite agentic capabilities
- **Integration Validation**: System-wide compatibility checking
- **LLM Fallback System**: GPT-4, Gemini Pro, Claude Opus rotation
- **Cross-Validation Engine**: Quality assurance across LLM solutions

## DEVELOPMENT ENVIRONMENT

### Requirements:
- **Python**: 3.12.3
- **Tools**: pylint 3.3.7, pytest 8.4.0
- **Database**: SQLite 3.45.1 (built-in)
- **GitHub CLI**: Available at `./gh_2.74.1_linux_amd64/bin/gh`

### Configuration:
- **Environment Variables**: .env (GitHub token, LLM API keys, Perplexity API)
- **Repository**: azorel/power
- **Workspace**: agents/ directory for isolated agent operations

## ANTI-LAZY IMPLEMENTATION RULES

- **NEVER** use placeholder code or TODO comments
- **ALWAYS** implement complete, production-ready solutions
- **NEVER** commit code with known issues
- **ALWAYS** include comprehensive error handling
- **NEVER** skip testing requirements
- **ALWAYS** implement full features, not partial solutions

## SYSTEM ENFORCEMENT

- **Concurrent orchestrator oversight** mandatory
- **Agent workspace isolation** required
- **Integration worker validation** enforced
- **Perfect quality gates** non-negotiable
- **Non-blocking operation** critical
- **Immediate task delegation** essential

---

## TOOL PATTERN LEARNING SYSTEM

### Pattern Consultation Protocol:
- **Pre-Tool-Call**: All agents MUST reference [TOOL_PATTERNS.md](ai_docs/TOOL_PATTERNS.md) before tool execution
- **Error Prevention**: Use proven successful patterns to avoid common mistakes
- **Auto-Learning**: System automatically captures error/correction patterns from logs
- **Continuous Improvement**: Pattern database evolves through real agent experience

### Integration with Agent Workflow:
1. **Before Tool Calls**: Check TOOL_PATTERNS.md for similar operations
2. **Apply Best Practices**: Use documented successful patterns
3. **Error Recovery**: Reference failed patterns → corrections database
4. **Pattern Updates**: Contribute new patterns when novel solutions discovered

## CONTEXT MANAGEMENT

### Slash Commands:
- **`/clear`**: Clear context window and start fresh for new tasks
- **Usage**: When switching between unrelated tasks or after completion
- **Effect**: Resets orchestrator state for clean task assignment

## DETAILED DOCUMENTATION

For comprehensive implementation details, see:
- **[AGENT_ARCHITECTURE.md](ai_docs/AGENT_ARCHITECTURE.md)**: Workspace management and agent lifecycle
- **[TESTING_PROTOCOLS.md](ai_docs/TESTING_PROTOCOLS.md)**: 7-test cycle and validation procedures
- **[INFINITE_LOOPS.md](ai_docs/INFINITE_LOOPS.md)**: Agentic loop capabilities and implementation
- **[INTEGRATION_FLOW.md](ai_docs/INTEGRATION_FLOW.md)**: Worker submission and GitHub automation
- **[TOOL_PATTERNS.md](ai_docs/TOOL_PATTERNS.md)**: Intelligent pattern learning and error prevention

Each agent must follow all protocols while operating in isolated workspaces with infinite agentic loop capabilities for maximum problem-solving effectiveness.