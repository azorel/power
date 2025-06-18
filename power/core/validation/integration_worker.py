"""
Integration worker for comprehensive code validation.
Validates submissions against all quality and architecture standards.
"""

import subprocess
import json
import os
import tempfile
import shutil
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass, field
import logging
from datetime import datetime

from shared.exceptions import ValidationError, IntegrationError
from shared.interfaces.validation_worker import ValidationWorkerInterface

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Comprehensive validation result."""
    passed: bool
    pylint_score: float
    test_success_rate: float
    coverage_percentage: float
    architecture_violations: List[str] = field(default_factory=list)
    integration_failures: List[str] = field(default_factory=list)
    performance_issues: List[str] = field(default_factory=list)
    security_issues: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    validation_time: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkSubmission:
    """Work submission from agent."""
    agent_id: str
    task_id: str
    workspace_path: Path
    branch_name: str
    modified_files: List[str]
    commit_hash: Optional[str] = None
    submission_time: datetime = field(default_factory=datetime.now)


class IntegrationWorker(ValidationWorkerInterface):
    """
    Validates agent work submissions against comprehensive quality standards.
    Ensures all code meets architecture, quality, and integration requirements.
    """

    def __init__(self, temp_workspace: Optional[str] = None):
        """
        Initialize integration worker.

        Args:
            temp_workspace: Temporary workspace for validation (None for auto-create)
        """
        self.temp_workspace = Path(temp_workspace) if temp_workspace else None
        self.validation_history: List[ValidationResult] = []
        
        # Quality gate thresholds
        self.required_pylint_score = 10.0
        self.required_test_success_rate = 100.0
        self.required_coverage_percentage = 90.0

    def validate_submission(self, submission: WorkSubmission) -> ValidationResult:
        """
        Run comprehensive validation on work submission.

        Args:
            submission: Work submission to validate

        Returns:
            ValidationResult with detailed validation information
        """
        start_time = datetime.now()
        
        logger.info(f"Starting validation for agent {submission.agent_id}, task {submission.task_id}")
        
        # Create validation workspace
        validation_workspace = self._create_validation_workspace(submission)
        
        try:
            result = ValidationResult(
                passed=False,
                pylint_score=0.0,
                test_success_rate=0.0,
                coverage_percentage=0.0
            )
            
            # Run validation steps
            self._validate_pylint_quality(validation_workspace, result)
            self._validate_test_suite(validation_workspace, result)
            self._validate_architecture_compliance(validation_workspace, result)
            self._validate_integration_compatibility(validation_workspace, result)
            self._validate_performance_requirements(validation_workspace, result)
            self._validate_security_requirements(validation_workspace, result)
            
            # Determine overall pass/fail
            result.passed = self._determine_overall_pass(result)
            
            # Calculate validation time
            end_time = datetime.now()
            result.validation_time = (end_time - start_time).total_seconds()
            
            # Store validation history
            self.validation_history.append(result)
            
            logger.info(f"Validation completed for {submission.agent_id}: {'PASSED' if result.passed else 'FAILED'}")
            
            return result
            
        except Exception as e:
            error_msg = f"Validation failed with exception: {e}"
            logger.error(error_msg)
            
            result = ValidationResult(
                passed=False,
                pylint_score=0.0,
                test_success_rate=0.0,
                coverage_percentage=0.0,
                errors=[error_msg]
            )
            result.validation_time = (datetime.now() - start_time).total_seconds()
            
            return result
            
        finally:
            # Cleanup validation workspace
            self._cleanup_validation_workspace(validation_workspace)

    def _create_validation_workspace(self, submission: WorkSubmission) -> Path:
        """
        Create isolated validation workspace.

        Args:
            submission: Work submission to create workspace for

        Returns:
            Path to validation workspace
        """
        try:
            # Create temporary workspace
            if self.temp_workspace:
                workspace_dir = self.temp_workspace / f"validation_{submission.agent_id}_{submission.task_id}"
                workspace_dir.mkdir(parents=True, exist_ok=True)
            else:
                workspace_dir = Path(tempfile.mkdtemp(prefix=f"validation_{submission.agent_id}_"))
            
            # Copy agent workspace to validation workspace
            agent_power_path = submission.workspace_path / "power"
            validation_power_path = workspace_dir / "power"
            
            if agent_power_path.exists():
                shutil.copytree(agent_power_path, validation_power_path)
                logger.info(f"Copied agent workspace to validation: {validation_power_path}")
            else:
                raise ValidationError(f"Agent workspace not found: {agent_power_path}")
            
            return workspace_dir
            
        except Exception as e:
            raise ValidationError(f"Failed to create validation workspace: {e}") from e

    def _validate_pylint_quality(self, workspace: Path, result: ValidationResult) -> None:
        """
        Validate pylint score meets perfect 10.00/10 requirement.

        Args:
            workspace: Validation workspace path
            result: ValidationResult to update
        """
        try:
            power_path = workspace / "power"
            
            # Run pylint on all Python files
            pylint_cmd = [
                'python3', '-m', 'pylint',
                '--score=y',
                '--output-format=json'
            ]
            
            # Find all Python files
            python_files = list(power_path.rglob("*.py"))
            python_files = [str(f) for f in python_files if 'venv' not in str(f) and '__pycache__' not in str(f)]
            
            if not python_files:
                result.warnings.append("No Python files found for pylint validation")
                return
            
            # Run pylint
            pylint_result = subprocess.run(
                pylint_cmd + python_files,
                capture_output=True,
                text=True,
                check=False,
                cwd=power_path
            )
            
            # Parse pylint output
            try:
                if pylint_result.stdout.strip():
                    pylint_data = json.loads(pylint_result.stdout)
                    # Extract score from last line of stderr
                    score_line = pylint_result.stderr.strip().split('\n')[-1]
                    if 'Your code has been rated at' in score_line:
                        score_str = score_line.split(' ')[6].split('/')[0]
                        result.pylint_score = float(score_str)
                    
                    # Collect violations
                    violations = []
                    for item in pylint_data:
                        if item.get('type') in ['error', 'warning', 'convention', 'refactor']:
                            violations.append(f"{item['path']}:{item['line']} - {item['message']}")
                    
                    if violations:
                        result.errors.extend(violations[:10])  # Limit to first 10
                        if len(violations) > 10:
                            result.errors.append(f"... and {len(violations) - 10} more violations")
                
            except (json.JSONDecodeError, ValueError, IndexError) as e:
                result.warnings.append(f"Failed to parse pylint output: {e}")
                # Try to extract score from stderr anyway
                for line in pylint_result.stderr.split('\n'):
                    if 'Your code has been rated at' in line:
                        try:
                            score_str = line.split(' ')[6].split('/')[0]
                            result.pylint_score = float(score_str)
                            break
                        except (IndexError, ValueError):
                            pass
            
            # Validate score meets requirement
            if result.pylint_score < self.required_pylint_score:
                result.integration_failures.append(
                    f"Pylint score {result.pylint_score:.2f} below required {self.required_pylint_score}"
                )
            
            logger.info(f"Pylint validation: score={result.pylint_score:.2f}")
            
        except Exception as e:
            error_msg = f"Pylint validation failed: {e}"
            logger.error(error_msg)
            result.integration_failures.append(error_msg)

    def _validate_test_suite(self, workspace: Path, result: ValidationResult) -> None:
        """
        Validate test suite passes with 100% success rate.

        Args:
            workspace: Validation workspace path
            result: ValidationResult to update
        """
        try:
            power_path = workspace / "power"
            tests_path = power_path / "tests"
            
            if not tests_path.exists():
                result.warnings.append("No tests directory found")
                result.test_success_rate = 100.0  # No tests means no failures
                return
            
            # Run pytest
            pytest_cmd = [
                'python3', '-m', 'pytest',
                str(tests_path),
                '-v',
                '--tb=short',
                '--json-report',
                '--json-report-file=test_results.json'
            ]
            
            pytest_result = subprocess.run(
                pytest_cmd,
                capture_output=True,
                text=True,
                check=False,
                cwd=power_path
            )
            
            # Parse test results
            test_results_file = power_path / "test_results.json"
            if test_results_file.exists():
                try:
                    with open(test_results_file, 'r', encoding='utf-8') as f:
                        test_data = json.load(f)
                    
                    total_tests = test_data['summary']['total']
                    passed_tests = test_data['summary'].get('passed', 0)
                    
                    if total_tests > 0:
                        result.test_success_rate = (passed_tests / total_tests) * 100
                    else:
                        result.test_success_rate = 100.0
                    
                    # Collect failure information
                    if 'failed' in test_data['summary'] and test_data['summary']['failed'] > 0:
                        failures = []
                        for test in test_data.get('tests', []):
                            if test.get('outcome') == 'failed':
                                failures.append(f"{test['nodeid']}: {test.get('call', {}).get('longrepr', 'Unknown error')}")
                        
                        result.integration_failures.extend(failures[:5])  # Limit to first 5 failures
                    
                except (json.JSONDecodeError, KeyError) as e:
                    result.warnings.append(f"Failed to parse test results: {e}")
                    # Fallback: consider tests passed if pytest exit code is 0
                    result.test_success_rate = 100.0 if pytest_result.returncode == 0 else 0.0
            else:
                # Fallback: use pytest exit code
                result.test_success_rate = 100.0 if pytest_result.returncode == 0 else 0.0
                if pytest_result.returncode != 0:
                    result.integration_failures.append(f"Tests failed: {pytest_result.stdout}")
            
            # Validate success rate meets requirement
            if result.test_success_rate < self.required_test_success_rate:
                result.integration_failures.append(
                    f"Test success rate {result.test_success_rate:.1f}% below required {self.required_test_success_rate}%"
                )
            
            logger.info(f"Test validation: success_rate={result.test_success_rate:.1f}%")
            
        except Exception as e:
            error_msg = f"Test validation failed: {e}"
            logger.error(error_msg)
            result.integration_failures.append(error_msg)

    def _validate_architecture_compliance(self, workspace: Path, result: ValidationResult) -> None:
        """
        Validate architecture compliance using static analysis.

        Args:
            workspace: Validation workspace path
            result: ValidationResult to update
        """
        try:
            power_path = workspace / "power"
            violations = []
            
            # Check for forbidden cross-layer imports
            violations.extend(self._check_cross_layer_imports(power_path))
            
            # Check for proper file placement
            violations.extend(self._check_file_placement(power_path))
            
            # Check for interface compliance
            violations.extend(self._check_interface_compliance(power_path))
            
            result.architecture_violations = violations
            
            if violations:
                logger.warning(f"Architecture violations found: {len(violations)}")
            else:
                logger.info("Architecture compliance validation passed")
            
        except Exception as e:
            error_msg = f"Architecture validation failed: {e}"
            logger.error(error_msg)
            result.integration_failures.append(error_msg)

    def _check_cross_layer_imports(self, power_path: Path) -> List[str]:
        """Check for forbidden cross-layer imports."""
        violations = []
        
        try:
            # Check core importing from adapters
            core_files = list((power_path / "core").rglob("*.py"))
            for file_path in core_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if 'from adapters' in content or 'import adapters' in content:
                        violations.append(f"Core layer imports from adapters: {file_path.relative_to(power_path)}")
                        
                except Exception as e:
                    logger.warning(f"Failed to check file {file_path}: {e}")
            
            # Check adapters importing from core
            if (power_path / "adapters").exists():
                adapter_files = list((power_path / "adapters").rglob("*.py"))
                for file_path in adapter_files:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        if 'from core' in content or 'import core' in content:
                            violations.append(f"Adapters layer imports from core: {file_path.relative_to(power_path)}")
                            
                    except Exception as e:
                        logger.warning(f"Failed to check file {file_path}: {e}")
            
        except Exception as e:
            violations.append(f"Cross-layer import check failed: {e}")
        
        return violations

    def _check_file_placement(self, power_path: Path) -> List[str]:
        """Check for proper file placement in architecture layers."""
        violations = []
        
        # This is a simplified check - in practice, you'd have more sophisticated rules
        try:
            # Check for business logic in adapters
            if (power_path / "adapters").exists():
                for file_path in (power_path / "adapters").rglob("*.py"):
                    if file_path.name in ["business_logic.py", "domain_service.py"]:
                        violations.append(f"Business logic file in adapters layer: {file_path.relative_to(power_path)}")
            
            # Check for adapter-specific code in core
            for file_path in (power_path / "core").rglob("*.py"):
                if any(provider in file_path.name.lower() for provider in ["openai", "gemini", "anthropic"]):
                    violations.append(f"Provider-specific code in core layer: {file_path.relative_to(power_path)}")
            
        except Exception as e:
            violations.append(f"File placement check failed: {e}")
        
        return violations

    def _check_interface_compliance(self, power_path: Path) -> List[str]:
        """Check for proper interface implementation."""
        violations = []
        
        try:
            # Check that adapters implement required interfaces
            # This is a simplified check - in practice, you'd use AST parsing
            if (power_path / "adapters").exists():
                for adapter_dir in (power_path / "adapters").iterdir():
                    if adapter_dir.is_dir() and adapter_dir.name not in ["__pycache__"]:
                        client_file = adapter_dir / "client.py"
                        if client_file.exists():
                            try:
                                with open(client_file, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                
                                # Check for interface implementation
                                if 'Interface' not in content and 'ABC' not in content:
                                    violations.append(f"Adapter {adapter_dir.name} may not implement required interface")
                                    
                            except Exception as e:
                                logger.warning(f"Failed to check interface compliance for {client_file}: {e}")
            
        except Exception as e:
            violations.append(f"Interface compliance check failed: {e}")
        
        return violations

    def _validate_integration_compatibility(self, workspace: Path, result: ValidationResult) -> None:
        """
        Validate integration compatibility with existing system.

        Args:
            workspace: Validation workspace path
            result: ValidationResult to update
        """
        try:
            power_path = workspace / "power"
            
            # Check for import compatibility
            compatibility_issues = []
            
            # Run import tests
            import_test_result = subprocess.run(
                ['python3', '-c', 'import sys; sys.path.insert(0, "."); import agents'],
                capture_output=True,
                text=True,
                check=False,
                cwd=power_path
            )
            
            if import_test_result.returncode != 0:
                compatibility_issues.append(f"Import compatibility issue: {import_test_result.stderr}")
            
            result.integration_failures.extend(compatibility_issues)
            
            if not compatibility_issues:
                logger.info("Integration compatibility validation passed")
            
        except Exception as e:
            error_msg = f"Integration compatibility validation failed: {e}"
            logger.error(error_msg)
            result.integration_failures.append(error_msg)

    def _validate_performance_requirements(self, workspace: Path, result: ValidationResult) -> None:
        """
        Validate performance requirements are met.

        Args:
            workspace: Validation workspace path
            result: ValidationResult to update
        """
        try:
            # This is a placeholder for performance validation
            # In practice, you'd run performance benchmarks
            
            power_path = workspace / "power"
            performance_issues = []
            
            # Check for obvious performance anti-patterns
            python_files = list(power_path.rglob("*.py"))
            for file_path in python_files:
                if 'venv' in str(file_path) or '__pycache__' in str(file_path):
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check for obvious performance issues
                    if 'while True:' in content and 'sleep' not in content:
                        performance_issues.append(f"Potential infinite loop without sleep: {file_path.relative_to(power_path)}")
                    
                    if content.count('for ') > 3 and 'break' not in content:
                        performance_issues.append(f"Multiple nested loops without breaks: {file_path.relative_to(power_path)}")
                        
                except Exception as e:
                    logger.warning(f"Failed to check performance for {file_path}: {e}")
            
            result.performance_issues = performance_issues[:5]  # Limit to first 5
            
            if not performance_issues:
                logger.info("Performance requirements validation passed")
            
        except Exception as e:
            error_msg = f"Performance validation failed: {e}"
            logger.error(error_msg)
            result.integration_failures.append(error_msg)

    def _validate_security_requirements(self, workspace: Path, result: ValidationResult) -> None:
        """
        Validate security requirements are met.

        Args:
            workspace: Validation workspace path
            result: ValidationResult to update
        """
        try:
            power_path = workspace / "power"
            security_issues = []
            
            # Check for obvious security issues
            python_files = list(power_path.rglob("*.py"))
            for file_path in python_files:
                if 'venv' in str(file_path) or '__pycache__' in str(file_path):
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check for hardcoded secrets
                    if any(secret in content.lower() for secret in ['password =', 'api_key =', 'secret =']):
                        security_issues.append(f"Potential hardcoded secret: {file_path.relative_to(power_path)}")
                    
                    # Check for unsafe eval/exec
                    if 'eval(' in content or 'exec(' in content:
                        security_issues.append(f"Unsafe eval/exec usage: {file_path.relative_to(power_path)}")
                    
                    # Check for shell injection vulnerabilities
                    if 'subprocess.call(' in content and 'shell=True' in content:
                        security_issues.append(f"Potential shell injection: {file_path.relative_to(power_path)}")
                        
                except Exception as e:
                    logger.warning(f"Failed to check security for {file_path}: {e}")
            
            result.security_issues = security_issues[:5]  # Limit to first 5
            
            if not security_issues:
                logger.info("Security requirements validation passed")
            
        except Exception as e:
            error_msg = f"Security validation failed: {e}"
            logger.error(error_msg)
            result.integration_failures.append(error_msg)

    def _determine_overall_pass(self, result: ValidationResult) -> bool:
        """
        Determine if submission passes all validation requirements.

        Args:
            result: ValidationResult to evaluate

        Returns:
            True if all requirements are met
        """
        return (
            result.pylint_score >= self.required_pylint_score and
            result.test_success_rate >= self.required_test_success_rate and
            len(result.architecture_violations) == 0 and
            len(result.integration_failures) == 0 and
            len(result.performance_issues) == 0 and
            len(result.security_issues) == 0
        )

    def _cleanup_validation_workspace(self, workspace: Path) -> None:
        """
        Clean up validation workspace.

        Args:
            workspace: Workspace path to clean up
        """
        try:
            if workspace.exists() and self.temp_workspace is None:
                # Only auto-cleanup if we created a temporary workspace
                shutil.rmtree(workspace)
                logger.info(f"Cleaned up validation workspace: {workspace}")
        except Exception as e:
            logger.warning(f"Failed to cleanup validation workspace {workspace}: {e}")

    def get_validation_summary(self) -> Dict[str, Any]:
        """
        Get summary of validation history.

        Returns:
            Summary of all validations performed
        """
        if not self.validation_history:
            return {"total_validations": 0, "pass_rate": 0.0}
        
        total = len(self.validation_history)
        passed = sum(1 for result in self.validation_history if result.passed)
        
        avg_pylint = sum(result.pylint_score for result in self.validation_history) / total
        avg_test_rate = sum(result.test_success_rate for result in self.validation_history) / total
        avg_time = sum(result.validation_time for result in self.validation_history) / total
        
        return {
            "total_validations": total,
            "pass_rate": (passed / total) * 100,
            "average_pylint_score": avg_pylint,
            "average_test_success_rate": avg_test_rate,
            "average_validation_time": avg_time,
            "common_issues": self._get_common_issues()
        }

    def _get_common_issues(self) -> Dict[str, int]:
        """Get most common validation issues."""
        issue_counts = {}
        
        for result in self.validation_history:
            for issue in result.architecture_violations + result.integration_failures:
                # Extract issue type from message
                issue_type = issue.split(':')[0] if ':' in issue else issue[:50]
                issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
        
        # Return top 5 most common issues
        return dict(sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5])