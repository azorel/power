# TOOL PATTERNS

Intelligent pattern learning system for consistent tool usage across all agents, featuring automatic error detection and correction guidance.

## SUCCESSFUL PATTERNS

### Bash Tool

#### File Path Handling

- ✅ `cd "path with spaces"` - Always quote paths containing spaces
- ✅ `python "/absolute/path/script.py"` - Use absolute paths with quotes
- ✅ `mkdir -p "parent dir/child dir"` - Create nested directories safely
- ✅ `cp "source file.txt" "destination dir/"` - Quote both source and destination

#### Multi-Command Operations

- ✅ `command1 && command2` - Sequential execution with failure stop
- ✅ `command1 ; command2` - Sequential execution regardless of failure
- ✅ `(cd dir && command)` - Subshell for directory-specific operations
- ✅ `command1 | command2` - Pipe operations for data flow

#### Git Operations (Branch-Based Workflow)

- ✅ Create feature branch:

```bash
git checkout -b feature/agent-{task-id}
```

- ✅ Git commit with heredoc:

```bash
git commit -m "$(cat <<'EOF'
Agent {task-id}: [Description]

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

- ✅ `git add .` - Stage all changes before commit
- ✅ `git status` - Always check status before operations
- ✅ `git diff --staged` - Review staged changes before commit
- ✅ `git push -u origin feature/agent-{task-id}` - Push feature branch
- ✅ `gh pr create --title "Agent Task: {description}" --body "PR description"` - Create PR

#### Environment & Dependencies

- ✅ `source venv/bin/activate` - Activate virtual environment
- ✅ `pip install -r requirements.txt` - Install dependencies from file
- ✅ `python -m venv venv` - Create virtual environment
- ✅ `which python` - Verify Python executable location

#### Testing & Validation

- ✅ `pytest -v` - Verbose test output for debugging
- ✅ `pylint file.py` - Code quality checking
- ✅ `pytest --tb=long` - Detailed traceback for failures
- ✅ `python -m pytest tests/` - Module-based test execution

## FAILED PATTERNS → CORRECTIONS

### Bash Tool Common Errors

#### Path Handling Issues

- ❌ `cd path with spaces` → ✅ `cd "path with spaces"`
- ❌ `python script with spaces.py` → ✅ `python "script with spaces.py"`
- ❌ `./relative/path/script.py` → ✅ `/absolute/path/script.py`
- ❌ `mkdir parent/child` → ✅ `mkdir -p "parent/child"`

#### Git Command Errors

- ❌ `git commit -m "Simple message"` → ✅ Use heredoc format for consistency
- ❌ `git add file.py` → ✅ `git add .` for comprehensive staging
- ❌ Direct commit without status → ✅ Always run `git status` first
- ❌ Commit without diff review → ✅ Run `git diff --staged` first
- ❌ Direct commit to main → ✅ Always work on feature branches
- ❌ `git push origin main` → ✅ `git push origin feature/agent-{task-id}`

#### Rollback & Recovery Errors

- ❌ `git reset --hard HEAD~1` without backup → ✅ Use `git revert` for safe rollback
- ❌ Direct force push to main → ✅ Use `git push --force-with-lease` on features only
- ❌ Manual merge conflict resolution → ✅ Use PR-based conflict resolution

#### Tool Availability Errors
<<<<<<< HEAD
=======

>>>>>>> 76cde24 (Implement comprehensive pre-commit hooks system with smart 3-test cycle)
- ❌ `gh pr create` without verification → ✅ Check `which gh` first, use manual workflow fallback
- ❌ `./gh_2.74.1_linux_amd64/bin/gh` (path doesn't exist) → ✅ Verify path before using
- ❌ Assuming documented tools exist → ✅ Always verify tool availability before execution
- ❌ No fallback for missing tools → ✅ Always have manual alternative workflow

#### Environment Setup Errors

- ❌ `pip install package` → ✅ Ensure virtual environment activated first
- ❌ `python script.py` without venv → ✅ Activate venv, then run
- ❌ Global package installation → ✅ Always use virtual environments
- ❌ Missing requirements.txt → ✅ Install from requirements file

#### Multi-Command Issues

- ❌ Using newlines in bash commands → ✅ Use `&&` or `;` separators
- ❌ `cd dir \n command` → ✅ `cd dir && command`
- ❌ Long command strings → ✅ Break into logical && chains
- ❌ Ignoring command failures → ✅ Use && for failure-aware execution

## ERROR PATTERN DETECTION

### Auto-Learning System

The system automatically detects these error patterns from agent logs:

#### Common Error Signatures

- **Path Errors**: "No such file or directory" with unquoted paths
- **Git Errors**: Commit message formatting issues
- **Environment Errors**: ModuleNotFoundError without venv activation
- **Permission Errors**: Access denied on file operations

#### Learning Triggers

- Tool call failure followed by successful correction
- Repeated error patterns across multiple agents
- Research-triggered solutions from Perplexity integration
- Manual pattern identification during quality review

#### Pattern Update Protocol

1. **Error Detection**: System identifies tool call failure
2. **Correction Analysis**: Parse successful follow-up command
3. **Pattern Extraction**: Identify reusable correction pattern
4. **Database Update**: Add new pattern to this document
5. **Validation**: Test pattern with similar scenarios

## PRE-FLIGHT VALIDATION SYSTEM

### Tool Availability Validation
<<<<<<< HEAD
=======

>>>>>>> 76cde24 (Implement comprehensive pre-commit hooks system with smart 3-test cycle)
```bash
# ✅ Always verify tools before using
validate_tool() {
    if command -v "$1" &> /dev/null; then
        echo "✅ $1 available"
        return 0
    else
        echo "❌ $1 not found, using fallback"
        return 1
    fi
}

# Example usage:
if validate_tool "gh"; then
    gh pr create --title "..." --body "..."
else
    # Manual workflow fallback
    git checkout master && git merge feature/branch-name
fi
```

### Path Validation Patterns
<<<<<<< HEAD
=======

>>>>>>> 76cde24 (Implement comprehensive pre-commit hooks system with smart 3-test cycle)
```bash
# ✅ Verify paths exist before operations
validate_path() {
    if [[ -e "$1" ]]; then
        echo "✅ Path exists: $1"
        return 0
    else
        echo "❌ Path not found: $1"
        return 1
    fi
}

# ✅ Auto-quote paths with spaces
safe_path() {
    if [[ "$1" =~ [[:space:]] ]]; then
        echo "\"$1\""
    else
        echo "$1"
    fi
}
```

### Environment Validation
<<<<<<< HEAD
=======

>>>>>>> 76cde24 (Implement comprehensive pre-commit hooks system with smart 3-test cycle)
```bash
# ✅ Check virtual environment status
check_venv() {
    if [[ -n "$VIRTUAL_ENV" ]]; then
        echo "✅ Virtual environment active: $VIRTUAL_ENV"
        return 0
    else
        echo "❌ No virtual environment active"
        return 1
    fi
}

# ✅ Verify correct directory
check_directory() {
    if [[ -f "CLAUDE.md" ]]; then
        echo "✅ In correct project directory"
        return 0
    else
        echo "❌ Not in project root directory"
        return 1
    fi
}
```

## AUTONOMOUS ERROR RESOLUTION SYSTEM

### Perplexity Research Integration
<<<<<<< HEAD
When tool calls fail and no pattern exists:

#### Research Trigger Protocol
```python
def handle_tool_error(tool_name, command, error_message):
    """Handle tool call errors with autonomous research."""
    
    # 1. Check existing patterns first
    if pattern_exists(tool_name, error_message):
        return apply_known_pattern(tool_name, error_message)
    
    # 2. Trigger Perplexity research automatically
    research_query = f"""
    TOOL CALL ERROR RESOLUTION REQUEST
    
=======

When tool calls fail and no pattern exists:

#### Research Trigger Protocol

```python
def handle_tool_error(tool_name, command, error_message):
    """Handle tool call errors with autonomous research."""

    # 1. Check existing patterns first
    if pattern_exists(tool_name, error_message):
        return apply_known_pattern(tool_name, error_message)

    # 2. Trigger Perplexity research automatically
    research_query = f"""
    TOOL CALL ERROR RESOLUTION REQUEST

>>>>>>> 76cde24 (Implement comprehensive pre-commit hooks system with smart 3-test cycle)
    Error Context:
    - Tool: {tool_name}
    - Command: {command}
    - Error: {error_message}
    - Environment: {get_environment_info()}
    - Working Directory: {os.getcwd()}
<<<<<<< HEAD
    
    Previous Attempts:
    - Checked TOOL_PATTERNS.md: No matching pattern found
    
    Required: Provide specific command fix or alternative approach.
    Include verification steps and fallback options.
    """
    
    # 3. Apply research solution
    solution = perplexity_research(research_query)
    
=======

    Previous Attempts:
    - Checked TOOL_PATTERNS.md: No matching pattern found

    Required: Provide specific command fix or alternative approach.
    Include verification steps and fallback options.
    """

    # 3. Apply research solution
    solution = perplexity_research(research_query)

>>>>>>> 76cde24 (Implement comprehensive pre-commit hooks system with smart 3-test cycle)
    # 4. Test and validate solution
    if test_solution(solution):
        # 5. Update patterns with successful solution
        update_tool_patterns(tool_name, error_message, solution)
        return solution
    else:
        # 6. Escalate to user only if research fails
        return escalate_to_user(tool_name, error_message, solution)
```

#### Auto-Learning Protocol
<<<<<<< HEAD
```python
def update_tool_patterns(tool_name, error_signature, solution):
    """Automatically update TOOL_PATTERNS.md with successful solutions."""
    
=======

```python
def update_tool_patterns(tool_name, error_signature, solution):
    """Automatically update TOOL_PATTERNS.md with successful solutions."""

>>>>>>> 76cde24 (Implement comprehensive pre-commit hooks system with smart 3-test cycle)
    new_pattern = {
        'error': error_signature,
        'solution': solution,
        'source': 'perplexity_research',
        'success_rate': 1.0,
        'timestamp': datetime.now().isoformat()
    }
<<<<<<< HEAD
    
    # Add to appropriate error category
    add_pattern_to_category(tool_name, new_pattern)
    
=======

    # Add to appropriate error category
    add_pattern_to_category(tool_name, new_pattern)

>>>>>>> 76cde24 (Implement comprehensive pre-commit hooks system with smart 3-test cycle)
    # Commit pattern update
    commit_pattern_update(f"Add {tool_name} error pattern from research")
```

### Error Resolution Hierarchy
<<<<<<< HEAD
=======

>>>>>>> 76cde24 (Implement comprehensive pre-commit hooks system with smart 3-test cycle)
1. **Pattern Match**: Check TOOL_PATTERNS.md for known solutions
2. **Auto-Research**: Trigger Perplexity research for novel errors
3. **Solution Testing**: Validate research suggestions automatically
4. **Pattern Learning**: Update database with successful solutions
5. **User Escalation**: Only when all automation fails

## INTEGRATION WITH AGENT WORKFLOW

### Enhanced Pre-Tool-Call Checklist
<<<<<<< HEAD
=======

>>>>>>> 76cde24 (Implement comprehensive pre-commit hooks system with smart 3-test cycle)
Before executing any tool call, agents should:

1. **Reference Patterns**: Check this document for similar operations
2. **Run Validation**: Execute pre-flight checks for tool/path/environment
3. **Apply Best Practices**: Use proven successful patterns
4. **Avoid Known Failures**: Check failed patterns section
5. **Enable Auto-Research**: Allow Perplexity research for novel errors
6. **Plan Error Recovery**: Identify likely correction steps

### Pattern Application Flow

```bash
# Example: Git commit operation
# 1. Check patterns for git commit
# 2. Apply heredoc format (successful pattern)
# 3. Include status check (best practice)
# 4. Stage all changes (comprehensive approach)

git status
git add .
git diff --staged
git commit -m "$(cat <<'EOF'
Add new feature implementation

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

### Error Recovery Protocol

When tool calls fail despite pattern guidance:

1. **Immediate Analysis**: Compare failed command to patterns
2. **Pattern Matching**: Identify similar error in database
3. **Apply Correction**: Use documented successful pattern
4. **Update Database**: Add new pattern if novel error discovered
5. **Validate Solution**: Ensure correction resolves issue

## INTELLIGENT PATTERN LEARNING

### Log Analysis Integration

System continuously analyzes agent logs for:

- **Error Frequencies**: Most common tool call failures
- **Success Patterns**: Consistently successful command formats
- **Context Dependencies**: Environment-specific requirements
- **Time Correlations**: Patterns that emerge over time

### Research Integration

When Perplexity research is triggered (Test 3 in testing protocol):

- **Solution Capture**: Extract actionable command patterns from research
- **Pattern Validation**: Test research-derived patterns in practice
- **Database Integration**: Add validated research patterns to database
- **Success Tracking**: Monitor effectiveness of research-derived patterns

### Cross-Agent Learning

Patterns learned by one agent benefit all subsequent agents:

- **Shared Knowledge**: All agents access same pattern database
- **Collaborative Learning**: Error corrections propagate system-wide
- **Consistency Enforcement**: Standardized tool usage across agents
- **Quality Improvement**: Reduced error rates through shared experience

## QUALITY METRICS

### Pattern Effectiveness Tracking

- **Error Reduction Rate**: Percentage decrease in repeated errors
- **First-Pass Success**: Tool calls succeeding without correction
- **Pattern Usage**: Frequency of pattern consultation before tool calls
- **Discovery Rate**: New patterns learned per development cycle

### Continuous Improvement

- **Pattern Refinement**: Update patterns based on effectiveness data
- **Coverage Expansion**: Add patterns for new tool types and scenarios
- **Obsolete Pattern Removal**: Remove patterns that become ineffective
- **Performance Optimization**: Streamline pattern lookup and application

This intelligent pattern learning system ensures consistent, error-free tool usage while continuously improving through real-world agent experience.
