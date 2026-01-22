import { useState, useRef, useEffect } from 'react';
import { useUser } from '../../contexts/UserContext';
import './UserProfile.css';

export default function UserProfile({ onShowAuth }) {
  const { user, isAuthenticated, isLoading, logout } = useUser();
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  if (isLoading) {
    return (
      <div className="user-profile-skeleton">
        <div className="skeleton-avatar"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <button className="sign-in-btn" onClick={onShowAuth}>
        <span className="sign-in-icon">👤</span>
        <span>Sign In</span>
      </button>
    );
  }

  const getInitials = (name) => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <div className="user-profile" ref={dropdownRef}>
      <button
        className="user-profile-btn"
        onClick={() => setShowDropdown(!showDropdown)}
        aria-expanded={showDropdown}
        aria-haspopup="true"
      >
        <div
          className="user-avatar"
          style={{ backgroundColor: user.avatar_color }}
        >
          {getInitials(user.display_name || user.username)}
        </div>
        <span className="user-name">{user.display_name || user.username}</span>
        <span className={`dropdown-arrow ${showDropdown ? 'open' : ''}`}>▾</span>
      </button>

      {showDropdown && (
        <div className="user-dropdown">
          <div className="dropdown-header">
            <div
              className="dropdown-avatar"
              style={{ backgroundColor: user.avatar_color }}
            >
              {getInitials(user.display_name || user.username)}
            </div>
            <div className="dropdown-user-info">
              <span className="dropdown-display-name">
                {user.display_name || user.username}
              </span>
              <span className="dropdown-username">@{user.username}</span>
            </div>
          </div>

          <div className="dropdown-divider"></div>

          <div className="dropdown-stats">
            <div className="stat-item">
              <span className="stat-icon">💬</span>
              <span className="stat-value">{user.conversation_count || 0}</span>
              <span className="stat-label">Conversations</span>
            </div>
            <div className="stat-item">
              <span className="stat-icon">📅</span>
              <span className="stat-value">
                {new Date(user.created_at).toLocaleDateString()}
              </span>
              <span className="stat-label">Member since</span>
            </div>
          </div>

          <div className="dropdown-divider"></div>

          <button className="dropdown-item" onClick={() => setShowDropdown(false)}>
            <span className="item-icon">⚙️</span>
            <span>Settings</span>
          </button>

          <button
            className="dropdown-item logout"
            onClick={() => {
              setShowDropdown(false);
              logout();
            }}
          >
            <span className="item-icon">🚪</span>
            <span>Sign Out</span>
          </button>
        </div>
      )}
    </div>
  );
}
