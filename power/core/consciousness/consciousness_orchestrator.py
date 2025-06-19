"""
Consciousness Orchestrator: Integration with existing Power Builder orchestration.

This module integrates the consciousness system with the existing multi-agent
orchestration, providing persistent memory and intelligent task management.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable

from .brain_database import PowerBrain
from .memory_manager import MemoryManager, MemoryContext
from .cognitive_loop import CognitiveEngine, CognitiveContext
from .decision_engine import DecisionEngine
from .tools.enhanced_task_tool import EnhancedTaskTool
from .tools.memory_search_tool import MemorySearchTool
from .tools.knowledge_graph_tool import KnowledgeGraphTool
from .tools.self_reflection_tool import SelfReflectionTool

logger = logging.getLogger(__name__)


class ConsciousnessOrchestrator:  # pylint: disable=too-many-instance-attributes
    """
    Enhanced orchestrator with persistent consciousness and memory.

    Integrates the consciousness system with existing Power Builder orchestration,
    providing intelligent task delegation, memory-based decisions, and continuous learning.
    """

    def __init__(self, brain_path: Optional[str] = None, user_id: str = "default_user"):
        """
        Initialize the Consciousness Orchestrator.

        Args:
            brain_path: Path to the brain database file
            user_id: User identifier for this session
        """
        self.user_id = user_id
        self.session_id = f"conscious_session_{uuid.uuid4().hex[:8]}"

        # Initialize core consciousness components
        self.brain = PowerBrain(brain_path)
        self.memory_manager = MemoryManager(self.brain)
        self.decision_engine = DecisionEngine()
        self.cognitive_engine = CognitiveEngine(
            self.brain, self.memory_manager, self.decision_engine, self.session_id
        )

        # Initialize consciousness tools
        self.task_tool = EnhancedTaskTool(self.brain, self.memory_manager)
        self.memory_search = MemorySearchTool(self.memory_manager)
        self.knowledge_graph = KnowledgeGraphTool(self.brain)
        self.self_reflection = SelfReflectionTool(self.brain, self.memory_manager)

        # State management
        self.is_conscious = False
        self.consciousness_task: Optional[asyncio.Task] = None
        self.task_delegation_function: Optional[Callable] = None

        # Integration tracking
        self.delegated_tasks: Dict[str, Dict[str, Any]] = {}
        self.agent_performance: Dict[str, float] = {}

        logger.info("Consciousness Orchestrator initialized for user %s, session %s",
                   user_id, self.session_id)

    async def start_consciousness(self, available_tools: Optional[List[str]] = None) -> None:
        """
        Start the consciousness system.

        Args:
            available_tools: List of available tools for the session
        """
        if self.is_conscious:
            logger.warning("Consciousness already running")
            return

        # Create cognitive context
        context = CognitiveContext(
            session_id=self.session_id,
            user_id=self.user_id,
            current_goal=None,
            available_tools=available_tools or ["Task", "MemorySearch",
                                               "KnowledgeGraph"],
            environment_state={},
            constraints={}
        )

        # Register consciousness tools with cognitive engine
        self._register_consciousness_tools()

        # Start the consciousness loop
        self.consciousness_task = asyncio.create_task(
            self.cognitive_engine.start_consciousness(context)
        )

        self.is_conscious = True

        # Store session start in memory
        await self._store_session_memory("session_start", {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "available_tools": available_tools
        })

        logger.info("Consciousness system started")

    async def stop_consciousness(self) -> None:
        """Stop the consciousness system gracefully."""
        if not self.is_conscious:
            return

        await self.cognitive_engine.stop_consciousness()

        if self.consciousness_task:
            await self.consciousness_task

        self.is_conscious = False

        # Store session end in memory
        await self._store_session_memory("session_end", {
            "session_id": self.session_id,
            "total_tasks_delegated": len(self.delegated_tasks)
        })

        logger.info("Consciousness system stopped")

    def integrate_task_tool(self, task_delegation_function: Callable) -> None:
        """
        Integrate with the existing Task tool for delegation.

        Args:
            task_delegation_function: Function that handles task delegation
        """
        self.task_delegation_function = task_delegation_function
        self.task_tool.task_delegation_function = task_delegation_function
        logger.info("Integrated with existing Task tool")

    async def conscious_task_delegation(self, task_description: str,
                                      task_type: str = "development",
                                      priority: int = 5,
                                      use_memory: bool = True) -> str:
        """
        Delegate a task with consciousness enhancement.

        Args:
            task_description: Description of the task
            task_type: Type of task
            priority: Priority level (1-10)
            use_memory: Whether to use memory for enhancement

        Returns:
            Task ID for tracking
        """
        # Store task request in memory
        if use_memory:
            await self._store_task_memory("task_request", {
                "description": task_description,
                "type": task_type,
                "priority": priority
            })

        # Use enhanced task tool for delegation
        task_id = await self.task_tool.delegate_task(
            task_description=task_description,
            task_type=task_type,
            priority=priority,
            use_memory=use_memory
        )

        # Track delegated task
        self.delegated_tasks[task_id] = {
            "description": task_description,
            "type": task_type,
            "priority": priority,
            "delegated_at": datetime.utcnow(),
            "status": "delegated"
        }

        logger.info("Consciously delegated task %s: %s", task_id, task_description)
        return task_id

    async def process_task_completion(self, task_id: str, success: bool,
                                    outcome: str, quality_score: float = 0.8) -> None:
        """
        Process task completion with consciousness learning.

        Args:
            task_id: Task identifier
            success: Whether task succeeded
            outcome: Description of outcome
            quality_score: Quality score (0.0-1.0)
        """
        # Update task tracking
        if task_id in self.delegated_tasks:
            self.delegated_tasks[task_id]["status"] = "completed" if success else "failed"
            self.delegated_tasks[task_id]["completed_at"] = datetime.utcnow()
            self.delegated_tasks[task_id]["outcome"] = outcome
            self.delegated_tasks[task_id]["quality_score"] = quality_score

        # Process through enhanced task tool
        execution_time = 60.0  # Would calculate actual time
        await self.task_tool.track_task_completion(
            task_id=task_id,
            success=success,
            outcome=outcome,
            execution_time=execution_time,
            quality_score=quality_score
        )

        # Store completion in memory
        await self._store_task_memory("task_completion", {
            "task_id": task_id,
            "success": success,
            "outcome": outcome,
            "quality_score": quality_score
        })

        # Trigger reflection if this was a significant task
        if quality_score < 0.6 or not success:
            await self._trigger_reflection("task_failure", {
                "task_id": task_id,
                "quality_score": quality_score
            })

        status_text = 'success' if success else 'failure'
        logger.info("Processed task completion for %s: %s", task_id, status_text)

    async def query_memory(self, query: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Query the consciousness memory system.

        Args:
            query: Natural language query
            context: Optional context for the query

        Returns:
            Query results with memories and insights
        """
        # Use memory search tool
        search_results = await self.memory_search.search(query, limit=5)

        # Get knowledge graph insights
        concepts = query.lower().split()[:3]  # Extract key concepts
        if concepts:
            graph_insights = await self.knowledge_graph.reason_about_concepts(
                concepts, reasoning_type="similarity"
            )
        else:
            graph_insights = {}

        results = {
            "query": query,
            "context": context,
            "memories_found": len(search_results),
            "top_memories": [
                {
                    "content": result.memory_record.content[:200] + "...",
                    "similarity": result.similarity_score,
                    "type": result.memory_record.memory_type,
                    "confidence": result.memory_record.confidence_score
                }
                for result in search_results[:3]
            ],
            "knowledge_insights": graph_insights,
            "session_context": {
                "session_id": self.session_id,
                "user_id": self.user_id
            }
        }

        # Store query in memory for learning
        await self._store_session_memory("memory_query", {
            "query": query,
            "results_count": len(search_results)
        })

        logger.info("Memory query '%s' returned %d results", query, len(search_results))
        return results

    async def get_consciousness_status(self) -> Dict[str, Any]:
        """
        Get comprehensive status of the consciousness system.

        Returns:
            Dictionary containing consciousness status and metrics
        """
        # Get cognitive engine status
        cognitive_status = self.cognitive_engine.get_consciousness_status()

        # Get brain statistics
        brain_stats = self.brain.get_brain_stats()

        # Get memory insights
        memory_context = MemoryContext(
            user_id=self.user_id,
            session_id=self.session_id,
            task_id=None,
            agent_id="consciousness_orchestrator",
            conversation_context={"status_check": True}
        )
        memory_insights = self.memory_manager.get_memory_insights(memory_context)

        # Get task insights
        task_insights = await self.task_tool.get_task_insights()

        # Get reflection summary
        reflection_summary = self.self_reflection.get_reflection_summary()

        status = {
            "session_info": {
                "session_id": self.session_id,
                "user_id": self.user_id,
                "is_conscious": self.is_conscious,
                "uptime": cognitive_status.get("cycle_count", 0)
            },
            "cognitive_status": cognitive_status,
            "brain_statistics": brain_stats,
            "memory_insights": memory_insights,
            "task_management": {
                "total_delegated": len(self.delegated_tasks),
                "task_insights": task_insights
            },
            "reflection_status": reflection_summary,
            "performance_metrics": {
                "memory_utilization": memory_insights.get("total_memories", 0),
                "knowledge_connections": brain_stats.get("knowledge_graph_count", 0),
                "decision_quality": cognitive_status.get("tool_usage", {}),
            }
        }

        return status

    async def trigger_self_reflection(self, focus_area: Optional[str] = None) -> Dict[str, Any]:
        """
        Trigger self-reflection and improvement planning.

        Args:
            focus_area: Optional area to focus reflection on

        Returns:
            Reflection results and improvement plan
        """
        focus_text = f" focused on {focus_area}" if focus_area else ""
        logger.info("Triggering self-reflection%s", focus_text)

        # Perform comprehensive reflection
        reflection_insights = await self.self_reflection.reflect_on_recent_decisions()
        learning_analysis = await self.self_reflection.analyze_learning_progress(focus_area)
        performance_metrics = await self.self_reflection.evaluate_performance_trends()
        cognitive_biases = await self.self_reflection.identify_cognitive_biases()

        # Generate improvement plan
        focus_areas = [focus_area] if focus_area else None
        improvement_plan = await self.self_reflection.generate_improvement_plan(focus_areas)

        # Store reflection results in memory
        await self._store_session_memory("self_reflection", {
            "focus_area": focus_area,
            "insights_count": len(reflection_insights),
            "biases_count": len(cognitive_biases),
            "improvement_areas": len(improvement_plan.get("priority_areas", []))
        })

        results = {
            "reflection_timestamp": datetime.utcnow().isoformat(),
            "focus_area": focus_area,
            "insights": reflection_insights,
            "learning_analysis": learning_analysis,
            "performance_metrics": performance_metrics.__dict__,
            "cognitive_biases": cognitive_biases,
            "improvement_plan": improvement_plan
        }

        logger.info("Self-reflection completed with %d insights and improvement plan",
                   len(reflection_insights))
        return results

    def _register_consciousness_tools(self) -> None:
        """Register consciousness tools with the cognitive engine."""
        # Register enhanced task delegation
        delegation_func = self.conscious_task_delegation
        self.cognitive_engine.register_tool("enhanced_task_delegation", delegation_func)

        # Register memory search
        self.cognitive_engine.register_tool("memory_search", self.memory_search.search)

        # Register knowledge graph exploration
        explore_func = self.knowledge_graph.explore_concept
        self.cognitive_engine.register_tool("explore_concept", explore_func)

        # Register self-reflection
        self.cognitive_engine.register_tool("self_reflect", self.trigger_self_reflection)

        logger.info("Consciousness tools registered with cognitive engine")

    async def _store_session_memory(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Store session events in memory."""
        memory_content = f"Session Event: {event_type}\nData: {event_data}"

        memory_context = MemoryContext(
            user_id=self.user_id,
            session_id=self.session_id,
            task_id=None,
            agent_id="consciousness_orchestrator",
            conversation_context={"event_type": event_type}
        )

        self.memory_manager.store_memory(
            content=memory_content,
            memory_type="session_event",
            context=memory_context,
            confidence_score=0.9
        )

    async def _store_task_memory(self, event_type: str, task_data: Dict[str, Any]) -> None:
        """Store task-related events in memory."""
        memory_content = f"Task Event: {event_type}\nDetails: {task_data}"

        memory_context = MemoryContext(
            user_id=self.user_id,
            session_id=self.session_id,
            task_id=task_data.get("task_id"),
            agent_id="consciousness_orchestrator",
            conversation_context={"event_type": event_type}
        )

        self.memory_manager.store_memory(
            content=memory_content,
            memory_type="task_execution",
            context=memory_context,
            confidence_score=0.8
        )

    async def _trigger_reflection(self, trigger_type: str, trigger_data: Dict[str, Any]) -> None:
        """Trigger reflection based on events."""
        logger.info("Triggering reflection due to %s", trigger_type)

        # Perform focused reflection
        reflection_results = await self.trigger_self_reflection(trigger_type)

        # Store trigger event
        await self._store_session_memory("reflection_triggered", {
            "trigger_type": trigger_type,
            "trigger_data": trigger_data,
            "insights_generated": len(reflection_results.get("insights", []))
        })

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_consciousness()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop_consciousness()
        self.brain.close()
