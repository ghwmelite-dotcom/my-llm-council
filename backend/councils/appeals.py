"""Handle appeals to the Supreme Council."""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import uuid
from .definitions import get_supreme_council, get_council


@dataclass
class Appeal:
    """Represents an appeal to the Supreme Council."""
    id: str
    original_query: str
    original_council: str
    original_response: str
    appeal_reason: str
    created_at: str
    status: str  # 'pending', 'reviewing', 'completed', 'rejected'
    supreme_response: Optional[str] = None
    resolution: Optional[str] = None


# In-memory appeal storage (could be persisted)
_appeals: Dict[str, Appeal] = {}


def create_appeal(
    original_query: str,
    original_council: str,
    original_response: str,
    appeal_reason: str
) -> Appeal:
    """
    Create a new appeal to the Supreme Council.

    Args:
        original_query: The original user query
        original_council: ID of the council that handled the query
        original_response: The original council's response
        appeal_reason: Why the user is appealing

    Returns:
        The created Appeal object
    """
    appeal = Appeal(
        id=str(uuid.uuid4()),
        original_query=original_query,
        original_council=original_council,
        original_response=original_response,
        appeal_reason=appeal_reason,
        created_at=datetime.utcnow().isoformat(),
        status='pending'
    )

    _appeals[appeal.id] = appeal
    return appeal


async def process_appeal(appeal_id: str) -> Optional[Appeal]:
    """
    Process an appeal through the Supreme Council.

    Args:
        appeal_id: The appeal ID to process

    Returns:
        Updated Appeal object or None if not found
    """
    from .executor import run_specialized_council

    appeal = _appeals.get(appeal_id)
    if not appeal:
        return None

    if appeal.status != 'pending':
        return appeal

    # Update status
    appeal.status = 'reviewing'

    # Get Supreme Council
    supreme = get_supreme_council()

    # Create appeal context
    original_council = get_council(appeal.original_council)
    council_name = original_council.name if original_council else 'Unknown Council'

    appeal_context = f"""
APPEAL TO SUPREME COUNCIL

This is an appeal of a decision made by the {council_name}.

ORIGINAL QUERY:
{appeal.original_query}

ORIGINAL COUNCIL'S RESPONSE:
{appeal.original_response}

APPEAL REASON:
{appeal.appeal_reason}

Your task as the Supreme Council is to:
1. Review the original query and response
2. Consider the appeal reason
3. Determine if the original response was adequate
4. Provide a revised response if the appeal has merit, or uphold the original decision with explanation
"""

    try:
        # Run through Supreme Council
        result = await run_specialized_council(
            appeal_context,
            supreme,
            is_appeal=True
        )

        appeal.supreme_response = result.get('stage3', {}).get('response', '')

        # Determine resolution
        if "uphold" in appeal.supreme_response.lower():
            appeal.resolution = "upheld"
        elif "revise" in appeal.supreme_response.lower() or "override" in appeal.supreme_response.lower():
            appeal.resolution = "overturned"
        else:
            appeal.resolution = "modified"

        appeal.status = 'completed'

    except Exception as e:
        appeal.status = 'rejected'
        appeal.resolution = f"Error processing appeal: {str(e)}"

    return appeal


def get_appeal(appeal_id: str) -> Optional[Appeal]:
    """Get an appeal by ID."""
    return _appeals.get(appeal_id)


def get_pending_appeals() -> List[Appeal]:
    """Get all pending appeals."""
    return [a for a in _appeals.values() if a.status == 'pending']


def get_appeal_summary(appeal_id: str) -> Dict[str, Any]:
    """
    Get a summary of an appeal.

    Args:
        appeal_id: The appeal ID

    Returns:
        Appeal summary dict or empty dict if not found
    """
    appeal = get_appeal(appeal_id)
    if not appeal:
        return {}

    return {
        'id': appeal.id,
        'status': appeal.status,
        'original_council': appeal.original_council,
        'appeal_reason': appeal.appeal_reason[:200] + '...' if len(appeal.appeal_reason) > 200 else appeal.appeal_reason,
        'resolution': appeal.resolution,
        'created_at': appeal.created_at,
        'has_response': appeal.supreme_response is not None
    }


def build_appeal_prompt(appeal: Appeal, original_council_name: str) -> str:
    """
    Build the full prompt for Supreme Council review.

    Args:
        appeal: The appeal to process
        original_council_name: Name of the original council

    Returns:
        Formatted prompt string
    """
    return f"""SUPREME COUNCIL APPEAL REVIEW

Case ID: {appeal.id}
Filed: {appeal.created_at}
Original Council: {original_council_name}

═══════════════════════════════════════════════════

ORIGINAL QUERY:
{appeal.original_query}

═══════════════════════════════════════════════════

ORIGINAL RESPONSE:
{appeal.original_response}

═══════════════════════════════════════════════════

GROUNDS FOR APPEAL:
{appeal.appeal_reason}

═══════════════════════════════════════════════════

SUPREME COUNCIL INSTRUCTIONS:

As the Supreme Council, you have full authority to review and potentially overturn decisions made by specialized councils. Your review should:

1. EVALUATE the original query's complexity and requirements
2. ASSESS whether the original council was appropriate for this query
3. EXAMINE the quality and accuracy of the original response
4. CONSIDER the appellant's concerns and their validity
5. RENDER a final decision:
   - UPHOLD: The original response stands
   - MODIFY: The response is partially correct but needs refinement
   - OVERTURN: The response is inadequate and should be replaced

Provide your comprehensive ruling with clear reasoning."""
