"""Council definitions and configurations."""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from ..config import SPECIALIZED_COUNCILS


@dataclass
class Council:
    """Represents a specialized council configuration."""
    id: str
    name: str
    description: str
    models: List[str]
    chairman: str
    keywords: List[str]
    priority: int = 0  # Higher priority councils are checked first


# Parse council definitions from config
COUNCIL_DEFINITIONS: Dict[str, Council] = {}

for council_id, config in SPECIALIZED_COUNCILS.items():
    COUNCIL_DEFINITIONS[council_id] = Council(
        id=council_id,
        name=config['name'],
        description=config['description'],
        models=config['models'],
        chairman=config['chairman'],
        keywords=config.get('keywords', []),
        priority=config.get('priority', 0)
    )


def get_council(council_id: str) -> Optional[Council]:
    """
    Get a council by ID.

    Args:
        council_id: The council identifier

    Returns:
        Council object or None if not found
    """
    return COUNCIL_DEFINITIONS.get(council_id)


def get_all_councils() -> List[Council]:
    """
    Get all available councils.

    Returns:
        List of Council objects
    """
    return list(COUNCIL_DEFINITIONS.values())


def get_councils_by_keyword(keyword: str) -> List[Council]:
    """
    Find councils that match a keyword.

    Args:
        keyword: The keyword to search for

    Returns:
        List of matching Council objects
    """
    keyword_lower = keyword.lower()
    matching = []

    for council in COUNCIL_DEFINITIONS.values():
        if any(kw.lower() in keyword_lower or keyword_lower in kw.lower()
               for kw in council.keywords):
            matching.append(council)

    return matching


def get_default_council() -> Council:
    """
    Get the default general council.

    Returns:
        The general Council object
    """
    return COUNCIL_DEFINITIONS.get('general', list(COUNCIL_DEFINITIONS.values())[0])


def get_supreme_council() -> Council:
    """
    Get the supreme council for appeals.

    Returns:
        The supreme Council object
    """
    return COUNCIL_DEFINITIONS.get('supreme', get_default_council())


def create_custom_council(
    name: str,
    models: List[str],
    chairman: str,
    keywords: List[str] = None,
    description: str = None
) -> Council:
    """
    Create a custom council configuration.

    Args:
        name: Display name for the council
        models: List of model IDs
        chairman: Chairman model ID
        keywords: Optional routing keywords
        description: Optional description

    Returns:
        New Council object (not persisted)
    """
    import uuid
    council_id = f"custom_{uuid.uuid4().hex[:8]}"

    return Council(
        id=council_id,
        name=name,
        description=description or f"Custom council: {name}",
        models=models,
        chairman=chairman,
        keywords=keywords or [],
        priority=0
    )


def get_council_info(council_id: str) -> Dict[str, Any]:
    """
    Get council information as a dictionary.

    Args:
        council_id: The council identifier

    Returns:
        Council info dict or empty dict if not found
    """
    council = get_council(council_id)
    if not council:
        return {}

    return {
        'id': council.id,
        'name': council.name,
        'description': council.description,
        'models': council.models,
        'chairman': council.chairman,
        'model_count': len(council.models),
        'keywords': council.keywords
    }
