"""Smart query router for cost-efficient council delegation."""

from dataclasses import dataclass, field
from typing import List, Optional, Any
from .complexity import ComplexityAnalysis, analyze_query_complexity
from ..config import SMART_ROUTING_CONFIG, COUNCIL_MODELS


@dataclass
class RoutingDecision:
    """Decision on how to route a query."""
    tier: int  # 1 = single, 2 = mini council, 3 = full council
    models: List[str]
    complexity: ComplexityAnalysis
    reason: str

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "tier": self.tier,
            "tier_name": {1: "single", 2: "mini_council", 3: "full_council"}[self.tier],
            "models": self.models,
            "model_count": len(self.models),
            "complexity_score": self.complexity.score,
            "complexity_factors": self.complexity.factors,
            "reason": self.reason,
        }


def route_query_smart(
    query: str,
    force_tier: Optional[int] = None
) -> RoutingDecision:
    """
    Route a query to the appropriate council tier based on complexity.

    Tiers:
    - Tier 1 (Single): Simple factual queries -> 1 model
    - Tier 2 (Mini): Moderate complexity -> 3 models
    - Tier 3 (Full): Complex/subjective -> all council models

    Args:
        query: The user's query
        force_tier: Optional tier override (1, 2, or 3)

    Returns:
        RoutingDecision with selected models and reasoning
    """
    config = SMART_ROUTING_CONFIG

    # Check if routing is enabled
    if not config.get("enabled", True):
        return RoutingDecision(
            tier=3,
            models=COUNCIL_MODELS.copy(),
            complexity=ComplexityAnalysis(score=1.0, reasoning="Smart routing disabled"),
            reason="Smart routing disabled - using full council"
        )

    # Analyze complexity
    complexity = analyze_query_complexity(query)

    # Allow override
    if force_tier is not None:
        tier = force_tier
        reason = f"Forced to tier {tier} by request"
    else:
        # Determine tier from complexity thresholds
        threshold_single = config.get("complexity_threshold_single", 0.3)
        threshold_full = config.get("complexity_threshold_full", 0.7)

        if complexity.score < threshold_single:
            tier = 1
            reason = f"Low complexity ({complexity.score:.2f}) -> single model"
        elif complexity.score < threshold_full:
            tier = 2
            reason = f"Medium complexity ({complexity.score:.2f}) -> mini council"
        else:
            tier = 3
            reason = f"High complexity ({complexity.score:.2f}) -> full council"

    # Select models based on tier
    if tier == 1:
        # Single model - use configured fast model
        single_model = config.get("single_model", "anthropic/claude-sonnet-4.5")
        models = [single_model]
    elif tier == 2:
        # Mini council - select subset of models
        mini_size = config.get("mini_council_size", 3)
        # Prioritize diversity: different providers if possible
        models = select_diverse_models(COUNCIL_MODELS, mini_size)
    else:
        # Full council
        models = COUNCIL_MODELS.copy()

    return RoutingDecision(
        tier=tier,
        models=models,
        complexity=complexity,
        reason=reason
    )


def select_diverse_models(all_models: List[str], count: int) -> List[str]:
    """
    Select a diverse subset of models from different providers.

    Args:
        all_models: Full list of available models
        count: Number of models to select

    Returns:
        List of selected model identifiers
    """
    if count >= len(all_models):
        return all_models.copy()

    # Group models by provider
    providers = {}
    for model in all_models:
        provider = model.split('/')[0] if '/' in model else 'unknown'
        if provider not in providers:
            providers[provider] = []
        providers[provider].append(model)

    selected = []
    provider_list = list(providers.keys())
    provider_index = 0

    # Round-robin selection from different providers
    while len(selected) < count:
        provider = provider_list[provider_index % len(provider_list)]
        if providers[provider]:
            selected.append(providers[provider].pop(0))
        provider_index += 1

        # Safety check to prevent infinite loop
        if provider_index > count * len(provider_list):
            break

    return selected
