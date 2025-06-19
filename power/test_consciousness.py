#!/usr/bin/env python3
"""
Test script to initialize and demonstrate the consciousness system.
"""

import asyncio
import logging
from datetime import datetime
from core.consciousness.consciousness_orchestrator import ConsciousnessOrchestrator
from core.consciousness.cognitive_loop import CognitiveEngine
from core.consciousness.decision_engine import ReasoningContext
from core.consciousness.tools.self_reflection_tool import SelfReflectionTool
from shared.models.memory_models import MemoryContext, MemoryImportance
from shared.interfaces.memory_provider import MemoryType

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    """Main test function for consciousness system."""
    logger.info("🧠 Initializing Consciousness System...")
    
    # Initialize consciousness orchestrator
    orchestrator = ConsciousnessOrchestrator()
    
    # Access cognitive engine from orchestrator
    logger.info("🔄 Accessing Cognitive Engine...")
    cognitive_engine = orchestrator.cognitive_engine
    
    # Create test memory context
    context = MemoryContext(
        agent_id="test-agent-001",
        session_id="consciousness-demo",
        task_id="system-initialization",
        tags=["initialization", "demo", "consciousness"]
    )
    
    # Store initial memories via memory manager
    logger.info("💾 Storing initial memories...")
    
    orchestrator.memory_manager.store_memory(
        "Consciousness system successfully initialized",
        MemoryType.EXPERIENCES.value,
        context
    )
    
    orchestrator.memory_manager.store_memory(
        "System capable of self-reflection and decision making",
        MemoryType.FACTS.value,
        context
    )
    
    # Test memory retrieval
    logger.info("🔍 Testing memory retrieval...")
    memories = orchestrator.memory_manager.search_memories("consciousness system", limit=5)
    
    for memory in memories:
        logger.info(f"Retrieved memory: {memory.content[:50]}...")
    
    # Test decision making  
    logger.info("🤔 Testing decision engine...")
    decision_context = ReasoningContext(
        situation_type="demonstration",
        urgency_level=5,
        complexity_score=3,
        available_data={
            "situation": "User wants to demonstrate consciousness capabilities",
            "available_actions": ["show_memory_stats", "run_self_reflection", "demonstrate_learning"]
        },
        constraints=["maintain_system_stability", "provide_useful_output"],
        success_criteria=["system_demonstrates_consciousness", "user_satisfied_with_demo"]
    )
    
    decision = await orchestrator.decision_engine.make_decision(decision_context)
    logger.info(f"Decision made: {decision}")
    
    # Start cognitive engine for a few cycles
    logger.info("🔄 Running cognitive engine cycles...")
    for cycle in range(3):
        logger.info(f"--- Cognitive Cycle {cycle + 1} ---")
        result = await cognitive_engine.process_cycle()
        logger.info(f"Cycle result: {result}")
        await asyncio.sleep(1)  # Brief pause between cycles
    
    # Display memory statistics
    logger.info("📊 Retrieving memory statistics...")
    stats = await orchestrator.memory_manager.get_memory_stats()
    logger.info(f"Total memories: {stats.total_memories}")
    logger.info(f"Memories by type: {stats.memories_by_type}")
    logger.info(f"Memories by importance: {stats.memories_by_importance}")
    
    # Test self-reflection
    logger.info("🪞 Running self-reflection...")
    reflection_tool = SelfReflectionTool(orchestrator.memory_manager, orchestrator.cognitive_engine)
    reflection = await reflection_tool.execute({"focus": "system_capabilities"})
    logger.info(f"Self-reflection: {reflection}")
    
    logger.info("✅ Consciousness system demonstration complete!")

if __name__ == "__main__":
    asyncio.run(main())