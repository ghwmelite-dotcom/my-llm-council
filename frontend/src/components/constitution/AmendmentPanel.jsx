import React, { useState, useEffect } from 'react';
import './AmendmentPanel.css';

const AmendmentPanel = ({ userId = 'anonymous', onClose }) => {
  const [amendments, setAmendments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [mode, setMode] = useState('list'); // 'list' or 'propose'
  const [proposalForm, setProposalForm] = useState({
    type: 'add',
    title: '',
    text: '',
    reason: '',
    targetArticleId: ''
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchAmendments();
  }, []);

  const fetchAmendments = async () => {
    try {
      const response = await fetch('/api/amendments');
      if (!response.ok) throw new Error('Failed to fetch amendments');
      const data = await response.json();
      setAmendments(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleVote = async (amendmentId, vote) => {
    try {
      const response = await fetch(`/api/amendments/${amendmentId}/vote`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          voter_id: userId,
          vote: vote,
          reason: ''
        })
      });

      if (!response.ok) throw new Error('Failed to vote');

      fetchAmendments();
    } catch (err) {
      setError(err.message);
    }
  };

  const handlePropose = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const response = await fetch('/api/amendments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          amendment_type: proposalForm.type,
          reason: proposalForm.reason,
          proposed_by: userId,
          proposed_text: proposalForm.text || null,
          proposed_title: proposalForm.title || null,
          target_article_id: proposalForm.targetArticleId || null,
          voting_days: 7
        })
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to propose amendment');
      }

      setMode('list');
      setProposalForm({ type: 'add', title: '', text: '', reason: '', targetArticleId: '' });
      fetchAmendments();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      pending: { icon: '⏳', label: 'Pending', className: 'pending' },
      voting: { icon: '🗳️', label: 'Voting', className: 'voting' },
      passed: { icon: '✅', label: 'Passed', className: 'passed' },
      rejected: { icon: '❌', label: 'Rejected', className: 'rejected' },
      expired: { icon: '⏰', label: 'Expired', className: 'expired' }
    };
    return badges[status] || badges.pending;
  };

  const getTypeLabel = (type) => {
    const labels = {
      add: 'Add Article',
      modify: 'Modify Article',
      remove: 'Remove Article'
    };
    return labels[type] || type;
  };

  if (mode === 'propose') {
    return (
      <div className="amendment-panel">
        <div className="panel-header">
          <h3>Propose Amendment</h3>
          <button className="close-btn" onClick={() => setMode('list')}>
            Back to List
          </button>
        </div>

        <form onSubmit={handlePropose} className="proposal-form">
          <div className="form-group">
            <label>Amendment Type</label>
            <select
              value={proposalForm.type}
              onChange={(e) => setProposalForm({ ...proposalForm, type: e.target.value })}
            >
              <option value="add">Add New Article</option>
              <option value="modify">Modify Existing Article</option>
              <option value="remove">Remove Article</option>
            </select>
          </div>

          {proposalForm.type === 'add' && (
            <div className="form-group">
              <label>Article Title</label>
              <input
                type="text"
                value={proposalForm.title}
                onChange={(e) => setProposalForm({ ...proposalForm, title: e.target.value })}
                placeholder="e.g., Transparency in Reasoning"
                required
              />
            </div>
          )}

          {(proposalForm.type === 'modify' || proposalForm.type === 'remove') && (
            <div className="form-group">
              <label>Target Article ID</label>
              <input
                type="text"
                value={proposalForm.targetArticleId}
                onChange={(e) => setProposalForm({ ...proposalForm, targetArticleId: e.target.value })}
                placeholder="e.g., truth_accuracy"
                required
              />
            </div>
          )}

          {proposalForm.type !== 'remove' && (
            <div className="form-group">
              <label>Article Text</label>
              <textarea
                value={proposalForm.text}
                onChange={(e) => setProposalForm({ ...proposalForm, text: e.target.value })}
                placeholder="The full text of the article..."
                rows={4}
                required
              />
            </div>
          )}

          <div className="form-group">
            <label>Reason for Amendment</label>
            <textarea
              value={proposalForm.reason}
              onChange={(e) => setProposalForm({ ...proposalForm, reason: e.target.value })}
              placeholder="Why is this amendment needed?"
              rows={3}
              required
            />
          </div>

          {error && <div className="form-error">{error}</div>}

          <div className="form-actions">
            <button type="button" onClick={() => setMode('list')} className="cancel-btn">
              Cancel
            </button>
            <button type="submit" disabled={submitting} className="submit-btn">
              {submitting ? 'Submitting...' : 'Submit Proposal'}
            </button>
          </div>
        </form>
      </div>
    );
  }

  return (
    <div className="amendment-panel">
      <div className="panel-header">
        <h3>
          <span className="panel-icon">⚖️</span>
          Amendments
        </h3>
        <div className="header-actions">
          <button className="propose-new-btn" onClick={() => setMode('propose')}>
            + Propose New
          </button>
          {onClose && (
            <button className="close-btn" onClick={onClose}>×</button>
          )}
        </div>
      </div>

      {loading ? (
        <div className="loading-state">Loading amendments...</div>
      ) : amendments.length === 0 ? (
        <div className="empty-state">
          <p>No pending amendments</p>
          <p className="sub-text">Be the first to propose one!</p>
        </div>
      ) : (
        <div className="amendments-list">
          {amendments.map((amendment) => {
            const status = getStatusBadge(amendment.status);
            const totalVotes = amendment.votes_for + amendment.votes_against;
            const forPercent = totalVotes > 0 ? (amendment.votes_for / totalVotes) * 100 : 50;

            return (
              <div key={amendment.id} className="amendment-card">
                <div className="amendment-header">
                  <span className={`status-badge ${status.className}`}>
                    {status.icon} {status.label}
                  </span>
                  <span className="amendment-type">{getTypeLabel(amendment.type)}</span>
                </div>

                <div className="amendment-body">
                  {amendment.proposed_title && (
                    <h4>{amendment.proposed_title}</h4>
                  )}
                  <p className="reason">{amendment.reason}</p>

                  {amendment.proposed_text && (
                    <div className="proposed-text">
                      <span className="label">Proposed text:</span>
                      <p>{amendment.proposed_text.substring(0, 200)}...</p>
                    </div>
                  )}
                </div>

                <div className="amendment-meta">
                  <span>By: {amendment.proposed_by}</span>
                  {amendment.voting_deadline && (
                    <span>Deadline: {new Date(amendment.voting_deadline).toLocaleDateString()}</span>
                  )}
                </div>

                {amendment.status === 'voting' && (
                  <div className="voting-section">
                    <div className="vote-bar">
                      <div
                        className="vote-fill for"
                        style={{ width: `${forPercent}%` }}
                      />
                    </div>
                    <div className="vote-counts">
                      <span className="for">{amendment.votes_for} For</span>
                      <span className="against">{amendment.votes_against} Against</span>
                    </div>
                    <div className="vote-buttons">
                      <button
                        className="vote-btn for"
                        onClick={() => handleVote(amendment.id, true)}
                      >
                        Vote For
                      </button>
                      <button
                        className="vote-btn against"
                        onClick={() => handleVote(amendment.id, false)}
                      >
                        Vote Against
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {error && <div className="panel-error">{error}</div>}
    </div>
  );
};

export default AmendmentPanel;
