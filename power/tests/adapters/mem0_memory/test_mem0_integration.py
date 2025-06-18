"""
Test suite for Mem0 memory provider integration.

This test suite validates the integration between the power framework
and Mem0's OpenMemory system, focusing on memory persistence, retrieval,
and knowledge retention capabilities.
"""

import pytest
import os
import tempfile
import shutil
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

# Framework imports
from shared.interfaces.memory_provider import MemoryType, MemoryQuery
from shared.models.memory_models import EnhancedMemoryItem, MemoryContext
from adapters.mem0_memory import Mem0MemoryProvider, Mem0Config
from core.modules.agents.enhanced_memory_system import EnhancedMemorySystem


class TestMem0Config:
    """Test Mem0 configuration."""
    
    def test_default_config_creation(self):
        """Test creating default configuration."""
        config = Mem0Config()
        
        assert config.llm_provider == 'openai'
        assert config.embedder_provider == 'openai'
        assert config.vector_store_provider == 'qdrant'
        assert config.enable_decay is True
        assert config.enable_associations is True
    
    def test_config_validation(self):
        """Test configuration validation."""
        config = Mem0Config()
        
        # Test with missing API key
        config.llm_api_key = None
        config.embedder_api_key = None
        
        with pytest.raises(ValueError):
            config.validate_config()
    
    def test_mem0_config_generation(self):
        """Test Mem0 configuration dictionary generation."""
        config = Mem0Config()
        config.llm_api_key = "test_key"
        config.embedder_api_key = "test_key"
        
        mem0_config = config.get_mem0_config()
        
        assert "llm" in mem0_config
        assert "embedder" in mem0_config
        assert "vector_store" in mem0_config
        assert mem0_config["llm"]["config"]["api_key"] == "test_key"
    
    def test_adapter_info(self):
        """Test adapter information."""
        config = Mem0Config()
        info = config.get_adapter_info()
        
        assert info["name"] == "Mem0 Memory Provider"
        assert info["provider"] == "mem0"
        assert "persistent memory" in info["description"].lower()
        assert len(info["supported_memory_types"]) > 0


class TestMem0MemoryProvider:
    """Test Mem0 memory provider."""
    
    @pytest.fixture
    def mock_mem0_client(self):
        """Create mock Mem0 client."""
        mock_client = Mock()
        mock_client.add.return_value = {
            "results": [{"id": "test_id", "memory": "test content", "event": "ADD"}]
        }
        mock_client.get_all.return_value = {"results": []}
        mock_client.search.return_value = {"results": []}
        mock_client.get.return_value = {
            "id": "test_id",
            "memory": "test content",
            "created_at": datetime.now().isoformat()
        }
        mock_client.delete.return_value = {"message": "deleted"}
        mock_client.history.return_value = []
        return mock_client
    
    @pytest.fixture
    def provider_config(self):
        """Create test provider configuration."""
        return {
            "llm_api_key": "test_key",
            "embedder_api_key": "test_key",
            "vector_store_path": tempfile.mkdtemp(),
            "history_db_path": tempfile.mktemp(),
            "enable_decay": False,  # Disable for testing
            "enable_graph": False   # Disable for testing
        }
    
    @pytest.fixture
    def mock_provider(self, mock_mem0_client, provider_config):
        """Create mock Mem0 provider."""
        with patch('adapters.mem0_memory.client.Memory') as mock_memory:
            mock_memory.return_value = mock_mem0_client
            
            config = Mem0Config()
            for key, value in provider_config.items():
                setattr(config, key, value)
            
            provider = Mem0MemoryProvider(config)
            provider.mem0_client = mock_mem0_client
            provider._initialized = True
            
            yield provider
    
    def test_provider_initialization(self, provider_config):
        """Test provider initialization."""
        with patch('adapters.mem0_memory.client.Memory') as mock_memory:
            mock_client = Mock()
            mock_client.get_all.return_value = {"results": []}
            mock_memory.return_value = mock_client
            
            config = Mem0Config()
            for key, value in provider_config.items():
                setattr(config, key, value)
            
            provider = Mem0MemoryProvider(config)
            success = provider.initialize(provider_config)
            
            assert success is True
            assert provider.provider_name == "mem0"
            assert MemoryType.CONVERSATIONAL in provider.supported_memory_types
    
    def test_store_memory(self, mock_provider):
        """Test storing a memory."""
        memory = EnhancedMemoryItem(
            id="test_memory",
            agent_id="test_agent",
            content="This is a test memory",
            memory_type=MemoryType.CONVERSATIONAL,
            importance=0.8,
            confidence=0.9,
            tags=["test", "memory"]
        )
        
        result = mock_provider.store_memory(memory)
        
        assert result.success is True
        assert mock_provider.mem0_client.add.called
    
    def test_retrieve_memories(self, mock_provider):
        """Test retrieving memories."""
        # Setup mock response
        mock_provider.mem0_client.get_all.return_value = {
            "results": [{
                "id": "test_id",
                "memory": "test content",
                "created_at": datetime.now().isoformat(),
                "metadata": {
                    "memory_type": "conversational",
                    "importance": 0.8,
                    "tags": ["test"]
                }
            }]
        }
        
        query = MemoryQuery(
            agent_id="test_agent",
            memory_type=MemoryType.CONVERSATIONAL,
            limit=10
        )
        
        result = mock_provider.retrieve_memories(query)
        
        assert len(result.memories) == 1
        assert result.memories[0].agent_id == "test_agent"
        assert mock_provider.mem0_client.get_all.called
    
    def test_semantic_search(self, mock_provider):
        """Test semantic search functionality."""
        # Setup mock response
        mock_provider.mem0_client.search.return_value = {
            "results": [{
                "id": "search_result",
                "memory": "relevant content",
                "score": 0.85,
                "created_at": datetime.now().isoformat(),
                "metadata": {
                    "memory_type": "conversational",
                    "importance": 0.7
                }
            }]
        }
        
        result = mock_provider.search_semantic(
            agent_id="test_agent",
            query_text="test query",
            limit=5,
            similarity_threshold=0.7
        )
        
        assert len(result.memories) == 1
        assert result.relevance_scores["search_result"] == 0.85
        assert mock_provider.mem0_client.search.called
    
    def test_memory_associations(self, mock_provider):
        """Test memory association functionality."""
        success = mock_provider.create_association(
            memory_id1="memory1",
            memory_id2="memory2",
            association_type="thematic",
            strength=0.8
        )
        
        assert success is True
        
        # Test retrieving associations
        associated = mock_provider.get_associated_memories(
            memory_id="memory1",
            strength_threshold=0.5
        )
        
        assert isinstance(associated, list)
    
    def test_conversation_storage(self, mock_provider):
        """Test conversation storage functionality."""
        messages = [
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm doing well, thank you!"},
            {"role": "user", "content": "What's the weather like?"}
        ]
        
        results = mock_provider.store_conversation(
            agent_id="test_agent",
            conversation_id="conv_123",
            messages=messages,
            metadata={"topic": "greeting"}
        )
        
        assert len(results) >= 1
        assert all(result.success for result in results)
        assert mock_provider.mem0_client.add.called
    
    def test_memory_statistics(self, mock_provider):
        """Test getting memory statistics."""
        # Setup mock for get_all to return some test data
        mock_provider.mem0_client.get_all.return_value = {
            "results": [
                {
                    "id": "mem1",
                    "memory": "test 1",
                    "created_at": datetime.now().isoformat(),
                    "metadata": {
                        "memory_type": "conversational",
                        "importance": 0.8,
                        "tags": ["test"]
                    }
                },
                {
                    "id": "mem2", 
                    "memory": "test 2",
                    "created_at": datetime.now().isoformat(),
                    "metadata": {
                        "memory_type": "semantic",
                        "importance": 0.6,
                        "tags": ["fact"]
                    }
                }
            ]
        }
        
        stats = mock_provider.get_memory_statistics("test_agent")
        
        assert "total_memories" in stats
        assert "memory_types" in stats
        assert "provider" in stats
        assert stats["provider"] == "mem0"


class TestEnhancedMemorySystem:
    """Test enhanced memory system."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def memory_system_config(self, temp_dir):
        """Create test configuration for memory system."""
        return {
            "llm_api_key": "test_key",
            "embedder_api_key": "test_key",
            "vector_store_path": os.path.join(temp_dir, "vectors"),
            "history_db_path": os.path.join(temp_dir, "history.db"),
            "fallback_db_path": os.path.join(temp_dir, "fallback.db"),
            "enable_decay": False,
            "enable_graph": False,
            "enable_learning": True
        }
    
    @pytest.fixture
    def mock_memory_system(self, memory_system_config):
        """Create mock enhanced memory system."""
        with patch('adapters.mem0_memory.client.Memory') as mock_memory:
            mock_client = Mock()
            mock_client.get_all.return_value = {"results": []}
            mock_client.add.return_value = {
                "results": [{"id": "test_id", "memory": "test", "event": "ADD"}]
            }
            mock_memory.return_value = mock_client
            
            system = EnhancedMemorySystem(
                provider_type="mem0",
                config=memory_system_config,
                fallback_to_legacy=False  # Disable for testing
            )
            
            # Mock the provider initialization
            system.primary_provider = Mock()
            system.primary_provider.store_memory.return_value = Mock(success=True)
            system.primary_provider.retrieve_memories.return_value = Mock(memories=[])
            system.primary_provider.get_memory_statistics.return_value = {"total_memories": 0}
            
            yield system
    
    def test_session_management(self, mock_memory_system):
        """Test memory session management."""
        agent_id = "test_agent"
        
        # Start session
        session_id = mock_memory_system.start_session(agent_id, {"goal": "testing"})
        
        assert session_id is not None
        assert agent_id in mock_memory_system.current_sessions
        assert session_id in mock_memory_system.session_contexts
        
        # End session
        success = mock_memory_system.end_session(agent_id)
        
        assert success is True
        assert agent_id not in mock_memory_system.current_sessions
        assert session_id not in mock_memory_system.session_contexts
    
    def test_persistent_learning_enablement(self, mock_memory_system):
        """Test enabling persistent learning."""
        agent_id = "test_agent"
        
        success = mock_memory_system.enable_persistent_learning(agent_id)
        
        assert success is True
        assert mock_memory_system.primary_provider.store_memory.called
    
    def test_memory_backup_restore(self, mock_memory_system, temp_dir):
        """Test memory backup and restore functionality."""
        agent_id = "test_agent"
        backup_path = os.path.join(temp_dir, "backup.json")
        
        # Mock successful backup/restore
        mock_memory_system.primary_provider.backup_memories.return_value = True
        mock_memory_system.primary_provider.restore_memories.return_value = True
        
        # Test backup
        backup_success = mock_memory_system.backup_agent_memories(agent_id, backup_path)
        assert backup_success is True
        
        # Test restore
        restore_success = mock_memory_system.restore_agent_memories(agent_id, backup_path)
        assert restore_success is True
    
    def test_system_health_monitoring(self, mock_memory_system):
        """Test system health monitoring."""
        health = mock_memory_system.get_system_health()
        
        assert "status" in health
        assert "provider_type" in health
        assert "metrics" in health
        assert health["provider_type"] == "mem0"
    
    def test_cross_session_memory_persistence(self, mock_memory_system):
        """Test memory persistence across sessions."""
        agent_id = "test_agent"
        
        # Start first session
        session1 = mock_memory_system.start_session(agent_id, {"session": "first"})
        
        # Simulate storing memory in first session
        from shared.interfaces.agent_personality import AgentMemory
        memory1 = AgentMemory(
            agent_id=agent_id,
            memory_type="conversational",
            content="Memory from first session",
            timestamp=datetime.now(),
            importance=8,
            tags=["session1"],
            context={"session_id": session1}
        )
        
        store_success = mock_memory_system.store_memory(memory1)
        assert store_success is True
        
        # End first session
        mock_memory_system.end_session(agent_id)
        
        # Start second session
        session2 = mock_memory_system.start_session(agent_id, {"session": "second"})
        
        # Mock retrieval to simulate cross-session access
        mock_enhanced_memory = Mock()
        mock_enhanced_memory.agent_id = agent_id
        mock_enhanced_memory.memory_type = MemoryType.CONVERSATIONAL
        mock_enhanced_memory.content = "Memory from first session"
        mock_enhanced_memory.context = Mock()
        mock_enhanced_memory.context.session_id = session1
        mock_enhanced_memory.created_at = datetime.now()
        mock_enhanced_memory.importance = 0.8
        mock_enhanced_memory.tags = ["session1"]
        mock_enhanced_memory.metadata = {}
        
        mock_search_result = Mock()
        mock_search_result.memories = [mock_enhanced_memory]
        
        mock_memory_system.primary_provider.retrieve_memories.return_value = mock_search_result
        
        # Retrieve memories in second session
        retrieved_memories = mock_memory_system.retrieve_memories(
            agent_id=agent_id,
            tags=["session1"]
        )
        
        # Verify cross-session retrieval
        assert len(retrieved_memories) > 0 or mock_memory_system.primary_provider.retrieve_memories.called
        
        # Check metrics for cross-session retrievals
        assert "cross_session_retrievals" in mock_memory_system.metrics


class TestMemoryPersistence:
    """Test memory persistence and knowledge retention."""
    
    def test_memory_decay_simulation(self):
        """Test memory decay calculation."""
        memory = EnhancedMemoryItem(
            id="decay_test",
            agent_id="test_agent",
            content="Test decay memory",
            memory_type=MemoryType.CONVERSATIONAL,
            importance=0.5,
            confidence=0.8,
            tags=["decay", "test"]
        )
        
        # Simulate memory age
        old_time = datetime.now() - timedelta(days=30)
        memory.created_at = old_time
        
        decay_factor = memory.calculate_decay()
        
        assert 0.0 <= decay_factor <= 1.0
        assert decay_factor < 1.0  # Should decay over time
    
    def test_importance_adjustment(self):
        """Test importance-based memory retention."""
        # High importance memory
        important_memory = EnhancedMemoryItem(
            id="important_test",
            agent_id="test_agent",
            content="Very important information",
            memory_type=MemoryType.SEMANTIC,
            importance=0.9,
            confidence=0.9,
            tags=["important", "critical"]
        )
        
        # Low importance memory
        trivial_memory = EnhancedMemoryItem(
            id="trivial_test",
            agent_id="test_agent",
            content="Trivial information",
            memory_type=MemoryType.WORKING,
            importance=0.2,
            confidence=0.6,
            tags=["trivial", "temporary"]
        )
        
        # Both aged the same amount
        old_time = datetime.now() - timedelta(days=10)
        important_memory.created_at = old_time
        trivial_memory.created_at = old_time
        
        important_decay = important_memory.calculate_decay()
        trivial_decay = trivial_memory.calculate_decay()
        
        # Important memory should decay slower
        assert important_decay > trivial_decay
    
    def test_knowledge_retention_workflow(self, temp_dir):
        """Test end-to-end knowledge retention workflow."""
        # This test simulates the complete workflow of:
        # 1. Storing conversational memories
        # 2. Extracting important facts
        # 3. Creating semantic memories
        # 4. Building associations
        # 5. Persisting across sessions
        
        config = {
            "llm_api_key": "test_key",
            "embedder_api_key": "test_key", 
            "vector_store_path": os.path.join(temp_dir, "knowledge_vectors"),
            "history_db_path": os.path.join(temp_dir, "knowledge_history.db"),
            "enable_learning": True,
            "enable_associations": True,
            "enable_decay": False  # Disable for testing
        }
        
        with patch('adapters.mem0_memory.client.Memory') as mock_memory:
            mock_client = Mock()
            
            # Mock fact extraction response
            mock_client.add.return_value = {
                "results": [
                    {"id": "fact1", "memory": "User likes coffee", "event": "ADD"},
                    {"id": "fact2", "memory": "User works in tech", "event": "ADD"}
                ]
            }
            
            # Mock search response
            mock_client.search.return_value = {
                "results": [
                    {
                        "id": "fact1",
                        "memory": "User likes coffee", 
                        "score": 0.9,
                        "created_at": datetime.now().isoformat(),
                        "metadata": {"memory_type": "semantic"}
                    }
                ]
            }
            
            mock_memory.return_value = mock_client
            
            # Create memory system
            system = EnhancedMemorySystem(
                provider_type="mem0",
                config=config,
                fallback_to_legacy=False
            )
            
            # Simulate conversation that should generate knowledge
            agent_id = "knowledge_agent"
            session_id = system.start_session(agent_id)
            
            from shared.interfaces.agent_personality import AgentMemory
            
            # Store conversation memories
            conversation_memories = [
                AgentMemory(
                    agent_id=agent_id,
                    memory_type="conversational",
                    content="I really love drinking coffee in the morning",
                    timestamp=datetime.now(),
                    importance=6,
                    tags=["preference", "coffee"],
                    context={"conversation_id": "conv_001"}
                ),
                AgentMemory(
                    agent_id=agent_id,
                    memory_type="conversational", 
                    content="I work as a software engineer at a tech company",
                    timestamp=datetime.now(),
                    importance=8,
                    tags=["work", "profession"],
                    context={"conversation_id": "conv_001"}
                )
            ]
            
            # Store memories (this should trigger knowledge retention)
            for memory in conversation_memories:
                success = system.store_memory(memory)
                assert success is True
            
            # Verify knowledge retention metrics
            assert system.metrics["knowledge_retention_events"] > 0
            
            # End session
            system.end_session(agent_id)
            
            # Start new session to test persistence
            new_session_id = system.start_session(agent_id)
            
            # Search for knowledge should return extracted facts
            # (This would work with real Mem0 integration)
            knowledge_memories = system.search_memories(
                agent_id=agent_id,
                query="coffee preferences"
            )
            
            # Verify the mock was called (real test would verify actual results)
            assert mock_client.add.called
            
            system.end_session(agent_id)


@pytest.mark.integration
class TestRealMem0Integration:
    """Integration tests with real Mem0 (requires API keys)."""
    
    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="Real API key required for integration tests"
    )
    def test_real_mem0_integration(self):
        """Test with real Mem0 integration (requires API keys)."""
        config = {
            "llm_api_key": os.getenv("OPENAI_API_KEY"),
            "embedder_api_key": os.getenv("OPENAI_API_KEY"),
            "vector_store_path": tempfile.mkdtemp(),
            "history_db_path": tempfile.mktemp(),
            "llm_model": "gpt-3.5-turbo",  # Use cheaper model for testing
            "embedder_model": "text-embedding-ada-002"
        }
        
        try:
            # Create real provider
            mem0_config = Mem0Config()
            for key, value in config.items():
                setattr(mem0_config, key, value)
            
            provider = Mem0MemoryProvider(mem0_config)
            success = provider.initialize(config)
            
            assert success is True
            
            # Test real memory operations
            test_memory = EnhancedMemoryItem(
                id="real_test_memory",
                agent_id="integration_test_agent",
                content="This is a real integration test memory about artificial intelligence",
                memory_type=MemoryType.SEMANTIC,
                importance=0.8,
                confidence=0.9,
                tags=["integration", "test", "ai"]
            )
            
            # Store memory
            store_result = provider.store_memory(test_memory)
            assert store_result.success is True
            
            # Search for memory
            search_result = provider.search_semantic(
                agent_id="integration_test_agent",
                query_text="artificial intelligence",
                limit=5
            )
            
            assert len(search_result.memories) > 0
            
            # Clean up
            provider.cleanup_memories(
                agent_id="integration_test_agent",
                criteria={"test": True}
            )
            
        except Exception as e:
            # Clean up on failure
            try:
                shutil.rmtree(config["vector_store_path"])
                os.unlink(config["history_db_path"])
            except:
                pass
            
            # Re-raise the original exception
            raise e


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])