"""Report generation for observer analyses."""

from typing import Dict, List, Any, Optional
from datetime import datetime
from .analyzer import analyze_deliberation_quality, get_analysis_store, get_aggregate_statistics
from .bias_detector import detect_biases, get_bias_report, COGNITIVE_BIASES


def get_cognitive_health_score(
    responses: List[Dict[str, Any]],
    rankings: List[Dict[str, Any]],
    query: str = None
) -> Dict[str, Any]:
    """
    Get a simple cognitive health score for a deliberation.

    Args:
        responses: Stage 1 responses
        rankings: Stage 2 rankings
        query: Original query

    Returns:
        Health score and summary
    """
    analysis = analyze_deliberation_quality(responses, rankings, query=query)

    score = analysis['overall_quality']
    biases = analysis.get('bias_analysis', {}).get('biases_detected', [])

    # Determine health level
    if score >= 0.8 and len(biases) == 0:
        health_level = 'healthy'
        icon = '🟢'
        message = 'Council deliberation appears healthy with no significant issues.'
    elif score >= 0.6 or len(biases) <= 1:
        health_level = 'moderate'
        icon = '🟡'
        message = 'Council deliberation has some minor concerns that could be addressed.'
    else:
        health_level = 'concerning'
        icon = '🔴'
        message = 'Council deliberation shows significant issues that should be reviewed.'

    return {
        'score': score,
        'health_level': health_level,
        'icon': icon,
        'message': message,
        'bias_count': len(biases),
        'quality_rating': analysis['quality_rating']
    }


def format_observations_for_display(analysis: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Format analysis results as a list of observations for UI display.

    Args:
        analysis: Full analysis results

    Returns:
        List of observation dicts with type, icon, title, description
    """
    observations = []

    # Overall quality observation
    quality = analysis.get('overall_quality', 0)
    quality_rating = analysis.get('quality_rating', 'Unknown')
    observations.append({
        'type': 'quality',
        'icon': '📊',
        'title': f'Overall Quality: {quality_rating}',
        'description': f'The deliberation scored {quality:.0%} on overall quality metrics.',
        'severity': 'info'
    })

    # Diversity observation
    diversity = analysis.get('diversity', {})
    div_score = diversity.get('diversity_score', 0)
    if div_score < 0.5:
        observations.append({
            'type': 'diversity',
            'icon': '🎭',
            'title': 'Low Response Diversity',
            'description': (
                'Responses show high similarity. Consider adding models with '
                'different perspectives for more diverse viewpoints.'
            ),
            'severity': 'warning'
        })
    elif div_score > 0.7:
        observations.append({
            'type': 'diversity',
            'icon': '🎭',
            'title': 'Good Response Diversity',
            'description': (
                'Council members provided diverse perspectives on the topic.'
            ),
            'severity': 'positive'
        })

    # Ranking quality observation
    ranking = analysis.get('ranking_quality', {})
    reasoning_ratio = ranking.get('reasoning_ratio', 0)
    if reasoning_ratio < 0.5:
        observations.append({
            'type': 'ranking',
            'icon': '📋',
            'title': 'Limited Evaluation Reasoning',
            'description': (
                'Some evaluations lack detailed reasoning for their rankings. '
                'More explicit justification would improve transparency.'
            ),
            'severity': 'warning'
        })

    # Bias observations
    bias_analysis = analysis.get('bias_analysis', {})
    for bias in bias_analysis.get('biases_detected', []):
        severity_map = {'high': 'error', 'medium': 'warning', 'low': 'info'}
        icon_map = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}

        observations.append({
            'type': 'bias',
            'icon': icon_map.get(bias['severity'], '⚪'),
            'title': f"Potential {bias['name']}",
            'description': COGNITIVE_BIASES[bias['type']]['description'],
            'severity': severity_map.get(bias['severity'], 'info'),
            'indicators': bias.get('indicators', [])
        })

    # Synthesis completeness observation
    synthesis = analysis.get('synthesis_completeness')
    if synthesis:
        ratio = synthesis.get('incorporation_ratio', 0)
        if ratio < 0.6:
            observations.append({
                'type': 'synthesis',
                'icon': '🔗',
                'title': 'Incomplete Synthesis',
                'description': (
                    f'The final synthesis incorporated only {ratio:.0%} of perspectives. '
                    'Some viewpoints may not be fully represented.'
                ),
                'severity': 'warning'
            })
        elif ratio > 0.8:
            observations.append({
                'type': 'synthesis',
                'icon': '🔗',
                'title': 'Comprehensive Synthesis',
                'description': (
                    'The final answer successfully incorporates perspectives from '
                    'most council members.'
                ),
                'severity': 'positive'
            })

    # Recommendations
    for rec in analysis.get('recommendations', [])[:3]:  # Limit to 3
        if 'good' not in rec.lower():
            observations.append({
                'type': 'recommendation',
                'icon': '💡',
                'title': 'Recommendation',
                'description': rec,
                'severity': 'info'
            })

    return observations


def generate_observer_report(
    conversation_id: str,
    responses: List[Dict[str, Any]],
    rankings: List[Dict[str, Any]],
    synthesis: str = None,
    query: str = None,
    format: str = 'full'
) -> Dict[str, Any]:
    """
    Generate a complete observer report.

    Args:
        conversation_id: Conversation ID
        responses: Stage 1 responses
        rankings: Stage 2 rankings
        synthesis: Stage 3 synthesis
        query: Original query
        format: Report format ('full', 'summary', 'text')

    Returns:
        Observer report
    """
    # Run analysis
    analysis = analyze_deliberation_quality(responses, rankings, synthesis, query)

    # Get health score
    health = get_cognitive_health_score(responses, rankings, query)

    # Format observations
    observations = format_observations_for_display(analysis)

    report = {
        'conversation_id': conversation_id,
        'generated_at': datetime.utcnow().isoformat(),
        'health': health,
        'observations': observations,
        'analysis': analysis
    }

    if format == 'summary':
        return {
            'conversation_id': conversation_id,
            'health': health,
            'observation_count': len(observations),
            'top_observations': observations[:3]
        }

    if format == 'text':
        return {
            'text': generate_text_report(report)
        }

    return report


def generate_text_report(report: Dict[str, Any]) -> str:
    """
    Generate a human-readable text report.

    Args:
        report: Full report dict

    Returns:
        Formatted text report
    """
    lines = []
    lines.append("=" * 50)
    lines.append("COUNCIL OBSERVER REPORT")
    lines.append("=" * 50)
    lines.append("")

    # Health summary
    health = report.get('health', {})
    lines.append(f"COGNITIVE HEALTH: {health.get('icon', '')} {health.get('health_level', 'Unknown').upper()}")
    lines.append(f"Quality Score: {health.get('score', 0):.0%}")
    lines.append(f"Biases Detected: {health.get('bias_count', 0)}")
    lines.append("")
    lines.append(health.get('message', ''))
    lines.append("")

    # Observations
    lines.append("-" * 50)
    lines.append("OBSERVATIONS")
    lines.append("-" * 50)
    lines.append("")

    for obs in report.get('observations', []):
        severity_prefix = {
            'error': '[!]',
            'warning': '[~]',
            'positive': '[+]',
            'info': '[i]'
        }.get(obs.get('severity', 'info'), '[?]')

        lines.append(f"{obs.get('icon', '')} {severity_prefix} {obs.get('title', 'Observation')}")
        lines.append(f"   {obs.get('description', '')}")

        if obs.get('indicators'):
            for indicator in obs['indicators']:
                lines.append(f"   • {indicator}")
        lines.append("")

    # Analysis details
    analysis = report.get('analysis', {})

    lines.append("-" * 50)
    lines.append("DETAILED METRICS")
    lines.append("-" * 50)
    lines.append("")

    diversity = analysis.get('diversity', {})
    lines.append(f"Response Diversity: {diversity.get('diversity_score', 0):.0%}")
    lines.append(f"  - Response Count: {diversity.get('response_count', 0)}")
    lines.append(f"  - Average Overlap: {diversity.get('average_overlap', 0):.0%}")
    lines.append("")

    ranking = analysis.get('ranking_quality', {})
    lines.append(f"Ranking Quality: {ranking.get('quality_score', 0):.0%}")
    lines.append(f"  - Evaluator Count: {ranking.get('evaluator_count', 0)}")
    lines.append(f"  - Reasoning Ratio: {ranking.get('reasoning_ratio', 0):.0%}")
    lines.append(f"  - Ranking Consistency: {ranking.get('ranking_consistency', 0):.0%}")
    lines.append("")

    synthesis = analysis.get('synthesis_completeness')
    if synthesis:
        lines.append(f"Synthesis Completeness: {synthesis.get('completeness_score', 0):.0%}")
        lines.append(f"  - Perspectives Incorporated: {synthesis.get('incorporated_count', 0)}/{synthesis.get('total_responses', 0)}")
        lines.append("")

    lines.append("=" * 50)
    lines.append(f"Report generated: {report.get('generated_at', 'Unknown')}")
    lines.append("=" * 50)

    return "\n".join(lines)


def get_historical_trends(limit: int = 30) -> Dict[str, Any]:
    """
    Get historical trends in deliberation quality.

    Args:
        limit: Number of recent analyses to consider

    Returns:
        Trend data
    """
    store = get_analysis_store()
    analyses = store.get_analyses(limit)

    if not analyses:
        return {'count': 0, 'trends': {}}

    # Extract time series data
    quality_series = []
    diversity_series = []
    bias_series = []

    for a in analyses:
        timestamp = a.get('analyzed_at', a.get('conversation_id'))
        quality_series.append({
            'x': timestamp,
            'y': a.get('overall_quality', 0)
        })
        diversity_series.append({
            'x': timestamp,
            'y': a.get('diversity', {}).get('diversity_score', 0)
        })
        bias_series.append({
            'x': timestamp,
            'y': a.get('bias_analysis', {}).get('bias_count', 0)
        })

    # Calculate trends (simple moving average comparison)
    def calculate_trend(series):
        if len(series) < 5:
            return 'stable'
        recent = sum(s['y'] for s in series[-5:]) / 5
        older = sum(s['y'] for s in series[:5]) / 5
        diff = recent - older
        if diff > 0.1:
            return 'improving'
        elif diff < -0.1:
            return 'declining'
        return 'stable'

    return {
        'count': len(analyses),
        'quality': {
            'series': quality_series,
            'trend': calculate_trend(quality_series),
            'current': quality_series[-1]['y'] if quality_series else 0
        },
        'diversity': {
            'series': diversity_series,
            'trend': calculate_trend(diversity_series),
            'current': diversity_series[-1]['y'] if diversity_series else 0
        },
        'biases': {
            'series': bias_series,
            'trend': 'improving' if calculate_trend(bias_series) == 'declining' else (
                'declining' if calculate_trend(bias_series) == 'improving' else 'stable'
            ),
            'current': bias_series[-1]['y'] if bias_series else 0
        },
        'aggregate': get_aggregate_statistics()
    }
