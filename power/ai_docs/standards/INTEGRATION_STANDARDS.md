# INTEGRATION STANDARDS

**MANDATORY**: All code integration and GitHub operations MUST follow these standards for quality assurance and workflow consistency.

## GitHub Workflow Requirements

### Branch Strategy (NON-NEGOTIABLE)
```
main (protected)
├── develop (integration branch)
└── feature/agent-{task-id} (individual agent branches)
    └── feature/agent-{task-id}-{subtask} (sub-feature branches)
```

### Branch Protection Rules (ABSOLUTE REQUIREMENT)
```yaml
# .github/branch-protection.yml
main:
  required_status_checks:
    strict: true
    contexts:
      - "test-suite"
      - "pylint-check" 
      - "integration-validation"
  enforce_admins: true
  required_pull_request_reviews:
    required_approving_review_count: 1
    dismiss_stale_reviews: true
  restrictions: null
  
develop:
  required_status_checks:
    strict: true
    contexts:
      - "test-suite"
      - "pylint-check"
  enforce_admins: false
```

### Pull Request Standards (MANDATORY)
```markdown
# PR Template (REQUIRED FORMAT)

## Summary
<!-- Brief description of changes and motivation -->

## Changes Made
- [ ] **Files Modified**: List all modified files with brief description
- [ ] **Files Added**: List all new files with purpose  
- [ ] **Files Deleted**: List deleted files with reason
- [ ] **Dependencies Updated**: Any new or updated dependencies

## Quality Validation
- [ ] **All tests pass** (pytest: 100% success rate)
- [ ] **Perfect pylint score** (10.00/10)
- [ ] **Coverage maintained** (minimum 90%)
- [ ] **Integration tests pass** (all external integrations validated)
- [ ] **No regression detected** (existing functionality preserved)

## Architecture Compliance
- [ ] **Layer boundaries respected** (no core ↔ adapter violations)
- [ ] **Interface contracts maintained** (shared interfaces implemented)
- [ ] **Configuration properly isolated** (no hardcoded values)
- [ ] **Error handling follows patterns** (proper exception translation)

## Testing Validation
- [ ] **Unit tests written** for all new functionality
- [ ] **Integration tests updated** for external dependencies
- [ ] **Error paths tested** with proper exception scenarios
- [ ] **Performance requirements met** (response times within limits)

## Documentation Updates
- [ ] **Code documentation complete** (docstrings for all functions)
- [ ] **Architecture docs updated** (if applicable)
- [ ] **API documentation updated** (if interfaces changed)
- [ ] **README updates** (if user-facing changes)

## Rollback Plan
<!-- Describe how to rollback if issues are discovered -->
- **Rollback commit**: [commit SHA]
- **Affected systems**: [list of affected components]
- **Validation steps**: [steps to verify rollback success]

## Test Plan
<!-- Checklist for manual testing if automated tests are insufficient -->
- [ ] **Functional testing**: [specific test cases]
- [ ] **Integration testing**: [external system validations]
- [ ] **Performance testing**: [load/stress test scenarios]
- [ ] **Security testing**: [security validation steps]

🤖 Generated with [Claude Code](https://claude.ai/code)
```

## Integration Worker Standards

### Validation Pipeline (ABSOLUTE REQUIREMENT)
```python
"""
Integration worker for comprehensive code validation.
Ensures all submissions meet quality and architecture standards.
"""
from typing import Dict, List, Any
from dataclasses import dataclass
import subprocess
import sys


@dataclass
class ValidationResult:
    """Results of code validation process."""
    passed: bool
    pylint_score: float
    test_success_rate: float
    coverage_percentage: float
    architecture_violations: List[str]
    integration_failures: List[str]
    performance_issues: List[str]


class IntegrationWorker:
    """
    Validates code submissions against all quality standards.
    MANDATORY for all code integration.
    """
    
    def __init__(self, workspace_path: str):
        """
        Initialize integration worker.
        
        Args:
            workspace_path: Path to agent workspace for validation
        """
        self.workspace_path = workspace_path
        self.validation_results = ValidationResult(
            passed=False,
            pylint_score=0.0,
            test_success_rate=0.0,
            coverage_percentage=0.0,
            architecture_violations=[],
            integration_failures=[],
            performance_issues=[]
        )
    
    def validate_submission(self) -> ValidationResult:
        """
        Run comprehensive validation on code submission.
        
        Returns:
            ValidationResult with detailed pass/fail information
        """
        try:
            # 1. MANDATORY: Pylint quality check
            self._validate_pylint_quality()
            
            # 2. MANDATORY: Test suite validation
            self._validate_test_suite()
            
            # 3. MANDATORY: Architecture compliance
            self._validate_architecture_compliance()
            
            # 4. MANDATORY: Integration testing
            self._validate_integration_tests()
            
            # 5. MANDATORY: Performance validation
            self._validate_performance_requirements()
            
            # 6. MANDATORY: Security validation
            self._validate_security_requirements()
            
            # Overall pass/fail determination
            self.validation_results.passed = self._determine_overall_pass()
            
        except Exception as e:
            self.validation_results.passed = False
            self.validation_results.integration_failures.append(f"Validation error: {e}")
        
        return self.validation_results
    
    def _validate_pylint_quality(self) -> None:
        """Validate pylint score meets perfect 10.00/10 requirement."""
        try:
            result = subprocess.run(
                ['pylint', '--score=y', f'{self.workspace_path}/**/*.py'],
                capture_output=True,
                text=True,
                check=False
            )
            
            # Extract score from pylint output
            for line in result.stdout.split('\n'):
                if 'Your code has been rated at' in line:
                    score_str = line.split(' ')[6].split('/')[0]
                    self.validation_results.pylint_score = float(score_str)
                    break
            
            # MANDATORY: Must achieve perfect 10.00/10
            if self.validation_results.pylint_score < 10.0:
                self.validation_results.integration_failures.append(
                    f"Pylint score {self.validation_results.pylint_score} below required 10.00"
                )
                
        except Exception as e:
            self.validation_results.integration_failures.append(f"Pylint validation failed: {e}")
    
    def _validate_test_suite(self) -> None:
        """Validate test suite passes with 100% success rate."""
        try:
            result = subprocess.run(
                ['python', '-m', 'pytest', f'{self.workspace_path}/tests/', '-v', '--tb=short'],
                capture_output=True,
                text=True,
                check=False
            )
            
            # Parse test results
            if result.returncode == 0:
                self.validation_results.test_success_rate = 100.0
            else:
                # Extract failure information
                self.validation_results.test_success_rate = self._parse_test_success_rate(result.stdout)
                self.validation_results.integration_failures.append(
                    f"Test suite failed: {result.stdout}"
                )
                
        except Exception as e:
            self.validation_results.integration_failures.append(f"Test validation failed: {e}")
    
    def _validate_architecture_compliance(self) -> None:
        """Validate architecture compliance using static analysis."""
        violations = []
        
        try:
            # Check for forbidden cross-layer imports
            violations.extend(self._check_cross_layer_imports())
            
            # Check for proper interface implementation
            violations.extend(self._check_interface_compliance())
            
            # Check for configuration isolation
            violations.extend(self._check_configuration_isolation())
            
            # Check for proper error handling patterns
            violations.extend(self._check_error_handling_patterns())
            
            self.validation_results.architecture_violations = violations
            
        except Exception as e:
            self.validation_results.integration_failures.append(f"Architecture validation failed: {e}")
    
    def _check_cross_layer_imports(self) -> List[str]:
        """Check for forbidden cross-layer imports."""
        violations = []
        
        # Use grep to find forbidden import patterns
        try:
            # Check core importing from adapters
            result = subprocess.run(
                ['grep', '-r', 'from adapters', f'{self.workspace_path}/core/'],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                violations.append("Core layer imports from adapters layer (FORBIDDEN)")
            
            # Check adapters importing from core
            result = subprocess.run(
                ['grep', '-r', 'from core', f'{self.workspace_path}/adapters/'],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                violations.append("Adapters layer imports from core layer (FORBIDDEN)")
                
        except Exception as e:
            violations.append(f"Cross-layer import check failed: {e}")
        
        return violations
    
    def _validate_integration_tests(self) -> None:
        """Run integration tests to validate external system connections."""
        try:
            result = subprocess.run(
                ['python', '-m', 'pytest', f'{self.workspace_path}/tests/integration/', '-v'],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                self.validation_results.integration_failures.append(
                    f"Integration tests failed: {result.stdout}"
                )
                
        except Exception as e:
            self.validation_results.integration_failures.append(f"Integration test validation failed: {e}")
    
    def _validate_performance_requirements(self) -> None:
        """Validate performance requirements are met."""
        try:
            # Run performance tests
            result = subprocess.run(
                ['python', '-m', 'pytest', f'{self.workspace_path}/tests/', '-m', 'performance'],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                self.validation_results.performance_issues.append(
                    f"Performance requirements not met: {result.stdout}"
                )
                
        except Exception as e:
            self.validation_results.performance_issues.append(f"Performance validation failed: {e}")
    
    def _determine_overall_pass(self) -> bool:
        """Determine if submission passes all validation requirements."""
        return (
            self.validation_results.pylint_score == 10.0 and
            self.validation_results.test_success_rate == 100.0 and
            len(self.validation_results.architecture_violations) == 0 and
            len(self.validation_results.integration_failures) == 0 and
            len(self.validation_results.performance_issues) == 0
        )
```

## Automated GitHub Actions (MANDATORY)

### CI/CD Pipeline Configuration
```yaml
# .github/workflows/validation.yml
name: Code Validation Pipeline

on:
  pull_request:
    branches: [ main, develop ]
  push:
    branches: [ main, develop ]

jobs:
  quality-check:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pylint pytest coverage
    
    - name: Run pylint quality check
      run: |
        pylint --score=y --fail-under=10.0 $(find . -name "*.py" -not -path "./tests/*")
    
    - name: Run test suite
      run: |
        python -m pytest tests/ -v --tb=short
    
    - name: Check code coverage
      run: |
        coverage run -m pytest tests/
        coverage report --fail-under=90
    
    - name: Validate architecture compliance
      run: |
        python tools/validate_architecture.py
  
  integration-tests:
    needs: quality-check
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run integration tests
      env:
        GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      run: |
        python -m pytest tests/integration/ -v
    
    - name: Run performance tests
      run: |
        python -m pytest tests/ -m performance -v

  security-scan:
    needs: quality-check
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Run security scan
      uses: bandit/bandit-action@main
      with:
        path: "."
        config_file: ".bandit"
    
    - name: Check for secrets
      uses: trufflesecurity/trufflehog@main
      with:
        path: ./
        base: main
        head: HEAD
```

## Code Review Standards

### Review Checklist (MANDATORY)
```markdown
# Code Review Checklist

## Architecture Review
- [ ] **Layer separation maintained** (core/adapters/shared boundaries respected)
- [ ] **Interface contracts implemented** correctly
- [ ] **Dependency injection used** appropriately
- [ ] **Configuration properly isolated** from business logic

## Code Quality Review
- [ ] **Pylint score 10.00/10** achieved
- [ ] **Test coverage adequate** (minimum 90%)
- [ ] **All tests passing** (100% success rate)
- [ ] **Code follows standards** (naming, structure, documentation)

## Functional Review
- [ ] **Requirements met** completely
- [ ] **Error handling comprehensive** and appropriate
- [ ] **Performance acceptable** for expected load
- [ ] **Security considerations** addressed

## Integration Review
- [ ] **External API calls** properly abstracted
- [ ] **Database operations** follow patterns
- [ ] **Rate limiting implemented** correctly
- [ ] **Caching strategies** appropriate

## Documentation Review
- [ ] **Code documentation complete** (all functions documented)
- [ ] **Architecture decisions explained** where necessary
- [ ] **API documentation updated** if interfaces changed
- [ ] **Examples provided** for complex functionality
```

### Review Process Requirements
```python
"""
Code review automation and enforcement.
Ensures all submissions receive proper review before integration.
"""
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class ReviewResult:
    """Results of code review process."""
    approved: bool
    reviewer: str
    comments: List[str]
    required_changes: List[str]
    approval_timestamp: str


class ReviewEnforcement:
    """
    Enforces code review requirements for all PRs.
    MANDATORY for main branch protection.
    """
    
    REQUIRED_REVIEWERS = {
        'core': ['architecture-team', 'senior-developers'],
        'adapters': ['integration-team', 'api-experts'],
        'shared': ['architecture-team', 'interface-designers']
    }
    
    def __init__(self, pr_info: Dict[str, Any]):
        """
        Initialize review enforcement.
        
        Args:
            pr_info: Pull request information including files changed
        """
        self.pr_info = pr_info
        self.affected_layers = self._identify_affected_layers()
        self.required_reviewers = self._determine_required_reviewers()
    
    def validate_review_requirements(self) -> bool:
        """
        Validate that PR has received adequate review.
        
        Returns:
            True if review requirements are met
        """
        # Check for required approvals
        if not self._has_required_approvals():
            return False
        
        # Check for unresolved comments
        if self._has_unresolved_comments():
            return False
        
        # Check for blocking changes requested
        if self._has_blocking_changes_requested():
            return False
        
        return True
    
    def _identify_affected_layers(self) -> List[str]:
        """Identify which architecture layers are affected by changes."""
        layers = []
        
        for file_path in self.pr_info.get('changed_files', []):
            if file_path.startswith('core/'):
                layers.append('core')
            elif file_path.startswith('adapters/'):
                layers.append('adapters')
            elif file_path.startswith('shared/'):
                layers.append('shared')
        
        return list(set(layers))  # Remove duplicates
```

## Rollback Procedures

### Emergency Rollback Protocol (CRITICAL)
```bash
#!/bin/bash
# scripts/emergency_rollback.sh - Emergency rollback procedures

set -e

ROLLBACK_TARGET_COMMIT="$1"
BRANCH="${2:-main}"

if [ -z "$ROLLBACK_TARGET_COMMIT" ]; then
    echo "Usage: $0 <commit-sha> [branch]"
    echo "Example: $0 abc123def main"
    exit 1
fi

echo "🚨 EMERGENCY ROLLBACK INITIATED 🚨"
echo "Target commit: $ROLLBACK_TARGET_COMMIT"
echo "Target branch: $BRANCH"

# 1. Validate target commit exists
if ! git cat-file -e "$ROLLBACK_TARGET_COMMIT" 2>/dev/null; then
    echo "❌ Error: Commit $ROLLBACK_TARGET_COMMIT does not exist"
    exit 1
fi

# 2. Create backup of current state
BACKUP_BRANCH="backup-before-rollback-$(date +%Y%m%d-%H%M%S)"
git checkout -b "$BACKUP_BRANCH"
git checkout "$BRANCH"

echo "✅ Backup created: $BACKUP_BRANCH"

# 3. Perform rollback
echo "🔄 Rolling back to $ROLLBACK_TARGET_COMMIT..."
git reset --hard "$ROLLBACK_TARGET_COMMIT"

# 4. Force push (DANGEROUS - only for emergencies)
read -p "⚠️  This will FORCE PUSH to $BRANCH. Are you sure? (type 'YES'): " confirmation
if [ "$confirmation" != "YES" ]; then
    echo "❌ Rollback cancelled"
    git checkout "$BACKUP_BRANCH"
    exit 1
fi

git push --force-with-lease origin "$BRANCH"

echo "✅ Rollback completed successfully"
echo "🔍 Backup available at: $BACKUP_BRANCH"

# 5. Validate rollback
echo "🧪 Running validation tests..."
python -m pytest tests/ -x --tb=short
if [ $? -eq 0 ]; then
    echo "✅ Rollback validation passed"
else
    echo "❌ Rollback validation failed - manual intervention required"
    exit 1
fi

echo "🎉 Emergency rollback completed successfully"
```

### Safe Rollback Protocol (PREFERRED)
```bash
#!/bin/bash
# scripts/safe_rollback.sh - Safe rollback using revert

set -e

PROBLEMATIC_COMMIT="$1"
BRANCH="${2:-main}"

if [ -z "$PROBLEMATIC_COMMIT" ]; then
    echo "Usage: $0 <commit-sha> [branch]"
    exit 1
fi

echo "🔄 SAFE ROLLBACK INITIATED"
echo "Reverting commit: $PROBLEMATIC_COMMIT"
echo "Target branch: $BRANCH"

# 1. Ensure we're on the correct branch
git checkout "$BRANCH"
git pull origin "$BRANCH"

# 2. Create revert commit
echo "📝 Creating revert commit..."
git revert --no-edit "$PROBLEMATIC_COMMIT"

# 3. Run validation tests
echo "🧪 Running validation tests..."
python -m pytest tests/ -v
if [ $? -ne 0 ]; then
    echo "❌ Tests failed after revert - manual intervention required"
    exit 1
fi

# 4. Run pylint check
echo "🔍 Running quality checks..."
pylint --score=y --fail-under=10.0 $(find . -name "*.py" -not -path "./tests/*")
if [ $? -ne 0 ]; then
    echo "❌ Quality checks failed after revert"
    exit 1
fi

# 5. Push revert commit
git push origin "$BRANCH"

echo "✅ Safe rollback completed successfully"
```

## Deployment Standards

### Pre-Deployment Validation (ABSOLUTE REQUIREMENT)
```python
"""
Pre-deployment validation to ensure system stability.
MANDATORY before any production deployment.
"""
from typing import Dict, List, Any
import subprocess
import requests


class DeploymentValidator:
    """
    Validates system readiness for deployment.
    All checks must pass before deployment proceeds.
    """
    
    def __init__(self, environment: str):
        """
        Initialize deployment validator.
        
        Args:
            environment: Target deployment environment (staging/production)
        """
        self.environment = environment
        self.validation_results = {}
    
    def validate_deployment_readiness(self) -> bool:
        """
        Run comprehensive deployment readiness validation.
        
        Returns:
            True if all validation checks pass
        """
        checks = [
            self._validate_test_suite,
            self._validate_code_quality,
            self._validate_dependencies,
            self._validate_configuration,
            self._validate_external_services,
            self._validate_performance,
            self._validate_security
        ]
        
        all_passed = True
        
        for check in checks:
            try:
                result = check()
                check_name = check.__name__
                self.validation_results[check_name] = result
                
                if not result:
                    all_passed = False
                    print(f"❌ {check_name} failed")
                else:
                    print(f"✅ {check_name} passed")
                    
            except Exception as e:
                all_passed = False
                print(f"❌ {check.__name__} error: {e}")
                self.validation_results[check.__name__] = False
        
        return all_passed
    
    def _validate_test_suite(self) -> bool:
        """Validate that all tests pass."""
        result = subprocess.run(
            ['python', '-m', 'pytest', 'tests/', '-v'],
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode == 0
    
    def _validate_code_quality(self) -> bool:
        """Validate code quality standards."""
        result = subprocess.run(
            ['pylint', '--score=y', '--fail-under=10.0'] + 
            ['$(find . -name "*.py" -not -path "./tests/*")'],
            shell=True,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode == 0
    
    def _validate_external_services(self) -> bool:
        """Validate external service connectivity."""
        services = {
            'gemini_api': 'https://generativelanguage.googleapis.com',
            'openai_api': 'https://api.openai.com/v1/models'
        }
        
        for service, url in services.items():
            try:
                response = requests.get(url, timeout=10)
                if response.status_code >= 400:
                    print(f"Service {service} returned {response.status_code}")
                    return False
            except requests.RequestException as e:
                print(f"Service {service} connectivity failed: {e}")
                return False
        
        return True
```

## Integration Validation Checklist (MANDATORY)

Before any code integration:

- [ ] **Perfect pylint score** (10.00/10) achieved
- [ ] **All tests pass** (100% success rate)
- [ ] **Integration tests pass** with real external services
- [ ] **Architecture compliance verified** (no layer violations)
- [ ] **Performance requirements met** (response times acceptable)
- [ ] **Security scan passed** (no vulnerabilities detected)
- [ ] **Code review completed** by qualified reviewers
- [ ] **Documentation updated** for any interface changes
- [ ] **Rollback plan documented** with clear procedures
- [ ] **Deployment validation passed** for target environment

## Quality Gate Enforcement

### Automatic Rejection Criteria (NON-NEGOTIABLE)
- Pylint score below 10.00/10
- Any test failures
- Architecture layer violations
- Security vulnerabilities detected
- Missing required documentation
- Failed integration tests
- Performance degradation detected
- Missing or inadequate code review

### Manual Review Requirements
- All changes to shared interfaces
- New external API integrations
- Database schema modifications
- Security-related changes
- Performance-critical modifications

**REMEMBER**: Integration standards ensure that all code meets the highest quality standards before reaching production. These requirements are non-negotiable and protect system stability and maintainability.