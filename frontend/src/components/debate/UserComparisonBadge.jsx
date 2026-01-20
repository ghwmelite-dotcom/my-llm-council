import './UserComparisonBadge.css';

export default function UserComparisonBadge({ userRank, totalParticipants, averageRank }) {
  if (!userRank) {
    return null;
  }

  const getPositionEmoji = (rank) => {
    if (rank === 1) return '🥇';
    if (rank === 2) return '🥈';
    if (rank === 3) return '🥉';
    return '🏅';
  };

  const getPositionClass = (rank, total) => {
    const percentile = ((total - rank) / (total - 1)) * 100;
    if (rank === 1) return 'gold';
    if (rank === 2) return 'silver';
    if (rank === 3) return 'bronze';
    if (percentile >= 50) return 'good';
    return 'needs-improvement';
  };

  const getMessage = (rank, total) => {
    if (rank === 1) return "You're the council's top pick!";
    if (rank === 2) return 'Runner-up! Great job!';
    if (rank === 3) return 'Third place - well done!';
    if (rank <= Math.ceil(total / 2)) return 'Upper half - nice work!';
    return 'Keep refining your answers!';
  };

  const positionClass = getPositionClass(userRank, totalParticipants);

  return (
    <div className={`user-comparison-badge ${positionClass}`}>
      <div className="badge-icon">
        <span className="position-emoji">{getPositionEmoji(userRank)}</span>
      </div>

      <div className="badge-content">
        <div className="badge-title">Your Ranking</div>
        <div className="badge-rank">
          <span className="rank-number">#{userRank}</span>
          <span className="rank-total">of {totalParticipants}</span>
        </div>
        <div className="badge-message">{getMessage(userRank, totalParticipants)}</div>
      </div>

      <div className="badge-stats">
        <div className="stat-item">
          <span className="stat-label">Avg. Rank</span>
          <span className="stat-value">{averageRank?.toFixed(2) || '—'}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Percentile</span>
          <span className="stat-value">
            {Math.round(((totalParticipants - userRank) / (totalParticipants - 1)) * 100)}%
          </span>
        </div>
      </div>
    </div>
  );
}
