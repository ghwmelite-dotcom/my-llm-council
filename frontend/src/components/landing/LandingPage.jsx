import React, { useState, useEffect, Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Stars } from '@react-three/drei';
import HeroScene from './HeroScene';
import FloatingPanel from './FloatingPanel';
import ParticleField from './ParticleField';
import './LandingPage.css';

const LandingPage = ({ onEnterCouncil }) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [isEntering, setIsEntering] = useState(false);
  const [hoveredModel, setHoveredModel] = useState(null);
  const [stats, setStats] = useState({
    totalDebates: 1247,
    activeModels: 4,
    avgConsensus: 78,
    predictions: 3891
  });
  const [recentDebates, setRecentDebates] = useState([
    { id: 1, topic: "Quantum computing implications", winner: "Claude", time: "2m ago" },
    { id: 2, topic: "Ethical AI development", winner: "GPT-5", time: "15m ago" },
    { id: 3, topic: "Climate solutions analysis", winner: "Gemini", time: "1h ago" },
  ]);
  const [leaderboard, setLeaderboard] = useState([
    { model: "Claude Sonnet", elo: 1847, change: +23 },
    { model: "GPT-5.1", elo: 1823, change: +12 },
    { model: "Gemini Pro", elo: 1801, change: -8 },
    { model: "Grok-4", elo: 1756, change: +5 },
  ]);

  useEffect(() => {
    // Cinematic load sequence
    const timer = setTimeout(() => setIsLoaded(true), 500);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    // Fetch real stats if available
    const fetchStats = async () => {
      try {
        const [leaderboardRes, summaryRes] = await Promise.all([
          fetch('/api/leaderboard?limit=4'),
          fetch('/api/predictions/summary')
        ]);

        if (leaderboardRes.ok) {
          const data = await leaderboardRes.json();
          if (data.entries?.length > 0) {
            setLeaderboard(data.entries.map(e => ({
              model: e.model_id?.split('/').pop() || e.model_id,
              elo: Math.round(e.rating || 1500),
              change: Math.round((e.rating - 1500) / 10) || 0
            })));
          }
        }

        if (summaryRes.ok) {
          const data = await summaryRes.json();
          setStats(prev => ({
            ...prev,
            predictions: data.total_predictions || prev.predictions
          }));
        }
      } catch (e) {
        // Use default stats
      }
    };

    fetchStats();
  }, []);

  const handleEnterCouncil = () => {
    setIsEntering(true);
    setTimeout(() => {
      if (onEnterCouncil) onEnterCouncil();
    }, 1500);
  };

  return (
    <div className={`landing-page ${isLoaded ? 'loaded' : ''} ${isEntering ? 'entering' : ''}`}>
      {/* Cinematic Overlay */}
      <div className="cinematic-bars">
        <div className="bar top" />
        <div className="bar bottom" />
      </div>

      {/* 3D Canvas */}
      <div className="hero-canvas">
        <Canvas
          camera={{ position: [0, 2, 12], fov: 60 }}
          gl={{ antialias: true, alpha: true }}
        >
          <Suspense fallback={null}>
            <ambientLight intensity={0.1} />
            <pointLight position={[0, 0, 0]} intensity={2} color="#00f0ff" />
            <pointLight position={[10, 10, 10]} intensity={0.5} color="#ff00aa" />
            <pointLight position={[-10, -10, -10]} intensity={0.3} color="#8b5cf6" />

            <Stars
              radius={100}
              depth={50}
              count={5000}
              factor={4}
              saturation={0}
              fade
              speed={0.5}
            />

            <ParticleField count={200} />

            <HeroScene
              onModelHover={setHoveredModel}
              isEntering={isEntering}
            />

            <OrbitControls
              enableZoom={false}
              enablePan={false}
              autoRotate
              autoRotateSpeed={0.3}
              maxPolarAngle={Math.PI / 1.8}
              minPolarAngle={Math.PI / 3}
            />
          </Suspense>
        </Canvas>
      </div>

      {/* Scan Lines Overlay */}
      <div className="scan-lines" />

      {/* Vignette */}
      <div className="vignette" />

      {/* Header */}
      <header className="landing-header">
        <div className="logo-container">
          <div className="logo-glow" />
          <h1 className="logo">
            <span className="logo-icon">◈</span>
            LLM COUNCIL
          </h1>
          <span className="logo-tagline">Collective Intelligence Protocol</span>
        </div>

        <nav className="header-nav">
          <a href="#about" className="nav-link">About</a>
          <a href="#models" className="nav-link">Models</a>
          <a href="#constitution" className="nav-link">Constitution</a>
          <button className="nav-cta" onClick={handleEnterCouncil}>
            <span className="cta-text">Enter Council</span>
            <span className="cta-icon">→</span>
          </button>
        </nav>
      </header>

      {/* Main Content */}
      <main className="landing-main">
        {/* Left Panel - Stats */}
        <FloatingPanel
          className="panel-stats"
          title="SYSTEM STATUS"
          delay={0.2}
        >
          <div className="stats-grid">
            <div className="stat-item">
              <span className="stat-value">{stats.totalDebates.toLocaleString()}</span>
              <span className="stat-label">Total Debates</span>
              <div className="stat-bar">
                <div className="stat-fill" style={{ width: '78%' }} />
              </div>
            </div>
            <div className="stat-item">
              <span className="stat-value">{stats.activeModels}</span>
              <span className="stat-label">Active Models</span>
              <div className="stat-indicator online" />
            </div>
            <div className="stat-item">
              <span className="stat-value">{stats.avgConsensus}%</span>
              <span className="stat-label">Avg Consensus</span>
              <div className="stat-ring">
                <svg viewBox="0 0 36 36">
                  <path
                    className="ring-bg"
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  />
                  <path
                    className="ring-fill"
                    strokeDasharray={`${stats.avgConsensus}, 100`}
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  />
                </svg>
              </div>
            </div>
            <div className="stat-item">
              <span className="stat-value">{stats.predictions.toLocaleString()}</span>
              <span className="stat-label">Predictions Made</span>
              <div className="stat-sparkline">
                {[40, 65, 45, 80, 55, 90, 70].map((h, i) => (
                  <div key={i} className="spark" style={{ height: `${h}%` }} />
                ))}
              </div>
            </div>
          </div>
        </FloatingPanel>

        {/* Center - Hero Text & CTA */}
        <div className="hero-center">
          <div className="hero-text">
            <h2 className="hero-title">
              <span className="title-line">Where AI Minds</span>
              <span className="title-line highlight">Converge & Deliberate</span>
            </h2>
            <p className="hero-subtitle">
              Four frontier models. Anonymous peer review.
              <br />One synthesized truth.
            </p>
          </div>

          <button
            className="enter-button"
            onClick={handleEnterCouncil}
            disabled={isEntering}
          >
            <span className="button-bg" />
            <span className="button-glow" />
            <span className="button-content">
              <span className="button-icon">◇</span>
              <span className="button-text">ENTER THE COUNCIL</span>
            </span>
            <span className="button-particles">
              {[...Array(6)].map((_, i) => (
                <span key={i} className="particle" />
              ))}
            </span>
          </button>

          {hoveredModel && (
            <div className="hovered-model-info">
              <span className="model-indicator" />
              <span className="model-name">{hoveredModel}</span>
            </div>
          )}
        </div>

        {/* Right Panel - Leaderboard */}
        <FloatingPanel
          className="panel-leaderboard"
          title="ELO RANKINGS"
          delay={0.4}
        >
          <div className="leaderboard-list">
            {leaderboard.map((entry, index) => (
              <div key={index} className={`leaderboard-item rank-${index + 1}`}>
                <span className="rank">#{index + 1}</span>
                <span className="model-name">{entry.model}</span>
                <span className="elo">{entry.elo}</span>
                <span className={`change ${entry.change >= 0 ? 'up' : 'down'}`}>
                  {entry.change >= 0 ? '↑' : '↓'} {Math.abs(entry.change)}
                </span>
              </div>
            ))}
          </div>
        </FloatingPanel>
      </main>

      {/* Bottom Panel - Recent Activity */}
      <FloatingPanel
        className="panel-activity"
        title="RECENT DELIBERATIONS"
        delay={0.6}
      >
        <div className="activity-feed">
          {recentDebates.map((debate) => (
            <div key={debate.id} className="activity-item">
              <div className="activity-indicator" />
              <div className="activity-content">
                <span className="activity-topic">{debate.topic}</span>
                <span className="activity-meta">
                  Won by <strong>{debate.winner}</strong> · {debate.time}
                </span>
              </div>
              <button className="activity-action">View →</button>
            </div>
          ))}
        </div>
      </FloatingPanel>

      {/* Corner Decorations */}
      <div className="corner-decor top-left">
        <svg viewBox="0 0 100 100">
          <path d="M0 50 L0 0 L50 0" />
          <circle cx="0" cy="0" r="4" />
        </svg>
      </div>
      <div className="corner-decor top-right">
        <svg viewBox="0 0 100 100">
          <path d="M50 0 L100 0 L100 50" />
          <circle cx="100" cy="0" r="4" />
        </svg>
      </div>
      <div className="corner-decor bottom-left">
        <svg viewBox="0 0 100 100">
          <path d="M0 50 L0 100 L50 100" />
          <circle cx="0" cy="100" r="4" />
        </svg>
      </div>
      <div className="corner-decor bottom-right">
        <svg viewBox="0 0 100 100">
          <path d="M50 100 L100 100 L100 50" />
          <circle cx="100" cy="100" r="4" />
        </svg>
      </div>

      {/* Status Bar */}
      <footer className="status-bar">
        <div className="status-item">
          <span className="status-dot online" />
          <span>System Operational</span>
        </div>
        <div className="status-item">
          <span className="status-label">Latency:</span>
          <span className="status-value">23ms</span>
        </div>
        <div className="status-item">
          <span className="status-label">Protocol:</span>
          <span className="status-value">v4.2.1</span>
        </div>
        <div className="status-item">
          <span className="status-label">Nodes:</span>
          <span className="status-value">4 Active</span>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
