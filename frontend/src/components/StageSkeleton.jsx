import './StageSkeleton.css';

export default function StageSkeleton({ stage, models = [] }) {
  const stageInfo = {
    1: {
      title: 'Stage 1: Individual Responses',
      description: 'Gathering perspectives from council members...',
      color: 'var(--accent-blue)',
    },
    2: {
      title: 'Stage 2: Peer Rankings',
      description: 'Models evaluating each other\'s responses...',
      color: '#f59e0b',
    },
    3: {
      title: 'Stage 3: Final Synthesis',
      description: 'Chairman synthesizing the final answer...',
      color: '#22c55e',
    },
  };

  const info = stageInfo[stage] || stageInfo[1];

  return (
    <div className={`stage-skeleton stage-skeleton-${stage}`}>
      <div className="skeleton-header">
        <div className="skeleton-badge" style={{ background: info.color }}>
          {stage}
        </div>
        <div className="skeleton-title">{info.title}</div>
      </div>

      {stage === 1 && (
        <>
          <div className="skeleton-tabs">
            {models.length > 0 ? (
              models.map((model, i) => (
                <div key={i} className="skeleton-tab">
                  {model.split('/')[1] || model}
                </div>
              ))
            ) : (
              <>
                <div className="skeleton-tab shimmer">Model 1</div>
                <div className="skeleton-tab shimmer">Model 2</div>
                <div className="skeleton-tab shimmer">Model 3</div>
              </>
            )}
          </div>
          <div className="skeleton-content">
            <div className="skeleton-model-name shimmer"></div>
            <div className="skeleton-lines">
              <div className="skeleton-line shimmer" style={{ width: '100%' }}></div>
              <div className="skeleton-line shimmer" style={{ width: '92%' }}></div>
              <div className="skeleton-line shimmer" style={{ width: '85%' }}></div>
              <div className="skeleton-line shimmer" style={{ width: '95%' }}></div>
              <div className="skeleton-line shimmer" style={{ width: '78%' }}></div>
              <div className="skeleton-line shimmer" style={{ width: '88%' }}></div>
            </div>
          </div>
        </>
      )}

      {stage === 2 && (
        <div className="skeleton-content">
          <div className="skeleton-ranking-header shimmer"></div>
          <div className="skeleton-rankings">
            <div className="skeleton-rank-item shimmer"></div>
            <div className="skeleton-rank-item shimmer"></div>
            <div className="skeleton-rank-item shimmer"></div>
          </div>
          <div className="skeleton-lines" style={{ marginTop: '16px' }}>
            <div className="skeleton-line shimmer" style={{ width: '100%' }}></div>
            <div className="skeleton-line shimmer" style={{ width: '88%' }}></div>
            <div className="skeleton-line shimmer" style={{ width: '92%' }}></div>
          </div>
        </div>
      )}

      {stage === 3 && (
        <div className="skeleton-content stage3-content">
          <div className="skeleton-chairman shimmer"></div>
          <div className="skeleton-lines">
            <div className="skeleton-line shimmer" style={{ width: '100%' }}></div>
            <div className="skeleton-line shimmer" style={{ width: '95%' }}></div>
            <div className="skeleton-line shimmer" style={{ width: '88%' }}></div>
            <div className="skeleton-line shimmer" style={{ width: '100%' }}></div>
            <div className="skeleton-line shimmer" style={{ width: '72%' }}></div>
            <div className="skeleton-line shimmer" style={{ width: '90%' }}></div>
            <div className="skeleton-line shimmer" style={{ width: '85%' }}></div>
          </div>
        </div>
      )}

      <div className="skeleton-status">
        <div className="skeleton-spinner"></div>
        <span>{info.description}</span>
      </div>
    </div>
  );
}
