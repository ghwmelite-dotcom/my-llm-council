import './ProcessingStatus.css';

/**
 * ProcessingStatus - Shows real-time status indicators for:
 * - Query routing tier (simple/mini/full council)
 * - Cache hits (instant response from similar query)
 * - Factual verification results (contradictions detected)
 */
export default function ProcessingStatus({ status }) {
  if (!status) return null;

  const {
    routing,
    cacheHit,
    verification,
    isProcessing,
  } = status;

  // Don't show if nothing to display
  if (!routing && !cacheHit && !verification && !isProcessing) {
    return null;
  }

  return (
    <div className="processing-status">
      {/* Routing Tier Indicator */}
      {routing && (
        <div className={`status-badge routing tier-${routing.tier}`}>
          <span className="status-icon">
            {routing.tier === 1 ? '⚡' : routing.tier === 2 ? '👥' : '🏛️'}
          </span>
          <span className="status-text">
            {routing.tier === 1 && 'Fast Mode'}
            {routing.tier === 2 && 'Mini Council'}
            {routing.tier === 3 && 'Full Council'}
          </span>
          <span className="status-detail">
            {routing.models?.length || routing.model_count} model{(routing.models?.length || routing.model_count) !== 1 ? 's' : ''}
          </span>
        </div>
      )}

      {/* Cache Hit Indicator */}
      {cacheHit && (
        <div className="status-badge cache-hit">
          <span className="status-icon">💾</span>
          <span className="status-text">Cached Response</span>
          <span className="status-detail">
            {Math.round(cacheHit.similarity * 100)}% match
          </span>
        </div>
      )}

      {/* Verification Results */}
      {verification && verification.has_contradictions && (
        <div className={`status-badge verification severity-${verification.highest_severity}`}>
          <span className="status-icon">⚠️</span>
          <span className="status-text">
            {verification.contradiction_count} Contradiction{verification.contradiction_count !== 1 ? 's' : ''}
          </span>
          <span className="status-detail">
            {verification.highest_severity} severity
          </span>
        </div>
      )}

      {/* Verification Running */}
      {verification && verification.running && (
        <div className="status-badge verification-running">
          <span className="status-icon spinning">🔍</span>
          <span className="status-text">Verifying facts...</span>
        </div>
      )}

      {/* Processing indicator when no specific status */}
      {isProcessing && !routing && !cacheHit && (
        <div className="status-badge processing">
          <span className="status-icon spinning">⏳</span>
          <span className="status-text">Processing...</span>
        </div>
      )}
    </div>
  );
}
