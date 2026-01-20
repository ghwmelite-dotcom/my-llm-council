"""Track and analyze relationships between council models."""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from ..config import MEMORY_CONFIG


@dataclass
class ModelRelationship:
    """Represents the relationship between two models."""
    model_a: str
    model_b: str
    agreement_rate: float  # 0-1, how often they rank similarly
    interaction_count: int
    last_interaction: str
    agreement_history: List[bool]  # Recent agreement/disagreement


class RelationshipTracker:
    """Tracks agreement patterns between council models."""

    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or MEMORY_CONFIG.get(
            'relationships_path', 'data/memory/relationships.json'
        )
        self.relationships: Dict[str, ModelRelationship] = {}
        self._ensure_storage_dir()
        self._load_relationships()

    def _ensure_storage_dir(self):
        """Ensure the storage directory exists."""
        Path(os.path.dirname(self.storage_path)).mkdir(parents=True, exist_ok=True)

    def _get_pair_key(self, model_a: str, model_b: str) -> str:
        """Get a consistent key for a model pair."""
        return f"{min(model_a, model_b)}|{max(model_a, model_b)}"

    def _load_relationships(self):
        """Load relationships from JSON file."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    for key, rel_data in data.get('relationships', {}).items():
                        self.relationships[key] = ModelRelationship(**rel_data)
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error loading relationships: {e}")
                self.relationships = {}
        else:
            self.relationships = {}

    def _save_relationships(self):
        """Save relationships to JSON file."""
        self._ensure_storage_dir()
        data = {
            'version': '1.0',
            'last_updated': datetime.utcnow().isoformat(),
            'relationships': {
                key: asdict(rel) for key, rel in self.relationships.items()
            }
        }
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)

    def get_relationship(
        self,
        model_a: str,
        model_b: str
    ) -> Optional[ModelRelationship]:
        """Get the relationship between two models."""
        key = self._get_pair_key(model_a, model_b)
        return self.relationships.get(key)

    def record_interaction(
        self,
        model_a: str,
        model_b: str,
        agreed: bool
    ):
        """
        Record an interaction between two models.

        Args:
            model_a: First model
            model_b: Second model
            agreed: Whether they agreed (ranked similarly)
        """
        key = self._get_pair_key(model_a, model_b)

        if key in self.relationships:
            rel = self.relationships[key]
            rel.interaction_count += 1
            rel.last_interaction = datetime.utcnow().isoformat()

            # Update agreement history (keep last 20 interactions)
            rel.agreement_history.append(agreed)
            if len(rel.agreement_history) > 20:
                rel.agreement_history = rel.agreement_history[-20:]

            # Recalculate agreement rate
            rel.agreement_rate = sum(rel.agreement_history) / len(rel.agreement_history)
        else:
            # Create new relationship
            self.relationships[key] = ModelRelationship(
                model_a=min(model_a, model_b),
                model_b=max(model_a, model_b),
                agreement_rate=1.0 if agreed else 0.0,
                interaction_count=1,
                last_interaction=datetime.utcnow().isoformat(),
                agreement_history=[agreed]
            )

        self._save_relationships()

    def update_from_rankings(
        self,
        rankings: List[Dict[str, Any]],
        label_to_model: Dict[str, str]
    ):
        """
        Update relationships based on ranking results.

        Args:
            rankings: List of model rankings
            label_to_model: Mapping from labels to model names
        """
        # Extract parsed rankings
        model_rankings = {}
        for ranking in rankings:
            model = ranking['model']
            parsed = ranking.get('parsed_ranking', [])
            if parsed:
                # Convert labels to model names
                model_rankings[model] = [
                    label_to_model.get(label, label) for label in parsed
                ]

        # Compare each pair of models
        models = list(model_rankings.keys())
        for i, model_a in enumerate(models):
            for model_b in models[i + 1:]:
                ranking_a = model_rankings.get(model_a, [])
                ranking_b = model_rankings.get(model_b, [])

                if ranking_a and ranking_b:
                    # Check if top 2 choices overlap
                    top_a = set(ranking_a[:2]) if len(ranking_a) >= 2 else set(ranking_a)
                    top_b = set(ranking_b[:2]) if len(ranking_b) >= 2 else set(ranking_b)
                    agreed = len(top_a & top_b) > 0

                    self.record_interaction(model_a, model_b, agreed)

    def get_all_relationships(self) -> List[ModelRelationship]:
        """Get all tracked relationships."""
        return list(self.relationships.values())

    def get_strongest_agreements(self, limit: int = 5) -> List[ModelRelationship]:
        """Get model pairs with highest agreement rates."""
        sorted_rels = sorted(
            self.relationships.values(),
            key=lambda r: (r.agreement_rate, r.interaction_count),
            reverse=True
        )
        return sorted_rels[:limit]

    def get_strongest_disagreements(self, limit: int = 5) -> List[ModelRelationship]:
        """Get model pairs with lowest agreement rates."""
        sorted_rels = sorted(
            self.relationships.values(),
            key=lambda r: (r.agreement_rate, -r.interaction_count)
        )
        return sorted_rels[:limit]

    def get_model_allies(self, model: str, limit: int = 3) -> List[Tuple[str, float]]:
        """
        Get models that most often agree with the given model.

        Args:
            model: The model to find allies for
            limit: Maximum number of allies to return

        Returns:
            List of (model_id, agreement_rate) tuples
        """
        allies = []
        for rel in self.relationships.values():
            if rel.model_a == model:
                allies.append((rel.model_b, rel.agreement_rate))
            elif rel.model_b == model:
                allies.append((rel.model_a, rel.agreement_rate))

        allies.sort(key=lambda x: x[1], reverse=True)
        return allies[:limit]

    def get_model_rivals(self, model: str, limit: int = 3) -> List[Tuple[str, float]]:
        """
        Get models that most often disagree with the given model.

        Args:
            model: The model to find rivals for
            limit: Maximum number of rivals to return

        Returns:
            List of (model_id, disagreement_rate) tuples
        """
        rivals = []
        for rel in self.relationships.values():
            if rel.model_a == model:
                rivals.append((rel.model_b, 1 - rel.agreement_rate))
            elif rel.model_b == model:
                rivals.append((rel.model_a, 1 - rel.agreement_rate))

        rivals.sort(key=lambda x: x[1], reverse=True)
        return rivals[:limit]

    def get_relationship_summary(self) -> Dict[str, Any]:
        """Get a summary of all relationships."""
        if not self.relationships:
            return {
                'total_relationships': 0,
                'avg_agreement_rate': 0,
                'total_interactions': 0
            }

        agreement_rates = [r.agreement_rate for r in self.relationships.values()]
        interactions = [r.interaction_count for r in self.relationships.values()]

        return {
            'total_relationships': len(self.relationships),
            'avg_agreement_rate': sum(agreement_rates) / len(agreement_rates),
            'total_interactions': sum(interactions),
            'strongest_pair': self.get_strongest_agreements(1)[0] if self.relationships else None,
            'weakest_pair': self.get_strongest_disagreements(1)[0] if self.relationships else None
        }


# Singleton instance
_relationship_tracker: Optional[RelationshipTracker] = None


def get_relationship_tracker() -> RelationshipTracker:
    """Get the singleton relationship tracker instance."""
    global _relationship_tracker
    if _relationship_tracker is None:
        _relationship_tracker = RelationshipTracker()
    return _relationship_tracker
