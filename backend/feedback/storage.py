"""Feedback storage for user ratings."""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from threading import Lock

from ..config import data_path


@dataclass
class Feedback:
    """User feedback for a response."""
    id: str
    conversation_id: str
    message_index: int
    rating: int  # 1-5 stars
    feedback_type: str  # 'helpful', 'accurate', 'clear', 'overall'
    comment: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "message_index": self.message_index,
            "rating": self.rating,
            "feedback_type": self.feedback_type,
            "comment": self.comment,
            "timestamp": self.timestamp.isoformat(),
        }


class FeedbackStorage:
    """Storage for feedback data."""
    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.storage_path = data_path("feedback.json")
        self.feedback: List[Feedback] = []
        self._load()
        self._initialized = True

    def _load(self):
        """Load feedback from disk."""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    for item in data.get('feedback', []):
                        self.feedback.append(Feedback(
                            id=item['id'],
                            conversation_id=item['conversation_id'],
                            message_index=item['message_index'],
                            rating=item['rating'],
                            feedback_type=item['feedback_type'],
                            comment=item.get('comment'),
                            timestamp=datetime.fromisoformat(item['timestamp'])
                        ))
        except Exception as e:
            print(f"Failed to load feedback: {e}")

    def _save(self):
        """Save feedback to disk."""
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            data = {
                'feedback': [f.to_dict() for f in self.feedback]
            }
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Failed to save feedback: {e}")

    def add_feedback(
        self,
        conversation_id: str,
        message_index: int,
        rating: int,
        feedback_type: str = 'overall',
        comment: Optional[str] = None
    ) -> Feedback:
        """Add feedback for a response."""
        import uuid
        feedback = Feedback(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            message_index=message_index,
            rating=min(5, max(1, rating)),  # Clamp to 1-5
            feedback_type=feedback_type,
            comment=comment
        )
        self.feedback.append(feedback)
        self._save()
        return feedback

    def get_feedback_for_conversation(self, conversation_id: str) -> List[Feedback]:
        """Get all feedback for a conversation."""
        return [f for f in self.feedback if f.conversation_id == conversation_id]

    def get_feedback_stats(self) -> dict:
        """Get overall feedback statistics."""
        if not self.feedback:
            return {
                "total_feedback": 0,
                "average_rating": 0,
                "rating_distribution": {},
            }

        ratings = [f.rating for f in self.feedback]
        distribution = {}
        for r in range(1, 6):
            distribution[r] = sum(1 for rating in ratings if rating == r)

        return {
            "total_feedback": len(self.feedback),
            "average_rating": sum(ratings) / len(ratings),
            "rating_distribution": distribution,
            "by_type": self._stats_by_type(),
        }

    def _stats_by_type(self) -> dict:
        """Get stats grouped by feedback type."""
        by_type = {}
        for f in self.feedback:
            if f.feedback_type not in by_type:
                by_type[f.feedback_type] = []
            by_type[f.feedback_type].append(f.rating)

        return {
            t: {
                "count": len(ratings),
                "average": sum(ratings) / len(ratings)
            }
            for t, ratings in by_type.items()
        }


_storage: Optional[FeedbackStorage] = None


def get_feedback_storage() -> FeedbackStorage:
    """Get the global feedback storage."""
    global _storage
    if _storage is None:
        _storage = FeedbackStorage()
    return _storage
