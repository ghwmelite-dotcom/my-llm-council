import React, { useState, useEffect } from 'react';
import './ConstitutionViewer.css';

const ConstitutionViewer = ({ onAmendmentClick }) => {
  const [constitution, setConstitution] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedArticle, setExpandedArticle] = useState(null);

  useEffect(() => {
    fetchConstitution();
  }, []);

  const fetchConstitution = async () => {
    try {
      const response = await fetch('/api/constitution');
      if (!response.ok) throw new Error('Failed to fetch constitution');
      const data = await response.json();
      setConstitution(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getPriorityBadge = (priority) => {
    const badges = {
      critical: { label: 'Critical', className: 'critical' },
      high: { label: 'High', className: 'high' },
      medium: { label: 'Medium', className: 'medium' },
      low: { label: 'Low', className: 'low' }
    };
    return badges[priority] || badges.medium;
  };

  const getEnforcementIcon = (enforcement) => {
    const icons = {
      strict: '⚖️',
      mandatory: '📋',
      advisory: '💡'
    };
    return icons[enforcement] || '📋';
  };

  if (loading) {
    return (
      <div className="constitution-viewer loading">
        <div className="constitution-header">
          <h2>Council Constitution</h2>
        </div>
        <div className="loading-indicator">Loading constitution...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="constitution-viewer error">
        <div className="constitution-header">
          <h2>Council Constitution</h2>
        </div>
        <div className="error-message">{error}</div>
        <button onClick={fetchConstitution}>Retry</button>
      </div>
    );
  }

  return (
    <div className="constitution-viewer">
      <div className="constitution-header">
        <div className="header-content">
          <span className="constitution-icon">📜</span>
          <div>
            <h2>{constitution?.name || 'Council Constitution'}</h2>
            <span className="version">Version {constitution?.version || '1.0'}</span>
          </div>
        </div>
        {onAmendmentClick && (
          <button className="propose-btn" onClick={onAmendmentClick}>
            Propose Amendment
          </button>
        )}
      </div>

      {constitution?.preamble && (
        <div className="preamble">
          <h3>Preamble</h3>
          <p>{constitution.preamble}</p>
        </div>
      )}

      <div className="articles-section">
        <h3>Articles ({constitution?.articles?.length || 0})</h3>

        <div className="articles-list">
          {constitution?.articles?.map((article) => {
            const priority = getPriorityBadge(article.priority);
            const isExpanded = expandedArticle === article.id;

            return (
              <div
                key={article.id}
                className={`article-card ${isExpanded ? 'expanded' : ''}`}
              >
                <div
                  className="article-header"
                  onClick={() => setExpandedArticle(isExpanded ? null : article.id)}
                >
                  <div className="article-title">
                    <span className="article-number">Article {article.number}</span>
                    <h4>{article.title}</h4>
                  </div>
                  <div className="article-badges">
                    <span className={`priority-badge ${priority.className}`}>
                      {priority.label}
                    </span>
                    <span className="enforcement-badge" title={`${article.enforcement} enforcement`}>
                      {getEnforcementIcon(article.enforcement)}
                    </span>
                    <span className="expand-icon">{isExpanded ? '▼' : '▶'}</span>
                  </div>
                </div>

                {isExpanded && (
                  <div className="article-content">
                    <p>{article.text}</p>
                    <div className="article-meta">
                      <span>Enforcement: {article.enforcement}</span>
                      {article.custom && <span className="custom-tag">Custom Article</span>}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      <div className="constitution-footer">
        <div className="meta-info">
          {constitution?.ratified_at && (
            <span>Ratified: {new Date(constitution.ratified_at).toLocaleDateString()}</span>
          )}
          {constitution?.amendment_count > 0 && (
            <span>Amendments: {constitution.amendment_count}</span>
          )}
        </div>
        <button className="refresh-btn" onClick={fetchConstitution}>
          Refresh
        </button>
      </div>
    </div>
  );
};

export default ConstitutionViewer;
