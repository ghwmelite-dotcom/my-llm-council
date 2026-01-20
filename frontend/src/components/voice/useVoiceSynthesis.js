import { useState, useEffect, useCallback, useRef } from 'react';
import { getModelProfile } from '../../config/modelProfiles';

// Custom hook for browser speech synthesis
export function useVoiceSynthesis() {
  const [isSupported, setIsSupported] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [voices, setVoices] = useState([]);
  const [currentUtterance, setCurrentUtterance] = useState(null);
  const synthRef = useRef(null);

  // Initialize speech synthesis
  useEffect(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      synthRef.current = window.speechSynthesis;
      setIsSupported(true);

      // Load voices
      const loadVoices = () => {
        const availableVoices = synthRef.current.getVoices();
        setVoices(availableVoices);
      };

      // Voices might load asynchronously
      loadVoices();
      synthRef.current.addEventListener('voiceschanged', loadVoices);

      return () => {
        synthRef.current?.removeEventListener('voiceschanged', loadVoices);
        synthRef.current?.cancel();
      };
    }
  }, []);

  // Find best matching voice for a model
  const getVoiceForModel = useCallback(
    (modelId) => {
      const profile = getModelProfile(modelId);
      const preferredVoiceName = profile.voice?.voiceName;

      if (!voices.length) return null;

      // Try to find exact match
      if (preferredVoiceName) {
        const exactMatch = voices.find((v) =>
          v.name.toLowerCase().includes(preferredVoiceName.toLowerCase())
        );
        if (exactMatch) return exactMatch;
      }

      // Fallback to any English voice
      const englishVoice = voices.find(
        (v) => v.lang.startsWith('en') && v.localService
      );
      if (englishVoice) return englishVoice;

      // Last resort: first available voice
      return voices[0];
    },
    [voices]
  );

  // Speak text with model-specific voice settings
  const speak = useCallback(
    (text, modelId, options = {}) => {
      if (!isSupported || !synthRef.current) return Promise.reject('Not supported');

      return new Promise((resolve, reject) => {
        // Cancel any ongoing speech
        synthRef.current.cancel();

        const utterance = new SpeechSynthesisUtterance(text);
        const profile = getModelProfile(modelId);

        // Set voice
        const voice = getVoiceForModel(modelId);
        if (voice) {
          utterance.voice = voice;
        }

        // Apply model-specific settings
        utterance.pitch = profile.voice?.pitch || 1;
        utterance.rate = (profile.voice?.rate || 1) * (options.speedMultiplier || 1);
        utterance.volume = options.volume || 1;

        // Event handlers
        utterance.onstart = () => {
          setIsSpeaking(true);
          setIsPaused(false);
          options.onStart?.();
        };

        utterance.onend = () => {
          setIsSpeaking(false);
          setIsPaused(false);
          setCurrentUtterance(null);
          options.onEnd?.();
          resolve();
        };

        utterance.onerror = (event) => {
          setIsSpeaking(false);
          setIsPaused(false);
          setCurrentUtterance(null);
          options.onError?.(event);
          reject(event);
        };

        utterance.onpause = () => {
          setIsPaused(true);
        };

        utterance.onresume = () => {
          setIsPaused(false);
        };

        setCurrentUtterance(utterance);
        synthRef.current.speak(utterance);
      });
    },
    [isSupported, getVoiceForModel]
  );

  // Pause current speech
  const pause = useCallback(() => {
    if (synthRef.current && isSpeaking) {
      synthRef.current.pause();
      setIsPaused(true);
    }
  }, [isSpeaking]);

  // Resume paused speech
  const resume = useCallback(() => {
    if (synthRef.current && isPaused) {
      synthRef.current.resume();
      setIsPaused(false);
    }
  }, [isPaused]);

  // Cancel all speech
  const cancel = useCallback(() => {
    if (synthRef.current) {
      synthRef.current.cancel();
      setIsSpeaking(false);
      setIsPaused(false);
      setCurrentUtterance(null);
    }
  }, []);

  // Speak a sequence of items
  const speakSequence = useCallback(
    async (items, options = {}) => {
      const { onItemStart, onItemEnd, onComplete, speedMultiplier } = options;

      for (let i = 0; i < items.length; i++) {
        const item = items[i];
        onItemStart?.(item, i);

        try {
          await speak(item.text, item.modelId, {
            speedMultiplier,
            onStart: () => onItemStart?.(item, i),
            onEnd: () => onItemEnd?.(item, i),
          });
        } catch (error) {
          console.error('Speech error:', error);
          // Continue with next item even if one fails
        }
      }

      onComplete?.();
    },
    [speak]
  );

  return {
    isSupported,
    isSpeaking,
    isPaused,
    voices,
    speak,
    pause,
    resume,
    cancel,
    speakSequence,
    getVoiceForModel,
  };
}

export default useVoiceSynthesis;
