# RESEARCH STANDARDS

**MANDATORY**: All research and search operations MUST follow these standards for accuracy, efficiency, and validation.

## Search Methodology Requirements

### Pre-Search Planning (MANDATORY)
```python
# REQUIRED: Define search strategy before execution
def plan_search(research_goal: str) -> SearchStrategy:
    """
    Plan comprehensive search strategy.
    
    Args:
        research_goal: Clear description of what needs to be found
        
    Returns:
        SearchStrategy with tools, keywords, and validation criteria
    """
    return SearchStrategy(
        primary_tools=['Grep', 'Glob', 'WebSearch'],
        secondary_tools=['Task', 'WebFetch'],
        keywords=extract_keywords(research_goal),
        validation_criteria=define_success_criteria(research_goal)
    )
```

### Search Tool Selection (PRIORITY ORDER)

1. **Local Codebase Search (FIRST PRIORITY)**
   ```python
   # Use Grep for content-based searches
   grep_results = Grep(pattern="function_name", include="*.py")
   
   # Use Glob for file pattern searches  
   file_matches = Glob(pattern="**/*config*.py")
   
   # Use Read for specific file analysis
   content = Read(file_path="/path/to/specific/file.py")
   ```

2. **Multi-Round Search (WHEN NEEDED)**
   ```python
   # Use Task tool for complex, multi-step searches
   complex_search = Task(
       description="Find error handling patterns",
       prompt="Search codebase for exception handling patterns, "
              "analyze consistency, and document best practices"
   )
   ```

3. **Web Research (WHEN LOCAL FAILS)**
   ```python
   # Use WebSearch for current information
   web_results = WebSearch(query="latest API changes gemini 2024")
   
   # Use WebFetch for specific documentation
   docs = WebFetch(
       url="https://docs.example.com/api",
       prompt="Extract API rate limiting information"
   )
   ```

### Search Pattern Standards

#### Keyword Strategy (REQUIRED)
```python
# CORRECT: Use multiple related terms
search_terms = [
    "rate limit",      # Primary term
    "rate_limit",      # Snake case variant
    "ratelimit",       # Single word variant
    "quota",           # Related concept
    "throttle"         # Alternative term
]

# INCORRECT: Single term only
search_terms = ["rate limit"]  # Too narrow
```

#### Progressive Search Refinement
```python
# Step 1: Broad search
broad_results = Grep(pattern="config", include="*.py")

# Step 2: Analyze results and refine
if len(broad_results) > 50:
    # Too many results - narrow down
    refined_results = Grep(pattern="config.*api", include="*.py")
elif len(broad_results) < 5:
    # Too few results - broaden search
    expanded_results = Grep(pattern="(config|settings|env)", include="*.py")
```

## Validation Requirements

### Source Verification (MANDATORY)
```python
def validate_search_results(results: List[SearchResult]) -> ValidationReport:
    """
    Validate search results for accuracy and completeness.
    
    Args:
        results: List of search results to validate
        
    Returns:
        ValidationReport with confidence scores and issues
    """
    validation = ValidationReport()
    
    for result in results:
        # Check source credibility
        if not is_credible_source(result.source):
            validation.add_warning(f"Unverified source: {result.source}")
            
        # Check information freshness
        if is_outdated(result.timestamp):
            validation.add_warning(f"Outdated information: {result.timestamp}")
            
        # Cross-reference with other results
        if not cross_reference_confirms(result, results):
            validation.add_error(f"Contradictory information found")
    
    return validation
```

### Information Freshness Standards
```python
# REQUIRED: Check information age
def validate_information_age(source_date: datetime) -> bool:
    """Validate that information is current enough for use."""
    max_age_days = {
        'api_documentation': 90,    # 3 months for API docs
        'library_versions': 30,     # 1 month for library info
        'best_practices': 180,      # 6 months for practices
        'security_info': 7          # 1 week for security
    }
    
    age = (datetime.now() - source_date).days
    return age <= max_age_days.get('default', 30)
```

### Cross-Reference Validation
```python
# REQUIRED: Confirm findings across multiple sources
def cross_reference_validation(primary_finding: str, sources: List[str]) -> bool:
    """
    Validate findings across multiple independent sources.
    
    Args:
        primary_finding: Main information to validate
        sources: List of sources to check against
        
    Returns:
        True if finding is confirmed by multiple sources
    """
    confirmations = 0
    
    for source in sources:
        if confirms_finding(source, primary_finding):
            confirmations += 1
    
    # Require at least 2 independent confirmations
    return confirmations >= 2
```

## Documentation Standards

### Research Documentation Format (MANDATORY)
```markdown
# Research Report: [Topic]

## Objective
Clear statement of what was being researched and why.

## Search Strategy
- **Tools Used**: List of search tools and rationale
- **Keywords**: Primary and secondary search terms
- **Scope**: Areas searched (local codebase, web, documentation)

## Findings
### Primary Results
- **Source**: [File path or URL]
- **Content**: [Relevant information found]
- **Confidence**: [High/Medium/Low]
- **Validation**: [How this was verified]

### Secondary Results
[Additional supporting information]

## Validation
- **Cross-References**: Sources that confirm findings
- **Conflicting Information**: Any contradictions found
- **Knowledge Gaps**: Areas requiring further research

## Recommendations
Based on research findings, specific actionable recommendations.

## Follow-Up Actions
Next steps for implementation or additional research needed.
```

### Evidence Documentation (REQUIRED)
```python
# REQUIRED: Document all evidence with sources
class ResearchEvidence:
    def __init__(self):
        self.findings = []
        self.sources = []
        self.validation_status = {}
    
    def add_finding(self, content: str, source: str, confidence: str):
        """Add research finding with source attribution."""
        finding = {
            'content': content,
            'source': source,
            'confidence': confidence,
            'timestamp': datetime.now(),
            'validation_status': 'pending'
        }
        self.findings.append(finding)
        
    def validate_finding(self, finding_id: int, validation_result: bool):
        """Record validation result for specific finding."""
        self.validation_status[finding_id] = validation_result
```

## Quality Assurance Standards

### Research Depth Requirements
```python
# REQUIRED: Comprehensive search coverage
def ensure_comprehensive_coverage(research_topic: str) -> CoverageReport:
    """
    Ensure research covers all relevant aspects of topic.
    
    Returns:
        CoverageReport indicating completeness
    """
    required_aspects = {
        'implementation': 'How to implement the solution',
        'best_practices': 'Industry standard approaches',
        'limitations': 'Known constraints and issues',
        'alternatives': 'Alternative approaches available',
        'examples': 'Working code examples',
        'documentation': 'Official documentation references'
    }
    
    coverage = CoverageReport()
    for aspect, description in required_aspects.items():
        if not research_covers_aspect(research_topic, aspect):
            coverage.add_gap(aspect, description)
    
    return coverage
```

### Accuracy Verification (MANDATORY)
```python
# REQUIRED: Verify all technical information
def verify_technical_accuracy(code_example: str, context: str) -> bool:
    """
    Verify that code examples and technical information are accurate.
    
    Args:
        code_example: Code snippet to verify
        context: Context in which code will be used
        
    Returns:
        True if code is syntactically correct and contextually appropriate
    """
    # Syntax validation
    if not is_syntactically_valid(code_example):
        return False
    
    # Context appropriateness
    if not fits_architecture(code_example, context):
        return False
        
    # Security validation
    if has_security_issues(code_example):
        return False
    
    return True
```

## Research Tool Usage Patterns

### Grep Usage Standards
```python
# CORRECT: Specific, targeted searches
Grep(pattern="class.*Config", include="*.py")  # Find config classes
Grep(pattern="def test_.*error", include="test_*.py")  # Find error tests

# INCORRECT: Overly broad searches
Grep(pattern=".*", include="*.*")  # Too broad, unhelpful
```

### Glob Usage Standards
```python
# CORRECT: Structured file searches
Glob(pattern="**/config/*.py")  # Config files
Glob(pattern="tests/**/test_*.py")  # Test files
Glob(pattern="adapters/*/exceptions.py")  # Exception handlers

# INCORRECT: Vague patterns
Glob(pattern="*.py")  # Too many results
```

### Task Tool Usage for Research
```python
# CORRECT: Complex, multi-step research tasks
Task(
    description="Analyze error handling patterns",
    prompt="""
    Research and analyze error handling patterns in the codebase:
    1. Find all exception classes and their hierarchy
    2. Identify common error handling patterns
    3. Document best practices found
    4. Suggest improvements for consistency
    
    Provide comprehensive analysis with code examples.
    """
)

# INCORRECT: Simple searches better done with Grep/Glob
Task(
    description="Find config files",
    prompt="Find all configuration files"  # Use Glob instead
)
```

## Information Synthesis Standards

### Synthesis Requirements (MANDATORY)
```python
def synthesize_research_findings(findings: List[ResearchFinding]) -> Synthesis:
    """
    Synthesize multiple research findings into coherent recommendations.
    
    Args:
        findings: List of validated research findings
        
    Returns:
        Synthesis with consolidated recommendations
    """
    synthesis = Synthesis()
    
    # Group related findings
    grouped_findings = group_by_topic(findings)
    
    # Identify patterns and commonalities
    patterns = identify_patterns(grouped_findings)
    
    # Resolve conflicts
    conflicts = identify_conflicts(grouped_findings)
    resolved_conflicts = resolve_conflicts(conflicts)
    
    # Generate recommendations
    recommendations = generate_recommendations(patterns, resolved_conflicts)
    
    synthesis.add_patterns(patterns)
    synthesis.add_recommendations(recommendations)
    synthesis.add_confidence_score(calculate_confidence(findings))
    
    return synthesis
```

### Conflict Resolution (REQUIRED)
```python
def resolve_information_conflicts(conflicting_sources: List[Source]) -> Resolution:
    """
    Resolve conflicts between different information sources.
    
    Args:
        conflicting_sources: Sources with contradictory information
        
    Returns:
        Resolution with preferred approach and rationale
    """
    resolution = Resolution()
    
    # Evaluate source credibility
    credibility_scores = [evaluate_credibility(source) for source in conflicting_sources]
    
    # Consider information freshness
    freshness_scores = [evaluate_freshness(source) for source in conflicting_sources]
    
    # Check for context appropriateness
    context_scores = [evaluate_context_fit(source) for source in conflicting_sources]
    
    # Calculate overall scores
    overall_scores = combine_scores(credibility_scores, freshness_scores, context_scores)
    
    # Select best source
    best_source_index = overall_scores.index(max(overall_scores))
    resolution.preferred_source = conflicting_sources[best_source_index]
    resolution.rationale = generate_rationale(overall_scores)
    
    return resolution
```

## Research Validation Checklist (MANDATORY)

Before using any research findings:

- [ ] **Multiple sources consulted** for each major finding
- [ ] **Information freshness validated** against age requirements
- [ ] **Source credibility assessed** for all references
- [ ] **Technical accuracy verified** for all code examples
- [ ] **Cross-references confirmed** findings across sources
- [ ] **Conflicts identified and resolved** with clear rationale
- [ ] **Coverage gaps documented** for incomplete areas
- [ ] **Recommendations synthesized** from validated findings
- [ ] **Evidence documented** with proper attribution
- [ ] **Follow-up actions identified** for implementation

## Research Quality Gates

### Minimum Standards (NON-NEGOTIABLE)
- **3+ independent sources** for critical findings
- **Technical validation** for all code examples
- **Documentation of uncertainty** where information is incomplete
- **Clear attribution** for all sources and findings
- **Synthesis quality** that provides actionable insights

### Rejection Criteria
- Single-source findings for critical decisions
- Unvalidated technical information
- Outdated security or API information
- Conflicting information without resolution
- Incomplete coverage of research objectives

**REMEMBER**: Quality research is the foundation of good implementation. These standards ensure that all development work is based on accurate, current, and comprehensive information.