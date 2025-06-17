#!/usr/bin/env python3
"""
Interface implementation validation script.
Validates that all adapters properly implement shared interfaces.
"""

import os
import sys
import ast
import inspect
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.interfaces.llm_provider import (
    LLMProvider, 
    AdvancedLLMProvider,
    MultiModalLLMProvider,
    StreamingLLMProvider,
    FunctionCallingLLMProvider
)


class InterfaceValidator:
    """Validates adapter implementations against shared interfaces."""

    def __init__(self, project_root: str = None):
        """Initialize interface validator."""
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.results = []

    def validate_all_adapters(self) -> Dict[str, Any]:
        """Validate all adapters in the adapters directory."""
        adapters_dir = self.project_root / 'adapters'
        
        if not adapters_dir.exists():
            return {
                'status': 'error',
                'message': 'No adapters directory found',
                'results': []
            }
        
        results = []
        total_adapters = 0
        compliant_adapters = 0
        
        for adapter_dir in adapters_dir.iterdir():
            if not adapter_dir.is_dir() or adapter_dir.name.startswith('.'):
                continue
                
            total_adapters += 1
            adapter_result = self.validate_adapter(adapter_dir)
            results.append(adapter_result)
            
            if adapter_result['is_compliant']:
                compliant_adapters += 1
        
        return {
            'status': 'success',
            'summary': {
                'total_adapters': total_adapters,
                'compliant_adapters': compliant_adapters,
                'compliance_rate': compliant_adapters / max(1, total_adapters),
                'all_compliant': compliant_adapters == total_adapters
            },
            'results': results
        }

    def validate_adapter(self, adapter_dir: Path) -> Dict[str, Any]:
        """Validate a single adapter directory."""
        adapter_name = adapter_dir.name
        
        # Find the main client file
        client_files = self._find_client_files(adapter_dir)
        
        if not client_files:
            return {
                'adapter_name': adapter_name,
                'is_compliant': False,
                'error': 'No client files found',
                'methods': {},
                'interfaces': []
            }
        
        # Try to import and inspect the main client
        try:
            main_client = self._get_main_client(adapter_dir, client_files)
            if not main_client:
                return {
                    'adapter_name': adapter_name,
                    'is_compliant': False,
                    'error': 'Could not import main client class',
                    'methods': {},
                    'interfaces': []
                }
            
            return self._validate_client_class(adapter_name, main_client)
            
        except Exception as e:
            return {
                'adapter_name': adapter_name,
                'is_compliant': False,
                'error': f'Validation failed: {str(e)}',
                'methods': {},
                'interfaces': []
            }

    def _find_client_files(self, adapter_dir: Path) -> List[Path]:
        """Find client files in adapter directory."""
        client_files = []
        
        # Look for specific patterns
        patterns = ['*client*.py', 'client.py', '__init__.py']
        
        for pattern in patterns:
            client_files.extend(adapter_dir.glob(pattern))
        
        # Filter out test files
        client_files = [f for f in client_files if 'test' not in f.name.lower()]
        
        return sorted(client_files)

    def _get_main_client(self, adapter_dir: Path, client_files: List[Path]) -> Any:
        """Get the main client class from the adapter."""
        adapter_name = adapter_dir.name
        
        # Try to import from the main module
        try:
            module_path = f'adapters.{adapter_name}'
            module = __import__(module_path, fromlist=[''])
            
            # Look for classes that implement LLMProvider
            for name in dir(module):
                obj = getattr(module, name)
                if (inspect.isclass(obj) and 
                    issubclass(obj, LLMProvider) and 
                    obj != LLMProvider):
                    return obj
                    
        except ImportError:
            pass
        
        # Try individual client files
        for client_file in client_files:
            try:
                client_class = self._extract_client_from_file(client_file)
                if client_class:
                    return client_class
            except Exception:
                continue
        
        return None

    def _extract_client_from_file(self, file_path: Path) -> Any:
        """Extract client class from a Python file."""
        try:
            # Read and parse the file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Look for class definitions that might be LLM providers
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check if class extends LLMProvider
                    for base in node.bases:
                        if (isinstance(base, ast.Name) and 
                            'LLM' in base.id and 'Provider' in base.id):
                            # Try to import this class
                            return self._import_class_from_file(file_path, node.name)
                            
        except Exception:
            pass
        
        return None

    def _import_class_from_file(self, file_path: Path, class_name: str) -> Any:
        """Import a specific class from a file."""
        try:
            # Get relative module path
            rel_path = file_path.relative_to(self.project_root)
            module_path = str(rel_path).replace('/', '.').replace('\\', '.').replace('.py', '')
            
            module = __import__(module_path, fromlist=[class_name])
            return getattr(module, class_name)
            
        except Exception:
            return None

    def _validate_client_class(self, adapter_name: str, client_class: Any) -> Dict[str, Any]:
        """Validate a client class against interface requirements."""
        
        # Check interface implementation
        interfaces_implemented = []
        if issubclass(client_class, LLMProvider):
            interfaces_implemented.append('LLMProvider')
        if issubclass(client_class, MultiModalLLMProvider):
            interfaces_implemented.append('MultiModalLLMProvider')
        if issubclass(client_class, StreamingLLMProvider):
            interfaces_implemented.append('StreamingLLMProvider')
        if issubclass(client_class, FunctionCallingLLMProvider):
            interfaces_implemented.append('FunctionCallingLLMProvider')
        if issubclass(client_class, AdvancedLLMProvider):
            interfaces_implemented.append('AdvancedLLMProvider')
        
        # Check required methods
        required_methods = {
            'generate_text': 'Generate text from prompt',
            'generate_chat_completion': 'Generate chat completion',
            'get_model_info': 'Get model information',
            'validate_credentials': 'Validate API credentials',
            'get_usage_stats': 'Get usage statistics',
            'provider_name': 'Provider name property',
            'supported_features': 'Supported features property'
        }
        
        method_results = {}
        missing_methods = []
        
        for method_name, description in required_methods.items():
            if hasattr(client_class, method_name):
                method_results[method_name] = {
                    'implemented': True,
                    'description': description,
                    'is_property': isinstance(getattr(client_class, method_name, None), property)
                }
            else:
                method_results[method_name] = {
                    'implemented': False,
                    'description': description,
                    'is_property': False
                }
                missing_methods.append(method_name)
        
        # Check error handling
        error_handling_ok = self._check_error_handling(client_class)
        
        # Determine compliance
        is_compliant = (
            len(interfaces_implemented) > 0 and
            len(missing_methods) == 0 and
            error_handling_ok
        )
        
        return {
            'adapter_name': adapter_name,
            'client_class': client_class.__name__,
            'is_compliant': is_compliant,
            'interfaces': interfaces_implemented,
            'methods': method_results,
            'missing_methods': missing_methods,
            'error_handling': error_handling_ok,
            'details': {
                'module': client_class.__module__,
                'file': inspect.getfile(client_class) if hasattr(client_class, '__file__') else 'unknown'
            }
        }

    def _check_error_handling(self, client_class: Any) -> bool:
        """Check if class properly handles errors using shared exceptions."""
        try:
            # Get the source file and check module directory
            source_file = Path(inspect.getfile(client_class))
            module_dir = source_file.parent
            
            # Check the main client file
            with open(source_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for shared exception imports and usage
            error_indicators = [
                'from shared.exceptions import',
                'LLMProviderError',
                'PowerBuilderError',
                'translate_exception',
                'handle.*exception'
            ]
            
            found_indicators = sum(1 for indicator in error_indicators if indicator in content)
            
            # If not found in main file, check for dedicated exceptions module
            if found_indicators < 2:
                exceptions_file = module_dir / 'exceptions.py'
                if exceptions_file.exists():
                    with open(exceptions_file, 'r', encoding='utf-8') as f:
                        exceptions_content = f.read()
                    
                    exceptions_indicators = sum(1 for indicator in error_indicators 
                                              if indicator in exceptions_content)
                    found_indicators += exceptions_indicators
            
            return found_indicators >= 2
            
        except Exception:
            return False

    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate a detailed interface compliance report."""
        lines = [
            "=" * 80,
            "INTERFACE IMPLEMENTATION VALIDATION REPORT",
            "=" * 80,
            "",
            "SUMMARY",
            "-" * 40
        ]
        
        if results['status'] == 'error':
            lines.extend([
                f"❌ ERROR: {results['message']}",
                ""
            ])
            return "\n".join(lines)
        
        summary = results['summary']
        lines.extend([
            f"Total Adapters: {summary['total_adapters']}",
            f"Compliant Adapters: {summary['compliant_adapters']}",
            f"Compliance Rate: {summary['compliance_rate']:.1%}",
            f"All Compliant: {'✅ YES' if summary['all_compliant'] else '❌ NO'}",
            ""
        ])
        
        # Detailed results for each adapter
        for result in results['results']:
            lines.extend([
                f"ADAPTER: {result['adapter_name'].upper()}",
                "-" * 40,
                f"Status: {'✅ COMPLIANT' if result['is_compliant'] else '❌ NON-COMPLIANT'}",
            ])
            
            if 'error' in result:
                lines.append(f"Error: {result['error']}")
            else:
                lines.extend([
                    f"Client Class: {result.get('client_class', 'Unknown')}",
                    f"Interfaces: {', '.join(result['interfaces'])}",
                    f"Error Handling: {'✅ OK' if result['error_handling'] else '❌ Missing'}",
                ])
                
                # Method implementation status
                if result['methods']:
                    lines.append("Methods:")
                    for method, info in result['methods'].items():
                        status = "✅" if info['implemented'] else "❌"
                        prop_indicator = " (property)" if info['is_property'] else ""
                        lines.append(f"  {status} {method}{prop_indicator}")
                
                if result['missing_methods']:
                    lines.append(f"Missing Methods: {', '.join(result['missing_methods'])}")
            
            lines.append("")
        
        # Recommendations
        lines.extend([
            "RECOMMENDATIONS",
            "-" * 40,
            "",
            "1. Ensure all adapters implement the base LLMProvider interface",
            "2. Implement all required methods defined in the interface",
            "3. Use shared exceptions for proper error handling",
            "4. Consider implementing advanced interfaces for additional capabilities",
            ""
        ])
        
        return "\n".join(lines)


def main():
    """Main entry point."""
    validator = InterfaceValidator()
    results = validator.validate_all_adapters()
    
    report = validator.generate_report(results)
    print(report)
    
    # Save results
    import json
    with open('interface_validation_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Exit with appropriate code
    if results['status'] == 'error':
        sys.exit(1)
    
    exit_code = 0 if results['summary']['all_compliant'] else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()