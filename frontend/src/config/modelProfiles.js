// Model profiles configuration for LLM Council
// Defines visual appearance, 3D positioning, and voice settings for each model

export const MODEL_PROFILES = {
  'openai/gpt-5.1': {
    shortName: 'GPT-5.1',
    displayName: 'GPT-5.1',
    color: '#10a37f', // OpenAI green
    accentColor: '#0d8c6d',
    position: { x: 0, y: 0, z: -2.5 }, // Front position
    rotation: 0, // Facing center
    avatarEmoji: '🧠',
    voice: {
      pitch: 1.0,
      rate: 1.0,
      voiceName: 'Google US English', // Fallback to available voice
    },
    traits: ['analytical', 'precise', 'comprehensive'],
  },
  'google/gemini-3-pro-preview': {
    shortName: 'Gemini-3',
    displayName: 'Gemini 3 Pro',
    color: '#4285f4', // Google blue
    accentColor: '#3367d6',
    position: { x: 2.5, y: 0, z: 0 }, // Right position
    rotation: Math.PI * 0.5, // Facing center
    avatarEmoji: '💎',
    voice: {
      pitch: 1.1,
      rate: 1.05,
      voiceName: 'Google UK English Male',
    },
    traits: ['balanced', 'multimodal', 'contextual'],
  },
  'anthropic/claude-sonnet-4.5': {
    shortName: 'Claude-4.5',
    displayName: 'Claude Sonnet 4.5',
    color: '#d97706', // Anthropic orange/amber
    accentColor: '#b45309',
    position: { x: 0, y: 0, z: 2.5 }, // Back position
    rotation: Math.PI, // Facing center
    avatarEmoji: '🎭',
    voice: {
      pitch: 0.95,
      rate: 0.95,
      voiceName: 'Google UK English Female',
    },
    traits: ['thoughtful', 'nuanced', 'ethical'],
  },
  'x-ai/grok-4': {
    shortName: 'Grok-4',
    displayName: 'Grok 4',
    color: '#1d9bf0', // X/Twitter blue
    accentColor: '#1a8cd8',
    position: { x: -2.5, y: 0, z: 0 }, // Left position
    rotation: -Math.PI * 0.5, // Facing center
    avatarEmoji: '🚀',
    voice: {
      pitch: 1.15,
      rate: 1.1,
      voiceName: 'Microsoft David',
    },
    traits: ['witty', 'direct', 'unconventional'],
  },
};

// Chairman configuration
export const CHAIRMAN_PROFILE = {
  model: 'google/gemini-3-pro-preview',
  position: { x: 0, y: 1, z: 0 }, // Above center
  podiumColor: '#ffd700', // Gold
};

// Stage configurations for camera positions and lighting
export const STAGE_CONFIGS = {
  idle: {
    camera: { x: 0, y: 8, z: 8 },
    lookAt: { x: 0, y: 0, z: 0 },
    ambientIntensity: 0.5,
  },
  stage1: {
    camera: { x: 0, y: 6, z: 6 },
    lookAt: { x: 0, y: 0, z: 0 },
    ambientIntensity: 0.7,
  },
  stage2: {
    camera: { x: 4, y: 5, z: 4 },
    lookAt: { x: 0, y: 0.5, z: 0 },
    ambientIntensity: 0.8,
  },
  stage3: {
    camera: { x: 0, y: 4, z: 5 },
    lookAt: { x: 0, y: 1, z: 0 },
    ambientIntensity: 1.0,
  },
};

// Connection line styles for agreement visualization
export const CONNECTION_STYLES = {
  strongAgreement: {
    color: '#22c55e', // Green
    opacity: 0.8,
    lineWidth: 3,
  },
  moderateAgreement: {
    color: '#eab308', // Yellow
    opacity: 0.6,
    lineWidth: 2,
  },
  disagreement: {
    color: '#ef4444', // Red
    opacity: 0.4,
    lineWidth: 1,
  },
};

// Animation timings
export const ANIMATION_CONFIG = {
  avatarPulse: 1.5, // seconds
  speechBubbleFade: 0.3,
  cameraTransition: 1.0,
  connectionDraw: 0.5,
};

// Helper function to get profile by model ID
export function getModelProfile(modelId) {
  return MODEL_PROFILES[modelId] || {
    shortName: modelId.split('/').pop(),
    displayName: modelId,
    color: '#666666',
    accentColor: '#444444',
    position: { x: 0, y: 0, z: 0 },
    rotation: 0,
    avatarEmoji: '🤖',
    voice: { pitch: 1.0, rate: 1.0, voiceName: null },
    traits: [],
  };
}

// Get all model positions for table layout
export function getModelPositions() {
  return Object.entries(MODEL_PROFILES).map(([id, profile]) => ({
    id,
    ...profile.position,
    rotation: profile.rotation,
  }));
}

// Get color palette for visualization
export function getModelColors() {
  return Object.entries(MODEL_PROFILES).reduce((acc, [id, profile]) => {
    acc[id] = profile.color;
    return acc;
  }, {});
}
