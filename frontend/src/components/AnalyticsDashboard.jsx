import { useState, useEffect } from 'react';
import './AnalyticsDashboard.css';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8001';

export default function AnalyticsDashboard({ isOpen, onClose }) {
  const [summary, setSummary] = useState(null);
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen) {
      loadAnalytics();
    }
  }, [isOpen]);

  const loadAnalytics = async () => {
    setLoading(true);
    setError(null);
    try {
      const [summaryRes, modelsRes] = await Promise.all([
        fetch(`${API_BASE}/api/analytics/summary`),
        fetch(`${API_BASE}/api/analytics/models`),
      ]);

      if (summaryRes.ok) {
        setSummary(await summaryRes.json());
      }
      if (modelsRes.ok) {
        const data = await modelsRes.json();
        setModels(data.models || []);
      }
    } catch (err) {
      setError('Failed to load analytics');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="analytics-overlay" onClick={onClose}>
      <div className="analytics-dashboard" onClick={(e) => e.stopPropagation()}>
        <div className="dashboard-header">
          <h2>Model Analytics</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        {loading ? (
          <div className="loading-state">Loading analytics...</div>
        ) : error ? (
          <div className="error-state">{error}</div>
        ) : (
          <div className="dashboard-content">
            {/* Summary Cards */}
            <div className="summary-cards">
              <div className="summary-card">
                <div className="card-label">Total Queries</div>
                <div className="card-value">{summary?.total_queries || 0}</div>
              </div>
              <div className="summary-card">
                <div className="card-label">Total Cost</div>
                <div className="card-value">${(summary?.total_cost || 0).toFixed(2)}</div>
              </div>
              <div className="summary-card">
                <div className="card-label">Total Tokens</div>
                <div className="card-value">{(summary?.total_tokens || 0).toLocaleString()}</div>
              </div>
              <div className="summary-card">
                <div className="card-label">Cache Hit Rate</div>
                <div className="card-value">{(summary?.cache_hit_rate || 0).toFixed(1)}%</div>
              </div>
            </div>

            {/* Tier Distribution */}
            {summary?.tier_distribution && Object.keys(summary.tier_distribution).length > 0 && (
              <div className="section">
                <h3>Query Distribution by Tier</h3>
                <div className="tier-bars">
                  {[1, 2, 3].map((tier) => {
                    const count = summary.tier_distribution[tier] || 0;
                    const total = Object.values(summary.tier_distribution).reduce((a, b) => a + b, 0);
                    const pct = total > 0 ? (count / total) * 100 : 0;
                    return (
                      <div key={tier} className="tier-bar">
                        <div className="tier-label">
                          {tier === 1 ? 'Fast Mode' : tier === 2 ? 'Mini Council' : 'Full Council'}
                        </div>
                        <div className="bar-container">
                          <div
                            className={`bar tier-${tier}`}
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                        <div className="tier-count">{count} ({pct.toFixed(0)}%)</div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Model Leaderboard */}
            <div className="section">
              <h3>Model Performance</h3>
              {models.length === 0 ? (
                <div className="empty-state">No data yet. Run some queries to see analytics.</div>
              ) : (
                <div className="model-table">
                  <div className="table-header">
                    <span className="col-rank">#</span>
                    <span className="col-model">Model</span>
                    <span className="col-stat">Win Rate</span>
                    <span className="col-stat">Avg Rank</span>
                    <span className="col-stat">Queries</span>
                    <span className="col-stat">Cost</span>
                  </div>
                  {models.map((model, idx) => (
                    <div key={model.model} className="table-row">
                      <span className="col-rank">
                        {idx === 0 ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : idx + 1}
                      </span>
                      <span className="col-model">{model.model_name}</span>
                      <span className="col-stat">{model.win_rate}%</span>
                      <span className="col-stat">{model.avg_rank || '—'}</span>
                      <span className="col-stat">{model.total_queries}</span>
                      <span className="col-stat">${model.total_cost.toFixed(2)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Recent Queries */}
            {summary?.recent_queries && summary.recent_queries.length > 0 && (
              <div className="section">
                <h3>Recent Queries</h3>
                <div className="recent-queries">
                  {summary.recent_queries.slice(-10).reverse().map((q, idx) => (
                    <div key={idx} className="query-row">
                      <span className={`tier-badge tier-${q.tier}`}>
                        {q.tier === 1 ? 'Fast' : q.tier === 2 ? 'Mini' : 'Full'}
                      </span>
                      <span className="query-models">{q.models_used.length} models</span>
                      <span className="query-tokens">{q.total_tokens.toLocaleString()} tokens</span>
                      <span className="query-cost">${q.total_cost.toFixed(4)}</span>
                      <span className="query-time">{Math.round(q.duration_ms)}ms</span>
                      {q.cache_hit && <span className="cache-badge">Cached</span>}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
