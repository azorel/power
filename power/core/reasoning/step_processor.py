"""
Step Processor

Processes and manages individual reasoning steps, providing utilities for
step validation, enhancement, and analysis.
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from shared.models.reasoning_models import (
    ReasoningStep,
    StepType,
    ConfidenceLevel,
    ThinkingChain
)


class StepProcessor:
    """
    Processes and manages reasoning steps in thinking chains.
    
    This processor validates steps, enhances them with additional metadata,
    and provides utilities for step analysis and optimization.
    """
    
    def __init__(self):
        """Initialize the step processor."""
        self.logger = logging.getLogger(__name__)
        self.step_patterns = self._initialize_step_patterns()
        self.confidence_indicators = self._initialize_confidence_indicators()
        
    def _initialize_step_patterns(self) -> Dict[StepType, List[str]]:
        """Initialize patterns for step type detection."""
        return {
            StepType.ANALYSIS: [
                r'\b(analyz|examin|investigat|study|review)\w*\b',
                r'\b(break\s+down|decompos|dissect)\b',
                r'\b(consider|look\s+at|observe)\b'
            ],
            StepType.INFERENCE: [
                r'\b(infer|deduce|conclude|derive)\w*\b',
                r'\b(therefore|thus|hence|consequently)\b',
                r'\b(this\s+means|this\s+suggests|this\s+implies)\b'
            ],
            StepType.SYNTHESIS: [
                r'\b(combin|integrat|merge|synthesiz)\w*\b',
                r'\b(put\s+together|bring\s+together)\b',
                r'\b(overall|in\s+summary|taking\s+everything)\b'
            ],
            StepType.EVALUATION: [
                r'\b(evaluat|assess|judg|weigh|measur)\w*\b',
                r'\b(compare|contrast|versus|better|worse)\b',
                r'\b(pros\s+and\s+cons|advantages|disadvantages)\b'
            ],
            StepType.CONCLUSION: [
                r'\b(conclud|final|result|answer|solution)\w*\b',
                r'\b(in\s+conclusion|to\s+summarize|ultimately)\b',
                r'\b(decision|recommendation|verdict)\b'
            ]
        }
    
    def _initialize_confidence_indicators(self) -> Dict[ConfidenceLevel, List[str]]:
        """Initialize patterns for confidence level detection."""
        return {
            ConfidenceLevel.LOW: [
                r'\b(uncertain|unsure|doubtful|maybe|perhaps)\b',
                r'\b(might|could|possibly|potentially)\b',
                r'\b(I\s+think|I\s+believe|seems\s+like)\b'
            ],
            ConfidenceLevel.MEDIUM: [
                r'\b(likely|probably|appears|suggests)\b',
                r'\b(reasonable|plausible|feasible)\b',
                r'\b(should|would|expected)\b'
            ],
            ConfidenceLevel.HIGH: [
                r'\b(certain|sure|confident|definite)\b',
                r'\b(clearly|obviously|evidently|undoubtedly)\b',
                r'\b(will|must|definitely|absolutely)\b'
            ],
            ConfidenceLevel.VERY_HIGH: [
                r'\b(guarantee|promise|assure|prove)\w*\b',
                r'\b(without\s+doubt|beyond\s+question)\b',
                r'\b(fact|truth|reality|certainty)\b'
            ]
        }
    
    def process_step(self, step: ReasoningStep) -> ReasoningStep:
        """
        Process and enhance a reasoning step with additional metadata.
        
        Args:
            step: The reasoning step to process
            
        Returns:
            ReasoningStep: The enhanced step
        """
        # Auto-detect step type if not set or generic
        if step.step_type == StepType.ANALYSIS:
            detected_type = self._detect_step_type(step.content)
            if detected_type != StepType.ANALYSIS:
                step.step_type = detected_type
        
        # Auto-detect confidence level if not set properly
        if step.confidence == ConfidenceLevel.MEDIUM:
            detected_confidence = self._detect_confidence_level(step.content)
            if detected_confidence != ConfidenceLevel.MEDIUM:
                step.confidence = detected_confidence
        
        # Enhance metadata
        step.metadata.update(self._extract_metadata(step))
        
        # Validate step content
        validation_results = self._validate_step(step)
        step.metadata['validation'] = validation_results
        
        self.logger.debug(f"Processed step {step.step_number}: {step.step_type.value}")
        
        return step
    
    def _detect_step_type(self, content: str) -> StepType:
        """
        Detect the type of reasoning step based on content.
        
        Args:
            content: The step content to analyze
            
        Returns:
            StepType: The detected step type
        """
        content_lower = content.lower()
        type_scores: Dict[StepType, int] = {step_type: 0 for step_type in StepType}
        
        for step_type, patterns in self.step_patterns.items():
            for pattern in patterns:
                matches = len(re.findall(pattern, content_lower, re.IGNORECASE))
                type_scores[step_type] += matches
        
        # Return type with highest score, default to ANALYSIS
        if max(type_scores.values()) > 0:
            return max(type_scores, key=type_scores.get)
        
        return StepType.ANALYSIS
    
    def _detect_confidence_level(self, content: str) -> ConfidenceLevel:
        """
        Detect confidence level based on language used in content.
        
        Args:
            content: The content to analyze
            
        Returns:
            ConfidenceLevel: The detected confidence level
        """
        content_lower = content.lower()
        confidence_scores: Dict[ConfidenceLevel, int] = {
            level: 0 for level in ConfidenceLevel
        }
        
        for confidence_level, patterns in self.confidence_indicators.items():
            for pattern in patterns:
                matches = len(re.findall(pattern, content_lower, re.IGNORECASE))
                confidence_scores[confidence_level] += matches
        
        # Return level with highest score, default to MEDIUM
        if max(confidence_scores.values()) > 0:
            return max(confidence_scores, key=confidence_scores.get)
        
        return ConfidenceLevel.MEDIUM
    
    def _extract_metadata(self, step: ReasoningStep) -> Dict[str, Any]:
        """
        Extract additional metadata from the step content.
        
        Args:
            step: The reasoning step
            
        Returns:
            Dict[str, Any]: Extracted metadata
        """
        metadata = {}
        
        # Content statistics
        metadata['word_count'] = len(step.content.split())
        metadata['character_count'] = len(step.content)
        metadata['sentence_count'] = len(re.findall(r'[.!?]+', step.content))
        
        # Extract keywords
        keywords = self._extract_keywords(step.content)
        metadata['keywords'] = keywords
        
        # Detect questions
        questions = re.findall(r'[^.!?]*\?', step.content)
        metadata['questions'] = len(questions)
        
        # Detect numbers and calculations
        numbers = re.findall(r'\b\d+(?:\.\d+)?\b', step.content)
        metadata['numbers'] = numbers
        
        # Processing timestamp
        metadata['processed_at'] = datetime.utcnow().isoformat()
        
        return metadata
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Extract key terms from content."""
        # Simple keyword extraction - remove common words
        common_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we',
            'they', 'me', 'him', 'her', 'us', 'them'
        }
        
        words = re.findall(r'\b\w+\b', content.lower())
        keywords = [word for word in words if len(word) > 3 and word not in common_words]
        
        # Return unique keywords, limited to most frequent
        from collections import Counter
        keyword_counts = Counter(keywords)
        return [word for word, count in keyword_counts.most_common(10)]
    
    def _validate_step(self, step: ReasoningStep) -> Dict[str, Any]:
        """
        Validate a reasoning step for quality and completeness.
        
        Args:
            step: The step to validate
            
        Returns:
            Dict[str, Any]: Validation results
        """
        validation = {
            'is_valid': True,
            'issues': [],
            'quality_score': 1.0,
            'completeness_score': 1.0
        }
        
        # Check content length
        if len(step.content.strip()) < 10:
            validation['issues'].append('Content too short')
            validation['quality_score'] -= 0.3
        
        # Check for meaningful content
        if not re.search(r'\b\w{4,}\b', step.content):
            validation['issues'].append('Content lacks meaningful words')
            validation['quality_score'] -= 0.2
        
        # Check description matches content type
        if step.description and step.step_type:
            expected_words = {
                StepType.ANALYSIS: ['analyz', 'examin', 'study'],
                StepType.INFERENCE: ['infer', 'deduce', 'conclude'],
                StepType.SYNTHESIS: ['combin', 'integrat', 'synthesiz'],
                StepType.EVALUATION: ['evaluat', 'assess', 'compar'],
                StepType.CONCLUSION: ['conclud', 'final', 'result']
            }
            
            if step.step_type in expected_words:
                desc_lower = step.description.lower()
                if not any(word in desc_lower for word in expected_words[step.step_type]):
                    validation['issues'].append('Description does not match step type')
                    validation['completeness_score'] -= 0.2
        
        # Overall validation
        validation['is_valid'] = len(validation['issues']) == 0
        validation['overall_score'] = (
            validation['quality_score'] + validation['completeness_score']
        ) / 2
        
        return validation
    
    def optimize_chain(self, chain: ThinkingChain) -> ThinkingChain:
        """
        Optimize a thinking chain by improving step quality and flow.
        
        Args:
            chain: The thinking chain to optimize
            
        Returns:
            ThinkingChain: The optimized chain
        """
        if not chain.steps:
            return chain
        
        # Process each step
        for i, step in enumerate(chain.steps):
            chain.steps[i] = self.process_step(step)
        
        # Ensure logical flow
        chain = self._ensure_logical_flow(chain)
        
        # Update overall confidence based on step confidences
        chain.overall_confidence = self._calculate_overall_confidence(chain.steps)
        
        # Add chain-level metadata
        chain.metadata.update(self._analyze_chain(chain))
        
        self.logger.info(f"Optimized thinking chain with {len(chain.steps)} steps")
        
        return chain
    
    def _ensure_logical_flow(self, chain: ThinkingChain) -> ThinkingChain:
        """Ensure logical flow between steps in the chain."""
        
        if len(chain.steps) < 2:
            return chain
        
        # Typical logical flow: Analysis -> Inference -> Synthesis -> Evaluation -> Conclusion
        preferred_order = [
            StepType.ANALYSIS,
            StepType.INFERENCE, 
            StepType.SYNTHESIS,
            StepType.EVALUATION,
            StepType.CONCLUSION
        ]
        
        # Check if steps follow logical order
        current_order = [step.step_type for step in chain.steps]
        flow_score = self._calculate_flow_score(current_order, preferred_order)
        
        chain.metadata['logical_flow_score'] = flow_score
        
        if flow_score < 0.5:
            chain.metadata['flow_warning'] = 'Steps may not follow optimal logical order'
        
        return chain
    
    def _calculate_flow_score(
        self, 
        current_order: List[StepType], 
        preferred_order: List[StepType]
    ) -> float:
        """Calculate how well the current order matches preferred flow."""
        
        if not current_order:
            return 1.0
        
        # Simple scoring based on order adherence
        score = 0.0
        for i, step_type in enumerate(current_order):
            if step_type in preferred_order:
                preferred_index = preferred_order.index(step_type)
                # Score higher if step appears in reasonable position
                position_score = 1.0 - abs(i - preferred_index) / max(len(current_order), len(preferred_order))
                score += position_score
        
        return score / len(current_order)
    
    def _calculate_overall_confidence(self, steps: List[ReasoningStep]) -> ConfidenceLevel:
        """Calculate overall confidence from individual step confidences."""
        
        if not steps:
            return ConfidenceLevel.MEDIUM
        
        # Map confidence levels to numeric values
        confidence_values = {
            ConfidenceLevel.LOW: 1,
            ConfidenceLevel.MEDIUM: 2,
            ConfidenceLevel.HIGH: 3,
            ConfidenceLevel.VERY_HIGH: 4
        }
        
        # Calculate average confidence
        total_confidence = sum(confidence_values[step.confidence] for step in steps)
        avg_confidence = total_confidence / len(steps)
        
        # Map back to confidence level
        if avg_confidence >= 3.5:
            return ConfidenceLevel.VERY_HIGH
        elif avg_confidence >= 2.5:
            return ConfidenceLevel.HIGH
        elif avg_confidence >= 1.5:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def _analyze_chain(self, chain: ThinkingChain) -> Dict[str, Any]:
        """Analyze the complete thinking chain and extract insights."""
        
        analysis = {}
        
        # Step type distribution
        step_types = [step.step_type.value for step in chain.steps]
        analysis['step_type_distribution'] = {
            step_type.value: step_types.count(step_type.value) 
            for step_type in StepType
        }
        
        # Average step quality
        quality_scores = []
        for step in chain.steps:
            if 'validation' in step.metadata:
                quality_scores.append(step.metadata['validation'].get('overall_score', 0.5))
        
        if quality_scores:
            analysis['average_quality'] = sum(quality_scores) / len(quality_scores)
        else:
            analysis['average_quality'] = 0.5
        
        # Chain complexity
        total_words = sum(
            step.metadata.get('word_count', 0) 
            for step in chain.steps 
            if 'word_count' in step.metadata
        )
        analysis['total_words'] = total_words
        analysis['complexity'] = min(total_words / 100, 1.0)  # Normalize to 0-1
        
        return analysis
    
    def get_step_statistics(self, steps: List[ReasoningStep]) -> Dict[str, Any]:
        """Get statistics about a collection of reasoning steps."""
        
        if not steps:
            return {'total_steps': 0}
        
        stats = {
            'total_steps': len(steps),
            'step_types': {},
            'confidence_levels': {},
            'average_word_count': 0,
            'validation_scores': []
        }
        
        # Collect statistics
        total_words = 0
        for step in steps:
            # Step type distribution
            step_type = step.step_type.value
            stats['step_types'][step_type] = stats['step_types'].get(step_type, 0) + 1
            
            # Confidence distribution
            confidence = step.confidence.value
            stats['confidence_levels'][confidence] = stats['confidence_levels'].get(confidence, 0) + 1
            
            # Word count
            word_count = step.metadata.get('word_count', 0)
            total_words += word_count
            
            # Validation scores
            if 'validation' in step.metadata:
                stats['validation_scores'].append(
                    step.metadata['validation'].get('overall_score', 0.5)
                )
        
        # Calculate averages
        stats['average_word_count'] = total_words / len(steps)
        
        if stats['validation_scores']:
            stats['average_validation_score'] = (
                sum(stats['validation_scores']) / len(stats['validation_scores'])
            )
        
        return stats