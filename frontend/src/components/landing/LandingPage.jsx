import React from 'react';
import './LandingPage.css';

const LandingPage = ({ onEnterCouncil }) => {
  return (
    <div className="landing-page">
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
