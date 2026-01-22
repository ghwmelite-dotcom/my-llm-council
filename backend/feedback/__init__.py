"""Feedback module for collecting user ratings."""

from .storage import FeedbackStorage, Feedback, get_feedback_storage

__all__ = ['FeedbackStorage', 'Feedback', 'get_feedback_storage']
