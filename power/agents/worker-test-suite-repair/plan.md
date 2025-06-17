# WORKER AGENT TASK: Test Suite Repair

## MISSION

Fix all 12 failed tests and 16 errors in the Gemini API test suite.

## MANDATORY STANDARDS COMPLIANCE

**CRITICAL**: You MUST read and follow ai_docs/standards/CODING_STANDARDS.md before starting any work.

## CURRENT FAILURE ANALYSIS

### 12 Failed Tests:

1. `test_get_genai_client_success` - Mock configuration issue
2. `test_get_genai_client_import_error` - Mock configuration issue
3. `test_get_model_info` - Mock attribute access error
4. `test_get_usage_stats` - Mock attribute access error
5. `test_map_image_request_unsupported_format` - Exception type setting error
6. `test_map_image_request_too_large` - Exception type setting error
7. `test_extract_model_info` - Mock attribute access error
8. `test_handle_google_api_error` - Exception type setting error
9. `test_handle_generative_ai_error` - Exception type setting error
10. `test_get_gemini_stats` - `image_generation_model` attribute missing
11. `test_get_optimal_batch_size` - Returns 1 instead of expected 3
12. `test_get_usage_summary` - `image_generation_model` attribute missing

### 16 Error Tests:

All errors are related to mock attribute access issues in various test methods.

## SPECIFIC FIXES REQUIRED

### Priority 1: Mock Configuration Issues

- **File**: `tests/adapters/gemini_api/test_rate_limiter.py`
- **Issue**: Mock object missing `image_generation_model` attribute
- **Fix**: Update mock to include `image_generation_model` or use proper method calls

### Priority 2: Batch Size Logic

- **File**: `adapters/gemini_api/rate_limiter.py`
- **Issue**: `get_optimal_batch_size()` returns 1 instead of 3
- **Fix**: Review and correct batch size calculation logic

### Priority 3: Exception Type Setting

- **Files**: `tests/adapters/gemini_api/test_data_mapper.py`, `test_exceptions.py`
- **Issue**: `TypeError: cannot set '__name__' attribute of immutable type 'Exception'`
- **Fix**: Use proper exception class inheritance instead of trying to modify immutable types

### Priority 4: Mock Attribute Access

- **Files**: All test files with ERROR status
- **Issue**: Mock objects missing expected attributes/methods
- **Fix**: Update mock configurations to match actual interface contracts

## EXECUTION PLAN

### Phase 1: Environment Setup (5 minutes)

1. Create isolated workspace: `agents/worker-test-suite-repair/`
2. Fresh clone from GitHub: `git clone azorel/power`
3. Create feature branch: `feature/agent-test-suite-repair`
4. Setup virtual environment and install dependencies
5. Read CODING_STANDARDS.md thoroughly

### Phase 2: Analysis & Diagnosis (10 minutes)

1. Run full test suite to confirm current failures
2. Examine each failing test in detail
3. Identify root causes for each failure type
4. Map failures to required fixes
5. Prioritize fixes by impact and dependencies

### Phase 3: Mock Configuration Fixes (15 minutes)

1. **Fix image_generation_model attribute errors**:

   - Update mocks in `test_rate_limiter.py`
   - Add missing attributes to mock configurations
   - Ensure mock matches actual interface

2. **Fix batch size calculation**:
   - Review `get_optimal_batch_size()` implementation
   - Correct logic to return expected value (3)
   - Validate calculation against test expectations

### Phase 4: Exception Handling Fixes (15 minutes)

1. **Fix Exception type setting errors**:

   - Replace direct `__name__` assignment with proper inheritance
   - Create custom exception classes if needed
   - Use exception factory patterns for dynamic exceptions

2. **Update exception mapper tests**:
   - Fix Google API error handling tests
   - Fix Generative AI error handling tests
   - Ensure proper exception translation

### Phase 5: Mock Interface Alignment (20 minutes)

1. **Review actual interfaces**:

   - Check `shared/interfaces/llm_provider.py`
   - Validate `adapters/gemini_api/client.py` implementation
   - Identify interface contract mismatches

2. **Update test mocks**:
   - Align mock configurations with actual interfaces
   - Add missing methods/attributes to mocks
   - Fix attribute access patterns in tests

### Phase 6: Validation & Testing (15 minutes)

1. **Run test suite iteratively**:

   - Fix one category of failures at a time
   - Validate fixes don't break other tests
   - Ensure 100% test pass rate

2. **Final validation**:
   - Run complete test suite: `pytest tests/ -v`
   - Confirm 0 failures, 0 errors
   - Validate all 118 tests pass or skip appropriately

### Phase 7: Quality Assurance (10 minutes)

1. **Code quality validation**:

   - Run `pylint` on modified files
   - Ensure 10/10 score maintenance
   - Fix any style or quality issues

2. **Architecture compliance**:
   - Verify no cross-layer violations
   - Confirm interface contracts maintained
   - Validate three-layer architecture compliance

## SUCCESS CRITERIA

- **100% test pass rate**: 0 failures, 0 errors
- **Perfect pylint score**: 10/10 on all modified files
- **Architecture compliance**: No violations of three-layer architecture
- **Interface integrity**: All mocks align with actual interfaces

## COMPLETION SIGNAL

When all tests pass (0 failures, 0 errors), commit changes with message:

```
fix: repair test suite - 12 failures and 16 errors resolved

- Fix mock configuration for image_generation_model attribute
- Correct get_optimal_batch_size calculation logic
- Fix Exception type setting using proper inheritance
- Align test mocks with actual interface contracts
- Ensure 100% test pass rate across all test files

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
```

**End with**: "Task complete and ready for next step"

## MANDATORY DELIVERABLES

1. All 118 tests passing (0 failures, 0 errors)
2. Pylint score 10/10 on modified files
3. Clean git commit on feature branch
4. Work package submission with validation results
