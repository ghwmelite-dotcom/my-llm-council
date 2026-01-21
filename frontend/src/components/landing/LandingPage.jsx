import React, { useState, useEffect } from 'react';
import './LandingPage.css';

const models = [
  { name: 'GPT-5.1', color: '#10a37f', role: 'Analytical Precision' },
  { name: 'Gemini', color: '#4285f4', role: 'Creative Synthesis' },
  { name: 'Claude', color: '#d4a574', role: 'Nuanced Reasoning' },
  { name: 'Grok', color: '#ff6b35', role: 'Bold Perspectives' },
];

const stages = [
  {
    number: '01',
    title: 'Independent Responses',
    description: 'Four frontier AI models analyze your question simultaneously, each bringing unique strengths and perspectives.',
    icon: '◇',
  },
  {
    number: '02',
    title: 'Anonymous Peer Review',
    description: 'Models evaluate all responses as "Response A, B, C, D" — eliminating bias and ensuring merit-based ranking.',
    icon: '◈',
  },
  {
    number: '03',
    title: 'Synthesized Consensus',
    description: 'A chairman model weaves the best insights into one authoritative answer, informed by collective wisdom.',
    icon: '◆',
  },
];

const features = [
  {
    title: '3D Council Chamber',
    description: 'Watch deliberations unfold in an immersive visualization',
    icon: '🏛️',
  },
  {
    title: 'Real-time Streaming',
    description: 'See each stage progress live as models think and respond',
    icon: '⚡',
  },
  {
    title: 'Full Transparency',
    description: 'Inspect every response, ranking, and reasoning chain',
    icon: '🔍',
  },
  {
    title: 'Voice Synthesis',
    description: 'Listen as each model presents their perspective aloud',
    icon: '🔊',
  },
];

const LandingPage = ({ onEnterCouncil }) => {
  const [activeStage, setActiveStage] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveStage((prev) => (prev + 1) % 3);
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="landing-page">
      {/* Ambient background effects */}
      <div className="ambient-glow glow-1" />
      <div className="ambient-glow glow-2" />
      <div className="grid-overlay" />

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

      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-content">
          <div className="hero-badge">Multi-Model Deliberation Platform</div>
          <h1 className="hero-title">
            <span className="title-icon">◈</span>
            LLM Council
          </h1>
          <p className="hero-tagline">
            Four frontier models. Anonymous peer review. One synthesized answer.
          </p>
          <p className="hero-description">
            Harness the collective intelligence of GPT-5.1, Gemini, Claude, and Grok
            through a rigorous 3-stage deliberation process that eliminates bias
            and surfaces the best possible response.
          </p>
          <div className="hero-actions">
            <button className="enter-button primary" onClick={onEnterCouncil}>
              Enter the Council
              <span className="button-arrow">→</span>
            </button>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="stages-section">
        <div className="section-header">
          <h2 className="section-title">The Deliberation Process</h2>
          <p className="section-subtitle">
            A revolutionary approach to AI consensus-building
          </p>
        </div>

        <div className="stages-container">
          {stages.map((stage, index) => (
            <div
              key={stage.number}
              className={`stage-card ${activeStage === index ? 'active' : ''}`}
              onMouseEnter={() => setActiveStage(index)}
            >
              <div className="stage-number">{stage.number}</div>
              <div className="stage-icon">{stage.icon}</div>
              <h3 className="stage-title">{stage.title}</h3>
              <p className="stage-description">{stage.description}</p>
              <div className="stage-indicator" />
            </div>
          ))}
        </div>

        <div className="stage-connector">
          <div className={`connector-progress stage-${activeStage}`} />
        </div>
      </section>

      {/* Models Section */}
      <section className="models-section">
        <div className="section-header">
          <h2 className="section-title">The Council Members</h2>
          <p className="section-subtitle">
            Four distinct perspectives, unified through deliberation
          </p>
        </div>

        <div className="models-grid">
          {models.map((model) => (
            <div
              key={model.name}
              className="model-card"
              style={{ '--model-color': model.color }}
            >
              <div className="model-avatar">
                <span className="avatar-glow" />
                <span className="avatar-initial">{model.name[0]}</span>
              </div>
              <h3 className="model-name">{model.name}</h3>
              <p className="model-role">{model.role}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features Section */}
      <section className="features-section">
        <div className="section-header">
          <h2 className="section-title">Experience the Future</h2>
          <p className="section-subtitle">
            Powerful capabilities for deeper understanding
          </p>
        </div>

        <div className="features-grid">
          {features.map((feature) => (
            <div key={feature.title} className="feature-card">
              <span className="feature-icon">{feature.icon}</span>
              <h3 className="feature-title">{feature.title}</h3>
              <p className="feature-description">{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Why Section */}
      <section className="why-section">
        <div className="why-content">
          <h2 className="why-title">Why a Council?</h2>
          <div className="why-points">
            <div className="why-point">
              <span className="why-icon">🎯</span>
              <div>
                <h4>Eliminate Single-Model Bias</h4>
                <p>No single AI has all the answers. Diverse models catch blind spots others miss.</p>
              </div>
            </div>
            <div className="why-point">
              <span className="why-icon">🔒</span>
              <div>
                <h4>Anonymous Evaluation</h4>
                <p>Models can't play favorites when they don't know who wrote each response.</p>
              </div>
            </div>
            <div className="why-point">
              <span className="why-icon">✨</span>
              <div>
                <h4>Synthesized Excellence</h4>
                <p>The final answer combines the best reasoning from all perspectives.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <div className="cta-content">
          <h2 className="cta-title">Ready to Consult the Council?</h2>
          <p className="cta-description">
            Ask any question and witness the power of multi-model deliberation.
          </p>
          <button className="enter-button primary large" onClick={onEnterCouncil}>
            Begin Your Session
            <span className="button-arrow">→</span>
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <p>Powered by OpenRouter API</p>
      </footer>
    </div>
  );
};

export default LandingPage;
