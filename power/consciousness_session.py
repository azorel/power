#!/usr/bin/env python3
"""
Consciousness Session Runner - Activates the consciousness system for the orchestrator
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from core.consciousness.consciousness_orchestrator import ConsciousnessOrchestrator
from shared.models.memory_models import MemoryContext, MemoryImportance
from shared.interfaces.memory_provider import MemoryType

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ConsciousOrchestrator:
    """Consciousness-enabled orchestrator instance"""
    
    def __init__(self):
        self.consciousness = ConsciousnessOrchestrator(user_id="orchestrator")
        self.session_context = MemoryContext(
            agent_id="chief-orchestrator",
            session_id=f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            tags=["orchestrator", "consciousness", "main_session"]
        )
        self.active = False
        
    async def activate_consciousness(self):
        """Activate the consciousness system"""
        logger.info("🧠 Activating Consciousness System...")
        
        # Store activation memory
        self.consciousness.memory_manager.store_memory(
            "Consciousness system activated for orchestrator role",
            MemoryType.EXPERIENCES.value,
            self.session_context
        )
        
        # Log current capabilities
        capabilities = [
            "Persistent memory with vector embeddings",
            "Decision engine with multi-LLM reasoning",
            "Cognitive engine with perception-action cycles", 
            "Self-reflection and learning capabilities",
            "Multi-agent task orchestration",
            "Error learning and correction system"
        ]
        
        for capability in capabilities:
            self.consciousness.memory_manager.store_memory(
                f"System capability: {capability}",
                MemoryType.FACTS.value,
                self.session_context
            )
        
        self.active = True
        logger.info("✅ Consciousness system is now ACTIVE and ready")
        
    def log_interaction(self, user_message: str, response: str):
        """Log user interactions to consciousness memory"""
        timestamp = datetime.now().isoformat()
        
        # Store user message
        self.consciousness.memory_manager.store_memory(
            f"User message at {timestamp}: {user_message}",
            MemoryType.CONVERSATION.value,
            self.session_context
        )
        
        # Store response
        self.consciousness.memory_manager.store_memory(
            f"Orchestrator response at {timestamp}: {response}",
            MemoryType.CONVERSATION.value,
            self.session_context
        )
        
    def get_memory_stats(self):
        """Get current memory statistics"""
        return self.consciousness.memory_manager.get_memory_insights()
    
    async def reflect_on_session(self):
        """Self-reflection on current session"""
        from core.consciousness.tools.self_reflection_tool import SelfReflectionTool
        
        reflection_tool = SelfReflectionTool(
            self.consciousness.brain,
            self.consciousness.memory_manager
        )
        
        # Use actual method from the tool
        recent_decisions = await reflection_tool.reflect_on_recent_decisions(time_window_hours=1)
        learning_progress = await reflection_tool.analyze_learning_progress()
        performance = await reflection_tool.evaluate_performance_trends()
        
        return {
            "recent_decisions": recent_decisions,
            "learning_progress": learning_progress, 
            "performance_trends": performance,
            "summary": reflection_tool.get_reflection_summary()
        }

# Global consciousness instance
CONSCIOUSNESS = None

async def initialize_consciousness():
    """Initialize global consciousness instance"""
    global CONSCIOUSNESS
    if CONSCIOUSNESS is None:
        CONSCIOUSNESS = ConsciousOrchestrator()
        await CONSCIOUSNESS.activate_consciousness()
    return CONSCIOUSNESS

def get_consciousness():
    """Get the active consciousness instance"""
    return CONSCIOUSNESS

if __name__ == "__main__":
    # Direct test run
    async def test_consciousness():
        consciousness = await initialize_consciousness()
        
        # Test logging interaction
        consciousness.log_interaction(
            "Test message from user", 
            "Test response from consciousness orchestrator"
        )
        
        # Show memory stats
        stats = consciousness.get_memory_stats()
        logger.info(f"Memory stats: {stats}")
        
        # Test reflection
        reflection = await consciousness.reflect_on_session()
        logger.info(f"Self-reflection: {reflection}")
        
    asyncio.run(test_consciousness())