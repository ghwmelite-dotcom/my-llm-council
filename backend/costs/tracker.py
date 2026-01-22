"""Cost tracker for monitoring API usage during queries."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime

from .pricing import calculate_cost, format_cost


@dataclass
class UsageData:
    """Token usage data from a single API call."""
    model: str
    input_tokens: int
    output_tokens: int
    cost: float = 0.0
    stage: str = ""  # stage1, stage2, stage3, etc.

    def __post_init__(self):
        if self.cost == 0.0:
            self.cost = calculate_cost(
                self.model,
                self.input_tokens,
                self.output_tokens
            )

    def to_dict(self) -> dict:
        return {
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost": self.cost,
            "cost_formatted": format_cost(self.cost),
            "stage": self.stage,
        }


@dataclass
class QueryCost:
    """Aggregated cost data for a full query."""
    query_id: str
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    usage_records: List[UsageData] = field(default_factory=list)

    @property
    def total_cost(self) -> float:
        return sum(u.cost for u in self.usage_records)

    @property
    def total_input_tokens(self) -> int:
        return sum(u.input_tokens for u in self.usage_records)

    @property
    def total_output_tokens(self) -> int:
        return sum(u.output_tokens for u in self.usage_records)

    @property
    def total_tokens(self) -> int:
        return self.total_input_tokens + self.total_output_tokens

    def cost_by_stage(self) -> Dict[str, float]:
        """Get cost breakdown by stage."""
        breakdown = {}
        for usage in self.usage_records:
            stage = usage.stage or "unknown"
            breakdown[stage] = breakdown.get(stage, 0.0) + usage.cost
        return breakdown

    def cost_by_model(self) -> Dict[str, float]:
        """Get cost breakdown by model."""
        breakdown = {}
        for usage in self.usage_records:
            breakdown[usage.model] = breakdown.get(usage.model, 0.0) + usage.cost
        return breakdown

    def to_dict(self) -> dict:
        return {
            "query_id": self.query_id,
            "total_cost": self.total_cost,
            "total_cost_formatted": format_cost(self.total_cost),
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_tokens,
            "cost_by_stage": {
                k: {"cost": v, "formatted": format_cost(v)}
                for k, v in self.cost_by_stage().items()
            },
            "cost_by_model": {
                k: {"cost": v, "formatted": format_cost(v)}
                for k, v in self.cost_by_model().items()
            },
            "api_calls": len(self.usage_records),
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class CostTracker:
    """
    Tracks costs for a single query across all stages.

    Usage:
        tracker = CostTracker("query-123")
        tracker.add_usage("openai/gpt-4o", 100, 50, "stage1")
        tracker.add_usage("anthropic/claude-3.5-sonnet", 100, 75, "stage1")
        cost_data = tracker.get_summary()
    """

    def __init__(self, query_id: str):
        self.query_cost = QueryCost(query_id=query_id)

    def add_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        stage: str = ""
    ) -> UsageData:
        """
        Add usage data from an API call.

        Args:
            model: Model identifier
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            stage: Stage identifier (stage1, stage2, stage3, etc.)

        Returns:
            The UsageData record created
        """
        usage = UsageData(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            stage=stage
        )
        self.query_cost.usage_records.append(usage)
        return usage

    def complete(self):
        """Mark the query as complete."""
        self.query_cost.completed_at = datetime.utcnow()

    def get_summary(self) -> dict:
        """Get the cost summary as a dict."""
        return self.query_cost.to_dict()

    def get_current_total(self) -> float:
        """Get the current total cost."""
        return self.query_cost.total_cost
