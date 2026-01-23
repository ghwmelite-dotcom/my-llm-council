"""Meta-analysis of council deliberations."""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from ..config import OBSERVER_CONFIG, data_path
from .bias_detector import detect_biases


class AnalysisStore:
    """Stores analysis results."""

    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or data_path("observer", "analyses.json")
        self.analyses: List[Dict[str, Any]] = []
        self._ensure_storage_dir()
        self._load_analyses()

    def _ensure_storage_dir(self):
        """Ensure storage directory exists."""
        Path(os.path.dirname(self.storage_path)).mkdir(parents=True, exist_ok=True)

    def _load_analyses(self):
        """Load analyses from storage."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.analyses = data.get('analyses', [])
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error loading analyses: {e}")

    def _save_analyses(self):
        """Save analyses to storage."""
        self._ensure_storage_dir()
        data = {
            'version': '1.0',
            'last_updated': datetime.utcnow().isoformat(),
            'analyses': self.analyses[-500:]  # Keep last 500
        }
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)

    def add_analysis(self, analysis: Dict[str, Any]):
        """Add an analysis result."""
        self.analyses.append(analysis)
        self._save_analyses()

    def get_analyses(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent analyses."""
        return self.analyses[-limit:]

    def get_analysis_for_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis for a specific conversation."""
        for analysis in reversed(self.analyses):
            if analysis.get('conversation_id') == conversation_id:
                return analysis
        return None


# Singleton instance
_analysis_store: Optional[AnalysisStore] = None


def get_analysis_store() -> AnalysisStore:
    """Get the singleton analysis store."""
    global _analysis_store
    if _analysis_store is None:
        _analysis_store = AnalysisStore()
    return _analysis_store


def analyze_response_diversity(responses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze diversity of responses.

    Args:
        responses: Stage 1 responses

    Returns:
        Diversity metrics
    """
    if not responses:
        return {'diversity_score': 0, 'unique_approaches': 0}

    # Extract content
    contents = [r.get('content', '') for r in responses]

    # Calculate word overlap between pairs
    word_sets = [set(c.lower().split()) for c in contents]
    overlaps = []

    for i in range(len(word_sets)):
        for j in range(i + 1, len(word_sets)):
            if word_sets[i] and word_sets[j]:
                intersection = len(word_sets[i] & word_sets[j])
                union = len(word_sets[i] | word_sets[j])
                overlap = intersection / union if union > 0 else 0
                overlaps.append(overlap)

    avg_overlap = sum(overlaps) / len(overlaps) if overlaps else 0
    diversity_score = 1 - avg_overlap

    # Count unique approaches (based on response length distribution)
    lengths = [len(c) for c in contents]
    avg_length = sum(lengths) / len(lengths) if lengths else 0
    length_variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths) if lengths else 0

    return {
        'diversity_score': diversity_score,
        'average_overlap': avg_overlap,
        'length_variance': length_variance,
        'response_count': len(responses)
    }


def analyze_ranking_quality(rankings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze quality of ranking evaluations.

    Args:
        rankings: Stage 2 rankings

    Returns:
        Ranking quality metrics
    """
    if not rankings:
        return {'quality_score': 0, 'consistency': 0}

    # Check if rankings have substantive evaluations
    evaluation_lengths = []
    has_reasoning = 0

    reasoning_indicators = [
        'because', 'since', 'therefore', 'however', 'although',
        'strength', 'weakness', 'better', 'worse', 'prefer'
    ]

    for ranking in rankings:
        content = ranking.get('content', '')
        evaluation_lengths.append(len(content))

        if any(ind in content.lower() for ind in reasoning_indicators):
            has_reasoning += 1

    avg_length = sum(evaluation_lengths) / len(evaluation_lengths) if evaluation_lengths else 0
    reasoning_ratio = has_reasoning / len(rankings) if rankings else 0

    # Check ranking consistency
    parsed_rankings = [r.get('parsed_ranking', []) for r in rankings if r.get('parsed_ranking')]

    consistency = 0
    if len(parsed_rankings) >= 2:
        # Check agreement on top choice
        first_choices = [r[0] if r else None for r in parsed_rankings]
        if first_choices:
            most_common = max(set(first_choices), key=first_choices.count)
            agreement = first_choices.count(most_common) / len(first_choices)
            consistency = agreement

    quality_score = (reasoning_ratio * 0.5) + (min(avg_length / 500, 1) * 0.3) + (consistency * 0.2)

    return {
        'quality_score': quality_score,
        'average_evaluation_length': avg_length,
        'reasoning_ratio': reasoning_ratio,
        'ranking_consistency': consistency,
        'evaluator_count': len(rankings)
    }


def analyze_synthesis_completeness(
    synthesis: str,
    responses: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Analyze how well the synthesis incorporates all responses.

    Args:
        synthesis: Stage 3 synthesis
        responses: Stage 1 responses

    Returns:
        Synthesis completeness metrics
    """
    if not synthesis or not responses:
        return {'completeness_score': 0, 'incorporated_count': 0}

    synthesis_lower = synthesis.lower()

    # Check for key concepts from each response
    incorporated = 0
    key_concepts = []

    for response in responses:
        content = response.get('content', '')
        # Extract key phrases (simple: longer words)
        words = content.split()
        key_words = [w.lower() for w in words if len(w) > 7][:10]

        # Check if any key words appear in synthesis
        if any(kw in synthesis_lower for kw in key_words):
            incorporated += 1
            key_concepts.extend([kw for kw in key_words if kw in synthesis_lower])

    incorporation_ratio = incorporated / len(responses) if responses else 0

    # Check for synthesis-specific indicators
    synthesis_indicators = [
        'overall', 'considering', 'combining', 'consensus', 'majority',
        'agree', 'disagree', 'different perspectives', 'synthesizing'
    ]
    synthesis_quality = sum(1 for ind in synthesis_indicators if ind in synthesis_lower) / len(synthesis_indicators)

    completeness_score = (incorporation_ratio * 0.6) + (synthesis_quality * 0.4)

    return {
        'completeness_score': completeness_score,
        'incorporated_count': incorporated,
        'total_responses': len(responses),
        'incorporation_ratio': incorporation_ratio,
        'synthesis_quality': synthesis_quality,
        'key_concepts_found': list(set(key_concepts))[:10]
    }


def analyze_deliberation_quality(
    responses: List[Dict[str, Any]],
    rankings: List[Dict[str, Any]],
    synthesis: str = None,
    query: str = None
) -> Dict[str, Any]:
    """
    Comprehensive analysis of deliberation quality.

    Args:
        responses: Stage 1 responses
        rankings: Stage 2 rankings
        synthesis: Stage 3 synthesis
        query: Original query

    Returns:
        Complete quality analysis
    """
    diversity = analyze_response_diversity(responses)
    ranking_quality = analyze_ranking_quality(rankings)
    synthesis_completeness = analyze_synthesis_completeness(synthesis, responses) if synthesis else None
    biases = detect_biases(responses, rankings, query)

    # Calculate overall quality score
    scores = [
        diversity['diversity_score'],
        ranking_quality['quality_score'],
        biases['overall_score']
    ]

    if synthesis_completeness:
        scores.append(synthesis_completeness['completeness_score'])

    overall_quality = sum(scores) / len(scores)

    return {
        'overall_quality': overall_quality,
        'quality_rating': get_quality_rating(overall_quality),
        'diversity': diversity,
        'ranking_quality': ranking_quality,
        'synthesis_completeness': synthesis_completeness,
        'bias_analysis': biases,
        'analyzed_at': datetime.utcnow().isoformat()
    }


def get_quality_rating(score: float) -> str:
    """Get a quality rating label from a score."""
    if score >= 0.9:
        return 'Excellent'
    elif score >= 0.75:
        return 'Good'
    elif score >= 0.6:
        return 'Satisfactory'
    elif score >= 0.4:
        return 'Needs Improvement'
    else:
        return 'Poor'


def run_meta_analysis(
    conversation_id: str,
    responses: List[Dict[str, Any]],
    rankings: List[Dict[str, Any]],
    synthesis: str = None,
    query: str = None
) -> Dict[str, Any]:
    """
    Run complete meta-analysis and store results.

    Args:
        conversation_id: Conversation ID
        responses: Stage 1 responses
        rankings: Stage 2 rankings
        synthesis: Stage 3 synthesis
        query: Original query

    Returns:
        Analysis results
    """
    store = get_analysis_store()

    # Run analysis
    analysis = analyze_deliberation_quality(responses, rankings, synthesis, query)
    analysis['conversation_id'] = conversation_id
    analysis['query'] = query

    # Generate recommendations
    recommendations = generate_recommendations(analysis)
    analysis['recommendations'] = recommendations

    # Store results
    store.add_analysis(analysis)

    return analysis


def generate_recommendations(analysis: Dict[str, Any]) -> List[str]:
    """
    Generate recommendations based on analysis.

    Args:
        analysis: Analysis results

    Returns:
        List of recommendations
    """
    recommendations = []

    # Diversity recommendations
    if analysis.get('diversity', {}).get('diversity_score', 1) < 0.5:
        recommendations.append(
            'Consider adding models with different training or perspectives '
            'to increase response diversity.'
        )

    # Ranking quality recommendations
    if analysis.get('ranking_quality', {}).get('reasoning_ratio', 1) < 0.5:
        recommendations.append(
            'Evaluations lack detailed reasoning. Consider prompting for '
            'more explicit justification of rankings.'
        )

    # Synthesis recommendations
    synthesis = analysis.get('synthesis_completeness')
    if synthesis and synthesis.get('incorporation_ratio', 1) < 0.6:
        recommendations.append(
            'Final synthesis does not fully incorporate all perspectives. '
            'Consider adjusting synthesis prompts to be more inclusive.'
        )

    # Bias recommendations
    biases = analysis.get('bias_analysis', {}).get('biases_detected', [])
    for bias in biases:
        if bias['severity'] == 'high':
            recommendations.append(
                f"High severity bias detected: {bias['name']}. "
                f"Review deliberation process to address this pattern."
            )

    if not recommendations:
        recommendations.append('Deliberation quality appears good. No major issues detected.')

    return recommendations


def get_analysis_history(limit: int = 50) -> List[Dict[str, Any]]:
    """Get analysis history."""
    return get_analysis_store().get_analyses(limit)


def get_aggregate_statistics() -> Dict[str, Any]:
    """
    Get aggregate statistics across all analyses.

    Returns:
        Aggregate stats
    """
    store = get_analysis_store()
    analyses = store.get_analyses(limit=100)

    if not analyses:
        return {'count': 0}

    quality_scores = [a.get('overall_quality', 0) for a in analyses]
    diversity_scores = [a.get('diversity', {}).get('diversity_score', 0) for a in analyses]
    bias_counts = [a.get('bias_analysis', {}).get('bias_count', 0) for a in analyses]

    return {
        'count': len(analyses),
        'average_quality': sum(quality_scores) / len(quality_scores),
        'average_diversity': sum(diversity_scores) / len(diversity_scores),
        'average_bias_count': sum(bias_counts) / len(bias_counts),
        'quality_trend': quality_scores[-10:] if len(quality_scores) >= 10 else quality_scores
    }
