import './VoiceControls.css';

export default function VoiceControls({
  isPlaying,
  isPaused,
  currentIndex,
  totalItems,
  currentLabel,
  speed,
  onPlayPause,
  onNext,
  onPrevious,
  onStop,
  onSpeedChange,
  disabled,
}) {
  const speedOptions = [0.5, 0.75, 1, 1.25, 1.5, 2];

  return (
    <div className={`voice-controls ${disabled ? 'disabled' : ''}`}>
      {/* Progress indicator */}
      <div className="voice-progress">
        <span className="progress-label">{currentLabel}</span>
        <span className="progress-count">
          {totalItems > 0 ? `${currentIndex + 1} / ${totalItems}` : '—'}
        </span>
      </div>

      {/* Main controls */}
      <div className="voice-main-controls">
        {/* Previous button */}
        <button
          className="voice-btn"
          onClick={onPrevious}
          disabled={disabled || currentIndex === 0}
          title="Previous"
        >
          ⏮️
        </button>

        {/* Play/Pause button */}
        <button
          className="voice-btn play-btn"
          onClick={onPlayPause}
          disabled={disabled}
          title={isPlaying ? 'Pause' : isPaused ? 'Resume' : 'Play'}
        >
          {isPlaying ? '⏸️' : '▶️'}
        </button>

        {/* Stop button */}
        <button
          className="voice-btn"
          onClick={onStop}
          disabled={disabled || (!isPlaying && !isPaused)}
          title="Stop"
        >
          ⏹️
        </button>

        {/* Next button */}
        <button
          className="voice-btn"
          onClick={onNext}
          disabled={disabled || currentIndex >= totalItems - 1}
          title="Next"
        >
          ⏭️
        </button>
      </div>

      {/* Speed control */}
      <div className="voice-speed">
        <label className="speed-label">Speed:</label>
        <select
          className="speed-select"
          value={speed}
          onChange={(e) => onSpeedChange(parseFloat(e.target.value))}
          disabled={disabled}
        >
          {speedOptions.map((s) => (
            <option key={s} value={s}>
              {s}x
            </option>
          ))}
        </select>
      </div>

      {/* Status indicator */}
      <div className="voice-status">
        {isPlaying && <span className="status-indicator speaking">Speaking</span>}
        {isPaused && <span className="status-indicator paused">Paused</span>}
        {!isPlaying && !isPaused && totalItems > 0 && (
          <span className="status-indicator ready">Ready</span>
        )}
      </div>
    </div>
  );
}
