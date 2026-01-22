"""Data models for analytics."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime


@dataclass
class ModelMetrics:
    """Metrics for a single model."""
    model: str
    total_queries: int = 0
    total_tokens_in: int = 0
    total_tokens_out: int = 0
    total_cost: float = 0.0
    avg_rank: float = 0.0
    rank_count: int = 0
    first_place_count: int = 0
    response_times: List[float] = field(default_factory=list)
    last_used: Optional[datetime] = None

    @property
    def avg_response_time(self) -> float:
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)

    @property
    def win_rate(self) -> float:
        if self.rank_count == 0:
            return 0.0
        return self.first_place_count / self.rank_count

    @property
    def avg_cost_per_query(self) -> float:
        if self.total_queries == 0:
            return 0.0
        return self.total_cost / self.total_queries

    def to_dict(self) -> dict:
        return {
            "model": self.model,
            "model_name": self.model.split('/')[-1] if '/' in self.model else self.model,
            "total_queries": self.total_queries,
            "total_tokens_in": self.total_tokens_in,
            "total_tokens_out": self.total_tokens_out,
            "total_cost": round(self.total_cost, 4),
            "avg_rank": round(self.avg_rank, 2) if self.rank_count > 0 else None,
            "rank_count": self.rank_count,
            "first_place_count": self.first_place_count,
            "win_rate": round(self.win_rate * 100, 1),
            "avg_response_time_ms": round(self.avg_response_time, 0),
            "avg_cost_per_query": round(self.avg_cost_per_query, 4),
            "last_used": self.last_used.isoformat() if self.last_used else None,
        }


@dataclass
class QueryMetrics:
    """Metrics for a single query execution."""
    query_id: str
    timestamp: datetime
    tier: int
    models_used: List[str]
    total_cost: float
    total_tokens: int
    duration_ms: float
    cache_hit: bool = False

    def to_dict(self) -> dict:
        return {
            "query_id": self.query_id,
            "timestamp": self.timestamp.isoformat(),
            "tier": self.tier,
            "models_used": self.models_used,
            "total_cost": round(self.total_cost, 4),
            "total_tokens": self.total_tokens,
            "duration_ms": round(self.duration_ms, 0),
            "cache_hit": self.cache_hit,
        }


@dataclass
class AnalyticsSummary:
    """Summary of all analytics."""
    total_queries: int = 0
    total_cost: float = 0.0
    total_tokens: int = 0
    avg_query_cost: float = 0.0
    cache_hit_rate: float = 0.0
    tier_distribution: Dict[int, int] = field(default_factory=dict)
    model_metrics: Dict[str, ModelMetrics] = field(default_factory=dict)
    recent_queries: List[QueryMetrics] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "total_queries": self.total_queries,
            "total_cost": round(self.total_cost, 2),
            "total_tokens": self.total_tokens,
            "avg_query_cost": round(self.avg_query_cost, 4),
            "cache_hit_rate": round(self.cache_hit_rate * 100, 1),
            "tier_distribution": self.tier_distribution,
            "model_metrics": {k: v.to_dict() for k, v in self.model_metrics.items()},
            "recent_queries": [q.to_dict() for q in self.recent_queries[-20:]],
        }
