import { useState, useEffect } from 'react';
import './CouncilBuilder.css';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8001';

// Available models with metadata
const AVAILABLE_MODELS = [
  { id: 'openai/gpt-4o', name: 'GPT-4o', provider: 'OpenAI', tier: 'premium' },
  { id: 'openai/gpt-4o-mini', name: 'GPT-4o Mini', provider: 'OpenAI', tier: 'standard' },
  { id: 'openai/o1-mini', name: 'o1-mini', provider: 'OpenAI', tier: 'reasoning' },
  { id: 'anthropic/claude-sonnet-4.5', name: 'Claude Sonnet 4.5', provider: 'Anthropic', tier: 'premium' },
  { id: 'anthropic/claude-3.5-haiku', name: 'Claude 3.5 Haiku', provider: 'Anthropic', tier: 'standard' },
  { id: 'google/gemini-2.5-pro', name: 'Gemini 2.5 Pro', provider: 'Google', tier: 'premium' },
  { id: 'google/gemini-2.5-flash', name: 'Gemini 2.5 Flash', provider: 'Google', tier: 'standard' },
  { id: 'meta-llama/llama-3.3-70b-instruct', name: 'Llama 3.3 70B', provider: 'Meta', tier: 'standard' },
  { id: 'deepseek/deepseek-r1', name: 'DeepSeek R1', provider: 'DeepSeek', tier: 'reasoning' },
  { id: 'qwen/qwq-32b', name: 'QwQ 32B', provider: 'Qwen', tier: 'reasoning' },
  { id: 'x-ai/grok-2', name: 'Grok 2', provider: 'xAI', tier: 'premium' },
  { id: 'mistralai/mistral-large', name: 'Mistral Large', provider: 'Mistral', tier: 'premium' },
];

const PRESETS = [
  {
    name: 'Balanced',
    description: 'Mix of different providers',
    models: ['openai/gpt-4o', 'anthropic/claude-sonnet-4.5', 'google/gemini-2.5-pro'],
    chairman: 'anthropic/claude-sonnet-4.5',
  },
  {
    name: 'Budget',
    description: 'Cost-effective options',
    models: ['openai/gpt-4o-mini', 'anthropic/claude-3.5-haiku', 'google/gemini-2.5-flash'],
    chairman: 'google/gemini-2.5-flash',
  },
  {
    name: 'Reasoning',
    description: 'Models with reasoning capabilities',
    models: ['openai/o1-mini', 'deepseek/deepseek-r1', 'qwen/qwq-32b'],
    chairman: 'openai/o1-mini',
  },
  {
    name: 'Full Council',
    description: 'All major providers',
    models: ['openai/gpt-4o', 'anthropic/claude-sonnet-4.5', 'google/gemini-2.5-pro', 'x-ai/grok-2', 'mistralai/mistral-large'],
    chairman: 'anthropic/claude-sonnet-4.5',
  },
];

export default function CouncilBuilder({ isOpen, onClose, onApply }) {
  const [selectedModels, setSelectedModels] = useState([]);
  const [chairman, setChairman] = useState('');
  const [currentConfig, setCurrentConfig] = useState(null);

  useEffect(() => {
    if (isOpen) {
      loadCurrentConfig();
    }
  }, [isOpen]);

  const loadCurrentConfig = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/config`);
      if (response.ok) {
        const config = await response.json();
        setCurrentConfig(config);
        setSelectedModels(config.models || []);
        setChairman(config.chairman || config.models?.[0] || '');
      }
    } catch (error) {
      console.error('Failed to load config:', error);
    }
  };

  const handleModelToggle = (modelId) => {
    setSelectedModels((prev) => {
      if (prev.includes(modelId)) {
        const newModels = prev.filter((m) => m !== modelId);
        // Update chairman if removed
        if (chairman === modelId && newModels.length > 0) {
          setChairman(newModels[0]);
        }
        return newModels;
      } else {
        return [...prev, modelId];
      }
    });
  };

  const applyPreset = (preset) => {
    setSelectedModels(preset.models);
    setChairman(preset.chairman);
  };

  const handleApply = () => {
    if (selectedModels.length === 0) return;

    onApply({
      models: selectedModels,
      chairman: chairman || selectedModels[0],
    });
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="council-builder-overlay" onClick={onClose}>
      <div className="council-builder" onClick={(e) => e.stopPropagation()}>
        <div className="builder-header">
          <h2>Configure Council</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="builder-content">
          {/* Presets */}
          <div className="section">
            <h3>Quick Presets</h3>
            <div className="presets-grid">
              {PRESETS.map((preset) => (
                <button
                  key={preset.name}
                  className="preset-btn"
                  onClick={() => applyPreset(preset)}
                >
                  <div className="preset-name">{preset.name}</div>
                  <div className="preset-desc">{preset.description}</div>
                  <div className="preset-count">{preset.models.length} models</div>
                </button>
              ))}
            </div>
          </div>

          {/* Model Selection */}
          <div className="section">
            <h3>Select Models ({selectedModels.length} selected)</h3>
            <div className="models-grid">
              {AVAILABLE_MODELS.map((model) => (
                <button
                  key={model.id}
                  className={`model-btn ${selectedModels.includes(model.id) ? 'selected' : ''}`}
                  onClick={() => handleModelToggle(model.id)}
                >
                  <div className="model-header">
                    <span className="model-name">{model.name}</span>
                    <span className={`tier-badge ${model.tier}`}>{model.tier}</span>
                  </div>
                  <div className="model-provider">{model.provider}</div>
                  {selectedModels.includes(model.id) && (
                    <span className="check-mark">✓</span>
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* Chairman Selection */}
          {selectedModels.length > 0 && (
            <div className="section">
              <h3>Select Chairman</h3>
              <p className="section-desc">The chairman synthesizes the final answer</p>
              <div className="chairman-options">
                {selectedModels.map((modelId) => {
                  const model = AVAILABLE_MODELS.find((m) => m.id === modelId);
                  return (
                    <button
                      key={modelId}
                      className={`chairman-btn ${chairman === modelId ? 'selected' : ''}`}
                      onClick={() => setChairman(modelId)}
                    >
                      {model?.name || modelId}
                      {chairman === modelId && <span className="crown">👑</span>}
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        <div className="builder-footer">
          <button className="cancel-btn" onClick={onClose}>
            Cancel
          </button>
          <button
            className="apply-btn"
            onClick={handleApply}
            disabled={selectedModels.length === 0}
          >
            Apply Configuration
          </button>
        </div>
      </div>
    </div>
  );
}
