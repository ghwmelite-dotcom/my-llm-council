"""Elo rating system for council models."""

import json
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
from ..config import PREDICTIONS_CONFIG


# Default Elo rating for new models
DEFAULT_ELO = 1500

# K-factor determines how much ratings change after each match
K_FACTOR = 32


class EloStore:
    """Manages Elo rating storage."""

    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.join(
            PREDICTIONS_CONFIG.get('storage_path', 'data/predictions'),
            'elo_ratings.json'
        )
        self.ratings: Dict[str, float] = {}
        self.history: List[Dict[str, Any]] = []
        self._ensure_storage_dir()
        self._load_ratings()

    def _ensure_storage_dir(self):
        """Ensure storage directory exists."""
        Path(os.path.dirname(self.storage_path)).mkdir(parents=True, exist_ok=True)

    def _load_ratings(self):
        """Load ratings from storage."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.ratings = data.get('ratings', {})
                    self.history = data.get('history', [])
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error loading Elo ratings: {e}")

    def _save_ratings(self):
        """Save ratings to storage."""
        self._ensure_storage_dir()
        data = {
            'version': '1.0',
            'last_updated': datetime.utcnow().isoformat(),
            'ratings': self.ratings,
            'history': self.history[-1000:]  # Keep last 1000 history entries
        }
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)

    def get_rating(self, model_id: str) -> float:
        """Get Elo rating for a model."""
        return self.ratings.get(model_id, DEFAULT_ELO)

    def set_rating(self, model_id: str, rating: float):
        """Set Elo rating for a model."""
        self.ratings[model_id] = rating
        self._save_ratings()

    def get_all_ratings(self) -> Dict[str, float]:
        """Get all model ratings."""
        return self.ratings.copy()

    def add_history_entry(self, entry: Dict[str, Any]):
        """Add a history entry."""
        self.history.append(entry)
        self._save_ratings()

    def get_history(self, model_id: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get rating history, optionally filtered by model."""
        if model_id:
            filtered = [h for h in self.history if model_id in h.get('models', [])]
            return filtered[-limit:]
        return self.history[-limit:]


# Singleton instance
_elo_store: Optional[EloStore] = None


def get_elo_store() -> EloStore:
    """Get the singleton Elo store."""
    global _elo_store
    if _elo_store is None:
        _elo_store = EloStore()
    return _elo_store


def calculate_expected_score(rating_a: float, rating_b: float) -> float:
    """
    Calculate expected score for player A against player B.

    Uses the standard Elo formula:
    E_A = 1 / (1 + 10^((R_B - R_A) / 400))

    Args:
        rating_a: Elo rating of player A
        rating_b: Elo rating of player B

    Returns:
        Expected score (0-1) for player A
    """
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))


def calculate_new_rating(
    current_rating: float,
    expected_score: float,
    actual_score: float,
    k_factor: float = K_FACTOR
) -> float:
    """
    Calculate new Elo rating after a match.

    R_new = R_old + K * (S - E)

    Args:
        current_rating: Current Elo rating
        expected_score: Expected score (0-1)
        actual_score: Actual score (0, 0.5, or 1)
        k_factor: K-factor for rating adjustment

    Returns:
        New Elo rating
    """
    return current_rating + k_factor * (actual_score - expected_score)


def update_elo_ratings(
    winner_id: str,
    loser_ids: List[str],
    conversation_id: str = None
) -> Dict[str, Dict[str, float]]:
    """
    Update Elo ratings after a council debate.

    The winner gains rating, losers lose rating based on expected outcomes.

    Args:
        winner_id: Model ID of the winner
        loser_ids: List of model IDs that lost
        conversation_id: Optional conversation ID for tracking

    Returns:
        Dict mapping model_id to {old_rating, new_rating, change}
    """
    store = get_elo_store()

    results = {}

    # Get current ratings
    winner_rating = store.get_rating(winner_id)

    # Calculate winner's new rating against each loser
    total_expected = 0
    total_actual = len(loser_ids)  # Winner beat all losers

    for loser_id in loser_ids:
        loser_rating = store.get_rating(loser_id)
        expected = calculate_expected_score(winner_rating, loser_rating)
        total_expected += expected

    # Update winner
    avg_expected = total_expected / len(loser_ids) if loser_ids else 0.5
    new_winner_rating = calculate_new_rating(
        winner_rating,
        avg_expected,
        1.0  # Winner gets score of 1
    )

    results[winner_id] = {
        'old_rating': winner_rating,
        'new_rating': new_winner_rating,
        'change': new_winner_rating - winner_rating
    }
    store.set_rating(winner_id, new_winner_rating)

    # Update each loser
    for loser_id in loser_ids:
        loser_rating = store.get_rating(loser_id)
        expected = calculate_expected_score(loser_rating, winner_rating)

        new_loser_rating = calculate_new_rating(
            loser_rating,
            expected,
            0.0  # Loser gets score of 0
        )

        results[loser_id] = {
            'old_rating': loser_rating,
            'new_rating': new_loser_rating,
            'change': new_loser_rating - loser_rating
        }
        store.set_rating(loser_id, new_loser_rating)

    # Record history
    store.add_history_entry({
        'timestamp': datetime.utcnow().isoformat(),
        'conversation_id': conversation_id,
        'winner': winner_id,
        'losers': loser_ids,
        'models': [winner_id] + loser_ids,
        'results': results
    })

    return results


def update_elo_from_rankings(
    rankings: List[Tuple[str, int]],
    conversation_id: str = None
) -> Dict[str, Dict[str, float]]:
    """
    Update Elo ratings based on full rankings.

    Each model is compared pairwise with models ranked below them.

    Args:
        rankings: List of (model_id, rank) tuples, sorted by rank (1 = best)
        conversation_id: Optional conversation ID

    Returns:
        Dict mapping model_id to rating changes
    """
    store = get_elo_store()

    # Sort by rank
    sorted_rankings = sorted(rankings, key=lambda x: x[1])
    results = {}

    # Initialize results with current ratings
    for model_id, _ in sorted_rankings:
        current = store.get_rating(model_id)
        results[model_id] = {
            'old_rating': current,
            'new_rating': current,
            'change': 0
        }

    # Compare each pair
    for i, (model_a, rank_a) in enumerate(sorted_rankings):
        for j, (model_b, rank_b) in enumerate(sorted_rankings[i + 1:], i + 1):
            # model_a ranked higher (better) than model_b
            rating_a = results[model_a]['new_rating']
            rating_b = results[model_b]['new_rating']

            expected_a = calculate_expected_score(rating_a, rating_b)
            expected_b = calculate_expected_score(rating_b, rating_a)

            # model_a wins (score = 1), model_b loses (score = 0)
            # Use smaller k-factor for pairwise comparisons
            k = K_FACTOR / len(sorted_rankings)

            new_rating_a = calculate_new_rating(rating_a, expected_a, 1.0, k)
            new_rating_b = calculate_new_rating(rating_b, expected_b, 0.0, k)

            results[model_a]['new_rating'] = new_rating_a
            results[model_b]['new_rating'] = new_rating_b

    # Calculate final changes and save
    for model_id in results:
        results[model_id]['change'] = (
            results[model_id]['new_rating'] - results[model_id]['old_rating']
        )
        store.set_rating(model_id, results[model_id]['new_rating'])

    # Record history
    store.add_history_entry({
        'timestamp': datetime.utcnow().isoformat(),
        'conversation_id': conversation_id,
        'rankings': rankings,
        'models': [m for m, _ in rankings],
        'results': results
    })

    return results


def get_model_elo(model_id: str) -> Dict[str, Any]:
    """
    Get Elo rating and stats for a model.

    Args:
        model_id: The model ID

    Returns:
        Dict with rating and statistics
    """
    store = get_elo_store()

    rating = store.get_rating(model_id)
    history = store.get_history(model_id, limit=100)

    # Calculate stats from history
    wins = 0
    losses = 0
    total_matches = 0

    for entry in history:
        if 'winner' in entry:
            total_matches += 1
            if entry['winner'] == model_id:
                wins += 1
            elif model_id in entry.get('losers', []):
                losses += 1
        elif 'rankings' in entry:
            # Count pairwise wins/losses from rankings
            rankings = dict(entry['rankings'])
            if model_id in rankings:
                rank = rankings[model_id]
                for other_id, other_rank in rankings.items():
                    if other_id != model_id:
                        if rank < other_rank:
                            wins += 1
                        elif rank > other_rank:
                            losses += 1

    win_rate = wins / (wins + losses) if (wins + losses) > 0 else 0

    return {
        'model_id': model_id,
        'rating': rating,
        'wins': wins,
        'losses': losses,
        'total_matches': total_matches,
        'win_rate': win_rate,
        'rating_history': [
            {
                'timestamp': h['timestamp'],
                'rating': h['results'].get(model_id, {}).get('new_rating')
            }
            for h in history
            if model_id in h.get('results', {})
        ][-20:]  # Last 20 rating changes
    }


def get_elo_leaderboard(limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get the Elo leaderboard.

    Args:
        limit: Maximum number of entries

    Returns:
        Sorted list of model ratings
    """
    store = get_elo_store()
    ratings = store.get_all_ratings()

    leaderboard = []
    for model_id, rating in ratings.items():
        stats = get_model_elo(model_id)
        leaderboard.append({
            'rank': 0,  # Will be set after sorting
            'model_id': model_id,
            'rating': rating,
            'wins': stats['wins'],
            'losses': stats['losses'],
            'win_rate': stats['win_rate']
        })

    # Sort by rating
    leaderboard.sort(key=lambda x: x['rating'], reverse=True)

    # Set ranks
    for i, entry in enumerate(leaderboard[:limit]):
        entry['rank'] = i + 1

    return leaderboard[:limit]


def get_head_to_head(model_a: str, model_b: str) -> Dict[str, Any]:
    """
    Get head-to-head statistics between two models.

    Args:
        model_a: First model ID
        model_b: Second model ID

    Returns:
        Head-to-head stats
    """
    store = get_elo_store()
    history = store.get_history(limit=1000)

    a_wins = 0
    b_wins = 0
    total = 0

    for entry in history:
        if model_a in entry.get('models', []) and model_b in entry.get('models', []):
            if 'winner' in entry:
                total += 1
                if entry['winner'] == model_a:
                    a_wins += 1
                elif entry['winner'] == model_b:
                    b_wins += 1
            elif 'rankings' in entry:
                rankings = dict(entry['rankings'])
                if model_a in rankings and model_b in rankings:
                    total += 1
                    if rankings[model_a] < rankings[model_b]:
                        a_wins += 1
                    elif rankings[model_b] < rankings[model_a]:
                        b_wins += 1

    rating_a = store.get_rating(model_a)
    rating_b = store.get_rating(model_b)

    return {
        'model_a': {
            'id': model_a,
            'rating': rating_a,
            'wins': a_wins,
            'win_rate': a_wins / total if total > 0 else 0
        },
        'model_b': {
            'id': model_b,
            'rating': rating_b,
            'wins': b_wins,
            'win_rate': b_wins / total if total > 0 else 0
        },
        'total_matches': total,
        'expected_a': calculate_expected_score(rating_a, rating_b),
        'expected_b': calculate_expected_score(rating_b, rating_a)
    }
