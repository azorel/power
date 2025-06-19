"""
Decision Engine: Multi-provider LLM integration for conscious reasoning.

This module integrates the cognitive loop with our existing multi-provider
LLM system (OpenAI, Gemini, Claude, Perplexity) for sophisticated reasoning
and decision-making capabilities.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from shared.interfaces.llm_provider import LLMProvider
from shared.models.llm_request import LLMRequest
from shared.exceptions import LLMProviderError

logger = logging.getLogger(__name__)


class ReasoningMode(Enum):
    """Different modes of reasoning for different situations."""
    FAST_DECISION = "fast_decision"        # Quick decisions with GPT-4.1
    DEEP_ANALYSIS = "deep_analysis"        # Complex analysis with Claude 4
    MULTIMODAL = "multimodal"              # Image/data analysis with Gemini 2.5
    RESEARCH = "research"                  # Knowledge synthesis with Perplexity
    CONSENSUS = "consensus"                # Multi-provider consensus


@dataclass
class ReasoningContext:
    """Context for reasoning operations."""
    situation_type: str
    urgency_level: int  # 1-10
    complexity_score: int  # 1-10
    available_data: Dict[str, Any]
    constraints: List[str]
    success_criteria: List[str]


@dataclass
class DecisionResult:
    """Result from decision-making process."""
    decision: str
    confidence: float
    reasoning_chain: List[str]
    provider_used: str
    alternative_options: List[str]
    resource_requirements: Dict[str, Any]
    execution_plan: List[str]


class DecisionEngine:
    """
    Advanced decision engine using multi-provider LLM reasoning.

    Integrates with the existing Power Builder LLM infrastructure to provide
    sophisticated reasoning capabilities for the cognitive loop.
    """

    def __init__(self):
        """Initialize the Decision Engine."""
        self.provider_registry: Dict[str, LLMProvider] = {}
        self.provider_performance: Dict[str, Dict[str, float]] = {}
        self.reasoning_templates: Dict[str, str] = {}
        self._initialize_reasoning_templates()

    def register_provider(self, name: str, provider: LLMProvider) -> None:
        """
        Register an LLM provider for decision making.

        Args:
            name: Provider name (openai, gemini, claude, perplexity)
            provider: LLM provider instance
        """
        self.provider_registry[name] = provider
        self.provider_performance[name] = {
            "accuracy": 0.8,
            "speed": 0.7,
            "consistency": 0.8,
            "total_calls": 0,
            "successful_calls": 0
        }
        logger.info("Registered LLM provider: %s", name)

    async def make_decision(self, context: ReasoningContext,
                          preferred_mode: Optional[ReasoningMode] = None) -> DecisionResult:
        """
        Make a decision based on the provided context.

        Args:
            context: Reasoning context with situation details
            preferred_mode: Preferred reasoning mode (auto-selected if None)

        Returns:
            DecisionResult with the decision and reasoning
        """
        # Auto-select reasoning mode if not specified
        reasoning_mode = preferred_mode or self._select_reasoning_mode(context)

        # Choose the best provider for this reasoning mode
        provider_name = self._select_provider(reasoning_mode, context)

        if provider_name not in self.provider_registry:
            logger.error("Provider %s not available", provider_name)
            return self._fallback_decision(context)

        try:
            # Generate the reasoning prompt
            prompt = self._build_reasoning_prompt(context, reasoning_mode)

            # Make the LLM call
            provider = self.provider_registry[provider_name]
            request = LLMRequest(
                prompt=prompt,
                model=self._get_optimal_model(provider_name, reasoning_mode),
                max_tokens=2048,
                temperature=0.3  # Lower temperature for more consistent reasoning
            )

            response = await provider.generate_response(request)

            # Parse the response into a structured decision
            decision_result = self._parse_decision_response(
                response.content, provider_name, reasoning_mode
            )

            # Update provider performance
            self._update_provider_performance(provider_name, True)

            logger.info("Decision made using %s: %s", provider_name, decision_result.decision)
            return decision_result

        except LLMProviderError as e:
            logger.error("LLM provider error: %s", e)
            self._update_provider_performance(provider_name, False)
            return await self._try_fallback_provider(context, reasoning_mode, provider_name)

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Unexpected error in decision making: %s", e)
            return self._fallback_decision(context)

    async def get_consensus_decision(self, context: ReasoningContext) -> DecisionResult:
        """
        Get consensus decision from multiple providers.

        Args:
            context: Reasoning context

        Returns:
            Consensus decision result
        """
        decisions = []
        providers_used = []

        # Get decisions from multiple providers
        for provider_name in ["openai", "claude", "gemini"]:
            if provider_name in self.provider_registry:
                try:
                    provider_decision = await self.make_decision(
                        context, ReasoningMode.FAST_DECISION
                    )
                    decisions.append(provider_decision)
                    providers_used.append(provider_name)
                except Exception as e:  # pylint: disable=broad-exception-caught
                    logger.warning("Provider %s failed in consensus: %s", provider_name, e)

        if not decisions:
            return self._fallback_decision(context)

        # Analyze consensus
        consensus_result = self._analyze_consensus(decisions, providers_used)
        return consensus_result

    def _select_reasoning_mode(self, context: ReasoningContext) -> ReasoningMode:
        """Select the optimal reasoning mode based on context."""
        # High urgency -> fast decision
        if context.urgency_level >= 8:
            return ReasoningMode.FAST_DECISION

        # Complex problem -> deep analysis
        if context.complexity_score >= 8:
            return ReasoningMode.DEEP_ANALYSIS

        # Research needed -> use Perplexity
        if "research" in context.situation_type.lower():
            return ReasoningMode.RESEARCH

        # Multimodal data present -> use Gemini
        if any(key in context.available_data for key in ["image", "chart", "diagram"]):
            return ReasoningMode.MULTIMODAL

        # Default to fast decision
        return ReasoningMode.FAST_DECISION

    def _select_provider(self, mode: ReasoningMode, context: ReasoningContext = None) -> str:
        """Select the best provider for the reasoning mode."""
        _ = context  # Context reserved for future provider selection logic
        provider_mapping = {
            ReasoningMode.FAST_DECISION: "openai",    # GPT-4.1 for speed
            ReasoningMode.DEEP_ANALYSIS: "claude",    # Claude 4 for reasoning
            ReasoningMode.MULTIMODAL: "gemini",       # Gemini 2.5 for multimodal
            ReasoningMode.RESEARCH: "perplexity",     # Perplexity for research
            ReasoningMode.CONSENSUS: "openai"         # Default for consensus
        }

        preferred = provider_mapping.get(mode, "openai")

        # Check if preferred provider is available and performing well
        if (preferred in self.provider_registry and
            self.provider_performance[preferred]["accuracy"] > 0.7):
            return preferred

        # Fallback to best available provider
        available_providers = [
            name for name in self.provider_registry
            if self.provider_performance[name]["accuracy"] > 0.6
        ]

        if available_providers:
            # Return the one with highest accuracy
            best_provider = max(
                available_providers,
                key=lambda p: self.provider_performance[p]["accuracy"]
            )
            return best_provider

        # Last resort - return any available provider
        return next(iter(self.provider_registry.keys()), "openai")

    def _get_optimal_model(self, provider_name: str, mode: ReasoningMode) -> str:
        """Get the optimal model for the provider and reasoning mode."""
        model_mapping = {
            "openai": {
                ReasoningMode.FAST_DECISION: "gpt-4.1-preview",
                ReasoningMode.DEEP_ANALYSIS: "gpt-4.1-preview",
                ReasoningMode.RESEARCH: "gpt-4.1-preview"
            },
            "claude": {
                ReasoningMode.FAST_DECISION: "claude-4-haiku",
                ReasoningMode.DEEP_ANALYSIS: "claude-4-sonnet",
                ReasoningMode.RESEARCH: "claude-4-opus"
            },
            "gemini": {
                ReasoningMode.FAST_DECISION: "gemini-2.5-flash",
                ReasoningMode.MULTIMODAL: "gemini-2.5-pro",
                ReasoningMode.DEEP_ANALYSIS: "gemini-2.5-pro"
            },
            "perplexity": {
                ReasoningMode.RESEARCH: "sonar-huge-32k-online",
                ReasoningMode.FAST_DECISION: "sonar-large-32k-online"
            }
        }

        provider_models = model_mapping.get(provider_name, {})
        return provider_models.get(mode, "default")

    def _build_reasoning_prompt(self, context: ReasoningContext, mode: ReasoningMode) -> str:
        """Build the reasoning prompt for the LLM."""
        template = self.reasoning_templates.get(mode.value,
                                               self.reasoning_templates["default"])

        situation_summary = f"""
        SITUATION: {context.situation_type}
        URGENCY: {context.urgency_level}/10
        COMPLEXITY: {context.complexity_score}/10

        AVAILABLE DATA:
        {json.dumps(context.available_data, indent=2)}

        CONSTRAINTS:
        {chr(10).join(f"- {constraint}" for constraint in context.constraints)}

        SUCCESS CRITERIA:
        {chr(10).join(f"- {criterion}" for criterion in context.success_criteria)}
        """

        return template.format(situation=situation_summary)

    def _parse_decision_response(self, response_content: str, provider_name: str,
                                mode: ReasoningMode = None) -> DecisionResult:
        """Parse the LLM response into a structured decision."""
        _ = mode  # Mode reserved for future parsing customization
        try:
            # Try to parse as JSON first
            if response_content.strip().startswith("{"):
                parsed = json.loads(response_content)
                return DecisionResult(
                    decision=parsed.get("decision", "No decision provided"),
                    confidence=parsed.get("confidence", 0.5),
                    reasoning_chain=parsed.get("reasoning_chain", []),
                    provider_used=provider_name,
                    alternative_options=parsed.get("alternatives", []),
                    resource_requirements=parsed.get("resources", {}),
                    execution_plan=parsed.get("execution_plan", [])
                )
        except json.JSONDecodeError:
            pass

        # Fallback to text parsing
        lines = response_content.split('\n')
        decision = lines[0] if lines else "Continue current action"

        # Extract reasoning (simple heuristic)
        reasoning_lines = [line.strip() for line in lines[1:] if line.strip()]
        reasoning_chain = reasoning_lines[:5]  # Limit to 5 reasoning steps

        return DecisionResult(
            decision=decision,
            confidence=0.7,  # Default confidence for text parsing
            reasoning_chain=reasoning_chain,
            provider_used=provider_name,
            alternative_options=[],
            resource_requirements={},
            execution_plan=[]
        )

    def _analyze_consensus(self, decisions: List[DecisionResult],
                          providers: List[str]) -> DecisionResult:
        """Analyze multiple decisions to find consensus."""
        if not decisions:
            return self._fallback_decision(ReasoningContext(
                situation_type="consensus_failure",
                urgency_level=5,
                complexity_score=5,
                available_data={},
                constraints=[],
                success_criteria=[]
            ))

        # Simple consensus: most common decision
        decision_counts = {}
        for decision_result in decisions:
            decision = decision_result.decision
            if decision in decision_counts:
                decision_counts[decision] += 1
            else:
                decision_counts[decision] = 1

        # Get the most common decision
        consensus_decision = max(decision_counts.keys(), key=lambda k: decision_counts[k])

        # Average confidence of decisions that match consensus
        consensus_decisions = [d for d in decisions if d.decision == consensus_decision]
        avg_confidence = sum(d.confidence for d in consensus_decisions) / len(consensus_decisions)

        # Combine reasoning chains
        combined_reasoning = []
        for i, decision_result in enumerate(consensus_decisions):
            provider_name = providers[i] if i < len(providers) else f"Provider_{i}"
            reasoning_text = (decision_result.reasoning_chain[0]
                            if decision_result.reasoning_chain
                            else 'No reasoning provided')
            combined_reasoning.append(f"Provider {provider_name}: {reasoning_text}")

        return DecisionResult(
            decision=consensus_decision,
            confidence=avg_confidence,
            reasoning_chain=combined_reasoning,
            provider_used=f"consensus_{len(consensus_decisions)}_{len(decisions)}",
            alternative_options=list(set(d.decision for d in decisions
                                       if d.decision != consensus_decision)),
            resource_requirements={},
            execution_plan=[]
        )

    async def _try_fallback_provider(self, context: ReasoningContext,
                                   mode: ReasoningMode, failed_provider: str) -> DecisionResult:
        """Try a fallback provider when the primary fails."""
        fallback_providers = [name for name in self.provider_registry
                             if name != failed_provider]

        for fallback in fallback_providers:
            try:
                provider = self.provider_registry[fallback]
                prompt = self._build_reasoning_prompt(context, mode)

                request = LLMRequest(
                    prompt=prompt,
                    model=self._get_optimal_model(fallback, mode),
                    max_tokens=1024,
                    temperature=0.3
                )

                response = await provider.generate_response(request)
                decision_result = self._parse_decision_response(
                    response.content, fallback, mode
                )

                logger.info("Fallback successful with provider: %s", fallback)
                return decision_result

            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.warning("Fallback provider %s also failed: %s", fallback, e)
                continue

        # All providers failed
        return self._fallback_decision(context)

    def _fallback_decision(self, context: ReasoningContext) -> DecisionResult:
        """Provide a fallback decision when all LLM providers fail."""
        # Simple rule-based fallback
        if context.urgency_level >= 8:
            decision = "Take immediate action based on best available information"
        elif context.complexity_score <= 3:
            decision = "Proceed with standard approach"
        else:
            decision = "Gather more information before deciding"

        return DecisionResult(
            decision=decision,
            confidence=0.5,
            reasoning_chain=["All LLM providers unavailable", "Using rule-based fallback"],
            provider_used="fallback_rules",
            alternative_options=["wait_for_provider", "manual_intervention"],
            resource_requirements={},
            execution_plan=["Execute fallback decision"]
        )

    def _update_provider_performance(self, provider_name: str, success: bool) -> None:
        """Update provider performance statistics."""
        if provider_name in self.provider_performance:
            stats = self.provider_performance[provider_name]
            stats["total_calls"] += 1
            if success:
                stats["successful_calls"] += 1

            # Update success rate
            stats["accuracy"] = stats["successful_calls"] / stats["total_calls"]

    def _initialize_reasoning_templates(self) -> None:
        """Initialize reasoning prompt templates."""
        self.reasoning_templates = {
            "fast_decision": """
            You are an AI decision-making system. Analyze the situation and provide a quick, actionable decision.

            {situation}

            Respond with a clear decision and brief reasoning. Focus on speed and practicality.

            Format your response as:
            DECISION: [Your decision]
            REASONING: [Brief reasoning]
            CONFIDENCE: [0.0-1.0]
            """,

            "deep_analysis": """
            You are an AI reasoning system specializing in complex analysis. Carefully analyze the situation from multiple angles.

            {situation}

            Provide a thorough analysis with:
            1. Multiple perspectives on the situation
            2. Potential consequences of different actions
            3. Risk assessment
            4. Recommended decision with detailed justification

            Format as JSON:
            {{
                "decision": "your decision",
                "confidence": 0.0-1.0,
                "reasoning_chain": ["step 1", "step 2", ...],
                "alternatives": ["option 1", "option 2"],
                "risk_assessment": "risk analysis"
            }}
            """,

            "research": """
            You are an AI research specialist. Analyze the situation and determine what information is needed.

            {situation}

            Focus on:
            1. What information is missing
            2. Best sources for gathering information
            3. Research strategy
            4. Decision framework based on research findings
            """,

            "multimodal": """
            You are an AI system with multimodal analysis capabilities. Analyze all available data including any visual/structured information.

            {situation}

            Consider:
            1. All data types present (text, visual, structured)
            2. Patterns and insights from multimodal analysis
            3. Integrated decision based on comprehensive analysis
            """,

            "default": """
            Analyze the following situation and provide a decision with reasoning:

            {situation}

            Provide:
            - Clear decision
            - Reasoning steps
            - Confidence level
            - Alternative options if applicable
            """
        }
