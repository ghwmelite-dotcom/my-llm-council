import { useEffect, useCallback, useState } from 'react';
import { useImmersiveStore } from '../../stores/immersiveStore';
import { useVoiceSynthesis } from './useVoiceSynthesis';
import VoiceControls from './VoiceControls';
import './VoiceController.css';

export default function VoiceController() {
  const {
    voiceEnabled,
    voiceSpeed,
    setVoiceSpeed,
    voicePlaying,
    setVoicePlaying,
    stage1Results,
    stage2Results,
    stage3Result,
    currentStage,
    setActiveSpeaker,
  } = useImmersiveStore();

  const {
    isSupported,
    isSpeaking,
    isPaused,
    speak,
    pause,
    resume,
    cancel,
    speakSequence,
  } = useVoiceSynthesis();

  const [currentIndex, setCurrentIndex] = useState(0);
  const [autoPlay, setAutoPlay] = useState(false);
  const [playbackQueue, setPlaybackQueue] = useState([]);

  // Build playback queue when results change
  useEffect(() => {
    const queue = [];

    // Add stage 1 responses
    if (stage1Results.length > 0) {
      stage1Results.forEach((result) => {
        queue.push({
          type: 'stage1',
          modelId: result.model,
          text: `${getModelShortName(result.model)} says: ${result.response}`,
          label: `Stage 1 - ${getModelShortName(result.model)}`,
        });
      });
    }

    // Add stage 2 rankings (summarized)
    if (stage2Results.length > 0) {
      stage2Results.forEach((result) => {
        const summary = summarizeRanking(result);
        queue.push({
          type: 'stage2',
          modelId: result.model,
          text: `${getModelShortName(result.model)}'s evaluation: ${summary}`,
          label: `Stage 2 - ${getModelShortName(result.model)}`,
        });
      });
    }

    // Add stage 3 synthesis
    if (stage3Result) {
      queue.push({
        type: 'stage3',
        modelId: stage3Result.model,
        text: `The chairman's final synthesis: ${stage3Result.response}`,
        label: 'Final Answer',
      });
    }

    setPlaybackQueue(queue);
  }, [stage1Results, stage2Results, stage3Result]);

  // Handle play/pause
  const handlePlayPause = useCallback(() => {
    if (isSpeaking && !isPaused) {
      pause();
      setVoicePlaying(false);
    } else if (isPaused) {
      resume();
      setVoicePlaying(true);
    } else if (playbackQueue.length > 0) {
      playFromIndex(currentIndex);
    }
  }, [isSpeaking, isPaused, playbackQueue, currentIndex]);

  // Play from specific index
  const playFromIndex = useCallback(
    async (index) => {
      if (index >= playbackQueue.length) return;

      setCurrentIndex(index);
      setVoicePlaying(true);
      setAutoPlay(true);

      const item = playbackQueue[index];
      setActiveSpeaker(item.modelId);

      try {
        await speak(item.text, item.modelId, {
          speedMultiplier: voiceSpeed,
          onEnd: () => {
            if (autoPlay && index < playbackQueue.length - 1) {
              playFromIndex(index + 1);
            } else {
              setVoicePlaying(false);
              setActiveSpeaker(null);
            }
          },
        });
      } catch (error) {
        console.error('Voice playback error:', error);
        setVoicePlaying(false);
        setActiveSpeaker(null);
      }
    },
    [playbackQueue, voiceSpeed, autoPlay, speak, setActiveSpeaker, setVoicePlaying]
  );

  // Skip to next
  const handleNext = useCallback(() => {
    cancel();
    const nextIndex = Math.min(currentIndex + 1, playbackQueue.length - 1);
    if (voicePlaying) {
      playFromIndex(nextIndex);
    } else {
      setCurrentIndex(nextIndex);
    }
  }, [currentIndex, playbackQueue.length, voicePlaying, cancel]);

  // Skip to previous
  const handlePrevious = useCallback(() => {
    cancel();
    const prevIndex = Math.max(currentIndex - 1, 0);
    if (voicePlaying) {
      playFromIndex(prevIndex);
    } else {
      setCurrentIndex(prevIndex);
    }
  }, [currentIndex, voicePlaying, cancel]);

  // Stop playback
  const handleStop = useCallback(() => {
    cancel();
    setVoicePlaying(false);
    setActiveSpeaker(null);
    setAutoPlay(false);
  }, [cancel, setActiveSpeaker, setVoicePlaying]);

  // Speed change
  const handleSpeedChange = useCallback(
    (speed) => {
      setVoiceSpeed(speed);
    },
    [setVoiceSpeed]
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cancel();
    };
  }, [cancel]);

  if (!isSupported) {
    return (
      <div className="voice-controller unsupported">
        <span>Voice synthesis not supported in this browser</span>
      </div>
    );
  }

  if (!voiceEnabled) return null;

  return (
    <div className="voice-controller">
      <VoiceControls
        isPlaying={isSpeaking && !isPaused}
        isPaused={isPaused}
        currentIndex={currentIndex}
        totalItems={playbackQueue.length}
        currentLabel={playbackQueue[currentIndex]?.label || 'Ready'}
        speed={voiceSpeed}
        onPlayPause={handlePlayPause}
        onNext={handleNext}
        onPrevious={handlePrevious}
        onStop={handleStop}
        onSpeedChange={handleSpeedChange}
        disabled={playbackQueue.length === 0}
      />
    </div>
  );
}

// Helper functions
function getModelShortName(modelId) {
  return modelId.split('/').pop();
}

function summarizeRanking(result) {
  if (!result.parsed_ranking || result.parsed_ranking.length === 0) {
    return 'Unable to parse ranking';
  }

  const top = result.parsed_ranking[0];
  const rankings = result.parsed_ranking
    .map((r, i) => `${i + 1}. ${r}`)
    .join(', ');

  return `Top pick is ${top}. Full ranking: ${rankings}`;
}
