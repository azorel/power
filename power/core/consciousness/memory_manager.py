"""
Memory Manager: Vector embeddings and semantic search for AI consciousness.

This module implements sophisticated memory management with vector embeddings,
semantic search, and associative memory retrieval for the Power Brain system.
"""

import hashlib
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
import numpy as np

from .brain_database import PowerBrain, MemoryRecord

logger = logging.getLogger(__name__)


@dataclass
class MemorySearchResult:
    """Result from semantic memory search."""
    memory_record: MemoryRecord
    similarity_score: float
    relevance_rank: int


@dataclass
class MemoryContext:
    """Context for memory storage and retrieval."""
    user_id: str
    session_id: str
    task_id: Optional[str]
    agent_id: Optional[str]
    conversation_context: Dict[str, Any]


class MemoryManager:
    """
    Advanced memory management with vector embeddings and semantic search.

    Provides human-like associative memory through vector similarity search,
    knowledge graph traversal, and intelligent memory consolidation.
    """

    def __init__(self, brain: PowerBrain, embedding_model: Optional[str] = None):
        """
        Initialize the Memory Manager.

        Args:
            brain: PowerBrain database instance
            embedding_model: Model for generating embeddings (future integration)
        """
        self.brain = brain
        self.embedding_model = embedding_model
        self.embedding_cache: Dict[str, np.ndarray] = {}
        self._memory_consolidation_threshold = 100

    def store_memory(self, content: str, memory_type: str,
                    context: MemoryContext,
                    confidence_score: float = 1.0) -> str:
        """
        Store a memory with vector embedding and context.

        Args:
            content: The memory content to store
            memory_type: Type of memory (conversation, fact, skill, etc.)
            context: Context information for the memory
            confidence_score: Confidence in the memory accuracy

        Returns:
            Generated memory ID
        """
        # Generate unique memory ID
        memory_id = self._generate_memory_id(content, context)

        # Generate embedding vector (placeholder for now)
        embedding_vector = self._generate_embedding(content)

        # Create memory record
        memory_record = MemoryRecord(
            memory_id=memory_id,
            content=content,
            embedding_vector=embedding_vector,
            memory_type=memory_type,
            source_type=self._determine_source_type(context),
            confidence_score=confidence_score,
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
            access_count=0
        )

        # Store in brain database
        self.brain.store_memory(memory_record)

        # Extract and store knowledge graph relationships
        self._extract_knowledge_relationships(content, memory_id)

        logger.info("Stored memory: %s (%s)", memory_id, memory_type)
        return memory_id

    def search_memories(self, query: str, memory_type: Optional[str] = None,
                       limit: int = 10,
                       similarity_threshold: float = 0.7) -> List[MemorySearchResult]:
        """
        Semantic search for relevant memories.

        Args:
            query: Search query
            memory_type: Optional memory type filter
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score

        Returns:
            List of relevant memory search results
        """
        # Generate query embedding
        query_embedding = self._generate_embedding(query)

        # Get candidate memories from database
        candidate_memories = self.brain.search_memories(memory_type, limit * 2)

        # Calculate similarity scores
        results = []
        for memory in candidate_memories:
            if memory.embedding_vector:
                memory_embedding = np.frombuffer(memory.embedding_vector, dtype=np.float32)
                similarity = self._calculate_similarity(query_embedding, memory_embedding)

                if similarity >= similarity_threshold:
                    results.append(MemorySearchResult(
                        memory_record=memory,
                        similarity_score=similarity,
                        relevance_rank=len(results) + 1
                    ))

        # Sort by similarity and update access patterns
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        results = results[:limit]

        # Update access counts for retrieved memories
        for result in results:
            self._update_memory_access(result.memory_record.memory_id)

        logger.info("Found %d relevant memories for query: %s", len(results), query)
        return results

    def get_associative_memories(self, seed_memory_id: str,
                                max_associations: int = 5) -> List[MemoryRecord]:
        """
        Get memories associated with a seed memory through the knowledge graph.

        Args:
            seed_memory_id: Starting memory ID
            max_associations: Maximum number of associations to return

        Returns:
            List of associated memory records
        """
        # Get the seed memory
        seed_memories = self.brain.search_memories(limit=1000)
        seed_memory = next((m for m in seed_memories if m.memory_id == seed_memory_id), None)

        if not seed_memory:
            return []

        # Extract key concepts from seed memory
        concepts = self._extract_concepts(seed_memory.content)

        # Find related concepts through knowledge graph
        related_concepts = []
        for concept in concepts:
            related = self.brain.get_related_concepts(concept)
            related_concepts.extend([r[0] for r in related])

        # Find memories containing related concepts
        associated_memories = []
        for concept in related_concepts[:max_associations * 2]:
            concept_memories = self.search_memories(concept, limit=3, similarity_threshold=0.5)
            for result in concept_memories:
                if (result.memory_record.memory_id != seed_memory_id and
                    result.memory_record not in associated_memories):
                    associated_memories.append(result.memory_record)

        return associated_memories[:max_associations]

    def consolidate_memories(self, session_id: str) -> Dict[str, Any]:
        """
        Consolidate memories for long-term storage and pattern recognition.

        Args:
            session_id: Session to consolidate memories for

        Returns:
            Consolidation statistics
        """
        # Get recent memories for consolidation
        recent_memories = self.brain.search_memories(limit=self._memory_consolidation_threshold)

        if len(recent_memories) < 10:
            return {"status": "insufficient_memories", "count": len(recent_memories)}

        # Group similar memories
        memory_clusters = self._cluster_similar_memories(recent_memories)

        # Create consolidated memory entries
        consolidated_count = 0
        for cluster in memory_clusters:
            if len(cluster) >= 3:  # Only consolidate clusters with multiple memories
                consolidated_content = self._create_consolidated_memory(cluster)
                self.store_memory(
                    content=consolidated_content,
                    memory_type="consolidated",
                    context=MemoryContext(
                        user_id="system",
                        session_id=session_id,
                        task_id=None,
                        agent_id="memory_manager",
                        conversation_context={"consolidation": True}
                    ),
                    confidence_score=0.8
                )
                consolidated_count += 1

        logger.info("Consolidated %d memory clusters", consolidated_count)
        return {
            "status": "completed",
            "clusters_found": len(memory_clusters),
            "consolidated_memories": consolidated_count,
            "total_memories": len(recent_memories)
        }

    def get_memory_insights(self, context: MemoryContext = None) -> Dict[str, Any]:
        """
        Generate insights about stored memories and learning patterns.

        Args:
            context: Context for insight generation (unused)

        Returns:
            Dictionary containing memory insights
        """
        _ = context  # Unused parameter
        stats = self.brain.get_brain_stats()

        # Get top memory types
        memory_types = stats.get('memory_types', {})
        top_types = sorted(memory_types.items(), key=lambda x: x[1], reverse=True)[:5]

        # Get recent high-confidence memories
        recent_memories = self.brain.search_memories(limit=20)
        high_confidence = [m for m in recent_memories if m.confidence_score > 0.8]

        # Analyze memory access patterns
        most_accessed = sorted(recent_memories, key=lambda x: x.access_count, reverse=True)[:10]

        insights = {
            "total_memories": stats.get('knowledge_store_count', 0),
            "memory_type_distribution": dict(top_types),
            "high_confidence_memories": len(high_confidence),
            "most_accessed_memories": [
                {"id": m.memory_id, "content_preview": m.content[:100],
                 "access_count": m.access_count}
                for m in most_accessed
            ],
            "knowledge_graph_edges": stats.get('knowledge_graph_count', 0),
            "consolidation_candidates": len(recent_memories) // 5
        }

        return insights

    def _generate_memory_id(self, content: str, context: MemoryContext) -> str:
        """Generate unique memory ID based on content and context."""
        _ = context  # Context reserved for future use in ID generation
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"mem_{timestamp}_{content_hash}"

    def _generate_embedding(self, text: str) -> bytes:
        """
        Generate vector embedding for text (placeholder implementation).

        Args:
            text: Text to embed

        Returns:
            Serialized embedding vector
        """
        # Placeholder: Simple hash-based pseudo-embedding
        # In production, this would use a real embedding model
        text_hash = hashlib.sha256(text.encode()).digest()
        # Convert to 128-dimensional float vector
        pseudo_embedding = np.frombuffer(text_hash, dtype=np.uint8)[:32]
        normalized = pseudo_embedding.astype(np.float32) / 255.0

        # Pad to 128 dimensions
        if len(normalized) < 128:
            padding = np.zeros(128 - len(normalized), dtype=np.float32)
            normalized = np.concatenate([normalized, padding])

        return normalized[:128].tobytes()

    def _calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between embeddings."""
        if len(embedding1) != len(embedding2):
            return 0.0

        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    def _determine_source_type(self, context: MemoryContext) -> str:
        """Determine the source type based on context."""
        if context.agent_id:
            return "agent_output"
        if context.task_id:
            return "task_execution"
        if context.conversation_context:
            return "conversation"
        return "system"

    def _extract_concepts(self, text: str) -> List[str]:
        """Extract key concepts from text for knowledge graph."""
        # Simple concept extraction (placeholder)
        words = text.lower().split()
        # Filter for potential concepts (nouns, technical terms)
        concepts = [w for w in words if len(w) > 3 and w.isalpha()]
        return list(set(concepts))[:10]  # Limit to top 10 unique concepts

    def _extract_knowledge_relationships(self, content: str, memory_id: str) -> None:
        """Extract and store relationships in the knowledge graph."""
        concepts = self._extract_concepts(content)

        # Create relationships between concepts found in the same memory
        for i, concept1 in enumerate(concepts):
            for concept2 in concepts[i+1:]:
                self.brain.add_knowledge_edge(
                    source=concept1,
                    target=concept2,
                    relationship="co_occurs_with",
                    confidence=0.7,
                    evidence=f"Found together in memory {memory_id}"
                )

    def _update_memory_access(self, memory_id: str) -> None:
        """Update memory access count and timestamp."""
        # This would be implemented as an SQL UPDATE statement
        # For now, we'll skip the implementation detail
        # Future: Implement SQL UPDATE for access tracking

    def _cluster_similar_memories(self, memories: List[MemoryRecord]) -> List[List[MemoryRecord]]:
        """Group similar memories for consolidation."""
        clusters = []
        processed = set()

        for i, memory1 in enumerate(memories):
            if memory1.memory_id in processed:
                continue

            cluster = [memory1]
            processed.add(memory1.memory_id)

            # Find similar memories
            if memory1.embedding_vector:
                embedding1 = np.frombuffer(memory1.embedding_vector, dtype=np.float32)

                for memory2 in memories[i+1:]:
                    if memory2.memory_id in processed or not memory2.embedding_vector:
                        continue

                    embedding2 = np.frombuffer(memory2.embedding_vector, dtype=np.float32)
                    similarity = self._calculate_similarity(embedding1, embedding2)

                    if similarity > 0.8:  # High similarity threshold for clustering
                        cluster.append(memory2)
                        processed.add(memory2.memory_id)

            if len(cluster) > 1:
                clusters.append(cluster)

        return clusters

    def _create_consolidated_memory(self, memory_cluster: List[MemoryRecord]) -> str:
        """Create a consolidated memory from a cluster of similar memories."""
        # Simple consolidation: combine content with summary
        contents = [m.content for m in memory_cluster]
        consolidated = f"Consolidated from {len(contents)} related memories: "
        consolidated += " | ".join(contents[:3])  # Limit to first 3 for brevity

        if len(contents) > 3:
            consolidated += f" ... and {len(contents) - 3} more related items."

        return consolidated
