"""Generate verification reports for Stage 2 injection."""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from .claim_extractor import Claim
from .contradiction_detector import Contradiction


@dataclass
class VerificationReport:
    """Complete verification report with claims and contradictions."""
    total_claims: int
    claims_by_model: Dict[str, int]
    contradictions: List[Contradiction]
    severity_summary: Dict[str, int]
    models_involved: List[str]

    @property
    def has_contradictions(self) -> bool:
        """Check if any contradictions were found."""
        return len(self.contradictions) > 0

    @property
    def highest_severity(self) -> str:
        """Get the highest severity level found."""
        if self.severity_summary.get("critical", 0) > 0:
            return "critical"
        elif self.severity_summary.get("high", 0) > 0:
            return "high"
        elif self.severity_summary.get("medium", 0) > 0:
            return "medium"
        elif self.severity_summary.get("low", 0) > 0:
            return "low"
        return "none"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "total_claims": self.total_claims,
            "claims_by_model": self.claims_by_model,
            "contradictions": [c.to_dict() for c in self.contradictions],
            "contradiction_count": len(self.contradictions),
            "severity_summary": self.severity_summary,
            "highest_severity": self.highest_severity,
            "models_involved": self.models_involved,
            "has_contradictions": self.has_contradictions
        }


def create_verification_report(
    claims_by_model: Dict[str, List[Claim]],
    contradictions: List[Contradiction]
) -> VerificationReport:
    """
    Create a verification report from claims and contradictions.

    Args:
        claims_by_model: Dict mapping model name to its claims
        contradictions: List of detected contradictions

    Returns:
        VerificationReport object
    """
    # Count claims
    total_claims = sum(len(claims) for claims in claims_by_model.values())
    claims_count = {model: len(claims) for model, claims in claims_by_model.items()}

    # Count severity levels
    severity_summary = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    for c in contradictions:
        if c.severity in severity_summary:
            severity_summary[c.severity] += 1

    # Get unique models involved in contradictions
    models_involved = set()
    for c in contradictions:
        models_involved.add(c.claim_a.model)
        models_involved.add(c.claim_b.model)

    return VerificationReport(
        total_claims=total_claims,
        claims_by_model=claims_count,
        contradictions=contradictions,
        severity_summary=severity_summary,
        models_involved=list(models_involved)
    )


def format_verification_for_stage2(report: VerificationReport) -> str:
    """
    Format verification report for injection into Stage 2 ranking prompt.

    Args:
        report: The verification report

    Returns:
        Formatted string to add to Stage 2 prompt
    """
    if not report.has_contradictions:
        return ""

    lines = [
        "\n\n--- FACTUAL VERIFICATION NOTICE ---",
        f"Cross-verification identified {len(report.contradictions)} contradiction(s) "
        f"between model responses. Please consider these when ranking:\n"
    ]

    for i, contradiction in enumerate(report.contradictions, 1):
        model_a = contradiction.claim_a.model.split('/')[-1]
        model_b = contradiction.claim_b.model.split('/')[-1]

        lines.append(f"Contradiction #{i} [{contradiction.severity.upper()}]:")
        lines.append(f"  • {model_a} claims: \"{contradiction.claim_a.text}\"")
        lines.append(f"  • {model_b} claims: \"{contradiction.claim_b.text}\"")
        lines.append(f"  • Issue: {contradiction.explanation}")
        if contradiction.resolution_hint:
            lines.append(f"  • Note: {contradiction.resolution_hint}")
        lines.append("")

    lines.append(
        "Consider factual accuracy heavily when ranking responses. "
        "Models with verified contradictions should be ranked lower unless "
        "their claims are demonstrably correct."
    )
    lines.append("--- END VERIFICATION NOTICE ---\n")

    return "\n".join(lines)


def format_verification_summary(report: VerificationReport) -> str:
    """
    Create a brief summary of verification results.

    Args:
        report: The verification report

    Returns:
        Brief summary string
    """
    if not report.has_contradictions:
        return f"Verified {report.total_claims} claims across {len(report.claims_by_model)} models. No contradictions detected."

    return (
        f"Verified {report.total_claims} claims across {len(report.claims_by_model)} models. "
        f"Found {len(report.contradictions)} contradiction(s) "
        f"(highest severity: {report.highest_severity})."
    )
