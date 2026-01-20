"""Specialized councils module for routing queries to appropriate sub-councils."""

from .definitions import get_council, get_all_councils, COUNCIL_DEFINITIONS
from .router import route_query, detect_topic
from .appeals import create_appeal, process_appeal
from .executor import run_specialized_council

__all__ = [
    'get_council',
    'get_all_councils',
    'COUNCIL_DEFINITIONS',
    'route_query',
    'detect_topic',
    'create_appeal',
    'process_appeal',
    'run_specialized_council',
]
