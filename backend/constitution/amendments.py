"""Constitutional amendment system."""

import json
import os
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
from ..config import CONSTITUTION_CONFIG
from .storage import get_constitution_store


@dataclass
class Amendment:
    """Represents a proposed constitutional amendment."""
    id: str
    type: str  # 'add', 'modify', 'remove'
    target_article_id: Optional[str]  # For modify/remove
    proposed_text: Optional[str]  # For add/modify
    proposed_title: Optional[str]  # For add
    reason: str
    proposed_by: str
    proposed_at: str
    status: str = 'pending'  # pending, voting, passed, rejected, expired
    votes_for: int = 0
    votes_against: int = 0
    votes: List[Dict[str, Any]] = None
    voting_deadline: Optional[str] = None
    resolved_at: Optional[str] = None

    def __post_init__(self):
        if self.votes is None:
            self.votes = []


class AmendmentStore:
    """Manages amendment storage."""

    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.join(
            CONSTITUTION_CONFIG.get('storage_path', 'data/constitution'),
            'amendments.json'
        )
        self.amendments: Dict[str, Amendment] = {}
        self._ensure_storage_dir()
        self._load_amendments()

    def _ensure_storage_dir(self):
        """Ensure storage directory exists."""
        Path(os.path.dirname(self.storage_path)).mkdir(parents=True, exist_ok=True)

    def _load_amendments(self):
        """Load amendments from storage."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    for amend_data in data.get('amendments', []):
                        amend = Amendment(**amend_data)
                        self.amendments[amend.id] = amend
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                print(f"Error loading amendments: {e}")

    def _save_amendments(self):
        """Save amendments to storage."""
        self._ensure_storage_dir()
        data = {
            'version': '1.0',
            'last_updated': datetime.utcnow().isoformat(),
            'amendments': [asdict(a) for a in self.amendments.values()]
        }
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)

    def add_amendment(self, amendment: Amendment):
        """Add a new amendment."""
        self.amendments[amendment.id] = amendment
        self._save_amendments()

    def get_amendment(self, amendment_id: str) -> Optional[Amendment]:
        """Get an amendment by ID."""
        return self.amendments.get(amendment_id)

    def update_amendment(self, amendment_id: str, **updates):
        """Update an amendment."""
        if amendment_id in self.amendments:
            amend = self.amendments[amendment_id]
            amend_dict = asdict(amend)
            amend_dict.update(updates)
            self.amendments[amendment_id] = Amendment(**amend_dict)
            self._save_amendments()

    def get_pending_amendments(self) -> List[Amendment]:
        """Get all pending amendments."""
        return [a for a in self.amendments.values() if a.status in ['pending', 'voting']]

    def get_all_amendments(self, include_resolved: bool = True) -> List[Amendment]:
        """Get all amendments."""
        if include_resolved:
            return list(self.amendments.values())
        return [a for a in self.amendments.values() if a.status in ['pending', 'voting']]


# Singleton instance
_amendment_store: Optional[AmendmentStore] = None


def get_amendment_store() -> AmendmentStore:
    """Get the singleton amendment store."""
    global _amendment_store
    if _amendment_store is None:
        _amendment_store = AmendmentStore()
    return _amendment_store


def propose_amendment(
    amendment_type: str,
    reason: str,
    proposed_by: str,
    target_article_id: str = None,
    proposed_text: str = None,
    proposed_title: str = None,
    voting_days: int = 7
) -> Amendment:
    """
    Propose a new constitutional amendment.

    Args:
        amendment_type: Type of amendment ('add', 'modify', 'remove')
        reason: Reason for the amendment
        proposed_by: User/model proposing the amendment
        target_article_id: Article to modify/remove (required for modify/remove)
        proposed_text: New text (required for add/modify)
        proposed_title: Article title (required for add)
        voting_days: Number of days for voting period

    Returns:
        Created Amendment object
    """
    store = get_amendment_store()

    # Validate inputs
    if amendment_type not in ['add', 'modify', 'remove']:
        raise ValueError(f"Invalid amendment type: {amendment_type}")

    if amendment_type == 'add' and not proposed_title:
        raise ValueError("Title required for adding new article")

    if amendment_type in ['modify', 'remove'] and not target_article_id:
        raise ValueError("Target article ID required for modify/remove")

    if amendment_type in ['add', 'modify'] and not proposed_text:
        raise ValueError("Proposed text required for add/modify")

    # Calculate voting deadline
    deadline = datetime.utcnow() + timedelta(days=voting_days)

    amendment = Amendment(
        id=str(uuid.uuid4()),
        type=amendment_type,
        target_article_id=target_article_id,
        proposed_text=proposed_text,
        proposed_title=proposed_title,
        reason=reason,
        proposed_by=proposed_by,
        proposed_at=datetime.utcnow().isoformat(),
        status='voting',
        voting_deadline=deadline.isoformat()
    )

    store.add_amendment(amendment)
    return amendment


def vote_on_amendment(
    amendment_id: str,
    voter_id: str,
    vote: bool,
    reason: str = None
) -> Optional[Amendment]:
    """
    Cast a vote on an amendment.

    Args:
        amendment_id: Amendment ID
        voter_id: ID of the voter
        vote: True for yes, False for no
        reason: Optional reason for vote

    Returns:
        Updated Amendment or None
    """
    store = get_amendment_store()
    amendment = store.get_amendment(amendment_id)

    if not amendment:
        return None

    if amendment.status != 'voting':
        return amendment

    # Check if already voted
    existing_votes = amendment.votes or []
    for v in existing_votes:
        if v.get('voter_id') == voter_id:
            # Already voted - could update or reject
            return amendment

    # Record vote
    new_vote = {
        'voter_id': voter_id,
        'vote': vote,
        'reason': reason,
        'timestamp': datetime.utcnow().isoformat()
    }

    existing_votes.append(new_vote)

    # Update counts
    votes_for = len([v for v in existing_votes if v['vote']])
    votes_against = len([v for v in existing_votes if not v['vote']])

    store.update_amendment(
        amendment_id,
        votes=existing_votes,
        votes_for=votes_for,
        votes_against=votes_against
    )

    return store.get_amendment(amendment_id)


def get_pending_amendments() -> List[Dict[str, Any]]:
    """
    Get all pending amendments.

    Returns:
        List of amendment dicts
    """
    store = get_amendment_store()
    amendments = store.get_pending_amendments()

    # Check for expired amendments
    now = datetime.utcnow()
    for amend in amendments:
        if amend.voting_deadline:
            deadline = datetime.fromisoformat(amend.voting_deadline)
            if now > deadline and amend.status == 'voting':
                # Process expired amendment
                process_amendment_vote(amend.id)

    # Re-fetch after processing
    amendments = store.get_pending_amendments()

    return [asdict(a) for a in amendments]


def process_amendment_vote(amendment_id: str) -> Optional[Amendment]:
    """
    Process voting results for an amendment.

    Args:
        amendment_id: Amendment ID

    Returns:
        Processed Amendment or None
    """
    store = get_amendment_store()
    constitution_store = get_constitution_store()

    amendment = store.get_amendment(amendment_id)
    if not amendment or amendment.status != 'voting':
        return amendment

    # Determine result
    total_votes = amendment.votes_for + amendment.votes_against
    required_threshold = CONSTITUTION_CONFIG.get('amendment_threshold', 0.6)

    passed = False
    if total_votes > 0:
        approval_rate = amendment.votes_for / total_votes
        passed = approval_rate >= required_threshold

    if passed:
        # Apply amendment to constitution
        if amendment.type == 'add':
            constitution_store.add_article(
                {
                    'id': f"article_{amendment.id[:8]}",
                    'title': amendment.proposed_title,
                    'text': amendment.proposed_text,
                    'priority': 'medium',
                    'enforcement': 'advisory'
                },
                reason=f"Amendment {amendment.id} passed"
            )
        elif amendment.type == 'modify':
            constitution_store.update_article(
                amendment.target_article_id,
                {'text': amendment.proposed_text},
                reason=f"Amendment {amendment.id} passed"
            )
        elif amendment.type == 'remove':
            constitution_store.remove_article(
                amendment.target_article_id,
                reason=f"Amendment {amendment.id} passed"
            )

        store.update_amendment(
            amendment_id,
            status='passed',
            resolved_at=datetime.utcnow().isoformat()
        )
    else:
        store.update_amendment(
            amendment_id,
            status='rejected',
            resolved_at=datetime.utcnow().isoformat()
        )

    return store.get_amendment(amendment_id)


def get_amendment_history(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get amendment history.

    Args:
        limit: Maximum entries

    Returns:
        List of amendment dicts
    """
    store = get_amendment_store()
    all_amendments = store.get_all_amendments(include_resolved=True)

    # Sort by proposed date
    all_amendments.sort(key=lambda x: x.proposed_at, reverse=True)

    return [asdict(a) for a in all_amendments[:limit]]


def create_amendment_summary(amendment: Amendment) -> str:
    """
    Create a human-readable summary of an amendment.

    Args:
        amendment: Amendment to summarize

    Returns:
        Summary string
    """
    if amendment.type == 'add':
        action = f"Add new article: '{amendment.proposed_title}'"
    elif amendment.type == 'modify':
        action = f"Modify article {amendment.target_article_id}"
    else:
        action = f"Remove article {amendment.target_article_id}"

    status_emoji = {
        'pending': '⏳',
        'voting': '🗳️',
        'passed': '✅',
        'rejected': '❌',
        'expired': '⏰'
    }.get(amendment.status, '❓')

    return f"""
{status_emoji} Amendment {amendment.id[:8]}

Action: {action}
Proposed by: {amendment.proposed_by}
Reason: {amendment.reason}

Status: {amendment.status.upper()}
Votes: {amendment.votes_for} for / {amendment.votes_against} against
Deadline: {amendment.voting_deadline}
""".strip()
