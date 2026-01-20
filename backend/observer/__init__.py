"""Observer model for meta-cognitive analysis of council deliberations."""

from .analyzer import (
    run_meta_analysis,
    analyze_deliberation_quality,
    get_analysis_history
)
from .bias_detector import (
    detect_biases,
    get_bias_report,
    COGNITIVE_BIASES
)
from .reporter import (
    generate_observer_report,
    get_cognitive_health_score,
    format_observations_for_display
)

__all__ = [
    'run_meta_analysis',
    'analyze_deliberation_quality',
    'get_analysis_history',
    'detect_biases',
    'get_bias_report',
    'COGNITIVE_BIASES',
    'generate_observer_report',
    'get_cognitive_health_score',
    'format_observations_for_display',
]
