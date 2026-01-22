import { useState, useEffect, useRef, useCallback } from 'react';
import './CollaborationPanel.css';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8001';
const WS_BASE = API_BASE.replace('http', 'ws');

export default function CollaborationPanel({
  conversationId,
  isOpen,
  onClose,
  onNewMessage
}) {
  const [connected, setConnected] = useState(false);
  const [users, setUsers] = useState([]);
  const [room, setRoom] = useState(null);
  const [inviteCode, setInviteCode] = useState('');
  const [typingUsers, setTypingUsers] = useState([]);
  const [userId] = useState(() => `user-${Date.now()}`);
  const [username, setUsername] = useState(() =>
    localStorage.getItem('llm-council-username') || `User-${Date.now().toString(36).slice(-4)}`
  );
  const [showSettings, setShowSettings] = useState(false);
  const wsRef = useRef(null);
  const reconnectTimeout = useRef(null);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (!conversationId || wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(
      `${WS_BASE}/ws/collaborate/${conversationId}?user_id=${userId}&username=${encodeURIComponent(username)}`
    );

    ws.onopen = () => {
      setConnected(true);
      // Clear any reconnect timeout
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
        reconnectTimeout.current = null;
      }
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleMessage(data);
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
      }
    };

    ws.onclose = () => {
      setConnected(false);
      // Attempt to reconnect after a delay
      reconnectTimeout.current = setTimeout(() => {
        if (isOpen) connect();
      }, 3000);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    wsRef.current = ws;
  }, [conversationId, userId, username, isOpen]);

  const handleMessage = (data) => {
    switch (data.type) {
      case 'user_joined':
      case 'user_left':
        setUsers(data.users || []);
        break;

      case 'typing':
        if (data.is_typing) {
          setTypingUsers((prev) => [...prev.filter(u => u !== data.username), data.username]);
        } else {
          setTypingUsers((prev) => prev.filter(u => u !== data.username));
        }
        break;

      case 'new_message':
        if (onNewMessage) {
          onNewMessage(data);
        }
        break;

      case 'stage_update':
        // Handle stage updates from other users
        break;

      default:
        break;
    }
  };

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
      reconnectTimeout.current = null;
    }
    setConnected(false);
    setUsers([]);
  }, []);

  useEffect(() => {
    if (isOpen && conversationId) {
      connect();
    } else {
      disconnect();
    }

    return () => disconnect();
  }, [isOpen, conversationId, connect, disconnect]);

  // Create or get room
  const createRoom = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/conversations/${conversationId}/room`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: `Collaboration Room`,
          is_public: false,
          max_users: 10
        })
      });
      if (response.ok) {
        const data = await response.json();
        setRoom(data);
        setInviteCode(data.invite_code);
      }
    } catch (error) {
      console.error('Failed to create room:', error);
    }
  };

  // Copy invite link
  const copyInviteLink = () => {
    const link = `${window.location.origin}?join=${inviteCode}`;
    navigator.clipboard.writeText(link);
  };

  // Send typing indicator
  const sendTyping = (isTyping) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'typing',
        is_typing: isTyping
      }));
    }
  };

  // Save username
  const saveUsername = (newUsername) => {
    setUsername(newUsername);
    localStorage.setItem('llm-council-username', newUsername);
    // Reconnect with new username
    disconnect();
    setTimeout(connect, 100);
  };

  if (!isOpen) return null;

  return (
    <div className="collab-panel">
      <div className="collab-header">
        <h3>Collaboration</h3>
        <div className="collab-status">
          <span className={`status-dot ${connected ? 'connected' : 'disconnected'}`} />
          <span>{connected ? 'Connected' : 'Disconnected'}</span>
        </div>
        <button className="close-btn" onClick={onClose}>×</button>
      </div>

      {/* Settings */}
      {showSettings ? (
        <div className="collab-settings">
          <h4>Your Settings</h4>
          <label>
            Display Name
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              onBlur={(e) => saveUsername(e.target.value)}
            />
          </label>
          <button onClick={() => setShowSettings(false)}>Done</button>
        </div>
      ) : (
        <>
          {/* User List */}
          <div className="collab-users">
            <div className="section-header">
              <span>Users ({users.length})</span>
              <button className="settings-btn" onClick={() => setShowSettings(true)}>
                Settings
              </button>
            </div>
            {users.length === 0 ? (
              <p className="empty-text">No other users connected</p>
            ) : (
              <ul className="user-list">
                {users.map((user) => (
                  <li key={user.user_id} className="user-item">
                    <span
                      className="user-avatar"
                      style={{ backgroundColor: user.color }}
                    >
                      {user.username[0].toUpperCase()}
                    </span>
                    <span className="user-name">
                      {user.username}
                      {user.user_id === userId && ' (You)'}
                    </span>
                    {typingUsers.includes(user.username) && (
                      <span className="typing-indicator">typing...</span>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Invite Section */}
          <div className="collab-invite">
            <div className="section-header">
              <span>Invite Others</span>
            </div>
            {inviteCode ? (
              <div className="invite-code">
                <input type="text" readOnly value={inviteCode} />
                <button onClick={copyInviteLink}>Copy Link</button>
              </div>
            ) : (
              <button className="create-room-btn" onClick={createRoom}>
                Create Shareable Link
              </button>
            )}
          </div>
        </>
      )}
    </div>
  );
}

// Export utility hook for typing indicator
export function useCollabTyping(sendTyping) {
  const typingTimeout = useRef(null);

  const handleTyping = useCallback(() => {
    sendTyping(true);

    if (typingTimeout.current) {
      clearTimeout(typingTimeout.current);
    }

    typingTimeout.current = setTimeout(() => {
      sendTyping(false);
    }, 2000);
  }, [sendTyping]);

  return handleTyping;
}
