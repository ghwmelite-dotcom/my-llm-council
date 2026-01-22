import { useState } from 'react';
import './CostDisplay.css';

/**
 * CostDisplay - Shows cost breakdown for a query
 */
export default function CostDisplay({ costSummary }) {
  const [expanded, setExpanded] = useState(false);

  if (!costSummary) return null;

  const {
    total_cost_formatted,
    total_tokens,
    total_input_tokens,
    total_output_tokens,
    cost_by_stage,
    cost_by_model,
    api_calls,
  } = costSummary;

  return (
    <div className="cost-display">
      <button
        className="cost-toggle"
        onClick={() => setExpanded(!expanded)}
        title={expanded ? 'Hide cost details' : 'Show cost details'}
      >
        <span className="cost-icon">💰</span>
        <span className="cost-total">{total_cost_formatted}</span>
        <span className="cost-tokens">({total_tokens.toLocaleString()} tokens)</span>
        <span className={`expand-icon ${expanded ? 'expanded' : ''}`}>▼</span>
      </button>

      {expanded && (
        <div className="cost-details">
          <div className="cost-section">
            <h4>Token Usage</h4>
            <div className="cost-row">
              <span>Input tokens:</span>
              <span>{total_input_tokens.toLocaleString()}</span>
            </div>
            <div className="cost-row">
              <span>Output tokens:</span>
              <span>{total_output_tokens.toLocaleString()}</span>
            </div>
            <div className="cost-row">
              <span>API calls:</span>
              <span>{api_calls}</span>
            </div>
          </div>

          <div className="cost-section">
            <h4>Cost by Stage</h4>
            {Object.entries(cost_by_stage).map(([stage, data]) => (
              <div key={stage} className="cost-row">
                <span>{stage.replace('stage', 'Stage ')}</span>
                <span>{data.formatted}</span>
              </div>
            ))}
          </div>

          <div className="cost-section">
            <h4>Cost by Model</h4>
            {Object.entries(cost_by_model)
              .sort(([, a], [, b]) => b.cost - a.cost)
              .map(([model, data]) => (
                <div key={model} className="cost-row">
                  <span className="model-name">{model.split('/')[1] || model}</span>
                  <span>{data.formatted}</span>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}
