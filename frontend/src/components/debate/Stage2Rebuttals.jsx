import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import './Stage2Rebuttals.css';

export default function Stage2Rebuttals({ rebuttals, debateRounds }) {
  const [expandedRounds, setExpandedRounds] = useState({});
  const [expandedRebuttals, setExpandedRebuttals] = useState({});

  const toggleRound = (roundNum) => {
    setExpandedRounds((prev) => ({
      ...prev,
      [roundNum]: !prev[roundNum],
    }));
  };

  const toggleRebuttal = (index) => {
    setExpandedRebuttals((prev) => ({
      ...prev,
      [index]: !prev[index],
    }));
  };

  if (!rebuttals || rebuttals.length === 0) {
    return null;
  }

  // Group rebuttals by round if debate rounds info is available
  const groupedRebuttals = {};
  let currentRound = 1;
  let rebuttalIndex = 0;

  if (debateRounds && debateRounds.length > 0) {
    debateRounds.forEach((round) => {
      if (round.rebuttal_count) {
        groupedRebuttals[round.round] = rebuttals.slice(
          rebuttalIndex,
          rebuttalIndex + round.rebuttal_count
        );
        rebuttalIndex += round.rebuttal_count;
      }
    });
  } else {
    // If no round info, put all in round 1
    groupedRebuttals[1] = rebuttals;
  }

  const getModelShortName = (modelId) => {
    return modelId?.split('/').pop() || modelId;
  };

  const getStatusLabel = (status) => {
    switch (status) {
      case 'consensus_reached':
        return 'Consensus Reached';
      case 'no_rebuttals':
        return 'No Rebuttals Needed';
      case 'rebuttals_collected':
        return 'Rebuttals Collected';
      default:
        return status;
    }
  };

  return (
    <div className="stage2-rebuttals">
      <div className="rebuttals-header">
        <h3>Debate Rounds</h3>
        <span className="rebuttals-count">
          {rebuttals.length} rebuttal{rebuttals.length !== 1 ? 's' : ''} across{' '}
          {Object.keys(groupedRebuttals).length} round
          {Object.keys(groupedRebuttals).length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Debate rounds timeline */}
      {debateRounds && debateRounds.length > 0 && (
        <div className="debate-timeline">
          {debateRounds.map((round, idx) => (
            <div
              key={idx}
              className={`timeline-item ${round.status}`}
              onClick={() => toggleRound(round.round)}
            >
              <div className="timeline-marker">
                <span className="round-number">{round.round}</span>
              </div>
              <div className="timeline-content">
                <div className="timeline-label">Round {round.round}</div>
                <div className="timeline-status">
                  {getStatusLabel(round.status)}
                  {round.top_model && (
                    <span className="consensus-model">
                      {' '}
                      ({getModelShortName(round.top_model)})
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Rebuttals by round */}
      {Object.entries(groupedRebuttals).map(([roundNum, roundRebuttals]) => (
        <div key={roundNum} className="rebuttal-round">
          <button
            className={`round-toggle ${expandedRounds[roundNum] ? 'expanded' : ''}`}
            onClick={() => toggleRound(roundNum)}
          >
            <span className="round-title">Round {roundNum}</span>
            <span className="round-count">
              {roundRebuttals.length} rebuttal{roundRebuttals.length !== 1 ? 's' : ''}
            </span>
            <span className="toggle-icon">{expandedRounds[roundNum] ? '▼' : '▶'}</span>
          </button>

          {expandedRounds[roundNum] && (
            <div className="round-rebuttals">
              {roundRebuttals.map((rebuttal, idx) => {
                const globalIdx = `${roundNum}-${idx}`;
                return (
                  <div key={globalIdx} className="rebuttal-item">
                    <button
                      className={`rebuttal-toggle ${expandedRebuttals[globalIdx] ? 'expanded' : ''}`}
                      onClick={() => toggleRebuttal(globalIdx)}
                    >
                      <span className="rebuttal-model">
                        {getModelShortName(rebuttal.model)}
                      </span>
                      <span className="critiques-badge">
                        {rebuttal.critiques_addressed} critique
                        {rebuttal.critiques_addressed !== 1 ? 's' : ''} addressed
                      </span>
                      <span className="toggle-icon">
                        {expandedRebuttals[globalIdx] ? '▼' : '▶'}
                      </span>
                    </button>

                    {expandedRebuttals[globalIdx] && (
                      <div className="rebuttal-content">
                        <div className="markdown-content">
                          <ReactMarkdown>{rebuttal.rebuttal}</ReactMarkdown>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
