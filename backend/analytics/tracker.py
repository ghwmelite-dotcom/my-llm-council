"""Analytics tracker for model performance."""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from threading import Lock

from .models import ModelMetrics, QueryMetrics, AnalyticsSummary


class AnalyticsTracker:
    """
    Singleton tracker for model analytics.
    Persists data to JSON file.
    """
    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.storage_path = os.path.join(
            os.path.dirname(__file__),
            '..', '..', 'data', 'analytics.json'
        )
        self.model_metrics: Dict[str, ModelMetrics] = {}
        self.query_history: List[QueryMetrics] = []
        self.cache_hits = 0
        self.total_queries = 0

        self._load()
        self._initialized = True

    def _load(self):
        """Load analytics from disk."""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)

                # Load model metrics
                for model, metrics in data.get('model_metrics', {}).items():
                    self.model_metrics[model] = ModelMetrics(
                        model=model,
                        total_queries=metrics.get('total_queries', 0),
                        total_tokens_in=metrics.get('total_tokens_in', 0),
                        total_tokens_out=metrics.get('total_tokens_out', 0),
                        total_cost=metrics.get('total_cost', 0.0),
                        avg_rank=metrics.get('avg_rank', 0.0),
                        rank_count=metrics.get('rank_count', 0),
                        first_place_count=metrics.get('first_place_count', 0),
                        response_times=metrics.get('response_times', [])[-100:],  # Keep last 100
                        last_used=datetime.fromisoformat(metrics['last_used']) if metrics.get('last_used') else None
                    )

                # Load query history (keep last 100)
                for q in data.get('query_history', [])[-100:]:
                    self.query_history.append(QueryMetrics(
                        query_id=q['query_id'],
                        timestamp=datetime.fromisoformat(q['timestamp']),
                        tier=q['tier'],
                        models_used=q['models_used'],
                        total_cost=q['total_cost'],
                        total_tokens=q['total_tokens'],
                        duration_ms=q['duration_ms'],
                        cache_hit=q.get('cache_hit', False)
                    ))

                self.cache_hits = data.get('cache_hits', 0)
                self.total_queries = data.get('total_queries', 0)
        except Exception as e:
            print(f"Failed to load analytics: {e}")

    def _save(self):
        """Save analytics to disk."""
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)

            data = {
                'model_metrics': {
                    model: {
                        'total_queries': m.total_queries,
                        'total_tokens_in': m.total_tokens_in,
                        'total_tokens_out': m.total_tokens_out,
                        'total_cost': m.total_cost,
                        'avg_rank': m.avg_rank,
                        'rank_count': m.rank_count,
                        'first_place_count': m.first_place_count,
                        'response_times': m.response_times[-100:],
                        'last_used': m.last_used.isoformat() if m.last_used else None
                    }
                    for model, m in self.model_metrics.items()
                },
                'query_history': [q.to_dict() for q in self.query_history[-100:]],
                'cache_hits': self.cache_hits,
                'total_queries': self.total_queries,
            }

            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Failed to save analytics: {e}")

    def record_model_usage(
        self,
        model: str,
        tokens_in: int,
        tokens_out: int,
        cost: float,
        response_time_ms: float = 0
    ):
        """Record usage for a model."""
        if model not in self.model_metrics:
            self.model_metrics[model] = ModelMetrics(model=model)

        m = self.model_metrics[model]
        m.total_queries += 1
        m.total_tokens_in += tokens_in
        m.total_tokens_out += tokens_out
        m.total_cost += cost
        if response_time_ms > 0:
            m.response_times.append(response_time_ms)
            m.response_times = m.response_times[-100:]  # Keep last 100
        m.last_used = datetime.utcnow()

    def record_ranking(self, model: str, rank: int, total_models: int):
        """Record a ranking result for a model."""
        if model not in self.model_metrics:
            self.model_metrics[model] = ModelMetrics(model=model)

        m = self.model_metrics[model]
        m.rank_count += 1
        if rank == 1:
            m.first_place_count += 1

        # Update rolling average rank
        m.avg_rank = ((m.avg_rank * (m.rank_count - 1)) + rank) / m.rank_count

    def record_query(
        self,
        query_id: str,
        tier: int,
        models_used: List[str],
        total_cost: float,
        total_tokens: int,
        duration_ms: float,
        cache_hit: bool = False
    ):
        """Record a complete query execution."""
        self.total_queries += 1
        if cache_hit:
            self.cache_hits += 1

        query = QueryMetrics(
            query_id=query_id,
            timestamp=datetime.utcnow(),
            tier=tier,
            models_used=models_used,
            total_cost=total_cost,
            total_tokens=total_tokens,
            duration_ms=duration_ms,
            cache_hit=cache_hit
        )
        self.query_history.append(query)
        self.query_history = self.query_history[-100:]  # Keep last 100

        self._save()

    def get_summary(self) -> AnalyticsSummary:
        """Get analytics summary."""
        total_cost = sum(m.total_cost for m in self.model_metrics.values())
        total_tokens = sum(m.total_tokens_in + m.total_tokens_out for m in self.model_metrics.values())

        # Calculate tier distribution
        tier_dist = {}
        for q in self.query_history:
            tier_dist[q.tier] = tier_dist.get(q.tier, 0) + 1

        return AnalyticsSummary(
            total_queries=self.total_queries,
            total_cost=total_cost,
            total_tokens=total_tokens,
            avg_query_cost=total_cost / max(self.total_queries, 1),
            cache_hit_rate=self.cache_hits / max(self.total_queries, 1),
            tier_distribution=tier_dist,
            model_metrics=self.model_metrics,
            recent_queries=self.query_history
        )

    def get_model_leaderboard(self) -> List[dict]:
        """Get models ranked by performance."""
        models = sorted(
            self.model_metrics.values(),
            key=lambda m: (m.win_rate, -m.avg_rank if m.rank_count > 0 else 999),
            reverse=True
        )
        return [m.to_dict() for m in models]


# Global analytics instance
_analytics: Optional[AnalyticsTracker] = None


def get_analytics() -> AnalyticsTracker:
    """Get the global analytics tracker."""
    global _analytics
    if _analytics is None:
        _analytics = AnalyticsTracker()
    return _analytics
