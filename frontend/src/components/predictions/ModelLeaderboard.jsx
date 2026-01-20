import React, { useState, useEffect } from 'react';
import './ModelLeaderboard.css';

const ModelLeaderboard = ({ refreshInterval = 30000 }) => {
  const [leaderboard, setLeaderboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [leaderboardType, setLeaderboardType] = useState('elo');

  const fetchLeaderboard = async () => {
    try {
      const response = await fetch(`/api/leaderboard?type=${leaderboardType}&limit=10`);
      if (!response.ok) throw new Error('Failed to fetch leaderboard');
      const data = await response.json();
      setLeaderboard(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLeaderboard();
    const interval = setInterval(fetchLeaderboard, refreshInterval);
    return () => clearInterval(interval);
  }, [leaderboardType, refreshInterval]);

  const getRankEmoji = (rank) => {
    if (rank === 1) return '🥇';
    if (rank === 2) return '🥈';
    if (rank === 3) return '🥉';
    return `#${rank}`;
  };

  const formatRating = (rating) => {
    return Math.round(rating);
  };

  const formatWinRate = (rate) => {
    return `${(rate * 100).toFixed(1)}%`;
  };

  const getModelDisplayName = (modelId) => {
    // Extract the model name from full identifier
    const parts = modelId.split('/');
    return parts[parts.length - 1];
  };

  if (loading) {
    return (
      <div className="model-leaderboard loading">
        <div className="leaderboard-header">
          <h3>Model Rankings</h3>
        </div>
        <div className="loading-indicator">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="model-leaderboard error">
        <div className="leaderboard-header">
          <h3>Model Rankings</h3>
        </div>
        <div className="error-message">{error}</div>
      </div>
    );
  }

  const entries = leaderboard?.entries || [];

  return (
    <div className="model-leaderboard">
      <div className="leaderboard-header">
        <h3>
          <span className="trophy-icon">🏆</span>
          {leaderboard?.title || 'Model Rankings'}
        </h3>
        <div className="leaderboard-tabs">
          <button
            className={leaderboardType === 'elo' ? 'active' : ''}
            onClick={() => setLeaderboardType('elo')}
          >
            Elo
          </button>
          <button
            className={leaderboardType === 'user_predictions' ? 'active' : ''}
            onClick={() => setLeaderboardType('user_predictions')}
          >
            Predictors
          </button>
        </div>
      </div>

      {leaderboard?.description && (
        <p className="leaderboard-description">{leaderboard.description}</p>
      )}

      <div className="leaderboard-table">
        <div className="table-header">
          <span className="col-rank">Rank</span>
          <span className="col-name">{leaderboardType === 'elo' ? 'Model' : 'User'}</span>
          <span className="col-rating">{leaderboardType === 'elo' ? 'Rating' : 'Accuracy'}</span>
          <span className="col-record">W/L</span>
        </div>

        {entries.length === 0 ? (
          <div className="no-data">No rankings yet</div>
        ) : (
          entries.map((entry, index) => (
            <div
              key={entry.model_id || entry.user_id || index}
              className={`table-row ${index < 3 ? `top-${index + 1}` : ''}`}
            >
              <span className="col-rank">
                {getRankEmoji(entry.rank || index + 1)}
              </span>
              <span className="col-name">
                {leaderboardType === 'elo'
                  ? getModelDisplayName(entry.model_id)
                  : entry.user_id}
              </span>
              <span className="col-rating">
                {leaderboardType === 'elo'
                  ? formatRating(entry.rating)
                  : formatWinRate(entry.accuracy)}
              </span>
              <span className="col-record">
                {leaderboardType === 'elo'
                  ? `${entry.wins}/${entry.losses}`
                  : `${entry.correct_predictions}/${entry.resolved_predictions}`}
              </span>
            </div>
          ))
        )}
      </div>

      <div className="leaderboard-footer">
        <span className="update-time">
          Updated: {new Date(leaderboard?.updated_at).toLocaleTimeString()}
        </span>
        <button className="refresh-btn" onClick={fetchLeaderboard}>
          Refresh
        </button>
      </div>
    </div>
  );
};

export default ModelLeaderboard;
