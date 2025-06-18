"""
Collaboration coordination system for AI agents.
Manages agent-to-agent interactions, joint decision making, and conflict resolution.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import sqlite3
import uuid
from collections import defaultdict
from enum import Enum

from shared.interfaces.agent_personality import (
    CollaborationCoordinator,
    AgentDecision,
    DecisionMakingStyle,
    AuthorityLevel
)
from shared.models.agent_models import (
    CollaborationSession,
    AgentInteraction,
    CollaborationType,
    AgentProfile,
    TaskAssignment
)


class ConflictType(Enum):
    """Types of conflicts that can occur between agents."""
    RESOURCE_CONFLICT = "resource_conflict"
    PRIORITY_CONFLICT = "priority_conflict"
    APPROACH_DISAGREEMENT = "approach_disagreement"
    AUTHORITY_CONFLICT = "authority_conflict"
    GOAL_MISALIGNMENT = "goal_misalignment"


class CollaborationStatus(Enum):
    """Status of collaboration sessions."""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    CONFLICT = "conflict"


class AgentCollaborationCoordinator(CollaborationCoordinator):
    """
    Core collaboration coordination system.
    Manages multi-agent interactions and decision making.
    """

    def __init__(self, database_path: str = "agent_collaboration.db"):
        """
        Initialize collaboration coordinator.

        Args:
            database_path: Path to SQLite database for collaboration data
        """
        self.database_path = database_path
        self.active_sessions: Dict[str, CollaborationSession] = {}
        self.interaction_history: Dict[str, List[AgentInteraction]] = defaultdict(list)
        self.conflict_resolution_strategies: Dict[ConflictType, List[str]] = {
            ConflictType.RESOURCE_CONFLICT: [
                "time_sharing", "priority_based_allocation", "resource_pooling"
            ],
            ConflictType.PRIORITY_CONFLICT: [
                "executive_decision", "voting", "compromise_solution"
            ],
            ConflictType.APPROACH_DISAGREEMENT: [
                "expert_consultation", "pilot_testing", "hybrid_approach"
            ],
            ConflictType.AUTHORITY_CONFLICT: [
                "hierarchy_clarification", "domain_separation", "mediation"
            ],
            ConflictType.GOAL_MISALIGNMENT: [
                "goal_reconciliation", "stakeholder_consultation", "objective_prioritization"
            ]
        }
        self._initialize_database()
        self._load_active_sessions()

    def _initialize_database(self) -> None:
        """Initialize database tables for collaboration data."""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        # Collaboration sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS collaboration_sessions (
                session_id TEXT PRIMARY KEY,
                participants TEXT NOT NULL,
                collaboration_type TEXT NOT NULL,
                objective TEXT NOT NULL,
                context TEXT NOT NULL,
                created_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                outcomes TEXT NOT NULL,
                decisions_made TEXT NOT NULL,
                action_items TEXT NOT NULL
            )
        """)

        # Agent interactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_interactions (
                interaction_id TEXT PRIMARY KEY,
                initiator_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                interaction_type TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                context TEXT NOT NULL,
                outcome TEXT,
                satisfaction_score REAL
            )
        """)

        # Conflict resolution table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conflict_resolutions (
                resolution_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                conflict_type TEXT NOT NULL,
                conflicting_agents TEXT NOT NULL,
                conflict_description TEXT NOT NULL,
                resolution_strategy TEXT NOT NULL,
                resolution_details TEXT NOT NULL,
                resolution_timestamp TEXT NOT NULL,
                effectiveness_score REAL,
                follow_up_required INTEGER DEFAULT 0,
                FOREIGN KEY (session_id) REFERENCES collaboration_sessions (session_id)
            )
        """)

        # Decision records table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS collaborative_decisions (
                decision_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                decision_type TEXT NOT NULL,
                participants TEXT NOT NULL,
                decision_context TEXT NOT NULL,
                options_considered TEXT NOT NULL,
                final_decision TEXT NOT NULL,
                decision_process TEXT NOT NULL,
                consensus_level REAL NOT NULL,
                timestamp TEXT NOT NULL,
                implementation_status TEXT DEFAULT 'pending',
                FOREIGN KEY (session_id) REFERENCES collaboration_sessions (session_id)
            )
        """)

        conn.commit()
        conn.close()

    def _load_active_sessions(self) -> None:
        """Load active collaboration sessions from database."""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM collaboration_sessions 
            WHERE status IN ('pending', 'active')
        """)

        for row in cursor.fetchall():
            session = CollaborationSession(
                session_id=row[0],
                participants=json.loads(row[1]),
                collaboration_type=CollaborationType(row[2]),
                objective=row[3],
                context=json.loads(row[4]),
                created_at=datetime.fromisoformat(row[5]),
                started_at=datetime.fromisoformat(row[6]) if row[6] else None,
                completed_at=datetime.fromisoformat(row[7]) if row[7] else None,
                status=row[8],
                outcomes=json.loads(row[9]),
                decisions_made=json.loads(row[10]),
                action_items=json.loads(row[11])
            )
            self.active_sessions[session.session_id] = session

        conn.close()

    def initiate_collaboration(
        self,
        initiator_id: str,
        target_agents: List[str],
        collaboration_type: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Initiate a collaboration session between agents.

        Args:
            initiator_id: ID of the agent initiating collaboration
            target_agents: List of agent IDs to collaborate with
            collaboration_type: Type of collaboration needed
            context: Context and information for collaboration

        Returns:
            Collaboration session ID
        """
        participants = [initiator_id] + target_agents
        
        session = CollaborationSession(
            session_id=str(uuid.uuid4()),
            participants=participants,
            collaboration_type=CollaborationType(collaboration_type),
            objective=context.get('objective', 'Collaborative task execution'),
            context=context
        )

        # Store in database and memory
        self._store_collaboration_session(session)
        self.active_sessions[session.session_id] = session

        # Create initial interaction record
        interaction = AgentInteraction(
            interaction_id=str(uuid.uuid4()),
            initiator_id=initiator_id,
            target_id=','.join(target_agents),
            interaction_type="collaboration_initiation",
            content={
                'session_id': session.session_id,
                'collaboration_type': collaboration_type,
                'objective': session.objective
            },
            context=context
        )

        self._store_interaction(interaction)

        return session.session_id

    def _store_collaboration_session(self, session: CollaborationSession) -> None:
        """Store collaboration session in database."""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO collaboration_sessions (
                    session_id, participants, collaboration_type, objective,
                    context, created_at, started_at, completed_at, status,
                    outcomes, decisions_made, action_items
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session.session_id,
                json.dumps(session.participants),
                session.collaboration_type.value,
                session.objective,
                json.dumps(session.context),
                session.created_at.isoformat(),
                session.started_at.isoformat() if session.started_at else None,
                session.completed_at.isoformat() if session.completed_at else None,
                session.status,
                json.dumps(session.outcomes),
                json.dumps(session.decisions_made),
                json.dumps(session.action_items)
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"Error storing collaboration session: {e}")

    def _store_interaction(self, interaction: AgentInteraction) -> None:
        """Store agent interaction in database."""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO agent_interactions (
                    interaction_id, initiator_id, target_id, interaction_type,
                    content, timestamp, context, outcome, satisfaction_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                interaction.interaction_id,
                interaction.initiator_id,
                interaction.target_id,
                interaction.interaction_type,
                json.dumps(interaction.content),
                interaction.timestamp.isoformat(),
                json.dumps(interaction.context),
                interaction.outcome,
                interaction.satisfaction_score
            ))

            conn.commit()
            conn.close()

            # Add to memory cache
            self.interaction_history[interaction.initiator_id].append(interaction)

        except Exception as e:
            print(f"Error storing interaction: {e}")

    def coordinate_decision_making(
        self,
        agents: List[str],
        decision_context: Dict[str, Any]
    ) -> AgentDecision:
        """
        Coordinate multi-agent decision making.

        Args:
            agents: List of agent IDs participating in decision
            decision_context: Context and information for decision

        Returns:
            Collective agent decision
        """
        # Create or find existing collaboration session
        session_id = self._find_or_create_decision_session(agents, decision_context)
        session = self.active_sessions.get(session_id)

        if not session:
            raise ValueError(f"Could not create decision session for agents: {agents}")

        # Gather individual agent perspectives
        agent_positions = self._gather_agent_positions(agents, decision_context)

        # Analyze consensus level
        consensus_analysis = self._analyze_consensus(agent_positions)

        # Select decision making approach based on consensus
        if consensus_analysis['consensus_level'] >= 0.8:
            # High consensus - proceed with agreed option
            final_decision = consensus_analysis['preferred_option']
            decision_process = "consensus"
        elif consensus_analysis['consensus_level'] >= 0.6:
            # Moderate consensus - negotiate compromise
            final_decision = self._negotiate_compromise(agent_positions, decision_context)
            decision_process = "negotiation"
        else:
            # Low consensus - escalate or use authority-based decision
            final_decision = self._resolve_through_authority(agent_positions, decision_context)
            decision_process = "authority_resolution"

        # Create collaborative decision
        decision = AgentDecision(
            decision_id=str(uuid.uuid4()),
            agent_id=f"collaborative_{'_'.join(agents)}",
            decision=final_decision,
            reasoning=self._generate_collaborative_reasoning(
                agent_positions, decision_process, consensus_analysis
            ),
            confidence=consensus_analysis['consensus_level'],
            timestamp=datetime.now(),
            context=decision_context,
            authority_level=AuthorityLevel.EXECUTIVE
        )

        # Record decision in session
        session.add_decision({
            'decision_id': decision.decision_id,
            'decision': final_decision,
            'process': decision_process,
            'consensus_level': consensus_analysis['consensus_level'],
            'participants': agents
        })

        # Store decision record
        self._store_collaborative_decision(session_id, decision, agent_positions, decision_process)

        # Update session
        self._store_collaboration_session(session)

        return decision

    def _find_or_create_decision_session(
        self,
        agents: List[str],
        context: Dict[str, Any]
    ) -> str:
        """Find existing session or create new one for decision making."""
        # Check for existing active session with same participants
        for session_id, session in self.active_sessions.items():
            if (set(session.participants) == set(agents) and 
                session.status == 'active' and
                session.collaboration_type == CollaborationType.JOINT_DECISION):
                return session_id

        # Create new session
        return self.initiate_collaboration(
            agents[0], agents[1:], CollaborationType.JOINT_DECISION.value, context
        )

    def _gather_agent_positions(
        self,
        agents: List[str],
        context: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """Gather individual agent positions on the decision."""
        positions = {}
        options = context.get('options', [])

        for agent_id in agents:
            # Simulate agent decision making (in real system, would call actual agent)
            agent_position = {
                'preferred_option': self._simulate_agent_preference(agent_id, options, context),
                'confidence': 0.8,  # Placeholder
                'reasoning': f"Agent {agent_id} analysis based on expertise and context",
                'concerns': context.get('concerns', []),
                'requirements': context.get('requirements', [])
            }
            positions[agent_id] = agent_position

        return positions

    def _simulate_agent_preference(
        self,
        agent_id: str,
        options: List[str],
        context: Dict[str, Any]
    ) -> str:
        """Simulate agent preference selection (placeholder implementation)."""
        # In real implementation, would call the actual agent's decision making
        if options:
            # Simple simulation - could be enhanced with actual personality data
            import random
            return random.choice(options)
        return "default_option"

    def _analyze_consensus(self, agent_positions: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze consensus level among agent positions."""
        if not agent_positions:
            return {'consensus_level': 0.0, 'preferred_option': None}

        # Count preferences
        option_counts = defaultdict(int)
        total_agents = len(agent_positions)

        for position in agent_positions.values():
            option_counts[position['preferred_option']] += 1

        # Find most popular option
        if option_counts:
            preferred_option = max(option_counts, key=option_counts.get)
            consensus_level = option_counts[preferred_option] / total_agents
        else:
            preferred_option = None
            consensus_level = 0.0

        return {
            'consensus_level': consensus_level,
            'preferred_option': preferred_option,
            'option_distribution': dict(option_counts),
            'total_participants': total_agents
        }

    def _negotiate_compromise(
        self,
        agent_positions: Dict[str, Dict[str, Any]],
        context: Dict[str, Any]
    ) -> str:
        """Negotiate a compromise solution when consensus is moderate."""
        # Simple compromise logic - could be enhanced
        all_concerns = []
        all_requirements = []

        for position in agent_positions.values():
            all_concerns.extend(position.get('concerns', []))
            all_requirements.extend(position.get('requirements', []))

        # Create hybrid solution addressing major concerns
        compromise_solution = f"Hybrid approach addressing: {', '.join(set(all_concerns[:3]))}"
        return compromise_solution

    def _resolve_through_authority(
        self,
        agent_positions: Dict[str, Dict[str, Any]],
        context: Dict[str, Any]
    ) -> str:
        """Resolve decision through authority when consensus is low."""
        # Find highest authority agent
        highest_authority_agent = context.get('highest_authority_agent')
        
        if highest_authority_agent and highest_authority_agent in agent_positions:
            return agent_positions[highest_authority_agent]['preferred_option']
        
        # Fallback to first agent's preference
        first_agent = list(agent_positions.keys())[0]
        return agent_positions[first_agent]['preferred_option']

    def _generate_collaborative_reasoning(
        self,
        agent_positions: Dict[str, Dict[str, Any]],
        decision_process: str,
        consensus_analysis: Dict[str, Any]
    ) -> str:
        """Generate reasoning explanation for collaborative decision."""
        reasoning_parts = []

        if decision_process == "consensus":
            reasoning_parts.append(
                f"Strong consensus ({consensus_analysis['consensus_level']:.1%}) "
                f"achieved among {len(agent_positions)} participating agents"
            )
        elif decision_process == "negotiation":
            reasoning_parts.append(
                f"Moderate agreement ({consensus_analysis['consensus_level']:.1%}) "
                "reached through negotiation and compromise"
            )
        else:
            reasoning_parts.append(
                "Decision made through authority resolution due to low initial consensus"
            )

        # Add key considerations
        all_concerns = set()
        for position in agent_positions.values():
            all_concerns.update(position.get('concerns', []))

        if all_concerns:
            reasoning_parts.append(f"Key considerations: {', '.join(list(all_concerns)[:3])}")

        return ". ".join(reasoning_parts) + "."

    def _store_collaborative_decision(
        self,
        session_id: str,
        decision: AgentDecision,
        agent_positions: Dict[str, Dict[str, Any]],
        decision_process: str
    ) -> None:
        """Store collaborative decision record."""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO collaborative_decisions (
                    decision_id, session_id, decision_type, participants,
                    decision_context, options_considered, final_decision,
                    decision_process, consensus_level, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                decision.decision_id,
                session_id,
                "collaborative",
                json.dumps(list(agent_positions.keys())),
                json.dumps(decision.context),
                json.dumps([pos['preferred_option'] for pos in agent_positions.values()]),
                decision.decision,
                decision_process,
                decision.confidence,
                decision.timestamp.isoformat()
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"Error storing collaborative decision: {e}")

    def resolve_conflicts(
        self,
        conflicting_agents: List[str],
        conflict_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resolve conflicts between agents.

        Args:
            conflicting_agents: List of agents in conflict
            conflict_context: Context and details of the conflict

        Returns:
            Dictionary with resolution results
        """
        # Identify conflict type
        conflict_type = self._identify_conflict_type(conflict_context)
        
        # Select resolution strategy
        resolution_strategy = self._select_resolution_strategy(conflict_type, conflict_context)
        
        # Execute resolution
        resolution_result = self._execute_conflict_resolution(
            conflicting_agents, conflict_type, resolution_strategy, conflict_context
        )
        
        # Record resolution
        resolution_id = self._store_conflict_resolution(
            conflicting_agents, conflict_type, resolution_strategy, 
            resolution_result, conflict_context
        )
        
        return {
            'resolution_id': resolution_id,
            'conflict_type': conflict_type.value,
            'resolution_strategy': resolution_strategy,
            'resolution_details': resolution_result,
            'conflicting_agents': conflicting_agents,
            'timestamp': datetime.now().isoformat(),
            'status': 'resolved' if resolution_result.get('success') else 'failed'
        }

    def _identify_conflict_type(self, context: Dict[str, Any]) -> ConflictType:
        """Identify the type of conflict based on context."""
        conflict_indicators = context.get('conflict_indicators', [])
        
        if 'resource' in str(conflict_indicators).lower():
            return ConflictType.RESOURCE_CONFLICT
        elif 'priority' in str(conflict_indicators).lower():
            return ConflictType.PRIORITY_CONFLICT
        elif 'approach' in str(conflict_indicators).lower() or 'method' in str(conflict_indicators).lower():
            return ConflictType.APPROACH_DISAGREEMENT
        elif 'authority' in str(conflict_indicators).lower():
            return ConflictType.AUTHORITY_CONFLICT
        else:
            return ConflictType.GOAL_MISALIGNMENT

    def _select_resolution_strategy(
        self,
        conflict_type: ConflictType,
        context: Dict[str, Any]
    ) -> str:
        """Select appropriate resolution strategy for conflict type."""
        available_strategies = self.conflict_resolution_strategies[conflict_type]
        
        # Simple strategy selection - could be enhanced with ML
        urgency = context.get('urgency', 'medium')
        
        if urgency == 'high':
            # Prefer faster resolution strategies
            if conflict_type == ConflictType.PRIORITY_CONFLICT:
                return "executive_decision"
            elif conflict_type == ConflictType.RESOURCE_CONFLICT:
                return "priority_based_allocation"
        
        # Default to first available strategy
        return available_strategies[0] if available_strategies else "mediation"

    def _execute_conflict_resolution(
        self,
        agents: List[str],
        conflict_type: ConflictType,
        strategy: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the selected conflict resolution strategy."""
        resolution_result = {
            'success': False,
            'details': {},
            'action_items': [],
            'follow_up_required': False
        }

        try:
            if strategy == "executive_decision":
                # Have highest authority agent make final decision
                executive_agent = context.get('executive_agent', agents[0])
                decision = f"Executive decision by {executive_agent}"
                resolution_result.update({
                    'success': True,
                    'details': {'decision_maker': executive_agent, 'decision': decision},
                    'action_items': [f"Implement decision: {decision}"]
                })

            elif strategy == "time_sharing":
                # Allocate resources based on time slots
                time_allocation = self._calculate_time_sharing(agents, context)
                resolution_result.update({
                    'success': True,
                    'details': {'time_allocation': time_allocation},
                    'action_items': [f"Follow time allocation schedule"]
                })

            elif strategy == "compromise_solution":
                # Find middle ground between conflicting positions
                compromise = self._find_compromise_solution(agents, context)
                resolution_result.update({
                    'success': True,
                    'details': {'compromise': compromise},
                    'action_items': [f"Implement compromise: {compromise}"]
                })

            else:
                # Default mediation approach
                resolution_result.update({
                    'success': True,
                    'details': {'strategy': 'mediation', 'mediator': 'system'},
                    'action_items': ['Schedule mediation session'],
                    'follow_up_required': True
                })

        except Exception as e:
            resolution_result.update({
                'success': False,
                'error': str(e)
            })

        return resolution_result

    def _calculate_time_sharing(self, agents: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate time sharing allocation for resource conflicts."""
        # Simple equal time sharing - could be enhanced with priority weighting
        total_time = context.get('total_time_available', 100)
        time_per_agent = total_time // len(agents)
        
        allocation = {}
        for i, agent in enumerate(agents):
            start_time = i * time_per_agent
            end_time = (i + 1) * time_per_agent
            allocation[agent] = {'start': start_time, 'end': end_time, 'duration': time_per_agent}
        
        return allocation

    def _find_compromise_solution(self, agents: List[str], context: Dict[str, Any]) -> str:
        """Find compromise solution between conflicting positions."""
        # Simplified compromise logic
        agent_positions = context.get('positions', {})
        
        if len(agent_positions) >= 2:
            positions = list(agent_positions.values())
            return f"Hybrid approach combining elements of: {' and '.join(positions[:2])}"
        
        return "Balanced solution addressing all concerns"

    def _store_conflict_resolution(
        self,
        agents: List[str],
        conflict_type: ConflictType,
        strategy: str,
        result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """Store conflict resolution record."""
        try:
            resolution_id = str(uuid.uuid4())
            
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO conflict_resolutions (
                    resolution_id, session_id, conflict_type, conflicting_agents,
                    conflict_description, resolution_strategy, resolution_details,
                    resolution_timestamp, effectiveness_score, follow_up_required
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                resolution_id,
                context.get('session_id', 'standalone'),
                conflict_type.value,
                json.dumps(agents),
                context.get('description', 'Agent conflict'),
                strategy,
                json.dumps(result),
                datetime.now().isoformat(),
                0.8 if result.get('success') else 0.2,  # Placeholder effectiveness
                int(result.get('follow_up_required', False))
            ))

            conn.commit()
            conn.close()
            
            return resolution_id

        except Exception as e:
            print(f"Error storing conflict resolution: {e}")
            return str(uuid.uuid4())  # Return placeholder ID

    def track_collaboration_outcomes(
        self,
        collaboration_id: str,
        outcomes: Dict[str, Any]
    ) -> bool:
        """
        Track and store collaboration results.

        Args:
            collaboration_id: ID of the collaboration session
            outcomes: Results and outcomes of the collaboration

        Returns:
            True if tracking successful
        """
        session = self.active_sessions.get(collaboration_id)
        if not session:
            return False

        try:
            # Update session with outcomes
            session.add_outcome(outcomes)
            
            # Mark session as completed if indicated
            if outcomes.get('status') == 'completed':
                session.status = 'completed'
                session.completed_at = datetime.now()

            # Store updated session
            self._store_collaboration_session(session)

            return True

        except Exception as e:
            print(f"Error tracking collaboration outcomes: {e}")
            return False

    def get_collaboration_history(
        self,
        agent_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get collaboration history for an agent."""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM collaboration_sessions 
                WHERE participants LIKE ? 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (f'%{agent_id}%', limit))

            history = []
            for row in cursor.fetchall():
                history.append({
                    'session_id': row[0],
                    'participants': json.loads(row[1]),
                    'collaboration_type': row[2],
                    'objective': row[3],
                    'status': row[8],
                    'created_at': row[5],
                    'outcomes_count': len(json.loads(row[9]))
                })

            conn.close()
            return history

        except Exception as e:
            print(f"Error getting collaboration history: {e}")
            return []

    def get_active_collaborations(self) -> List[Dict[str, Any]]:
        """Get all active collaboration sessions."""
        active_collaborations = []
        
        for session in self.active_sessions.values():
            if session.status in ['pending', 'active']:
                active_collaborations.append({
                    'session_id': session.session_id,
                    'participants': session.participants,
                    'collaboration_type': session.collaboration_type.value,
                    'objective': session.objective,
                    'status': session.status,
                    'created_at': session.created_at.isoformat(),
                    'duration_minutes': (
                        datetime.now() - session.created_at
                    ).total_seconds() / 60
                })
        
        return active_collaborations