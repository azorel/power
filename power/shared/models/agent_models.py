"""
Shared data models for AI agent personality system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from enum import Enum
import uuid


class TaskStatus(Enum):
    """Status values for agent tasks."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class TaskPriority(Enum):
    """Priority levels for tasks."""
    LOW = 1
    MEDIUM = 5
    HIGH = 8
    URGENT = 10


class CollaborationType(Enum):
    """Types of collaboration between agents."""
    CONSULTATION = "consultation"
    JOINT_DECISION = "joint_decision"
    TASK_HANDOFF = "task_handoff"
    PEER_REVIEW = "peer_review"
    MENTORING = "mentoring"
    BRAINSTORMING = "brainstorming"


class AgentStatus(Enum):
    """Status values for agent monitoring."""
    ACTIVE = "active"
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"


@dataclass
class AgentProfile:
    """Complete profile for an AI agent personality."""
    agent_id: str
    name: str
    role: str
    department: str
    personality_traits: Dict[str, float]  # trait_name -> strength (0.0-1.0)
    decision_making_style: str
    communication_style: str
    authority_level: str
    expertise_domains: List[str]
    skills: Dict[str, int]  # skill_name -> proficiency (1-10)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    active: bool = True
    version: str = "1.0"
    
    def __post_init__(self):
        """Validate profile data after initialization."""
        if not self.agent_id:
            self.agent_id = str(uuid.uuid4())
        
        # Ensure personality traits are within valid range
        for trait, value in self.personality_traits.items():
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"Personality trait '{trait}' must be between 0.0 and 1.0")
        
        # Ensure skills are within valid range
        for skill, level in self.skills.items():
            if not 1 <= level <= 10:
                raise ValueError(f"Skill level for '{skill}' must be between 1 and 10")


@dataclass
class TaskAssignment:
    """Task assignment with all relevant details."""
    task_id: str
    assigned_to: str
    assigned_by: str
    title: str
    description: str
    priority: TaskPriority
    status: TaskStatus
    deadline: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    notes: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Generate task ID if not provided."""
        if not self.task_id:
            self.task_id = f"task_{str(uuid.uuid4())[:8]}"
    
    def add_note(self, note: str) -> None:
        """Add a note to the task."""
        self.notes.append(f"{datetime.now().isoformat()}: {note}")
        self.updated_at = datetime.now()
    
    def update_status(self, new_status: TaskStatus) -> None:
        """Update task status with timestamp tracking."""
        self.status = new_status
        self.updated_at = datetime.now()
        
        if new_status == TaskStatus.IN_PROGRESS and not self.started_at:
            self.started_at = datetime.now()
        elif new_status == TaskStatus.COMPLETED and not self.completed_at:
            self.completed_at = datetime.now()


@dataclass
class AgentInteraction:
    """Record of interaction between agents."""
    interaction_id: str
    initiator_id: str
    target_id: str
    interaction_type: str
    content: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)
    outcome: Optional[str] = None
    satisfaction_score: Optional[float] = None  # 0.0-1.0
    
    def __post_init__(self):
        """Generate interaction ID if not provided."""
        if not self.interaction_id:
            self.interaction_id = f"int_{str(uuid.uuid4())[:8]}"


@dataclass
class CollaborationSession:
    """Multi-agent collaboration session."""
    session_id: str
    participants: List[str]
    collaboration_type: CollaborationType
    objective: str
    context: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "pending"
    outcomes: List[Dict[str, Any]] = field(default_factory=list)
    decisions_made: List[Dict[str, Any]] = field(default_factory=list)
    action_items: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        """Generate session ID if not provided."""
        if not self.session_id:
            self.session_id = f"collab_{str(uuid.uuid4())[:8]}"
    
    def add_outcome(self, outcome: Dict[str, Any]) -> None:
        """Add an outcome to the collaboration session."""
        outcome['timestamp'] = datetime.now().isoformat()
        self.outcomes.append(outcome)
    
    def add_decision(self, decision: Dict[str, Any]) -> None:
        """Add a decision made during collaboration."""
        decision['timestamp'] = datetime.now().isoformat()
        self.decisions_made.append(decision)
    
    def add_action_item(self, item: Dict[str, Any]) -> None:
        """Add an action item from the collaboration."""
        item['created_at'] = datetime.now().isoformat()
        item['status'] = 'pending'
        self.action_items.append(item)


@dataclass
class PerformanceMetrics:
    """Performance metrics for an agent."""
    agent_id: str
    metric_type: str
    period_start: datetime
    period_end: datetime
    metrics: Dict[str, float]
    task_count: int = 0
    success_rate: float = 0.0
    average_completion_time: float = 0.0
    quality_score: float = 0.0
    collaboration_score: float = 0.0
    learning_progress: Dict[str, float] = field(default_factory=dict)
    areas_for_improvement: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class LearningRecord:
    """Record of agent learning and adaptation."""
    record_id: str
    agent_id: str
    learning_type: str
    experience_data: Dict[str, Any]
    outcome: str
    lessons_learned: List[str]
    skill_improvements: Dict[str, float]
    confidence_changes: Dict[str, float]
    timestamp: datetime = field(default_factory=datetime.now)
    feedback_received: Optional[str] = None
    applied_successfully: bool = False
    
    def __post_init__(self):
        """Generate record ID if not provided."""
        if not self.record_id:
            self.record_id = f"learn_{str(uuid.uuid4())[:8]}"


@dataclass
class AgentMemoryItem:
    """Individual memory item for an agent."""
    memory_id: str
    agent_id: str
    memory_type: str
    content: Dict[str, Any]
    importance: int  # 1-10 scale
    tags: List[str]
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    accessed_at: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    retention_score: float = 1.0  # Decays over time
    
    def __post_init__(self):
        """Generate memory ID if not provided."""
        if not self.memory_id:
            self.memory_id = f"mem_{str(uuid.uuid4())[:8]}"
        
        # Validate importance score
        if not 1 <= self.importance <= 10:
            raise ValueError("Importance must be between 1 and 10")
    
    def access(self) -> None:
        """Record access to this memory."""
        self.accessed_at = datetime.now()
        self.access_count += 1
        # Boost retention score on access
        self.retention_score = min(1.0, self.retention_score + 0.1)


@dataclass
class DecisionRecord:
    """Record of a decision made by an agent."""
    decision_id: str
    agent_id: str
    decision_context: Dict[str, Any]
    options_considered: List[str]
    chosen_option: str
    reasoning: str
    confidence_level: float  # 0.0-1.0
    decision_factors: Dict[str, float]
    timestamp: datetime = field(default_factory=datetime.now)
    outcome: Optional[str] = None
    effectiveness_score: Optional[float] = None
    lessons_learned: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Generate decision ID if not provided."""
        if not self.decision_id:
            self.decision_id = f"dec_{str(uuid.uuid4())[:8]}"
        
        # Validate confidence level
        if not 0.0 <= self.confidence_level <= 1.0:
            raise ValueError("Confidence level must be between 0.0 and 1.0")
    
    def record_outcome(self, outcome: str, effectiveness: float) -> None:
        """Record the outcome and effectiveness of the decision."""
        self.outcome = outcome
        self.effectiveness_score = effectiveness
        
        # Add automatic lesson based on effectiveness
        if effectiveness < 0.3:
            self.lessons_learned.append("Low effectiveness - reconsider decision factors")
        elif effectiveness > 0.8:
            self.lessons_learned.append("High effectiveness - replicate decision pattern")


@dataclass
class SkillAssessment:
    """Assessment of an agent's skills and capabilities."""
    assessment_id: str
    agent_id: str
    skill_domain: str
    assessed_skills: Dict[str, int]  # skill_name -> level (1-10)
    strengths: List[str]
    improvement_areas: List[str]
    recommendations: List[str]
    assessor: str  # Who/what performed the assessment
    assessment_date: datetime = field(default_factory=datetime.now)
    next_assessment_date: Optional[datetime] = None
    
    def __post_init__(self):
        """Generate assessment ID if not provided."""
        if not self.assessment_id:
            self.assessment_id = f"assess_{str(uuid.uuid4())[:8]}"
        
        # Validate skill levels
        for skill, level in self.assessed_skills.items():
            if not 1 <= level <= 10:
                raise ValueError(f"Skill level for '{skill}' must be between 1 and 10")


@dataclass
class AgentGoal:
    """Goal or objective for an agent."""
    goal_id: str
    agent_id: str
    title: str
    description: str
    target_date: datetime
    priority: TaskPriority
    success_criteria: List[str]
    current_progress: float = 0.0  # 0.0-1.0
    milestones: List[Dict[str, Any]] = field(default_factory=list)
    obstacles: List[str] = field(default_factory=list)
    resources_needed: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    status: str = "active"
    
    def __post_init__(self):
        """Generate goal ID if not provided."""
        if not self.goal_id:
            self.goal_id = f"goal_{str(uuid.uuid4())[:8]}"
        
        # Validate progress
        if not 0.0 <= self.current_progress <= 1.0:
            raise ValueError("Progress must be between 0.0 and 1.0")
    
    def update_progress(self, new_progress: float, note: str = "") -> None:
        """Update goal progress."""
        if not 0.0 <= new_progress <= 1.0:
            raise ValueError("Progress must be between 0.0 and 1.0")
        
        self.current_progress = new_progress
        self.updated_at = datetime.now()
        
        if new_progress >= 1.0:
            self.status = "completed"
        
        # Add milestone if significant progress made
        if note:
            milestone = {
                'progress': new_progress,
                'note': note,
                'timestamp': datetime.now().isoformat()
            }
            self.milestones.append(milestone)


@dataclass
class CommunicationPreferences:
    """Communication preferences for an agent."""
    agent_id: str
    preferred_channels: List[str]
    communication_frequency: str
    response_time_expectation: str
    formality_level: str
    information_detail_level: str
    preferred_meeting_times: List[str]
    collaboration_style: str
    feedback_preferences: Dict[str, str]
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class TaskEvent:
    """Event related to task execution by an agent."""
    event_id: str
    agent_id: str
    task_id: str
    event_type: str  # started, progress, completed, failed, paused
    event_data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    performance_metrics: Optional[Dict[str, float]] = None
    
    def __post_init__(self):
        """Generate event ID if not provided."""
        if not self.event_id:
            self.event_id = f"event_{str(uuid.uuid4())[:8]}"