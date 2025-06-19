#!/usr/bin/env python3
"""
Interaction Journal System - Comprehensive logging of all user interactions
Logs every message, timestamp, context for learning and recovery
"""

import asyncio
import logging
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

from consciousness_session import get_consciousness, initialize_consciousness
from shared.models.memory_models import MemoryContext, MemoryImportance
from shared.interfaces.memory_provider import MemoryType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class InteractionEntry:
    """Single interaction entry in the journal"""
    id: str
    timestamp: datetime
    user_message: str
    assistant_response: str
    context: Dict[str, Any]
    session_id: str
    conversation_thread: str
    metadata: Dict[str, Any]
    error_occurred: bool = False
    error_details: Optional[str] = None
    performance_metrics: Optional[Dict[str, Any]] = None

class InteractionJournal:
    """Comprehensive interaction logging and learning system"""
    
    def __init__(self, db_path: str = "interaction_journal.db"):
        self.db_path = db_path
        self.consciousness = None
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.conversation_thread = f"thread_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self._init_database()
    
    def _init_database(self):
        """Initialize the interaction journal database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create interactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                user_message TEXT NOT NULL,
                assistant_response TEXT NOT NULL,
                context TEXT NOT NULL,
                session_id TEXT NOT NULL,
                conversation_thread TEXT NOT NULL,
                metadata TEXT NOT NULL,
                error_occurred BOOLEAN DEFAULT FALSE,
                error_details TEXT,
                performance_metrics TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create conversation sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_sessions (
                session_id TEXT PRIMARY KEY,
                start_time TEXT NOT NULL,
                end_time TEXT,
                total_interactions INTEGER DEFAULT 0,
                user_satisfaction REAL,
                session_summary TEXT,
                key_learnings TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create error patterns table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS error_patterns (
                id TEXT PRIMARY KEY,
                error_type TEXT NOT NULL,
                error_pattern TEXT NOT NULL,
                fix_pattern TEXT NOT NULL,
                success_rate REAL DEFAULT 0.0,
                usage_count INTEGER DEFAULT 0,
                last_used TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create learning insights table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_insights (
                id TEXT PRIMARY KEY,
                insight_type TEXT NOT NULL,
                description TEXT NOT NULL,
                evidence TEXT NOT NULL,
                confidence REAL NOT NULL,
                actionable_items TEXT,
                implementation_status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        
        logger.info(f"📖 Interaction Journal initialized: {self.db_path}")
    
    async def initialize_consciousness(self):
        """Initialize consciousness system for the journal"""
        if self.consciousness is None:
            self.consciousness = await initialize_consciousness()
            logger.info("🧠 Consciousness system integrated with journal")
    
    async def log_interaction(self, user_message: str, assistant_response: str, 
                            context: Optional[Dict[str, Any]] = None,
                            error_occurred: bool = False,
                            error_details: Optional[str] = None) -> str:
        """Log a complete interaction to the journal"""
        
        await self.initialize_consciousness()
        
        # Generate unique interaction ID
        interaction_id = f"interaction_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Create interaction entry
        entry = InteractionEntry(
            id=interaction_id,
            timestamp=datetime.now(),
            user_message=user_message,
            assistant_response=assistant_response,
            context=context or {},
            session_id=self.session_id,
            conversation_thread=self.conversation_thread,
            metadata={
                "message_length": len(user_message),
                "response_length": len(assistant_response),
                "contains_code": "```" in assistant_response,
                "contains_error": error_occurred
            },
            error_occurred=error_occurred,
            error_details=error_details
        )
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO interactions 
            (id, timestamp, user_message, assistant_response, context, session_id, 
             conversation_thread, metadata, error_occurred, error_details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry.id,
            entry.timestamp.isoformat(),
            entry.user_message,
            entry.assistant_response,
            json.dumps(entry.context),
            entry.session_id,
            entry.conversation_thread,
            json.dumps(entry.metadata),
            entry.error_occurred,
            entry.error_details
        ))
        
        conn.commit()
        conn.close()
        
        # Store in consciousness memory
        if self.consciousness:
            memory_context = MemoryContext(
                agent_id="interaction-journal",
                session_id=self.session_id,
                conversation_id=self.conversation_thread,
                tags=["interaction", "journal", "conversation"]
            )
            
            # Store user message
            self.consciousness.consciousness.memory_manager.store_memory(
                f"User: {user_message}",
                MemoryType.CONVERSATION.value,
                memory_context
            )
            
            # Store assistant response
            self.consciousness.consciousness.memory_manager.store_memory(
                f"Assistant: {assistant_response}",
                MemoryType.CONVERSATION.value,
                memory_context
            )
            
            # Store error if occurred
            if error_occurred:
                self.consciousness.consciousness.memory_manager.store_memory(
                    f"Error in interaction {interaction_id}: {error_details}",
                    MemoryType.EXPERIENCES.value,
                    memory_context
                )
        
        logger.info(f"📝 Logged interaction: {interaction_id}")
        return interaction_id
    
    async def learn_from_error(self, error_type: str, error_details: str, 
                             fix_applied: str) -> str:
        """Learn from errors and store fix patterns"""
        
        pattern_id = f"pattern_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if similar error pattern exists
        cursor.execute("""
            SELECT id, usage_count, success_rate FROM error_patterns 
            WHERE error_type = ? AND error_pattern LIKE ?
        """, (error_type, f"%{error_details[:50]}%"))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update existing pattern
            pattern_id = existing[0]
            new_count = existing[1] + 1
            cursor.execute("""
                UPDATE error_patterns 
                SET usage_count = ?, last_used = ?, fix_pattern = ?
                WHERE id = ?
            """, (new_count, datetime.now().isoformat(), fix_applied, pattern_id))
        else:
            # Create new pattern
            cursor.execute("""
                INSERT INTO error_patterns 
                (id, error_type, error_pattern, fix_pattern, usage_count, last_used)
                VALUES (?, ?, ?, ?, 1, ?)
            """, (pattern_id, error_type, error_details, fix_applied, 
                  datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        # Store in consciousness
        if self.consciousness:
            memory_context = MemoryContext(
                agent_id="error-learning",
                session_id=self.session_id,
                tags=["error", "learning", "pattern", error_type]
            )
            
            self.consciousness.consciousness.memory_manager.store_memory(
                f"Error pattern learned: {error_type} -> {fix_applied}",
                MemoryType.EXPERIENCES.value,
                memory_context
            )
        
        logger.info(f"🎓 Learned from error: {pattern_id}")
        return pattern_id
    
    def get_error_fix_suggestion(self, error_type: str, error_details: str) -> Optional[str]:
        """Get fix suggestion for similar errors"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Find similar error patterns
        cursor.execute("""
            SELECT fix_pattern, success_rate, usage_count 
            FROM error_patterns 
            WHERE error_type = ? 
            ORDER BY success_rate DESC, usage_count DESC 
            LIMIT 1
        """, (error_type,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            fix_pattern, success_rate, usage_count = result
            logger.info(f"💡 Found fix suggestion (success: {success_rate}, used: {usage_count}x)")
            return fix_pattern
        
        return None
    
    def get_conversation_history(self, limit: int = 10) -> List[InteractionEntry]:
        """Get recent conversation history"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM interactions 
            WHERE session_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (self.session_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        conversations = []
        for row in rows:
            conversations.append(InteractionEntry(
                id=row[0],
                timestamp=datetime.fromisoformat(row[1]),
                user_message=row[2],
                assistant_response=row[3],
                context=json.loads(row[4]),
                session_id=row[5],
                conversation_thread=row[6],
                metadata=json.loads(row[7]),
                error_occurred=bool(row[8]),
                error_details=row[9]
            ))
        
        return conversations
    
    async def generate_session_insights(self) -> Dict[str, Any]:
        """Generate insights from the current session"""
        
        if not self.consciousness:
            await self.initialize_consciousness()
        
        # Get conversation statistics
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*), AVG(LENGTH(user_message)), AVG(LENGTH(assistant_response)),
                   SUM(CASE WHEN error_occurred THEN 1 ELSE 0 END)
            FROM interactions WHERE session_id = ?
        """, (self.session_id,))
        
        stats = cursor.fetchone()
        conn.close()
        
        total_interactions = stats[0] if stats[0] else 0
        avg_user_length = stats[1] if stats[1] else 0
        avg_response_length = stats[2] if stats[2] else 0
        total_errors = stats[3] if stats[3] else 0
        
        # Use consciousness for deeper analysis
        reflection = await self.consciousness.reflect_on_session()
        
        insights = {
            "session_id": self.session_id,
            "total_interactions": total_interactions,
            "average_user_message_length": avg_user_length,
            "average_response_length": avg_response_length,
            "error_rate": total_errors / total_interactions if total_interactions > 0 else 0,
            "consciousness_reflection": reflection,
            "session_duration_minutes": (datetime.now() - datetime.fromisoformat(self.session_id.split('_')[1] + '_' + self.session_id.split('_')[2])).total_seconds() / 60,
            "generated_at": datetime.now().isoformat()
        }
        
        logger.info(f"📊 Generated session insights: {total_interactions} interactions, {total_errors} errors")
        return insights
    
    def get_learning_progress(self) -> Dict[str, Any]:
        """Get overall learning progress from the journal"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total interactions across all sessions
        cursor.execute("SELECT COUNT(*) FROM interactions")
        total_interactions = cursor.fetchone()[0]
        
        # Error patterns learned
        cursor.execute("SELECT COUNT(*) FROM error_patterns")
        error_patterns = cursor.fetchone()[0]
        
        # Recent performance (last 24 hours)
        yesterday = datetime.now() - timedelta(days=1)
        cursor.execute("""
            SELECT COUNT(*), SUM(CASE WHEN error_occurred THEN 1 ELSE 0 END)
            FROM interactions 
            WHERE timestamp > ?
        """, (yesterday.isoformat(),))
        
        recent_stats = cursor.fetchone()
        recent_interactions = recent_stats[0] if recent_stats[0] else 0
        recent_errors = recent_stats[1] if recent_stats[1] else 0
        
        conn.close()
        
        progress = {
            "total_interactions_logged": total_interactions,
            "error_patterns_learned": error_patterns,
            "recent_24h_interactions": recent_interactions,
            "recent_24h_error_rate": recent_errors / recent_interactions if recent_interactions > 0 else 0,
            "learning_velocity": recent_interactions / 24 if recent_interactions > 0 else 0,  # interactions per hour
            "system_maturity": min(total_interactions / 1000, 1.0),  # 0-1 scale
            "last_updated": datetime.now().isoformat()
        }
        
        return progress

# Global journal instance
JOURNAL = None

async def get_journal() -> InteractionJournal:
    """Get the global journal instance"""
    global JOURNAL
    if JOURNAL is None:
        JOURNAL = InteractionJournal()
        await JOURNAL.initialize_consciousness()
    return JOURNAL

async def log_user_interaction(user_message: str, assistant_response: str, 
                             context: Optional[Dict[str, Any]] = None,
                             error_occurred: bool = False,
                             error_details: Optional[str] = None) -> str:
    """Convenience function to log interactions"""
    journal = await get_journal()
    return await journal.log_interaction(
        user_message, assistant_response, context, error_occurred, error_details
    )

if __name__ == "__main__":
    # Test the journal system
    async def test_journal():
        journal = await get_journal()
        
        # Test interaction logging
        interaction_id = await journal.log_interaction(
            "Hello, test the consciousness system",
            "I'll test the consciousness system comprehensively for you.",
            {"test": True}
        )
        
        # Test error learning
        await journal.learn_from_error(
            "import_error",
            "ModuleNotFoundError: No module named 'numpy'",
            "pip install numpy in virtual environment"
        )
        
        # Test fix suggestion
        fix = journal.get_error_fix_suggestion("import_error", "numpy not found")
        print(f"Fix suggestion: {fix}")
        
        # Generate insights
        insights = await journal.generate_session_insights()
        print(f"Session insights: {insights}")
        
        # Learning progress
        progress = journal.get_learning_progress()
        print(f"Learning progress: {progress}")
    
    asyncio.run(test_journal())