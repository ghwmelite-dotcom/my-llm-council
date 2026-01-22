import { useState } from 'react';
import './Sidebar.css';

export default function Sidebar({
  conversations,
  currentConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(null);

  const handleSelectConversation = (id) => {
    onSelectConversation(id);
    setIsOpen(false);
  };

  const handleNewConversation = () => {
    onNewConversation();
    setIsOpen(false);
  };

  const handleDeleteClick = (e, id) => {
    e.stopPropagation();
    setDeleteConfirm(id);
  };

  const handleConfirmDelete = (e, id) => {
    e.stopPropagation();
    onDeleteConversation(id);
    setDeleteConfirm(null);
  };

  const handleCancelDelete = (e) => {
    e.stopPropagation();
    setDeleteConfirm(null);
  };

  return (
    <>
      <button
        className="sidebar-toggle"
        onClick={() => setIsOpen(!isOpen)}
        aria-label={isOpen ? 'Close sidebar' : 'Open sidebar'}
      >
        {isOpen ? '✕' : '☰'}
      </button>
      <div
        className={`sidebar-overlay ${isOpen ? 'visible' : ''}`}
        onClick={() => setIsOpen(false)}
      />
      <div className={`sidebar ${isOpen ? 'open' : ''}`}>
      <div className="sidebar-header">
        <h1>LLM Council</h1>
        <button className="new-conversation-btn" onClick={handleNewConversation}>
          + New Conversation
        </button>
      </div>

      <div className="conversation-list">
        {conversations.length === 0 ? (
          <div className="no-conversations">No conversations yet</div>
        ) : (
          conversations.map((conv) => (
            <div
              key={conv.id}
              className={`conversation-item ${
                conv.id === currentConversationId ? 'active' : ''
              }`}
              onClick={() => handleSelectConversation(conv.id)}
            >
              <div className="conversation-content">
                <div className="conversation-title">
                  {conv.title || 'New Conversation'}
                </div>
                <div className="conversation-meta">
                  {conv.message_count} messages
                </div>
              </div>
              {deleteConfirm === conv.id ? (
                <div className="delete-confirm">
                  <button
                    className="delete-confirm-btn yes"
                    onClick={(e) => handleConfirmDelete(e, conv.id)}
                    title="Confirm delete"
                  >
                    Yes
                  </button>
                  <button
                    className="delete-confirm-btn no"
                    onClick={handleCancelDelete}
                    title="Cancel"
                  >
                    No
                  </button>
                </div>
              ) : (
                <button
                  className="delete-btn"
                  onClick={(e) => handleDeleteClick(e, conv.id)}
                  title="Delete conversation"
                >
                  <span className="delete-icon">&#x2715;</span>
                </button>
              )}
            </div>
          ))
        )}
      </div>
    </div>
    </>
  );
}
