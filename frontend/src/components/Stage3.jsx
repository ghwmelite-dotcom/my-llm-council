import ReactMarkdown from 'react-markdown';
import CopyButton from './CopyButton';
import './Stage3.css';

export default function Stage3({ finalResponse }) {
  if (!finalResponse) {
    return null;
  }

  const isStreaming = finalResponse.isStreaming;
  const hasContent = finalResponse.response && finalResponse.response.length > 0;
  const hasModel = finalResponse.model && finalResponse.model.length > 0;

  return (
    <div className={`stage stage3 ${isStreaming ? 'streaming' : ''}`}>
      <div className="stage-header">
        <h3 className="stage-title">
          Stage 3: Final Council Answer
          {isStreaming && <span className="streaming-badge">Streaming</span>}
        </h3>
        {!isStreaming && hasContent && (
          <CopyButton text={finalResponse.response} label="Copy" />
        )}
      </div>
      <div className="final-response">
        {hasModel && (
          <div className="chairman-label">
            Chairman: {finalResponse.model.split('/')[1] || finalResponse.model}
          </div>
        )}
        <div className="final-text markdown-content">
          {hasContent ? (
            <>
              <ReactMarkdown>{finalResponse.response}</ReactMarkdown>
              {isStreaming && <span className="streaming-cursor">|</span>}
            </>
          ) : isStreaming ? (
            <div className="streaming-placeholder">
              <span className="streaming-cursor">|</span>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
