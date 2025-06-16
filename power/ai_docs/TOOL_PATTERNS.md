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

## INTEGRATION WITH AGENT WORKFLOW

### Pre-Tool-Call Checklist
Before executing any tool call, agents should:
1. **Reference Patterns**: Check this document for similar operations
2. **Apply Best Practices**: Use proven successful patterns
3. **Avoid Known Failures**: Check failed patterns section
4. **Plan Error Recovery**: Identify likely correction steps

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