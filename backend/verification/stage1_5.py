"""Stage 1.5: Verification orchestrator between Stage 1 and Stage 2."""

from typing import List, Dict, Any, Optional, Tuple
from .claim_extractor import extract_claims_batch, Claim
from .contradiction_detector import detect_contradictions
from .reporter import (
    VerificationReport, create_verification_report,
    format_verification_for_stage2, format_verification_summary
)
from ..config import VERIFICATION_CONFIG


async def run_verification_stage(
    stage1_results: List[Dict[str, Any]],
    user_query: str
) -> Tuple[Optional[VerificationReport], str]:
    """
    Run Stage 1.5: Factual verification between Stage 1 and Stage 2.

    This stage:
    1. Extracts factual claims from each Stage 1 response
    2. Compares claims across models for contradictions
    3. Generates a verification report
    4. Returns context to inject into Stage 2 ranking

    Args:
        stage1_results: List of Stage 1 responses with 'model' and 'response' keys
        user_query: The original user query (for context)

    Returns:
        Tuple of (VerificationReport, stage2_injection_text)
    """
    config = VERIFICATION_CONFIG

    # Check if verification is enabled
    if not config.get("enabled", True):
        return None, ""

    # Need at least 2 responses to verify
    if len(stage1_results) < 2:
        return None, ""

    # Extract claims from all responses
    claims_by_model = await extract_claims_batch(stage1_results)

    # Count total claims
    total_claims = sum(len(claims) for claims in claims_by_model.values())

    # Check if we have enough claims to verify
    min_claims = config.get("min_claims_for_verification", 3)
    if total_claims < min_claims:
        return None, ""

    # Detect contradictions
    contradictions = await detect_contradictions(claims_by_model)

    # Create report
    report = create_verification_report(claims_by_model, contradictions)

    # Format for Stage 2 injection
    stage2_text = format_verification_for_stage2(report)

    return report, stage2_text


def should_run_verification(
    stage1_results: List[Dict[str, Any]],
    routing_tier: Optional[int] = None
) -> bool:
    """
    Determine if verification should run based on context.

    Args:
        stage1_results: Stage 1 responses
        routing_tier: The routing tier used (1, 2, or 3)

    Returns:
        True if verification should run
    """
    config = VERIFICATION_CONFIG

    if not config.get("enabled", True):
        return False

    # Don't verify single-model responses
    if len(stage1_results) < 2:
        return False

    # Skip verification for simple queries (tier 1)
    if routing_tier == 1:
        return False

    return True
