import React, { useState, useEffect } from 'react';
import './PredictionPanel.css';

const PredictionPanel = ({
  conversationId,
  models = [],
  onPredictionPlaced,
  userId = 'anonymous'
}) => {
  const [selectedModel, setSelectedModel] = useState('');
  const [confidence, setConfidence] = useState(0.5);
  const [isPlacing, setIsPlacing] = useState(false);
  const [prediction, setPrediction] = useState(null);
  const [error, setError] = useState(null);

  const handlePlacePrediction = async () => {
    if (!selectedModel) {
      setError('Please select a model');
      return;
    }

    setIsPlacing(true);
    setError(null);

    try {
      const response = await fetch(`/api/predictions/${conversationId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          predicted_winner: selectedModel,
          confidence: confidence
        })
      });

      if (!response.ok) {
        throw new Error('Failed to place prediction');
      }

      const data = await response.json();
      setPrediction(data);

      if (onPredictionPlaced) {
        onPredictionPlaced(data);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setIsPlacing(false);
    }
  };

  const confidenceLabel = () => {
    if (confidence < 0.3) return 'Low';
    if (confidence < 0.6) return 'Medium';
    if (confidence < 0.8) return 'High';
    return 'Very High';
  };

  const potentialPoints = () => {
    const basePoints = 10;
    if (confidence >= 0.5) {
      // Correct prediction
      return `+${(basePoints * (1 + confidence)).toFixed(1)}`;
    }
    return `${(-confidence * 5).toFixed(1)} to +${(basePoints * (1 + confidence)).toFixed(1)}`;
  };

  if (prediction) {
    return (
      <div className="prediction-panel prediction-placed">
        <div className="prediction-header">
          <span className="prediction-icon">🎯</span>
          <h3>Prediction Placed</h3>
        </div>
        <div className="prediction-summary">
          <div className="prediction-detail">
            <span className="label">Your Pick:</span>
            <span className="value">{prediction.predicted_winner}</span>
          </div>
          <div className="prediction-detail">
            <span className="label">Confidence:</span>
            <span className="value">{(prediction.confidence * 100).toFixed(0)}%</span>
          </div>
          <p className="prediction-note">
            Wait for the debate to conclude to see if you were right!
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="prediction-panel">
      <div className="prediction-header">
        <span className="prediction-icon">🎲</span>
        <h3>Make a Prediction</h3>
      </div>

      <p className="prediction-intro">
        Who do you think will produce the best response?
      </p>

      <div className="model-selection">
        <label>Select Model:</label>
        <div className="model-buttons">
          {models.map(model => (
            <button
              key={model}
              className={`model-button ${selectedModel === model ? 'selected' : ''}`}
              onClick={() => setSelectedModel(model)}
            >
              {model.split('/').pop()}
            </button>
          ))}
        </div>
      </div>

      <div className="confidence-selection">
        <label>
          Confidence: <strong>{confidenceLabel()}</strong> ({(confidence * 100).toFixed(0)}%)
        </label>
        <input
          type="range"
          min="0.1"
          max="1"
          step="0.1"
          value={confidence}
          onChange={(e) => setConfidence(parseFloat(e.target.value))}
          className="confidence-slider"
        />
        <div className="confidence-scale">
          <span>Low Risk</span>
          <span>High Risk/Reward</span>
        </div>
      </div>

      <div className="points-preview">
        <span className="label">Potential Points:</span>
        <span className="value">{potentialPoints()}</span>
      </div>

      {error && <div className="prediction-error">{error}</div>}

      <button
        className="place-prediction-btn"
        onClick={handlePlacePrediction}
        disabled={isPlacing || !selectedModel}
      >
        {isPlacing ? 'Placing...' : 'Place Prediction'}
      </button>
    </div>
  );
};

export default PredictionPanel;
