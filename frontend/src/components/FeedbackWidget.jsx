import { useState } from 'react';
import './FeedbackWidget.css';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8001';

export default function FeedbackWidget({ conversationId, messageIndex }) {
  const [rating, setRating] = useState(0);
  const [hoveredRating, setHoveredRating] = useState(0);
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [showComment, setShowComment] = useState(false);
  const [comment, setComment] = useState('');

  const handleSubmit = async (selectedRating) => {
    if (submitting) return;

    setSubmitting(true);
    setRating(selectedRating);

    try {
      const response = await fetch(
        `${API_BASE}/api/conversations/${conversationId}/feedback`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            message_index: messageIndex,
            rating: selectedRating,
            feedback_type: 'overall',
            comment: comment || null,
          }),
        }
      );

      if (response.ok) {
        setSubmitted(true);
      }
    } catch (error) {
      console.error('Failed to submit feedback:', error);
    } finally {
      setSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <div className="feedback-widget submitted">
        <span className="thanks-message">Thanks for your feedback!</span>
        <span className="rating-display">
          {[1, 2, 3, 4, 5].map((star) => (
            <span key={star} className={`star ${star <= rating ? 'filled' : ''}`}>
              ★
            </span>
          ))}
        </span>
      </div>
    );
  }

  return (
    <div className="feedback-widget">
      <span className="feedback-label">Rate this response:</span>
      <div className="star-rating">
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            className={`star-btn ${star <= (hoveredRating || rating) ? 'filled' : ''}`}
            onClick={() => {
              if (!showComment) {
                handleSubmit(star);
              } else {
                setRating(star);
              }
            }}
            onMouseEnter={() => setHoveredRating(star)}
            onMouseLeave={() => setHoveredRating(0)}
            disabled={submitting}
          >
            ★
          </button>
        ))}
      </div>

      {!showComment && (
        <button
          className="add-comment-btn"
          onClick={() => setShowComment(true)}
          title="Add a comment"
        >
          💬
        </button>
      )}

      {showComment && (
        <div className="comment-section">
          <textarea
            className="comment-input"
            placeholder="Add a comment (optional)"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            rows={2}
          />
          <button
            className="submit-btn"
            onClick={() => handleSubmit(rating || 5)}
            disabled={submitting || rating === 0}
          >
            {submitting ? 'Sending...' : 'Submit'}
          </button>
        </div>
      )}
    </div>
  );
}
