import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import Stage1 from './Stage1';
import Stage2 from './Stage2';
import Stage3 from './Stage3';
import StageSkeleton from './StageSkeleton';
import ProcessingStatus from './ProcessingStatus';
import CostDisplay from './CostDisplay';
import ExportButton from './ExportButton';
import QueryTemplates from './QueryTemplates';
import FeedbackWidget from './FeedbackWidget';
import ImageUpload from './ImageUpload';
import './ChatInterface.css';

export default function ChatInterface({
  conversation,
  onSendMessage,
  isLoading,
  processingStatus,
}) {
  const [input, setInput] = useState('');
  const [imageIds, setImageIds] = useState([]);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [conversation]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSendMessage(input, imageIds.length > 0 ? imageIds : null);
      setInput('');
      setImageIds([]);
    }
  };

  const handleKeyDown = (e) => {
    // Submit on Enter (without Shift)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  if (!conversation) {
    return (
      <div className="chat-interface">
        <div className="empty-state">
          <h2>Welcome to LLM Council</h2>
          <p>Create a new conversation to get started</p>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-interface">
      {/* Conversation Header with Export */}
      {conversation.messages.length > 0 && (
        <div className="conversation-header">
          <div className="header-actions">
            <ExportButton
              conversationId={conversation.id}
              disabled={isLoading}
            />
          </div>
        </div>
      )}

      <div className="messages-container">
        {conversation.messages.length === 0 ? (
          <div className="empty-state">
            <h2>Start a conversation</h2>
            <p>Ask a question to consult the LLM Council</p>
          </div>
        ) : (
          conversation.messages.map((msg, index) => (
            <div key={index} className="message-group">
              {msg.role === 'user' ? (
                <div className="user-message">
                  <div className="message-label">You</div>
                  <div className="message-content">
                    <div className="markdown-content">
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="assistant-message">
                  <div className="message-label">LLM Council</div>

                  {/* Stage 1 */}
                  {msg.loading?.stage1 && !msg.stage1 && (
                    <StageSkeleton stage={1} />
                  )}
                  {msg.stage1 && <Stage1 responses={msg.stage1} />}

                  {/* Stage 2 */}
                  {msg.loading?.stage2 && !msg.stage2 && (
                    <StageSkeleton stage={2} />
                  )}
                  {msg.stage2 && (
                    <Stage2
                      rankings={msg.stage2}
                      labelToModel={msg.metadata?.label_to_model}
                      aggregateRankings={msg.metadata?.aggregate_rankings}
                    />
                  )}

                  {/* Stage 3 */}
                  {msg.loading?.stage3 && !msg.stage3 && (
                    <StageSkeleton stage={3} />
                  )}
                  {msg.stage3 && <Stage3 finalResponse={msg.stage3} />}

                  {/* Cost Display */}
                  {msg.costSummary && <CostDisplay costSummary={msg.costSummary} />}

                  {/* Feedback Widget - show after Stage 3 is complete */}
                  {msg.stage3 && !msg.stage3.isStreaming && conversation.id && (
                    <FeedbackWidget
                      conversationId={conversation.id}
                      messageIndex={index}
                    />
                  )}
                </div>
              )}
            </div>
          ))
        )}

        {/* Processing Status Bar */}
        {isLoading && processingStatus && (
          <ProcessingStatus status={processingStatus} />
        )}

        {isLoading && !processingStatus?.cacheHit && (
          <div className="loading-indicator">
            <div className="spinner"></div>
            <span>Consulting the council...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {conversation.messages.length === 0 && (
        <div className="input-section">
          <div className="input-container">
            {/* Toolbar above input */}
            <div className="input-toolbar">
              <div className="toolbar-left">
                <QueryTemplates
                  onSelectTemplate={(template) => setInput(template)}
                  disabled={isLoading}
                />
                <ImageUpload
                  onImagesChange={setImageIds}
                  disabled={isLoading}
                />
              </div>
            </div>

            {/* Input form */}
            <form className="input-form" onSubmit={handleSubmit}>
              <div className="input-wrapper">
                <textarea
                  className="message-input"
                  placeholder="Ask your question... (Shift+Enter for new line, Enter to send)"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  disabled={isLoading}
                  rows={3}
                />
                <button
                  type="submit"
                  className="send-button"
                  disabled={!input.trim() || isLoading}
                >
                  <span className="send-icon">↑</span>
                  <span className="send-text">Send</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
