import { useState, useEffect, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import CouncilChamber from './components/immersive/CouncilChamber';
import VoiceController from './components/voice/VoiceController';
import LandingPage from './components/landing/LandingPage';
import Toast from './components/Toast';
import AnalyticsDashboard from './components/AnalyticsDashboard';
import CouncilBuilder from './components/CouncilBuilder';
import MemoryManager from './components/MemoryManager';
import CollaborationPanel from './components/CollaborationPanel';
import PluginManager from './components/PluginManager';
import { useImmersiveStore } from './stores/immersiveStore';
import { useToastStore } from './stores/toastStore';
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

  // Processing status for new features (routing, caching, verification)
  const [processingStatus, setProcessingStatus] = useState(null);

  // Analytics dashboard state
  const [showAnalytics, setShowAnalytics] = useState(false);

  // Council builder state
  const [showCouncilBuilder, setShowCouncilBuilder] = useState(false);

  // Memory manager state
  const [showMemoryManager, setShowMemoryManager] = useState(false);

  // Collaboration panel state
  const [showCollaboration, setShowCollaboration] = useState(false);

  // Plugin manager state
  const [showPluginManager, setShowPluginManager] = useState(false);

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

  // Toast notifications
  const toast = useToastStore();

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
      toast.error('Failed to load conversations');
    }
  };

  const loadConversation = async (id) => {
    try {
      const conv = await api.getConversation(id);
      setCurrentConversation(conv);
    } catch (error) {
      console.error('Failed to load conversation:', error);
      toast.error('Failed to load conversation');
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
      toast.success('New conversation started');
    } catch (error) {
      console.error('Failed to create conversation:', error);
      toast.error('Failed to create conversation');
    }
  };

  const handleSelectConversation = (id) => {
    setCurrentConversationId(id);
    resetForNewQuery();
  };

  const handleDeleteConversation = async (id) => {
    try {
      await api.deleteConversation(id);
      // Remove from local state
      setConversations((prev) => prev.filter((c) => c.id !== id));
      // If we deleted the current conversation, clear it
      if (id === currentConversationId) {
        setCurrentConversationId(null);
        setCurrentConversation(null);
      }
      toast.success('Conversation deleted');
    } catch (error) {
      console.error('Failed to delete conversation:', error);
      toast.error('Failed to delete conversation');
    }
  };

  const handleSendMessage = async (content, imageIds = null) => {
    if (!currentConversationId) return;

    setIsLoading(true);
    resetForNewQuery();
    setProcessing(true);
    setProcessingStatus({ isProcessing: true });

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
      await api.sendMessageStream(currentConversationId, content, imageIds, (eventType, event) => {
        switch (eventType) {
          case 'routing_decision':
            // Smart routing determined the query complexity
            setProcessingStatus((prev) => ({
              ...prev,
              routing: event.data,
              isProcessing: true,
            }));
            break;

          case 'cache_hit':
            // Response served from semantic cache
            setProcessingStatus((prev) => ({
              ...prev,
              cacheHit: event.data,
              isProcessing: false,
            }));
            toast.success('Cached response found!');
            break;

          case 'stage1_5_start':
            // Factual verification starting
            setProcessingStatus((prev) => ({
              ...prev,
              verification: { running: true },
            }));
            break;

          case 'stage1_5_complete':
            // Factual verification complete
            setProcessingStatus((prev) => ({
              ...prev,
              verification: event.data?.skipped
                ? null
                : { ...event.data, running: false },
            }));
            if (event.data?.contradiction_count > 0) {
              toast.warning(`${event.data.contradiction_count} contradiction(s) detected between models`);
            }
            break;

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
              // Initialize stage3 with empty streaming response
              lastMsg.stage3 = { model: '', response: '', isStreaming: true };
              return { ...prev, messages };
            });
            break;

          case 'stage3_token':
            // Append token to the streaming response
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              if (lastMsg.stage3) {
                lastMsg.stage3 = {
                  ...lastMsg.stage3,
                  response: lastMsg.stage3.response + event.token,
                };
              }
              return { ...prev, messages };
            });
            break;

          case 'stage3_complete':
            setStage3Result(event.data);
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              // Set final response and mark streaming as complete
              lastMsg.stage3 = { ...event.data, isStreaming: false };
              lastMsg.loading.stage3 = false;
              return { ...prev, messages };
            });
            break;

          case 'cost_summary':
            // Store cost data in the message metadata
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.costSummary = event.data;
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
            // Keep status visible for a moment, then clear
            setTimeout(() => {
              setProcessingStatus((prev) => prev ? { ...prev, isProcessing: false } : null);
            }, 500);
            break;

          case 'error':
            console.error('Stream error:', event.message);
            toast.error(event.message || 'An error occurred during processing');
            setIsLoading(false);
            setProcessing(false);
            break;

          default:
            console.log('Unknown event type:', eventType);
        }
      });
    } catch (error) {
      console.error('Failed to send message:', error);
      toast.error('Failed to send message. Please try again.');
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
        onDeleteConversation={handleDeleteConversation}
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
          <div className="toggle-group">
            <button
              className="analytics-btn"
              onClick={() => setShowAnalytics(true)}
              title="View Analytics"
            >
              <span className="toggle-icon">📊</span>
              <span className="toggle-label">Analytics</span>
            </button>
            <button
              className="analytics-btn"
              onClick={() => setShowMemoryManager(true)}
              title="Memory Bank"
            >
              <span className="toggle-icon">🧠</span>
              <span className="toggle-label">Memory</span>
            </button>
          </div>
          <div className="toggle-group">
            <button
              className="config-btn"
              onClick={() => setShowCouncilBuilder(true)}
              title="Configure Council"
            >
              <span className="toggle-icon">⚙️</span>
              <span className="toggle-label">Council</span>
            </button>
            <button
              className={`config-btn ${showCollaboration ? 'active' : ''}`}
              onClick={() => setShowCollaboration(!showCollaboration)}
              title="Real-time Collaboration"
            >
              <span className="toggle-icon">👥</span>
              <span className="toggle-label">Collab</span>
            </button>
            <button
              className="config-btn"
              onClick={() => setShowPluginManager(true)}
              title="Plugin Manager"
            >
              <span className="toggle-icon">🔌</span>
              <span className="toggle-label">Plugins</span>
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
            processingStatus={processingStatus}
          />
        )}

        {/* Voice Controller (renders regardless of mode) */}
        {voiceEnabled && <VoiceController />}
      </div>

      {/* Toast Notifications */}
      <Toast />

      {/* Analytics Dashboard */}
      <AnalyticsDashboard
        isOpen={showAnalytics}
        onClose={() => setShowAnalytics(false)}
      />

      {/* Council Builder */}
      <CouncilBuilder
        isOpen={showCouncilBuilder}
        onClose={() => setShowCouncilBuilder(false)}
        onApply={async (config) => {
          try {
            const response = await fetch(
              `${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api/config`,
              {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config),
              }
            );
            if (response.ok) {
              toast.success('Council configuration updated');
            } else {
              toast.error('Failed to update configuration');
            }
          } catch (error) {
            console.error('Failed to update config:', error);
            toast.error('Failed to update configuration');
          }
        }}
      />

      {/* Memory Manager */}
      <MemoryManager
        isOpen={showMemoryManager}
        onClose={() => setShowMemoryManager(false)}
      />

      {/* Collaboration Panel */}
      <CollaborationPanel
        conversationId={currentConversationId}
        isOpen={showCollaboration}
        onClose={() => setShowCollaboration(false)}
        onNewMessage={(msg) => {
          // Handle incoming collaborative messages
          console.log('Collaborative message:', msg);
        }}
      />

      {/* Plugin Manager */}
      <PluginManager
        isOpen={showPluginManager}
        onClose={() => setShowPluginManager(false)}
      />
    </div>
  );
}

export default App;
