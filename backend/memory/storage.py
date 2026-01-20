"""JSON-based memory storage for the council."""

import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from ..config import MEMORY_CONFIG


@dataclass
class Memory:
    """Represents a single memory."""
    id: str
    type: str  # 'fact', 'preference', 'decision', 'insight', 'relationship'
    content: str
    created_at: str
    related_models: List[str]
    tags: List[str]
    source_conversation: Optional[str] = None
    importance: float = 0.5  # 0-1 scale
    access_count: int = 0
    last_accessed: Optional[str] = None


class MemoryStore:
    """Manages persistent memory storage."""

    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or MEMORY_CONFIG.get(
            'storage_path', 'data/memory/memories.json'
        )
        self.memories: List[Memory] = []
        self._ensure_storage_dir()
        self._load_memories()

    def _ensure_storage_dir(self):
        """Ensure the storage directory exists."""
        Path(os.path.dirname(self.storage_path)).mkdir(parents=True, exist_ok=True)

    def _load_memories(self):
        """Load memories from JSON file."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.memories = [
                        Memory(**m) for m in data.get('memories', [])
                    ]
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error loading memories: {e}")
                self.memories = []
        else:
            self.memories = []

    def _save_memories(self):
        """Save memories to JSON file."""
        self._ensure_storage_dir()
        data = {
            'version': '1.0',
            'last_updated': datetime.utcnow().isoformat(),
            'memory_count': len(self.memories),
            'memories': [asdict(m) for m in self.memories]
        }
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)

    def add_memory(
        self,
        content: str,
        memory_type: str = 'insight',
        related_models: List[str] = None,
        tags: List[str] = None,
        source_conversation: str = None,
        importance: float = 0.5
    ) -> Memory:
        """
        Add a new memory to the store.

        Args:
            content: The memory content
            memory_type: Type of memory (fact, preference, decision, insight, relationship)
            related_models: List of model IDs related to this memory
            tags: List of tags for categorization
            source_conversation: ID of the conversation that generated this memory
            importance: Importance score (0-1)

        Returns:
            The created Memory object
        """
        memory = Memory(
            id=str(uuid.uuid4()),
            type=memory_type,
            content=content,
            created_at=datetime.utcnow().isoformat(),
            related_models=related_models or [],
            tags=tags or [],
            source_conversation=source_conversation,
            importance=importance,
            access_count=0,
            last_accessed=None
        )
        self.memories.append(memory)
        self._save_memories()
        return memory

    def get_memory(self, memory_id: str) -> Optional[Memory]:
        """Get a memory by ID."""
        for memory in self.memories:
            if memory.id == memory_id:
                return memory
        return None

    def update_memory(self, memory_id: str, **updates) -> Optional[Memory]:
        """Update a memory's attributes."""
        for i, memory in enumerate(self.memories):
            if memory.id == memory_id:
                memory_dict = asdict(memory)
                memory_dict.update(updates)
                self.memories[i] = Memory(**memory_dict)
                self._save_memories()
                return self.memories[i]
        return None

    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory by ID."""
        for i, memory in enumerate(self.memories):
            if memory.id == memory_id:
                del self.memories[i]
                self._save_memories()
                return True
        return False

    def get_all_memories(self) -> List[Memory]:
        """Get all memories."""
        return self.memories.copy()

    def get_memories_by_type(self, memory_type: str) -> List[Memory]:
        """Get memories of a specific type."""
        return [m for m in self.memories if m.type == memory_type]

    def get_memories_by_tag(self, tag: str) -> List[Memory]:
        """Get memories with a specific tag."""
        return [m for m in self.memories if tag in m.tags]

    def get_memories_by_model(self, model_id: str) -> List[Memory]:
        """Get memories related to a specific model."""
        return [m for m in self.memories if model_id in m.related_models]

    def record_access(self, memory_id: str):
        """Record that a memory was accessed."""
        for i, memory in enumerate(self.memories):
            if memory.id == memory_id:
                memory.access_count += 1
                memory.last_accessed = datetime.utcnow().isoformat()
                self._save_memories()
                return

    def get_recent_memories(self, limit: int = 10) -> List[Memory]:
        """Get the most recent memories."""
        sorted_memories = sorted(
            self.memories,
            key=lambda m: m.created_at,
            reverse=True
        )
        return sorted_memories[:limit]

    def get_important_memories(self, min_importance: float = 0.7) -> List[Memory]:
        """Get memories above a certain importance threshold."""
        return [m for m in self.memories if m.importance >= min_importance]

    def search_by_keywords(self, keywords: List[str]) -> List[Memory]:
        """Search memories by keywords in content."""
        results = []
        keywords_lower = [k.lower() for k in keywords]
        for memory in self.memories:
            content_lower = memory.content.lower()
            if any(kw in content_lower for kw in keywords_lower):
                results.append(memory)
        return results

    def clear_all(self):
        """Clear all memories (use with caution)."""
        self.memories = []
        self._save_memories()


# Singleton instance
_memory_store: Optional[MemoryStore] = None


def get_memory_store() -> MemoryStore:
    """Get the singleton memory store instance."""
    global _memory_store
    if _memory_store is None:
        _memory_store = MemoryStore()
    return _memory_store
