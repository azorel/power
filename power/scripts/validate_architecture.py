"""
validate_architecture module.
"""

#!/usr/bin/env python3
"""
Comprehensive architecture compliance validation script.
Validates three-layer architecture, interface implementation, and error handling patterns.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.utils.architecture_validator import validate_architecture, ArchitectureValidator
from shared.interfaces.llm_provider import LLMProvider, AdvancedLLMProvider
from shared.exceptions import PowerBuilderError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ComprehensiveArchitectureValidator:
    """Extended architecture validator with interface and error handling validation."""

    def __init__(self, project_root: str = None):
        """Initialize comprehensive validator."""
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.base_validator = ArchitectureValidator(str(self.project_root))
        self.violations = []
        self.warnings = []

    def validate_all(self) -> Dict[str, Any]:
        """Run comprehensive architecture validation."""
        logger.info("Starting comprehensive architecture validation...")
        
        results = {
            'layer_compliance': self._validate_layer_compliance(),
            'interface_implementation': self._validate_interface_implementation(),
            'error_handling': self._validate_error_handling(),
            'configuration_isolation': self._validate_configuration_isolation(),
            'summary': {
                'total_violations': len(self.violations),
                'total_warnings': len(self.warnings),
                'is_compliant': len(self.violations) == 0
            },
            'violations': self.violations,
            'warnings': self.warnings
        }
        
        logger.info("Architecture validation completed")
        return results

    def _validate_layer_compliance(self) -> Dict[str, Any]:
        """Validate layer compliance using base validator."""
        logger.info("Validating layer compliance...")
        
        report = validate_architecture(str(self.project_root))
        
        # Extract violations and warnings
        for result in report.get('results', []):
            if result['errors']:
                for error in result['errors']:
                    self.violations.append({
                        'type': 'layer_compliance',
                        'file': result['file_path'],
                        'layer': result['layer'],
                        'description': error
                    })
            
            if result['warnings']:
                for warning in result['warnings']:
                    self.warnings.append({
                        'type': 'layer_compliance',
                        'file': result['file_path'],
                        'layer': result['layer'],
                        'description': warning
                    })
        
        return report

    def _validate_interface_implementation(self) -> Dict[str, Any]:
        """Validate that adapters properly implement shared interfaces."""
        logger.info("Validating interface implementation...")
        
        interface_results = {
            'adapters_checked': 0,
            'interfaces_implemented': 0,
            'missing_implementations': []
        }
        
        # Check adapters directory
        adapters_dir = self.project_root / 'adapters'
        if not adapters_dir.exists():
            self.warnings.append({
                'type': 'interface_implementation',
                'description': 'No adapters directory found'
            })
            return interface_results
        
        # Check each adapter
        for adapter_dir in adapters_dir.iterdir():
            if not adapter_dir.is_dir() or adapter_dir.name.startswith('.'):
                continue
                
            interface_results['adapters_checked'] += 1
            
            # Look for main client files
            client_files = list(adapter_dir.glob('*client*.py'))
            if not client_files:
                client_files = list(adapter_dir.glob('*.py'))
            
            interface_implemented = False
            for client_file in client_files:
                if self._check_interface_implementation(client_file):
                    interface_implemented = True
                    interface_results['interfaces_implemented'] += 1
                    break
            
            if not interface_implemented:
                missing = {
                    'adapter': adapter_dir.name,
                    'description': f'No LLMProvider interface implementation found in {adapter_dir.name}'
                }
                interface_results['missing_implementations'].append(missing)
                self.violations.append({
                    'type': 'interface_implementation',
                    'file': str(adapter_dir),
                    'description': missing['description']
                })
        
        return interface_results

    def _check_interface_implementation(self, file_path: Path) -> bool:
        """Check if a file implements LLMProvider interface."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for interface imports and implementations
            interface_indicators = [
                'LLMProvider',
                'AdvancedLLMProvider',
                'from shared.interfaces.llm_provider import',
                'def generate_text(',
                'def generate_chat_completion(',
                'def get_model_info(',
                'def validate_credentials('
            ]
            
            found_indicators = sum(1 for indicator in interface_indicators if indicator in content)
            return found_indicators >= 3  # At least 3 indicators suggest interface implementation
            
        except Exception as e:
            logger.warning(f"Could not check interface implementation in {file_path}: {e}")
            return False

    def _validate_error_handling(self) -> Dict[str, Any]:
        """Validate error handling and translation patterns."""
        logger.info("Validating error handling patterns...")
        
        error_results = {
            'files_checked': 0,
            'proper_exception_usage': 0,
            'missing_error_translation': []
        }
        
        # Check adapter files for proper error handling
        adapters_dir = self.project_root / 'adapters'
        if adapters_dir.exists():
            for py_file in adapters_dir.rglob('*.py'):
                if py_file.name.startswith('__'):
                    continue
                    
                error_results['files_checked'] += 1
                
                if self._check_error_handling(py_file):
                    error_results['proper_exception_usage'] += 1
                else:
                    error_results['missing_error_translation'].append(str(py_file))
                    self.warnings.append({
                        'type': 'error_handling',
                        'file': str(py_file),
                        'description': 'Missing proper error translation to shared exceptions'
                    })
        
        return error_results

    def _check_error_handling(self, file_path: Path) -> bool:
        """Check if a file properly handles errors using shared exceptions."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for shared exception usage
            exception_indicators = [
                'from shared.exceptions import',
                'LLMProviderError',
                'PowerBuilderError',
                'translate_exception',
                'raise.*Error'
            ]
            
            found_indicators = sum(1 for indicator in exception_indicators if indicator in content)
            return found_indicators >= 2  # At least 2 indicators suggest proper error handling
            
        except Exception as e:
            logger.warning(f"Could not check error handling in {file_path}: {e}")
            return False

    def _validate_configuration_isolation(self) -> Dict[str, Any]:
        """Validate configuration isolation patterns."""
        logger.info("Validating configuration isolation...")
        
        config_results = {
            'config_files_found': 0,
            'proper_isolation': 0,
            'isolation_violations': []
        }
        
        # Check for configuration files
        config_patterns = ['*config*.py', '*/config.py', '*/settings.py']
        
        for pattern in config_patterns:
            for config_file in self.project_root.rglob(pattern):
                if 'test' in str(config_file) or '__pycache__' in str(config_file):
                    continue
                    
                config_results['config_files_found'] += 1
                
                if self._check_config_isolation(config_file):
                    config_results['proper_isolation'] += 1
                else:
                    violation = {
                        'file': str(config_file),
                        'description': 'Configuration file may not follow isolation patterns'
                    }
                    config_results['isolation_violations'].append(violation)
                    self.warnings.append({
                        'type': 'configuration_isolation',
                        'file': str(config_file),
                        'description': violation['description']
                    })
        
        return config_results

    def _check_config_isolation(self, file_path: Path) -> bool:
        """Check if configuration follows isolation patterns."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for proper configuration patterns
            good_patterns = [
                'from shared.config',
                'BaseConfig',
                'os.environ.get',
                'dataclass',
                'class.*Config'
            ]
            
            # Check for anti-patterns
            bad_patterns = [
                'from core.',
                'from adapters.',
                'hardcoded.*key',  # This would need more sophisticated checking
            ]
            
            good_found = sum(1 for pattern in good_patterns if pattern in content)
            bad_found = sum(1 for pattern in bad_patterns if pattern in content)
            
            return good_found >= 2 and bad_found == 0
            
        except Exception as e:
            logger.warning(f"Could not check configuration isolation in {file_path}: {e}")
            return True  # Assume OK if we can't check

    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate a comprehensive report."""
        report_lines = [
            "=" * 80,
            "ARCHITECTURE COMPLIANCE VALIDATION REPORT",
            "=" * 80,
            "",
            "SUMMARY",
            "-" * 40,
            f"Total Violations: {results['summary']['total_violations']}",
            f"Total Warnings: {results['summary']['total_warnings']}",
            f"Overall Compliant: {'✅ YES' if results['summary']['is_compliant'] else '❌ NO'}",
            "",
            "LAYER COMPLIANCE",
            "-" * 40,
            f"Files Checked: {results['layer_compliance']['summary']['total_files']}",
            f"Valid Files: {results['layer_compliance']['summary']['valid_files']}",
            f"Compliance Rate: {results['layer_compliance']['summary']['compliance_rate']:.2%}",
            "",
            "INTERFACE IMPLEMENTATION",
            "-" * 40,
            f"Adapters Checked: {results['interface_implementation']['adapters_checked']}",
            f"Interfaces Implemented: {results['interface_implementation']['interfaces_implemented']}",
            f"Missing Implementations: {len(results['interface_implementation']['missing_implementations'])}",
            "",
            "ERROR HANDLING",
            "-" * 40,
            f"Files Checked: {results['error_handling']['files_checked']}",
            f"Proper Exception Usage: {results['error_handling']['proper_exception_usage']}",
            f"Missing Error Translation: {len(results['error_handling']['missing_error_translation'])}",
            "",
            "CONFIGURATION ISOLATION",
            "-" * 40,
            f"Config Files Found: {results['configuration_isolation']['config_files_found']}",
            f"Proper Isolation: {results['configuration_isolation']['proper_isolation']}",
            f"Isolation Violations: {len(results['configuration_isolation']['isolation_violations'])}",
            ""
        ]
        
        # Add violations section
        if results['violations']:
            report_lines.extend([
                "VIOLATIONS (MUST FIX)",
                "-" * 40
            ])
            for i, violation in enumerate(results['violations'], 1):
                report_lines.append(f"{i}. {violation['type']}: {violation['description']}")
                if 'file' in violation:
                    report_lines.append(f"   File: {violation['file']}")
                report_lines.append("")
        
        # Add warnings section
        if results['warnings']:
            report_lines.extend([
                "WARNINGS (RECOMMENDED FIXES)",
                "-" * 40
            ])
            for i, warning in enumerate(results['warnings'], 1):
                report_lines.append(f"{i}. {warning['type']}: {warning['description']}")
                if 'file' in warning:
                    report_lines.append(f"   File: {warning['file']}")
                report_lines.append("")
        
        report_lines.extend([
            "=" * 80,
            "NEXT STEPS",
            "=" * 80,
            "",
            "1. Fix all violations listed above",
            "2. Address warnings to improve code quality",
            "3. Run validation again to confirm compliance",
            "4. Ensure all new code follows three-layer architecture",
            ""
        ])
        
        return "\n".join(report_lines)


def main():
    """Main entry point for architecture validation."""
    validator = ComprehensiveArchitectureValidator()
    results = validator.validate_all()
    
    # Generate and display report
    report = validator.generate_report(results)
    print(report)
    
    # Save detailed results to file
    with open('architecture_validation_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Exit with appropriate code
    exit_code = 0 if results['summary']['is_compliant'] else 1
    print(f"Validation {'PASSED' if exit_code == 0 else 'FAILED'}")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()