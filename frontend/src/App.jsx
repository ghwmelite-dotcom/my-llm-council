import { useState, useEffect, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import CouncilChamber from './components/immersive/CouncilChamber';
import VoiceController from './components/voice/VoiceController';
import LandingPage from './components/landing/LandingPage';
import { useImmersiveStore } from './stores/immersiveStore';
import { api } from './api';
import './App.css';

// Helper to safely access localStorage
const getStoredValue = (key, defaultValue) => {
  try {
    const stored = localStorage.getItem(key);
    return stored !== null ? JSON.parse(stored) : defaultValue;
  } catch {
    return defaultValue;
  }
};

function App() {
  // Restore state from localStorage on initial load
  const [showLanding, setShowLanding] = useState(() => getStoredValue('llm-council-show-landing', true));
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(() => getStoredValue('llm-council-conversation-id', null));
  const [currentConversation, setCurrentConversation] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  // Persist showLanding to localStorage
  useEffect(() => {
    localStorage.setItem('llm-council-show-landing', JSON.stringify(showLanding));
  }, [showLanding]);

  // Persist currentConversationId to localStorage
  useEffect(() => {
    localStorage.setItem('llm-council-conversation-id', JSON.stringify(currentConversationId));
  }, [currentConversationId]);

  // Immersive mode state from Zustand
  const {
    isImmersiveMode,
    setImmersiveMode,
    voiceEnabled,
    setVoiceEnabled,
    setCurrentStage,
    setProcessing,
    setStage1Results,
    setStage2Results,
    setStage3Result,
    resetForNewQuery,
    setModelStatus,
  } = useImmersiveStore();

  // Load conversations on mount
  useEffect(() => {
    loadConversations();
  }, []);

  // Load conversation details when selected
  useEffect(() => {
    if (currentConversationId) {
      loadConversation(currentConversationId);
    }
  }, [currentConversationId]);

  const loadConversations = async () => {
    try {
      const convs = await api.listConversations();
      setConversations(convs);
    } catch (error) {
      console.error('Failed to load conversations:', error);
    }
  };

  const loadConversation = async (id) => {
    try {
      const conv = await api.getConversation(id);
      setCurrentConversation(conv);
    } catch (error) {
      console.error('Failed to load conversation:', error);
    }
  };

  const handleNewConversation = async () => {
    try {
      const newConv = await api.createConversation();
      setConversations([
        { id: newConv.id, created_at: newConv.created_at, message_count: 0 },
        ...conversations,
      ]);
      setCurrentConversationId(newConv.id);
      resetForNewQuery();
    } catch (error) {
      console.error('Failed to create conversation:', error);
    }
  };

  const handleSelectConversation = (id) => {
    setCurrentConversationId(id);
    resetForNewQuery();
  };

  const handleSendMessage = async (content) => {
    if (!currentConversationId) return;

    setIsLoading(true);
    resetForNewQuery();
    setProcessing(true);

    try {
      // Optimistically add user message to UI
      const userMessage = { role: 'user', content };
      setCurrentConversation((prev) => ({
        ...prev,
        messages: [...prev.messages, userMessage],
      }));

      // Create a partial assistant message that will be updated progressively
      const assistantMessage = {
        role: 'assistant',
        stage1: null,
        stage2: null,
        stage3: null,
        metadata: null,
        loading: {
          stage1: false,
          stage2: false,
          stage3: false,
        },
      };

      // Add the partial assistant message
      setCurrentConversation((prev) => ({
        ...prev,
        messages: [...prev.messages, assistantMessage],
      }));

      // Send message with streaming
      await api.sendMessageStream(currentConversationId, content, (eventType, event) => {
        switch (eventType) {
          case 'stage1_start':
            setCurrentStage('stage1');
            // Set all models to thinking state
            event.data?.models?.forEach((model) => {
              setModelStatus(model, 'thinking');
            });
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.loading.stage1 = true;
              return { ...prev, messages };
            });
            break;

          case 'stage1_complete':
            setStage1Results(event.data);
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.stage1 = event.data;
              lastMsg.loading.stage1 = false;
              return { ...prev, messages };
            });
            break;

          case 'stage2_start':
            setCurrentStage('stage2');
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.loading.stage2 = true;
              return { ...prev, messages };
            });
            break;

          case 'stage2_complete':
            setStage2Results(event.data, event.metadata);
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.stage2 = event.data;
              lastMsg.metadata = event.metadata;
              lastMsg.loading.stage2 = false;
              return { ...prev, messages };
            });
            break;

          case 'stage3_start':
            setCurrentStage('stage3');
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.loading.stage3 = true;
              return { ...prev, messages };
            });
            break;

          case 'stage3_complete':
            setStage3Result(event.data);
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.stage3 = event.data;
              lastMsg.loading.stage3 = false;
              return { ...prev, messages };
            });
            break;

          case 'title_complete':
            // Reload conversations to get updated title
            loadConversations();
            break;

          case 'complete':
            // Stream complete, reload conversations list
            loadConversations();
            setIsLoading(false);
            setProcessing(false);
            break;

          case 'error':
            console.error('Stream error:', event.message);
            setIsLoading(false);
            setProcessing(false);
            break;

          default:
            console.log('Unknown event type:', eventType);
        }
      });
    } catch (error) {
      console.error('Failed to send message:', error);
      // Remove optimistic messages on error
      setCurrentConversation((prev) => ({
        ...prev,
        messages: prev.messages.slice(0, -2),
      }));
      setIsLoading(false);
      setProcessing(false);
    }
  };

  const handleToggleImmersive = useCallback(() => {
    setImmersiveMode(!isImmersiveMode);
  }, [isImmersiveMode, setImmersiveMode]);

  const handleToggleVoice = useCallback(() => {
    setVoiceEnabled(!voiceEnabled);
  }, [voiceEnabled, setVoiceEnabled]);

  const handleEnterCouncil = useCallback(() => {
    setShowLanding(false);
  }, []);

  // Show landing page initially
  if (showLanding) {
    return <LandingPage onEnterCouncil={handleEnterCouncil} />;
  }

  return (
    <div className="app">
      <Sidebar
        conversations={conversations}
        currentConversationId={currentConversationId}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
      />
      <div className="main-content">
        {/* Mode Toggle Header */}
        <div className="mode-toggle-header">
          <div className="toggle-group">
            <button
              className={`mode-toggle-btn ${!isImmersiveMode ? 'active' : ''}`}
              onClick={() => setImmersiveMode(false)}
              title="Text Mode"
            >
              <span className="toggle-icon">📝</span>
              <span className="toggle-label">Text</span>
            </button>
            <button
              className={`mode-toggle-btn ${isImmersiveMode ? 'active' : ''}`}
              onClick={() => setImmersiveMode(true)}
              title="3D Council Chamber"
            >
              <span className="toggle-icon">🏛️</span>
              <span className="toggle-label">3D Chamber</span>
            </button>
          </div>
          <div className="toggle-group">
            <button
              className={`voice-toggle-btn ${voiceEnabled ? 'active' : ''}`}
              onClick={handleToggleVoice}
              title={voiceEnabled ? 'Disable Voice' : 'Enable Voice'}
            >
              <span className="toggle-icon">{voiceEnabled ? '🔊' : '🔇'}</span>
              <span className="toggle-label">Voice</span>
            </button>
          </div>
        </div>

        {/* Main Content Area */}
        {isImmersiveMode ? (
          <CouncilChamber
            conversation={currentConversation}
            onSendMessage={handleSendMessage}
            isLoading={isLoading}
          />
        ) : (
          <ChatInterface
            conversation={currentConversation}
            onSendMessage={handleSendMessage}
            isLoading={isLoading}
          />
        )}

        {/* Voice Controller (renders regardless of mode) */}
        {voiceEnabled && <VoiceController />}
      </div>
    </div>
  );
}

export default App;
