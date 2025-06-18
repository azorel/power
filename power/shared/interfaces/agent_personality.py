"""
Abstract interfaces for AI agent personalities.
All agent personality implementations MUST implement these interfaces.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class DecisionMakingStyle(Enum):
    """Decision making styles for different agent personalities."""
    ANALYTICAL = "analytical"
    INTUITIVE = "intuitive" 
    DIRECTIVE = "directive"
    COLLABORATIVE = "collaborative"
    CONSULTATIVE = "consultative"
    CREATIVE = "creative"


class CommunicationStyle(Enum):
    """Communication styles for agent interactions."""
    FORMAL = "formal"
    CASUAL = "casual"
    DIRECT = "direct"
    DIPLOMATIC = "diplomatic"
    SUPPORTIVE = "supportive"
    STRATEGIC = "strategic"


class AuthorityLevel(Enum):
    """Authority levels for autonomous decision making."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXECUTIVE = "executive"


@dataclass
class AgentMemory:
    """Memory structure for agent learning and context."""
    agent_id: str
    memory_type: str
    content: Dict[str, Any]
    timestamp: datetime
    importance: int  # 1-10 scale
    tags: List[str]
    context: Optional[Dict[str, Any]] = None


@dataclass
class AgentDecision:
    """Structure for agent decision making results."""
    decision_id: str
    agent_id: str
    decision: str
    reasoning: str
    confidence: float  # 0.0-1.0
    timestamp: datetime
    context: Dict[str, Any]
    authority_level: AuthorityLevel


@dataclass
class AgentTask:
    """Task structure for agent work assignments."""
    task_id: str
    assigned_to: str
    title: str
    description: str
    priority: int  # 1-10 scale
    deadline: Optional[datetime]
    status: str
    dependencies: List[str]
    metadata: Dict[str, Any]


@dataclass
class AgentNotification:
    """Notification structure for agent-related events."""
    notification_id: str
    agent_id: str
    title: str
    message: str
    notification_type: str  # info, warning, error, success
    timestamp: datetime
    read: bool = False
    metadata: Optional[Dict[str, Any]] = None


class BaseAgentPersonality(ABC):
    """Base interface for all agent personalities."""

    @property
    @abstractmethod
    def agent_id(self) -> str:
        """Unique identifier for this agent."""
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self) -> str:
        """Display name for this agent."""
        raise NotImplementedError

    @property
    @abstractmethod
    def role(self) -> str:
        """Role/position of this agent."""
        raise NotImplementedError

    @property
    @abstractmethod
    def personality_traits(self) -> Dict[str, Any]:
        """Dictionary of personality traits and their values."""
        raise NotImplementedError

    @property
    @abstractmethod
    def decision_making_style(self) -> DecisionMakingStyle:
        """Primary decision making approach."""
        raise NotImplementedError

    @property
    @abstractmethod
    def communication_style(self) -> CommunicationStyle:
        """Primary communication approach."""
        raise NotImplementedError

    @property
    @abstractmethod
    def authority_level(self) -> AuthorityLevel:
        """Level of autonomous decision making authority."""
        raise NotImplementedError

    @property
    @abstractmethod
    def expertise_domains(self) -> List[str]:
        """Areas of specialized knowledge and expertise."""
        raise NotImplementedError

    @abstractmethod
    def make_decision(
        self,
        context: Dict[str, Any],
        options: List[str],
        constraints: Optional[Dict[str, Any]] = None
    ) -> AgentDecision:
        """
        Make a decision based on context and available options.

        Args:
            context: Current situation and relevant information
            options: Available choices to decide between
            constraints: Any limitations or requirements

        Returns:
            AgentDecision with the chosen option and reasoning
        """
        raise NotImplementedError

    @abstractmethod
    def process_information(
        self,
        information: Dict[str, Any],
        information_type: str
    ) -> Dict[str, Any]:
        """
        Process and interpret information according to personality.

        Args:
            information: Raw information to process
            information_type: Type/category of information

        Returns:
            Processed information with agent's interpretation
        """
        raise NotImplementedError

    @abstractmethod
    def generate_response(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a response in the agent's communication style.

        Args:
            prompt: Input prompt or question
            context: Additional context for response

        Returns:
            Response string in agent's voice and style
        """
        raise NotImplementedError

    @abstractmethod
    def learn_from_experience(
        self,
        experience: Dict[str, Any],
        outcome: str,
        feedback: Optional[str] = None
    ) -> bool:
        """
        Learn and adapt from experiences and outcomes.

        Args:
            experience: The experience to learn from
            outcome: Result or outcome of the experience
            feedback: Additional feedback for learning

        Returns:
            True if learning was successful
        """
        raise NotImplementedError

    @abstractmethod
    def collaborate_with_agent(
        self,
        other_agent_id: str,
        collaboration_type: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Collaborate with another agent on a task or decision.

        Args:
            other_agent_id: ID of the agent to collaborate with
            collaboration_type: Type of collaboration needed
            context: Context and information for collaboration

        Returns:
            Collaboration result and any shared information
        """
        raise NotImplementedError


class MemoryManager(ABC):
    """Interface for agent memory management systems."""

    @abstractmethod
    def store_memory(self, memory: AgentMemory) -> bool:
        """Store a memory for future retrieval."""
        raise NotImplementedError

    @abstractmethod
    def retrieve_memories(
        self,
        agent_id: str,
        memory_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[AgentMemory]:
        """Retrieve memories based on criteria."""
        raise NotImplementedError

    @abstractmethod
    def search_memories(
        self,
        agent_id: str,
        query: str,
        memory_type: Optional[str] = None
    ) -> List[AgentMemory]:
        """Search memories using semantic search."""
        raise NotImplementedError

    @abstractmethod
    def update_memory_importance(
        self,
        memory_id: str,
        new_importance: int
    ) -> bool:
        """Update the importance score of a memory."""
        raise NotImplementedError

    @abstractmethod
    def forget_memories(
        self,
        agent_id: str,
        criteria: Dict[str, Any]
    ) -> int:
        """Remove memories based on criteria (returns count removed)."""
        raise NotImplementedError


class LearningSystem(ABC):
    """Interface for agent learning and adaptation systems."""

    @abstractmethod
    def analyze_performance(
        self,
        agent_id: str,
        task_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze agent performance across multiple tasks."""
        raise NotImplementedError

    @abstractmethod
    def identify_improvement_areas(
        self,
        agent_id: str,
        performance_data: Dict[str, Any]
    ) -> List[str]:
        """Identify areas where the agent can improve."""
        raise NotImplementedError

    @abstractmethod
    def adapt_personality(
        self,
        agent_id: str,
        adaptation_data: Dict[str, Any]
    ) -> bool:
        """Adapt agent personality based on learning."""
        raise NotImplementedError

    @abstractmethod
    def generate_training_data(
        self,
        agent_id: str,
        improvement_areas: List[str]
    ) -> List[Dict[str, Any]]:
        """Generate training scenarios for improvement."""
        raise NotImplementedError


class CollaborationCoordinator(ABC):
    """Interface for managing agent-to-agent collaboration."""

    @abstractmethod
    def initiate_collaboration(
        self,
        initiator_id: str,
        target_agents: List[str],
        collaboration_type: str,
        context: Dict[str, Any]
    ) -> str:
        """Initiate a collaboration session between agents."""
        raise NotImplementedError

    @abstractmethod
    def coordinate_decision_making(
        self,
        agents: List[str],
        decision_context: Dict[str, Any]
    ) -> AgentDecision:
        """Coordinate multi-agent decision making."""
        raise NotImplementedError

    @abstractmethod
    def resolve_conflicts(
        self,
        conflicting_agents: List[str],
        conflict_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resolve conflicts between agents."""
        raise NotImplementedError

    @abstractmethod
    def track_collaboration_outcomes(
        self,
        collaboration_id: str,
        outcomes: Dict[str, Any]
    ) -> bool:
        """Track and store collaboration results."""
        raise NotImplementedError


class ExecutiveAgent(BaseAgentPersonality):
    """Extended interface for executive-level agents."""

    @abstractmethod
    def develop_strategy(
        self,
        goal: str,
        constraints: Dict[str, Any],
        timeframe: str
    ) -> Dict[str, Any]:
        """Develop strategic plans to achieve goals."""
        raise NotImplementedError

    @abstractmethod
    def delegate_tasks(
        self,
        tasks: List[AgentTask],
        available_agents: List[str]
    ) -> Dict[str, str]:
        """Delegate tasks to appropriate agents."""
        raise NotImplementedError

    @abstractmethod
    def monitor_progress(
        self,
        task_ids: List[str]
    ) -> Dict[str, Any]:
        """Monitor progress on delegated tasks."""
        raise NotImplementedError

    @abstractmethod
    def make_executive_decision(
        self,
        situation: Dict[str, Any],
        stakeholders: List[str]
    ) -> AgentDecision:
        """Make high-level executive decisions."""
        raise NotImplementedError


class SpecialistAgent(BaseAgentPersonality):
    """Extended interface for specialist agents."""

    @abstractmethod
    def provide_expert_analysis(
        self,
        data: Dict[str, Any],
        analysis_type: str
    ) -> Dict[str, Any]:
        """Provide expert analysis in the agent's domain."""
        raise NotImplementedError

    @abstractmethod
    def recommend_solutions(
        self,
        problem: str,
        constraints: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Recommend solutions based on expertise."""
        raise NotImplementedError

    @abstractmethod
    def validate_approach(
        self,
        approach: Dict[str, Any],
        domain: str
    ) -> Dict[str, Any]:
        """Validate approaches within the specialist domain."""
        raise NotImplementedError

    @abstractmethod
    def mentor_other_agents(
        self,
        mentee_id: str,
        skill_area: str,
        current_level: str
    ) -> Dict[str, Any]:
        """Provide mentoring and skill development."""
        raise NotImplementedError


class PerformanceTracker(ABC):
    """Interface for tracking agent performance and optimization."""

    @abstractmethod
    def record_task_performance(
        self,
        agent_id: str,
        task_id: str,
        performance_metrics: Dict[str, Any]
    ) -> bool:
        """Record performance metrics for a completed task."""
        raise NotImplementedError

    @abstractmethod
    def generate_performance_report(
        self,
        agent_id: str,
        time_period: str
    ) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        raise NotImplementedError

    @abstractmethod
    def compare_agent_performance(
        self,
        agent_ids: List[str],
        metric: str
    ) -> Dict[str, Any]:
        """Compare performance across multiple agents."""
        raise NotImplementedError

    @abstractmethod
    def identify_optimization_opportunities(
        self,
        agent_id: str
    ) -> List[Dict[str, Any]]:
        """Identify opportunities for performance optimization."""
        raise NotImplementedError

    @abstractmethod
    def track_learning_progress(
        self,
        agent_id: str,
        skill_area: str
    ) -> Dict[str, Any]:
        """Track progress in learning and skill development."""
        raise NotImplementedError