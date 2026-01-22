import { useState, useEffect } from 'react';
import './AuthModal.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';

export default function AuthModal({ isOpen, onClose, onLogin }) {
  const [mode, setMode] = useState('login'); // 'login' or 'register'
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [usernameAvailable, setUsernameAvailable] = useState(null);
  const [checkingUsername, setCheckingUsername] = useState(false);

  // Debounced username availability check
  useEffect(() => {
    if (mode !== 'register' || username.length < 3) {
      setUsernameAvailable(null);
      return;
    }

    const timer = setTimeout(async () => {
      setCheckingUsername(true);
      try {
        const response = await fetch(`${API_URL}/api/auth/check-username/${encodeURIComponent(username)}`);
        const data = await response.json();
        setUsernameAvailable(data.available);
      } catch (err) {
        console.error('Failed to check username:', err);
        setUsernameAvailable(null);
      } finally {
        setCheckingUsername(false);
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [username, mode]);

  const resetForm = () => {
    setUsername('');
    setPassword('');
    setConfirmPassword('');
    setDisplayName('');
    setError('');
    setUsernameAvailable(null);
  };

  const handleModeSwitch = (newMode) => {
    setMode(newMode);
    resetForm();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      if (mode === 'register') {
        // Validation
        if (username.length < 3) {
          setError('Username must be at least 3 characters');
          setIsLoading(false);
          return;
        }
        if (password.length < 6) {
          setError('Password must be at least 6 characters');
          setIsLoading(false);
          return;
        }
        if (password !== confirmPassword) {
          setError('Passwords do not match');
          setIsLoading(false);
          return;
        }
        if (usernameAvailable === false) {
          setError('Username is already taken');
          setIsLoading(false);
          return;
        }

        const response = await fetch(`${API_URL}/api/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            username,
            password,
            display_name: displayName || username,
          }),
        });

        if (!response.ok) {
          const data = await response.json();
          throw new Error(data.detail || 'Registration failed');
        }

        const data = await response.json();
        onLogin(data.token, data.user);
        onClose();
      } else {
        // Login
        const response = await fetch(`${API_URL}/api/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, password }),
        });

        if (!response.ok) {
          const data = await response.json();
          throw new Error(data.detail || 'Login failed');
        }

        const data = await response.json();
        onLogin(data.token, data.user);
        onClose();
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="auth-modal-overlay" onClick={onClose}>
      <div className="auth-modal" onClick={(e) => e.stopPropagation()}>
        <button className="auth-modal-close" onClick={onClose}>
          &times;
        </button>

        <div className="auth-modal-header">
          <div className="auth-logo">
            <span className="auth-logo-icon">🏛️</span>
            <span className="auth-logo-text">LLM Council</span>
          </div>
          <h2>{mode === 'login' ? 'Welcome Back' : 'Join the Council'}</h2>
          <p className="auth-subtitle">
            {mode === 'login'
              ? 'Sign in to access your conversations and preferences'
              : 'Create an account to save your conversations and customize your experience'}
          </p>
        </div>

        <div className="auth-tabs">
          <button
            className={`auth-tab ${mode === 'login' ? 'active' : ''}`}
            onClick={() => handleModeSwitch('login')}
          >
            Sign In
          </button>
          <button
            className={`auth-tab ${mode === 'register' ? 'active' : ''}`}
            onClick={() => handleModeSwitch('register')}
          >
            Register
          </button>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="auth-field">
            <label htmlFor="username">Username</label>
            <div className="auth-input-wrapper">
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter your username"
                autoComplete="username"
                required
                minLength={3}
                maxLength={30}
              />
              {mode === 'register' && username.length >= 3 && (
                <span className={`username-status ${checkingUsername ? 'checking' : usernameAvailable ? 'available' : 'taken'}`}>
                  {checkingUsername ? '...' : usernameAvailable ? '✓' : '✗'}
                </span>
              )}
            </div>
            {mode === 'register' && username.length >= 3 && !checkingUsername && usernameAvailable === false && (
              <span className="auth-field-error">Username is already taken</span>
            )}
          </div>

          {mode === 'register' && (
            <div className="auth-field">
              <label htmlFor="displayName">Display Name (optional)</label>
              <input
                id="displayName"
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="How should we call you?"
                maxLength={50}
              />
            </div>
          )}

          <div className="auth-field">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={mode === 'register' ? 'Create a password (min 6 characters)' : 'Enter your password'}
              autoComplete={mode === 'register' ? 'new-password' : 'current-password'}
              required
              minLength={6}
            />
          </div>

          {mode === 'register' && (
            <div className="auth-field">
              <label htmlFor="confirmPassword">Confirm Password</label>
              <input
                id="confirmPassword"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Confirm your password"
                autoComplete="new-password"
                required
              />
              {password && confirmPassword && password !== confirmPassword && (
                <span className="auth-field-error">Passwords do not match</span>
              )}
            </div>
          )}

          {error && <div className="auth-error">{error}</div>}

          <button
            type="submit"
            className="auth-submit"
            disabled={isLoading || (mode === 'register' && usernameAvailable === false)}
          >
            {isLoading ? (
              <span className="auth-loading">
                <span className="spinner"></span>
                {mode === 'login' ? 'Signing in...' : 'Creating account...'}
              </span>
            ) : mode === 'login' ? (
              'Sign In'
            ) : (
              'Create Account'
            )}
          </button>
        </form>

        <div className="auth-footer">
          {mode === 'login' ? (
            <p>
              Don't have an account?{' '}
              <button type="button" onClick={() => handleModeSwitch('register')}>
                Register now
              </button>
            </p>
          ) : (
            <p>
              Already have an account?{' '}
              <button type="button" onClick={() => handleModeSwitch('login')}>
                Sign in
              </button>
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
