"""
Memory management system for AI agents.
Handles storage, retrieval, and organization of agent memories.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import sqlite3
import uuid
import math
from collections import defaultdict

from shared.interfaces.agent_personality import MemoryManager, AgentMemory
from shared.models.agent_models import AgentMemoryItem


class MemorySystem(MemoryManager):
    """
    Core memory management system for AI agents.
    Implements storage, retrieval, and decay mechanisms.
    """

    def __init__(self, database_path: str = "agent_memories.db"):
        """
        Initialize memory system.

        Args:
            database_path: Path to SQLite database for memory storage
        """
        self.database_path = database_path
        self.memory_cache: Dict[str, List[AgentMemoryItem]] = defaultdict(list)
        self.decay_rate = 0.1  # Memory decay rate per day
        self._initialize_database()
        self._load_recent_memories()

    def _initialize_database(self) -> None:
        """Initialize database tables for memory storage."""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        # Memories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                memory_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                content TEXT NOT NULL,
                importance INTEGER NOT NULL,
                tags TEXT NOT NULL,
                context TEXT NOT NULL,
                created_at TEXT NOT NULL,
                accessed_at TEXT NOT NULL,
                access_count INTEGER NOT NULL DEFAULT 0,
                retention_score REAL NOT NULL DEFAULT 1.0
            )
        """)

        # Memory associations table for semantic connections
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_associations (
                association_id TEXT PRIMARY KEY,
                memory1_id TEXT NOT NULL,
                memory2_id TEXT NOT NULL,
                association_type TEXT NOT NULL,
                strength REAL NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (memory1_id) REFERENCES memories (memory_id),
                FOREIGN KEY (memory2_id) REFERENCES memories (memory_id)
            )
        """)

        # Memory search index for full-text search
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS memory_search 
            USING fts5(memory_id, content, tags, content='memories', content_rowid='rowid')
        """)

        conn.commit()
        conn.close()

    def _load_recent_memories(self) -> None:
        """Load recent memories into cache for faster access."""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        # Load memories accessed in the last 7 days
        cutoff_date = (datetime.now() - timedelta(days=7)).isoformat()
        cursor.execute("""
            SELECT * FROM memories 
            WHERE accessed_at > ? 
            ORDER BY accessed_at DESC 
            LIMIT 1000
        """, (cutoff_date,))

        rows = cursor.fetchall()
        for row in rows:
            memory_item = self._row_to_memory_item(row)
            self.memory_cache[memory_item.agent_id].append(memory_item)

        conn.close()

    def _row_to_memory_item(self, row: tuple) -> AgentMemoryItem:
        """Convert database row to AgentMemoryItem."""
        return AgentMemoryItem(
            memory_id=row[0],
            agent_id=row[1],
            memory_type=row[2],
            content=json.loads(row[3]),
            importance=row[4],
            tags=json.loads(row[5]),
            context=json.loads(row[6]),
            created_at=datetime.fromisoformat(row[7]),
            accessed_at=datetime.fromisoformat(row[8]),
            access_count=row[9],
            retention_score=row[10]
        )

    def store_memory(self, memory: AgentMemory) -> bool:
        """
        Store a memory for future retrieval.

        Args:
            memory: AgentMemory to store

        Returns:
            True if storage successful
        """
        try:
            memory_item = AgentMemoryItem(
                memory_id=str(uuid.uuid4()),
                agent_id=memory.agent_id,
                memory_type=memory.memory_type,
                content=memory.content,
                importance=memory.importance,
                tags=memory.tags,
                context=memory.context or {}
            )

            # Store in database
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO memories (
                    memory_id, agent_id, memory_type, content, importance,
                    tags, context, created_at, accessed_at, access_count,
                    retention_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                memory_item.memory_id,
                memory_item.agent_id,
                memory_item.memory_type,
                json.dumps(memory_item.content),
                memory_item.importance,
                json.dumps(memory_item.tags),
                json.dumps(memory_item.context),
                memory_item.created_at.isoformat(),
                memory_item.accessed_at.isoformat(),
                memory_item.access_count,
                memory_item.retention_score
            ))

            # Update search index
            cursor.execute("""
                INSERT INTO memory_search (memory_id, content, tags)
                VALUES (?, ?, ?)
            """, (
                memory_item.memory_id,
                json.dumps(memory_item.content),
                ' '.join(memory_item.tags)
            ))

            conn.commit()
            conn.close()

            # Add to cache
            self.memory_cache[memory.agent_id].append(memory_item)
            
            # Keep cache size manageable
            if len(self.memory_cache[memory.agent_id]) > 100:
                self.memory_cache[memory.agent_id] = sorted(
                    self.memory_cache[memory.agent_id],
                    key=lambda m: m.accessed_at,
                    reverse=True
                )[:100]

            return True

        except Exception as e:
            print(f"Error storing memory: {e}")
            return False

    def retrieve_memories(
        self,
        agent_id: str,
        memory_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[AgentMemory]:
        """
        Retrieve memories based on criteria.

        Args:
            agent_id: ID of the agent
            memory_type: Filter by memory type
            tags: Filter by tags (matches any tag)
            limit: Maximum number of memories to return

        Returns:
            List of matching memories
        """
        # First check cache
        cached_memories = self.memory_cache.get(agent_id, [])
        results = []

        for memory_item in cached_memories:
            if memory_type and memory_item.memory_type != memory_type:
                continue
            
            if tags and not any(tag in memory_item.tags for tag in tags):
                continue
            
            # Update access information
            memory_item.access()
            results.append(self._memory_item_to_agent_memory(memory_item))
            
            if len(results) >= limit:
                break

        # If we need more results, query database
        if len(results) < limit:
            additional_needed = limit - len(results)
            db_results = self._query_database_memories(
                agent_id, memory_type, tags, additional_needed, exclude_cached=True
            )
            results.extend(db_results)

        # Update database with access information
        self._update_memory_access(results)

        # Apply memory decay
        self._apply_memory_decay(results)

        # Sort by importance and recency
        results.sort(key=lambda m: (m.importance, m.timestamp), reverse=True)

        return results[:limit]

    def _memory_item_to_agent_memory(self, item: AgentMemoryItem) -> AgentMemory:
        """Convert AgentMemoryItem to AgentMemory."""
        return AgentMemory(
            agent_id=item.agent_id,
            memory_type=item.memory_type,
            content=item.content,
            timestamp=item.created_at,
            importance=item.importance,
            tags=item.tags,
            context=item.context
        )

    def _query_database_memories(
        self,
        agent_id: str,
        memory_type: Optional[str],
        tags: Optional[List[str]],
        limit: int,
        exclude_cached: bool = False
    ) -> List[AgentMemory]:
        """Query database for memories."""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        # Build query
        conditions = ["agent_id = ?"]
        params = [agent_id]

        if memory_type:
            conditions.append("memory_type = ?")
            params.append(memory_type)

        if exclude_cached:
            cached_ids = [m.memory_id for m in self.memory_cache.get(agent_id, [])]
            if cached_ids:
                placeholders = ','.join('?' * len(cached_ids))
                conditions.append(f"memory_id NOT IN ({placeholders})")
                params.extend(cached_ids)

        query = f"""
            SELECT * FROM memories 
            WHERE {' AND '.join(conditions)}
            ORDER BY importance DESC, accessed_at DESC
            LIMIT ?
        """
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        memories = []
        for row in rows:
            memory_item = self._row_to_memory_item(row)
            
            # Filter by tags if specified
            if tags and not any(tag in memory_item.tags for tag in tags):
                continue
                
            memories.append(self._memory_item_to_agent_memory(memory_item))

        conn.close()
        return memories

    def search_memories(
        self,
        agent_id: str,
        query: str,
        memory_type: Optional[str] = None
    ) -> List[AgentMemory]:
        """
        Search memories using semantic search.

        Args:
            agent_id: ID of the agent
            query: Search query
            memory_type: Filter by memory type

        Returns:
            List of matching memories
        """
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        # Use FTS5 for full-text search
        search_query = f"""
            SELECT m.* FROM memories m
            JOIN memory_search ms ON m.memory_id = ms.memory_id
            WHERE m.agent_id = ? AND ms.memory_search MATCH ?
        """
        params = [agent_id, query]

        if memory_type:
            search_query += " AND m.memory_type = ?"
            params.append(memory_type)

        search_query += " ORDER BY rank LIMIT 20"

        cursor.execute(search_query, params)
        rows = cursor.fetchall()

        memories = []
        for row in rows:
            memory_item = self._row_to_memory_item(row)
            memories.append(self._memory_item_to_agent_memory(memory_item))

        conn.close()

        # Apply semantic relevance scoring
        scored_memories = self._score_semantic_relevance(memories, query)
        return [m for m, score in scored_memories if score > 0.3]

    def _score_semantic_relevance(
        self,
        memories: List[AgentMemory],
        query: str
    ) -> List[Tuple[AgentMemory, float]]:
        """Score memories by semantic relevance to query."""
        query_words = set(query.lower().split())
        scored_memories = []

        for memory in memories:
            # Simple keyword-based scoring (could be enhanced with embeddings)
            content_text = json.dumps(memory.content).lower()
            content_words = set(content_text.split())
            
            # Calculate overlap
            overlap = len(query_words.intersection(content_words))
            total_words = len(query_words.union(content_words))
            
            if total_words > 0:
                score = overlap / total_words
                # Boost score based on importance
                score *= (1.0 + memory.importance / 10.0)
                scored_memories.append((memory, score))

        # Sort by score
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        return scored_memories

    def update_memory_importance(
        self,
        memory_id: str,
        new_importance: int
    ) -> bool:
        """
        Update the importance score of a memory.

        Args:
            memory_id: ID of the memory to update
            new_importance: New importance score (1-10)

        Returns:
            True if update successful
        """
        if not 1 <= new_importance <= 10:
            return False

        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE memories 
                SET importance = ?, accessed_at = ?
                WHERE memory_id = ?
            """, (new_importance, datetime.now().isoformat(), memory_id))

            conn.commit()
            conn.close()

            # Update cache if present
            for agent_memories in self.memory_cache.values():
                for memory in agent_memories:
                    if memory.memory_id == memory_id:
                        memory.importance = new_importance
                        memory.accessed_at = datetime.now()
                        break

            return True

        except Exception as e:
            print(f"Error updating memory importance: {e}")
            return False

    def forget_memories(
        self,
        agent_id: str,
        criteria: Dict[str, Any]
    ) -> int:
        """
        Remove memories based on criteria.

        Args:
            agent_id: ID of the agent
            criteria: Criteria for memory removal

        Returns:
            Number of memories removed
        """
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            # Build deletion criteria
            conditions = ["agent_id = ?"]
            params = [agent_id]

            if 'memory_type' in criteria:
                conditions.append("memory_type = ?")
                params.append(criteria['memory_type'])

            if 'importance_below' in criteria:
                conditions.append("importance < ?")
                params.append(criteria['importance_below'])

            if 'older_than_days' in criteria:
                cutoff_date = (datetime.now() - timedelta(days=criteria['older_than_days']))
                conditions.append("created_at < ?")
                params.append(cutoff_date.isoformat())

            if 'retention_below' in criteria:
                conditions.append("retention_score < ?")
                params.append(criteria['retention_below'])

            # Get memory IDs to delete
            select_query = f"""
                SELECT memory_id FROM memories 
                WHERE {' AND '.join(conditions)}
            """
            cursor.execute(select_query, params)
            memory_ids = [row[0] for row in cursor.fetchall()]

            if not memory_ids:
                return 0

            # Delete from search index
            placeholders = ','.join('?' * len(memory_ids))
            cursor.execute(f"""
                DELETE FROM memory_search 
                WHERE memory_id IN ({placeholders})
            """, memory_ids)

            # Delete memories
            cursor.execute(f"""
                DELETE FROM memories 
                WHERE memory_id IN ({placeholders})
            """, memory_ids)

            # Delete associations
            cursor.execute(f"""
                DELETE FROM memory_associations 
                WHERE memory1_id IN ({placeholders}) 
                OR memory2_id IN ({placeholders})
            """, memory_ids + memory_ids)

            conn.commit()
            conn.close()

            # Remove from cache
            if agent_id in self.memory_cache:
                self.memory_cache[agent_id] = [
                    m for m in self.memory_cache[agent_id] 
                    if m.memory_id not in memory_ids
                ]

            return len(memory_ids)

        except Exception as e:
            print(f"Error forgetting memories: {e}")
            return 0

    def _update_memory_access(self, memories: List[AgentMemory]) -> None:
        """Update access information for memories."""
        if not memories:
            return

        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            for memory in memories:
                # Find corresponding memory_id (simplified approach)
                cursor.execute("""
                    SELECT memory_id FROM memories 
                    WHERE agent_id = ? AND memory_type = ? AND created_at = ?
                """, (memory.agent_id, memory.memory_type, memory.timestamp.isoformat()))
                
                result = cursor.fetchone()
                if result:
                    memory_id = result[0]
                    cursor.execute("""
                        UPDATE memories 
                        SET accessed_at = ?, access_count = access_count + 1
                        WHERE memory_id = ?
                    """, (datetime.now().isoformat(), memory_id))

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"Error updating memory access: {e}")

    def _apply_memory_decay(self, memories: List[AgentMemory]) -> None:
        """Apply decay to memory retention scores."""
        current_time = datetime.now()
        
        for memory in memories:
            # Calculate days since creation
            days_old = (current_time - memory.timestamp).days
            
            # Apply exponential decay
            decay_factor = math.exp(-self.decay_rate * days_old)
            
            # Adjust based on importance (important memories decay slower)
            importance_factor = 1.0 + (memory.importance - 5) * 0.1
            
            # Calculate new retention score
            new_retention = decay_factor * importance_factor
            
            # Update in database (simplified - would batch in production)
            self._update_retention_score(memory, new_retention)

    def _update_retention_score(self, memory: AgentMemory, new_score: float) -> None:
        """Update retention score for a memory."""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE memories 
                SET retention_score = ?
                WHERE agent_id = ? AND memory_type = ? AND created_at = ?
            """, (new_score, memory.agent_id, memory.memory_type, 
                  memory.timestamp.isoformat()))

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"Error updating retention score: {e}")

    def create_memory_association(
        self,
        memory1_id: str,
        memory2_id: str,
        association_type: str,
        strength: float
    ) -> bool:
        """
        Create an association between two memories.

        Args:
            memory1_id: ID of first memory
            memory2_id: ID of second memory
            association_type: Type of association
            strength: Strength of association (0.0-1.0)

        Returns:
            True if association created successfully
        """
        if not 0.0 <= strength <= 1.0:
            return False

        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            association_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO memory_associations (
                    association_id, memory1_id, memory2_id, 
                    association_type, strength, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                association_id, memory1_id, memory2_id,
                association_type, strength, datetime.now().isoformat()
            ))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"Error creating memory association: {e}")
            return False

    def get_associated_memories(
        self,
        memory_id: str,
        association_type: Optional[str] = None
    ) -> List[str]:
        """
        Get memories associated with a given memory.

        Args:
            memory_id: ID of the reference memory
            association_type: Filter by association type

        Returns:
            List of associated memory IDs
        """
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            query = """
                SELECT memory2_id FROM memory_associations 
                WHERE memory1_id = ?
            """
            params = [memory_id]

            if association_type:
                query += " AND association_type = ?"
                params.append(association_type)

            query += " ORDER BY strength DESC"

            cursor.execute(query, params)
            results = [row[0] for row in cursor.fetchall()]

            conn.close()
            return results

        except Exception as e:
            print(f"Error getting associated memories: {e}")
            return []

    def cleanup_old_memories(self, days_threshold: int = 365) -> int:
        """
        Clean up very old memories with low retention scores.

        Args:
            days_threshold: Delete memories older than this many days

        Returns:
            Number of memories cleaned up
        """
        cutoff_date = datetime.now() - timedelta(days=days_threshold)
        
        criteria = {
            'older_than_days': days_threshold,
            'retention_below': 0.1,
            'importance_below': 3
        }
        
        # Get all agents and clean up their old memories
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT agent_id FROM memories")
        agent_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        total_cleaned = 0
        for agent_id in agent_ids:
            cleaned = self.forget_memories(agent_id, criteria)
            total_cleaned += cleaned
        
        return total_cleaned