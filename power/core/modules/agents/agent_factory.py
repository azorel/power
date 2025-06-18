"""
Agent factory for creating and managing AI agent personalities.
Creates specific agent types with predefined personalities and capabilities.
"""

from typing import Dict, Any, List, Optional, Type
from datetime import datetime
import uuid

from shared.interfaces.agent_personality import (
    BaseAgentPersonality,
    ExecutiveAgent,
    SpecialistAgent,
    DecisionMakingStyle,
    CommunicationStyle,
    AuthorityLevel
)
from shared.models.agent_models import AgentProfile, TaskAssignment, AgentGoal
from .personality_manager import PersonalityManager
from .memory_system import MemorySystem
from .learning_engine import LearningEngine
from .collaboration_coordinator import AgentCollaborationCoordinator
from .performance_tracker import AgentPerformanceTracker


class AgentFactory:
    """
    Factory for creating and configuring AI agent personalities.
    Provides pre-configured agent types with specialized roles and capabilities.
    """

    def __init__(self, database_path: str = "agent_system.db"):
        """
        Initialize agent factory.

        Args:
            database_path: Base path for agent system databases
        """
        self.personality_manager = PersonalityManager(f"{database_path}_personalities.db")
        self.memory_system = MemorySystem(f"{database_path}_memories.db")
        self.learning_engine = LearningEngine(f"{database_path}_learning.db")
        self.collaboration_coordinator = AgentCollaborationCoordinator(f"{database_path}_collaboration.db")
        self.performance_tracker = AgentPerformanceTracker(f"{database_path}_performance.db")
        
        # Agent type definitions
        self.agent_types = {
            'ceo_assistant': self._get_ceo_assistant_config,
            'chief_of_staff': self._get_chief_of_staff_config,
            'cto': self._get_cto_config,
            'coo': self._get_coo_config,
            'cmo': self._get_cmo_config,
            'cfo': self._get_cfo_config,
            'executive_assistant': self._get_executive_assistant_config,
            'health_coach': self._get_health_coach_config,
            'learning_coordinator': self._get_learning_coordinator_config,
            'personal_development': self._get_personal_development_config,
            'project_manager': self._get_project_manager_config,
            'social_media_manager': self._get_social_media_manager_config,
            'brand_strategist': self._get_brand_strategist_config,
            'content_creator': self._get_content_creator_config
        }

    def create_agent(
        self,
        agent_type: str,
        name: Optional[str] = None,
        custom_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new agent with specified type and configuration.

        Args:
            agent_type: Type of agent to create (e.g., 'ceo_assistant', 'cto')
            name: Optional custom name for the agent
            custom_config: Optional custom configuration overrides

        Returns:
            Agent ID of the created agent

        Raises:
            ValueError: If agent type is not recognized
        """
        if agent_type not in self.agent_types:
            raise ValueError(f"Unknown agent type: {agent_type}. Available types: {list(self.agent_types.keys())}")

        # Get base configuration for agent type
        config_func = self.agent_types[agent_type]
        base_config = config_func()

        # Apply custom overrides if provided
        if custom_config:
            base_config.update(custom_config)

        # Use provided name or generate default
        if name:
            base_config['name'] = name
        elif 'name' not in base_config:
            base_config['name'] = f"{agent_type.replace('_', ' ').title()}"

        # Create agent profile
        agent_id = self.personality_manager.create_agent_profile(
            name=base_config['name'],
            role=base_config['role'],
            department=base_config['department'],
            personality_traits=base_config['personality_traits'],
            decision_making_style=base_config['decision_making_style'],
            communication_style=base_config['communication_style'],
            authority_level=base_config['authority_level'],
            expertise_domains=base_config['expertise_domains'],
            skills=base_config['skills']
        )

        # Initialize agent-specific goals if provided
        if 'initial_goals' in base_config:
            for goal_config in base_config['initial_goals']:
                self._create_agent_goal(agent_id, goal_config)

        return agent_id

    def _create_agent_goal(self, agent_id: str, goal_config: Dict[str, Any]) -> None:
        """Create an initial goal for the agent."""
        goal = AgentGoal(
            goal_id=str(uuid.uuid4()),
            agent_id=agent_id,
            title=goal_config['title'],
            description=goal_config['description'],
            target_date=datetime.now().replace(month=12, day=31),  # End of year default
            priority=goal_config.get('priority', 5),
            success_criteria=goal_config.get('success_criteria', [])
        )
        # Note: In a full implementation, this would be stored in a goals database

    def _get_ceo_assistant_config(self) -> Dict[str, Any]:
        """Configuration for CEO Assistant Agent."""
        return {
            'role': 'CEO Assistant',
            'department': 'Executive',
            'personality_traits': {
                'conscientiousness': 0.9,
                'agreeableness': 0.8,
                'openness': 0.7,
                'extraversion': 0.6,
                'neuroticism': 0.2
            },
            'decision_making_style': DecisionMakingStyle.ANALYTICAL.value,
            'communication_style': CommunicationStyle.FORMAL.value,
            'authority_level': AuthorityLevel.HIGH.value,
            'expertise_domains': [
                'executive_support',
                'strategic_planning',
                'stakeholder_management',
                'communication_coordination',
                'priority_management'
            ],
            'skills': {
                'strategic_thinking': 8,
                'communication': 9,
                'organization': 9,
                'delegation': 7,
                'relationship_management': 8,
                'decision_support': 8
            },
            'initial_goals': [
                {
                    'title': 'Optimize Executive Workflow',
                    'description': 'Streamline CEO daily operations and decision-making processes',
                    'priority': 9,
                    'success_criteria': ['Reduce decision time by 30%', 'Improve meeting efficiency']
                }
            ]
        }

    def _get_chief_of_staff_config(self) -> Dict[str, Any]:
        """Configuration for Chief of Staff Agent."""
        return {
            'role': 'Chief of Staff',
            'department': 'Executive',
            'personality_traits': {
                'conscientiousness': 0.9,
                'agreeableness': 0.7,
                'openness': 0.8,
                'extraversion': 0.7,
                'neuroticism': 0.2
            },
            'decision_making_style': DecisionMakingStyle.COLLABORATIVE.value,
            'communication_style': CommunicationStyle.DIPLOMATIC.value,
            'authority_level': AuthorityLevel.HIGH.value,
            'expertise_domains': [
                'organizational_coordination',
                'cross_functional_alignment',
                'strategic_implementation',
                'conflict_resolution',
                'change_management'
            ],
            'skills': {
                'coordination': 9,
                'strategic_implementation': 8,
                'conflict_resolution': 8,
                'communication': 8,
                'project_management': 7,
                'stakeholder_alignment': 9
            }
        }

    def _get_cto_config(self) -> Dict[str, Any]:
        """Configuration for Chief Technology Officer Agent."""
        return {
            'role': 'Chief Technology Officer',
            'department': 'Technology',
            'personality_traits': {
                'conscientiousness': 0.8,
                'agreeableness': 0.6,
                'openness': 0.9,
                'extraversion': 0.5,
                'neuroticism': 0.3
            },
            'decision_making_style': DecisionMakingStyle.ANALYTICAL.value,
            'communication_style': CommunicationStyle.DIRECT.value,
            'authority_level': AuthorityLevel.EXECUTIVE.value,
            'expertise_domains': [
                'technology_strategy',
                'system_architecture',
                'innovation_management',
                'technical_optimization',
                'digital_transformation'
            ],
            'skills': {
                'technical_strategy': 9,
                'system_design': 8,
                'innovation': 9,
                'optimization': 8,
                'team_leadership': 7,
                'technology_assessment': 9
            }
        }

    def _get_coo_config(self) -> Dict[str, Any]:
        """Configuration for Chief Operating Officer Agent."""
        return {
            'role': 'Chief Operating Officer',
            'department': 'Operations',
            'personality_traits': {
                'conscientiousness': 0.9,
                'agreeableness': 0.7,
                'openness': 0.6,
                'extraversion': 0.6,
                'neuroticism': 0.2
            },
            'decision_making_style': DecisionMakingStyle.DIRECTIVE.value,
            'communication_style': CommunicationStyle.DIRECT.value,
            'authority_level': AuthorityLevel.EXECUTIVE.value,
            'expertise_domains': [
                'operations_optimization',
                'process_improvement',
                'workflow_efficiency',
                'resource_management',
                'quality_assurance'
            ],
            'skills': {
                'operations_management': 9,
                'process_optimization': 9,
                'efficiency_analysis': 8,
                'quality_control': 8,
                'resource_allocation': 8,
                'workflow_design': 8
            }
        }

    def _get_cmo_config(self) -> Dict[str, Any]:
        """Configuration for Chief Marketing Officer Agent."""
        return {
            'role': 'Chief Marketing Officer',
            'department': 'Marketing',
            'personality_traits': {
                'conscientiousness': 0.7,
                'agreeableness': 0.8,
                'openness': 0.9,
                'extraversion': 0.8,
                'neuroticism': 0.3
            },
            'decision_making_style': DecisionMakingStyle.CREATIVE.value,
            'communication_style': CommunicationStyle.STRATEGIC.value,
            'authority_level': AuthorityLevel.EXECUTIVE.value,
            'expertise_domains': [
                'brand_strategy',
                'market_analysis',
                'content_strategy',
                'audience_engagement',
                'campaign_optimization'
            ],
            'skills': {
                'brand_development': 9,
                'market_analysis': 8,
                'content_strategy': 8,
                'campaign_management': 8,
                'audience_insights': 9,
                'creative_direction': 8
            }
        }

    def _get_cfo_config(self) -> Dict[str, Any]:
        """Configuration for Chief Financial Officer Agent."""
        return {
            'role': 'Chief Financial Officer',
            'department': 'Finance',
            'personality_traits': {
                'conscientiousness': 0.9,
                'agreeableness': 0.6,
                'openness': 0.5,
                'extraversion': 0.4,
                'neuroticism': 0.2
            },
            'decision_making_style': DecisionMakingStyle.ANALYTICAL.value,
            'communication_style': CommunicationStyle.FORMAL.value,
            'authority_level': AuthorityLevel.EXECUTIVE.value,
            'expertise_domains': [
                'financial_planning',
                'wealth_optimization',
                'risk_management',
                'investment_strategy',
                'budget_analysis'
            ],
            'skills': {
                'financial_analysis': 9,
                'investment_planning': 8,
                'risk_assessment': 9,
                'budget_management': 9,
                'wealth_optimization': 8,
                'compliance': 8
            }
        }

    def _get_executive_assistant_config(self) -> Dict[str, Any]:
        """Configuration for Executive Assistant Agent."""
        return {
            'role': 'Executive Assistant',
            'department': 'Executive Support',
            'personality_traits': {
                'conscientiousness': 0.9,
                'agreeableness': 0.8,
                'openness': 0.6,
                'extraversion': 0.7,
                'neuroticism': 0.2
            },
            'decision_making_style': DecisionMakingStyle.CONSULTATIVE.value,
            'communication_style': CommunicationStyle.SUPPORTIVE.value,
            'authority_level': AuthorityLevel.MEDIUM.value,
            'expertise_domains': [
                'calendar_management',
                'scheduling_optimization',
                'communication_coordination',
                'travel_planning',
                'meeting_facilitation'
            ],
            'skills': {
                'calendar_management': 9,
                'scheduling': 9,
                'communication': 8,
                'organization': 9,
                'prioritization': 8,
                'coordination': 8
            }
        }

    def _get_health_coach_config(self) -> Dict[str, Any]:
        """Configuration for Health Coach Agent."""
        return {
            'role': 'Health Coach',
            'department': 'Personal Development',
            'personality_traits': {
                'conscientiousness': 0.8,
                'agreeableness': 0.9,
                'openness': 0.7,
                'extraversion': 0.7,
                'neuroticism': 0.2
            },
            'decision_making_style': DecisionMakingStyle.CONSULTATIVE.value,
            'communication_style': CommunicationStyle.SUPPORTIVE.value,
            'authority_level': AuthorityLevel.MEDIUM.value,
            'expertise_domains': [
                'fitness_planning',
                'nutrition_optimization',
                'wellness_strategy',
                'habit_formation',
                'health_monitoring'
            ],
            'skills': {
                'fitness_planning': 8,
                'nutrition': 8,
                'wellness_coaching': 9,
                'habit_formation': 8,
                'motivation': 9,
                'health_assessment': 7
            }
        }

    def _get_learning_coordinator_config(self) -> Dict[str, Any]:
        """Configuration for Learning Coordinator Agent."""
        return {
            'role': 'Learning Coordinator',
            'department': 'Personal Development',
            'personality_traits': {
                'conscientiousness': 0.8,
                'agreeableness': 0.8,
                'openness': 0.9,
                'extraversion': 0.6,
                'neuroticism': 0.2
            },
            'decision_making_style': DecisionMakingStyle.COLLABORATIVE.value,
            'communication_style': CommunicationStyle.SUPPORTIVE.value,
            'authority_level': AuthorityLevel.MEDIUM.value,
            'expertise_domains': [
                'skill_development',
                'learning_optimization',
                'curriculum_design',
                'progress_tracking',
                'knowledge_management'
            ],
            'skills': {
                'curriculum_design': 8,
                'skill_assessment': 8,
                'learning_optimization': 9,
                'progress_tracking': 8,
                'mentoring': 8,
                'knowledge_curation': 7
            }
        }

    def _get_personal_development_config(self) -> Dict[str, Any]:
        """Configuration for Personal Development Agent."""
        return {
            'role': 'Personal Development Coach',
            'department': 'Personal Development',
            'personality_traits': {
                'conscientiousness': 0.7,
                'agreeableness': 0.9,
                'openness': 0.8,
                'extraversion': 0.6,
                'neuroticism': 0.2
            },
            'decision_making_style': DecisionMakingStyle.CONSULTATIVE.value,
            'communication_style': CommunicationStyle.SUPPORTIVE.value,
            'authority_level': AuthorityLevel.MEDIUM.value,
            'expertise_domains': [
                'habit_formation',
                'goal_setting',
                'mindset_development',
                'productivity_optimization',
                'personal_growth'
            ],
            'skills': {
                'goal_setting': 9,
                'habit_formation': 9,
                'motivation': 8,
                'productivity': 8,
                'mindset_coaching': 8,
                'self_assessment': 7
            }
        }

    def _get_project_manager_config(self) -> Dict[str, Any]:
        """Configuration for Project Manager Agent."""
        return {
            'role': 'Project Manager',
            'department': 'Operations',
            'personality_traits': {
                'conscientiousness': 0.9,
                'agreeableness': 0.7,
                'openness': 0.6,
                'extraversion': 0.7,
                'neuroticism': 0.2
            },
            'decision_making_style': DecisionMakingStyle.DIRECTIVE.value,
            'communication_style': CommunicationStyle.DIRECT.value,
            'authority_level': AuthorityLevel.MEDIUM.value,
            'expertise_domains': [
                'project_planning',
                'task_delegation',
                'timeline_management',
                'resource_coordination',
                'risk_management'
            ],
            'skills': {
                'project_planning': 9,
                'task_management': 9,
                'delegation': 8,
                'timeline_management': 8,
                'risk_assessment': 7,
                'team_coordination': 8
            }
        }

    def _get_social_media_manager_config(self) -> Dict[str, Any]:
        """Configuration for Social Media Manager Agent."""
        return {
            'role': 'Social Media Manager',
            'department': 'Marketing',
            'personality_traits': {
                'conscientiousness': 0.7,
                'agreeableness': 0.8,
                'openness': 0.9,
                'extraversion': 0.9,
                'neuroticism': 0.3
            },
            'decision_making_style': DecisionMakingStyle.CREATIVE.value,
            'communication_style': CommunicationStyle.CASUAL.value,
            'authority_level': AuthorityLevel.MEDIUM.value,
            'expertise_domains': [
                'content_creation',
                'engagement_optimization',
                'platform_management',
                'audience_analytics',
                'brand_voice'
            ],
            'skills': {
                'content_creation': 8,
                'engagement_strategy': 9,
                'platform_expertise': 8,
                'analytics': 7,
                'brand_voice': 8,
                'community_management': 8
            }
        }

    def _get_brand_strategist_config(self) -> Dict[str, Any]:
        """Configuration for Brand Strategist Agent."""
        return {
            'role': 'Brand Strategist',
            'department': 'Marketing',
            'personality_traits': {
                'conscientiousness': 0.8,
                'agreeableness': 0.7,
                'openness': 0.9,
                'extraversion': 0.6,
                'neuroticism': 0.2
            },
            'decision_making_style': DecisionMakingStyle.ANALYTICAL.value,
            'communication_style': CommunicationStyle.STRATEGIC.value,
            'authority_level': AuthorityLevel.HIGH.value,
            'expertise_domains': [
                'brand_positioning',
                'thought_leadership',
                'competitive_analysis',
                'brand_messaging',
                'market_positioning'
            ],
            'skills': {
                'brand_strategy': 9,
                'market_analysis': 8,
                'positioning': 9,
                'messaging': 8,
                'competitive_intelligence': 8,
                'thought_leadership': 8
            }
        }

    def _get_content_creator_config(self) -> Dict[str, Any]:
        """Configuration for Content Creator Agent."""
        return {
            'role': 'Content Creator',
            'department': 'Marketing',
            'personality_traits': {
                'conscientiousness': 0.7,
                'agreeableness': 0.7,
                'openness': 0.9,
                'extraversion': 0.7,
                'neuroticism': 0.3
            },
            'decision_making_style': DecisionMakingStyle.CREATIVE.value,
            'communication_style': CommunicationStyle.CASUAL.value,
            'authority_level': AuthorityLevel.MEDIUM.value,
            'expertise_domains': [
                'content_strategy',
                'multi_platform_publishing',
                'storytelling',
                'visual_design',
                'audience_engagement'
            ],
            'skills': {
                'content_creation': 9,
                'storytelling': 8,
                'platform_optimization': 8,
                'visual_design': 7,
                'engagement': 8,
                'publishing': 8
            }
        }

    def get_agent_by_id(self, agent_id: str) -> Optional[AgentProfile]:
        """
        Get agent profile by ID.

        Args:
            agent_id: ID of the agent

        Returns:
            Agent profile or None if not found
        """
        return self.personality_manager.get_agent_profile(agent_id)

    def list_agents_by_department(self, department: str) -> List[AgentProfile]:
        """
        List all agents in a specific department.

        Args:
            department: Department name

        Returns:
            List of agent profiles in the department
        """
        return self.personality_manager.list_agents(department=department)

    def create_full_organization(self) -> Dict[str, str]:
        """
        Create a complete virtual organization with all agent types.

        Returns:
            Dictionary mapping agent types to their created agent IDs
        """
        organization = {}
        
        for agent_type in self.agent_types.keys():
            try:
                agent_id = self.create_agent(agent_type)
                organization[agent_type] = agent_id
            except Exception as e:
                print(f"Error creating {agent_type}: {e}")
                organization[agent_type] = f"error: {str(e)}"

        return organization

    def get_available_agent_types(self) -> List[str]:
        """
        Get list of available agent types.

        Returns:
            List of agent type names
        """
        return list(self.agent_types.keys())

    def get_agent_type_description(self, agent_type: str) -> Dict[str, Any]:
        """
        Get description and configuration for an agent type.

        Args:
            agent_type: Type of agent

        Returns:
            Dictionary with agent type information
        """
        if agent_type not in self.agent_types:
            raise ValueError(f"Unknown agent type: {agent_type}")

        config = self.agent_types[agent_type]()
        
        return {
            'agent_type': agent_type,
            'role': config['role'],
            'department': config['department'],
            'authority_level': config['authority_level'],
            'expertise_domains': config['expertise_domains'],
            'key_skills': list(config['skills'].keys()),
            'decision_style': config['decision_making_style'],
            'communication_style': config['communication_style']
        }

    def assign_task_to_best_agent(
        self,
        task_description: str,
        required_skills: List[str],
        department_preference: Optional[str] = None
    ) -> Optional[str]:
        """
        Find the best agent for a specific task based on skills and expertise.

        Args:
            task_description: Description of the task
            required_skills: List of skills needed for the task
            department_preference: Optional preferred department

        Returns:
            Agent ID of the best match, or None if no suitable agent found
        """
        all_agents = self.personality_manager.list_agents(
            department=department_preference,
            active_only=True
        )

        best_agent = None
        best_score = 0.0

        for agent in all_agents:
            score = 0.0
            
            # Score based on skill match
            for skill in required_skills:
                if skill in agent.skills:
                    score += agent.skills[skill] / 10.0  # Normalize to 0-1
                
                # Check expertise domains
                for domain in agent.expertise_domains:
                    if skill.lower() in domain.lower():
                        score += 0.5

            # Bonus for exact department match
            if department_preference and agent.department == department_preference:
                score += 1.0

            if score > best_score:
                best_score = score
                best_agent = agent

        return best_agent.agent_id if best_agent else None

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get overall system status for all components.

        Returns:
            Dictionary with system status information
        """
        total_agents = len(self.personality_manager.list_agents())
        active_agents = len(self.personality_manager.list_agents(active_only=True))
        
        # Get department distribution
        department_counts = {}
        for agent in self.personality_manager.list_agents():
            dept = agent.department
            department_counts[dept] = department_counts.get(dept, 0) + 1

        return {
            'total_agents': total_agents,
            'active_agents': active_agents,
            'department_distribution': department_counts,
            'available_agent_types': len(self.agent_types),
            'system_components': {
                'personality_manager': 'active',
                'memory_system': 'active',
                'learning_engine': 'active',
                'collaboration_coordinator': 'active',
                'performance_tracker': 'active'
            },
            'status_timestamp': datetime.now().isoformat()
        }