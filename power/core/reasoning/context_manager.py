"""
Reasoning Context Manager

Manages context and memory for reasoning operations, maintaining conversation
history and user preferences to improve reasoning quality over time.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from shared.models.reasoning_models import (
    ReasoningRequest,
    ReasoningResponse,
    ReasoningMode,
    ThinkingChain,
    ComplexityAnalysis
)


@dataclass
class ReasoningContext:
    """Represents reasoning context for a session."""
    session_id: str
    user_id: str
    conversation_history: List[Dict[str, Any]]
    user_preferences: Dict[str, Any]
    reasoning_history: List[Dict[str, Any]]
    created_at: datetime
    last_updated: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'conversation_history': self.conversation_history,
            'user_preferences': self.user_preferences,
            'reasoning_history': self.reasoning_history,
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat()
        }


@dataclass
class UserPreferences:
    """User preferences for reasoning operations."""
    preferred_mode: Optional[ReasoningMode] = None
    detail_level: str = "medium"  # low, medium, high
    response_speed: str = "balanced"  # fast, balanced, thorough
    explanation_style: str = "conversational"  # formal, conversational, technical
    confidence_threshold: float = 0.5
    max_steps: int = 10
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert preferences to dictionary."""
        result = asdict(self)
        if self.preferred_mode:
            result['preferred_mode'] = self.preferred_mode.value
        return result


class ReasoningContextManager:
    """
    Manages reasoning context and user session data.
    
    This manager maintains conversation history, user preferences, and reasoning
    patterns to improve the quality and relevance of reasoning operations.
    """
    
    def __init__(self, max_history_size: int = 100):
        """
        Initialize the context manager.
        
        Args:
            max_history_size: Maximum number of history items to maintain
        """
        self.logger = logging.getLogger(__name__)
        self.max_history_size = max_history_size
        self.contexts: Dict[str, ReasoningContext] = {}
        self.user_preferences: Dict[str, UserPreferences] = {}
        
    def get_or_create_context(
        self, 
        session_id: str, 
        user_id: str
    ) -> ReasoningContext:
        """
        Get existing context or create a new one.
        
        Args:
            session_id: Unique session identifier
            user_id: User identifier
            
        Returns:
            ReasoningContext: The context for this session
        """
        if session_id not in self.contexts:
            self.contexts[session_id] = ReasoningContext(
                session_id=session_id,
                user_id=user_id,
                conversation_history=[],
                user_preferences=self._get_user_preferences(user_id).to_dict(),
                reasoning_history=[],
                created_at=datetime.utcnow(),
                last_updated=datetime.utcnow()
            )
            self.logger.info(f"Created new reasoning context for session {session_id}")
        
        return self.contexts[session_id]
    
    def update_context(
        self, 
        session_id: str, 
        request: ReasoningRequest, 
        response: ReasoningResponse
    ) -> None:
        """
        Update context with new request/response pair.
        
        Args:
            session_id: Session identifier
            request: The reasoning request
            response: The reasoning response
        """
        if session_id not in self.contexts:
            self.logger.warning(f"Context not found for session {session_id}")
            return
        
        context = self.contexts[session_id]
        
        # Add to conversation history
        interaction = {
            'timestamp': datetime.utcnow().isoformat(),
            'request': request.to_dict(),
            'response': response.to_dict(),
            'success': response.success
        }
        
        context.conversation_history.append(interaction)
        
        # Maintain history size limit
        if len(context.conversation_history) > self.max_history_size:
            context.conversation_history = context.conversation_history[-self.max_history_size:]
        
        # Add to reasoning history if successful
        if response.success:
            reasoning_entry = {
                'prompt': request.prompt,
                'mode_used': response.mode_used.value,
                'complexity_score': response.complexity_score,
                'processing_time': response.processing_time,
                'user_satisfaction': None,  # To be updated later
                'timestamp': datetime.utcnow().isoformat()
            }
            
            context.reasoning_history.append(reasoning_entry)
            
            # Maintain reasoning history size
            if len(context.reasoning_history) > self.max_history_size:
                context.reasoning_history = context.reasoning_history[-self.max_history_size:]
        
        # Update timestamp
        context.last_updated = datetime.utcnow()
        
        self.logger.debug(f"Updated context for session {session_id}")
    
    def _get_user_preferences(self, user_id: str) -> UserPreferences:
        """Get user preferences, creating defaults if not found."""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = UserPreferences()
        
        return self.user_preferences[user_id]
    
    def update_user_preferences(
        self, 
        user_id: str, 
        preferences: Dict[str, Any]
    ) -> None:
        """
        Update user preferences.
        
        Args:
            user_id: User identifier
            preferences: Preference updates
        """
        current_prefs = self._get_user_preferences(user_id)
        
        # Update preferences
        if 'preferred_mode' in preferences:
            mode_value = preferences['preferred_mode']
            if isinstance(mode_value, str):
                try:
                    current_prefs.preferred_mode = ReasoningMode(mode_value)
                except ValueError:
                    self.logger.warning(f"Invalid reasoning mode: {mode_value}")
        
        for field in ['detail_level', 'response_speed', 'explanation_style']:
            if field in preferences:
                setattr(current_prefs, field, preferences[field])
        
        for field in ['confidence_threshold', 'max_steps']:
            if field in preferences:
                try:
                    setattr(current_prefs, field, float(preferences[field]) if field == 'confidence_threshold' else int(preferences[field]))
                except (ValueError, TypeError):
                    self.logger.warning(f"Invalid value for {field}: {preferences[field]}")
        
        self.logger.info(f"Updated preferences for user {user_id}")
    
    def get_context_for_request(
        self, 
        session_id: str, 
        request: ReasoningRequest
    ) -> Dict[str, Any]:
        """
        Get relevant context information for a reasoning request.
        
        Args:
            session_id: Session identifier
            request: The reasoning request
            
        Returns:
            Dict[str, Any]: Context information to enhance reasoning
        """
        if session_id not in self.contexts:
            return {}
        
        context = self.contexts[session_id]
        
        # Build context information
        context_info = {
            'session_id': session_id,
            'user_id': context.user_id,
            'user_preferences': context.user_preferences,
            'conversation_length': len(context.conversation_history),
            'reasoning_history_length': len(context.reasoning_history)
        }
        
        # Add recent conversation context
        if context.conversation_history:
            recent_interactions = context.conversation_history[-3:]  # Last 3 interactions
            context_info['recent_prompts'] = [
                interaction['request']['prompt'] 
                for interaction in recent_interactions
            ]
        
        # Add relevant reasoning patterns
        context_info['reasoning_patterns'] = self._analyze_reasoning_patterns(context)
        
        # Add topic continuity information
        context_info['topic_context'] = self._analyze_topic_continuity(
            context, request.prompt
        )
        
        return context_info
    
    def _analyze_reasoning_patterns(self, context: ReasoningContext) -> Dict[str, Any]:
        """Analyze user's reasoning patterns from history."""
        patterns = {
            'preferred_modes': {},
            'complexity_preference': 0.5,
            'speed_preference': 0.5,
            'success_rate': 0.0
        }
        
        if not context.reasoning_history:
            return patterns
        
        # Analyze mode preferences
        for entry in context.reasoning_history:
            mode = entry['mode_used']
            patterns['preferred_modes'][mode] = patterns['preferred_modes'].get(mode, 0) + 1
        
        # Calculate complexity preference (0 = simple, 1 = complex)
        complexity_scores = [
            entry.get('complexity_score', 0.5) 
            for entry in context.reasoning_history
        ]
        if complexity_scores:
            patterns['complexity_preference'] = sum(complexity_scores) / len(complexity_scores)
        
        # Calculate speed preference based on processing times
        processing_times = [
            entry.get('processing_time', 5.0) 
            for entry in context.reasoning_history
        ]
        if processing_times:
            avg_time = sum(processing_times) / len(processing_times)
            # Normalize to 0-1 scale (0 = fast preference, 1 = thorough preference)
            patterns['speed_preference'] = min(avg_time / 30.0, 1.0)
        
        # Calculate success rate
        successful_entries = len([
            entry for entry in context.reasoning_history 
            if entry.get('user_satisfaction', 0.5) > 0.5
        ])
        patterns['success_rate'] = successful_entries / len(context.reasoning_history)
        
        return patterns
    
    def _analyze_topic_continuity(
        self, 
        context: ReasoningContext, 
        current_prompt: str
    ) -> Dict[str, Any]:
        """Analyze topic continuity with previous interactions."""
        continuity = {
            'is_follow_up': False,
            'related_prompts': [],
            'topic_shift_score': 0.0,
            'context_relevance': 0.0
        }
        
        if not context.conversation_history:
            return continuity
        
        # Get recent prompts
        recent_prompts = [
            interaction['request']['prompt'] 
            for interaction in context.conversation_history[-5:]
        ]
        
        # Simple topic continuity analysis using keyword overlap
        current_keywords = self._extract_keywords(current_prompt.lower())
        
        for prompt in recent_prompts:
            prompt_keywords = self._extract_keywords(prompt.lower())
            overlap = len(set(current_keywords) & set(prompt_keywords))
            
            if overlap > 0:
                similarity = overlap / max(len(current_keywords), len(prompt_keywords))
                if similarity > 0.3:  # Threshold for related content
                    continuity['related_prompts'].append({
                        'prompt': prompt,
                        'similarity': similarity
                    })
        
        # Determine if this is a follow-up
        if continuity['related_prompts']:
            continuity['is_follow_up'] = True
            continuity['context_relevance'] = max(
                prompt['similarity'] for prompt in continuity['related_prompts']
            )
        
        # Calculate topic shift (0 = same topic, 1 = completely new topic)
        if recent_prompts:
            last_prompt = recent_prompts[-1]
            last_keywords = self._extract_keywords(last_prompt.lower())
            overlap = len(set(current_keywords) & set(last_keywords))
            
            if overlap > 0:
                continuity['topic_shift_score'] = 1.0 - (
                    overlap / max(len(current_keywords), len(last_keywords))
                )
            else:
                continuity['topic_shift_score'] = 1.0
        
        return continuity
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text for topic analysis."""
        import re
        
        # Remove common words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we',
            'they', 'me', 'him', 'her', 'us', 'them', 'what', 'where', 'when',
            'why', 'how', 'can', 'may', 'might', 'must'
        }
        
        # Extract words
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter keywords
        keywords = [
            word for word in words 
            if len(word) > 3 and word not in stop_words
        ]
        
        return list(set(keywords))  # Return unique keywords
    
    def record_user_satisfaction(
        self, 
        session_id: str, 
        interaction_index: int, 
        satisfaction_score: float
    ) -> None:
        """
        Record user satisfaction for a specific interaction.
        
        Args:
            session_id: Session identifier
            interaction_index: Index of the interaction (negative for recent)
            satisfaction_score: Satisfaction score (0-1)
        """
        if session_id not in self.contexts:
            return
        
        context = self.contexts[session_id]
        
        try:
            if interaction_index < 0:
                # Negative index for recent interactions
                history_index = len(context.reasoning_history) + interaction_index
            else:
                history_index = interaction_index
            
            if 0 <= history_index < len(context.reasoning_history):
                context.reasoning_history[history_index]['user_satisfaction'] = satisfaction_score
                self.logger.info(
                    f"Recorded satisfaction {satisfaction_score} for session {session_id}, "
                    f"interaction {interaction_index}"
                )
                
        except (IndexError, KeyError) as e:
            self.logger.error(f"Failed to record satisfaction: {e}")
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get a summary of the reasoning session."""
        if session_id not in self.contexts:
            return {'error': 'Session not found'}
        
        context = self.contexts[session_id]
        
        # Calculate statistics
        total_interactions = len(context.conversation_history)
        successful_interactions = len([
            interaction for interaction in context.conversation_history
            if interaction['success']
        ])
        
        # Mode usage
        mode_usage = {}
        processing_times = []
        
        for entry in context.reasoning_history:
            mode = entry['mode_used']
            mode_usage[mode] = mode_usage.get(mode, 0) + 1
            processing_times.append(entry['processing_time'])
        
        summary = {
            'session_id': session_id,
            'user_id': context.user_id,
            'created_at': context.created_at.isoformat(),
            'last_updated': context.last_updated.isoformat(),
            'total_interactions': total_interactions,
            'successful_interactions': successful_interactions,
            'success_rate': successful_interactions / total_interactions if total_interactions > 0 else 0,
            'mode_usage': mode_usage,
            'average_processing_time': sum(processing_times) / len(processing_times) if processing_times else 0,
            'reasoning_patterns': self._analyze_reasoning_patterns(context),
            'user_preferences': context.user_preferences
        }
        
        return summary
    
    def cleanup_old_contexts(self, max_age_hours: int = 24) -> int:
        """
        Clean up old contexts to manage memory usage.
        
        Args:
            max_age_hours: Maximum age of contexts to keep
            
        Returns:
            int: Number of contexts removed
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        sessions_to_remove = []
        
        for session_id, context in self.contexts.items():
            if context.last_updated < cutoff_time:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.contexts[session_id]
        
        self.logger.info(f"Cleaned up {len(sessions_to_remove)} old reasoning contexts")
        
        return len(sessions_to_remove)