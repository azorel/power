# PROMPTING STANDARDS

**MANDATORY**: All LLM interactions and agent communication MUST follow these standards for consistency, efficiency, and quality results.

## Agent Communication Standards

### Task Delegation Format (ABSOLUTE REQUIREMENT)
```python
# REQUIRED: Standardized task delegation prompt format
AGENT_TASK_TEMPLATE = """
You are a development agent. Complete this task with PYLINT-CLEAN CODE from the first attempt:

TASK: {task_description}

MANDATORY PRE-CODING STEPS:
1. Read ai_docs/standards/CODING_STANDARDS.md completely before any coding
2. Read ai_docs/standards/{relevant_standards}.md for task-specific requirements
3. Understand three-layer architecture: core/ adapters/ shared/
4. Plan all docstrings, type hints, and import organization upfront

PYLINT 10/10 REQUIREMENTS (WRITE CLEAN FROM START):
- Module docstring: Triple-quoted description at file top
- Function docstrings: Args, Returns, Raises for every function
- Type hints: All parameters and return types annotated
- Import organization: stdlib → third-party → local with blank lines
- Variable naming: snake_case, descriptive names, no single letters
- Function length: Keep under 15 lines, extract complex logic
- Error handling: Specific exception types, no bare except
- Code complexity: Simple, readable, well-structured

ARCHITECTURE COMPLIANCE:
- Place files in correct layer (core/adapters/shared)
- Use shared interfaces for external dependencies
- No cross-layer imports (core ↔ adapters forbidden)
- Follow dependency injection patterns

QUALITY GATES (MUST ACHIEVE):
- Perfect 10/10 pylint score on first attempt
- 100% test coverage with proper test structure
- Zero architecture violations
- Complete documentation

COMPLETION REQUIREMENT:
End with: "Task complete and ready for next step"

Begin with reading required standards, then implement clean code immediately.
"""
```

### Standards Integration (MANDATORY)
```python
def create_agent_prompt(task: str, work_type: str) -> str:
    """
    Create standardized agent prompt with appropriate standards.
    
    Args:
        task: Description of task to be completed
        work_type: Type of work (coding, research, integration, testing)
        
    Returns:
        Formatted prompt with required standards
    """
    # Map work types to required standards
    standards_mapping = {
        'coding': ['CODING_STANDARDS.md'],
        'api_integration': ['CODING_STANDARDS.md', 'API_INTEGRATION_STANDARDS.md'],
        'research': ['RESEARCH_STANDARDS.md'],
        'testing': ['TESTING_STANDARDS.md', 'CODING_STANDARDS.md'],
        'integration': ['INTEGRATION_STANDARDS.md', 'CODING_STANDARDS.md']
    }
    
    required_standards = standards_mapping.get(work_type, ['CODING_STANDARDS.md'])
    
    standards_instructions = "\n".join([
        f"- Read ai_docs/standards/{standard} completely before starting"
        for standard in required_standards
    ])
    
    return AGENT_TASK_TEMPLATE.format(
        task_description=task,
        relevant_standards=", ".join(required_standards),
        standards_instructions=standards_instructions
    )
```

## LLM Provider Interaction Standards

### Request Formatting (REQUIRED)
```python
"""
Standardized LLM request formatting for consistent results.
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class StandardLLMRequest:
    """Standard format for all LLM requests."""
    prompt: str
    system_instruction: Optional[str] = None
    max_tokens: int = 2000
    temperature: float = 0.7
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: Optional[list] = None
    
    def to_provider_format(self, provider: str) -> Dict[str, Any]:
        """Convert to provider-specific format."""
        if provider == 'gemini':
            return self._to_gemini_format()
        elif provider == 'openai':
            return self._to_openai_format()
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def _to_gemini_format(self) -> Dict[str, Any]:
        """Convert to Gemini API format."""
        request = {
            'contents': [{'parts': [{'text': self.prompt}]}],
            'generationConfig': {
                'maxOutputTokens': self.max_tokens,
                'temperature': self.temperature,
                'topP': self.top_p
            }
        }
        
        if self.system_instruction:
            request['systemInstruction'] = {
                'parts': [{'text': self.system_instruction}]
            }
        
        if self.stop_sequences:
            request['generationConfig']['stopSequences'] = self.stop_sequences
        
        return request
    
    def _to_openai_format(self) -> Dict[str, Any]:
        """Convert to OpenAI API format."""
        messages = []
        
        if self.system_instruction:
            messages.append({
                'role': 'system',
                'content': self.system_instruction
            })
        
        messages.append({
            'role': 'user',
            'content': self.prompt
        })
        
        request = {
            'messages': messages,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'top_p': self.top_p,
            'frequency_penalty': self.frequency_penalty,
            'presence_penalty': self.presence_penalty
        }
        
        if self.stop_sequences:
            request['stop'] = self.stop_sequences
        
        return request
```

### Response Validation (MANDATORY)
```python
def validate_llm_response(response: str, expected_format: str) -> bool:
    """
    Validate LLM response meets expected format and quality.
    
    Args:
        response: LLM response to validate
        expected_format: Expected response format (code, markdown, json, etc.)
        
    Returns:
        True if response meets validation criteria
    """
    if not response or len(response.strip()) == 0:
        return False
    
    if expected_format == 'code':
        return validate_code_response(response)
    elif expected_format == 'markdown':
        return validate_markdown_response(response)
    elif expected_format == 'json':
        return validate_json_response(response)
    
    return True

def validate_code_response(code: str) -> bool:
    """Validate code response format and syntax."""
    try:
        # Check for basic code structure
        if 'def ' not in code and 'class ' not in code:
            return False
        
        # Check for docstrings
        if '"""' not in code and "'''" not in code:
            return False
        
        # Validate Python syntax
        import ast
        ast.parse(code)
        return True
        
    except SyntaxError:
        return False
```

## Prompt Engineering Best Practices

### Task Decomposition (REQUIRED)
```python
"""
Break complex tasks into manageable sub-tasks for better results.
"""
def decompose_complex_task(task_description: str) -> list:
    """
    Decompose complex task into manageable sub-tasks.
    
    Args:
        task_description: Complex task to be decomposed
        
    Returns:
        List of sub-tasks in execution order
    """
    # Use LLM to analyze and decompose task
    decomposition_prompt = f"""
    Analyze this complex task and break it down into specific, manageable sub-tasks:
    
    TASK: {task_description}
    
    REQUIREMENTS:
    - Each sub-task should be completable in under 30 minutes
    - Sub-tasks should have clear dependencies
    - Each sub-task should have measurable completion criteria
    - Order sub-tasks by dependency requirements
    
    FORMAT YOUR RESPONSE AS:
    1. Sub-task 1: [Clear description]
       - Depends on: [dependencies or "None"]
       - Completion criteria: [how to know it's done]
    
    2. Sub-task 2: [Clear description]
       - Depends on: [dependencies]
       - Completion criteria: [how to know it's done]
    
    Continue for all necessary sub-tasks.
    """
    
    # This would be sent to LLM for decomposition
    return decomposition_prompt
```

### Context Management (MANDATORY)
```python
"""
Manage context efficiently for consistent LLM interactions.
"""
class ContextManager:
    """Manages context for consistent LLM interactions."""
    
    def __init__(self, max_context_length: int = 8000):
        """
        Initialize context manager.
        
        Args:
            max_context_length: Maximum context length in tokens
        """
        self.max_context_length = max_context_length
        self.context_history = []
        self.system_context = ""
    
    def add_system_context(self, context: str) -> None:
        """Add persistent system context."""
        self.system_context = context
    
    def add_interaction(self, prompt: str, response: str) -> None:
        """Add interaction to context history."""
        self.context_history.append({
            'prompt': prompt,
            'response': response,
            'timestamp': time.time()
        })
        
        # Manage context length
        self._trim_context_if_needed()
    
    def get_current_context(self) -> str:
        """Get current context for LLM interaction."""
        context_parts = []
        
        if self.system_context:
            context_parts.append(f"SYSTEM CONTEXT:\n{self.system_context}\n")
        
        if self.context_history:
            context_parts.append("RECENT INTERACTIONS:")
            for interaction in self.context_history[-5:]:  # Last 5 interactions
                context_parts.append(f"Q: {interaction['prompt']}")
                context_parts.append(f"A: {interaction['response'][:200]}...\n")
        
        return "\n".join(context_parts)
    
    def _trim_context_if_needed(self) -> None:
        """Trim context if it exceeds maximum length."""
        current_length = self._estimate_token_count(self.get_current_context())
        
        while current_length > self.max_context_length and self.context_history:
            self.context_history.pop(0)  # Remove oldest interaction
            current_length = self._estimate_token_count(self.get_current_context())
    
    def _estimate_token_count(self, text: str) -> int:
        """Rough estimation of token count."""
        return len(text.split()) * 1.3  # Approximate tokens per word
```

## Quality Assurance for Prompts

### Prompt Testing Framework (REQUIRED)
```python
"""
Test prompts for consistency and quality of results.
"""
import json
from typing import List, Dict, Any


class PromptTester:
    """Framework for testing prompt effectiveness."""
    
    def __init__(self, llm_client):
        """
        Initialize prompt tester.
        
        Args:
            llm_client: LLM client for testing prompts
        """
        self.llm_client = llm_client
        self.test_results = []
    
    def test_prompt_variations(self, base_prompt: str, variations: List[str], test_inputs: List[str]) -> Dict[str, Any]:
        """
        Test different prompt variations for consistency.
        
        Args:
            base_prompt: Base prompt template
            variations: List of prompt variations to test
            test_inputs: Test inputs to evaluate with each variation
            
        Returns:
            Test results comparing variation effectiveness
        """
        results = {
            'base_prompt': base_prompt,
            'variation_results': {},
            'consistency_scores': {},
            'quality_scores': {}
        }
        
        for i, variation in enumerate(variations):
            variation_name = f"variation_{i+1}"
            variation_results = []
            
            for test_input in test_inputs:
                prompt = variation.format(input=test_input)
                response = self.llm_client.generate_text(prompt)
                
                variation_results.append({
                    'input': test_input,
                    'prompt': prompt,
                    'response': response,
                    'quality_score': self._assess_response_quality(response),
                    'follows_format': self._check_format_compliance(response)
                })
            
            results['variation_results'][variation_name] = variation_results
            results['consistency_scores'][variation_name] = self._calculate_consistency(variation_results)
            results['quality_scores'][variation_name] = self._calculate_average_quality(variation_results)
        
        return results
    
    def _assess_response_quality(self, response: str) -> float:
        """Assess response quality on scale of 0-1."""
        quality_factors = {
            'length_appropriate': 0.2,
            'contains_code': 0.3,
            'has_documentation': 0.2,
            'follows_standards': 0.3
        }
        
        score = 0.0
        
        # Length check
        if 100 <= len(response) <= 2000:
            score += quality_factors['length_appropriate']
        
        # Code presence check
        if 'def ' in response or 'class ' in response:
            score += quality_factors['contains_code']
        
        # Documentation check
        if '"""' in response or "'''" in response:
            score += quality_factors['has_documentation']
        
        # Standards compliance check (basic)
        if 'typing' in response and 'Args:' in response:
            score += quality_factors['follows_standards']
        
        return score
    
    def _check_format_compliance(self, response: str) -> bool:
        """Check if response follows expected format."""
        # Basic format compliance checks
        has_proper_structure = any([
            'def ' in response,
            'class ' in response,
            'import ' in response
        ])
        
        has_documentation = '"""' in response or "'''" in response
        
        return has_proper_structure and has_documentation
```

### Prompt Optimization (MANDATORY)
```python
"""
Optimize prompts for better results through iterative improvement.
"""
class PromptOptimizer:
    """Optimize prompts based on performance metrics."""
    
    def __init__(self, llm_client):
        """
        Initialize prompt optimizer.
        
        Args:
            llm_client: LLM client for testing optimizations
        """
        self.llm_client = llm_client
        self.optimization_history = []
    
    def optimize_prompt(self, initial_prompt: str, test_cases: List[Dict], target_metrics: Dict) -> str:
        """
        Optimize prompt through iterative improvement.
        
        Args:
            initial_prompt: Starting prompt to optimize
            test_cases: Test cases with expected outputs
            target_metrics: Target performance metrics
            
        Returns:
            Optimized prompt that meets target metrics
        """
        current_prompt = initial_prompt
        best_prompt = initial_prompt
        best_score = 0.0
        
        optimization_strategies = [
            self._add_explicit_instructions,
            self._add_examples,
            self._refine_structure,
            self._add_constraints,
            self._improve_clarity
        ]
        
        for iteration in range(10):  # Max 10 optimization iterations
            for strategy in optimization_strategies:
                candidate_prompt = strategy(current_prompt)
                score = self._evaluate_prompt(candidate_prompt, test_cases, target_metrics)
                
                if score > best_score:
                    best_score = score
                    best_prompt = candidate_prompt
                    self.optimization_history.append({
                        'iteration': iteration,
                        'strategy': strategy.__name__,
                        'prompt': candidate_prompt,
                        'score': score
                    })
            
            current_prompt = best_prompt
            
            # Check if target metrics are met
            if self._meets_target_metrics(best_score, target_metrics):
                break
        
        return best_prompt
    
    def _add_explicit_instructions(self, prompt: str) -> str:
        """Add more explicit instructions to prompt."""
        explicit_additions = [
            "\nBe specific and detailed in your response.",
            "\nProvide complete, working code examples.",
            "\nInclude proper error handling and documentation.",
            "\nFollow Python best practices and PEP 8 standards."
        ]
        
        return prompt + "\n" + "\n".join(explicit_additions)
    
    def _add_examples(self, prompt: str) -> str:
        """Add examples to prompt for better guidance."""
        example_section = """
        
EXAMPLE FORMAT:
```python
def example_function(param: str) -> str:
    \"\"\"
    Example function with proper documentation.
    
    Args:
        param: Description of parameter
        
    Returns:
        Description of return value
    \"\"\"
    return f"Processed: {param}"
```
"""
        return prompt + example_section
```

## Agent Coordination Standards

### Multi-Agent Communication (REQUIRED)
```python
"""
Standards for communication between multiple agents.
"""
class AgentCoordinator:
    """Coordinates communication between multiple agents."""
    
    def __init__(self):
        """Initialize agent coordinator."""
        self.active_agents = {}
        self.communication_log = []
    
    def send_agent_message(self, sender_id: str, recipient_id: str, message: str, message_type: str) -> bool:
        """
        Send message between agents with standardized format.
        
        Args:
            sender_id: ID of sending agent
            recipient_id: ID of receiving agent
            message: Message content
            message_type: Type of message (task, status, result, error)
            
        Returns:
            True if message sent successfully
        """
        standardized_message = {
            'sender': sender_id,
            'recipient': recipient_id,
            'content': message,
            'type': message_type,
            'timestamp': time.time(),
            'format_version': '1.0'
        }
        
        # Validate message format
        if not self._validate_message_format(standardized_message):
            return False
        
        # Log communication
        self.communication_log.append(standardized_message)
        
        # Deliver message
        return self._deliver_message(standardized_message)
    
    def _validate_message_format(self, message: Dict[str, Any]) -> bool:
        """Validate message follows required format."""
        required_fields = ['sender', 'recipient', 'content', 'type', 'timestamp']
        return all(field in message for field in required_fields)
```

## Prompt Quality Validation Checklist (MANDATORY)

Before using any prompt:

- [ ] **Clear task description** with specific requirements
- [ ] **Appropriate standards referenced** for task type
- [ ] **Expected output format specified** clearly
- [ ] **Completion criteria defined** unambiguously
- [ ] **Error handling instructions** included
- [ ] **Quality requirements stated** explicitly
- [ ] **Context appropriately managed** for task complexity
- [ ] **Examples provided** for complex formats
- [ ] **Validation criteria included** for self-checking
- [ ] **Response format tested** with sample inputs

## Response Processing Standards

### Output Validation (REQUIRED)
```python
def validate_agent_response(response: str, task_type: str) -> bool:
    """
    Validate agent response meets quality standards.
    
    Args:
        response: Agent response to validate
        task_type: Type of task (coding, research, integration)
        
    Returns:
        True if response meets standards
    """
    # Universal validations
    if not response or len(response.strip()) < 10:
        return False
    
    # Task-specific validations
    if task_type == 'coding':
        return validate_coding_response(response)
    elif task_type == 'research':
        return validate_research_response(response)
    elif task_type == 'integration':
        return validate_integration_response(response)
    
    return True

def validate_coding_response(response: str) -> bool:
    """Validate coding task response."""
    required_elements = [
        'def ' in response or 'class ' in response,  # Has functions/classes
        '"""' in response or "'''" in response,      # Has docstrings
        'import ' in response,                       # Has imports
        'Task complete and ready for next step' in response  # Completion signal
    ]
    
    return all(required_elements)
```

**REMEMBER**: Consistent, high-quality prompting is essential for reliable agent performance. These standards ensure that all LLM interactions produce predictable, high-quality results that meet our architectural and quality requirements.