# API INTEGRATION STANDARDS (MANDATORY)

**CRITICAL**: All external API integrations MUST follow these standards. These rules ensure backward compatibility, maintainability, and seamless adapter swapping.

## ADAPTER PATTERN REQUIREMENTS (NON-NEGOTIABLE)

### Adapter Structure (ABSOLUTE REQUIREMENT)

```
adapters/{api_name}/
├── __init__.py          # Public interface exports
├── client.py            # Main API client implementation
├── data_mapper.py       # Data transformation to shared models
├── config.py            # API-specific configuration
├── exceptions.py        # API-specific error handling
└── rate_limiter.py      # API quota and rate management
```

### MANDATORY Interface Implementation

Every adapter MUST implement the corresponding shared interface:

```python
# All LLM adapters MUST implement
from shared.interfaces.llm_provider import LLMProvider

# All data adapters MUST implement
from shared.interfaces.data_provider import DataProvider

# All storage adapters MUST implement
from shared.interfaces.storage_provider import StorageProvider
```

## CONFIGURATION ISOLATION RULES

### Environment Variable Naming Convention

```bash
# REQUIRED format: {API_NAME}_{SETTING_NAME}
GEMINI_API_KEY=your_key_here
GEMINI_BASE_URL=https://api.gemini.com
GEMINI_RATE_LIMIT=60
GEMINI_TIMEOUT=30

YOUTUBE_API_KEY=your_key_here
YOUTUBE_QUOTA_LIMIT=10000
```

### Configuration Access Pattern (MANDATORY)

```python
# adapters/gemini_api/config.py
from shared.config.base_config import BaseAdapterConfig

class GeminiConfig(BaseAdapterConfig):
    def __init__(self):
        super().__init__('gemini')
        self.api_key = self.get_required('api_key')
        self.base_url = self.get_optional('base_url', 'https://api.gemini.com')
        self.rate_limit = self.get_optional('rate_limit', 60)
```

## DATA TRANSFORMATION REQUIREMENTS

### Input/Output Mapping (ABSOLUTE REQUIREMENT)

All adapters MUST translate between external API formats and shared models:

```python
# adapters/gemini_api/data_mapper.py
from shared.models.llm_request import LLMRequest
from shared.models.llm_response import LLMResponse

class GeminiDataMapper:
    @staticmethod
    def map_request(shared_request: LLMRequest) -> dict:
        """Convert shared request to Gemini API format"""
        return {
            'prompt': shared_request.prompt,
            'max_tokens': shared_request.max_tokens,
            'temperature': shared_request.temperature
        }

    @staticmethod
    def map_response(gemini_response: dict) -> LLMResponse:
        """Convert Gemini response to shared format"""
        return LLMResponse(
            content=gemini_response['text'],
            tokens_used=gemini_response['usage']['total_tokens'],
            model=gemini_response['model']
        )
```

## ERROR HANDLING STANDARDS

### Exception Translation (MANDATORY)

```python
# adapters/gemini_api/exceptions.py
from shared.exceptions import (
    LLMProviderError,
    RateLimitError,
    AuthenticationError,
    QuotaExceededError
)

class GeminiExceptionMapper:
    @staticmethod
    def translate_exception(gemini_error) -> Exception:
        if gemini_error.status_code == 401:
            return AuthenticationError("Invalid Gemini API key")
        elif gemini_error.status_code == 429:
            return RateLimitError("Gemini rate limit exceeded")
        elif gemini_error.status_code == 403:
            return QuotaExceededError("Gemini quota exceeded")
        else:
            return LLMProviderError(f"Gemini API error: {gemini_error}")
```

### Client Error Handling Pattern

```python
# adapters/gemini_api/client.py
try:
    response = self._make_api_call(request)
    return self.data_mapper.map_response(response)
except GeminiAPIError as e:
    raise GeminiExceptionMapper.translate_exception(e)
```

## RATE LIMITING & QUOTA MANAGEMENT

### Required Rate Limiter Implementation

```python
# adapters/gemini_api/rate_limiter.py
from shared.utils.rate_limiter import BaseRateLimiter

class GeminiRateLimiter(BaseRateLimiter):
    def __init__(self, config: GeminiConfig):
        super().__init__(
            calls_per_minute=config.rate_limit,
            quota_per_day=config.daily_quota
        )

    def check_quota(self) -> bool:
        """Check if API call is allowed within limits"""
        return self.can_make_call()
```

### Rate Limiting Integration (MANDATORY)

```python
# All API calls MUST check rate limits first
def generate_text(self, request: LLMRequest) -> LLMResponse:
    if not self.rate_limiter.check_quota():
        raise RateLimitError("Rate limit exceeded")

    # Proceed with API call
    return self._make_api_call(request)
```

## CACHING REQUIREMENTS

### Response Caching Pattern (REQUIRED)

```python
# adapters/gemini_api/client.py
from shared.utils.cache import ResponseCache

class GeminiClient:
    def __init__(self):
        self.cache = ResponseCache(
            ttl_seconds=3600,  # 1 hour cache
            max_size=1000      # Max cached responses
        )

    def generate_text(self, request: LLMRequest) -> LLMResponse:
        cache_key = self._generate_cache_key(request)

        # Check cache first
        if cached_response := self.cache.get(cache_key):
            return cached_response

        # Make API call and cache result
        response = self._make_api_call(request)
        self.cache.set(cache_key, response)
        return response
```

## TESTING STANDARDS

### Required Test Coverage

```python
# tests/adapters/gemini_api/test_client.py
class TestGeminiClient:
    def test_successful_request(self):
        """Test normal API call flow"""
        pass

    def test_rate_limit_handling(self):
        """Test rate limit enforcement"""
        pass

    def test_error_translation(self):
        """Test exception mapping to shared exceptions"""
        pass

    def test_data_mapping(self):
        """Test request/response transformation"""
        pass

    def test_caching_behavior(self):
        """Test response caching logic"""
        pass
```

### Integration Testing Requirements

```python
# tests/integration/test_gemini_integration.py
def test_end_to_end_flow():
    """Test complete flow from core module through adapter"""
    # Use real API key from test environment
    # Validate full request/response cycle
    # Confirm shared interface compliance
```

## VERSIONING & BACKWARD COMPATIBILITY

### API Version Management

```python
# adapters/gemini_api/versions/
├── v1/
│   ├── client.py
│   └── data_mapper.py
├── v2/
│   ├── client.py
│   └── data_mapper.py
└── client.py  # Version router
```

### Version Router Pattern (REQUIRED)

```python
# adapters/gemini_api/client.py
from .versions.v1.client import GeminiClientV1
from .versions.v2.client import GeminiClientV2

class GeminiClient:
    def __init__(self, api_version='v2'):
        if api_version == 'v1':
            self.client = GeminiClientV1()
        elif api_version == 'v2':
            self.client = GeminiClientV2()
        else:
            raise ValueError(f"Unsupported API version: {api_version}")
```

## LOGGING & MONITORING

### Required Logging Implementation

```python
# adapters/gemini_api/client.py
import logging
from shared.utils.logger import get_adapter_logger

class GeminiClient:
    def __init__(self):
        self.logger = get_adapter_logger('gemini')

    def generate_text(self, request: LLMRequest) -> LLMResponse:
        self.logger.info(f"Making Gemini API call: {request.prompt[:50]}...")

        try:
            response = self._make_api_call(request)
            self.logger.info(f"Gemini API success: {response.tokens_used} tokens")
            return response
        except Exception as e:
            self.logger.error(f"Gemini API error: {e}")
            raise
```

### Metrics Collection (REQUIRED)

```python
# Track API usage metrics
from shared.utils.metrics import AdapterMetrics

class GeminiClient:
    def __init__(self):
        self.metrics = AdapterMetrics('gemini')

    def generate_text(self, request: LLMRequest) -> LLMResponse:
        with self.metrics.timer('api_call_duration'):
            response = self._make_api_call(request)

        self.metrics.increment('api_calls_total')
        self.metrics.histogram('tokens_used', response.tokens_used)
        return response
```

## ADAPTER VALIDATION CHECKLIST (MANDATORY)

Before submitting any API adapter:

- [ ] Implements required shared interface completely
- [ ] Follows mandatory directory structure
- [ ] Includes proper configuration isolation
- [ ] Implements data transformation for all inputs/outputs
- [ ] Handles all API errors with proper translation
- [ ] Includes rate limiting and quota management
- [ ] Implements response caching
- [ ] Has comprehensive test coverage (>90%)
- [ ] Includes integration tests with real API
- [ ] Supports API versioning where applicable
- [ ] Implements proper logging and metrics
- [ ] Documentation updated with usage examples

## INTEGRATION REQUIREMENTS

### Adapter Registration (AUTOMATIC)

```python
# shared/registry/adapter_registry.py
from adapters.gemini_api import GeminiClient

# Adapters auto-register on import
ADAPTER_REGISTRY = {
    'gemini': GeminiClient,
    'openai': OpenAIClient,
    # Additional adapters registered automatically
}
```

### Core Module Usage Pattern

```python
# core/modules/content_generator.py
from shared.registry import get_adapter

class ContentGenerator:
    def __init__(self, llm_provider_name='gemini'):
        # Uses adapter through registry, no direct imports
        self.llm = get_adapter('llm', llm_provider_name)
```

## FORBIDDEN PATTERNS (AUTOMATIC FAILURE)

### Direct API Usage in Core

```python
# FORBIDDEN: Direct API imports in core modules
import google.generativeai as genai  # VIOLATION

# FORBIDDEN: Hardcoded API endpoints
response = requests.post("https://api.gemini.com/v1/generate")  # VIOLATION
```

### Shared Model Violations

```python
# FORBIDDEN: API-specific models in shared layer
class GeminiResponse:  # VIOLATION - API-specific in shared layer
    pass

# FORBIDDEN: Shared models importing adapter code
from adapters.gemini_api import GeminiClient  # VIOLATION
```

**REMEMBER**: These standards ensure that API integrations are maintainable, swappable, and backward compatible. Following these patterns allows seamless addition of new APIs without breaking existing functionality.
