"""Semantic cache storage and management."""

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from ..config import SEMANTIC_CACHE_CONFIG


@dataclass
class CachedResponse:
    """A cached council response."""
    query: str
    stage1_results: List[Dict[str, Any]]
    stage2_results: List[Dict[str, Any]]
    stage3_result: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    hit_count: int = 0
    routing_tier: Optional[int] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON storage."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'CachedResponse':
        """Create from dictionary."""
        return cls(**data)

    def is_expired(self, ttl_hours: int) -> bool:
        """Check if cache entry has expired."""
        created = datetime.fromisoformat(self.created_at)
        expiry = created + timedelta(hours=ttl_hours)
        return datetime.utcnow() > expiry


class SemanticCache:
    """Semantic cache for council responses."""

    _instance: Optional['SemanticCache'] = None

    def __init__(self):
        self.cache: Dict[str, CachedResponse] = {}
        self.config = SEMANTIC_CACHE_CONFIG
        self._load_from_disk()

    @classmethod
    def get_instance(cls) -> 'SemanticCache':
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _get_storage_path(self) -> str:
        """Get the cache storage file path."""
        return self.config.get("storage_path", "data/cache/semantic_cache.json")

    def _load_from_disk(self) -> None:
        """Load cache from disk."""
        path = self._get_storage_path()
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.cache = {
                        k: CachedResponse.from_dict(v)
                        for k, v in data.items()
                    }
                # Clean expired entries on load
                self._clean_expired()
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Could not load cache: {e}")
                self.cache = {}

    def _save_to_disk(self) -> None:
        """Save cache to disk."""
        path = self._get_storage_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(
                {k: v.to_dict() for k, v in self.cache.items()},
                f,
                indent=2
            )

    def _clean_expired(self) -> None:
        """Remove expired cache entries."""
        ttl = self.config.get("ttl_hours", 24)
        expired_keys = [
            k for k, v in self.cache.items()
            if v.is_expired(ttl)
        ]
        for key in expired_keys:
            del self.cache[key]

    def _enforce_size_limit(self) -> None:
        """Remove oldest entries if cache exceeds max size."""
        max_size = self.config.get("max_cache_size", 1000)
        if len(self.cache) > max_size:
            # Sort by created_at and remove oldest
            sorted_entries = sorted(
                self.cache.items(),
                key=lambda x: x[1].created_at
            )
            excess = len(self.cache) - max_size
            for key, _ in sorted_entries[:excess]:
                del self.cache[key]

    def _generate_key(self, query: str) -> str:
        """Generate a cache key from a query."""
        # Normalize: lowercase and strip whitespace
        normalized = query.lower().strip()
        # Use hash for consistent key length
        return str(hash(normalized))

    def get(self, query: str) -> Optional[CachedResponse]:
        """
        Get a cached response for a query.

        Note: This is for exact match. For semantic matching, use find_similar.

        Args:
            query: The query to look up

        Returns:
            CachedResponse if found, None otherwise
        """
        key = self._generate_key(query)
        if key in self.cache:
            entry = self.cache[key]
            ttl = self.config.get("ttl_hours", 24)
            if not entry.is_expired(ttl):
                entry.hit_count += 1
                return entry
            else:
                del self.cache[key]
        return None

    def find_similar(self, query: str) -> Optional[CachedResponse]:
        """
        Find a semantically similar cached query.

        Args:
            query: The query to match

        Returns:
            CachedResponse if found with high similarity, None otherwise
        """
        from .similarity import calculate_query_similarity

        threshold = self.config.get("similarity_threshold", 0.85)
        ttl = self.config.get("ttl_hours", 24)

        best_match = None
        best_score = 0.0

        for key, entry in list(self.cache.items()):
            # Skip expired
            if entry.is_expired(ttl):
                del self.cache[key]
                continue

            similarity = calculate_query_similarity(query, entry.query)
            if similarity >= threshold and similarity > best_score:
                best_score = similarity
                best_match = entry

        if best_match:
            best_match.hit_count += 1
            return best_match

        return None

    def set(
        self,
        query: str,
        stage1_results: List[Dict[str, Any]],
        stage2_results: List[Dict[str, Any]],
        stage3_result: Dict[str, Any],
        metadata: Dict[str, Any],
        routing_tier: Optional[int] = None
    ) -> None:
        """
        Cache a council response.

        Args:
            query: The original query
            stage1_results: Stage 1 responses
            stage2_results: Stage 2 rankings
            stage3_result: Stage 3 synthesis
            metadata: Additional metadata
            routing_tier: Which tier was used
        """
        key = self._generate_key(query)
        self.cache[key] = CachedResponse(
            query=query,
            stage1_results=stage1_results,
            stage2_results=stage2_results,
            stage3_result=stage3_result,
            metadata=metadata,
            routing_tier=routing_tier
        )

        self._enforce_size_limit()
        self._save_to_disk()

    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache = {}
        self._save_to_disk()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        self._clean_expired()
        total_hits = sum(e.hit_count for e in self.cache.values())
        return {
            "total_entries": len(self.cache),
            "total_hits": total_hits,
            "max_size": self.config.get("max_cache_size", 1000),
            "ttl_hours": self.config.get("ttl_hours", 24),
            "similarity_threshold": self.config.get("similarity_threshold", 0.85),
        }


def get_cache() -> SemanticCache:
    """Get the semantic cache singleton."""
    return SemanticCache.get_instance()
