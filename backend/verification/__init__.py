"""Factual verification layer for cross-checking claims."""

from .claim_extractor import Claim, extract_claims
from .contradiction_detector import Contradiction, detect_contradictions
from .reporter import VerificationReport, format_verification_for_stage2
from .stage1_5 import run_verification_stage, should_run_verification

__all__ = [
    'Claim',
    'extract_claims',
    'Contradiction',
    'detect_contradictions',
    'VerificationReport',
    'format_verification_for_stage2',
    'run_verification_stage',
    'should_run_verification',
]
