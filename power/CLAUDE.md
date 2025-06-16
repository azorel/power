# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project: Power Builder

A Python development environment with integrated AI capabilities, multi-agent orchestration system, and GitHub workflow automation featuring LLM fallback mechanisms for robust task completion.

## MULTI-AGENT ORCHESTRATOR ARCHITECTURE

### System Architecture Overview
The Power Builder implements a sophisticated multi-agent system with LLM fallback capabilities:

- **Orchestrator Agent**: Central task queue manager with priority levels
- **Worker Agent Pool**: Fresh Claude Code instances with isolated contexts
- **LLM Fallback System**: GPT-4, Gemini Pro, Claude Opus rotation on failures
- **Cross-Validation Engine**: Original Claude worker validates alternative LLM solutions
- **Health Monitoring**: Worker performance tracking and load balancing

### Enhanced Task Flow with Intelligent Error Resolution
1. **Initial Assignment**: Orchestrator assigns task to new Claude Code worker
2. **Worker Execution**: Agent completes requirements with comprehensive logging at every step
3. **Test Execution**: Run full test suite with detailed failure analysis
4. **Intelligent Error Resolution Pipeline** (on test failure):
   - **Log Analysis**: Worker analyzes its own execution logs to identify root cause
   - **Self-Healing Attempt**: Use log insights to implement targeted fixes
   - **Perplexity Research**: Query Perplexity with structured error context for solutions
   - **Research-Driven Fix**: Apply research-based solutions with logging
   - **Re-test Cycle**: Run full test suite again with comprehensive validation
5. **Escalation Logic**: After 3 self-correction attempts, escalate to LLM fallback
6. **LLM Fallback**: Alternative LLM receives error context and research insights
7. **Cross-Validation**: Original Claude worker validates fallback LLM solution
8. **Result Integration**: Only 100% validated solutions with full error resolution are accepted

### Enhanced Worker Agent Specification with Intelligent Error Resolution
Each worker agent operates with:
- **Fresh Claude Code Instance**: Completely isolated context per task
- **Structured Task Payload**: `{task_id, requirements, test_suite, max_attempts, priority, error_context}`
- **Complete Requirements Fulfillment**: ALL specifications must be met before validation
- **Comprehensive Test Execution**: 100% test pass rate required for completion
- **Intelligent Error Resolution Engine**: Self-healing capabilities with log analysis
- **Research Integration**: Perplexity API access for error resolution research
- **Detailed Process Logging**: Full attempt history, failure analysis, and resolution tracking
- **Resource Cleanup**: Automatic cleanup of worker environments on completion/failure

#### **Error Resolution Capabilities**
- **Log-Based Debugging**: Analyze execution logs to identify failure patterns
- **Self-Correction Mechanisms**: Implement targeted fixes based on log insights
- **Research-Enhanced Problem Solving**: Query external knowledge bases for solutions
- **Structured Error Reporting**: Generate comprehensive error reports with context
- **Learning from Failures**: Track successful resolution patterns for future use

## INTELLIGENT ERROR RESOLUTION ARCHITECTURE

### Log-Based Debugging Engine
Each worker implements comprehensive log analysis for self-healing:

#### **Error Pattern Recognition**
```python
def analyze_execution_logs(worker_id, task_id, attempt_num):
    """Analyze worker execution logs to identify failure patterns."""
    logger = logging.getLogger(f'modules.error_resolution.{worker_id}')
    
    # Load execution logs for analysis
    log_file = f"logs/workers/worker-{worker_id}-{datetime.now().strftime('%Y%m%d')}.log"
    
    error_patterns = {
        'import_errors': [],
        'syntax_errors': [],
        'test_failures': [],
        'dependency_issues': [],
        'logic_errors': [],
        'environment_issues': []
    }
    
    logger.info("Starting log analysis for error resolution", extra={
        'worker_id': worker_id,
        'task_id': task_id,
        'attempt_num': attempt_num,
        'log_file': log_file
    })
    
    # Parse logs and categorize errors
    with open(log_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            if '| ERROR |' in line or '| CRITICAL |' in line:
                error_context = extract_error_context(line, line_num)
                categorize_error(error_context, error_patterns)
    
    logger.info("Log analysis completed", extra={
        'worker_id': worker_id,
        'task_id': task_id,
        'attempt_num': attempt_num,
        'error_patterns_found': {k: len(v) for k, v in error_patterns.items()},
        'primary_error_category': identify_primary_error_category(error_patterns)
    })
    
    return error_patterns
```

#### **Self-Healing Implementation**
```python
def attempt_self_healing(worker_id, task_id, attempt_num, error_patterns):
    """Implement self-healing based on log analysis."""
    logger = logging.getLogger(f'modules.error_resolution.{worker_id}')
    
    healing_strategies = {
        'import_errors': fix_import_issues,
        'syntax_errors': fix_syntax_issues,
        'test_failures': analyze_and_fix_test_failures,
        'dependency_issues': resolve_dependency_conflicts,
        'logic_errors': implement_logic_corrections,
        'environment_issues': fix_environment_setup
    }
    
    healing_results = {}
    
    for error_type, errors in error_patterns.items():
        if errors:
            logger.info(f"Attempting self-healing for {error_type}", extra={
                'worker_id': worker_id,
                'task_id': task_id,
                'attempt_num': attempt_num,
                'error_type': error_type,
                'error_count': len(errors)
            })
            
            try:
                healing_result = healing_strategies[error_type](errors)
                healing_results[error_type] = healing_result
                
                logger.info(f"Self-healing completed for {error_type}", extra={
                    'worker_id': worker_id,
                    'task_id': task_id,
                    'attempt_num': attempt_num,
                    'error_type': error_type,
                    'healing_success': healing_result['success'],
                    'fixes_applied': healing_result['fixes_applied']
                })
            except Exception as e:
                logger.error(f"Self-healing failed for {error_type}", extra={
                    'worker_id': worker_id,
                    'task_id': task_id,
                    'attempt_num': attempt_num,
                    'error_type': error_type,
                    'healing_error': str(e),
                    'stack_trace': traceback.format_exc()
                })
                healing_results[error_type] = {'success': False, 'error': str(e)}
    
    return healing_results
```

### Research-Enhanced Error Resolution
When self-healing fails, workers query Perplexity for advanced solutions:

#### **Structured Research Query Format**
```python
def generate_research_query(worker_id, task_id, error_patterns, healing_results):
    """Generate structured research query for Perplexity."""
    logger = logging.getLogger(f'modules.error_resolution.research.{worker_id}')
    
    # Build comprehensive error context
    error_context = {
        'task_details': get_task_details(task_id),
        'environment_info': get_environment_info(),
        'error_patterns': error_patterns,
        'failed_healing_attempts': [k for k, v in healing_results.items() if not v.get('success', False)],
        'code_context': extract_relevant_code_context(),
        'test_failures': extract_test_failure_details()
    }
    
    # Format research query
    research_query = f"""
    PYTHON ERROR RESOLUTION REQUEST
    
    Task Context:
    - Task ID: {task_id}
    - Worker ID: {worker_id}
    - Environment: Python {error_context['environment_info']['python_version']}
    - Dependencies: {', '.join(error_context['environment_info']['packages'])}
    
    Error Summary:
    - Primary Error Categories: {list(error_patterns.keys())}
    - Failed Self-Healing: {error_context['failed_healing_attempts']}
    
    Specific Error Details:
    {format_error_details(error_patterns)}
    
    Code Context:
    {error_context['code_context']}
    
    Test Failures:
    {error_context['test_failures']}
    
    REQUIRED: Provide specific, actionable solutions with:
    1. Root cause analysis
    2. Step-by-step resolution instructions
    3. Code examples where applicable
    4. Verification steps to confirm fix
    """
    
    logger.info("Research query generated", extra={
        'worker_id': worker_id,
        'task_id': task_id,
        'query_length': len(research_query),
        'error_categories': len(error_patterns),
        'failed_healing_attempts': len(error_context['failed_healing_attempts'])
    })
    
    return research_query
```

#### **Perplexity Research Integration**
```python
async def query_perplexity_for_solution(research_query, worker_id, task_id):
    """Query Perplexity API for error resolution solutions."""
    logger = logging.getLogger(f'modules.error_resolution.research.{worker_id}')
    
    logger.info("Initiating Perplexity research query", extra={
        'worker_id': worker_id,
        'task_id': task_id,
        'query_timestamp': datetime.now().isoformat()
    })
    
    try:
        # Initialize Perplexity client
        from perplexity import PerplexityClient
        client = PerplexityClient(api_key=os.getenv('PERPLEXITY_API_KEY'))
        
        # Execute research query
        response = await client.query(
            query=research_query,
            mode='research',  # Research mode for comprehensive analysis
            sources=True      # Include source citations
        )
        
        logger.info("Perplexity research completed", extra={
            'worker_id': worker_id,
            'task_id': task_id,
            'response_length': len(response.content),
            'sources_count': len(response.sources) if response.sources else 0,
            'research_confidence': response.confidence_score
        })
        
        return {
            'success': True,
            'solution': response.content,
            'sources': response.sources,
            'confidence': response.confidence_score,
            'research_timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("Perplexity research failed", extra={
            'worker_id': worker_id,
            'task_id': task_id,
            'error': str(e),
            'stack_trace': traceback.format_exc()
        })
        
        return {
            'success': False,
            'error': str(e),
            'research_timestamp': datetime.now().isoformat()
        }
```

#### **Research-Driven Fix Implementation**
```python
def apply_research_solutions(worker_id, task_id, research_result):
    """Apply solutions derived from Perplexity research."""
    logger = logging.getLogger(f'modules.error_resolution.research.{worker_id}')
    
    if not research_result['success']:
        logger.error("Cannot apply research solutions - research failed", extra={
            'worker_id': worker_id,
            'task_id': task_id,
            'research_error': research_result['error']
        })
        return {'success': False, 'reason': 'research_failed'}
    
    logger.info("Applying research-driven solutions", extra={
        'worker_id': worker_id,
        'task_id': task_id,
        'research_confidence': research_result['confidence'],
        'sources_count': len(research_result['sources'])
    })
    
    try:
        # Parse research solution for actionable steps
        solution_steps = parse_research_solution(research_result['solution'])
        
        application_results = []
        
        for step_num, step in enumerate(solution_steps, 1):
            logger.info(f"Applying research solution step {step_num}", extra={
                'worker_id': worker_id,
                'task_id': task_id,
                'step_description': step['description'][:100],  # First 100 chars
                'step_type': step['type']  # 'code_change', 'config_update', 'dependency_install', etc.
            })
            
            step_result = execute_solution_step(step)
            application_results.append({
                'step_num': step_num,
                'success': step_result['success'],
                'details': step_result
            })
            
            if not step_result['success']:
                logger.warning(f"Research solution step {step_num} failed", extra={
                    'worker_id': worker_id,
                    'task_id': task_id,
                    'step_error': step_result['error']
                })
                # Continue with remaining steps
        
        overall_success = all(result['success'] for result in application_results)
        
        logger.info("Research-driven solution application completed", extra={
            'worker_id': worker_id,
            'task_id': task_id,
            'overall_success': overall_success,
            'successful_steps': sum(1 for r in application_results if r['success']),
            'total_steps': len(application_results)
        })
        
        return {
            'success': overall_success,
            'steps_applied': len(application_results),
            'successful_steps': sum(1 for r in application_results if r['success']),
            'step_details': application_results
        }
        
    except Exception as e:
        logger.error("Failed to apply research solutions", extra={
            'worker_id': worker_id,
            'task_id': task_id,
            'error': str(e),
            'stack_trace': traceback.format_exc()
        })
        
        return {
            'success': False,
            'error': str(e),
            'research_confidence': research_result['confidence']
        }
```

## MANDATORY DEVELOPMENT STANDARDS - NO EXCEPTIONS

### Multi-Agent Worker Isolation & Environment Management
- **Each worker gets its own isolated branch**: `feature/worker-{id}-{task-name}`
- **Each worker gets its own virtual environment**: Create separate venv for each task
- **Dedicated logging per worker**: Each worker maintains isolated log files with detailed tracing
- **Task queue integration**: Workers receive structured payloads from orchestrator
- **All returned errors must be fixed immediately** - no exceptions
- **Lint score enforcement**: If pylint score < 10/10, automatic fix is required
- **Complete pytest coverage**: All tests must pass with 100% success rate
- **LLM fallback preparation**: Failed tasks automatically queued for alternative LLM
- **Cross-validation ready**: All solutions must pass original test suite regardless of LLM
- **Feature categorization**: Each main feature area gets its own module structure
- **Independent sub-modules**: All sub-features are self-contained modules
- **Clean directory maintenance**: Delete old tests, temporary files, and artifacts after use
- **Post-task cleanup**: Remove all temporary branches and environments after PR merge
- **Comprehensive error logging**: All exceptions, state changes, and decisions logged with full context

### Anti-Lazy Implementation Rules
- **NEVER** use placeholder code, TODO comments, or incomplete implementations
- **ALWAYS** implement complete, production-ready solutions
- **NEVER** commit code that doesn't work or has known issues
- **ALWAYS** include comprehensive error handling and input validation
- **NEVER** skip testing or documentation requirements
- **ALWAYS** implement the full feature as requested, not partial solutions

### Quality Gates (ALL MUST PASS)
1. **Code Quality**: All code must pass pylint with perfect 10/10 score
2. **Test Coverage**: All tests must pass with pytest (100% success rate required)
3. **Functionality**: Code must work as intended with no known bugs
4. **Documentation**: All new functions/classes must have docstrings
5. **Error Handling**: Robust error handling for all edge cases
6. **Cleanup Verification**: No temporary files or artifacts remain
7. **Multi-Agent Integration**: All workers must report to orchestrator with structured results
8. **LLM Fallback Compatibility**: Solutions must be testable by alternative LLMs
9. **Cross-Validation Ready**: Original test suite must validate any LLM's solution
10. **Comprehensive Logging**: All components must implement detailed logging using Python's logging module
11. **Debug Traceability**: All errors, attempts, and state changes must be logged with full context
12. **Intelligent Error Resolution**: All workers must implement log analysis and self-healing capabilities
13. **Research Integration**: Failed self-healing must trigger Perplexity research for advanced solutions
14. **Resolution Learning**: Successful error resolution patterns must be tracked and reused

## MANDATORY LOGGING ARCHITECTURE - PYTHON LOGGING MODULE

### Logging Configuration Standards
All components MUST implement comprehensive logging using Python's built-in logging module with the following specifications:

#### **Logging Levels and Usage**
- **DEBUG**: Detailed information for diagnosing problems, variable states, function entry/exit
- **INFO**: General information about program execution, task progress, state transitions
- **WARNING**: Something unexpected happened but program continues, potential issues
- **ERROR**: Serious problem occurred, function/feature failed but program continues
- **CRITICAL**: Very serious error occurred, program may be unable to continue

#### **Required Loggers by Component**
- **Orchestrator Logger**: `modules.orchestrator.main` - Task queue, worker management, decisions
- **Worker Logger**: `modules.workers.{worker_id}` - Individual worker actions and state
- **LLM Fallback Logger**: `modules.llm_fallback.{llm_name}` - Alternative LLM interactions
- **Task Queue Logger**: `modules.task_queue.manager` - Queue operations and priority changes
- **Cross-Validation Logger**: `modules.validation.cross_check` - Validation results and comparisons

#### **Mandatory Logging Points**
1. **Function Entry/Exit**: Log all major function calls with parameters and return values
2. **Error Conditions**: Full exception details with stack traces and context
3. **State Changes**: All object state modifications with before/after values
4. **Decision Points**: Logic branches, retry attempts, fallback triggers
5. **External API Calls**: All LLM API requests/responses with timing
6. **Resource Operations**: File I/O, database operations, network calls
7. **Worker Lifecycle**: Creation, task assignment, completion, cleanup
8. **Performance Metrics**: Execution times, memory usage, success rates

#### **Log File Organization**
```
logs/
├── orchestrator/
│   ├── main-{date}.log           # Main orchestrator operations
│   ├── task-queue-{date}.log     # Task queue management
│   └── worker-management-{date}.log # Worker pool operations
├── workers/
│   ├── worker-{id}-{date}.log    # Individual worker detailed logs
│   └── worker-summary-{date}.log # All worker operations summary
├── llm-fallback/
│   ├── gpt4-{date}.log          # GPT-4 fallback operations
│   ├── gemini-{date}.log        # Gemini fallback operations
│   └── claude-opus-{date}.log   # Claude Opus fallback operations
├── validation/
│   ├── cross-validation-{date}.log # Cross-validation results
│   └── test-execution-{date}.log   # Test suite execution details
└── system/
    ├── performance-{date}.log    # Performance metrics and monitoring
    └── errors-{date}.log         # Consolidated error tracking
```

#### **Logging Format Specification**
```python
LOGGING_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)-30s | "
    "Worker:%(worker_id)s | Task:%(task_id)s | "
    "Attempt:%(attempt_num)s | %(funcName)-20s:%(lineno)-4d | "
    "%(message)s"
)

LOGGING_DATE_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
```

#### **Required Logging Context Fields**
All log entries MUST include contextual information:
- `worker_id`: Unique worker identifier
- `task_id`: Task identifier from orchestrator
- `attempt_num`: Current attempt number (1-3 before fallback)
- `llm_source`: Which LLM generated the solution (claude/gpt4/gemini/opus)
- `execution_time`: Time taken for operation
- `memory_usage`: Memory consumption at log point
- `thread_id`: Thread identifier for concurrent operations

## MANDATORY WORKFLOW - MULTI-AGENT ORCHESTRATED DEVELOPMENT

### Orchestrator Task Assignment Protocol:
1. **Task Queue Reception**: Receive structured task payload from orchestrator
2. **Worker ID Generation**: `WORKER_ID=$(date +%s)-$(uuidgen | cut -d'-' -f1)`
3. **Isolated Context Setup**: Each attempt gets completely fresh environment
4. **Structured Result Reporting**: Return standardized payload to orchestrator
5. **Failure Escalation**: After 3 attempts, automatically escalate to LLM fallback

### Before Starting ANY Task (Worker Initialization):
1. **Receive Task Payload**: `{task_id, requirements, test_suite, max_attempts, priority}`
2. **Create isolated worker branch**: `git checkout -b feature/worker-{id}-{task-name}`
3. **Create dedicated virtual environment**: `python -m venv venv-worker-{id}`
4. **Activate worker environment**: `source venv-worker-{id}/bin/activate`
5. **Install dependencies**: `pip install -r requirements.txt`
6. **Initialize comprehensive logging system**:
   ```python
   import logging
   import os
   from datetime import datetime
   
   # Create worker-specific log directory
   log_dir = f"logs/workers"
   os.makedirs(log_dir, exist_ok=True)
   
   # Configure worker logger with full context
   logger = logging.getLogger(f'modules.workers.{worker_id}')
   logger.setLevel(logging.DEBUG)
   
   # Create file handler with detailed formatting
   log_file = f"{log_dir}/worker-{worker_id}-{datetime.now().strftime('%Y%m%d')}.log"
   file_handler = logging.FileHandler(log_file)
   file_handler.setLevel(logging.DEBUG)
   
   # Custom formatter with all required context fields
   formatter = logging.Formatter(
       "%(asctime)s | %(levelname)-8s | %(name)-30s | "
       f"Worker:{worker_id} | Task:{task_id} | "
       "Attempt:%(attempt_num)s | %(funcName)-20s:%(lineno)-4d | "
       "%(message)s",
       datefmt="%Y-%m-%d %H:%M:%S.%f"
   )
   file_handler.setFormatter(formatter)
   logger.addHandler(file_handler)
   
   # Log worker initialization
   logger.info("Worker initialized", extra={
       'worker_id': worker_id,
       'task_id': task_id,
       'attempt_num': 1,
       'execution_time': 0,
       'memory_usage': psutil.Process().memory_info().rss
   })
   ```
7. **Run existing tests**: `pytest` (ensure all pass before starting)
8. **Check code quality**: `pylint .` (fix any existing issues to 10/10 score)
9. **Log environment setup completion**:
   ```python
   logger.info("Environment setup completed successfully", extra={
       'worker_id': worker_id,
       'task_id': task_id,
       'attempt_num': 1,
       'pylint_score': '10/10',
       'test_status': 'all_passed'
   })
   ```

### During Development with Intelligent Error Resolution:
1. **Write code with full implementation** (no placeholders)
   ```python
   # Log function entry with parameters
   logger.debug(f"Starting implementation of {function_name}", extra={
       'worker_id': worker_id,
       'task_id': task_id,
       'attempt_num': attempt_num,
       'function_name': function_name,
       'parameters': str(parameters)
   })
   ```

2. **Add comprehensive tests** for new functionality
   ```python
   # Log test creation and execution
   logger.info("Creating test suite for new functionality", extra={
       'worker_id': worker_id,
       'task_id': task_id,
       'attempt_num': attempt_num,
       'test_count': len(test_cases),
       'coverage_target': '100%'
   })
   ```

3. **Run tests with intelligent error resolution**: `pytest` with failure analysis
   ```python
   # Enhanced test execution with error resolution
   test_result = subprocess.run(['pytest', '-v', '--tb=long'], capture_output=True, text=True)
   
   if test_result.returncode != 0:
       logger.warning("Test failures detected, initiating intelligent error resolution", extra={
           'worker_id': worker_id,
           'task_id': task_id,
           'attempt_num': attempt_num,
           'test_output': test_result.stdout,
           'test_errors': test_result.stderr
       })
       
       # Trigger intelligent error resolution pipeline
       error_patterns = analyze_execution_logs(worker_id, task_id, attempt_num)
       healing_results = attempt_self_healing(worker_id, task_id, attempt_num, error_patterns)
       
       # If self-healing fails, trigger research-enhanced resolution
       if not all(result.get('success', False) for result in healing_results.values()):
           research_query = generate_research_query(worker_id, task_id, error_patterns, healing_results)
           research_result = await query_perplexity_for_solution(research_query, worker_id, task_id)
           
           if research_result['success']:
               solution_result = apply_research_solutions(worker_id, task_id, research_result)
               logger.info("Research-driven solution applied", extra={
                   'worker_id': worker_id,
                   'task_id': task_id,
                   'attempt_num': attempt_num,
                   'solution_success': solution_result['success'],
                   'research_confidence': research_result['confidence']
               })
               
               # Re-run tests after applying research solutions
               retest_result = subprocess.run(['pytest', '-v'], capture_output=True, text=True)
               logger.info("Post-research retest completed", extra={
                   'worker_id': worker_id,
                   'task_id': task_id,
                   'attempt_num': attempt_num,
                   'retest_status': 'passed' if retest_result.returncode == 0 else 'failed'
               })
   else:
       logger.info("Test execution completed successfully", extra={
           'worker_id': worker_id,
           'task_id': task_id,
           'attempt_num': attempt_num,
           'test_status': 'passed',
           'execution_time': time.time() - start_time
       })
   ```

4. **Lint code with error resolution**: `pylint` with intelligent fixing
   ```python
   # Enhanced pylint with automatic issue resolution
   lint_result = subprocess.run(['pylint', file_path], capture_output=True, text=True)
   score = extract_pylint_score(lint_result.stdout)
   
   if float(score) < 10.0:
       logger.warning("Code quality issues detected, applying intelligent fixes", extra={
           'worker_id': worker_id,
           'task_id': task_id,
           'attempt_num': attempt_num,
           'pylint_score': score,
           'issues_count': count_issues(lint_result.stdout)
       })
       
       # Analyze pylint output and apply targeted fixes
       lint_issues = parse_pylint_issues(lint_result.stdout)
       fix_results = apply_pylint_fixes(lint_issues, worker_id, task_id)
       
       # Re-run pylint after fixes
       recheck_result = subprocess.run(['pylint', file_path], capture_output=True, text=True)
       new_score = extract_pylint_score(recheck_result.stdout)
       
       logger.info("Pylint fixes applied", extra={
           'worker_id': worker_id,
           'task_id': task_id,
           'attempt_num': attempt_num,
           'original_score': score,
           'new_score': new_score,
           'fixes_applied': len(fix_results['successful_fixes'])
       })
   ```

5. **Intelligent error resolution pipeline** - comprehensive error handling
   ```python
   def handle_error_with_intelligence(error, worker_id, task_id, attempt_num):
       """Comprehensive error handling with intelligence."""
       logger.error("Error encountered, initiating intelligent resolution", extra={
           'worker_id': worker_id,
           'task_id': task_id,
           'attempt_num': attempt_num,
           'error_type': type(error).__name__,
           'error_message': str(error),
           'stack_trace': traceback.format_exc()
       })
       
       # Step 1: Log analysis
       error_patterns = analyze_execution_logs(worker_id, task_id, attempt_num)
       
       # Step 2: Self-healing attempt
       healing_results = attempt_self_healing(worker_id, task_id, attempt_num, error_patterns)
       
       # Step 3: Research-enhanced resolution if needed
       if not all(result.get('success', False) for result in healing_results.values()):
           research_query = generate_research_query(worker_id, task_id, error_patterns, healing_results)
           research_result = await query_perplexity_for_solution(research_query, worker_id, task_id)
           
           if research_result['success']:
               solution_result = apply_research_solutions(worker_id, task_id, research_result)
               return solution_result
       
       return healing_results
   ```

6. **Organize features into categorized modules** with independent sub-modules

7. **Log all state changes and decisions with resolution tracking**:
   ```python
   # Enhanced decision logging with resolution context
   logger.info(f"Decision point: {decision_context}", extra={
       'worker_id': worker_id,
       'task_id': task_id,
       'attempt_num': attempt_num,
       'decision_options': options,
       'selected_option': chosen_option,
       'reasoning': decision_reasoning,
       'previous_errors': get_previous_error_count(),
       'resolution_attempts': get_resolution_attempt_count()
   })
   ```

8. **Prepare for cross-validation**: Ensure test suite can validate any LLM solution with error context

### Before Committing (Validation Gate):
1. **Final test run**: `pytest` (100% pass rate required)
   ```python
   logger.info("Starting final validation gate", extra={
       'worker_id': worker_id,
       'task_id': task_id,
       'attempt_num': attempt_num,
       'validation_stage': 'final_tests'
   })
   
   final_test_result = subprocess.run(['pytest', '-v', '--tb=long'], capture_output=True, text=True)
   logger.critical("Final test results", extra={
       'worker_id': worker_id,
       'task_id': task_id,
       'attempt_num': attempt_num,
       'test_status': 'passed' if final_test_result.returncode == 0 else 'failed',
       'test_output': final_test_result.stdout,
       'failure_details': final_test_result.stderr if final_test_result.returncode != 0 else None
   })
   ```

2. **Final lint check**: `pylint .` (perfect 10/10 score required)
   ```python
   final_lint_result = subprocess.run(['pylint', '.'], capture_output=True, text=True)
   final_score = extract_pylint_score(final_lint_result.stdout)
   logger.critical("Final code quality validation", extra={
       'worker_id': worker_id,
       'task_id': task_id,
       'attempt_num': attempt_num,
       'final_pylint_score': final_score,
       'quality_gate_passed': final_score == '10.00/10',
       'remaining_issues': count_issues(final_lint_result.stdout)
   })
   ```

3. **Manual testing**: Verify functionality works as expected
   ```python
   logger.info("Manual functionality verification", extra={
       'worker_id': worker_id,
       'task_id': task_id,
       'attempt_num': attempt_num,
       'verification_steps': manual_test_steps,
       'verification_results': test_results
   })
   ```

4. **Cross-validation preparation**: Ensure tests can validate alternative LLM solutions
   ```python
   logger.info("Cross-validation test suite preparation", extra={
       'worker_id': worker_id,
       'task_id': task_id,
       'attempt_num': attempt_num,
       'test_suite_portable': True,
       'alternative_llms_supported': ['gpt4', 'gemini', 'claude-opus']
   })
   ```

5. **Clean up temporary files**: Remove test artifacts, temp files, old tests
   ```python
   cleanup_start = time.time()
   # Perform cleanup operations
   logger.info("Cleanup operations completed", extra={
       'worker_id': worker_id,
       'task_id': task_id,
       'attempt_num': attempt_num,
       'files_removed': cleaned_files,
       'cleanup_time': time.time() - cleanup_start
   })
   ```

6. **Commit with descriptive message**
   ```python
   logger.info("Creating commit with validation results", extra={
       'worker_id': worker_id,
       'task_id': task_id,
       'attempt_num': attempt_num,
       'commit_message': commit_message,
       'files_committed': committed_files
   })
   ```

7. **Report to orchestrator**: Send structured success/failure payload
   ```python
   success_payload = {
       'worker_id': worker_id,
       'task_id': task_id,
       'attempt_num': attempt_num,
       'status': 'success',
       'validation_results': {
           'tests_passed': True,
           'pylint_score': '10.00/10',
           'manual_verification': True,
           'cross_validation_ready': True
       },
       'performance_metrics': {
           'total_execution_time': time.time() - task_start_time,
           'peak_memory_usage': max_memory_usage,
           'files_modified': len(modified_files)
       }
   }
   
   logger.critical("Task completion - SUCCESS", extra=success_payload)
   # Send to orchestrator
   orchestrator.report_success(success_payload)
   ```

### After Development Complete (Worker Success):
1. **Final cleanup verification**: Ensure no artifacts remain
2. **Push branch**: `git push -u origin feature/worker-{id}-{task-name}`
3. **Create PR**: `./gh_2.74.1_linux_amd64/bin/gh pr create`
4. **Report success to orchestrator**: Send completion payload with results
5. **After PR merge**: Delete worker branch and worker virtual environment
6. **Never merge directly to master** - always use PR review process

### Worker Failure Protocol:
1. **Log failure details**: Capture complete error context and attempt history
   ```python
   failure_payload = {
       'worker_id': worker_id,
       'task_id': task_id,
       'attempt_num': attempt_num,
       'status': 'failed',
       'failure_details': {
           'error_type': type(error).__name__,
           'error_message': str(error),
           'stack_trace': traceback.format_exc(),
           'failure_stage': current_stage,  # 'setup', 'development', 'testing', 'validation'
           'last_successful_action': last_action,
           'environment_state': get_environment_state()
       },
       'diagnostic_information': {
           'pylint_score_achieved': current_pylint_score,
           'tests_passed': tests_passed_count,
           'tests_failed': tests_failed_count,
           'files_modified': modified_files,
           'execution_time': time.time() - task_start_time,
           'memory_usage_peak': max_memory_usage
       }
   }
   
   logger.critical("Task completion - FAILURE", extra=failure_payload)
   ```

2. **Report to orchestrator**: Send failure payload with diagnostic information
   ```python
   # Comprehensive failure reporting to orchestrator
   orchestrator_failure_report = {
       **failure_payload,
       'retry_recommendation': analyze_retry_potential(),
       'resource_cleanup_required': list_cleanup_actions(),
       'lessons_learned': extract_failure_patterns(),
       'environment_snapshot': capture_environment_state()
   }
   
   logger.error("Sending failure report to orchestrator", extra={
       'worker_id': worker_id,
       'task_id': task_id,
       'attempt_num': attempt_num,
       'report_size': len(str(orchestrator_failure_report)),
       'retry_viable': orchestrator_failure_report['retry_recommendation']['viable']
   })
   
   orchestrator.report_failure(orchestrator_failure_report)
   ```

3. **Orchestrator decision**: Retry with fresh worker OR escalate to LLM fallback
   ```python
   # Orchestrator logs decision-making process
   orchestrator_logger = logging.getLogger('modules.orchestrator.main')
   orchestrator_logger.info("Processing worker failure report", extra={
       'task_id': task_id,
       'failed_worker_id': worker_id,
       'attempt_num': attempt_num,
       'failure_analysis': failure_analysis_results,
       'decision_factors': decision_criteria
   })
   
   if attempt_num < 3:
       orchestrator_logger.info("Decision: Retry with fresh worker", extra={
           'task_id': task_id,
           'next_attempt': attempt_num + 1,
           'new_worker_id': new_worker_id,
           'retry_modifications': retry_adjustments
       })
   else:
       orchestrator_logger.warning("Decision: Escalate to LLM fallback", extra={
           'task_id': task_id,
           'total_attempts': attempt_num,
           'selected_fallback_llm': selected_llm,
           'escalation_reason': escalation_reasoning
       })
   ```

4. **LLM fallback handoff**: Original test suite transferred to alternative LLM
   ```python
   fallback_logger = logging.getLogger(f'modules.llm_fallback.{selected_llm}')
   fallback_logger.info("LLM fallback initiated", extra={
       'task_id': task_id,
       'fallback_llm': selected_llm,
       'original_worker_id': worker_id,
       'claude_attempts': attempt_num,
       'test_suite_size': len(test_suite),
       'requirements_complexity': analyze_requirements_complexity()
   })
   
   # Log test suite transfer
   fallback_logger.debug("Test suite transfer details", extra={
       'task_id': task_id,
       'test_files': test_files,
       'validation_criteria': validation_criteria,
       'cross_validation_setup': cross_validation_config
   })
   ```

5. **Cross-validation**: Claude worker validates alternative LLM solution
   ```python
   validation_logger = logging.getLogger('modules.validation.cross_check')
   validation_logger.info("Cross-validation of fallback solution initiated", extra={
       'task_id': task_id,
       'solution_source': selected_llm,
       'validator_worker_id': new_claude_worker_id,
       'original_test_suite': original_test_suite,
       'fallback_solution_files': solution_files
   })
   
   # Log validation results
   validation_result = run_cross_validation()
   validation_logger.critical("Cross-validation results", extra={
       'task_id': task_id,
       'validation_status': 'passed' if validation_result.success else 'failed',
       'test_results': validation_result.test_results,
       'compatibility_score': validation_result.compatibility_score,
       'solution_quality_score': validation_result.quality_score,
       'recommendation': validation_result.recommendation
   })
   ```

### Post-Task Cleanup (MANDATORY):
1. **Delete worker branch**: `git branch -d feature/worker-{id}-{task-name}`
2. **Remove worker environment**: `rm -rf venv-worker-{id}`
3. **Clean working directory**: Remove any temporary files or test artifacts
4. **Verify clean state**: `git status` should show clean working tree
5. **Update orchestrator**: Confirm resource cleanup completion

## Development Environment

### Python Setup
- **Python Version**: 3.12.3
- **Virtual Environment**: `venv/` (activate with `source venv/bin/activate`)
- **Package Management**: pip

### Installed Tools
- **pylint 3.3.7**: Code linting - MUST show zero warnings/errors
- **pytest 8.4.0**: Testing framework - ALL tests MUST pass

### Database
- **SQLite**: Version 3.45.1 (available through Python's built-in sqlite3 module)
- **Usage**: No separate installation required - use `import sqlite3` in Python
- **Database Files**: Store `.db` files in project root or `data/` directory
- **Connection Pattern**: Always use context managers or explicit close() for connections

### SQLite Usage Examples
```python
import sqlite3

# Basic connection and table creation
def create_database():
    conn = sqlite3.connect('project.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Using context manager (recommended)
def safe_database_operation():
    with sqlite3.connect('project.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users')
        return cursor.fetchall()
```

### GitHub Integration
- **Repository**: azorel/power
- **Authentication**: Configured via GITHUB_TOKEN in .env
- **GitHub CLI**: Available at `./gh_2.74.1_linux_amd64/bin/gh`

## Required Development Commands

```bash
# 1. MULTI-AGENT ORCHESTRATOR SETUP (Initialize orchestrator system)
# Set up orchestrator with task queue and worker pool management
python -m modules.orchestrator.setup --workers=5 --queue-size=100
export ORCHESTRATOR_ACTIVE=true

# 2. WORKER INITIALIZATION (Receive task from orchestrator)
# Worker receives structured task payload: {task_id, requirements, test_suite, max_attempts, priority}
WORKER_ID=$(date +%s)-$(uuidgen | cut -d'-' -f1)  # Unique worker ID
TASK_ID=$1  # Received from orchestrator
git checkout -b feature/worker-${WORKER_ID}-${TASK_ID}
python -m venv venv-worker-${WORKER_ID}
source venv-worker-${WORKER_ID}/bin/activate
pip install -r requirements.txt
pytest  # Ensure all existing tests pass
pylint .  # Fix any existing issues to 10/10 score

# Initialize comprehensive logging system for orchestrator reporting
mkdir -p logs/{orchestrator,workers,llm-fallback,validation,system}
python -c "
import logging
import os
from datetime import datetime

# Set up comprehensive logging configuration
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)-8s | %(name)-30s | Worker:${WORKER_ID} | Task:${TASK_ID} | Attempt:1 | %(funcName)-20s:%(lineno)-4d | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S.%f'
)

# Create worker-specific logger
logger = logging.getLogger(f'modules.workers.${WORKER_ID}')
handler = logging.FileHandler(f'logs/workers/worker-${WORKER_ID}-{datetime.now().strftime(\"%Y%m%d\")}.log')
handler.setFormatter(logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(name)-30s | Worker:${WORKER_ID} | Task:${TASK_ID} | Attempt:1 | %(funcName)-20s:%(lineno)-4d | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S.%f'
))
logger.addHandler(handler)
logger.info('Worker logging system initialized', extra={'worker_id': '${WORKER_ID}', 'task_id': '${TASK_ID}', 'attempt_num': 1})
"

# 3. DURING DEVELOPMENT (Worker execution with comprehensive logging)
# Run tests with detailed logging
python -c "
import logging
import subprocess
import time
logger = logging.getLogger(f'modules.workers.${WORKER_ID}')
start_time = time.time()
result = subprocess.run(['pytest', '-v'], capture_output=True, text=True)
logger.info('Test execution completed', extra={
    'worker_id': '${WORKER_ID}',
    'task_id': '${TASK_ID}',
    'attempt_num': 1,
    'test_status': 'passed' if result.returncode == 0 else 'failed',
    'execution_time': time.time() - start_time,
    'test_output': result.stdout[:1000]  # First 1000 chars
})
"

# Run pylint with detailed logging
python -c "
import logging
import subprocess
import re
logger = logging.getLogger(f'modules.workers.${WORKER_ID}')
result = subprocess.run(['pylint', '.'], capture_output=True, text=True)
score_match = re.search(r'Your code has been rated at ([\d\.]+)/10', result.stdout)
score = score_match.group(1) if score_match else '0.00'
logger.info('Code quality check completed', extra={
    'worker_id': '${WORKER_ID}',
    'task_id': '${TASK_ID}',
    'attempt_num': 1,
    'pylint_score': score,
    'quality_gate_passed': float(score) == 10.0
})
"

# Fix ALL errors immediately - no exceptions (with logging)
# Any error fixing must be logged with detailed context

# 4. VALIDATION GATE (Before committing - ALL must pass)
pytest  # Final test verification (100% success rate)
pylint .  # Final quality check (perfect 10/10 score)
# Prepare cross-validation test suite for potential LLM fallback
python -m modules.llm_fallback.prepare_test_suite --task-id=${TASK_ID}
# Clean up temporary files and test artifacts
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +
# Only commit if both commands show perfect scores
# Report success to orchestrator
python -m modules.orchestrator.report_success --worker-id=${WORKER_ID} --task-id=${TASK_ID}

# 5. WORKER SUCCESS COMPLETION
git push -u origin feature/worker-${WORKER_ID}-${TASK_ID}
./gh_2.74.1_linux_amd64/bin/gh pr create --title "Task ${TASK_ID}: Worker ${WORKER_ID} Success" --body "Complete implementation with tests and cross-validation ready"

# 6. WORKER FAILURE PROTOCOL (If validation fails)
# Report failure to orchestrator with detailed diagnostics
python -m modules.orchestrator.report_failure --worker-id=${WORKER_ID} --task-id=${TASK_ID} --attempt=${ATTEMPT_NUM}
# Orchestrator decides: retry with fresh worker OR escalate to LLM fallback
# If LLM fallback triggered:
python -m modules.llm_fallback.execute --task-id=${TASK_ID} --fallback-llm=gpt4
# Cross-validation of fallback solution by original Claude worker
python -m modules.workers.cross_validate --task-id=${TASK_ID} --solution-source=fallback

# 7. POST-COMPLETION CLEANUP (MANDATORY)
git checkout master
git pull origin master
git branch -d feature/worker-${WORKER_ID}-${TASK_ID}
deactivate  # Exit worker environment
rm -rf venv-worker-${WORKER_ID}  # Remove worker environment
git clean -fd  # Remove any remaining artifacts
# Update orchestrator with cleanup completion
python -m modules.orchestrator.cleanup_complete --worker-id=${WORKER_ID}

# 8. ORCHESTRATOR MANAGEMENT OPERATIONS WITH COMPREHENSIVE LOGGING
# View orchestrator status and worker pool health (with logging)
python -c "
import logging
logger = logging.getLogger('modules.orchestrator.main')
logger.info('Orchestrator status check initiated', extra={'operation': 'status_check'})
# Run actual status check
import modules.orchestrator.status as status
status_result = status.get_status()
logger.info('Orchestrator status retrieved', extra={
    'active_workers': status_result['active_workers'],
    'queued_tasks': status_result['queued_tasks'],
    'system_health': status_result['health_status']
})
"

# Monitor task queue and completion rates (with detailed logging)
python -c "
import logging
logger = logging.getLogger('modules.orchestrator.main')
logger.info('Task queue monitoring initiated', extra={'operation': 'queue_monitor'})
# Monitor implementation with logging
import modules.orchestrator.monitor as monitor
monitor_result = monitor.get_detailed_stats()
logger.info('Task queue monitoring completed', extra={
    'completion_rate': monitor_result['completion_rate'],
    'average_task_time': monitor_result['avg_execution_time'],
    'failure_rate': monitor_result['failure_rate'],
    'fallback_usage': monitor_result['llm_fallback_percentage']
})
"

# View LLM fallback usage statistics (with comprehensive logging)
python -c "
import logging
logger = logging.getLogger('modules.llm_fallback.main')
logger.info('LLM fallback statistics request', extra={'operation': 'fallback_stats'})
import modules.llm_fallback.stats as fallback_stats
stats = fallback_stats.get_comprehensive_stats()
logger.info('LLM fallback statistics compiled', extra={
    'gpt4_usage': stats['gpt4']['usage_count'],
    'gemini_usage': stats['gemini']['usage_count'],
    'claude_opus_usage': stats['claude_opus']['usage_count'],
    'cross_validation_success_rate': stats['cross_validation_success_rate'],
    'fallback_trigger_reasons': stats['trigger_reasons']
})
"

# Performance analysis across all LLMs (with detailed logging)
python -c "
import logging
logger = logging.getLogger('modules.orchestrator.performance')
logger.info('Performance analysis initiated', extra={'operation': 'performance_analysis'})
import modules.orchestrator.performance_report as perf
report = perf.generate_comprehensive_report()
logger.critical('Performance analysis completed', extra={
    'claude_success_rate': report['claude']['success_rate'],
    'gpt4_success_rate': report['gpt4']['success_rate'],
    'gemini_success_rate': report['gemini']['success_rate'],
    'average_task_completion_time': report['system']['avg_completion_time'],
    'memory_efficiency': report['system']['memory_efficiency'],
    'recommendation': report['optimization_recommendations']['primary']
})
"

# Log analysis and debugging commands
# View recent errors across all components
python -c "
import logging
from glob import glob
import os
from datetime import datetime, timedelta

logger = logging.getLogger('modules.system.analysis')
logger.info('System-wide error analysis initiated')

# Analyze error patterns from all log files
error_patterns = {}
log_files = glob('logs/*/*.log')
for log_file in log_files:
    # Parse log file for ERROR and CRITICAL entries
    with open(log_file, 'r') as f:
        for line in f:
            if '| ERROR |' in line or '| CRITICAL |' in line:
                # Extract error patterns and count occurrences
                pass

logger.info('Error analysis completed', extra={
    'total_log_files_analyzed': len(log_files),
    'error_patterns_found': len(error_patterns),
    'critical_issues': sum(1 for pattern in error_patterns if 'CRITICAL' in pattern)
})
"

# GitHub operations
./gh_2.74.1_linux_amd64/bin/gh repo view azorel/power
./gh_2.74.1_linux_amd64/bin/gh pr list
./gh_2.74.1_linux_amd64/bin/gh pr review
```

## Configuration

### Environment Variables (.env)
- GitHub token and repository settings
- **Multi-LLM API Keys**: OpenAI, Anthropic, Google Gemini, and Perplexity for fallback system
- **Perplexity Research API**: API key for intelligent error resolution research queries
- **Orchestrator Configuration**: Task queue settings, retry limits, timeout values
- **Worker Pool Settings**: Max concurrent workers, resource allocation limits
- **Error Resolution Settings**: Self-healing attempt limits, research query thresholds
- Database paths for integrations

### Repository Structure
- `.env`: Environment configuration (not committed)
- `venv/`: Main Python virtual environment
- `venv-worker-*/`: Isolated worker virtual environments (temporary)
- `CLAUDE.md`: This guidance file
- `modules/`: Feature-categorized module structure
  - `modules/orchestrator/`: Multi-agent orchestration system
  - `modules/workers/`: Worker agent implementations
  - `modules/llm_fallback/`: Alternative LLM integration and validation
  - `modules/task_queue/`: Priority task management system
  - `modules/error_resolution/`: Intelligent error resolution engine
    - `modules/error_resolution/log_analyzer/`: Log-based debugging and pattern recognition
    - `modules/error_resolution/self_healing/`: Automated fix implementation
    - `modules/error_resolution/research/`: Perplexity integration for advanced solutions
    - `modules/error_resolution/learning/`: Pattern learning and resolution optimization
  - `modules/validation/`: Cross-validation and testing framework
  - `modules/{main-feature}/`: Main feature areas
  - `modules/{main-feature}/{sub-feature}/`: Independent sub-modules

## Multi-Agent Module Organization Standards
- **Feature Categorization**: Group related functionality into main feature areas
- **Multi-Agent Core Modules**: Essential orchestration components:
  - `modules/orchestrator/`: Task queue, worker management, failure handling
  - `modules/workers/`: Claude Code worker implementations with isolation
  - `modules/llm_fallback/`: GPT-4, Gemini, Claude Opus integration
  - `modules/task_queue/`: Priority management and retry logic
- **Independent Sub-modules**: Each sub-feature is self-contained with its own:
  - `__init__.py`: Module initialization
  - `{feature}.py`: Core implementation
  - `test_{feature}.py`: Comprehensive tests (cross-validation compatible)
  - `requirements.txt`: Module-specific dependencies (if needed)
  - `worker_interface.py`: Orchestrator communication protocol
- **Clean Interfaces**: Modules communicate through well-defined APIs
- **Cross-Validation Ready**: All test suites can validate any LLM's solution
- **No Cross-Dependencies**: Sub-modules must not depend on each other directly
- **Orchestrator Integration**: All modules report status and results to central orchestrator

## Multi-Agent System Enforcement
- Any code that violates these standards will be rejected
- All PRs must pass quality gates before review
- **Orchestrator Oversight**: All tasks must be processed through orchestrator
- **Worker Isolation Mandatory**: No exceptions to isolated worker workflow
- **LLM Fallback Compliance**: Failed tasks automatically escalate to alternative LLMs
- **Cross-Validation Required**: All solutions must pass original test suite
- Complete implementations only - no partial solutions
- Perfect pylint scores (10/10) mandatory
- 100% pytest success rate required
- **Structured Reporting**: All workers must send standardized payloads to orchestrator
- **Resource Cleanup**: All temporary files and environments must be cleaned up
- **Performance Tracking**: Worker success/failure rates monitored for optimization
- Workers must maintain isolated branches and environments
- **Health Monitoring**: System tracks worker performance and automatically rebalances load

### **MANDATORY LOGGING ENFORCEMENT - NO EXCEPTIONS**
- **Every Function Call**: All function entry/exit points must be logged with parameters
- **Every Error**: All exceptions must be logged with full stack traces and context
- **Every State Change**: All object modifications must be logged with before/after values
- **Every Decision**: All logic branches and retry attempts must be logged with reasoning
- **Every API Call**: All external LLM interactions must be logged with timing and responses
- **Every Test Execution**: All test runs must be logged with detailed results and timing
- **Every Worker Action**: All worker lifecycle events must be logged with comprehensive context
- **Centralized Error Tracking**: All CRITICAL and ERROR logs must be aggregated for analysis
- **Performance Metrics**: Execution time, memory usage, and resource consumption must be logged
- **Cross-Component Traceability**: All log entries must include worker_id, task_id, and attempt_num
- **Log File Integrity**: All log files must be maintained with proper rotation and backup
- **Debug Accessibility**: All logs must be easily searchable and analyzable for bug fixing

### **MANDATORY INTELLIGENT ERROR RESOLUTION ENFORCEMENT - NO EXCEPTIONS**
- **Automatic Error Analysis**: All test failures must trigger immediate log analysis
- **Self-Healing Attempts**: Workers must attempt automated fixes based on log insights
- **Research Integration**: Failed self-healing must automatically query Perplexity for solutions
- **Resolution Tracking**: All error resolution attempts must be logged with detailed context
- **Pattern Learning**: Successful resolution strategies must be recorded for future use
- **Error Categorization**: All errors must be classified into predefined categories for targeted fixing
- **Research Query Optimization**: Perplexity queries must include comprehensive error context
- **Solution Validation**: All research-driven fixes must be verified through comprehensive testing
- **Resolution Performance Metrics**: Success rates of different resolution strategies must be tracked
- **Escalation Triggers**: Clear criteria for escalating to LLM fallback after resolution failures
- **Cross-Worker Learning**: Resolution patterns must be shared across worker instances
- **Continuous Improvement**: Error resolution effectiveness must be continuously monitored and optimized