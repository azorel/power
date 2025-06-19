"""
Enhanced Task Tool: Brain-aware task delegation and management.

Integrates the existing Task tool with consciousness system for intelligent
task delegation based on agent performance history and memory insights.
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from ..brain_database import PowerBrain, TaskRecord
from ..memory_manager import MemoryManager, MemoryContext

logger = logging.getLogger(__name__)


@dataclass
class TaskExecutionContext:
    """Context for task execution with consciousness integration."""
    task_id: str
    agent_performance_history: Dict[str, float]
    relevant_memories: List[Dict[str, Any]]
    estimated_complexity: int
    resource_requirements: Dict[str, Any]
    success_criteria: List[str]


class EnhancedTaskTool:
    """
    Brain-aware task delegation tool that learns from past executions.

    Integrates with the existing agent orchestration system while adding
    consciousness features like memory-based agent selection and learning
    from task outcomes.
    """

    def __init__(self, brain: PowerBrain, memory_manager: MemoryManager,
                 task_delegation_function: Optional[callable] = None):
        """
        Initialize the Enhanced Task Tool.

        Args:
            brain: PowerBrain database instance
            memory_manager: Memory management system
            task_delegation_function: Existing Task tool function
        """
        self.brain = brain
        self.memory_manager = memory_manager
        self.task_delegation_function = task_delegation_function
        self.agent_performance_cache: Dict[str, Dict[str, float]] = {}

    async def delegate_task(self, task_description: str,
                          task_type: str = "development", **kwargs) -> str:
        """
        Delegate a task with consciousness-enhanced agent selection.

        Args:
            task_description: Description of the task
            task_type: Type of task (development, research, testing, etc.)
            **kwargs: Additional arguments (preferred_agent, priority, use_memory)

        Returns:
            Task ID for tracking
        """
        # Extract parameters from kwargs
        preferred_agent = kwargs.get('preferred_agent')
        priority = kwargs.get('priority', 5)
        use_memory = kwargs.get('use_memory', True)
        # Generate unique task ID
        task_id = f"task_{uuid.uuid4().hex[:8]}"

        # Create task execution context
        context = await self._build_execution_context(
            task_id, task_description, task_type, use_memory
        )

        # Select the best agent based on performance history
        selected_agent = await self._select_optimal_agent(
            context, preferred_agent
        )

        # Create enhanced task record
        task_record = TaskRecord(
            task_id=task_id,
            parent_goal_id=None,
            description=task_description,
            task_type=task_type,
            status="pending",
            priority=priority,
            agent_assigned=selected_agent,
            workspace_path=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            completion_signal=None
        )

        # Store task in brain
        self.brain.add_task(task_record)

        # Store task delegation as memory
        if use_memory:
            await self._store_task_memory(task_record, context)

        # Delegate to actual Task tool if available
        if self.task_delegation_function:
            try:
                # Enhance the task description with memory insights
                enhanced_description = await self._enhance_task_description(
                    task_description, context
                )

                # Call the original Task tool
                delegation_result = self.task_delegation_function(
                    description=f"Enhanced Task {task_id}",
                    prompt=enhanced_description
                )

                logger.info("Task %s delegated successfully: %s", task_id, delegation_result)

            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error("Task delegation failed: %s", e)
                self.brain.update_task_status(task_id, "failed", f"Delegation error: {e}")
                return task_id

        # Update task status
        self.brain.update_task_status(task_id, "delegated", f"Assigned to {selected_agent}")

        logger.info("Task %s (%s) delegated to %s", task_id, task_type, selected_agent)
        return task_id

    async def track_task_completion(self, task_id: str, success: bool,  # pylint: disable=too-many-arguments,too-many-positional-arguments
                                  outcome: str, execution_time: float,
                                  quality_score: float = 0.0) -> None:
        """
        Track task completion and update agent performance.

        Args:
            task_id: Task identifier
            success: Whether task completed successfully
            outcome: Description of the outcome
            execution_time: Time taken to complete
            quality_score: Quality score (0.0-1.0)
        """
        # Update task status in brain
        status = "completed" if success else "failed"
        self.brain.update_task_status(task_id, status, outcome)

        # Get task details
        next_task = self.brain.get_next_task()  # Simplified - would need proper task lookup

        if next_task and next_task.task_id == task_id:
            agent_id = next_task.agent_assigned
            task_type = next_task.task_type

            # Update agent performance
            await self._update_agent_performance(
                agent_id, task_type, success, execution_time, quality_score
            )

            # Store outcome as memory
            await self._store_outcome_memory(next_task, success, outcome, quality_score)

            logger.info("Task %s completion tracked: %s", task_id, status)

    async def get_task_insights(self, task_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get insights about task execution patterns and agent performance.

        Args:
            task_type: Optional filter by task type

        Returns:
            Dictionary containing task insights
        """
        # Get task statistics from brain
        brain_stats = self.brain.get_brain_stats()

        # Get agent performance data
        agent_insights = {}
        for agent_id, performance in self.agent_performance_cache.items():
            if task_type:
                type_performance = performance.get(f"{task_type}_success_rate", 0.0)
                agent_insights[agent_id] = {
                    "task_type_success_rate": type_performance,
                    "avg_execution_time": performance.get(f"{task_type}_avg_time", 0.0)
                }
            else:
                agent_insights[agent_id] = {
                    "overall_success_rate": performance.get("overall_success_rate", 0.0),
                    "total_tasks": performance.get("total_tasks", 0)
                }

        # Get memory insights related to tasks
        task_memories = self.memory_manager.search_memories(
            query=f"task execution {task_type}" if task_type else "task execution",
            memory_type="task_execution",
            limit=10
        )

        insights = {
            "total_tasks": brain_stats.get("task_queue_count", 0),
            "task_status_distribution": brain_stats.get("task_status", {}),
            "agent_performance": agent_insights,
            "recent_task_patterns": [
                {
                    "content_preview": memory.memory_record.content[:100],
                    "confidence": memory.memory_record.confidence_score,
                    "similarity": memory.similarity_score
                }
                for memory in task_memories[:5]
            ],
            "top_performing_agents": self._get_top_performing_agents(task_type),
            "failure_patterns": await self._analyze_failure_patterns(task_type)
        }

        return insights

    async def _build_execution_context(self, task_id: str, task_description: str,
                                     task_type: str, use_memory: bool) -> TaskExecutionContext:
        """Build execution context for task delegation."""
        # Get relevant memories if enabled
        relevant_memories = []
        if use_memory:
            memory_results = self.memory_manager.search_memories(
                query=f"{task_type} {task_description}",
                memory_type="task_execution",
                limit=5
            )
            relevant_memories = [
                {
                    "content": result.memory_record.content,
                    "similarity": result.similarity_score,
                    "confidence": result.memory_record.confidence_score
                }
                for result in memory_results
            ]

        # Estimate complexity based on task description
        complexity = self._estimate_task_complexity(task_description, task_type)

        # Get agent performance history
        performance_history = await self._get_agent_performance_history(task_type)

        return TaskExecutionContext(
            task_id=task_id,
            agent_performance_history=performance_history,
            relevant_memories=relevant_memories,
            estimated_complexity=complexity,
            resource_requirements={"estimated_time": complexity * 10},
            success_criteria=["Task completed successfully", "Quality standards met"]
        )

    async def _select_optimal_agent(self, context: TaskExecutionContext,
                                   preferred_agent: Optional[str]) -> str:
        """Select the best agent for the task based on performance history."""
        if preferred_agent and preferred_agent in context.agent_performance_history:
            return preferred_agent

        # Select agent with highest success rate for this task type
        if context.agent_performance_history:
            best_agent = max(
                context.agent_performance_history.keys(),
                key=lambda agent: context.agent_performance_history[agent]
            )
            return best_agent

        # Default agent selection
        return "general_agent"

    async def _enhance_task_description(self, original_description: str,
                                      context: TaskExecutionContext) -> str:
        """Enhance task description with memory insights."""
        enhanced = f"""
TASK: {original_description}

CONSCIOUSNESS ENHANCEMENT:
Task ID: {context.task_id}
Estimated Complexity: {context.estimated_complexity}/10

RELEVANT PAST EXPERIENCE:
"""

        # Add relevant memories
        for i, memory in enumerate(context.relevant_memories[:3]):
            enhanced += f"""
Experience {i+1} (similarity: {memory['similarity']:.2f}):
{memory['content'][:200]}...
"""

        enhanced += f"""

SUCCESS CRITERIA:
{chr(10).join(f"- {criterion}" for criterion in context.success_criteria)}

RESOURCE ESTIMATION:
{chr(10).join(f"- {key}: {value}" for key, value in context.resource_requirements.items())}

Execute this task with full consciousness and memory integration.
End with: "Task complete and ready for next step"
"""

        return enhanced

    async def _store_task_memory(self, task_record: TaskRecord,
                               context: TaskExecutionContext) -> None:
        """Store task delegation as memory."""
        memory_content = f"""
Task Delegation: {task_record.task_id}
Type: {task_record.task_type}
Description: {task_record.description}
Agent: {task_record.agent_assigned}
Priority: {task_record.priority}
Complexity: {context.estimated_complexity}
Relevant Experience: {len(context.relevant_memories)} similar tasks found
"""

        memory_context = MemoryContext(
            user_id="system",
            session_id="task_delegation",
            task_id=task_record.task_id,
            agent_id="enhanced_task_tool",
            conversation_context={"delegation": True}
        )

        self.memory_manager.store_memory(
            content=memory_content,
            memory_type="task_execution",
            context=memory_context,
            confidence_score=0.9
        )

    async def _store_outcome_memory(self, task_record: TaskRecord, success: bool,
                                  outcome: str, quality_score: float) -> None:
        """Store task outcome as memory."""
        memory_content = f"""
Task Completion: {task_record.task_id}
Type: {task_record.task_type}
Agent: {task_record.agent_assigned}
Success: {success}
Quality Score: {quality_score:.2f}
Outcome: {outcome}
Description: {task_record.description}
"""

        memory_context = MemoryContext(
            user_id="system",
            session_id="task_completion",
            task_id=task_record.task_id,
            agent_id=task_record.agent_assigned,
            conversation_context={"completion": True, "success": success}
        )

        self.memory_manager.store_memory(
            content=memory_content,
            memory_type="task_execution",
            context=memory_context,
            confidence_score=quality_score
        )

    def _estimate_task_complexity(self, description: str, task_type: str) -> int:
        """Estimate task complexity on a scale of 1-10."""
        complexity_indicators = {
            "simple": 1, "basic": 2, "implement": 3, "create": 4, "develop": 5,
            "complex": 6, "advanced": 7, "sophisticated": 8, "comprehensive": 9,
            "revolutionary": 10
        }

        description_lower = description.lower()
        max_complexity = 1

        for indicator, score in complexity_indicators.items():
            if indicator in description_lower:
                max_complexity = max(max_complexity, score)

        # Adjust based on task type
        type_modifiers = {
            "research": 1.2,
            "development": 1.0,
            "testing": 0.8,
            "analysis": 1.1,
            "integration": 1.3
        }

        modifier = type_modifiers.get(task_type, 1.0)
        final_complexity = min(10, int(max_complexity * modifier))

        return final_complexity

    async def _get_agent_performance_history(self, task_type: str) -> Dict[str, float]:
        """Get agent performance history for the task type."""
        # This would query the agent_performance table in the brain
        # For now, return cached performance data
        performance = {}

        for agent_id, agent_stats in self.agent_performance_cache.items():
            type_key = f"{task_type}_success_rate"
            if type_key in agent_stats:
                performance[agent_id] = agent_stats[type_key]

        return performance

    async def _update_agent_performance(self, agent_id: str, task_type: str,  # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
                                      success: bool, execution_time: float,
                                      quality_score: float = 0.0) -> None:
        """Update agent performance statistics."""
        _ = quality_score  # Quality score reserved for future use
        if agent_id not in self.agent_performance_cache:
            self.agent_performance_cache[agent_id] = {}

        agent_stats = self.agent_performance_cache[agent_id]

        # Update task type specific stats
        type_key = f"{task_type}_success_rate"
        count_key = f"{task_type}_count"
        time_key = f"{task_type}_avg_time"

        current_count = agent_stats.get(count_key, 0)
        current_success_rate = agent_stats.get(type_key, 0.0)
        current_avg_time = agent_stats.get(time_key, 0.0)

        # Update counts
        new_count = current_count + 1

        # Update success rate
        if success:
            new_success_rate = ((current_success_rate * current_count) + 1.0) / new_count
        else:
            new_success_rate = (current_success_rate * current_count) / new_count

        # Update average time
        new_avg_time = ((current_avg_time * current_count) + execution_time) / new_count

        # Store updated stats
        agent_stats[count_key] = new_count
        agent_stats[type_key] = new_success_rate
        agent_stats[time_key] = new_avg_time

        # Update overall stats
        total_tasks = agent_stats.get("total_tasks", 0) + 1
        overall_success = agent_stats.get("overall_success_rate", 0.0)

        if success:
            new_overall = ((overall_success * (total_tasks - 1)) + 1.0) / total_tasks
        else:
            new_overall = (overall_success * (total_tasks - 1)) / total_tasks

        agent_stats["total_tasks"] = total_tasks
        agent_stats["overall_success_rate"] = new_overall

    def _get_top_performing_agents(self, task_type: Optional[str]) -> List[Dict[str, Any]]:
        """Get top performing agents for the task type."""
        if task_type:
            type_key = f"{task_type}_success_rate"
            agents = [
                {
                    "agent_id": agent_id,
                    "success_rate": stats.get(type_key, 0.0),
                    "task_count": stats.get(f"{task_type}_count", 0)
                }
                for agent_id, stats in self.agent_performance_cache.items()
                if type_key in stats
            ]
        else:
            agents = [
                {
                    "agent_id": agent_id,
                    "success_rate": stats.get("overall_success_rate", 0.0),
                    "task_count": stats.get("total_tasks", 0)
                }
                for agent_id, stats in self.agent_performance_cache.items()
            ]

        # Sort by success rate and return top 5
        agents.sort(key=lambda x: x["success_rate"], reverse=True)
        return agents[:5]

    async def _analyze_failure_patterns(self, task_type: Optional[str]) -> List[str]:
        """Analyze failure patterns from memory."""
        # Search for failed task memories
        query = f"failed {task_type}" if task_type else "failed task"
        failure_memories = self.memory_manager.search_memories(
            query=query,
            memory_type="task_execution",
            limit=10
        )

        # Extract common failure patterns (simplified)
        patterns = []
        for memory_result in failure_memories:
            content = memory_result.memory_record.content.lower()
            if "timeout" in content:
                patterns.append("Task timeouts")
            elif "dependency" in content:
                patterns.append("Dependency issues")
            elif "complexity" in content:
                patterns.append("Underestimated complexity")
            elif "resource" in content:
                patterns.append("Resource constraints")

        # Return unique patterns
        return list(set(patterns))
