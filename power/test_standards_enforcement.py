#!/usr/bin/env python3
"""
Test standards enforcement system by attempting violations.
This validates that our architecture validation catches violations.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_cross_layer_import_violation():
    """Test that cross-layer imports are detected."""
    print("🚫 Testing cross-layer import violation detection...")

    # Create a temporary file that violates architecture
    violation_code = '''
# This file violates architecture by importing from adapters in core
from adapters.gemini_api.client import GeminiClient
from shared.interfaces.llm_provider import LLMProvider

class BadCoreModule:
    def __init__(self):
        self.client = GeminiClient()  # VIOLATION: core importing adapter
'''

    # Write to a temporary file in core layer
    temp_file = Path("core/modules/bad_module.py")
    temp_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(temp_file, 'w') as f:
            f.write(violation_code)

        from shared.utils.architecture_validator import validate_architecture

        report = validate_architecture(
            project_root="/home/ikino/dev/power",
            file_path=str(temp_file.absolute())
        )

        if report['summary']['total_errors'] > 0:
            print("✅ Cross-layer violation detected!")
            for result in report['results']:
                if result['errors']:
                    print(f"  - Error: {result['errors'][0]}")
            return True
        else:
            print("❌ Cross-layer violation NOT detected!")
            return False

    finally:
        # Clean up
        if temp_file.exists():
            temp_file.unlink()

def test_forbidden_import_violation():
    """Test that forbidden imports are detected."""
    print("🚫 Testing forbidden import violation detection...")

    # Create a temporary file that violates architecture
    violation_code = '''
# This file violates architecture by using external API libraries in core
import requests
from openai import OpenAI

class BadCoreModule:
    def __init__(self):
        self.client = OpenAI()  # VIOLATION: direct API usage in core

    def make_request(self):
        return requests.get("https://api.example.com")  # VIOLATION
'''

    temp_file = Path("core/modules/bad_api_module.py")
    temp_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(temp_file, 'w') as f:
            f.write(violation_code)

        from shared.utils.architecture_validator import validate_architecture

        report = validate_architecture(
            project_root="/home/ikino/dev/power",
            file_path=str(temp_file.absolute())
        )

        if report['summary']['total_errors'] > 0:
            print("✅ Forbidden import violation detected!")
            for result in report['results']:
                if result['errors']:
                    print(f"  - Error: {result['errors'][0]}")
            return True
        else:
            print("❌ Forbidden import violation NOT detected!")
            return False

    finally:
        # Clean up
        if temp_file.exists():
            temp_file.unlink()

def test_correct_architecture_passes():
    """Test that correct architecture passes validation."""
    print("✅ Testing correct architecture validation...")

    # Create a proper core module
    correct_code = '''
# This file follows correct architecture
from shared.interfaces.llm_provider import LLMProvider
from shared.models.llm_request import LLMRequest

class GoodCoreModule:
    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider  # CORRECT: uses interface

    def generate_content(self, prompt: str):
        request = LLMRequest(prompt=prompt)
        return self.llm.generate_text(request)
'''

    temp_file = Path("core/modules/good_module.py")
    temp_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(temp_file, 'w') as f:
            f.write(correct_code)

        from shared.utils.architecture_validator import validate_architecture

        report = validate_architecture(
            project_root="/home/ikino/dev/power",
            file_path=str(temp_file.absolute())
        )

        if report['summary']['total_errors'] == 0:
            print("✅ Correct architecture validated successfully!")
            return True
        else:
            print("❌ Correct architecture failed validation!")
            for result in report['results']:
                if result['errors']:
                    print(f"  - Unexpected error: {result['errors'][0]}")
            return False

    finally:
        # Clean up
        if temp_file.exists():
            temp_file.unlink()

def test_gemini_adapter_compliance():
    """Test that our Gemini adapter follows all standards."""
    print("🔍 Testing Gemini adapter compliance...")

    from shared.utils.architecture_validator import validate_architecture

    # Test all Gemini adapter files
    adapter_files = [
        "/home/ikino/dev/power/adapters/gemini_api/__init__.py",
        "/home/ikino/dev/power/adapters/gemini_api/client.py",
        "/home/ikino/dev/power/adapters/gemini_api/config.py",
        "/home/ikino/dev/power/adapters/gemini_api/data_mapper.py",
        "/home/ikino/dev/power/adapters/gemini_api/exceptions.py",
        "/home/ikino/dev/power/adapters/gemini_api/rate_limiter.py"
    ]

    all_valid = True
    total_files = 0

    for file_path in adapter_files:
        if Path(file_path).exists():
            total_files += 1
            report = validate_architecture(
                project_root="/home/ikino/dev/power",
                file_path=file_path
            )

            if report['summary']['total_errors'] > 0:
                print(f"❌ {Path(file_path).name} has violations:")
                for result in report['results']:
                    if result['errors']:
                        for error in result['errors']:
                            print(f"    - {error}")
                all_valid = False
            else:
                print(f"✅ {Path(file_path).name} compliant")

    if all_valid and total_files > 0:
        print(f"🎉 All {total_files} Gemini adapter files are compliant!")
        return True
    else:
        print(f"❌ {total_files - (total_files if all_valid else 0)} files have violations")
        return False

def test_shared_layer_compliance():
    """Test that shared layer follows standards."""
    print("🔍 Testing shared layer compliance...")

    from shared.utils.architecture_validator import validate_architecture

    # Test shared layer files
    shared_files = [
        "/home/ikino/dev/power/shared/__init__.py",
        "/home/ikino/dev/power/shared/exceptions.py",
        "/home/ikino/dev/power/shared/interfaces/llm_provider.py",
        "/home/ikino/dev/power/shared/models/llm_request.py",
        "/home/ikino/dev/power/shared/models/llm_response.py",
        "/home/ikino/dev/power/shared/config/base_config.py",
        "/home/ikino/dev/power/shared/utils/architecture_validator.py"
    ]

    all_valid = True
    total_files = 0

    for file_path in shared_files:
        if Path(file_path).exists():
            total_files += 1
            report = validate_architecture(
                project_root="/home/ikino/dev/power",
                file_path=file_path
            )

            if report['summary']['total_errors'] > 0:
                print(f"❌ {Path(file_path).name} has violations:")
                for result in report['results']:
                    if result['errors']:
                        for error in result['errors']:
                            print(f"    - {error}")
                all_valid = False
            else:
                print(f"✅ {Path(file_path).name} compliant")

    if all_valid and total_files > 0:
        print(f"🎉 All {total_files} shared layer files are compliant!")
        return True
    else:
        print(f"❌ Some files have violations")
        return False

def main():
    """Run all standards enforcement tests."""
    print("🛡️  Testing Standards Enforcement System")
    print("=" * 60)

    tests = [
        ("Cross-layer Import Violation", test_cross_layer_import_violation),
        ("Forbidden Import Violation", test_forbidden_import_violation),
        ("Correct Architecture Validation", test_correct_architecture_passes),
        ("Gemini Adapter Compliance", test_gemini_adapter_compliance),
        ("Shared Layer Compliance", test_shared_layer_compliance),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)

        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"💥 {test_name} CRASHED: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"🏁 Standards Enforcement Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 STANDARDS ENFORCEMENT WORKING PERFECTLY!")
        print("✅ Architecture violations are detected!")
        print("✅ Compliant code passes validation!")
        print("✅ Three-layer system is enforced!")
        return True
    else:
        print(f"❌ {total - passed} enforcement tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
