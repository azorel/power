"""
Power Brain Database: The persistent consciousness storage system.

This module implements the SQLite-based brain that stores working memory,
task queues, thought logs, knowledge stores, and symbolic relationships.
"""

import sqlite3
import json
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class WorkingMemoryState:
    """Current cognitive state of the agent."""
    session_id: str
    current_goal_id: Optional[str]
    current_task_id: Optional[str]
    cognitive_state: str
    context_data: Dict[str, Any]
    last_update: datetime


@dataclass
class TaskRecord:  # pylint: disable=too-many-instance-attributes
    """Enhanced task record with agent assignment and workspace info."""
    task_id: str
    description: str
    task_type: str
    status: str
    priority: int
    created_at: datetime
    updated_at: datetime
    parent_goal_id: Optional[str] = None
    agent_assigned: Optional[str] = None
    completion_signal: Optional[str] = None
    workspace_path: Optional[str] = None


@dataclass
class ThoughtRecord:  # pylint: disable=too-many-instance-attributes
    """Introspection and reasoning log entry."""
    thought_id: str
    timestamp: datetime
    decision_type: str
    reasoning: str
    action_taken: str
    context: Dict[str, Any] = None
    outcome: Optional[str] = None
    learning_extracted: Optional[str] = None

    def __post_init__(self):
        if self.context is None:
            self.context = {}


@dataclass
class MemoryRecord:  # pylint: disable=too-many-instance-attributes
    """Vector-embedded knowledge storage."""
    memory_id: str
    content: str
    memory_type: str
    source_type: str
    created_at: datetime
    confidence_score: float = 1.0
    last_accessed: datetime = None
    embedding_vector: Optional[bytes] = None
    access_count: int = 0

    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = self.created_at


class PowerBrain:
    """
    The persistent brain database for AI consciousness.

    Provides ACID-compliant storage for working memory, task queues,
    thought logs, episodic memory, and symbolic knowledge graphs.
    """

    def __init__(self, brain_path: Optional[str] = None):
        """
        Initialize the Power Brain database.

        Args:
            brain_path: Path to SQLite database file (defaults to power_brain.db)
        """
        self.brain_path = brain_path or "power_brain.db"
        self.connection: Optional[sqlite3.Connection] = None
        self._initialize_database()

    def _initialize_database(self) -> None:
        """Create database schema and initialize brain structures."""
        self.connection = sqlite3.connect(
            self.brain_path,
            check_same_thread=False,
            timeout=30.0
        )
        # Enable foreign keys and WAL mode for performance
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute("PRAGMA journal_mode = WAL")
        self.connection.execute("PRAGMA synchronous = NORMAL")
        self._create_schema()
        logger.info("Power Brain initialized: %s", self.brain_path)

    def _create_schema(self) -> None:
        """Create all brain database tables."""
        schema_statements = [
            # Working Memory: Current cognitive state
            """
            CREATE TABLE IF NOT EXISTS working_memory (
                session_id TEXT PRIMARY KEY,
                current_goal_id TEXT,
                current_task_id TEXT,
                cognitive_state TEXT NOT NULL,
                context_data TEXT, -- JSON
                last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,

            # Executive Function: Enhanced task management
            """
            CREATE TABLE IF NOT EXISTS task_queue (
                task_id TEXT PRIMARY KEY,
                parent_goal_id TEXT,
                description TEXT NOT NULL,
                task_type TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                priority INTEGER DEFAULT 0,
                agent_assigned TEXT,
                workspace_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completion_signal TEXT
            )
            """,

            # Introspection: Thought logging and reasoning
            """
            CREATE TABLE IF NOT EXISTS thought_log (
                thought_id TEXT PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                decision_type TEXT NOT NULL,
                reasoning TEXT NOT NULL,
                context TEXT, -- JSON
                action_taken TEXT NOT NULL,
                outcome TEXT,
                learning_extracted TEXT
            )
            """,

            # Episodic Memory: Vector-embedded knowledge
            """
            CREATE TABLE IF NOT EXISTS knowledge_store (
                memory_id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                embedding_vector BLOB,
                memory_type TEXT NOT NULL,
                source_type TEXT NOT NULL,
                confidence_score REAL DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 0
            )
            """,

            # Symbolic Knowledge: Relationship mapping
            """
            CREATE TABLE IF NOT EXISTS knowledge_graph (
                edge_id TEXT PRIMARY KEY,
                source_node TEXT NOT NULL,
                target_node TEXT NOT NULL,
                relationship_type TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                evidence TEXT
            )
            """,

            # Agent Performance: Learning and improvement
            """
            CREATE TABLE IF NOT EXISTS agent_performance (
                performance_id TEXT PRIMARY KEY,
                agent_type TEXT NOT NULL,
                task_type TEXT NOT NULL,
                success_rate REAL DEFAULT 0.0,
                avg_completion_time INTEGER DEFAULT 0,
                quality_score REAL DEFAULT 0.0,
                failure_patterns TEXT,
                improvement_suggestions TEXT,
                last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        ]

        for statement in schema_statements:
            self.connection.execute(statement)

        # Create indexes for performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_task_status ON task_queue(status)",
            "CREATE INDEX IF NOT EXISTS idx_task_priority ON task_queue(priority DESC)",
            "CREATE INDEX IF NOT EXISTS idx_memory_type ON knowledge_store(memory_type)",
            "CREATE INDEX IF NOT EXISTS idx_memory_accessed ON knowledge_store(last_accessed DESC)",
            "CREATE INDEX IF NOT EXISTS idx_thought_timestamp ON thought_log(timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_graph_source ON knowledge_graph(source_node)",
            "CREATE INDEX IF NOT EXISTS idx_graph_target ON knowledge_graph(target_node)"
        ]

        for index in indexes:
            self.connection.execute(index)

        self.connection.commit()

    def update_working_memory(self, state: WorkingMemoryState) -> None:
        """Update the current cognitive state."""
        self.connection.execute(
            """
            INSERT OR REPLACE INTO working_memory
            (session_id, current_goal_id, current_task_id, cognitive_state,
             context_data, last_update)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                state.session_id,
                state.current_goal_id,
                state.current_task_id,
                state.cognitive_state,
                json.dumps(state.context_data),
                state.last_update
            )
        )
        self.connection.commit()

    def get_working_memory(self, session_id: str) -> Optional[WorkingMemoryState]:
        """Retrieve current cognitive state."""
        cursor = self.connection.execute(
            "SELECT * FROM working_memory WHERE session_id = ?",
            (session_id,)
        )
        row = cursor.fetchone()

        if not row:
            return None

        return WorkingMemoryState(
            session_id=row[0],
            current_goal_id=row[1],
            current_task_id=row[2],
            cognitive_state=row[3],
            context_data=json.loads(row[4]) if row[4] else {},
            last_update=datetime.fromisoformat(row[5])
        )

    def add_task(self, task: TaskRecord) -> None:
        """Add a new task to the queue."""
        self.connection.execute(
            """
            INSERT INTO task_queue
            (task_id, parent_goal_id, description, task_type, status, priority,
             agent_assigned, workspace_path, created_at, updated_at,
             completion_signal)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task.task_id,
                task.parent_goal_id,
                task.description,
                task.task_type,
                task.status,
                task.priority,
                task.agent_assigned,
                task.workspace_path,
                task.created_at,
                task.updated_at,
                task.completion_signal
            )
        )
        self.connection.commit()

    def get_next_task(self, agent_type: Optional[str] = None) -> Optional[TaskRecord]:
        """Get the highest priority pending task."""
        query = "SELECT * FROM task_queue WHERE status = 'pending'"
        params = []

        if agent_type:
            query += " AND (agent_assigned IS NULL OR agent_assigned = ?)"
            params.append(agent_type)

        query += " ORDER BY priority DESC, created_at ASC LIMIT 1"

        cursor = self.connection.execute(query, params)
        row = cursor.fetchone()

        if not row:
            return None

        return self._row_to_task_record(row)

    def update_task_status(self, task_id: str, status: str,
                          completion_signal: Optional[str] = None) -> None:
        """Update task status and completion signal."""
        params = [status, datetime.utcnow(), task_id]
        query = "UPDATE task_queue SET status = ?, updated_at = ?"

        if completion_signal:
            query += ", completion_signal = ?"
            params.insert(-1, completion_signal)

        query += " WHERE task_id = ?"

        self.connection.execute(query, params)
        self.connection.commit()

    def log_thought(self, thought: ThoughtRecord) -> None:
        """Log a thought/decision for introspection."""
        self.connection.execute(
            """
            INSERT INTO thought_log
            (thought_id, timestamp, decision_type, reasoning, context,
             action_taken, outcome, learning_extracted)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                thought.thought_id,
                thought.timestamp,
                thought.decision_type,
                thought.reasoning,
                json.dumps(thought.context),
                thought.action_taken,
                thought.outcome,
                thought.learning_extracted
            )
        )
        self.connection.commit()

    def store_memory(self, memory: MemoryRecord) -> None:
        """Store a memory with optional vector embedding."""
        self.connection.execute(
            """
            INSERT OR REPLACE INTO knowledge_store
            (memory_id, content, embedding_vector, memory_type, source_type,
             confidence_score, created_at, last_accessed, access_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                memory.memory_id,
                memory.content,
                memory.embedding_vector,
                memory.memory_type,
                memory.source_type,
                memory.confidence_score,
                memory.created_at,
                memory.last_accessed,
                memory.access_count
            )
        )
        self.connection.commit()

    def search_memories(self, memory_type: Optional[str] = None,
                       limit: int = 10) -> List[MemoryRecord]:
        """Search memories by type and recency."""
        query = "SELECT * FROM knowledge_store"
        params = []

        if memory_type:
            query += " WHERE memory_type = ?"
            params.append(memory_type)

        query += " ORDER BY last_accessed DESC LIMIT ?"
        params.append(limit)

        cursor = self.connection.execute(query, params)
        return [self._row_to_memory_record(row) for row in cursor.fetchall()]

    def add_knowledge_edge(self, source: str, target: str, relationship: str,
                          **kwargs) -> None:
        """Add a relationship to the knowledge graph."""
        confidence = kwargs.get('confidence', 1.0)
        evidence = kwargs.get('evidence', '')
        edge_id = f"{source}_{relationship}_{target}_{int(time.time())}"

        self.connection.execute(
            """
            INSERT INTO knowledge_graph
            (edge_id, source_node, target_node, relationship_type, confidence, evidence)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (edge_id, source, target, relationship, confidence, evidence)
        )
        self.connection.commit()

    def get_related_concepts(self, concept: str,
                            max_depth: int = 2) -> List[Tuple[str, str, float]]:
        """Get concepts related to the given concept through the knowledge graph."""
        # max_depth parameter reserved for future multi-hop implementation
        _ = max_depth
        related = []

        # Direct relationships
        cursor = self.connection.execute(
            """
            SELECT target_node, relationship_type, confidence
            FROM knowledge_graph
            WHERE source_node = ?
            UNION
            SELECT source_node, relationship_type, confidence
            FROM knowledge_graph
            WHERE target_node = ?
            ORDER BY confidence DESC
            """,
            (concept, concept)
        )

        related.extend(cursor.fetchall())
        return related[:20]  # Limit results

    def get_brain_stats(self) -> Dict[str, Any]:
        """Get comprehensive brain statistics."""
        stats = {}

        tables = ['working_memory', 'task_queue', 'thought_log',
                 'knowledge_store', 'knowledge_graph', 'agent_performance']

        for table in tables:
            cursor = self.connection.execute(f"SELECT COUNT(*) FROM {table}")
            stats[f"{table}_count"] = cursor.fetchone()[0]

        # Task status distribution
        cursor = self.connection.execute(
            "SELECT status, COUNT(*) FROM task_queue GROUP BY status"
        )
        stats['task_status'] = dict(cursor.fetchall())

        # Memory type distribution
        cursor = self.connection.execute(
            "SELECT memory_type, COUNT(*) FROM knowledge_store GROUP BY memory_type"
        )
        stats['memory_types'] = dict(cursor.fetchall())

        return stats

    def _row_to_task_record(self, row) -> TaskRecord:
        """Convert database row to TaskRecord."""
        return TaskRecord(
            task_id=row[0],
            parent_goal_id=row[1],
            description=row[2],
            task_type=row[3],
            status=row[4],
            priority=row[5],
            agent_assigned=row[6],
            workspace_path=row[7],
            created_at=datetime.fromisoformat(row[8]),
            updated_at=datetime.fromisoformat(row[9]),
            completion_signal=row[10]
        )

    def _row_to_memory_record(self, row) -> MemoryRecord:
        """Convert database row to MemoryRecord."""
        return MemoryRecord(
            memory_id=row[0],
            content=row[1],
            embedding_vector=row[2],
            memory_type=row[3],
            source_type=row[4],
            confidence_score=row[5],
            created_at=datetime.fromisoformat(row[6]),
            last_accessed=datetime.fromisoformat(row[7]),
            access_count=row[8]
        )

    def close(self) -> None:
        """Close the brain database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
