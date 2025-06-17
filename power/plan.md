# Gemini API Adapter Implementation Plan

## STANDARDS COMPLIANCE ACKNOWLEDGMENT

✅ **MANDATORY STANDARDS READ AND UNDERSTOOD:**

1. ✅ Read `ai_docs/standards/CODING_STANDARDS.md` completely
2. ✅ Read `ai_docs/standards/API_INTEGRATION_STANDARDS.md` completely
3. ✅ Confirmed understanding of three-layer architecture requirements
4. ✅ Standards compliance checklist included below

## TASK OVERVIEW

Create production-ready Gemini API adapter using NEW Google Gen AI SDK (2024) that integrates with Power Builder three-layer architecture system.

## TECHNICAL IMPLEMENTATION DETAILS

### New Google Gen AI SDK Requirements

- **Package**: `google-genai` (NOT the deprecated google-generativeai)
- **Installation**: `pip install google-genai`
- **Authentication**: Uses GEMINI_API_KEY environment variable
- **Client**: `genai.Client(api_key="YOUR_API_KEY")`
- **Method**: `client.models.generate_content(model="gemini-2.0-flash", contents="prompt")`
- **Response**: `response.text` for generated content

### Architecture Compliance (NON-NEGOTIABLE)

- ✅ Place all files in `adapters/gemini_api/` directory
- ✅ Follow mandatory directory structure from API_INTEGRATION_STANDARDS.md
- ✅ Use shared interfaces and models exclusively
- ✅ No direct imports from core layer
- ✅ Implement proper configuration isolation

## IMPLEMENTATION STRUCTURE

```
adapters/gemini_api/
├── __init__.py              # Public interface exports
├── client.py                # Main Gemini client implementing LLMProvider
├── data_mapper.py           # Data transformation to/from shared models
├── config.py                # Gemini-specific configuration
├── exceptions.py            # Error translation to shared exceptions
└── rate_limiter.py          # Rate limiting implementation
```

## IMPLEMENTATION STEPS

### Step 1: Update Configuration (config.py)

- ✅ Update model names to use gemini-2.0-flash
- ✅ Use BaseAdapterConfig from shared.config.base_config
- ✅ Load GEMINI_API_KEY from environment
- ✅ Support configuration for model selection, timeouts, rate limits
- ✅ Remove references to old models

### Step 2: Update Data Mapper (data_mapper.py)

- ✅ Convert LLMRequest to new Gemini format
- ✅ Map new Gemini responses to LLMResponse with proper usage stats
- ✅ Handle finish reasons (completed, max_tokens, etc.)
- ✅ Update for new SDK response format

### Step 3: Update Exception Handling (exceptions.py)

- ✅ Translate new Gemini exceptions to shared exceptions
- ✅ Handle authentication errors, rate limits, quota exceeded
- ✅ Implement proper retry logic for transient errors
- ✅ Update error patterns for new SDK

### Step 4: Update Rate Limiter (rate_limiter.py)

- ✅ Use BaseRateLimiter from shared utilities
- ✅ Implement Gemini-specific rate limiting logic
- ✅ Handle new API response patterns
- ✅ Support adaptive rate limiting

### Step 5: Update Main Client (client.py)

- ✅ Replace old google-generativeai with google-genai
- ✅ Implement complete LLMProvider interface
- ✅ Use new client initialization: `genai.Client(api_key="YOUR_API_KEY")`
- ✅ Use new method: `client.models.generate_content(model="gemini-2.0-flash", contents="prompt")`
- ✅ Update response parsing for new SDK
- ✅ Maintain all existing features (streaming, multimodal, etc.)

### Step 6: Update Package Exports (**init**.py)

- ✅ Export main client class
- ✅ Export configuration class
- ✅ Follow export patterns from standards

### Step 7: Testing and Validation

- ✅ Update all unit tests for new SDK
- ✅ Test with real Gemini API using GEMINI_API_KEY
- ✅ Validate architecture compliance
- ✅ Ensure 100% test success rate
- ✅ Achieve perfect 10/10 pylint score

## SUCCESS CRITERIA

- ✅ All tests pass (100% success rate)
- ✅ Perfect 10/10 pylint score
- ✅ Zero architecture violations using validation script
- ✅ Successful integration with shared interfaces
- ✅ Real Gemini API calls working with GEMINI_API_KEY
- ✅ Proper error handling and rate limiting

## STANDARDS COMPLIANCE CHECKLIST (MANDATORY)

### Three-Layer Architecture Compliance

- ✅ All files placed in adapters/ layer (external integrations only)
- ✅ No cross-layer imports (adapters ↔ core forbidden)
- ✅ Uses shared interfaces for all external dependencies
- ✅ Configuration properly isolated using BaseAdapterConfig
- ✅ Error handling follows translation patterns
- ✅ Tests validate layer boundaries

### API Integration Standards Compliance

- ✅ Implements required shared interface (LLMProvider) completely
- ✅ Follows mandatory directory structure
- ✅ Includes proper configuration isolation with GEMINI\_\* env vars
- ✅ Implements data transformation for all inputs/outputs
- ✅ Handles all API errors with proper translation to shared exceptions
- ✅ Includes rate limiting and quota management
- ✅ Implements response caching
- ✅ Has comprehensive test coverage (>90%)
- ✅ Includes integration tests with real API
- ✅ Implements proper logging and metrics

### Additional Requirements

- ✅ Uses GEMINI_API_KEY from .env file
- ✅ Supports gemini-2.0-flash model
- ✅ Implements proper error handling with shared exception translation
- ✅ Includes rate limiting and quota management
- ✅ Adds response caching for efficiency

## VALIDATION PROCESS

Run architecture validation before submission:

```python
from shared.utils.architecture_validator import validate_architecture
result = validate_architecture(file_path="adapters/gemini_api/client.py")
```

## COMPLETION SIGNAL

Report completion with: **"Task complete and ready for next step"**
