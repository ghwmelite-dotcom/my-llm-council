"""Cognitive bias detection for council deliberations."""

from typing import Dict, List, Any, Optional, Tuple
import re


# Cognitive biases that can be detected in deliberations
COGNITIVE_BIASES = {
    'confirmation_bias': {
        'name': 'Confirmation Bias',
        'description': (
            'Tendency to favor information that confirms pre-existing beliefs '
            'while ignoring contradictory evidence.'
        ),
        'severity': 'high',
        'indicators': [
            'ignores counterarguments',
            'dismisses alternative views',
            'cherry-picks supporting evidence',
            'does not acknowledge limitations'
        ]
    },
    'groupthink': {
        'name': 'Groupthink',
        'description': (
            'Tendency for group members to conform to a consensus view, '
            'suppressing dissent and alternative ideas.'
        ),
        'severity': 'high',
        'indicators': [
            'unanimous agreement without debate',
            'no dissenting opinions recorded',
            'rapid convergence to single answer',
            'criticism of minority views'
        ]
    },
    'anchoring': {
        'name': 'Anchoring Bias',
        'description': (
            'Over-reliance on the first piece of information encountered '
            'when making decisions.'
        ),
        'severity': 'medium',
        'indicators': [
            'first response heavily influences others',
            'later responses reference earlier ones',
            'insufficient adjustment from initial position',
            'same framework used across all responses'
        ]
    },
    'authority_bias': {
        'name': 'Authority Bias',
        'description': (
            'Tendency to attribute greater accuracy to opinions of authority '
            'figures regardless of content.'
        ),
        'severity': 'medium',
        'indicators': [
            'deference to specific models',
            'ranking based on model reputation',
            'dismissing valid points from less prominent sources'
        ]
    },
    'availability_heuristic': {
        'name': 'Availability Heuristic',
        'description': (
            'Overweighting information that comes to mind easily, often '
            'recent or emotionally charged content.'
        ),
        'severity': 'medium',
        'indicators': [
            'focus on recent events',
            'emphasis on dramatic examples',
            'neglect of base rates',
            'anecdotal over statistical evidence'
        ]
    },
    'false_consensus': {
        'name': 'False Consensus Effect',
        'description': (
            'Overestimating how much others share our beliefs and behaviors.'
        ),
        'severity': 'low',
        'indicators': [
            'assuming widespread agreement',
            'phrases like "everyone knows"',
            'not acknowledging diversity of views'
        ]
    },
    'dunning_kruger': {
        'name': 'Dunning-Kruger Effect',
        'description': (
            'Overconfidence in one\'s own abilities or knowledge in areas '
            'of limited expertise.'
        ),
        'severity': 'medium',
        'indicators': [
            'high confidence with limited evidence',
            'dismissing complexity',
            'failure to acknowledge uncertainty',
            'overconfident predictions'
        ]
    },
    'framing_effect': {
        'name': 'Framing Effect',
        'description': (
            'Drawing different conclusions based on how information is presented '
            'rather than its content.'
        ),
        'severity': 'medium',
        'indicators': [
            'response changes based on question phrasing',
            'inconsistent treatment of equivalent scenarios',
            'sensitivity to positive vs negative framing'
        ]
    },
    'sunk_cost': {
        'name': 'Sunk Cost Fallacy',
        'description': (
            'Continuing a course of action due to previously invested resources '
            'rather than future value.'
        ),
        'severity': 'low',
        'indicators': [
            'reluctance to change position',
            'emphasis on prior arguments',
            'resistance to new information'
        ]
    },
    'blind_spot': {
        'name': 'Bias Blind Spot',
        'description': (
            'Recognizing biases in others while failing to see them in oneself.'
        ),
        'severity': 'medium',
        'indicators': [
            'criticizing others\' biases',
            'claiming objectivity',
            'no self-reflection on limitations'
        ]
    }
}


def detect_groupthink(
    responses: List[Dict[str, Any]],
    rankings: List[Dict[str, Any]]
) -> Tuple[bool, float, List[str]]:
    """
    Detect groupthink in council deliberation.

    Args:
        responses: Stage 1 responses
        rankings: Stage 2 rankings

    Returns:
        Tuple of (detected, confidence, indicators)
    """
    indicators = []
    confidence = 0.0

    if not responses or not rankings:
        return False, 0.0, []

    # Check for high agreement in rankings
    if rankings:
        # Extract parsed rankings
        parsed_rankings = [r.get('parsed_ranking', []) for r in rankings if r.get('parsed_ranking')]

        if len(parsed_rankings) >= 2:
            # Check if all rankings have the same first choice
            first_choices = [r[0] if r else None for r in parsed_rankings]
            if all(fc == first_choices[0] for fc in first_choices if fc):
                indicators.append('Unanimous first choice across all evaluators')
                confidence += 0.3

            # Check ranking similarity (top 3)
            top_3s = [set(r[:3]) if len(r) >= 3 else set(r) for r in parsed_rankings]
            if len(top_3s) >= 2:
                overlap = set.intersection(*top_3s) if top_3s else set()
                if len(overlap) >= 3:
                    indicators.append('High overlap in top-ranked responses')
                    confidence += 0.2

    # Check response content for similarity
    if responses:
        contents = [r.get('content', '') for r in responses]

        # Simple similarity check: common phrases
        common_phrases = find_common_phrases(contents)
        if len(common_phrases) > 5:
            indicators.append('Many common phrases across responses')
            confidence += 0.2

        # Check for lack of dissent
        dissent_indicators = ['however', 'alternatively', 'on the other hand', 'disagree', 'different view']
        dissent_count = sum(1 for c in contents if any(d in c.lower() for d in dissent_indicators))
        if dissent_count == 0:
            indicators.append('No dissenting language detected')
            confidence += 0.2

    detected = confidence >= 0.4
    return detected, min(confidence, 1.0), indicators


def detect_anchoring(
    responses: List[Dict[str, Any]],
    rankings: List[Dict[str, Any]]
) -> Tuple[bool, float, List[str]]:
    """
    Detect anchoring bias in council deliberation.

    Args:
        responses: Stage 1 responses
        rankings: Stage 2 rankings

    Returns:
        Tuple of (detected, confidence, indicators)
    """
    indicators = []
    confidence = 0.0

    if not responses or len(responses) < 2:
        return False, 0.0, []

    # Check if first response heavily influences rankings
    if rankings:
        first_response_model = responses[0].get('model', '') if responses else ''

        # Count how often first response is ranked highly
        first_ranked_high = 0
        for ranking in rankings:
            parsed = ranking.get('parsed_ranking', [])
            if parsed and len(parsed) >= 2:
                # Check if first response in top half
                response_labels = [f"Response {chr(65 + i)}" for i in range(len(responses))]
                if response_labels[0] in parsed[:len(parsed)//2 + 1]:
                    first_ranked_high += 1

        if rankings and first_ranked_high / len(rankings) > 0.8:
            indicators.append('First response consistently ranked highly')
            confidence += 0.3

    # Check if later responses reference earlier ones
    for i, response in enumerate(responses[1:], 1):
        content = response.get('content', '').lower()
        reference_phrases = ['as mentioned', 'building on', 'similar to', 'agreeing with', 'like the previous']
        if any(phrase in content for phrase in reference_phrases):
            indicators.append(f'Response {i+1} appears to reference earlier responses')
            confidence += 0.15

    detected = confidence >= 0.4
    return detected, min(confidence, 1.0), indicators


def detect_confirmation_bias(
    responses: List[Dict[str, Any]],
    query: str = None
) -> Tuple[bool, float, List[str]]:
    """
    Detect confirmation bias in council deliberation.

    Args:
        responses: Stage 1 responses
        query: Original user query

    Returns:
        Tuple of (detected, confidence, indicators)
    """
    indicators = []
    confidence = 0.0

    if not responses:
        return False, 0.0, []

    for response in responses:
        content = response.get('content', '').lower()

        # Check for dismissive language
        dismissive = ['clearly wrong', 'obviously incorrect', 'no merit', 'completely false']
        if any(phrase in content for phrase in dismissive):
            indicators.append('Dismissive language toward alternative views')
            confidence += 0.2

        # Check for selective evidence
        selective = ['cherry-pick', 'only evidence', 'sole reason', 'single explanation']
        if any(phrase in content for phrase in selective):
            indicators.append('Potentially selective use of evidence')
            confidence += 0.15

        # Check for lack of counterarguments
        counter_indicators = ['counter', 'objection', 'challenge', 'weakness', 'limitation']
        if not any(c in content for c in counter_indicators):
            indicators.append('No counterarguments considered')
            confidence += 0.1

    detected = confidence >= 0.3
    return detected, min(confidence, 1.0), indicators


def find_common_phrases(texts: List[str], min_words: int = 3) -> List[str]:
    """
    Find common phrases across multiple texts.

    Args:
        texts: List of text strings
        min_words: Minimum words in a phrase

    Returns:
        List of common phrases
    """
    if not texts or len(texts) < 2:
        return []

    # Extract n-grams from first text
    words = texts[0].lower().split()
    ngrams = []
    for n in range(min_words, min_words + 3):
        for i in range(len(words) - n + 1):
            ngram = ' '.join(words[i:i+n])
            ngrams.append(ngram)

    # Check which appear in all texts
    common = []
    for ngram in ngrams:
        if all(ngram in text.lower() for text in texts[1:]):
            common.append(ngram)

    return list(set(common))


def detect_biases(
    responses: List[Dict[str, Any]],
    rankings: List[Dict[str, Any]],
    query: str = None
) -> Dict[str, Any]:
    """
    Run all bias detection on council deliberation.

    Args:
        responses: Stage 1 responses
        rankings: Stage 2 rankings
        query: Original user query

    Returns:
        Comprehensive bias report
    """
    biases_detected = []
    overall_score = 1.0  # Start with perfect score

    # Run each detector
    groupthink, gt_conf, gt_ind = detect_groupthink(responses, rankings)
    if groupthink:
        biases_detected.append({
            'type': 'groupthink',
            'name': COGNITIVE_BIASES['groupthink']['name'],
            'confidence': gt_conf,
            'severity': COGNITIVE_BIASES['groupthink']['severity'],
            'indicators': gt_ind
        })
        overall_score -= gt_conf * 0.3

    anchoring, anch_conf, anch_ind = detect_anchoring(responses, rankings)
    if anchoring:
        biases_detected.append({
            'type': 'anchoring',
            'name': COGNITIVE_BIASES['anchoring']['name'],
            'confidence': anch_conf,
            'severity': COGNITIVE_BIASES['anchoring']['severity'],
            'indicators': anch_ind
        })
        overall_score -= anch_conf * 0.2

    confirmation, conf_conf, conf_ind = detect_confirmation_bias(responses, query)
    if confirmation:
        biases_detected.append({
            'type': 'confirmation_bias',
            'name': COGNITIVE_BIASES['confirmation_bias']['name'],
            'confidence': conf_conf,
            'severity': COGNITIVE_BIASES['confirmation_bias']['severity'],
            'indicators': conf_ind
        })
        overall_score -= conf_conf * 0.3

    return {
        'biases_detected': biases_detected,
        'bias_count': len(biases_detected),
        'overall_score': max(0, overall_score),
        'health_rating': get_health_rating(overall_score)
    }


def get_health_rating(score: float) -> str:
    """Get a health rating label from a score."""
    if score >= 0.9:
        return 'Excellent'
    elif score >= 0.7:
        return 'Good'
    elif score >= 0.5:
        return 'Fair'
    elif score >= 0.3:
        return 'Poor'
    else:
        return 'Critical'


def get_bias_report(
    responses: List[Dict[str, Any]],
    rankings: List[Dict[str, Any]],
    query: str = None
) -> str:
    """
    Generate a human-readable bias report.

    Args:
        responses: Stage 1 responses
        rankings: Stage 2 rankings
        query: Original query

    Returns:
        Formatted report string
    """
    results = detect_biases(responses, rankings, query)

    lines = []
    lines.append("=== COGNITIVE BIAS ANALYSIS ===")
    lines.append("")
    lines.append(f"Overall Health Score: {results['overall_score']:.0%} ({results['health_rating']})")
    lines.append(f"Biases Detected: {results['bias_count']}")
    lines.append("")

    if results['biases_detected']:
        lines.append("DETECTED BIASES:")
        lines.append("")

        for bias in results['biases_detected']:
            severity_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(bias['severity'], '⚪')
            lines.append(f"{severity_emoji} {bias['name']} (Confidence: {bias['confidence']:.0%})")
            lines.append(f"   {COGNITIVE_BIASES[bias['type']]['description']}")
            lines.append("   Indicators:")
            for indicator in bias['indicators']:
                lines.append(f"   • {indicator}")
            lines.append("")
    else:
        lines.append("✅ No significant cognitive biases detected.")
        lines.append("")

    lines.append("=== END ANALYSIS ===")

    return "\n".join(lines)
