"""
Pytest configuration for Gemini API adapter tests.
"""

import pytest
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests that require real API access"
    )


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    # Set test environment variables
    test_env = {
        'GEMINI_RATE_LIMIT_PER_MINUTE': '10',  # Lower rate limit for testing
        'GEMINI_CACHE_TTL_SECONDS': '60',      # Shorter cache TTL for testing
        'GEMINI_ENABLE_CACHING': 'true',
        'GEMINI_ENABLE_STREAMING': 'true',
        'GEMINI_MODEL': 'gemini-2.0-flash'    # Updated for new SDK
    }

    # Only set if not already present (don't override real values)
    for key, value in test_env.items():
        if key not in os.environ:
            os.environ[key] = value

    yield

    # Cleanup - remove test env vars we added
    for key in test_env:
        if os.environ.get(key) == test_env[key]:
            os.environ.pop(key, None)


@pytest.fixture
def mock_api_key():
    """Provide a mock API key for tests that don't use real API."""
    return 'test_api_key_12345678901234567890'


def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle integration tests."""
    # Skip integration tests if no API key is available
    if not os.getenv('GEMINI_API_KEY'):
        skip_integration = pytest.mark.skip(
            reason="GEMINI_API_KEY environment variable not set"
        )
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)


def pytest_addoption(parser):
    """Add command line options for test configuration."""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests that require real API access"
    )

    parser.addoption(
        "--api-key",
        action="store",
        default=None,
        help="Gemini API key for integration tests"
    )


def pytest_runtest_setup(item):
    """Set up individual test runs."""
    # Handle integration test setup
    if "integration" in item.keywords:
        if not item.config.getoption("--run-integration"):
            pytest.skip("Integration tests not enabled (use --run-integration)")

        # Set API key if provided via command line
        api_key = item.config.getoption("--api-key")
        if api_key:
            os.environ['GEMINI_API_KEY'] = api_key
