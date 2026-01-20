import { useState } from 'react';
import './UserResponseForm.css';

export default function UserResponseForm({ onSubmit, disabled }) {
  const [userResponse, setUserResponse] = useState('');
  const [isExpanded, setIsExpanded] = useState(false);

  const handleSubmit = () => {
    if (userResponse.trim()) {
      onSubmit(userResponse.trim());
    }
  };

  const handleClear = () => {
    setUserResponse('');
    setIsExpanded(false);
  };

  if (!isExpanded) {
    return (
      <button
        className="join-council-btn"
        onClick={() => setIsExpanded(true)}
        disabled={disabled}
      >
        <span className="join-icon">🙋</span>
        <span className="join-text">Join the Council</span>
        <span className="join-subtitle">Submit your own answer to be ranked</span>
      </button>
    );
  }

  return (
    <div className="user-response-form">
      <div className="form-header">
        <span className="form-title">Your Answer</span>
        <button className="close-btn" onClick={handleClear}>
          ✕
        </button>
      </div>

      <div className="form-body">
        <textarea
          value={userResponse}
          onChange={(e) => setUserResponse(e.target.value)}
          placeholder="Write your answer here. It will be anonymized and ranked alongside AI responses..."
          disabled={disabled}
          rows={6}
          className="user-response-input"
        />

        <div className="form-info">
          <div className="info-icon">ℹ️</div>
          <div className="info-text">
            Your response will be shown as "Response X" during peer review.
            The AI models won't know which response is yours.
          </div>
        </div>
      </div>

      <div className="form-actions">
        <button
          className="cancel-btn"
          onClick={handleClear}
          disabled={disabled}
        >
          Cancel
        </button>
        <button
          className="submit-btn"
          onClick={handleSubmit}
          disabled={disabled || !userResponse.trim()}
        >
          Submit & Compare
        </button>
      </div>
    </div>
  );
}
