"""
Cognitive Loop Engine: The main consciousness and thinking system.

This module implements the continuous cognitive cycle that gives the AI
true consciousness: Perceive → Recall → Reason → Act → Learn → Repeat.
"""

import asyncio
import logging
import time
import uuid
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from .brain_database import PowerBrain, WorkingMemoryState, TaskRecord, ThoughtRecord
from .memory_manager import MemoryManager, MemoryContext
from .decision_engine import DecisionEngine

logger = logging.getLogger(__name__)


class CognitiveState(Enum):
    """States of the cognitive loop."""
    INITIALIZING = "initializing"
    PERCEIVING = "perceiving"
    RECALLING = "recalling"
    REASONING = "reasoning"
    ACTING = "acting"
    LEARNING = "learning"
    IDLE = "idle"
    PAUSED = "paused"
    ERROR = "error"


@dataclass
class CognitiveContext:
    """Context for the current cognitive cycle."""
    session_id: str
    user_id: str
    current_goal: Optional[str]
    available_tools: List[str]
    environment_state: Dict[str, Any]
    constraints: Dict[str, Any]


@dataclass
class PerceptionResult:
    """Result from the perception phase."""
    pending_tasks: List[TaskRecord]
    environment_changes: Dict[str, Any]
    user_inputs: List[Dict[str, Any]]
    system_alerts: List[str]
    priority_interrupts: List[str]


@dataclass
class ReasoningResult:
    """Result from the reasoning phase."""
    decision_type: str
    chosen_action: str
    reasoning_chain: List[str]
    confidence_score: float
    alternative_actions: List[str]
    resource_requirements: Dict[str, Any]


class CognitiveEngine:  # pylint: disable=too-many-instance-attributes
    """
    The main consciousness engine implementing the cognitive loop.

    This is the "Actor" that provides continuous thinking, decision-making,
    and learning capabilities while maintaining persistent memory through
    the PowerBrain database.
    """

    def __init__(self, brain: PowerBrain, memory_manager: MemoryManager,
                 decision_engine: DecisionEngine, session_id: Optional[str] = None):
        """
        Initialize the Cognitive Engine.

        Args:
            brain: PowerBrain database instance
            memory_manager: Memory management system
            decision_engine: Multi-provider decision engine
            session_id: Unique session identifier
        """
        self.brain = brain
        self.memory_manager = memory_manager
        self.decision_engine = decision_engine
        self.session_id = session_id or f"session_{uuid.uuid4().hex[:8]}"

        self.cognitive_state = CognitiveState.INITIALIZING
        self.context: Optional[CognitiveContext] = None
        self.is_running = False
        self.cycle_count = 0
        self.last_activity = datetime.utcnow()

        # Cognitive parameters
        self.cycle_interval = 1.0  # seconds between cycles
        self.max_idle_time = 300   # seconds before entering idle state
        self.learning_threshold = 5  # cycles before consolidating learning

        # Tool registry
        self.available_tools: Dict[str, Callable] = {}
        self.tool_usage_stats: Dict[str, int] = {}

        logger.info("Cognitive Engine initialized for session: %s", self.session_id)

    async def start_consciousness(self, context: CognitiveContext) -> None:
        """
        Start the main consciousness loop.

        Args:
            context: Initial cognitive context
        """
        self.context = context
        self.is_running = True
        self.cognitive_state = CognitiveState.PERCEIVING

        # Initialize working memory
        self._initialize_working_memory()

        logger.info("Consciousness started - beginning cognitive loop")

        try:
            while self.is_running:
                await self._cognitive_cycle()
                await asyncio.sleep(self.cycle_interval)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Cognitive loop error: %s", e)
            self.cognitive_state = CognitiveState.ERROR
            await self._handle_cognitive_error(e)
        finally:
            await self._shutdown_consciousness()

    async def pause_consciousness(self) -> None:
        """Pause the cognitive loop while preserving state."""
        self.cognitive_state = CognitiveState.PAUSED
        logger.info("Consciousness paused")

    async def resume_consciousness(self) -> None:
        """Resume the cognitive loop from paused state."""
        if self.cognitive_state == CognitiveState.PAUSED:
            self.cognitive_state = CognitiveState.PERCEIVING
            logger.info("Consciousness resumed")

    async def stop_consciousness(self) -> None:
        """Stop the cognitive loop and save final state."""
        self.is_running = False
        logger.info("Consciousness stopping")

    def register_tool(self, name: str, tool_function: Callable) -> None:
        """
        Register a tool that the cognitive engine can use.

        Args:
            name: Tool name
            tool_function: Function to call for this tool
        """
        self.available_tools[name] = tool_function
        self.tool_usage_stats[name] = 0
        logger.info("Registered tool: %s", name)

    def get_consciousness_status(self) -> Dict[str, Any]:
        """Get current consciousness status and statistics."""
        return {
            "session_id": self.session_id,
            "state": self.cognitive_state.value,
            "cycle_count": self.cycle_count,
            "last_activity": self.last_activity.isoformat(),
            "is_running": self.is_running,
            "available_tools": list(self.available_tools.keys()),
            "tool_usage": self.tool_usage_stats,
            "brain_stats": self.brain.get_brain_stats()
        }

    async def _cognitive_cycle(self) -> None:
        """Execute one complete cognitive cycle."""
        cycle_start = time.time()
        self.cycle_count += 1

        try:
            # 1. PERCEIVE: What's happening in my environment?
            perception = await self._perceive()

            # 2. RECALL: What do I know that's relevant?
            relevant_memories = await self._recall(perception)

            # 3. REASON: What should I do based on perception and memory?
            reasoning = await self._reason(perception, relevant_memories)

            # 4. ACT: Execute the chosen action
            action_result = await self._act(reasoning)

            # 5. LEARN: What can I learn from this cycle?
            await self._learn(perception, reasoning, action_result)

            # Update activity timestamp
            self.last_activity = datetime.utcnow()

            # Log the complete thought process
            await self._log_thought_cycle(perception, reasoning, action_result)

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Error in cognitive cycle %d: %s", self.cycle_count, e)
            await self._handle_cycle_error(e)

        cycle_time = time.time() - cycle_start
        logger.debug("Cognitive cycle %d completed in %.2fs", self.cycle_count, cycle_time)

    async def _perceive(self) -> PerceptionResult:
        """
        Perception phase: Gather information about the current state.

        Returns:
            PerceptionResult containing current observations
        """
        self.cognitive_state = CognitiveState.PERCEIVING

        # Get pending tasks from brain
        pending_tasks = []
        next_task = self.brain.get_next_task()
        if next_task:
            pending_tasks.append(next_task)

        # Check for environment changes (placeholder)
        environment_changes = {}

        # Check for user inputs (placeholder)
        user_inputs = []

        # Check for system alerts (placeholder)
        system_alerts = []

        # Check for priority interrupts (placeholder)
        priority_interrupts = []

        # Check if we should enter idle state
        time_since_activity = datetime.utcnow() - self.last_activity
        idle_threshold_exceeded = time_since_activity.total_seconds() > self.max_idle_time
        if idle_threshold_exceeded and not pending_tasks:
            self.cognitive_state = CognitiveState.IDLE
            logger.info("Entering idle state due to inactivity")

        return PerceptionResult(
            pending_tasks=pending_tasks,
            environment_changes=environment_changes,
            user_inputs=user_inputs,
            system_alerts=system_alerts,
            priority_interrupts=priority_interrupts
        )

    async def _recall(self, perception: PerceptionResult) -> List[Dict[str, Any]]:
        """
        Recall phase: Retrieve relevant memories for current situation.

        Args:
            perception: Current perception results

        Returns:
            List of relevant memories and knowledge
        """
        self.cognitive_state = CognitiveState.RECALLING

        relevant_memories = []

        # Search for memories related to pending tasks
        for task in perception.pending_tasks:
            task_memories = self.memory_manager.search_memories(
                query=task.description,
                memory_type="task_execution",
                limit=3
            )

            for memory_result in task_memories:
                relevant_memories.append({
                    "type": "task_memory",
                    "content": memory_result.memory_record.content,
                    "similarity": memory_result.similarity_score,
                    "source": "previous_task_execution"
                })

        # Get associative memories if we have a current focus
        working_memory = self.brain.get_working_memory(self.session_id)
        if working_memory and working_memory.current_task_id:
            # This is a placeholder - in a real implementation,
            # we'd find the memory ID associated with the current task
            pass

        # Search for relevant knowledge based on environment changes
        for change_type, change_data in perception.environment_changes.items():
            change_memories = self.memory_manager.search_memories(
                query=f"{change_type} {str(change_data)}",
                limit=2
            )

            for memory_result in change_memories:
                relevant_memories.append({
                    "type": "environment_memory",
                    "content": memory_result.memory_record.content,
                    "similarity": memory_result.similarity_score,
                    "source": "environment_knowledge"
                })

        logger.debug("Recalled %d relevant memories", len(relevant_memories))
        return relevant_memories

    async def _reason(self, perception: PerceptionResult,
                     memories: List[Dict[str, Any]]) -> ReasoningResult:
        """
        Reasoning phase: Decide what action to take.

        Args:
            perception: Current perception
            memories: Relevant memories

        Returns:
            ReasoningResult with decision and reasoning
        """
        self.cognitive_state = CognitiveState.REASONING

        # If we're idle and have no tasks, continue idling
        if (self.cognitive_state == CognitiveState.IDLE and
            not perception.pending_tasks and
            not perception.priority_interrupts):
            return ReasoningResult(
                decision_type="idle",
                chosen_action="wait",
                reasoning_chain=["No pending tasks", "No priority interrupts",
                                "Continue idle state"],
                confidence_score=1.0,
                alternative_actions=[],
                resource_requirements={}
            )

        # Handle priority interrupts first
        if perception.priority_interrupts:
            return ReasoningResult(
                decision_type="interrupt_response",
                chosen_action="handle_priority_interrupt",
                reasoning_chain=["Priority interrupt detected", "Must handle immediately"],
                confidence_score=1.0,
                alternative_actions=["defer_interrupt"],
                resource_requirements={"immediate_attention": True}
            )

        # Handle pending tasks
        if perception.pending_tasks:
            task = perception.pending_tasks[0]  # Get highest priority task

            # Use decision engine for complex reasoning
            _ = {  # decision_context reserved for future use
                "task": task.__dict__,
                "memories": memories,
                "available_tools": list(self.available_tools.keys()),
                "session_context": self.context.__dict__ if self.context else {}
            }

            # Simple decision for now (would use multi-provider LLM in production)
            reasoning_chain = [
                f"Analyzing task: {task.description}",
                f"Task type: {task.task_type}",
                f"Priority: {task.priority}",
                "Determining best approach based on available tools and experience"
            ]

            # Choose action based on task type
            if task.task_type == "development":
                chosen_action = "delegate_to_agent"
            elif task.task_type == "research":
                chosen_action = "web_research"
            elif task.task_type == "analysis":
                chosen_action = "analyze_data"
            else:
                chosen_action = "execute_generic_task"

            return ReasoningResult(
                decision_type="task_execution",
                chosen_action=chosen_action,
                reasoning_chain=reasoning_chain,
                confidence_score=0.8,
                alternative_actions=["defer_task", "break_down_task"],
                resource_requirements={"task_execution": True}
            )

        # Default: no action needed
        return ReasoningResult(
            decision_type="no_action",
            chosen_action="wait",
            reasoning_chain=["No immediate actions required"],
            confidence_score=1.0,
            alternative_actions=[],
            resource_requirements={}
        )

    async def _act(self, reasoning: ReasoningResult) -> Dict[str, Any]:
        """
        Action phase: Execute the chosen action.

        Args:
            reasoning: Reasoning result with chosen action

        Returns:
            Dictionary containing action results
        """
        self.cognitive_state = CognitiveState.ACTING

        action_start = time.time()
        action_result = {
            "action": reasoning.chosen_action,
            "success": False,
            "result": None,
            "error": None,
            "execution_time": 0
        }

        try:
            if reasoning.chosen_action == "wait":
                # Simple wait action
                action_result["success"] = True
                action_result["result"] = "Waiting for new tasks or inputs"

            elif reasoning.chosen_action == "delegate_to_agent":
                # Delegate to agent (would integrate with existing agent system)
                action_result["success"] = True
                action_result["result"] = "Task delegated to specialized agent"

            elif reasoning.chosen_action == "web_research":
                # Web research action (would use Playwright)
                action_result["success"] = True
                action_result["result"] = "Web research initiated"

            elif reasoning.chosen_action in self.available_tools:
                # Execute registered tool
                tool_function = self.available_tools[reasoning.chosen_action]
                if asyncio.iscoroutinefunction(tool_function):
                    result = await tool_function()
                else:
                    result = tool_function()
                action_result["success"] = True
                action_result["result"] = result
                self.tool_usage_stats[reasoning.chosen_action] += 1

            else:
                action_result["error"] = f"Unknown action: {reasoning.chosen_action}"

        except Exception as e:  # pylint: disable=broad-exception-caught
            action_result["error"] = str(e)
            logger.error("Action execution failed: %s", e)

        action_result["execution_time"] = time.time() - action_start
        return action_result

    async def _learn(self, perception: PerceptionResult, reasoning: ReasoningResult,
                    action_result: Dict[str, Any]) -> None:
        """
        Learning phase: Extract knowledge from the cycle.

        Args:
            perception: Perception results
            reasoning: Reasoning results
            action_result: Action execution results
        """
        self.cognitive_state = CognitiveState.LEARNING

        # Store the experience as a memory
        tasks_count = len(perception.pending_tasks)
        alerts_count = len(perception.system_alerts)
        result_text = action_result.get('result', action_result.get('error', 'No result'))
        experience_content = f"""
        Cognitive Cycle {self.cycle_count}:
        Perception: {tasks_count} tasks, {alerts_count} alerts
        Reasoning: {reasoning.decision_type} -> {reasoning.chosen_action}
        (confidence: {reasoning.confidence_score})
        Action: {action_result['action']} (success: {action_result['success']})
        Result: {result_text}
        """

        memory_context = MemoryContext(
            user_id=self.context.user_id if self.context else "system",
            session_id=self.session_id,
            task_id=None,
            agent_id="cognitive_engine",
            conversation_context={"cycle": self.cycle_count}
        )

        self.memory_manager.store_memory(
            content=experience_content,
            memory_type="experience",
            context=memory_context,
            confidence_score=reasoning.confidence_score
        )

        # Periodic memory consolidation
        if self.cycle_count % self.learning_threshold == 0:
            consolidation_result = self.memory_manager.consolidate_memories(self.session_id)
            logger.info("Memory consolidation: %s", consolidation_result)

        # Learn from action outcomes
        if action_result["success"]:
            # Store successful pattern
            pattern = f"{reasoning.chosen_action} for {reasoning.decision_type}"
            success_memory = f"Successful action pattern: {pattern}"
            self.memory_manager.store_memory(
                content=success_memory,
                memory_type="pattern",
                context=memory_context,
                confidence_score=0.9
            )
        else:
            # Store failure pattern for future avoidance
            error_detail = action_result.get('error', 'unknown error')
            action_name = reasoning.chosen_action
            failure_memory = f"Failed action pattern: {action_name} failed with: {error_detail}"
            self.memory_manager.store_memory(
                content=failure_memory,
                memory_type="pattern",
                context=memory_context,
                confidence_score=0.8
            )

    def _initialize_working_memory(self) -> None:
        """Initialize the working memory for this session."""
        working_memory = WorkingMemoryState(
            session_id=self.session_id,
            current_goal_id=None,
            current_task_id=None,
            cognitive_state=self.cognitive_state.value,
            context_data=self.context.__dict__ if self.context else {},
            last_update=datetime.utcnow()
        )

        self.brain.update_working_memory(working_memory)

    async def _log_thought_cycle(self, perception: PerceptionResult,
                                reasoning: ReasoningResult,
                                action_result: Dict[str, Any]) -> None:
        """Log the complete thought process for introspection."""
        result_text = action_result.get('result', action_result.get('error', 'No result'))
        thought_record = ThoughtRecord(
            thought_id=f"thought_{self.session_id}_{self.cycle_count}",
            timestamp=datetime.utcnow(),
            decision_type=reasoning.decision_type,
            reasoning=" | ".join(reasoning.reasoning_chain),
            context={
                "perception": {
                    "tasks": len(perception.pending_tasks),
                    "alerts": len(perception.system_alerts)
                },
                "confidence": reasoning.confidence_score,
                "alternatives": reasoning.alternative_actions
            },
            action_taken=reasoning.chosen_action,
            outcome=f"Success: {action_result['success']}, Result: {result_text}",
            learning_extracted=f"Cycle {self.cycle_count} completed"
        )

        self.brain.log_thought(thought_record)

    async def _handle_cognitive_error(self, error: Exception) -> None:
        """Handle errors in the cognitive loop."""
        logger.error("Cognitive error in cycle %d: %s", self.cycle_count, error)

        # Store error as learning experience
        if hasattr(self, 'memory_manager') and self.memory_manager:
            error_context = MemoryContext(
                user_id="system",
                session_id=self.session_id,
                task_id=None,
                agent_id="cognitive_engine",
                conversation_context={"error": True, "cycle": self.cycle_count}
            )

            error_content = f"Cognitive error: {str(error)} in cycle {self.cycle_count}"
            self.memory_manager.store_memory(
                content=error_content,
                memory_type="error",
                context=error_context,
                confidence_score=1.0
            )

    async def _handle_cycle_error(self, error: Exception) -> None:
        """Handle errors within a single cycle."""
        logger.warning("Cycle error: %s", error)
        # Could implement recovery strategies here

    async def _shutdown_consciousness(self) -> None:
        """Clean shutdown of consciousness."""
        # Update final working memory state
        if hasattr(self, 'brain') and self.brain:
            final_state = WorkingMemoryState(
                session_id=self.session_id,
                current_goal_id=None,
                current_task_id=None,
                cognitive_state="shutdown",
                context_data={"final_cycle": self.cycle_count},
                last_update=datetime.utcnow()
            )
            self.brain.update_working_memory(final_state)

        logger.info("Consciousness shutdown complete. Total cycles: %d", self.cycle_count)
