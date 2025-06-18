"""
Mode Manager

Manages reasoning mode selection and optimization based on prompt analysis
and historical performance data.
"""

import logging
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from shared.models.reasoning_models import (
    ReasoningMode,
    ComplexityAnalysis,
    ConfidenceLevel
)


@dataclass
class ModeRule:
    """Represents a rule for mode selection."""
    name: str
    pattern: str
    mode: ReasoningMode
    weight: float
    description: str


class ModeManager:
    """
    Manages reasoning mode selection and optimization.
    
    This manager analyzes prompts and determines the most appropriate
    reasoning mode based on content patterns and complexity indicators.
    """
    
    def __init__(self):
        """Initialize the mode manager with default rules."""
        self.logger = logging.getLogger(__name__)
        self.mode_rules = self._initialize_mode_rules()
        self.performance_history: Dict[str, List[float]] = {}
        
    def _initialize_mode_rules(self) -> List[ModeRule]:
        """Initialize default mode selection rules."""
        return [
            # Rapid mode indicators
            ModeRule(
                name="simple_question",
                pattern=r"\b(what is|who is|when is|where is)\b",
                mode=ReasoningMode.RAPID,
                weight=0.8,
                description="Simple factual questions"
            ),
            ModeRule(
                name="definition_request",
                pattern=r"\b(define|definition of|meaning of)\b",
                mode=ReasoningMode.RAPID,
                weight=0.7,
                description="Definition requests"
            ),
            ModeRule(
                name="quick_calculation",
                pattern=r"\b\d+\s*[\+\-\*\/]\s*\d+\b",
                mode=ReasoningMode.RAPID,
                weight=0.9,
                description="Simple calculations"
            ),
            
            # Thoughtful mode indicators
            ModeRule(
                name="complex_analysis",
                pattern=r"\b(analyze|analysis|compare|contrast|evaluate)\b",
                mode=ReasoningMode.THOUGHTFUL,
                weight=0.8,
                description="Analysis and evaluation tasks"
            ),
            ModeRule(
                name="reasoning_required",
                pattern=r"\b(why|how|explain|reason|because|therefore)\b",
                mode=ReasoningMode.THOUGHTFUL,
                weight=0.7,
                description="Reasoning and explanation requests"
            ),
            ModeRule(
                name="decision_making",
                pattern=r"\b(decide|choose|select|recommend|suggest)\b",
                mode=ReasoningMode.THOUGHTFUL,
                weight=0.8,
                description="Decision making tasks"
            ),
            
            # Chain of thought indicators
            ModeRule(
                name="step_by_step_request",
                pattern=r"\b(step by step|step-by-step|walk me through|show steps)\b",
                mode=ReasoningMode.CHAIN_OF_THOUGHT,
                weight=0.9,
                description="Explicit step-by-step requests"
            ),
            ModeRule(
                name="problem_solving",
                pattern=r"\b(solve|solution|problem|algorithm|method)\b",
                mode=ReasoningMode.CHAIN_OF_THOUGHT,
                weight=0.7,
                description="Problem solving tasks"
            ),
            
            # Step by step indicators
            ModeRule(
                name="detailed_breakdown",
                pattern=r"\b(detailed|comprehensive|thorough|in depth)\b",
                mode=ReasoningMode.STEP_BY_STEP,
                weight=0.8,
                description="Requests for detailed analysis"
            ),
            ModeRule(
                name="complex_problem",
                pattern=r"\b(complex|complicated|difficult|challenging)\b",
                mode=ReasoningMode.STEP_BY_STEP,
                weight=0.6,
                description="Complex problem indicators"
            )
        ]
    
    def determine_optimal_mode(
        self, 
        prompt: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> ReasoningMode:
        """
        Determine the optimal reasoning mode for a given prompt.
        
        Args:
            prompt: The input prompt to analyze
            context: Optional context information
            
        Returns:
            ReasoningMode: The recommended reasoning mode
        """
        prompt_lower = prompt.lower()
        mode_scores: Dict[ReasoningMode, float] = {
            ReasoningMode.RAPID: 0.0,
            ReasoningMode.THOUGHTFUL: 0.0,
            ReasoningMode.CHAIN_OF_THOUGHT: 0.0,
            ReasoningMode.STEP_BY_STEP: 0.0
        }
        
        # Apply rules to calculate scores
        for rule in self.mode_rules:
            if re.search(rule.pattern, prompt_lower, re.IGNORECASE):
                mode_scores[rule.mode] += rule.weight
                self.logger.debug(f"Rule '{rule.name}' matched, +{rule.weight} to {rule.mode.value}")
        
        # Factor in prompt length (longer prompts tend to need more reasoning)
        prompt_length_factor = min(len(prompt) / 1000, 1.0)  # Normalize to 0-1
        mode_scores[ReasoningMode.THOUGHTFUL] += prompt_length_factor * 0.3
        mode_scores[ReasoningMode.STEP_BY_STEP] += prompt_length_factor * 0.2
        
        # Factor in complexity indicators
        complexity_score = self._calculate_complexity_score(prompt)
        if complexity_score > 0.7:
            mode_scores[ReasoningMode.STEP_BY_STEP] += 0.4
        elif complexity_score > 0.5:
            mode_scores[ReasoningMode.THOUGHTFUL] += 0.3
        else:
            mode_scores[ReasoningMode.RAPID] += 0.2
        
        # Use historical performance if available
        if context and 'user_id' in context:
            self._apply_performance_history(mode_scores, context['user_id'])
        
        # Find mode with highest score
        optimal_mode = max(mode_scores, key=mode_scores.get)
        
        self.logger.info(
            f"Mode selection scores: {mode_scores}, "
            f"selected: {optimal_mode.value}"
        )
        
        return optimal_mode
    
    def _calculate_complexity_score(self, prompt: str) -> float:
        """
        Calculate a complexity score for the prompt.
        
        Args:
            prompt: The input prompt
            
        Returns:
            float: Complexity score between 0 and 1
        """
        score = 0.0
        
        # Length factor
        length_score = min(len(prompt) / 1000, 0.3)
        score += length_score
        
        # Question complexity
        question_words = len(re.findall(r'\b(what|why|how|when|where|which|who)\b', prompt.lower()))
        score += min(question_words * 0.1, 0.2)
        
        # Technical terms
        technical_patterns = [
            r'\b(algorithm|implementation|architecture|system|database)\b',
            r'\b(analysis|synthesis|evaluation|optimization)\b',
            r'\b(complex|complicated|sophisticated|advanced)\b'
        ]
        
        for pattern in technical_patterns:
            if re.search(pattern, prompt.lower()):
                score += 0.15
        
        # Mathematical content
        if re.search(r'[\+\-\*\/\=\(\)\[\]]', prompt) or re.search(r'\b\d+\b', prompt):
            score += 0.1
        
        # Conditional logic
        if re.search(r'\b(if|then|else|when|unless|provided|given)\b', prompt.lower()):
            score += 0.1
        
        return min(score, 1.0)
    
    def _apply_performance_history(
        self, 
        mode_scores: Dict[ReasoningMode, float], 
        user_id: str
    ) -> None:
        """Apply historical performance data to mode selection."""
        
        if user_id not in self.performance_history:
            return
        
        history = self.performance_history[user_id]
        if not history:
            return
        
        # Boost modes that have performed well historically
        avg_performance = sum(history) / len(history)
        if avg_performance > 0.8:
            # User prefers detailed reasoning
            mode_scores[ReasoningMode.THOUGHTFUL] += 0.2
            mode_scores[ReasoningMode.STEP_BY_STEP] += 0.1
        elif avg_performance < 0.5:
            # User prefers quick responses
            mode_scores[ReasoningMode.RAPID] += 0.3
    
    def record_performance(
        self, 
        user_id: str, 
        mode: ReasoningMode, 
        satisfaction_score: float
    ) -> None:
        """
        Record performance data for future mode selection.
        
        Args:
            user_id: User identifier
            mode: Mode that was used
            satisfaction_score: User satisfaction score (0-1)
        """
        if user_id not in self.performance_history:
            self.performance_history[user_id] = []
        
        self.performance_history[user_id].append(satisfaction_score)
        
        # Keep only recent history (last 20 interactions)
        if len(self.performance_history[user_id]) > 20:
            self.performance_history[user_id] = self.performance_history[user_id][-20:]
    
    def get_mode_statistics(self) -> Dict[str, Any]:
        """Get statistics about mode usage and performance."""
        
        total_users = len(self.performance_history)
        avg_satisfaction = 0.0
        
        if total_users > 0:
            all_scores = []
            for user_scores in self.performance_history.values():
                all_scores.extend(user_scores)
            
            if all_scores:
                avg_satisfaction = sum(all_scores) / len(all_scores)
        
        return {
            'total_users': total_users,
            'average_satisfaction': avg_satisfaction,
            'rule_count': len(self.mode_rules),
            'supported_modes': [mode.value for mode in ReasoningMode]
        }
    
    def add_custom_rule(self, rule: ModeRule) -> None:
        """Add a custom mode selection rule."""
        self.mode_rules.append(rule)
        self.logger.info(f"Added custom rule: {rule.name}")
    
    def remove_rule(self, rule_name: str) -> bool:
        """Remove a mode selection rule by name."""
        for i, rule in enumerate(self.mode_rules):
            if rule.name == rule_name:
                self.mode_rules.pop(i)
                self.logger.info(f"Removed rule: {rule_name}")
                return True
        return False