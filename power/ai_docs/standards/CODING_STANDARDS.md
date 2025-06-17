# CODING STANDARDS (MANDATORY - NO DEVIATIONS)

**CRITICAL**: All coding work MUST follow these standards. Violation results in immediate task failure and restart.

## THREE-LAYER ARCHITECTURE (NON-NEGOTIABLE)

### Layer Structure (ABSOLUTE REQUIREMENT)

```
core/                    # Business logic, database operations, HTML generation ONLY
adapters/               # External API & MCP integrations ONLY
shared/                 # Common interfaces, models, utilities ONLY
```

### MANDATORY File Placement Rules

#### core/ Layer - Business Logic Only

- **Allowed**: Database handlers, HTML generators, business logic modules
- **Forbidden**: Direct API calls, external service integrations, MCP connections
- **Example**: `core/modules/user_management/user_service.py`

#### adapters/ Layer - External Integrations Only

- **Allowed**: API clients, MCP integrations, external service wrappers
- **Forbidden**: Business logic, database operations, HTML generation
- **Example**: `adapters/gemini_api/client.py`

#### shared/ Layer - Common Contracts Only

- **Allowed**: Interfaces, data models, utilities, configuration abstractions
- **Forbidden**: Implementation details, business logic, API-specific code
- **Example**: `shared/interfaces/llm_provider.py`

## FORBIDDEN PATTERNS (AUTOMATIC FAILURE)

### Cross-Layer Violations

```python
# FORBIDDEN: Core importing from adapters
from adapters.gemini_api import GeminiClient  # VIOLATION

# FORBIDDEN: Adapters importing from core
from core.modules.user_service import UserService  # VIOLATION

# FORBIDDEN: Direct API calls in core
import requests
response = requests.get("https://api.example.com")  # VIOLATION
```

### REQUIRED Patterns

```python
# REQUIRED: Use shared interfaces
from shared.interfaces.llm_provider import LLMProvider

# REQUIRED: Dependency injection through shared layer
class ContentService:
    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider
```

## INTERFACE CONTRACT REQUIREMENTS

### All External Integrations MUST Implement Shared Interfaces

```python
# adapters/gemini_api/client.py
from shared.interfaces.llm_provider import LLMProvider

class GeminiAdapter(LLLProvider):
    def generate_text(self, prompt: str) -> str:
        # Implementation details
        pass
```

### Core Modules MUST Use Interface Abstractions

```python
# core/modules/content_generator.py
from shared.interfaces.llm_provider import LLMProvider

class ContentGenerator:
    def __init__(self, llm: LLMProvider):
        self.llm = llm  # Uses interface, not concrete implementation
```

## DEPENDENCY MANAGEMENT

### Package Installation Rules

- **Core dependencies**: Only business logic libraries (SQLAlchemy, Jinja2, etc.)
- **Adapter dependencies**: API-specific packages isolated per adapter
- **Shared dependencies**: Common utilities only (pydantic, typing, etc.)

### Requirements Structure

```
requirements/
├── core.txt          # Core layer dependencies
├── adapters.txt      # Common adapter dependencies
├── gemini.txt        # Gemini-specific dependencies
└── shared.txt        # Shared layer dependencies
```

## CONFIGURATION ISOLATION

### Environment Variables

- **Core**: Database URLs, HTML template paths
- **Adapters**: API keys, endpoint URLs, rate limits
- **Shared**: Common settings, logging configuration

### Configuration Access Pattern

```python
# REQUIRED: Use shared configuration abstraction
from shared.config.settings import get_adapter_config

config = get_adapter_config('gemini')
api_key = config.get('api_key')
```

## ERROR HANDLING STANDARDS

### Adapter Error Translation

```python
# REQUIRED: Translate external errors to shared exceptions
from shared.exceptions import LLMProviderError

try:
    response = external_api.call()
except ExternalAPIError as e:
    raise LLMProviderError(f"Gemini API failed: {e}")
```

### Core Error Handling

```python
# REQUIRED: Handle shared exceptions only
from shared.exceptions import LLMProviderError

try:
    content = self.llm.generate_text(prompt)
except LLMProviderError:
    # Handle abstracted error, no knowledge of specific API
    pass
```

## TESTING REQUIREMENTS

### Layer-Specific Testing

- **Core tests**: Mock all external dependencies through interfaces
- **Adapter tests**: Test external API integration and error handling
- **Shared tests**: Validate interface contracts and models

### Test Structure

```
tests/
├── core/             # Business logic tests
├── adapters/         # Integration tests
├── shared/           # Interface contract tests
└── integration/      # Full system tests
```

## VALIDATION CHECKLIST (MANDATORY)

Before any code submission, verify:

- [ ] All files placed in correct layer (core/adapters/shared)
- [ ] No cross-layer imports (core ↔ adapters)
- [ ] Shared interfaces used for all external dependencies
- [ ] Configuration properly isolated
- [ ] Error handling follows translation patterns
- [ ] Tests validate layer boundaries
- [ ] Documentation updated for new components

## VIOLATION CONSEQUENCES

### Immediate Actions for Non-Compliance

1. **Task termination** and restart from clean state
2. **Architecture review** before any new coding attempts
3. **Mandatory re-reading** of this standards document
4. **Compliance verification** in updated plan.md

### Integration Rejection Criteria

- Any cross-layer violations detected
- Missing interface implementations
- Improper configuration handling
- Inadequate error translation
- Test coverage gaps for layer boundaries

## CONTINUOUS COMPLIANCE

### Before Every Coding Session

1. **Read this document** completely
2. **Identify target layer** for your work
3. **Plan interface contracts** needed
4. **Validate approach** against these standards
5. **Confirm understanding** in plan.md

### During Development

- **Check file placement** before creating new files
- **Validate imports** before adding dependencies
- **Test interface contracts** continuously
- **Document architectural decisions**

### Before Submission

- **Run architecture validation** scripts
- **Verify layer compliance** with automated checks
- **Test interface boundaries** thoroughly
- **Confirm zero violations** in submission package

**REMEMBER**: These standards are not suggestions - they are requirements that ensure system maintainability, testability, and scalability. Deviation is not acceptable under any circumstances.
