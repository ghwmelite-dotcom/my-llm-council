"""Machine learning routing model."""

import json
import os
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

from .features import extract_features, QueryFeatures
from ...config import data_path


@dataclass
class RoutingPrediction:
    """Prediction from the routing model."""
    tier: int  # 1 = single, 2 = mini, 3 = full
    confidence: float
    reasoning: str
    features: Dict[str, Any]


class RoutingModel:
    """
    ML-based routing model that learns from past queries.

    Uses a simple weighted scoring model that can be trained
    from historical data.
    """

    def __init__(self, model_path: str = None):
        if model_path is None:
            model_path = data_path("routing", "model.json")
        self.model_path = model_path
        self.weights: List[float] = []
        self.bias: List[float] = [0.0, 0.0, 0.0]  # Bias for each tier
        self.training_samples: int = 0
        self.last_trained: Optional[str] = None
        self._ensure_dir()
        self._load_model()

    def _ensure_dir(self):
        """Ensure the model directory exists."""
        Path(os.path.dirname(self.model_path)).mkdir(parents=True, exist_ok=True)

    def _load_model(self):
        """Load model from file."""
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'r') as f:
                    data = json.load(f)
                    self.weights = data.get('weights', [])
                    self.bias = data.get('bias', [0.0, 0.0, 0.0])
                    self.training_samples = data.get('training_samples', 0)
                    self.last_trained = data.get('last_trained')
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading routing model: {e}")
                self._initialize_weights()
        else:
            self._initialize_weights()

    def _initialize_weights(self):
        """Initialize model weights with heuristics."""
        # 16 features, weights for predicting "complexity score"
        # Higher score = more complex = higher tier
        self.weights = [
            0.3,   # char_count (normalized)
            0.4,   # word_count (normalized)
            0.3,   # sentence_count
            0.1,   # avg_word_length
            0.4,   # question_count
            0.5,   # has_multiple_questions
            0.2,   # has_bullet_points
            0.3,   # has_code_block
            0.3,   # technical_keyword_count
            0.4,   # reasoning_keyword_count
            0.2,   # creative_keyword_count
            -0.5,  # matches_simple_pattern (negative = lower complexity)
            0.3,   # has_conditional
            0.4,   # has_comparison
            0.3,   # nested_clause_count
            0.2,   # conjunction_count
        ]

    def _save_model(self):
        """Save model to file."""
        self._ensure_dir()
        data = {
            'weights': self.weights,
            'bias': self.bias,
            'training_samples': self.training_samples,
            'last_trained': self.last_trained,
            'version': '1.0',
        }
        with open(self.model_path, 'w') as f:
            json.dump(data, f, indent=2)

    def predict(self, query: str) -> RoutingPrediction:
        """
        Predict the optimal routing tier for a query.

        Args:
            query: The user's query

        Returns:
            RoutingPrediction with tier, confidence, and reasoning
        """
        features = extract_features(query)
        feature_vector = features.to_vector()

        # Calculate complexity score
        complexity_score = sum(w * f for w, f in zip(self.weights, feature_vector))

        # Add biases and determine tier
        tier_scores = [
            complexity_score + self.bias[0],  # Tier 1
            complexity_score + self.bias[1],  # Tier 2
            complexity_score + self.bias[2],  # Tier 3
        ]

        # Determine tier based on thresholds
        if complexity_score < 0.3:
            tier = 1
            confidence = 1.0 - complexity_score / 0.3
        elif complexity_score < 0.7:
            tier = 2
            confidence = 1.0 - abs(complexity_score - 0.5) / 0.2
        else:
            tier = 3
            confidence = min(1.0, (complexity_score - 0.7) / 0.3 + 0.5)

        # Generate reasoning
        reasoning_parts = []
        if features.matches_simple_pattern:
            reasoning_parts.append("matches simple query pattern")
        if features.has_multiple_questions:
            reasoning_parts.append("contains multiple questions")
        if features.technical_keyword_count > 2:
            reasoning_parts.append("highly technical content")
        if features.reasoning_keyword_count > 2:
            reasoning_parts.append("requires analytical reasoning")
        if features.has_comparison:
            reasoning_parts.append("involves comparison")

        reasoning = ", ".join(reasoning_parts) if reasoning_parts else "based on query complexity"

        return RoutingPrediction(
            tier=tier,
            confidence=min(1.0, max(0.0, confidence)),
            reasoning=f"Tier {tier} recommended: {reasoning}",
            features=features.to_dict(),
        )

    def update_weights(
        self,
        features: List[float],
        actual_tier: int,
        learning_rate: float = 0.01
    ):
        """
        Update model weights based on feedback.

        Args:
            features: Feature vector from the query
            actual_tier: The tier that should have been used (1, 2, or 3)
            learning_rate: Learning rate for weight updates
        """
        # Calculate current prediction
        complexity_score = sum(w * f for w, f in zip(self.weights, features))

        # Target score based on actual tier
        target_scores = {1: 0.15, 2: 0.5, 3: 0.85}
        target = target_scores[actual_tier]

        # Update weights using gradient descent
        error = target - complexity_score
        for i in range(len(self.weights)):
            self.weights[i] += learning_rate * error * features[i]

        self.training_samples += 1
        self.last_trained = datetime.utcnow().isoformat()
        self._save_model()

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information and statistics."""
        return {
            'training_samples': self.training_samples,
            'last_trained': self.last_trained,
            'weight_count': len(self.weights),
            'version': '1.0',
        }


# Singleton instance
_routing_model: Optional[RoutingModel] = None


def get_routing_model() -> RoutingModel:
    """Get the singleton routing model instance."""
    global _routing_model
    if _routing_model is None:
        _routing_model = RoutingModel()
    return _routing_model
