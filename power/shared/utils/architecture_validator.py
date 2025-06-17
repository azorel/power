"""
Architecture validation utilities to enforce three-layer architecture compliance.
"""

import os
import ast
import re
from typing import List, Dict, Set, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from shared.exceptions import ArchitectureViolationError, LayerViolationError, CrossLayerImportError


@dataclass
class ValidationResult:
    """Result of architecture validation."""

    is_valid: bool
    errors: List[str]
    warnings: List[str]
    file_path: str
    layer: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert result to dictionary format."""
        return {
            'is_valid': self.is_valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'file_path': self.file_path,
            'layer': self.layer
        }


class ArchitectureValidator:
    """Validates three-layer architecture compliance."""

    # Layer definitions
    LAYERS = {
        'core': {
            'path_patterns': [r'^core/.*'],
            'allowed_imports': [
                r'^shared\..*',
                r'^core\..*',
                # Standard library imports
                r'^(os|sys|json|datetime|typing|dataclasses|pathlib|re|collections|itertools|functools|asyncio|logging|unittest|pytest).*',
                # Common business logic libraries
                r'^(sqlalchemy|jinja2|pandas|numpy|scipy|matplotlib|sqlite3|psycopg2|mysql).*'
            ],
            'forbidden_imports': [
                r'^adapters\..*',
                # External API libraries
                r'^(requests|httpx|aiohttp|openai|google|anthropic).*'
            ],
            'description': 'Business logic, database operations, HTML generation'
        },
        'adapters': {
            'path_patterns': [r'^adapters/.*'],
            'allowed_imports': [
                r'^shared\..*',
                r'^adapters\..*',
                # Standard library imports
                r'^(os|sys|json|datetime|typing|dataclasses|pathlib|re|collections|itertools|functools|asyncio|logging|unittest|pytest|threading|time|hashlib|ast|base64).*',
                # External API libraries
                r'^(requests|httpx|aiohttp|openai|google|anthropic|tweepy|youtube_data_api|slack_sdk).*'
            ],
            'forbidden_imports': [
                r'^core\..*'
            ],
            'description': 'External API integrations, MCP connections'
        },
        'shared': {
            'path_patterns': [r'^shared/.*'],
            'allowed_imports': [
                r'^shared\..*',
                # Standard library imports only
                r'^(os|sys|json|datetime|typing|dataclasses|pathlib|re|collections|itertools|functools|asyncio|logging|enum|abc|unittest|pytest|threading|time|hashlib|ast).*',
                # Common utility libraries
                r'^(pydantic|validators).*'
            ],
            'forbidden_imports': [
                r'^core\..*',
                r'^adapters\..*',
                # No external API libraries in shared
                r'^(requests|httpx|aiohttp|openai|google|anthropic).*'
            ],
            'description': 'Common interfaces, models, utilities'
        }
    }

    def __init__(self, project_root: str = None):
        """Initialize validator with project root directory."""
        self.project_root = Path(project_root) if project_root else Path.cwd()

    def validate_file(self, file_path: str) -> ValidationResult:
        """Validate a single Python file for architecture compliance."""
        file_path = Path(file_path)

        # Convert to relative path from project root
        try:
            relative_path = file_path.relative_to(self.project_root)
        except ValueError:
            return ValidationResult(
                is_valid=False,
                errors=[f"File {file_path} is outside project root"],
                warnings=[],
                file_path=str(file_path)
            )

        # Determine layer
        layer = self._determine_layer(str(relative_path))
        if not layer:
            return ValidationResult(
                is_valid=True,
                errors=[],
                warnings=[f"File {relative_path} is not in any defined layer"],
                file_path=str(file_path),
                layer=None
            )

        # Read and parse file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Could not read file: {e}"],
                warnings=[],
                file_path=str(file_path),
                layer=layer
            )

        # Parse imports
        try:
            imports = self._extract_imports(content)
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Could not parse file: {e}"],
                warnings=[],
                file_path=str(file_path),
                layer=layer
            )

        # Validate imports
        errors = []
        warnings = []

        for import_name in imports:
            result = self._validate_import(import_name, layer)
            if result['is_forbidden']:
                errors.append(f"Forbidden import '{import_name}' in {layer} layer: {result['reason']}")
            elif result['is_warning']:
                warnings.append(f"Suspicious import '{import_name}' in {layer} layer: {result['reason']}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            file_path=str(file_path),
            layer=layer
        )

    def validate_directory(self, directory: str = None) -> List[ValidationResult]:
        """Validate all Python files in a directory tree."""
        directory = Path(directory) if directory else self.project_root
        results = []

        for py_file in directory.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue

            result = self.validate_file(py_file)
            results.append(result)

        return results

    def validate_project(self) -> Dict[str, List[ValidationResult]]:
        """Validate the entire project, grouped by layer."""
        all_results = self.validate_directory()

        grouped_results = {
            'core': [],
            'adapters': [],
            'shared': [],
            'other': []
        }

        for result in all_results:
            layer = result.layer or 'other'
            grouped_results[layer].append(result)

        return grouped_results

    def generate_report(self, results: List[ValidationResult]) -> Dict:
        """Generate a comprehensive validation report."""
        total_files = len(results)
        valid_files = sum(1 for r in results if r.is_valid)
        invalid_files = total_files - valid_files

        total_errors = sum(len(r.errors) for r in results)
        total_warnings = sum(len(r.warnings) for r in results)

        layer_stats = {}
        for layer in self.LAYERS.keys():
            layer_results = [r for r in results if r.layer == layer]
            layer_stats[layer] = {
                'total_files': len(layer_results),
                'valid_files': sum(1 for r in layer_results if r.is_valid),
                'errors': sum(len(r.errors) for r in layer_results),
                'warnings': sum(len(r.warnings) for r in layer_results)
            }

        return {
            'summary': {
                'total_files': total_files,
                'valid_files': valid_files,
                'invalid_files': invalid_files,
                'total_errors': total_errors,
                'total_warnings': total_warnings,
                'compliance_rate': valid_files / total_files if total_files > 0 else 0.0
            },
            'layer_stats': layer_stats,
            'results': [r.to_dict() for r in results]
        }

    def _determine_layer(self, file_path: str) -> Optional[str]:
        """Determine which layer a file belongs to based on its path."""
        for layer_name, layer_config in self.LAYERS.items():
            for pattern in layer_config['path_patterns']:
                if re.match(pattern, file_path):
                    return layer_name
        return None

    def _extract_imports(self, content: str) -> Set[str]:
        """Extract all import statements from Python code."""
        imports = set()

        try:
            tree = ast.parse(content)
        except SyntaxError:
            # Fallback to regex parsing for syntax errors
            return self._extract_imports_regex(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
                    # Also add specific imports for more granular checking
                    for alias in node.names:
                        imports.add(f"{node.module}.{alias.name}")

        return imports

    def _extract_imports_regex(self, content: str) -> Set[str]:
        """Fallback import extraction using regex."""
        imports = set()

        # Match 'import module' statements
        import_pattern = r'^import\s+([\w\.]+)'
        for match in re.finditer(import_pattern, content, re.MULTILINE):
            imports.add(match.group(1))

        # Match 'from module import ...' statements
        from_pattern = r'^from\s+([\w\.]+)\s+import'
        for match in re.finditer(from_pattern, content, re.MULTILINE):
            imports.add(match.group(1))

        return imports

    def _validate_import(self, import_name: str, layer: str) -> Dict:
        """Validate a single import against layer rules."""
        layer_config = self.LAYERS.get(layer)
        if not layer_config:
            return {'is_forbidden': False, 'is_warning': False, 'reason': ''}

        # Check if import is explicitly forbidden
        for forbidden_pattern in layer_config['forbidden_imports']:
            if re.match(forbidden_pattern, import_name):
                return {
                    'is_forbidden': True,
                    'is_warning': False,
                    'reason': f"Import matches forbidden pattern: {forbidden_pattern}"
                }

        # Check if import is allowed
        for allowed_pattern in layer_config['allowed_imports']:
            if re.match(allowed_pattern, import_name):
                return {'is_forbidden': False, 'is_warning': False, 'reason': ''}

        # Special handling for relative imports within the same layer
        if layer == 'adapters' and self._is_relative_adapter_import(import_name):
            return {'is_forbidden': False, 'is_warning': False, 'reason': ''}
            
        if layer == 'shared' and self._is_relative_shared_import(import_name):
            return {'is_forbidden': False, 'is_warning': False, 'reason': ''}

        # Import is not explicitly allowed or forbidden - warn
        return {
            'is_forbidden': False,
            'is_warning': True,
            'reason': f"Import not in allowed patterns for {layer} layer"
        }

    def _is_relative_adapter_import(self, import_name: str) -> bool:
        """Check if import is a relative import within the same adapter."""
        # Relative imports (starting with .) or simple module names without dots
        return (import_name.startswith('.') or 
                ('.' not in import_name and not import_name.startswith(('shared', 'core', 'adapters'))))

    def _is_relative_shared_import(self, import_name: str) -> bool:
        """Check if import is a relative import within shared utilities."""
        # Relative imports or simple module names like 'cache', 'rate_limiter'
        return (import_name.startswith('.') or 
                import_name in ['cache', 'rate_limiter', 'threading', 'time', 'hashlib', 'ast'])

    def _should_skip_file(self, file_path: Path) -> bool:
        """Determine if a file should be skipped during validation."""
        skip_patterns = [
            r'.*/__pycache__/.*',
            r'.*/\..*',  # Hidden files
            r'.*/tests?/.*',  # Test files (separate validation)
            r'.*/venv/.*',  # Virtual environment
            r'.*/\.venv/.*',  # Virtual environment
            r'.*/node_modules/.*',  # Node modules
            r'.*\.pyc$',  # Compiled Python files
            r'.*\.pyo$',  # Compiled Python files
            r'.*test.*\.py$',  # Test files at root level
        ]

        file_str = str(file_path)
        for pattern in skip_patterns:
            if re.match(pattern, file_str):
                return True

        return False


def validate_architecture(project_root: str = None,
                         file_path: str = None) -> Dict:
    """
    Convenience function to validate architecture compliance.

    Args:
        project_root: Root directory of the project
        file_path: Specific file to validate (validates entire project if None)

    Returns:
        Validation report dictionary
    """
    validator = ArchitectureValidator(project_root)

    if file_path:
        result = validator.validate_file(file_path)
        return validator.generate_report([result])
    else:
        results = validator.validate_directory()
        return validator.generate_report(results)


def check_layer_compliance(file_path: str, project_root: str = None) -> bool:
    """
    Quick check if a file complies with architecture rules.

    Args:
        file_path: Path to the file to check
        project_root: Root directory of the project

    Returns:
        True if compliant, False otherwise

    Raises:
        ArchitectureViolationError: If file violates architecture rules
    """
    validator = ArchitectureValidator(project_root)
    result = validator.validate_file(file_path)

    if not result.is_valid:
        error_details = '; '.join(result.errors)
        raise ArchitectureViolationError(
            f"Architecture violation in {file_path}: {error_details}",
            file_path=file_path,
            violation_type='layer_compliance'
        )

    return True


if __name__ == "__main__":
    # Command-line interface for validation
    import sys
    import json

    if len(sys.argv) > 1:
        target = sys.argv[1]
        if os.path.isfile(target):
            report = validate_architecture(file_path=target)
        else:
            report = validate_architecture(project_root=target)
    else:
        report = validate_architecture()

    print(json.dumps(report, indent=2))
