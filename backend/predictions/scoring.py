"""Prediction scoring system."""

from typing import Dict, Any


def calculate_confidence_bonus(confidence: float, correct: bool) -> float:
    """
    Calculate bonus/penalty based on confidence level.

    Higher confidence = higher reward if correct, higher penalty if wrong.

    Args:
        confidence: The confidence level (0-1)
        correct: Whether the prediction was correct

    Returns:
        Bonus multiplier
    """
    if correct:
        # Higher confidence = bigger bonus (1.0 to 2.0 multiplier)
        return 1.0 + confidence
    else:
        # Higher confidence = bigger penalty (0.5 to 0.0 multiplier)
        return 0.5 * (1 - confidence)


def score_prediction(confidence: float, correct: bool) -> float:
    """
    Calculate points earned for a prediction.

    Args:
        confidence: The confidence level (0-1)
        correct: Whether the prediction was correct

    Returns:
        Points earned (positive or negative)
    """
    base_points = 10.0  # Base points for any prediction

    if correct:
        # Correct prediction: base points * confidence bonus
        bonus = calculate_confidence_bonus(confidence, True)
        return base_points * bonus
    else:
        # Incorrect prediction: negative points scaled by confidence
        # High confidence wrong = bigger penalty
        penalty = confidence * 5.0  # Up to -5 points
        return -penalty


def calculate_brier_score(confidence: float, correct: bool) -> float:
    """
    Calculate Brier score for prediction calibration.

    Brier score measures the accuracy of probabilistic predictions.
    Lower is better (0 = perfect, 1 = worst).

    Args:
        confidence: The confidence level (0-1)
        correct: Whether the prediction was correct

    Returns:
        Brier score (0-1)
    """
    outcome = 1.0 if correct else 0.0
    return (confidence - outcome) ** 2


def evaluate_calibration(predictions: list) -> Dict[str, Any]:
    """
    Evaluate the calibration of a set of predictions.

    Args:
        predictions: List of (confidence, correct) tuples

    Returns:
        Calibration metrics
    """
    if not predictions:
        return {
            'count': 0,
            'mean_brier': 0,
            'calibration_error': 0
        }

    # Calculate mean Brier score
    brier_scores = [
        calculate_brier_score(conf, correct)
        for conf, correct in predictions
    ]
    mean_brier = sum(brier_scores) / len(brier_scores)

    # Calculate calibration error
    # Group predictions by confidence buckets
    buckets = {}
    for conf, correct in predictions:
        bucket = round(conf * 10) / 10  # 0.1 buckets
        if bucket not in buckets:
            buckets[bucket] = {'count': 0, 'correct': 0}
        buckets[bucket]['count'] += 1
        if correct:
            buckets[bucket]['correct'] += 1

    # Calculate expected vs actual accuracy per bucket
    calibration_errors = []
    for bucket, data in buckets.items():
        if data['count'] > 0:
            expected = bucket
            actual = data['correct'] / data['count']
            calibration_errors.append(abs(expected - actual))

    calibration_error = sum(calibration_errors) / len(calibration_errors) if calibration_errors else 0

    return {
        'count': len(predictions),
        'mean_brier': mean_brier,
        'calibration_error': calibration_error,
        'buckets': buckets
    }


def calculate_streak_bonus(streak_length: int) -> float:
    """
    Calculate bonus for consecutive correct predictions.

    Args:
        streak_length: Number of consecutive correct predictions

    Returns:
        Bonus points
    """
    if streak_length < 3:
        return 0
    elif streak_length < 5:
        return 5.0  # Small streak bonus
    elif streak_length < 10:
        return 15.0  # Medium streak bonus
    else:
        return 30.0  # Large streak bonus


def rank_predictors(user_stats: Dict[str, Dict]) -> list:
    """
    Rank users by their prediction performance.

    Args:
        user_stats: Dict mapping user_id to stats

    Returns:
        Sorted list of (user_id, score) tuples
    """
    scores = []

    for user_id, stats in user_stats.items():
        # Score based on accuracy and volume
        if stats['resolved_predictions'] < 5:
            # Not enough data
            continue

        accuracy = stats['accuracy']
        volume = stats['resolved_predictions']
        points = stats['total_points']

        # Combined score: weighted combination
        # Higher accuracy and volume = better
        score = (accuracy * 50) + (min(volume, 50) * 0.5) + (points * 0.1)
        scores.append((user_id, score, stats))

    scores.sort(key=lambda x: x[1], reverse=True)
    return scores
