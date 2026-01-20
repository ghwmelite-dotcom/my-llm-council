import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import './DevilsAdvocate.css';

export default function DevilsAdvocate({ challenge }) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!challenge) {
    return null;
  }

  const getModelShortName = (modelId) => {
    return modelId?.split('/').pop() || modelId;
  };

  return (
    <div className="devils-advocate">
      <button
        className={`devils-advocate-toggle ${isExpanded ? 'expanded' : ''}`}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <span className="devils-icon">😈</span>
        <div className="devils-header-content">
          <span className="devils-title">Devil's Advocate Challenge</span>
          <span className="devils-subtitle">
            Challenging {getModelShortName(challenge.target_model)}'s top-ranked response
          </span>
        </div>
        <span className="devils-toggle-icon">{isExpanded ? '▼' : '▶'}</span>
      </button>

      {isExpanded && (
        <div className="devils-advocate-content">
          <div className="challenge-header">
            <span className="challenger-model">
              Challenger: {getModelShortName(challenge.model)}
            </span>
            <span className="target-model">
              Target: {getModelShortName(challenge.target_model)}
            </span>
          </div>

          <div className="challenge-body">
            <div className="markdown-content">
              <ReactMarkdown>{challenge.challenge}</ReactMarkdown>
            </div>
          </div>

          <div className="challenge-footer">
            <div className="challenge-note">
              This challenge was considered by the Chairman when synthesizing the final answer.
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
