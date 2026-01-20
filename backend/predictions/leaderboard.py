"""Leaderboard generation for council predictions."""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from .elo import get_elo_leaderboard, get_model_elo, get_elo_store
from .betting import get_prediction_store, get_user_prediction_stats
from .scoring import evaluate_calibration, rank_predictors


def get_leaderboard(
    leaderboard_type: str = 'elo',
    limit: int = 20,
    time_period: str = 'all'
) -> Dict[str, Any]:
    """
    Get leaderboard data.

    Args:
        leaderboard_type: Type of leaderboard ('elo', 'user_predictions', 'combined')
        limit: Maximum entries to return
        time_period: Time period filter ('day', 'week', 'month', 'all')

    Returns:
        Leaderboard data with entries and metadata
    """
    if leaderboard_type == 'elo':
        return get_model_elo_leaderboard(limit)
    elif leaderboard_type == 'user_predictions':
        return get_user_prediction_leaderboard(limit, time_period)
    elif leaderboard_type == 'combined':
        return get_combined_leaderboard(limit)
    else:
        return {'error': f'Unknown leaderboard type: {leaderboard_type}'}


def get_model_elo_leaderboard(limit: int = 20) -> Dict[str, Any]:
    """
    Get model Elo rating leaderboard.

    Args:
        limit: Maximum entries

    Returns:
        Leaderboard dict
    """
    entries = get_elo_leaderboard(limit)

    return {
        'type': 'elo',
        'title': 'Model Elo Rankings',
        'description': 'Models ranked by their Elo rating from council debates',
        'updated_at': datetime.utcnow().isoformat(),
        'total_entries': len(entries),
        'entries': entries
    }


def get_user_prediction_leaderboard(
    limit: int = 20,
    time_period: str = 'all'
) -> Dict[str, Any]:
    """
    Get user prediction accuracy leaderboard.

    Args:
        limit: Maximum entries
        time_period: Time period filter

    Returns:
        Leaderboard dict
    """
    store = get_prediction_store()

    # Calculate cutoff time
    cutoff = None
    if time_period == 'day':
        cutoff = datetime.utcnow() - timedelta(days=1)
    elif time_period == 'week':
        cutoff = datetime.utcnow() - timedelta(weeks=1)
    elif time_period == 'month':
        cutoff = datetime.utcnow() - timedelta(days=30)

    # Get all users with predictions
    user_ids = set()
    for pred in store.predictions.values():
        # Filter by time if needed
        if cutoff:
            pred_time = datetime.fromisoformat(pred.placed_at)
            if pred_time < cutoff:
                continue
        user_ids.add(pred.user_id)

    # Calculate stats for each user
    entries = []
    for user_id in user_ids:
        stats = get_user_prediction_stats(user_id)

        # Skip users with too few predictions
        if stats['resolved_predictions'] < 3:
            continue

        entries.append({
            'user_id': user_id,
            'accuracy': stats['accuracy'],
            'total_predictions': stats['total_predictions'],
            'resolved_predictions': stats['resolved_predictions'],
            'correct_predictions': stats['correct_predictions'],
            'total_points': stats['total_points'],
            'average_confidence': stats['average_confidence']
        })

    # Sort by accuracy, then by total points
    entries.sort(key=lambda x: (x['accuracy'], x['total_points']), reverse=True)

    # Add ranks
    for i, entry in enumerate(entries[:limit]):
        entry['rank'] = i + 1

    return {
        'type': 'user_predictions',
        'title': 'Top Predictors',
        'description': f'Users ranked by prediction accuracy ({time_period})',
        'updated_at': datetime.utcnow().isoformat(),
        'time_period': time_period,
        'total_entries': len(entries),
        'entries': entries[:limit]
    }


def get_combined_leaderboard(limit: int = 20) -> Dict[str, Any]:
    """
    Get combined leaderboard with both models and users.

    Args:
        limit: Maximum entries per category

    Returns:
        Combined leaderboard dict
    """
    model_lb = get_model_elo_leaderboard(limit)
    user_lb = get_user_prediction_leaderboard(limit)

    return {
        'type': 'combined',
        'title': 'Council Leaderboards',
        'updated_at': datetime.utcnow().isoformat(),
        'models': model_lb,
        'users': user_lb
    }


def get_model_stats(model_id: str) -> Dict[str, Any]:
    """
    Get comprehensive statistics for a model.

    Args:
        model_id: The model ID

    Returns:
        Model statistics
    """
    elo_stats = get_model_elo(model_id)
    store = get_prediction_store()

    # Count predictions involving this model
    predictions_for = []
    predictions_against = []

    for pred in store.predictions.values():
        if pred.predicted_winner == model_id:
            predictions_for.append(pred)
        elif pred.resolved and pred.actual_winner == model_id:
            # Someone predicted against this model but it won
            predictions_against.append(pred)

    # Calculate prediction stats
    correct_predictions_for = len([p for p in predictions_for if p.correct])
    total_predictions_for = len([p for p in predictions_for if p.resolved])

    return {
        'model_id': model_id,
        'elo': {
            'rating': elo_stats['rating'],
            'wins': elo_stats['wins'],
            'losses': elo_stats['losses'],
            'win_rate': elo_stats['win_rate'],
            'total_matches': elo_stats['total_matches']
        },
        'predictions': {
            'times_predicted_to_win': len(predictions_for),
            'times_actually_won': len([p for p in predictions_for if p.correct]),
            'prediction_accuracy': (
                correct_predictions_for / total_predictions_for
                if total_predictions_for > 0 else 0
            )
        },
        'rating_history': elo_stats['rating_history']
    }


def get_model_comparison(model_ids: List[str]) -> Dict[str, Any]:
    """
    Compare multiple models side by side.

    Args:
        model_ids: List of model IDs to compare

    Returns:
        Comparison data
    """
    models = []
    for model_id in model_ids:
        stats = get_model_stats(model_id)
        models.append(stats)

    # Sort by Elo rating
    models.sort(key=lambda x: x['elo']['rating'], reverse=True)

    return {
        'models': models,
        'generated_at': datetime.utcnow().isoformat()
    }


def get_trending_models(period_days: int = 7, limit: int = 5) -> Dict[str, Any]:
    """
    Get models with biggest Elo changes recently.

    Args:
        period_days: Number of days to consider
        limit: Maximum entries

    Returns:
        Trending models data
    """
    store = get_elo_store()
    cutoff = datetime.utcnow() - timedelta(days=period_days)

    # Get recent history
    history = store.get_history(limit=500)

    # Calculate rating changes per model
    changes = {}
    for entry in history:
        entry_time = datetime.fromisoformat(entry['timestamp'])
        if entry_time < cutoff:
            continue

        for model_id, result in entry.get('results', {}).items():
            if model_id not in changes:
                changes[model_id] = 0
            changes[model_id] += result.get('change', 0)

    # Sort by absolute change
    trending = [
        {
            'model_id': model_id,
            'rating_change': change,
            'current_rating': store.get_rating(model_id),
            'trending': 'up' if change > 0 else 'down'
        }
        for model_id, change in changes.items()
    ]

    # Sort by absolute change magnitude
    trending.sort(key=lambda x: abs(x['rating_change']), reverse=True)

    return {
        'title': f'Trending Models (Last {period_days} Days)',
        'period_days': period_days,
        'generated_at': datetime.utcnow().isoformat(),
        'models': trending[:limit]
    }


def get_prediction_market_summary() -> Dict[str, Any]:
    """
    Get overall prediction market summary.

    Returns:
        Market summary statistics
    """
    store = get_prediction_store()
    elo_store = get_elo_store()

    all_predictions = list(store.predictions.values())
    resolved = [p for p in all_predictions if p.resolved]
    correct = [p for p in resolved if p.correct]

    # Calibration analysis
    calibration_data = [
        (p.confidence, p.correct)
        for p in resolved
    ]
    calibration = evaluate_calibration(calibration_data)

    # Most predicted models
    prediction_counts = {}
    for pred in all_predictions:
        model = pred.predicted_winner
        if model not in prediction_counts:
            prediction_counts[model] = 0
        prediction_counts[model] += 1

    most_predicted = sorted(
        prediction_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]

    return {
        'total_predictions': len(all_predictions),
        'resolved_predictions': len(resolved),
        'pending_predictions': len(all_predictions) - len(resolved),
        'overall_accuracy': len(correct) / len(resolved) if resolved else 0,
        'total_points_distributed': sum(p.points_earned for p in resolved),
        'calibration': {
            'mean_brier_score': calibration['mean_brier'],
            'calibration_error': calibration['calibration_error']
        },
        'most_predicted_models': [
            {'model_id': m, 'count': c}
            for m, c in most_predicted
        ],
        'total_models_tracked': len(elo_store.get_all_ratings()),
        'generated_at': datetime.utcnow().isoformat()
    }
