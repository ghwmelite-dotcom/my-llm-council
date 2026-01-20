"""Constitutional governance for council models."""

from .storage import (
    get_constitution,
    save_constitution,
    get_article,
    get_constitution_history
)
from .enforcement import (
    inject_constitution,
    check_compliance,
    format_constitution_for_prompt
)
from .amendments import (
    propose_amendment,
    vote_on_amendment,
    get_pending_amendments,
    process_amendment_vote
)
from .templates import get_default_constitution, ARTICLE_TEMPLATES

__all__ = [
    'get_constitution',
    'save_constitution',
    'get_article',
    'get_constitution_history',
    'inject_constitution',
    'check_compliance',
    'format_constitution_for_prompt',
    'propose_amendment',
    'vote_on_amendment',
    'get_pending_amendments',
    'process_amendment_vote',
    'get_default_constitution',
    'ARTICLE_TEMPLATES',
]
