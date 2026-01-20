"""Prediction betting system."""

import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
from ..config import PREDICTIONS_CONFIG


@dataclass
class Prediction:
    """Represents a prediction on a council debate."""
    id: str
    user_id: str
    conversation_id: str
    predicted_winner: str  # Model ID
    confidence: float  # 0-1, how confident the user is
    placed_at: str
    resolved: bool = False
    actual_winner: Optional[str] = None
    correct: Optional[bool] = None
    points_earned: float = 0.0


class PredictionStore:
    """Manages prediction storage."""

    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.join(
            PREDICTIONS_CONFIG.get('storage_path', 'data/predictions'),
            'predictions.json'
        )
        self.predictions: Dict[str, Prediction] = {}
        self._ensure_storage_dir()
        self._load_predictions()

    def _ensure_storage_dir(self):
        """Ensure storage directory exists."""
        Path(os.path.dirname(self.storage_path)).mkdir(parents=True, exist_ok=True)

    def _load_predictions(self):
        """Load predictions from storage."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    for pred_data in data.get('predictions', []):
                        pred = Prediction(**pred_data)
                        self.predictions[pred.id] = pred
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error loading predictions: {e}")

    def _save_predictions(self):
        """Save predictions to storage."""
        self._ensure_storage_dir()
        data = {
            'version': '1.0',
            'last_updated': datetime.utcnow().isoformat(),
            'predictions': [asdict(p) for p in self.predictions.values()]
        }
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)

    def add_prediction(self, prediction: Prediction):
        """Add a new prediction."""
        self.predictions[prediction.id] = prediction
        self._save_predictions()

    def get_prediction(self, prediction_id: str) -> Optional[Prediction]:
        """Get a prediction by ID."""
        return self.predictions.get(prediction_id)

    def update_prediction(self, prediction_id: str, **updates):
        """Update a prediction."""
        if prediction_id in self.predictions:
            pred = self.predictions[prediction_id]
            pred_dict = asdict(pred)
            pred_dict.update(updates)
            self.predictions[prediction_id] = Prediction(**pred_dict)
            self._save_predictions()

    def get_user_predictions(self, user_id: str) -> List[Prediction]:
        """Get all predictions for a user."""
        return [p for p in self.predictions.values() if p.user_id == user_id]

    def get_conversation_predictions(self, conversation_id: str) -> List[Prediction]:
        """Get all predictions for a conversation."""
        return [p for p in self.predictions.values() if p.conversation_id == conversation_id]

    def get_unresolved_predictions(self) -> List[Prediction]:
        """Get all unresolved predictions."""
        return [p for p in self.predictions.values() if not p.resolved]


# Singleton instance
_prediction_store: Optional[PredictionStore] = None


def get_prediction_store() -> PredictionStore:
    """Get the singleton prediction store."""
    global _prediction_store
    if _prediction_store is None:
        _prediction_store = PredictionStore()
    return _prediction_store


def place_prediction(
    user_id: str,
    conversation_id: str,
    predicted_winner: str,
    confidence: float = 0.5
) -> Prediction:
    """
    Place a prediction on which model will win the council debate.

    Args:
        user_id: The user placing the prediction
        conversation_id: The conversation/debate ID
        predicted_winner: The model ID predicted to win
        confidence: Confidence level (0-1)

    Returns:
        The created Prediction object
    """
    store = get_prediction_store()

    # Validate confidence
    confidence = max(0.1, min(1.0, confidence))

    prediction = Prediction(
        id=str(uuid.uuid4()),
        user_id=user_id,
        conversation_id=conversation_id,
        predicted_winner=predicted_winner,
        confidence=confidence,
        placed_at=datetime.utcnow().isoformat()
    )

    store.add_prediction(prediction)
    return prediction


def resolve_prediction(
    prediction_id: str,
    actual_winner: str
) -> Optional[Prediction]:
    """
    Resolve a prediction with the actual outcome.

    Args:
        prediction_id: The prediction to resolve
        actual_winner: The model that actually won

    Returns:
        Updated Prediction object or None
    """
    from .scoring import score_prediction

    store = get_prediction_store()
    prediction = store.get_prediction(prediction_id)

    if not prediction or prediction.resolved:
        return prediction

    # Determine if prediction was correct
    correct = prediction.predicted_winner == actual_winner

    # Calculate points earned
    points = score_prediction(prediction.confidence, correct)

    # Update prediction
    store.update_prediction(
        prediction_id,
        resolved=True,
        actual_winner=actual_winner,
        correct=correct,
        points_earned=points
    )

    return store.get_prediction(prediction_id)


def resolve_conversation_predictions(
    conversation_id: str,
    actual_winner: str
) -> List[Prediction]:
    """
    Resolve all predictions for a conversation.

    Args:
        conversation_id: The conversation ID
        actual_winner: The winning model

    Returns:
        List of resolved predictions
    """
    store = get_prediction_store()
    predictions = store.get_conversation_predictions(conversation_id)

    resolved = []
    for pred in predictions:
        if not pred.resolved:
            resolved_pred = resolve_prediction(pred.id, actual_winner)
            if resolved_pred:
                resolved.append(resolved_pred)

    return resolved


def get_user_predictions(user_id: str) -> List[Dict[str, Any]]:
    """
    Get all predictions for a user with stats.

    Args:
        user_id: The user ID

    Returns:
        List of prediction dicts with stats
    """
    store = get_prediction_store()
    predictions = store.get_user_predictions(user_id)

    return [
        {
            'id': p.id,
            'conversation_id': p.conversation_id,
            'predicted_winner': p.predicted_winner,
            'confidence': p.confidence,
            'placed_at': p.placed_at,
            'resolved': p.resolved,
            'correct': p.correct,
            'points_earned': p.points_earned
        }
        for p in predictions
    ]


def get_user_prediction_stats(user_id: str) -> Dict[str, Any]:
    """
    Get prediction statistics for a user.

    Args:
        user_id: The user ID

    Returns:
        Stats dict
    """
    store = get_prediction_store()
    predictions = store.get_user_predictions(user_id)

    resolved = [p for p in predictions if p.resolved]
    correct = [p for p in resolved if p.correct]

    total_points = sum(p.points_earned for p in resolved)
    accuracy = len(correct) / len(resolved) if resolved else 0

    return {
        'total_predictions': len(predictions),
        'resolved_predictions': len(resolved),
        'correct_predictions': len(correct),
        'accuracy': accuracy,
        'total_points': total_points,
        'average_confidence': sum(p.confidence for p in predictions) / len(predictions) if predictions else 0
    }
