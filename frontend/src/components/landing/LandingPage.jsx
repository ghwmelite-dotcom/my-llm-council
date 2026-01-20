import React from 'react';
import './LandingPage.css';

const models = [
  { name: 'GPT-5.1', color: '#10a37f' },
  { name: 'Gemini', color: '#4285f4' },
  { name: 'Claude', color: '#d4a574' },
  { name: 'Grok', color: '#ff6b35' },
];

const LandingPage = ({ onEnterCouncil }) => {
  return (
    <div className="landing-page">
      {/* Model badges arranged in a circle */}
      <div className="model-badges">
        {models.map((model, index) => (
          <div
            key={model.name}
            className={`model-badge badge-${index}`}
            style={{ '--model-color': model.color }}
          >
            <span className="badge-glow" />
            <span className="badge-name">{model.name}</span>
          </div>
        ))}
      </div>

      <div className="landing-content">
        <h1 className="landing-title">
          <span className="title-icon">◈</span>
          LLM Council
        </h1>
        <p className="landing-tagline">
          Four frontier models. Anonymous peer review. One synthesized answer.
        </p>
        <button className="enter-button" onClick={onEnterCouncil}>
          Enter Council
        </button>
      </div>
    </div>
  );
};

export default LandingPage;
