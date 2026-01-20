import React, { useState, useEffect } from 'react';
import './Observer.css';

const Observer = ({ conversationId, autoAnalyze = false }) => {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    if (conversationId && autoAnalyze) {
      runAnalysis();
    }
  }, [conversationId, autoAnalyze]);

  const runAnalysis = async () => {
    if (!conversationId) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/observer/report/${conversationId}?format=full`);
      if (!response.ok) throw new Error('Failed to generate report');
      const data = await response.json();
      setReport(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityIcon = (severity) => {
    const icons = {
      error: '🔴',
      warning: '🟡',
      positive: '🟢',
      info: 'ℹ️'
    };
    return icons[severity] || icons.info;
  };

  const getHealthColor = (level) => {
    const colors = {
      healthy: '#00ff88',
      moderate: '#ffbb00',
      concerning: '#ff4444'
    };
    return colors[level] || colors.moderate;
  };

  if (!conversationId) {
    return null;
  }

  if (loading) {
    return (
      <div className="observer-panel loading">
        <div className="observer-header">
          <span className="observer-icon">🔬</span>
          <h3>Observer Analysis</h3>
        </div>
        <div className="loading-indicator">
          <div className="spinner" />
          Analyzing deliberation...
        </div>
      </div>
    );
  }

  if (!report && !error) {
    return (
      <div className="observer-panel ready">
        <div className="observer-header">
          <span className="observer-icon">🔬</span>
          <h3>Observer</h3>
        </div>
        <p className="observer-intro">
          Run cognitive analysis to detect biases and evaluate deliberation quality.
        </p>
        <button className="analyze-btn" onClick={runAnalysis}>
          Analyze Deliberation
        </button>
      </div>
    );
  }

  if (error) {
    return (
      <div className="observer-panel error">
        <div className="observer-header">
          <span className="observer-icon">🔬</span>
          <h3>Observer</h3>
        </div>
        <div className="error-message">{error}</div>
        <button className="retry-btn" onClick={runAnalysis}>Retry</button>
      </div>
    );
  }

  const health = report.health || {};
  const observations = report.observations || [];
  const analysis = report.analysis || {};

  return (
    <div className={`observer-panel ${expanded ? 'expanded' : ''}`}>
      <div className="observer-header" onClick={() => setExpanded(!expanded)}>
        <div className="header-left">
          <span className="observer-icon">🔬</span>
          <h3>Observer Analysis</h3>
        </div>
        <div className="header-right">
          <span
            className="health-score"
            style={{ color: getHealthColor(health.health_level) }}
          >
            {health.icon} {(health.score * 100).toFixed(0)}%
          </span>
          <span className="expand-icon">{expanded ? '▼' : '▶'}</span>
        </div>
      </div>

      <div className="health-summary">
        <div
          className="health-bar"
          style={{
            background: `linear-gradient(90deg, ${getHealthColor(health.health_level)} ${health.score * 100}%, #333 ${health.score * 100}%)`
          }}
        />
        <p className="health-message">{health.message}</p>
      </div>

      {expanded && (
        <div className="observer-details">
          {/* Observations Section */}
          <div className="observations-section">
            <h4>Observations ({observations.length})</h4>
            <div className="observations-list">
              {observations.map((obs, index) => (
                <div key={index} className={`observation-card ${obs.severity}`}>
                  <div className="observation-header">
                    <span className="obs-icon">{obs.icon}</span>
                    <span className="obs-title">{obs.title}</span>
                    <span className="obs-severity">{getSeverityIcon(obs.severity)}</span>
                  </div>
                  <p className="obs-description">{obs.description}</p>
                  {obs.indicators && obs.indicators.length > 0 && (
                    <ul className="obs-indicators">
                      {obs.indicators.map((ind, i) => (
                        <li key={i}>{ind}</li>
                      ))}
                    </ul>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Metrics Section */}
          <div className="metrics-section">
            <h4>Quality Metrics</h4>
            <div className="metrics-grid">
              <div className="metric-card">
                <span className="metric-label">Diversity</span>
                <span className="metric-value">
                  {((analysis.diversity?.diversity_score || 0) * 100).toFixed(0)}%
                </span>
                <div className="metric-bar">
                  <div
                    className="metric-fill"
                    style={{ width: `${(analysis.diversity?.diversity_score || 0) * 100}%` }}
                  />
                </div>
              </div>

              <div className="metric-card">
                <span className="metric-label">Ranking Quality</span>
                <span className="metric-value">
                  {((analysis.ranking_quality?.quality_score || 0) * 100).toFixed(0)}%
                </span>
                <div className="metric-bar">
                  <div
                    className="metric-fill"
                    style={{ width: `${(analysis.ranking_quality?.quality_score || 0) * 100}%` }}
                  />
                </div>
              </div>

              {analysis.synthesis_completeness && (
                <div className="metric-card">
                  <span className="metric-label">Synthesis</span>
                  <span className="metric-value">
                    {((analysis.synthesis_completeness?.completeness_score || 0) * 100).toFixed(0)}%
                  </span>
                  <div className="metric-bar">
                    <div
                      className="metric-fill"
                      style={{ width: `${(analysis.synthesis_completeness?.completeness_score || 0) * 100}%` }}
                    />
                  </div>
                </div>
              )}

              <div className="metric-card">
                <span className="metric-label">Bias Score</span>
                <span className="metric-value">
                  {((analysis.bias_analysis?.overall_score || 0) * 100).toFixed(0)}%
                </span>
                <div className="metric-bar">
                  <div
                    className="metric-fill bias"
                    style={{ width: `${(analysis.bias_analysis?.overall_score || 0) * 100}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Recommendations Section */}
          {analysis.recommendations && analysis.recommendations.length > 0 && (
            <div className="recommendations-section">
              <h4>Recommendations</h4>
              <ul className="recommendations-list">
                {analysis.recommendations.map((rec, index) => (
                  <li key={index}>{rec}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <div className="observer-footer">
        <button className="refresh-btn" onClick={runAnalysis}>
          Re-analyze
        </button>
        <span className="timestamp">
          {report.generated_at && new Date(report.generated_at).toLocaleTimeString()}
        </span>
      </div>
    </div>
  );
};

export default Observer;
