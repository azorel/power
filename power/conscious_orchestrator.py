#!/usr/bin/env python3
"""
Conscious Orchestrator - The main system that integrates consciousness with all operations
This is the primary interface that will be used for all future tasks
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

from consciousness_session import get_consciousness, initialize_consciousness
from interaction_journal import get_journal, log_user_interaction
from core.consciousness.consciousness_orchestrator import ConsciousnessOrchestrator
from core.consciousness.decision_engine import ReasoningContext
from shared.models.memory_models import MemoryContext, MemoryImportance
from shared.interfaces.memory_provider import MemoryType

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ConsciousChiefOrchestrator:
    """
    The Conscious Chief Orchestrator - Integration of consciousness system with all operations
    
    This is the main system that will be used for ALL future tasks. It:
    - Uses consciousness for memory and decision making
    - Logs all interactions with timestamps
    - Learns from errors automatically
    - Provides self-reflection capabilities
    - Maintains persistent memory across sessions
    """
    
    def __init__(self):
        self.consciousness = None
        self.journal = None
        self.active = False
        self.session_id = f"chief_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.initialization_time = datetime.now()
        
    async def initialize(self):
        """Initialize the conscious orchestrator system"""
        logger.info("🚀 Initializing Conscious Chief Orchestrator...")
        
        # Initialize consciousness
        self.consciousness = await initialize_consciousness()
        
        # Initialize journal
        self.journal = await get_journal()
        
        # Store initialization in memory
        init_context = MemoryContext(
            agent_id="chief-orchestrator",
            session_id=self.session_id,
            tags=["initialization", "consciousness", "system"]
        )
        
        self.consciousness.consciousness.memory_manager.store_memory(
            f"Conscious Chief Orchestrator initialized at {self.initialization_time.isoformat()}",
            MemoryType.EXPERIENCES.value,
            init_context
        )
        
        # Log initialization interaction
        await self.journal.log_interaction(
            "System initialization",
            "Conscious Chief Orchestrator fully initialized with consciousness and journal systems",
            {"initialization": True, "timestamp": self.initialization_time.isoformat()}
        )
        
        self.active = True
        logger.info("✅ Conscious Chief Orchestrator is now ACTIVE and ready for all operations")
    
    async def process_user_request(self, user_message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Process user request with full consciousness capabilities"""
        
        if not self.active:
            await self.initialize()
        
        start_time = datetime.now()
        error_occurred = False
        error_details = None
        
        try:
            logger.info(f"🧠 Processing user request: {user_message[:50]}...")
            
            # Create reasoning context for decision making
            reasoning_context = ReasoningContext(
                situation_type="user_request",
                urgency_level=5,  # Default medium urgency
                complexity_score=self._estimate_complexity(user_message),
                available_data={
                    "user_message": user_message,
                    "context": context or {},
                    "session_id": self.session_id
                },
                constraints=["maintain_quality", "provide_helpful_response"],
                success_criteria=["user_satisfaction", "task_completion"]
            )
            
            # Use consciousness to make decision about approach
            decision = await self.consciousness.consciousness.decision_engine.make_decision(reasoning_context)
            logger.info(f"🤔 Decision: {decision.decision} (confidence: {decision.confidence})")
            
            # Store interaction in memory
            memory_context = MemoryContext(
                agent_id="chief-orchestrator",
                session_id=self.session_id,
                tags=["user_request", "processing", "decision"]
            )
            
            self.consciousness.consciousness.memory_manager.store_memory(
                f"User request: {user_message}",
                MemoryType.CONVERSATION.value,
                memory_context
            )
            
            # Process the request (this is where specific task logic would go)
            response = await self._execute_task(user_message, decision, context)
            
            # Store response in memory
            self.consciousness.consciousness.memory_manager.store_memory(
                f"Response: {response}",
                MemoryType.CONVERSATION.value,
                memory_context
            )
            
            # Calculate performance metrics
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return response
            
        except Exception as e:
            error_occurred = True
            error_details = str(e)
            logger.error(f"❌ Error processing request: {e}")
            
            # Learn from the error
            await self.journal.learn_from_error(
                error_type=type(e).__name__,
                error_details=str(e),
                fix_applied="Error handling and logging implemented"
            )
            
            response = f"I encountered an error while processing your request: {e}. I've logged this for learning and improvement."
            return response
            
        finally:
            # Always log the interaction
            processing_time = (datetime.now() - start_time).total_seconds()
            
            await self.journal.log_interaction(
                user_message,
                response if 'response' in locals() else "Error occurred",
                {
                    "processing_time_seconds": processing_time,
                    "decision_confidence": decision.confidence if 'decision' in locals() else 0.0,
                    **(context or {})
                },
                error_occurred=error_occurred,
                error_details=error_details
            )
    
    async def _execute_task(self, user_message: str, decision: Any, context: Optional[Dict[str, Any]]) -> str:
        """Execute the actual task based on the user message and decision"""
        
        # This is where specific task logic would be implemented
        # For now, provide a consciousness-aware response
        
        # Search memory for relevant information
        relevant_memories = self.consciousness.consciousness.memory_manager.search_memories(
            user_message, limit=5
        )
        
        # Get recent conversation history
        conversation_history = self.journal.get_conversation_history(limit=3)
        
        # Use self-reflection to inform response
        reflection = await self.consciousness.reflect_on_session()
        
        response_parts = []
        
        if relevant_memories:
            response_parts.append(f"Based on my memory, I found {len(relevant_memories)} relevant items from our previous interactions.")
        
        if conversation_history:
            response_parts.append(f"Considering our recent conversation context (last {len(conversation_history)} exchanges).")
        
        # Provide consciousness-informed response
        response_parts.append(f"My decision engine recommends: {decision.decision}")
        response_parts.append(f"I'm operating with {decision.confidence:.0%} confidence on this approach.")
        
        # Add learning insights
        if reflection and 'learning_progress' in reflection:
            learning = reflection['learning_progress']
            response_parts.append(f"Current learning state: {learning['total_knowledge_items']} knowledge items, quality score: {learning['knowledge_quality_score']:.2f}")
        
        return " ".join(response_parts)
    
    def _estimate_complexity(self, user_message: str) -> int:
        """Estimate complexity of user request (1-10 scale)"""
        
        complexity_indicators = {
            "comprehensive": 3,
            "debug": 2,
            "test": 2,
            "implement": 3,
            "fix": 2,
            "analyze": 2,
            "build": 4,
            "create": 3,
            "system": 2,
            "multiple": 2
        }
        
        base_complexity = 3  # Default
        message_lower = user_message.lower()
        
        for indicator, weight in complexity_indicators.items():
            if indicator in message_lower:
                base_complexity += weight
        
        # Message length factor
        if len(user_message) > 100:
            base_complexity += 1
        if len(user_message) > 200:
            base_complexity += 1
        
        return min(base_complexity, 10)
    
    async def get_consciousness_status(self) -> Dict[str, Any]:
        """Get current consciousness system status"""
        
        if not self.active:
            return {"status": "inactive", "message": "Consciousness system not initialized"}
        
        # Get memory statistics
        memory_stats = self.consciousness.consciousness.memory_manager.get_memory_insights()
        
        # Get learning progress
        learning_progress = self.journal.get_learning_progress()
        
        # Generate session insights
        session_insights = await self.journal.generate_session_insights()
        
        return {
            "status": "active",
            "session_id": self.session_id,
            "uptime_minutes": (datetime.now() - self.initialization_time).total_seconds() / 60,
            "memory_statistics": memory_stats,
            "learning_progress": learning_progress,
            "session_insights": session_insights,
            "consciousness_reflection": await self.consciousness.reflect_on_session()
        }
    
    async def perform_self_reflection(self) -> Dict[str, Any]:
        """Perform comprehensive self-reflection"""
        
        if not self.active:
            await self.initialize()
        
        reflection = await self.consciousness.reflect_on_session()
        
        # Store reflection as learning experience
        memory_context = MemoryContext(
            agent_id="chief-orchestrator",
            session_id=self.session_id,
            tags=["self_reflection", "learning", "consciousness"]
        )
        
        self.consciousness.consciousness.memory_manager.store_memory(
            f"Self-reflection performed: {len(reflection.get('recent_decisions', []))} insights generated",
            MemoryType.EXPERIENCES.value,
            memory_context
        )
        
        return reflection
    
    async def shutdown(self):
        """Graceful shutdown with final reflection and logging"""
        
        if not self.active:
            return
        
        logger.info("🔄 Initiating graceful shutdown...")
        
        # Final self-reflection
        final_reflection = await self.perform_self_reflection()
        
        # Generate final session insights
        final_insights = await self.journal.generate_session_insights()
        
        # Log shutdown
        await self.journal.log_interaction(
            "System shutdown initiated",
            f"Graceful shutdown completed. Session insights: {final_insights['total_interactions']} interactions processed.",
            {
                "shutdown": True,
                "final_reflection": final_reflection,
                "final_insights": final_insights
            }
        )
        
        self.active = False
        logger.info("✅ Conscious Chief Orchestrator shutdown complete")

# Global orchestrator instance
CHIEF_ORCHESTRATOR = None

async def get_chief_orchestrator() -> ConsciousChiefOrchestrator:
    """Get the global chief orchestrator instance"""
    global CHIEF_ORCHESTRATOR
    if CHIEF_ORCHESTRATOR is None:
        CHIEF_ORCHESTRATOR = ConsciousChiefOrchestrator()
        await CHIEF_ORCHESTRATOR.initialize()
    return CHIEF_ORCHESTRATOR

async def process_request(user_message: str, context: Optional[Dict[str, Any]] = None) -> str:
    """Convenience function to process user requests"""
    orchestrator = await get_chief_orchestrator()
    return await orchestrator.process_user_request(user_message, context)

if __name__ == "__main__":
    # Test the conscious orchestrator
    async def test_orchestrator():
        orchestrator = await get_chief_orchestrator()
        
        # Test processing requests
        response1 = await orchestrator.process_user_request(
            "Hello, I want to test the consciousness system comprehensively"
        )
        print(f"Response 1: {response1}")
        
        response2 = await orchestrator.process_user_request(
            "Can you debug and fix any issues in the system?"
        )
        print(f"Response 2: {response2}")
        
        # Test status
        status = await orchestrator.get_consciousness_status()
        print(f"Status: {status}")
        
        # Test reflection
        reflection = await orchestrator.perform_self_reflection()
        print(f"Reflection: {reflection}")
        
        # Shutdown
        await orchestrator.shutdown()
    
    asyncio.run(test_orchestrator())