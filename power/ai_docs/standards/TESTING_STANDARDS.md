# TESTING STANDARDS

**MANDATORY**: All code MUST achieve perfect test scores before submission. These standards ensure reliability, maintainability, and quality.

## Quality Gates (NON-NEGOTIABLE)

### Perfect Score Requirements
```bash
# REQUIRED: All tests must pass
pytest -v                    # 100% success rate MANDATORY
pylint --score=y *.py       # Perfect 10.00/10 score MANDATORY
coverage run -m pytest      # 100% line coverage target
coverage report --fail-under=90  # Minimum 90% coverage ENFORCED
```

### Validation Protocol (ABSOLUTE REQUIREMENT)
```python
def validate_test_requirements() -> ValidationResult:
    """
    Validate that all testing requirements are met.
    
    Returns:
        ValidationResult with pass/fail status for each requirement
    """
    result = ValidationResult()
    
    # Check pytest results
    pytest_result = run_pytest()
    result.add_check('pytest_success', pytest_result.success_rate == 100)
    
    # Check pylint score
    pylint_result = run_pylint()
    result.add_check('pylint_perfect', pylint_result.score == 10.0)
    
    # Check coverage
    coverage_result = run_coverage()
    result.add_check('coverage_adequate', coverage_result.percentage >= 90)
    
    # All checks must pass
    result.overall_pass = all(result.checks.values())
    
    return result
```

## Test Structure Standards

### Directory Organization (MANDATORY)
```
tests/
├── unit/                   # Unit tests (isolated functionality)
│   ├── core/              # Tests for core layer
│   ├── adapters/          # Tests for adapter layer
│   └── shared/            # Tests for shared layer
├── integration/           # Integration tests (component interaction)
│   ├── api_tests/         # External API integration tests
│   └── database_tests/    # Database integration tests
├── e2e/                   # End-to-end tests (full workflow)
└── fixtures/              # Test data and fixtures
    ├── data/              # Test data files
    └── mocks/             # Mock objects and responses
```

### Test File Naming (ABSOLUTE REQUIREMENT)
```python
# CORRECT: Clear, descriptive test file names
tests/unit/core/services/test_text_processor.py
tests/integration/adapters/test_gemini_integration.py
tests/e2e/workflows/test_content_generation_workflow.py

# INCORRECT: Vague or inconsistent naming
tests/test_stuff.py         # Too vague
tests/gemini_test.py        # Wrong naming pattern
tests/unit_tests.py         # Missing specificity
```

## Unit Test Standards

### Test Class Structure (MANDATORY)
```python
"""
Unit tests for TextProcessor service.
Tests all public methods and error conditions.
"""
import pytest
from unittest.mock import Mock, patch
from typing import List

from core.services.text_processor import TextProcessor
from shared.exceptions import ProcessingError
from shared.interfaces.llm_provider import LLMProvider


class TestTextProcessor:
    """Test cases for TextProcessor service."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.mock_llm = Mock(spec=LLMProvider)
        self.processor = TextProcessor(self.mock_llm)

    def test_process_text_success(self):
        """Test successful text processing with valid input."""
        # Arrange
        input_text = "test input"
        expected_output = "processed text"
        self.mock_llm.generate_text.return_value = expected_output

        # Act
        result = self.processor.process_text(input_text)

        # Assert
        assert result == expected_output
        self.mock_llm.generate_text.assert_called_once_with(input_text)

    def test_process_text_empty_input(self):
        """Test error handling for empty input."""
        # Arrange & Act & Assert
        with pytest.raises(ValueError, match="Input text cannot be empty"):
            self.processor.process_text("")

    def test_process_text_llm_error(self):
        """Test error handling when LLM provider fails."""
        # Arrange
        self.mock_llm.generate_text.side_effect = ProcessingError("LLM failed")

        # Act & Assert
        with pytest.raises(ProcessingError, match="LLM failed"):
            self.processor.process_text("test input")

    def teardown_method(self):
        """Clean up after each test method."""
        # Reset mocks or clean up resources if needed
        pass
```

### Test Method Requirements (NON-NEGOTIABLE)
```python
def test_method_template(self):
    """
    REQUIRED: Every test method must have:
    1. Clear, descriptive docstring
    2. AAA pattern (Arrange, Act, Assert)
    3. Specific assertions
    4. Meaningful test data
    """
    # Arrange - Set up test conditions
    test_input = "meaningful test data"
    expected_result = "expected outcome"
    
    # Act - Execute the functionality being tested
    actual_result = self.system_under_test.method_to_test(test_input)
    
    # Assert - Verify the results
    assert actual_result == expected_result
    assert self.mock_dependency.called
```

## Integration Test Standards

### API Integration Testing (MANDATORY)
```python
"""
Integration tests for Gemini API adapter.
Tests actual API interactions with proper authentication.
"""
import pytest
import os
from adapters.gemini_api.client import GeminiClient
from adapters.gemini_api.config import GeminiConfig
from shared.models.llm_request import LLMRequest


class TestGeminiIntegration:
    """Integration tests for Gemini API adapter."""

    @classmethod
    def setup_class(cls):
        """Set up test environment for integration tests."""
        # Skip if no API key available
        if not os.getenv('GEMINI_API_KEY'):
            pytest.skip("GEMINI_API_KEY not available for integration tests")
        
        cls.config = GeminiConfig()
        cls.client = GeminiClient(cls.config)

    def test_successful_text_generation(self):
        """Test successful text generation through API."""
        # Arrange
        request = LLMRequest(
            prompt="Write a short greeting",
            max_tokens=50,
            temperature=0.7
        )

        # Act
        response = self.client.generate_text(request)

        # Assert
        assert response.content is not None
        assert len(response.content) > 0
        assert response.tokens_used > 0
        assert response.model.startswith('gemini')

    def test_rate_limit_handling(self):
        """Test rate limit enforcement in real conditions."""
        # Arrange - Make requests rapidly
        requests = [
            LLMRequest(prompt=f"Test {i}", max_tokens=10)
            for i in range(5)
        ]

        # Act & Assert - Should handle rate limits gracefully
        responses = []
        for request in requests:
            try:
                response = self.client.generate_text(request)
                responses.append(response)
            except RateLimitError:
                # Rate limiting is working correctly
                break

        # Verify at least some requests succeeded
        assert len(responses) > 0

    @pytest.mark.slow
    def test_large_content_processing(self):
        """Test processing of large content within limits."""
        # Arrange
        large_prompt = "Test prompt. " * 1000  # Large but within limits
        request = LLMRequest(
            prompt=large_prompt,
            max_tokens=100
        )

        # Act
        response = self.client.generate_text(request)

        # Assert
        assert response.content is not None
        assert response.tokens_used > 0
```

### Database Integration Testing (REQUIRED)
```python
"""
Database integration tests with transaction rollback.
Tests real database operations with proper cleanup.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.database.models import User, Content
from core.database.repositories import UserRepository


class TestDatabaseIntegration:
    """Integration tests for database operations."""

    @classmethod
    def setup_class(cls):
        """Set up test database."""
        cls.engine = create_engine('sqlite:///:memory:')
        cls.SessionLocal = sessionmaker(bind=cls.engine)
        
        # Create tables
        User.metadata.create_all(cls.engine)
        Content.metadata.create_all(cls.engine)

    def setup_method(self):
        """Set up database session with transaction."""
        self.session = self.SessionLocal()
        self.transaction = self.session.begin()
        self.repository = UserRepository(self.session)

    def test_user_creation_and_retrieval(self):
        """Test creating and retrieving user from database."""
        # Arrange
        user_data = {
            'username': 'testuser',
            'email': 'test@example.com'
        }

        # Act
        created_user = self.repository.create_user(user_data)
        retrieved_user = self.repository.get_user_by_id(created_user.id)

        # Assert
        assert retrieved_user is not None
        assert retrieved_user.username == user_data['username']
        assert retrieved_user.email == user_data['email']

    def teardown_method(self):
        """Clean up database transaction."""
        self.transaction.rollback()
        self.session.close()
```

## End-to-End Test Standards

### Workflow Testing (MANDATORY)
```python
"""
End-to-end tests for complete user workflows.
Tests integration of all system components.
"""
import pytest
from e2e.page_objects.content_generator_page import ContentGeneratorPage
from e2e.fixtures.test_data import get_test_content_request


class TestContentGenerationWorkflow:
    """End-to-end tests for content generation workflow."""

    def setup_method(self):
        """Set up test environment."""
        self.page = ContentGeneratorPage()

    def test_complete_content_generation_flow(self):
        """Test complete flow from request to generated content."""
        # Arrange
        test_request = get_test_content_request()

        # Act - Complete workflow
        self.page.navigate_to_generator()
        self.page.enter_content_request(test_request)
        self.page.click_generate()
        result = self.page.wait_for_generation_complete()

        # Assert - Verify complete workflow
        assert result.status == 'success'
        assert result.content is not None
        assert len(result.content) > 100
        assert result.generation_time < 30  # Within acceptable time

    def test_error_recovery_workflow(self):
        """Test error handling and recovery in complete workflow."""
        # Arrange
        invalid_request = get_invalid_test_request()

        # Act
        self.page.navigate_to_generator()
        self.page.enter_content_request(invalid_request)
        self.page.click_generate()

        # Assert - Verify graceful error handling
        error_message = self.page.get_error_message()
        assert "Invalid request" in error_message
        assert self.page.is_retry_available()
```

## Test Data Management

### Fixture Standards (REQUIRED)
```python
"""
Test fixtures for consistent test data.
Provides reusable test data across test suites.
"""
import pytest
from typing import Dict, Any
from datetime import datetime

from shared.models.llm_request import LLMRequest
from shared.models.user import User


@pytest.fixture
def sample_llm_request() -> LLMRequest:
    """Provide standard LLM request for testing."""
    return LLMRequest(
        prompt="Generate a test response",
        max_tokens=100,
        temperature=0.7,
        model="gemini-pro"
    )


@pytest.fixture
def sample_user_data() -> Dict[str, Any]:
    """Provide standard user data for testing."""
    return {
        'username': 'testuser',
        'email': 'test@example.com',
        'created_at': datetime.now(),
        'preferences': {
            'theme': 'dark',
            'language': 'en'
        }
    }


@pytest.fixture
def mock_api_response() -> Dict[str, Any]:
    """Provide standard API response for mocking."""
    return {
        'content': 'Generated test content',
        'usage': {
            'total_tokens': 75,
            'prompt_tokens': 25,
            'completion_tokens': 50
        },
        'model': 'gemini-pro-1.0',
        'finish_reason': 'stop'
    }
```

### Test Data Isolation (MANDATORY)
```python
# REQUIRED: Each test must use isolated test data
class TestUserService:
    def test_user_creation(self, sample_user_data):
        """Test with isolated data - no interference between tests."""
        # Each test gets fresh copy of test data
        user_data = sample_user_data.copy()
        user_data['username'] = f"test_{uuid4().hex[:8]}"
        
        # Test implementation with unique data
        user = self.service.create_user(user_data)
        assert user.username == user_data['username']

    def test_user_update(self, sample_user_data):
        """Test with different isolated data."""
        # Different test, fresh data - no contamination
        user_data = sample_user_data.copy()
        user_data['username'] = f"update_{uuid4().hex[:8]}"
        
        # Test implementation
        user = self.service.create_user(user_data)
        updated = self.service.update_user(user.id, {'email': 'new@example.com'})
        assert updated.email == 'new@example.com'
```

## Mock and Stub Standards

### Mocking Best Practices (MANDATORY)
```python
"""
Proper mocking techniques for isolated unit tests.
Ensures tests are fast, reliable, and deterministic.
"""
from unittest.mock import Mock, patch, MagicMock
import pytest


class TestWithProperMocking:
    """Demonstrate proper mocking techniques."""

    def test_with_mock_injection(self):
        """Test using mock injection (PREFERRED)."""
        # Arrange - Create mocks
        mock_llm = Mock(spec=LLMProvider)
        mock_llm.generate_text.return_value = "mocked response"
        
        # Inject mock through constructor (dependency injection)
        service = TextProcessor(mock_llm)
        
        # Act
        result = service.process_text("test input")
        
        # Assert
        assert result == "mocked response"
        mock_llm.generate_text.assert_called_once_with("test input")

    @patch('adapters.gemini_api.client.requests.post')
    def test_with_patch_decorator(self, mock_post):
        """Test using patch decorator for external dependencies."""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = {'text': 'mocked API response'}
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        client = GeminiClient()
        
        # Act
        result = client.make_request("test prompt")
        
        # Assert
        assert result['text'] == 'mocked API response'
        mock_post.assert_called_once()

    def test_with_context_manager_patch(self):
        """Test using patch as context manager."""
        with patch('os.getenv') as mock_getenv:
            # Arrange
            mock_getenv.return_value = 'test_api_key'
            
            # Act
            config = Config()
            
            # Assert
            assert config.api_key == 'test_api_key'
            mock_getenv.assert_called_with('API_KEY')
```

### Mock Validation (REQUIRED)
```python
def test_mock_specifications():
    """Ensure mocks match actual interface specifications."""
    # REQUIRED: Use spec parameter to enforce interface compliance
    mock_llm = Mock(spec=LLMProvider)
    
    # This will work - method exists in spec
    mock_llm.generate_text.return_value = "response"
    
    # This will raise AttributeError - method doesn't exist in spec
    with pytest.raises(AttributeError):
        mock_llm.nonexistent_method()
```

## Performance Testing Standards

### Performance Benchmarks (REQUIRED)
```python
"""
Performance tests to ensure acceptable response times.
"""
import time
import pytest
from statistics import mean, median


class TestPerformance:
    """Performance tests for critical operations."""

    @pytest.mark.performance
    def test_text_generation_performance(self):
        """Test text generation performance within acceptable limits."""
        # Arrange
        client = GeminiClient()
        request = LLMRequest(prompt="Generate test text", max_tokens=100)
        
        # Act - Measure multiple runs
        execution_times = []
        for _ in range(5):
            start_time = time.time()
            response = client.generate_text(request)
            end_time = time.time()
            execution_times.append(end_time - start_time)
        
        # Assert - Performance requirements
        avg_time = mean(execution_times)
        median_time = median(execution_times)
        max_time = max(execution_times)
        
        assert avg_time < 5.0, f"Average response time {avg_time}s exceeds 5s limit"
        assert median_time < 4.0, f"Median response time {median_time}s exceeds 4s limit"
        assert max_time < 10.0, f"Max response time {max_time}s exceeds 10s limit"

    @pytest.mark.performance
    def test_concurrent_request_handling(self):
        """Test system performance under concurrent load."""
        import concurrent.futures
        
        def make_request():
            client = GeminiClient()
            request = LLMRequest(prompt="Concurrent test", max_tokens=50)
            start_time = time.time()
            response = client.generate_text(request)
            return time.time() - start_time
        
        # Act - Execute concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            execution_times = [future.result() for future in futures]
        
        # Assert - Concurrent performance requirements
        avg_concurrent_time = mean(execution_times)
        assert avg_concurrent_time < 8.0, "Concurrent performance degraded too much"
```

## Test Execution Standards

### Continuous Testing Protocol (MANDATORY)
```bash
#!/bin/bash
# tests/run_tests.sh - Complete test execution pipeline

echo "Starting comprehensive test suite..."

# 1. Fast unit tests first
echo "Running unit tests..."
pytest tests/unit/ -v --tb=short
if [ $? -ne 0 ]; then
    echo "Unit tests failed. Stopping execution."
    exit 1
fi

# 2. Pylint quality check
echo "Running pylint quality check..."
pylint --score=y --fail-under=10.0 $(find . -name "*.py" -not -path "./tests/*")
if [ $? -ne 0 ]; then
    echo "Pylint quality check failed. Stopping execution."
    exit 1
fi

# 3. Integration tests
echo "Running integration tests..."
pytest tests/integration/ -v --tb=short
if [ $? -ne 0 ]; then
    echo "Integration tests failed. Stopping execution."
    exit 1
fi

# 4. Coverage check
echo "Running coverage analysis..."
coverage run -m pytest tests/unit/ tests/integration/
coverage report --fail-under=90
if [ $? -ne 0 ]; then
    echo "Coverage requirements not met. Stopping execution."
    exit 1
fi

# 5. End-to-end tests (if available)
if [ -d "tests/e2e" ]; then
    echo "Running end-to-end tests..."
    pytest tests/e2e/ -v --tb=short -m "not slow"
fi

echo "All tests passed successfully!"
```

### Test Configuration (REQUIRED)
```ini
# pytest.ini - Test configuration
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --color=yes
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    performance: Performance tests
    slow: Slow-running tests
    skip_ci: Skip in CI environment
```

## Quality Validation Checklist (MANDATORY)

Before any code submission:

- [ ] **All pytest tests pass** (100% success rate)
- [ ] **Perfect pylint score** (10.00/10)
- [ ] **Coverage meets minimum** (90% line coverage)
- [ ] **Unit tests written** for all public methods
- [ ] **Integration tests written** for external dependencies
- [ ] **Error paths tested** with proper exception handling
- [ ] **Performance tests pass** within acceptable limits
- [ ] **Test data isolated** between test cases
- [ ] **Mocks properly specified** with interface compliance
- [ ] **Test documentation complete** with clear descriptions

## Test Failure Resolution Protocol

### Failure Analysis (REQUIRED)
```python
def analyze_test_failure(test_result: TestResult) -> FailureAnalysis:
    """
    Analyze test failure to determine root cause and solution.
    
    Args:
        test_result: Failed test result with details
        
    Returns:
        FailureAnalysis with cause and recommended actions
    """
    analysis = FailureAnalysis()
    
    if test_result.error_type == 'AssertionError':
        analysis.cause = 'Logic error or incorrect expectations'
        analysis.actions = ['Review test logic', 'Verify expected behavior']
    elif test_result.error_type == 'ImportError':
        analysis.cause = 'Missing dependency or import path error'
        analysis.actions = ['Check dependencies', 'Verify import paths']
    elif test_result.error_type == 'AttributeError':
        analysis.cause = 'Interface mismatch or missing implementation'
        analysis.actions = ['Verify interface compliance', 'Check implementation']
    
    return analysis
```

### Remediation Requirements (NON-NEGOTIABLE)
1. **Fix immediately** - All test failures must be resolved before proceeding
2. **Root cause analysis** - Understand why the test failed, not just fix symptoms
3. **Additional tests** - Add tests to prevent similar failures
4. **Documentation update** - Update docs if behavior changed
5. **Re-run full suite** - Ensure fix doesn't break other tests

**REMEMBER**: Testing is not optional - it's the foundation of reliable software. These standards ensure that all code meets the highest quality standards before integration.