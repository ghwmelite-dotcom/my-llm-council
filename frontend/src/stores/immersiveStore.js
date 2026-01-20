// Zustand store for immersive 3D council mode
import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import { STAGE_CONFIGS, MODEL_PROFILES } from '../config/modelProfiles';

// Initial model states
const createInitialModelStates = () => {
  const states = {};
  Object.keys(MODEL_PROFILES).forEach((modelId) => {
    states[modelId] = {
      status: 'idle', // idle, thinking, speaking, finished
      response: null,
      ranking: null,
      parsedRanking: [],
      isHighlighted: false,
      pulseIntensity: 0,
    };
  });
  return states;
};

export const useImmersiveStore = create(
  subscribeWithSelector((set, get) => ({
    // Core state
    isImmersiveMode: false,
    currentStage: 'idle', // idle, stage1, stage2, stage2_rebuttals, stage3
    isProcessing: false,

    // Model states
    modelStates: createInitialModelStates(),
    activeSpeaker: null,
    chairmanSpeaking: false,

    // Stage data
    stage1Results: [],
    stage2Results: [],
    stage2Metadata: null,
    stage3Result: null,
    rebuttals: [], // For Tier 2 debate rounds

    // Agreement connections
    connections: [], // { from: modelId, to: modelId, strength: 0-1 }

    // Voice state
    voiceEnabled: false,
    voicePlaying: false,
    voiceQueue: [],
    currentVoiceIndex: 0,
    voiceSpeed: 1.0,

    // Camera state
    cameraPosition: STAGE_CONFIGS.idle.camera,
    cameraLookAt: STAGE_CONFIGS.idle.lookAt,
    cameraTransitioning: false,

    // Devil's advocate state (Tier 2)
    devilsAdvocate: null,

    // User participation state (Tier 2)
    userResponse: null,
    userRank: null,

    // Actions
    setImmersiveMode: (enabled) => set({ isImmersiveMode: enabled }),

    setCurrentStage: (stage) => {
      const config = STAGE_CONFIGS[stage] || STAGE_CONFIGS.idle;
      set({
        currentStage: stage,
        cameraPosition: config.camera,
        cameraLookAt: config.lookAt,
        cameraTransitioning: true,
      });
      // Reset transitioning after animation
      setTimeout(() => set({ cameraTransitioning: false }), 1000);
    },

    setProcessing: (isProcessing) => set({ isProcessing }),

    // Model state updates
    setModelStatus: (modelId, status) =>
      set((state) => ({
        modelStates: {
          ...state.modelStates,
          [modelId]: {
            ...state.modelStates[modelId],
            status,
            pulseIntensity: status === 'thinking' ? 0.5 : status === 'speaking' ? 1 : 0,
          },
        },
      })),

    setModelResponse: (modelId, response) =>
      set((state) => ({
        modelStates: {
          ...state.modelStates,
          [modelId]: {
            ...state.modelStates[modelId],
            response,
            status: 'finished',
          },
        },
      })),

    setModelRanking: (modelId, ranking, parsedRanking) =>
      set((state) => ({
        modelStates: {
          ...state.modelStates,
          [modelId]: {
            ...state.modelStates[modelId],
            ranking,
            parsedRanking: parsedRanking || [],
          },
        },
      })),

    highlightModel: (modelId, isHighlighted) =>
      set((state) => ({
        modelStates: {
          ...state.modelStates,
          [modelId]: {
            ...state.modelStates[modelId],
            isHighlighted,
          },
        },
      })),

    setActiveSpeaker: (modelId) => {
      const state = get();
      // Reset previous speaker
      if (state.activeSpeaker && state.activeSpeaker !== modelId) {
        set((s) => ({
          modelStates: {
            ...s.modelStates,
            [s.activeSpeaker]: {
              ...s.modelStates[s.activeSpeaker],
              status: 'finished',
            },
          },
        }));
      }
      // Set new speaker
      set({
        activeSpeaker: modelId,
        modelStates: {
          ...state.modelStates,
          ...(modelId && {
            [modelId]: {
              ...state.modelStates[modelId],
              status: 'speaking',
            },
          }),
        },
      });
    },

    // Stage data updates
    setStage1Results: (results) => {
      set({ stage1Results: results });
      // Update individual model states
      results.forEach((r) => {
        get().setModelResponse(r.model, r.response);
      });
    },

    setStage2Results: (results, metadata) => {
      set({
        stage2Results: results,
        stage2Metadata: metadata,
      });
      // Update model rankings
      results.forEach((r) => {
        get().setModelRanking(r.model, r.ranking, r.parsed_ranking);
      });
      // Calculate connections based on agreement
      get().calculateConnections(metadata);
    },

    setStage3Result: (result) => {
      set({
        stage3Result: result,
        chairmanSpeaking: true,
      });
    },

    // Calculate agreement connections from rankings
    calculateConnections: (metadata) => {
      if (!metadata?.aggregate_rankings) {
        set({ connections: [] });
        return;
      }

      const rankings = metadata.aggregate_rankings;
      const connections = [];
      const modelIds = Object.keys(MODEL_PROFILES);

      // Compare each pair of models
      for (let i = 0; i < modelIds.length; i++) {
        for (let j = i + 1; j < modelIds.length; j++) {
          const modelA = modelIds[i];
          const modelB = modelIds[j];

          // Find their positions in each ranking
          const stateA = get().modelStates[modelA];
          const stateB = get().modelStates[modelB];

          if (stateA?.parsedRanking && stateB?.parsedRanking) {
            // Compare ranking similarity
            const similarity = calculateRankingSimilarity(
              stateA.parsedRanking,
              stateB.parsedRanking
            );
            if (similarity > 0.3) {
              connections.push({
                from: modelA,
                to: modelB,
                strength: similarity,
              });
            }
          }
        }
      }

      set({ connections });
    },

    // Voice controls
    setVoiceEnabled: (enabled) => set({ voiceEnabled: enabled }),
    setVoicePlaying: (playing) => set({ voicePlaying: playing }),
    setVoiceSpeed: (speed) => set({ voiceSpeed: speed }),

    queueVoice: (items) =>
      set((state) => ({
        voiceQueue: [...state.voiceQueue, ...items],
      })),

    advanceVoiceQueue: () =>
      set((state) => ({
        currentVoiceIndex: state.currentVoiceIndex + 1,
      })),

    clearVoiceQueue: () =>
      set({
        voiceQueue: [],
        currentVoiceIndex: 0,
        voicePlaying: false,
      }),

    // Rebuttals (Tier 2)
    addRebuttalRound: (round) =>
      set((state) => ({
        rebuttals: [...state.rebuttals, round],
      })),

    // Devil's advocate (Tier 2)
    setDevilsAdvocate: (challenge) => set({ devilsAdvocate: challenge }),

    // User participation (Tier 2)
    setUserResponse: (response) => set({ userResponse: response }),
    setUserRank: (rank) => set({ userRank: rank }),

    // Reset for new query
    resetForNewQuery: () =>
      set({
        currentStage: 'idle',
        isProcessing: false,
        modelStates: createInitialModelStates(),
        activeSpeaker: null,
        chairmanSpeaking: false,
        stage1Results: [],
        stage2Results: [],
        stage2Metadata: null,
        stage3Result: null,
        rebuttals: [],
        connections: [],
        voiceQueue: [],
        currentVoiceIndex: 0,
        voicePlaying: false,
        devilsAdvocate: null,
        userResponse: null,
        userRank: null,
        cameraPosition: STAGE_CONFIGS.idle.camera,
        cameraLookAt: STAGE_CONFIGS.idle.lookAt,
      }),

    // Full reset
    reset: () =>
      set({
        isImmersiveMode: false,
        currentStage: 'idle',
        isProcessing: false,
        modelStates: createInitialModelStates(),
        activeSpeaker: null,
        chairmanSpeaking: false,
        stage1Results: [],
        stage2Results: [],
        stage2Metadata: null,
        stage3Result: null,
        rebuttals: [],
        connections: [],
        voiceEnabled: false,
        voicePlaying: false,
        voiceQueue: [],
        currentVoiceIndex: 0,
        voiceSpeed: 1.0,
        cameraPosition: STAGE_CONFIGS.idle.camera,
        cameraLookAt: STAGE_CONFIGS.idle.lookAt,
        cameraTransitioning: false,
        devilsAdvocate: null,
        userResponse: null,
        userRank: null,
      }),
  }))
);

// Helper function to calculate ranking similarity (Kendall tau-like)
function calculateRankingSimilarity(rankingA, rankingB) {
  if (!rankingA.length || !rankingB.length) return 0;

  let concordant = 0;
  let total = 0;

  for (let i = 0; i < rankingA.length; i++) {
    for (let j = i + 1; j < rankingA.length; j++) {
      const itemI = rankingA[i];
      const itemJ = rankingA[j];

      const posIinB = rankingB.indexOf(itemI);
      const posJinB = rankingB.indexOf(itemJ);

      if (posIinB >= 0 && posJinB >= 0) {
        total++;
        if ((posIinB < posJinB) === (i < j)) {
          concordant++;
        }
      }
    }
  }

  return total > 0 ? concordant / total : 0;
}

// Selectors for common state combinations
export const selectIsActive = (state) =>
  state.isImmersiveMode && state.currentStage !== 'idle';

export const selectActiveModelIds = (state) =>
  Object.entries(state.modelStates)
    .filter(([_, s]) => s.status !== 'idle')
    .map(([id]) => id);

export const selectTopRankedModel = (state) => {
  if (!state.stage2Metadata?.aggregate_rankings?.length) return null;
  return state.stage2Metadata.aggregate_rankings[0]?.model;
};
