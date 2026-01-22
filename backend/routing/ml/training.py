"""Training utilities for the routing model."""

import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict

from .features import extract_features
from .model import get_routing_model


@dataclass
class TrainingSample:
    """A training sample for the routing model."""
    query: str
    features: List[float]
    predicted_tier: int
    actual_tier: int
    feedback_score: float  # 1-5 rating
    timestamp: str
    conversation_id: Optional[str] = None


class TrainingDataStore:
    """Stores training data for the routing model."""

    def __init__(self, storage_path: str = "data/routing/training_data.json"):
        self.storage_path = storage_path
        self.samples: List[TrainingSample] = []
        self._ensure_dir()
        self._load_data()

    def _ensure_dir(self):
        """Ensure the storage directory exists."""
        Path(os.path.dirname(self.storage_path)).mkdir(parents=True, exist_ok=True)

    def _load_data(self):
        """Load training data from file."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.samples = [
                        TrainingSample(**s) for s in data.get('samples', [])
                    ]
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error loading training data: {e}")
                self.samples = []

    def _save_data(self):
        """Save training data to file."""
        self._ensure_dir()
        data = {
            'samples': [asdict(s) for s in self.samples],
            'last_updated': datetime.utcnow().isoformat(),
            'count': len(self.samples),
        }
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)

    def add_sample(self, sample: TrainingSample):
        """Add a training sample."""
        self.samples.append(sample)
        self._save_data()

    def get_samples(self, limit: int = None) -> List[TrainingSample]:
        """Get training samples."""
        if limit:
            return self.samples[-limit:]
        return self.samples

    def get_stats(self) -> Dict[str, Any]:
        """Get training data statistics."""
        if not self.samples:
            return {'count': 0}

        tier_counts = {1: 0, 2: 0, 3: 0}
        accuracy_sum = 0

        for s in self.samples:
            if s.actual_tier in tier_counts:
                tier_counts[s.actual_tier] += 1
            if s.predicted_tier == s.actual_tier:
                accuracy_sum += 1

        return {
            'count': len(self.samples),
            'tier_distribution': tier_counts,
            'accuracy': accuracy_sum / len(self.samples) if self.samples else 0,
            'avg_feedback': sum(s.feedback_score for s in self.samples) / len(self.samples),
        }


# Singleton instance
_training_store: Optional[TrainingDataStore] = None


def get_training_store() -> TrainingDataStore:
    """Get the singleton training data store."""
    global _training_store
    if _training_store is None:
        _training_store = TrainingDataStore()
    return _training_store


def collect_training_sample(
    query: str,
    predicted_tier: int,
    actual_tier: int,
    feedback_score: float,
    conversation_id: str = None
) -> TrainingSample:
    """
    Collect a training sample from user feedback.

    Args:
        query: The original query
        predicted_tier: The tier the model predicted
        actual_tier: The tier that should have been used
        feedback_score: User feedback (1-5)
        conversation_id: Optional conversation ID

    Returns:
        The created TrainingSample
    """
    features = extract_features(query)
    feature_vector = features.to_vector()

    sample = TrainingSample(
        query=query,
        features=feature_vector,
        predicted_tier=predicted_tier,
        actual_tier=actual_tier,
        feedback_score=feedback_score,
        timestamp=datetime.utcnow().isoformat(),
        conversation_id=conversation_id,
    )

    store = get_training_store()
    store.add_sample(sample)

    return sample


def train_model(
    samples: List[TrainingSample] = None,
    learning_rate: float = 0.01,
    epochs: int = 10
) -> Dict[str, Any]:
    """
    Train the routing model on collected samples.

    Args:
        samples: Training samples (uses stored samples if None)
        learning_rate: Learning rate for weight updates
        epochs: Number of training epochs

    Returns:
        Training statistics
    """
    model = get_routing_model()
    store = get_training_store()

    if samples is None:
        samples = store.get_samples()

    if not samples:
        return {'status': 'no_data', 'samples': 0}

    # Training loop
    for epoch in range(epochs):
        for sample in samples:
            model.update_weights(
                features=sample.features,
                actual_tier=sample.actual_tier,
                learning_rate=learning_rate
            )

    return {
        'status': 'trained',
        'samples': len(samples),
        'epochs': epochs,
        'model_info': model.get_model_info(),
    }


def auto_train_on_feedback(
    query: str,
    predicted_tier: int,
    feedback_score: float,
    threshold: float = 3.0
):
    """
    Automatically train if feedback indicates prediction was wrong.

    Args:
        query: The query
        predicted_tier: What the model predicted
        feedback_score: User feedback (1-5)
        threshold: Below this, assume prediction was wrong
    """
    if feedback_score < threshold:
        # Determine what tier should have been used based on feedback
        # Low feedback + tier 1 -> probably needed tier 2 or 3
        # Low feedback + tier 3 -> probably could have been tier 1 or 2
        if predicted_tier == 1:
            actual_tier = 2  # Needed more models
        elif predicted_tier == 3:
            actual_tier = 2  # Overkill, could use fewer
        else:
            actual_tier = predicted_tier  # Keep tier 2

        sample = collect_training_sample(
            query=query,
            predicted_tier=predicted_tier,
            actual_tier=actual_tier,
            feedback_score=feedback_score,
        )

        # Update model immediately
        model = get_routing_model()
        model.update_weights(sample.features, actual_tier, learning_rate=0.01)
