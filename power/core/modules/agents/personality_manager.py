"""
Core personality management system for AI agents.
Handles personality traits, decision making, and behavioral patterns.
"""

import json
import random
import sqlite3
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from shared.interfaces.agent_personality import (
    DecisionMakingStyle,
    CommunicationStyle,
    AuthorityLevel,
    AgentDecision
)
from shared.models.agent_models import (
    AgentProfile,
    DecisionRecord
)


class PersonalityManager:
    """
    Core personality management system.
    Manages agent profiles, decision making, and behavioral adaptations.
    """

    def __init__(self, database_path: str = "agents.db"):
        """
        Initialize personality manager.

        Args:
            database_path: Path to SQLite database for persistence
        """
        self.database_path = database_path
        self.agents: Dict[str, AgentProfile] = {}
        self.decision_history: Dict[str, List[DecisionRecord]] = {}
        self._initialize_database()
        self._load_agents()

    def _initialize_database(self) -> None:
        """Initialize database tables for agent data."""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        # Agents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                agent_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                department TEXT NOT NULL,
                personality_traits TEXT NOT NULL,
                decision_making_style TEXT NOT NULL,
                communication_style TEXT NOT NULL,
                authority_level TEXT NOT NULL,
                expertise_domains TEXT NOT NULL,
                skills TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                version TEXT NOT NULL DEFAULT '1.0'
            )
        """)

        # Decision history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                decision_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                decision_context TEXT NOT NULL,
                options_considered TEXT NOT NULL,
                chosen_option TEXT NOT NULL,
                reasoning TEXT NOT NULL,
                confidence_level REAL NOT NULL,
                decision_factors TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                outcome TEXT,
                effectiveness_score REAL,
                lessons_learned TEXT,
                FOREIGN KEY (agent_id) REFERENCES agents (agent_id)
            )
        """)

        # Performance metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                metric_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                metric_type TEXT NOT NULL,
                period_start TEXT NOT NULL,
                period_end TEXT NOT NULL,
                metrics TEXT NOT NULL,
                task_count INTEGER NOT NULL DEFAULT 0,
                success_rate REAL NOT NULL DEFAULT 0.0,
                average_completion_time REAL NOT NULL DEFAULT 0.0,
                quality_score REAL NOT NULL DEFAULT 0.0,
                collaboration_score REAL NOT NULL DEFAULT 0.0,
                learning_progress TEXT NOT NULL,
                areas_for_improvement TEXT NOT NULL,
                strengths TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (agent_id) REFERENCES agents (agent_id)
            )
        """)

        conn.commit()
        conn.close()

    def _load_agents(self) -> None:
        """Load agent profiles from database."""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM agents WHERE active = 1")
        rows = cursor.fetchall()

        for row in rows:
            agent_profile = AgentProfile(
                agent_id=row[0],
                name=row[1],
                role=row[2],
                department=row[3],
                personality_traits=json.loads(row[4]),
                decision_making_style=row[5],
                communication_style=row[6],
                authority_level=row[7],
                expertise_domains=json.loads(row[8]),
                skills=json.loads(row[9]),
                created_at=datetime.fromisoformat(row[10]),
                updated_at=datetime.fromisoformat(row[11]),
                active=bool(row[12]),
                version=row[13]
            )
            self.agents[agent_profile.agent_id] = agent_profile

        conn.close()

    def create_agent_profile(  # pylint: disable=too-many-arguments
        self,
        name: str,
        role: str,
        department: str,
        personality_traits: Dict[str, float],
        decision_making_style: str,
        communication_style: str,
        authority_level: str,
        expertise_domains: List[str],
        skills: Dict[str, int]
    ) -> str:
        """
        Create a new agent personality profile.

        Args:
            name: Display name for the agent
            role: Role/position of the agent
            department: Department or organizational unit
            personality_traits: Dictionary of personality traits (0.0-1.0)
            decision_making_style: Primary decision making approach
            communication_style: Primary communication style
            authority_level: Level of autonomous decision authority
            expertise_domains: Areas of specialized knowledge
            skills: Skills and proficiency levels (1-10)

        Returns:
            Agent ID of the created profile

        Raises:
            ValueError: If validation fails
        """
        agent_id = str(uuid.uuid4())

        # Validate personality traits
        for trait, value in personality_traits.items():
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"Personality trait '{trait}' must be between 0.0 and 1.0")

        # Validate skills
        for skill, level in skills.items():
            if not 1 <= level <= 10:
                raise ValueError(f"Skill level for '{skill}' must be between 1 and 10")

        # Create profile
        profile = AgentProfile(
            agent_id=agent_id,
            name=name,
            role=role,
            department=department,
            personality_traits=personality_traits,
            decision_making_style=decision_making_style,
            communication_style=communication_style,
            authority_level=authority_level,
            expertise_domains=expertise_domains,
            skills=skills
        )

        # Store in memory and database
        self.agents[agent_id] = profile
        self._save_agent_profile(profile)

        return agent_id

    def _save_agent_profile(self, profile: AgentProfile) -> None:
        """Save agent profile to database."""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO agents (
                agent_id, name, role, department, personality_traits,
                decision_making_style, communication_style, authority_level,
                expertise_domains, skills, created_at, updated_at, active, version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            profile.agent_id,
            profile.name,
            profile.role,
            profile.department,
            json.dumps(profile.personality_traits),
            profile.decision_making_style,
            profile.communication_style,
            profile.authority_level,
            json.dumps(profile.expertise_domains),
            json.dumps(profile.skills),
            profile.created_at.isoformat(),
            profile.updated_at.isoformat(),
            int(profile.active),
            profile.version
        ))

        conn.commit()
        conn.close()

    def get_agent_profile(self, agent_id: str) -> Optional[AgentProfile]:
        """
        Get agent profile by ID.

        Args:
            agent_id: Unique identifier for the agent

        Returns:
            Agent profile or None if not found
        """
        return self.agents.get(agent_id)

    def list_agents(
        self,
        department: Optional[str] = None,
        role: Optional[str] = None,
        active_only: bool = True
    ) -> List[AgentProfile]:
        """
        List agent profiles with optional filtering.

        Args:
            department: Filter by department
            role: Filter by role
            active_only: Only return active agents

        Returns:
            List of matching agent profiles
        """
        agents = list(self.agents.values())

        if active_only:
            agents = [agent for agent in agents if agent.active]

        if department:
            agents = [agent for agent in agents if agent.department == department]

        if role:
            agents = [agent for agent in agents if agent.role == role]

        return agents

    def make_decision(
        self,
        agent_id: str,
        context: Dict[str, Any],
        options: List[str],
        constraints: Optional[Dict[str, Any]] = None
    ) -> AgentDecision:
        """
        Make a decision using the agent's personality and decision-making style.

        Args:
            agent_id: ID of the agent making the decision
            context: Current situation and relevant information
            options: Available choices to decide between
            constraints: Any limitations or requirements

        Returns:
            AgentDecision with chosen option and reasoning

        Raises:
            ValueError: If agent not found or invalid inputs
        """
        agent = self.agents.get(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        if not options:
            raise ValueError("Options list cannot be empty")

        # Simulate decision making based on personality
        decision_factors = self._calculate_decision_factors(agent, context, constraints)
        chosen_option, confidence = self._select_option(
            agent, options, decision_factors, context
        )
        reasoning = self._generate_reasoning(
            agent, chosen_option, decision_factors, context
        )

        # Create decision record
        decision = AgentDecision(
            decision_id=str(uuid.uuid4()),
            agent_id=agent_id,
            decision=chosen_option,
            reasoning=reasoning,
            confidence=confidence,
            timestamp=datetime.now(),
            context=context,
            authority_level=AuthorityLevel(agent.authority_level)
        )

        # Store decision history
        decision_record = DecisionRecord(
            decision_id=decision.decision_id,
            agent_id=agent_id,
            decision_context=context,
            options_considered=options,
            chosen_option=chosen_option,
            reasoning=reasoning,
            confidence_level=confidence,
            decision_factors=decision_factors
        )

        if agent_id not in self.decision_history:
            self.decision_history[agent_id] = []
        self.decision_history[agent_id].append(decision_record)

        self._save_decision_record(decision_record)

        return decision

    def _calculate_decision_factors(
        self,
        agent: AgentProfile,
        context: Dict[str, Any],
        constraints: Optional[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate decision factors based on agent personality."""
        factors = {}

        # Base factors from personality traits
        factors['risk_tolerance'] = agent.personality_traits.get('openness', 0.5)
        factors['analytical_weight'] = agent.personality_traits.get('conscientiousness', 0.5)
        factors['intuitive_weight'] = agent.personality_traits.get('openness', 0.5)
        factors['collaborative_weight'] = agent.personality_traits.get('agreeableness', 0.5)

        # Adjust based on decision making style
        if agent.decision_making_style == DecisionMakingStyle.ANALYTICAL.value:
            factors['analytical_weight'] *= 1.5
            factors['intuitive_weight'] *= 0.7
        elif agent.decision_making_style == DecisionMakingStyle.INTUITIVE.value:
            factors['intuitive_weight'] *= 1.5
            factors['analytical_weight'] *= 0.7
        elif agent.decision_making_style == DecisionMakingStyle.COLLABORATIVE.value:
            factors['collaborative_weight'] *= 1.3

        # Consider context factors
        if context.get('urgency') == 'high':
            factors['speed_weight'] = 0.8
        else:
            factors['speed_weight'] = 0.3

        if context.get('stakeholder_count', 0) > 3:
            factors['collaborative_weight'] *= 1.2

        # Apply constraints
        if constraints:
            if constraints.get('budget_limited'):
                factors['cost_weight'] = 0.9
            if constraints.get('time_limited'):
                factors['speed_weight'] *= 1.4

        return factors

    def _select_option(
        self,
        agent: AgentProfile,
        options: List[str],
        decision_factors: Dict[str, float],
        context: Dict[str, Any]  # pylint: disable=unused-argument
    ) -> Tuple[str, float]:
        """Select the best option based on decision factors."""
        # Simplified decision logic - in reality would be more sophisticated
        scores = {}

        for option in options:
            score = 0.0

            # Score based on agent's expertise
            for domain in agent.expertise_domains:
                if domain.lower() in option.lower():
                    score += 0.3

            # Score based on decision factors
            if 'innovative' in option.lower() or 'new' in option.lower():
                score += decision_factors.get('risk_tolerance', 0.5) * 0.4

            if 'collaborate' in option.lower() or 'team' in option.lower():
                score += decision_factors.get('collaborative_weight', 0.5) * 0.3

            if 'analyze' in option.lower() or 'research' in option.lower():
                score += decision_factors.get('analytical_weight', 0.5) * 0.3

            # Add some randomness based on personality
            randomness = agent.personality_traits.get('openness', 0.5) * 0.2
            score += random.uniform(-randomness, randomness)

            scores[option] = max(0.0, min(1.0, score))

        # Select highest scoring option
        best_option = max(scores, key=scores.get)
        confidence = scores[best_option]

        return best_option, confidence

    def _generate_reasoning(
        self,
        agent: AgentProfile,
        chosen_option: str,
        decision_factors: Dict[str, float],  # pylint: disable=unused-argument
        context: Dict[str, Any]
    ) -> str:
        """Generate reasoning explanation for the decision."""
        reasoning_parts = []

        # Base reasoning on decision style
        if agent.decision_making_style == DecisionMakingStyle.ANALYTICAL.value:
            reasoning_parts.append("After careful analysis of the available data")
        elif agent.decision_making_style == DecisionMakingStyle.INTUITIVE.value:
            reasoning_parts.append("Based on my experience and intuition")
        elif agent.decision_making_style == DecisionMakingStyle.COLLABORATIVE.value:
            reasoning_parts.append("Considering the need for stakeholder alignment")

        # Add expertise-based reasoning
        relevant_domains = [d for d in agent.expertise_domains 
                          if d.lower() in chosen_option.lower()]
        if relevant_domains:
            reasoning_parts.append(
                f"leveraging my expertise in {', '.join(relevant_domains)}"
            )

        # Add context-based reasoning
        if context.get('urgency') == 'high':
            reasoning_parts.append("given the urgent nature of the situation")

        if context.get('budget_limited'):
            reasoning_parts.append("while maintaining cost effectiveness")

        reasoning_parts.append(f"I recommend '{chosen_option}' as the optimal choice")

        return ", ".join(reasoning_parts) + "."

    def _save_decision_record(self, record: DecisionRecord) -> None:
        """Save decision record to database."""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO decisions (
                decision_id, agent_id, decision_context, options_considered,
                chosen_option, reasoning, confidence_level, decision_factors,
                timestamp, outcome, effectiveness_score, lessons_learned
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.decision_id,
            record.agent_id,
            json.dumps(record.decision_context),
            json.dumps(record.options_considered),
            record.chosen_option,
            record.reasoning,
            record.confidence_level,
            json.dumps(record.decision_factors),
            record.timestamp.isoformat(),
            record.outcome,
            record.effectiveness_score,
            json.dumps(record.lessons_learned)
        ))

        conn.commit()
        conn.close()

    def update_agent_personality(
        self,
        agent_id: str,
        personality_updates: Dict[str, float]
    ) -> bool:
        """
        Update agent personality traits based on learning.

        Args:
            agent_id: ID of the agent to update
            personality_updates: Trait updates to apply

        Returns:
            True if update successful

        Raises:
            ValueError: If agent not found or invalid updates
        """
        agent = self.agents.get(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        # Validate updates
        for trait, value in personality_updates.items():
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"Personality trait '{trait}' must be between 0.0 and 1.0")

        # Apply updates with dampening to prevent extreme changes
        for trait, new_value in personality_updates.items():
            if trait in agent.personality_traits:
                current_value = agent.personality_traits[trait]
                # Apply 20% of the change to prevent dramatic shifts
                adjusted_change = (new_value - current_value) * 0.2
                agent.personality_traits[trait] = current_value + adjusted_change
            else:
                agent.personality_traits[trait] = new_value

        agent.updated_at = datetime.now()
        self._save_agent_profile(agent)

        return True

    def get_decision_history(
        self,
        agent_id: str,
        limit: int = 10
    ) -> List[DecisionRecord]:
        """
        Get decision history for an agent.

        Args:
            agent_id: ID of the agent
            limit: Maximum number of decisions to return

        Returns:
            List of recent decision records
        """
        if agent_id not in self.decision_history:
            return []

        decisions = self.decision_history[agent_id]
        return sorted(decisions, key=lambda d: d.timestamp, reverse=True)[:limit]

    def deactivate_agent(self, agent_id: str) -> bool:
        """
        Deactivate an agent profile.

        Args:
            agent_id: ID of the agent to deactivate

        Returns:
            True if deactivation successful
        """
        agent = self.agents.get(agent_id)
        if not agent:
            return False

        agent.active = False
        agent.updated_at = datetime.now()
        self._save_agent_profile(agent)

        return True

    def get_agents_by_expertise(self, domain: str) -> List[AgentProfile]:
        """
        Get agents with expertise in a specific domain.

        Args:
            domain: Expertise domain to search for

        Returns:
            List of agents with matching expertise
        """
        matching_agents = []

        for agent in self.agents.values():
            if not agent.active:
                continue

            for expertise in agent.expertise_domains:
                if domain.lower() in expertise.lower():
                    matching_agents.append(agent)
                    break

        return matching_agents

    def calculate_agent_compatibility(
        self,
        agent1_id: str,
        agent2_id: str
    ) -> float:
        """
        Calculate compatibility score between two agents.

        Args:
            agent1_id: ID of first agent
            agent2_id: ID of second agent

        Returns:
            Compatibility score (0.0-1.0)

        Raises:
            ValueError: If agents not found
        """
        agent1 = self.agents.get(agent1_id)
        agent2 = self.agents.get(agent2_id)

        if not agent1 or not agent2:
            raise ValueError("One or both agents not found")

        # Calculate compatibility based on personality traits
        trait_compatibility = 0.0
        trait_count = 0

        for trait in agent1.personality_traits:
            if trait in agent2.personality_traits:
                # Some traits work better when similar, others when complementary
                if trait in ['agreeableness', 'conscientiousness']:
                    # These work better when similar
                    diff = abs(agent1.personality_traits[trait] - 
                             agent2.personality_traits[trait])
                    trait_compatibility += 1.0 - diff
                else:
                    # These can work well when complementary
                    diff = abs(agent1.personality_traits[trait] - 
                             agent2.personality_traits[trait])
                    trait_compatibility += max(0.5, 1.0 - diff)
                trait_count += 1

        if trait_count > 0:
            trait_compatibility /= trait_count

        # Consider communication style compatibility
        comm_compatibility = 0.7  # Default neutral
        if agent1.communication_style == agent2.communication_style:
            comm_compatibility = 0.8
        elif (agent1.communication_style == CommunicationStyle.DIPLOMATIC.value and
              agent2.communication_style == CommunicationStyle.DIRECT.value):
            comm_compatibility = 0.6  # Can work but requires adjustment

        # Consider authority level compatibility
        auth_compatibility = 0.7  # Default neutral
        auth1 = AuthorityLevel(agent1.authority_level)
        auth2 = AuthorityLevel(agent2.authority_level)

        if auth1 != auth2:
            auth_compatibility = 0.8  # Different authority levels can work well

        # Overall compatibility score
        compatibility = (trait_compatibility * 0.5 +
                        comm_compatibility * 0.3 +
                        auth_compatibility * 0.2)

        return max(0.0, min(1.0, compatibility))
