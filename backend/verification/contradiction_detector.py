"""Detect contradictions between factual claims from different models."""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from .claim_extractor import Claim
from ..openrouter import query_model
from ..config import VERIFICATION_CONFIG
import json
import re


@dataclass
class Contradiction:
    """A detected contradiction between claims."""
    claim_a: Claim
    claim_b: Claim
    severity: str = "medium"    # low, medium, high, critical
    explanation: str = ""       # Why these claims contradict
    resolution_hint: str = ""   # Hint for which might be correct

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "claim_a": self.claim_a.to_dict(),
            "claim_b": self.claim_b.to_dict(),
            "severity": self.severity,
            "explanation": self.explanation,
            "resolution_hint": self.resolution_hint
        }


CONTRADICTION_PROMPT = """Analyze these two claims from different sources and determine if they contradict each other.

Claim 1 (from {model_a}):
"{claim_a}"

Claim 2 (from {model_b}):
"{claim_b}"

Determine:
1. Do these claims contradict each other? (direct contradiction, partial contradiction, or no contradiction)
2. If contradicting, how severe is it? (low, medium, high, critical)
3. Brief explanation of the contradiction
4. Any hint about which might be more accurate

Return JSON:
{{
  "contradicts": true|false,
  "severity": "none|low|medium|high|critical",
  "explanation": "brief explanation",
  "resolution_hint": "hint about which is likely correct, if any"
}}

Only return the JSON, nothing else.
"""


async def check_contradiction(
    claim_a: Claim,
    claim_b: Claim
) -> Optional[Contradiction]:
    """
    Check if two claims contradict each other.

    Args:
        claim_a: First claim
        claim_b: Second claim

    Returns:
        Contradiction object if they contradict, None otherwise
    """
    config = VERIFICATION_CONFIG
    detector_model = config.get("model", "anthropic/claude-sonnet-4.5")
    threshold = config.get("contradiction_threshold", 0.7)

    prompt = CONTRADICTION_PROMPT.format(
        model_a=claim_a.model.split('/')[-1],
        claim_a=claim_a.text,
        model_b=claim_b.model.split('/')[-1],
        claim_b=claim_b.text
    )

    messages = [{"role": "user", "content": prompt}]
    result = await query_model(detector_model, messages, timeout=30.0)

    if not result:
        return None

    content = result.get('content', '{}')

    try:
        # Extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            parsed = json.loads(json_match.group())

            if parsed.get("contradicts", False):
                return Contradiction(
                    claim_a=claim_a,
                    claim_b=claim_b,
                    severity=parsed.get("severity", "medium"),
                    explanation=parsed.get("explanation", ""),
                    resolution_hint=parsed.get("resolution_hint", "")
                )
    except json.JSONDecodeError:
        pass

    return None


def find_claim_pairs(
    claims_by_model: Dict[str, List[Claim]]
) -> List[Tuple[Claim, Claim]]:
    """
    Find all pairs of claims from different models to compare.

    Args:
        claims_by_model: Dict mapping model name to its claims

    Returns:
        List of (claim_a, claim_b) pairs to check
    """
    pairs = []
    models = list(claims_by_model.keys())

    for i, model_a in enumerate(models):
        for model_b in models[i + 1:]:
            for claim_a in claims_by_model[model_a]:
                for claim_b in claims_by_model[model_b]:
                    pairs.append((claim_a, claim_b))

    return pairs


async def detect_contradictions(
    claims_by_model: Dict[str, List[Claim]],
    max_comparisons: int = 50
) -> List[Contradiction]:
    """
    Detect contradictions between claims from different models.

    Args:
        claims_by_model: Dict mapping model name to its claims
        max_comparisons: Maximum number of claim pairs to compare

    Returns:
        List of detected Contradiction objects
    """
    import asyncio

    # Get all claim pairs
    pairs = find_claim_pairs(claims_by_model)

    # Limit comparisons to avoid too many API calls
    if len(pairs) > max_comparisons:
        # Prioritize by confidence
        pairs = sorted(
            pairs,
            key=lambda p: p[0].confidence + p[1].confidence,
            reverse=True
        )[:max_comparisons]

    # Check all pairs in parallel (with some batching for API limits)
    batch_size = 10
    contradictions = []

    for i in range(0, len(pairs), batch_size):
        batch = pairs[i:i + batch_size]
        tasks = [check_contradiction(a, b) for a, b in batch]
        results = await asyncio.gather(*tasks)

        for result in results:
            if result is not None:
                contradictions.append(result)

    return contradictions
