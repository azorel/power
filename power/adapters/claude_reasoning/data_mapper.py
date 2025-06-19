"""
Claude Reasoning Data Mapper

Handles data transformation between shared models and Claude API formats
following API integration standards.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from shared.models.reasoning_models import (
    ReasoningRequest,
    ReasoningResponse,
    ReasoningStep,
    ReasoningMode,
    ThinkingChain,
    StepType,
    ConfidenceLevel,
    ComplexityAnalysis
)


class ClaudeReasoningDataMapper:
    """
    Data mapper for transforming between shared reasoning models and Claude API formats.
    
    This mapper handles the conversion of reasoning requests and responses to/from
    Claude's API format while preserving all reasoning-specific information.
    """
    
    def __init__(self):
        """Initialize the data mapper."""
        self.logger = logging.getLogger(__name__)
        
        # Claude message format templates
        self.reasoning_prompts = {
            ReasoningMode.RAPID: self._get_rapid_prompt_template(),
            ReasoningMode.THOUGHTFUL: self._get_thoughtful_prompt_template(),
            ReasoningMode.CHAIN_OF_THOUGHT: self._get_chain_of_thought_template(),
            ReasoningMode.STEP_BY_STEP: self._get_step_by_step_template(),
            ReasoningMode.ADAPTIVE: self._get_adaptive_prompt_template()
        }
    
    def map_request_to_claude(
        self, 
        request: ReasoningRequest, 
        api_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Map a reasoning request to Claude API format.
        
        Args:
            request: The reasoning request to map
            api_config: API configuration parameters
            
        Returns:
            Dict[str, Any]: Claude API request format
        """
        # Get the appropriate prompt template for the mode
        prompt_template = self.reasoning_prompts.get(
            request.mode, 
            self.reasoning_prompts[ReasoningMode.THOUGHTFUL]
        )
        
        # Build the system message based on reasoning mode
        system_message = self._build_system_message(request)
        
        # Format the user prompt
        formatted_prompt = prompt_template.format(
            user_prompt=request.prompt,
            max_steps=request.max_steps,
            context=self._format_context(request.context),
            temperature=request.temperature
        )
        
        # Build Claude messages
        messages = [
            {
                "role": "user",
                "content": formatted_prompt
            }
        ]
        
        # Claude API request
        claude_request = {
            "model": api_config.get('model', 'claude-3-sonnet-20240229'),
            "max_tokens": api_config.get('max_tokens', 4096),
            "temperature": request.temperature,
            "system": system_message,
            "messages": messages
        }
        
        # Add streaming if requested
        if request.stream_steps:
            claude_request["stream"] = True
        
        # Add metadata
        claude_request["metadata"] = {
            "reasoning_request_id": str(request.id),
            "reasoning_mode": request.mode.value,
            "max_steps": request.max_steps,
            "created_at": request.created_at.isoformat()
        }
        
        self.logger.debug(f"Mapped reasoning request to Claude format: {request.mode.value}")
        
        return claude_request
    
    def map_response_from_claude(
        self, 
        claude_response: Dict[str, Any], 
        request: ReasoningRequest
    ) -> ReasoningResponse:
        """
        Map Claude API response to reasoning response format.
        
        Args:
            claude_response: The Claude API response
            request: The original reasoning request
            
        Returns:
            ReasoningResponse: Mapped reasoning response
        """
        try:
            # Extract response content
            content = claude_response.get('content', [])
            if content and isinstance(content, list):
                response_text = content[0].get('text', '')
            else:
                response_text = str(claude_response.get('content', ''))
            
            # Parse reasoning content based on mode
            if request.mode == ReasoningMode.RAPID:
                return self._parse_rapid_response(claude_response, request, response_text)
            else:
                return self._parse_structured_response(claude_response, request, response_text)
                
        except Exception as e:
            self.logger.error(f"Failed to map Claude response: {e}")
            return ReasoningResponse(
                request_id=request.id,
                success=False,
                error_message=f"Response mapping failed: {e}",
                provider="claude"
            )
    
    def _parse_rapid_response(
        self, 
        claude_response: Dict[str, Any], 
        request: ReasoningRequest,
        response_text: str
    ) -> ReasoningResponse:
        """Parse rapid response format."""
        
        return ReasoningResponse(
            request_id=request.id,
            rapid_answer=response_text,
            mode_used=ReasoningMode.RAPID,
            tokens_used=claude_response.get('usage', {}).get('output_tokens', 0),
            complexity_score=0.2,  # Low complexity for rapid responses
            provider="claude",
            success=True
        )
    
    def _parse_structured_response(
        self, 
        claude_response: Dict[str, Any], 
        request: ReasoningRequest,
        response_text: str
    ) -> ReasoningResponse:
        """Parse structured reasoning response with thinking chain."""
        
        # Try to parse structured thinking from response
        thinking_chain = self._extract_thinking_chain(response_text, request.mode)
        
        # Calculate complexity score based on response length and structure
        complexity_score = self._calculate_complexity_score(response_text, thinking_chain)
        
        return ReasoningResponse(
            request_id=request.id,
            thinking_chain=thinking_chain,
            mode_used=request.mode,
            tokens_used=claude_response.get('usage', {}).get('output_tokens', 0),
            complexity_score=complexity_score,
            provider="claude",
            success=True
        )
    
    def _extract_thinking_chain(self, response_text: str, mode: ReasoningMode) -> ThinkingChain:
        """Extract thinking chain from Claude response text."""
        
        thinking_chain = ThinkingChain()
        
        # Look for structured step patterns
        step_patterns = [
            r'Step (\d+):\s*(.+?)(?=Step \d+:|$)',
            r'(\d+)\.\s*(.+?)(?=\d+\.|$)',
            r'## (.+?)\n(.+?)(?=##|$)',
            r'\*\*(.+?)\*\*\s*(.+?)(?=\*\*|$)'
        ]
        
        steps_found = False
        
        for pattern in step_patterns:
            import re
            matches = re.findall(pattern, response_text, re.DOTALL | re.MULTILINE)
            
            if matches:
                steps_found = True
                for i, match in enumerate(matches):
                    if len(match) >= 2:
                        step_description = match[0] if isinstance(match[0], str) else f"Step {i+1}"
                        step_content = match[1].strip()
                        
                        step = ReasoningStep(
                            step_number=i + 1,
                            step_type=self._detect_step_type(step_description, step_content),
                            description=step_description,
                            content=step_content,
                            confidence=self._detect_confidence(step_content)
                        )
                        
                        thinking_chain.add_step(step)
                break
        
        # If no structured steps found, create a single comprehensive step
        if not steps_found:
            step = ReasoningStep(
                step_number=1,
                step_type=StepType.ANALYSIS,
                description="Comprehensive reasoning",
                content=response_text,
                confidence=ConfidenceLevel.MEDIUM
            )
            thinking_chain.add_step(step)
        
        # Extract final answer
        thinking_chain.final_answer = self._extract_final_answer(response_text)
        
        # Set overall confidence
        if thinking_chain.steps:
            confidences = [step.confidence for step in thinking_chain.steps]
            thinking_chain.overall_confidence = self._calculate_overall_confidence(confidences)
        
        return thinking_chain
    
    def _detect_step_type(self, description: str, content: str) -> StepType:
        """Detect step type from description and content."""
        
        combined_text = (description + " " + content).lower()
        
        type_keywords = {
            StepType.ANALYSIS: ['analyz', 'examin', 'study', 'investigat', 'break down'],
            StepType.INFERENCE: ['infer', 'deduce', 'conclude', 'therefore', 'thus'],
            StepType.SYNTHESIS: ['combin', 'integrat', 'synthesiz', 'merge', 'together'],
            StepType.EVALUATION: ['evaluat', 'assess', 'compar', 'weigh', 'measur'],
            StepType.CONCLUSION: ['conclud', 'final', 'result', 'answer', 'decision']
        }
        
        for step_type, keywords in type_keywords.items():
            if any(keyword in combined_text for keyword in keywords):
                return step_type
        
        return StepType.ANALYSIS  # Default
    
    def _detect_confidence(self, content: str) -> ConfidenceLevel:
        """Detect confidence level from content language."""
        
        content_lower = content.lower()
        
        high_confidence_words = ['certain', 'definite', 'clear', 'obvious', 'definitely']
        medium_confidence_words = ['likely', 'probably', 'appears', 'suggests']
        low_confidence_words = ['uncertain', 'maybe', 'might', 'possibly', 'perhaps']
        
        if any(word in content_lower for word in high_confidence_words):
            return ConfidenceLevel.HIGH
        elif any(word in content_lower for word in low_confidence_words):
            return ConfidenceLevel.LOW
        elif any(word in content_lower for word in medium_confidence_words):
            return ConfidenceLevel.MEDIUM
        
        return ConfidenceLevel.MEDIUM
    
    def _extract_final_answer(self, response_text: str) -> str:
        """Extract final answer from response text."""
        
        # Look for conclusion patterns
        conclusion_patterns = [
            r'(?:In conclusion|Therefore|Finally|The answer is)[:\s]*(.+?)(?:\n|$)',
            r'(?:Conclusion|Final answer|Result)[:\s]*(.+?)(?:\n|$)',
            r'(.+?)(?:\n|$)'  # Last resort - use last sentence
        ]
        
        import re
        for pattern in conclusion_patterns:
            match = re.search(pattern, response_text, re.IGNORECASE | re.DOTALL)
            if match:
                answer = match.group(1).strip()
                if len(answer) > 10:  # Ensure meaningful content
                    return answer
        
        # Return last paragraph as fallback
        paragraphs = response_text.strip().split('\n\n')
        return paragraphs[-1] if paragraphs else response_text[:200]
    
    def _calculate_overall_confidence(self, confidences: List[ConfidenceLevel]) -> ConfidenceLevel:
        """Calculate overall confidence from individual step confidences."""
        
        confidence_values = {
            ConfidenceLevel.LOW: 1,
            ConfidenceLevel.MEDIUM: 2,
            ConfidenceLevel.HIGH: 3,
            ConfidenceLevel.VERY_HIGH: 4
        }
        
        if not confidences:
            return ConfidenceLevel.MEDIUM
        
        avg_confidence = sum(confidence_values[c] for c in confidences) / len(confidences)
        
        if avg_confidence >= 3.5:
            return ConfidenceLevel.VERY_HIGH
        elif avg_confidence >= 2.5:
            return ConfidenceLevel.HIGH
        elif avg_confidence >= 1.5:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def _calculate_complexity_score(self, response_text: str, thinking_chain: ThinkingChain) -> float:
        """Calculate complexity score based on response characteristics."""
        
        score = 0.0
        
        # Length factor
        length_score = min(len(response_text) / 2000, 0.3)
        score += length_score
        
        # Number of steps
        if thinking_chain and thinking_chain.steps:
            step_score = min(len(thinking_chain.steps) / 10, 0.3)
            score += step_score
        
        # Structural complexity
        import re
        structured_elements = len(re.findall(r'(?:Step|##|\*\*|\d+\.)', response_text))
        structure_score = min(structured_elements / 20, 0.2)
        score += structure_score
        
        # Technical content
        technical_patterns = [
            r'\b(?:algorithm|implementation|analysis|synthesis)\b',
            r'\b(?:because|therefore|however|moreover)\b',
            r'\b(?:consider|evaluate|compare|determine)\b'
        ]
        
        for pattern in technical_patterns:
            if re.search(pattern, response_text, re.IGNORECASE):
                score += 0.05
        
        return min(score, 1.0)
    
    def _build_system_message(self, request: ReasoningRequest) -> str:
        """Build system message based on reasoning mode."""
        
        base_system = """You are Claude, an AI assistant created by Anthropic. You are designed to be helpful, harmless, and honest."""
        
        mode_instructions = {
            ReasoningMode.RAPID: """
Provide quick, concise responses. Focus on direct answers without extensive reasoning steps.
Be accurate but prioritize speed and brevity.
""",
            ReasoningMode.THOUGHTFUL: """
Take time to think through problems carefully. Provide detailed reasoning and consider multiple perspectives.
Structure your response with clear reasoning steps when helpful.
""",
            ReasoningMode.CHAIN_OF_THOUGHT: """
Show your reasoning process step by step. Break down complex problems into logical steps.
Use clear step numbering and explain your reasoning at each stage.
Format: Step 1: [reasoning], Step 2: [reasoning], etc.
""",
            ReasoningMode.STEP_BY_STEP: """
Provide comprehensive, detailed analysis with explicit step-by-step reasoning.
Use structured thinking with clear sections for analysis, inference, and conclusions.
Be thorough and methodical in your approach.
""",
            ReasoningMode.ADAPTIVE: """
Adapt your reasoning approach based on the complexity and nature of the question.
Use quick responses for simple questions and detailed reasoning for complex ones.
"""
        }
        
        mode_instruction = mode_instructions.get(request.mode, mode_instructions[ReasoningMode.THOUGHTFUL])
        
        return base_system + mode_instruction
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context information for inclusion in prompts."""
        
        if not context:
            return ""
        
        context_parts = []
        
        if 'recent_prompts' in context:
            context_parts.append(f"Recent conversation context: {context['recent_prompts']}")
        
        if 'user_preferences' in context:
            prefs = context['user_preferences']
            if 'detail_level' in prefs:
                context_parts.append(f"Preferred detail level: {prefs['detail_level']}")
        
        if 'topic_context' in context and context['topic_context'].get('is_follow_up'):
            context_parts.append("This appears to be a follow-up question.")
        
        return "\n".join(context_parts) if context_parts else ""
    
    def _get_rapid_prompt_template(self) -> str:
        """Get prompt template for rapid mode."""
        return """
{context}

Question: {user_prompt}

Please provide a quick, direct answer. Be concise but accurate.
"""
    
    def _get_thoughtful_prompt_template(self) -> str:
        """Get prompt template for thoughtful mode."""
        return """
{context}

Question: {user_prompt}

Please think through this carefully and provide a detailed response with your reasoning.
"""
    
    def _get_chain_of_thought_template(self) -> str:
        """Get prompt template for chain of thought mode."""
        return """
{context}

Question: {user_prompt}

Please solve this step by step. Show your reasoning process clearly with numbered steps.
Use the format:

Step 1: [First reasoning step]
Step 2: [Second reasoning step]
...
Final Answer: [Your conclusion]

Maximum steps: {max_steps}
"""
    
    def _get_step_by_step_template(self) -> str:
        """Get prompt template for step-by-step mode."""
        return """
{context}

Question: {user_prompt}

Please provide a comprehensive, step-by-step analysis. Be thorough and methodical.

Structure your response with:
1. Problem Analysis
2. Reasoning Steps
3. Evaluation of Options (if applicable)
4. Final Conclusion

Maximum steps: {max_steps}
"""
    
    def _get_adaptive_prompt_template(self) -> str:
        """Get prompt template for adaptive mode."""
        return """
{context}

Question: {user_prompt}

Please respond appropriately to this question, using the level of detail and reasoning depth that best fits the complexity and nature of the question.
"""