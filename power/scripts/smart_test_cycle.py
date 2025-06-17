#!/usr/bin/env python3
"""
Smart 3-Test Cycle with LLM Fallback Integration
Optimized error resolution for pre-commit hooks
"""
import os
import sys
import json
import subprocess
import time
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import tempfile
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/smart_test_cycle.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SmartTestCycle:
    """Manages 3-test cycle with intelligent LLM fallback for error resolution."""

    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.max_attempts = 3
        self.test_commands = [
            {'name': 'pytest', 'cmd': ['python', '-m', 'pytest', '-v', '--tb=short', 'tests/']},
            {'name': 'pylint', 'cmd': ['python', '-m', 'pylint', '--fail-under=10.0', '--rcfile=.pylintrc', 'shared/', 'adapters/', 'core/']},
            {'name': 'mypy', 'cmd': ['python', '-m', 'mypy', '--config-file=mypy.ini', 'shared/', 'adapters/', 'core/']},
            {'name': 'architecture', 'cmd': ['python', '-c', 'import sys; sys.path.append("."); from shared.utils.architecture_validator import validate_architecture; import json; print(json.dumps(validate_architecture(), indent=2))']}
        ]
        self.llm_fallback_enabled = self._check_llm_availability()

    def _check_llm_availability(self) -> bool:
        """Check if LLM fallback is available via environment variables."""
        env_vars = ['OPENAI_API_KEY', 'GOOGLE_API_KEY', 'ANTHROPIC_API_KEY', 'PERPLEXITY_API_KEY']
        available_llms = [var for var in env_vars if os.getenv(var)]

        if available_llms:
            logger.info(f"LLM fallback available with: {', '.join(available_llms)}")
            return True
        else:
            logger.warning("No LLM API keys found - fallback disabled")
            return False

    def run_test_cycle(self) -> bool:
        """Execute the 3-test cycle with optional LLM fallback."""
        logger.info("Starting Smart 3-Test Cycle")

        for attempt in range(1, self.max_attempts + 1):
            logger.info(f"=== Test Attempt {attempt}/{self.max_attempts} ===")

            test_results = self._run_all_tests()

            if all(result['passed'] for result in test_results):
                logger.info("✅ All tests passed! Cycle completed successfully.")
                return True

            # Log failures
            failed_tests = [r for r in test_results if not r['passed']]
            logger.error(f"❌ {len(failed_tests)} test(s) failed:")
            for result in failed_tests:
                logger.error(f"  - {result['name']}: {result['error']}")

            # On final attempt with failures, try LLM fallback
            if attempt == self.max_attempts - 1 and self.llm_fallback_enabled:
                logger.info("🤖 Triggering LLM fallback for error resolution...")
                if self._llm_error_resolution(failed_tests):
                    # Run final test after LLM fixes
                    final_results = self._run_all_tests()
                    if all(result['passed'] for result in final_results):
                        logger.info("✅ LLM fallback successful! All tests now pass.")
                        return True
                    else:
                        logger.error("❌ LLM fallback could not resolve all issues.")

            if attempt < self.max_attempts:
                logger.info(f"Preparing for attempt {attempt + 1}...")
                time.sleep(2)  # Brief pause between attempts

        logger.error("❌ Test cycle failed after all attempts.")
        return False

    def _run_all_tests(self) -> List[Dict]:
        """Run all configured tests and return results."""
        results = []

        for test_config in self.test_commands:
            logger.info(f"Running {test_config['name']}...")
            result = self._run_single_test(test_config)
            results.append(result)

            if not result['passed']:
                logger.warning(f"⚠️  {test_config['name']} failed: {result['error'][:200]}...")

        return results

    def _run_single_test(self, test_config: Dict) -> Dict:
        """Run a single test command and capture results."""
        try:
            # Change to project root
            os.chdir(self.project_root)

            # Run the test command
            process = subprocess.run(
                test_config['cmd'],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            success = process.returncode == 0
            output = process.stdout + process.stderr

            return {
                'name': test_config['name'],
                'passed': success,
                'output': output,
                'error': output if not success else '',
                'return_code': process.returncode
            }

        except subprocess.TimeoutExpired:
            return {
                'name': test_config['name'],
                'passed': False,
                'output': '',
                'error': f"Test {test_config['name']} timed out after 5 minutes",
                'return_code': -1
            }
        except Exception as e:
            return {
                'name': test_config['name'],
                'passed': False,
                'output': '',
                'error': f"Failed to run {test_config['name']}: {str(e)}",
                'return_code': -1
            }

    def _llm_error_resolution(self, failed_tests: List[Dict]) -> bool:
        """Use LLM fallback to analyze and potentially fix errors."""
        try:
            # Prepare error context for LLM
            error_context = self._prepare_error_context(failed_tests)

            # Try different LLM providers in order of preference
            llm_providers = [
                ('perplexity', self._query_perplexity),
                ('openai', self._query_openai),
                ('google', self._query_google),
                ('anthropic', self._query_anthropic)
            ]

            for provider_name, query_func in llm_providers:
                if self._is_llm_available(provider_name):
                    logger.info(f"Trying {provider_name} for error resolution...")

                    try:
                        suggestion = query_func(error_context)
                        if suggestion and self._apply_llm_suggestion(suggestion):
                            logger.info(f"✅ Applied suggestion from {provider_name}")
                            return True
                    except Exception as e:
                        logger.warning(f"❌ {provider_name} failed: {str(e)}")
                        continue

            logger.warning("❌ All LLM providers failed or unavailable")
            return False

        except Exception as e:
            logger.error(f"❌ LLM error resolution failed: {str(e)}")
            return False

    def _prepare_error_context(self, failed_tests: List[Dict]) -> str:
        """Prepare error context for LLM analysis."""
        context = "Python code testing errors that need resolution:\n\n"

        for test in failed_tests:
            context += f"=== {test['name']} Error ===\n"
            context += f"Error Output:\n{test['error'][:1000]}\n\n"

        context += "Project Structure:\n"
        context += "- Three-layer architecture: core/, adapters/, shared/\n"
        context += "- Requirements: 100% pytest success, 10/10 pylint score\n"
        context += "- Python 3.12, modern typing practices\n\n"
        context += "Please provide specific, actionable fixes for these errors."

        return context

    def _is_llm_available(self, provider: str) -> bool:
        """Check if specific LLM provider is available."""
        provider_env_map = {
            'openai': 'OPENAI_API_KEY',
            'google': 'GOOGLE_API_KEY',
            'anthropic': 'ANTHROPIC_API_KEY',
            'perplexity': 'PERPLEXITY_API_KEY'
        }
        return bool(os.getenv(provider_env_map.get(provider, '')))

    def _query_perplexity(self, error_context: str) -> Optional[str]:
        """Query Perplexity for error resolution suggestions."""
        try:
            import requests

            api_key = os.getenv('PERPLEXITY_API_KEY')
            if not api_key:
                return None

            response = requests.post(
                'https://api.perplexity.ai/chat/completions',
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'llama-3.1-sonar-small-128k-online',
                    'messages': [
                        {
                            'role': 'system',
                            'content': 'You are a Python debugging expert. Provide specific, actionable code fixes.'
                        },
                        {
                            'role': 'user',
                            'content': error_context
                        }
                    ],
                    'max_tokens': 1000,
                    'temperature': 0.1
                },
                timeout=30
            )

            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                logger.warning(f"Perplexity API error: {response.status_code}")
                return None

        except Exception as e:
            logger.warning(f"Perplexity query failed: {str(e)}")
            return None

    def _query_openai(self, error_context: str) -> Optional[str]:
        """Query OpenAI for error resolution suggestions."""
        try:
            import openai

            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                return None

            client = openai.OpenAI(api_key=api_key)

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a Python debugging expert. Provide specific, actionable code fixes."
                    },
                    {
                        "role": "user",
                        "content": error_context
                    }
                ],
                max_tokens=1000,
                temperature=0.1
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.warning(f"OpenAI query failed: {str(e)}")
            return None

    def _query_google(self, error_context: str) -> Optional[str]:
        """Query Google Gemini for error resolution suggestions."""
        try:
            import google.generativeai as genai

            api_key = os.getenv('GOOGLE_API_KEY')
            if not api_key:
                return None

            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-pro')

            prompt = f"""You are a Python debugging expert. Provide specific, actionable code fixes.

{error_context}"""

            response = model.generate_content(prompt)
            return response.text

        except Exception as e:
            logger.warning(f"Google Gemini query failed: {str(e)}")
            return None

    def _query_anthropic(self, error_context: str) -> Optional[str]:
        """Query Anthropic Claude for error resolution suggestions."""
        try:
            import anthropic

            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                return None

            client = anthropic.Anthropic(api_key=api_key)

            response = client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                messages=[
                    {
                        "role": "user",
                        "content": f"You are a Python debugging expert. Provide specific, actionable code fixes.\n\n{error_context}"
                    }
                ]
            )

            return response.content[0].text

        except Exception as e:
            logger.warning(f"Anthropic query failed: {str(e)}")
            return None

    def _apply_llm_suggestion(self, suggestion: str) -> bool:
        """Apply LLM suggestion if it contains actionable code fixes."""
        # For now, just log the suggestion
        # In a more advanced implementation, this could parse and apply code changes
        logger.info("🤖 LLM Suggestion:")
        logger.info(suggestion)

        # Save suggestion to file for manual review
        suggestions_file = self.project_root / 'logs' / 'llm_suggestions.log'
        suggestions_file.parent.mkdir(exist_ok=True)

        with open(suggestions_file, 'a', encoding='utf-8') as f:
            f.write(f"\n=== {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
            f.write(suggestion)
            f.write("\n" + "="*50 + "\n")

        logger.info(f"💾 Suggestion saved to {suggestions_file}")

        # Return False for now - manual intervention required
        # This could be enhanced to automatically apply simple fixes
        return False


def main():
    """Main entry point for the smart test cycle."""
    # Ensure logs directory exists
    Path('logs').mkdir(exist_ok=True)

    # Initialize and run test cycle
    test_cycle = SmartTestCycle()
    success = test_cycle.run_test_cycle()

    if success:
        logger.info("🎉 Smart test cycle completed successfully!")
        sys.exit(0)
    else:
        logger.error("💥 Smart test cycle failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
