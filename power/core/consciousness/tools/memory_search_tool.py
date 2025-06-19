"""
Memory Search Tool: Semantic search and knowledge retrieval.

Provides sophisticated memory search capabilities for the consciousness system,
enabling contextual knowledge retrieval and associative memory operations.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from ..memory_manager import MemoryManager, MemorySearchResult

logger = logging.getLogger(__name__)


@dataclass
class SearchContext:
    """Context for memory search operations."""
    query_intent: str  # question, fact_lookup, pattern_search, association
    domain: Optional[str]  # programming, research, conversation, etc.
    time_scope: Optional[str]  # recent, session, all
    confidence_threshold: float


class MemorySearchTool:
    """
    Advanced memory search tool with semantic understanding.

    Provides natural language queries against the knowledge store with
    contextual understanding and intelligent result ranking.
    """

    def __init__(self, memory_manager: MemoryManager):
        """
        Initialize the Memory Search Tool.

        Args:
            memory_manager: Memory management system
        """
        self.memory_manager = memory_manager
        self.search_history: List[Dict[str, Any]] = []
        self.common_queries: Dict[str, int] = {}

    async def search(self, query: str, context: Optional[SearchContext] = None,
                    limit: int = 10) -> List[MemorySearchResult]:
        """
        Perform semantic search across stored memories.

        Args:
            query: Natural language search query
            context: Optional search context for refinement
            limit: Maximum number of results

        Returns:
            List of relevant memory search results
        """
        # Use default context if none provided
        if context is None:
            context = SearchContext(
                query_intent=self._detect_query_intent(query),
                domain=None,
                time_scope="all",
                confidence_threshold=0.5
            )

        # Enhance query based on context
        enhanced_query = self._enhance_query(query, context)

        # Perform the search
        results = self.memory_manager.search_memories(
            query=enhanced_query,
            memory_type=None,
            limit=limit,
            similarity_threshold=context.confidence_threshold
        )

        # Post-process results based on context
        filtered_results = self._filter_results_by_context(results, context)

        # Record search for analysis
        self._record_search(query, context, len(filtered_results))

        logger.info("Memory search '%s' returned %d results", query, len(filtered_results))
        return filtered_results

    async def find_related_memories(self, memory_id: str,
                                  max_associations: int = 5) -> List[Dict[str, Any]]:
        """
        Find memories related to a specific memory through associations.

        Args:
            memory_id: ID of the seed memory
            max_associations: Maximum number of related memories

        Returns:
            List of related memory records with relationship info
        """
        # Get associative memories from memory manager
        related_memories = self.memory_manager.get_associative_memories(
            seed_memory_id=memory_id,
            max_associations=max_associations
        )

        # Format results with relationship information
        formatted_results = []
        for memory in related_memories:
            formatted_results.append({
                "memory_id": memory.memory_id,
                "content": memory.content,
                "memory_type": memory.memory_type,
                "confidence": memory.confidence_score,
                "relationship": "associative",  # Would be more specific in full implementation
                "access_count": memory.access_count
            })

        logger.info("Found %d related memories for %s", len(formatted_results), memory_id)
        return formatted_results

    async def ask_memory(self, question: str, domain: Optional[str] = None) -> Dict[str, Any]:
        """
        Ask a question and get an answer based on stored memories.

        Args:
            question: Natural language question
            domain: Optional domain filter

        Returns:
            Dictionary with answer and supporting memories
        """
        # Search for relevant memories
        search_context = SearchContext(
            query_intent="question",
            domain=domain,
            time_scope="all",
            confidence_threshold=0.6
        )

        relevant_memories = await self.search(question, search_context, limit=5)

        if not relevant_memories:
            return {
                "answer": "I don't have enough information to answer that question.",
                "confidence": 0.0,
                "supporting_memories": [],
                "suggestions": ["Try rephrasing the question", "Add more context"]
            }

        # Synthesize answer from memories (simplified implementation)
        answer = self._synthesize_answer(question, relevant_memories)

        # Calculate confidence based on memory relevance
        avg_confidence = sum(r.similarity_score for r in relevant_memories) / len(relevant_memories)

        return {
            "answer": answer,
            "confidence": avg_confidence,
            "supporting_memories": [
                {
                    "content": r.memory_record.content[:200] + "...",
                    "similarity": r.similarity_score,
                    "source": r.memory_record.source_type
                }
                for r in relevant_memories
            ],
            "memory_count": len(relevant_memories)
        }

    async def search_by_pattern(self, pattern_description: str,
                              memory_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Search for memories that match a specific pattern.

        Args:
            pattern_description: Description of the pattern to find
            memory_types: Optional list of memory types to search

        Returns:
            List of memories matching the pattern
        """
        results = []

        # Search each memory type if specified
        types_to_search = memory_types or ["experience", "pattern", "task_execution"]

        for memory_type in types_to_search:
            type_results = self.memory_manager.search_memories(
                query=pattern_description,
                memory_type=memory_type,
                limit=10,
                similarity_threshold=0.7
            )

            for result in type_results:
                results.append({
                    "memory_id": result.memory_record.memory_id,
                    "content": result.memory_record.content,
                    "type": result.memory_record.memory_type,
                    "pattern_match": result.similarity_score,
                    "created_at": result.memory_record.created_at.isoformat()
                })

        # Sort by pattern match score
        results.sort(key=lambda x: x["pattern_match"], reverse=True)

        logger.info("Pattern search '%s' found %d matches", pattern_description, len(results))
        return results

    async def get_memory_timeline(self, time_period: str = "recent",
                                 memory_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get a timeline of memories for a specific period.

        Args:
            time_period: "recent", "session", "today", "week"
            memory_type: Optional memory type filter

        Returns:
            List of memories in chronological order
        """
        # Get memories (simplified - would implement proper time filtering)
        memories = self.memory_manager.search_memories(
            memory_type=memory_type,
            limit=50
        )

        # Format timeline
        timeline = []
        for result in memories:
            memory = result.memory_record
            timeline.append({
                "timestamp": memory.created_at.isoformat(),
                "memory_id": memory.memory_id,
                "content_preview": memory.content[:100] + "...",
                "type": memory.memory_type,
                "confidence": memory.confidence_score,
                "access_count": memory.access_count
            })

        # Sort by timestamp (most recent first)
        timeline.sort(key=lambda x: x["timestamp"], reverse=True)

        # Limit based on time period
        if time_period == "recent":
            timeline = timeline[:10]
        elif time_period == "session":
            timeline = timeline[:20]

        logger.info("Generated timeline with %d memories for %s", len(timeline), time_period)
        return timeline

    def get_search_analytics(self) -> Dict[str, Any]:
        """
        Get analytics about search patterns and memory usage.

        Returns:
            Dictionary containing search analytics
        """
        total_searches = len(self.search_history)

        if total_searches == 0:
            return {
                "total_searches": 0,
                "most_common_queries": [],
                "search_success_rate": 0.0,
                "average_results": 0.0
            }

        # Calculate analytics
        successful_searches = sum(1 for s in self.search_history if s["result_count"] > 0)
        success_rate = successful_searches / total_searches

        avg_results = sum(s["result_count"] for s in self.search_history) / total_searches

        # Get most common query types
        query_intents = {}
        for search in self.search_history:
            intent = search["context"]["query_intent"]
            query_intents[intent] = query_intents.get(intent, 0) + 1

        top_intents = sorted(query_intents.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "total_searches": total_searches,
            "search_success_rate": success_rate,
            "average_results": avg_results,
            "most_common_intents": dict(top_intents),
            "recent_searches": self.search_history[-5:] if self.search_history else []
        }

    def _detect_query_intent(self, query: str) -> str:
        """Detect the intent behind a search query."""
        query_lower = query.lower()

        question_words = ["what", "how", "why", "when", "where", "who", "which"]
        if any(word in query_lower for word in question_words):
            return "question"

        if any(word in query_lower for word in ["find", "search", "look for"]):
            return "fact_lookup"

        if any(word in query_lower for word in ["pattern", "similar", "like"]):
            return "pattern_search"

        if any(word in query_lower for word in ["related", "connected", "associated"]):
            return "association"

        return "general_search"

    def _enhance_query(self, query: str, context: SearchContext) -> str:
        """Enhance the query based on context."""
        enhanced = query

        # Add domain context
        if context.domain:
            enhanced = f"{context.domain} {enhanced}"

        # Modify based on intent
        if context.query_intent == "pattern_search":
            enhanced = f"pattern similar to {enhanced}"
        elif context.query_intent == "association":
            enhanced = f"related to {enhanced}"

        return enhanced

    def _filter_results_by_context(self, results: List[MemorySearchResult],
                                 context: SearchContext) -> List[MemorySearchResult]:
        """Filter and rank results based on search context."""
        filtered = []

        for result in results:
            memory = result.memory_record

            # Apply confidence threshold
            if result.similarity_score < context.confidence_threshold:
                continue

            # Apply domain filter
            if context.domain and context.domain.lower() not in memory.content.lower():
                # Reduce score but don't eliminate
                result.similarity_score *= 0.8

            # Apply time scope (simplified)
            if context.time_scope == "recent":
                # Boost recent memories
                if memory.access_count > 0:
                    result.similarity_score *= 1.1

            filtered.append(result)

        # Re-sort by adjusted similarity scores
        filtered.sort(key=lambda x: x.similarity_score, reverse=True)

        return filtered

    def _synthesize_answer(self, question: str,
                          memories: List[MemorySearchResult]) -> str:
        """Synthesize an answer from relevant memories."""
        _ = question  # Question used for context in full implementation
        if not memories:
            return "No relevant information found."

        # Simple synthesis - combine content from top memories
        top_memory = memories[0].memory_record

        # Extract relevant portion of the content (simplified)
        content = top_memory.content
        if len(content) > 300:
            content = content[:300] + "..."

        answer = f"Based on my memory: {content}"

        if len(memories) > 1:
            answer += f" (Found {len(memories)} related memories)"

        return answer

    def _record_search(self, query: str, context: SearchContext, result_count: int) -> None:
        """Record search for analytics."""
        search_record = {
            "query": query,
            "context": {
                "query_intent": context.query_intent,
                "domain": context.domain,
                "time_scope": context.time_scope,
                "confidence_threshold": context.confidence_threshold
            },
            "result_count": result_count,
            "timestamp": "now"  # Would use actual timestamp
        }

        self.search_history.append(search_record)

        # Keep only recent searches (limit memory usage)
        if len(self.search_history) > 100:
            self.search_history = self.search_history[-50:]

        # Update common queries
        intent = context.query_intent
        self.common_queries[intent] = self.common_queries.get(intent, 0) + 1
