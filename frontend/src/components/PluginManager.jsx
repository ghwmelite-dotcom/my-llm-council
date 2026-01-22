import { useState, useEffect } from 'react';
import './PluginManager.css';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8001';

export default function PluginManager({ isOpen, onClose }) {
  const [plugins, setPlugins] = useState([]);
  const [builtinPlugins, setBuiltinPlugins] = useState([]);
  const [loading, setLoading] = useState(false);
  const [expandedPlugin, setExpandedPlugin] = useState(null);

  useEffect(() => {
    if (isOpen) {
      loadPlugins();
    }
  }, [isOpen]);

  const loadPlugins = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/plugins`);
      if (response.ok) {
        const data = await response.json();
        setPlugins(data.plugins || []);
        setBuiltinPlugins(data.available_builtin || []);
      }
    } catch (error) {
      console.error('Failed to load plugins:', error);
    }
    setLoading(false);
  };

  const togglePlugin = async (pluginName, currentEnabled) => {
    try {
      const action = currentEnabled ? 'disable' : 'enable';
      const response = await fetch(`${API_BASE}/api/plugins/${pluginName}/${action}`, {
        method: 'POST'
      });
      if (response.ok) {
        loadPlugins();
      }
    } catch (error) {
      console.error('Failed to toggle plugin:', error);
    }
  };

  const registerPlugin = async (pluginName) => {
    try {
      const response = await fetch(`${API_BASE}/api/plugins/builtin/${pluginName}/register`, {
        method: 'POST'
      });
      if (response.ok) {
        loadPlugins();
      }
    } catch (error) {
      console.error('Failed to register plugin:', error);
    }
  };

  const unregisterPlugin = async (pluginName) => {
    if (!confirm(`Unregister ${pluginName}?`)) return;

    try {
      const response = await fetch(`${API_BASE}/api/plugins/${pluginName}`, {
        method: 'DELETE'
      });
      if (response.ok) {
        loadPlugins();
      }
    } catch (error) {
      console.error('Failed to unregister plugin:', error);
    }
  };

  const getHookBadgeColor = (hook) => {
    const colors = {
      'on_query_received': '#4a90e2',
      'on_stage1_complete': '#22c55e',
      'on_stage2_complete': '#f59e0b',
      'on_synthesis_complete': '#a855f7',
      'on_response_complete': '#ec4899',
    };
    return colors[hook] || '#6b7280';
  };

  const isRegistered = (pluginName) => {
    return plugins.some(p => p.name === pluginName);
  };

  if (!isOpen) return null;

  return (
    <div className="plugin-overlay" onClick={onClose}>
      <div className="plugin-manager" onClick={(e) => e.stopPropagation()}>
        <div className="plugin-header">
          <h2>Plugin Manager</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="plugin-content">
          {loading ? (
            <div className="loading">Loading plugins...</div>
          ) : (
            <>
              {/* Registered Plugins */}
              <div className="plugin-section">
                <h3>Active Plugins ({plugins.length})</h3>
                {plugins.length === 0 ? (
                  <p className="empty-text">No plugins registered. Enable one from the available plugins below.</p>
                ) : (
                  <div className="plugin-list">
                    {plugins.map((plugin) => (
                      <div
                        key={plugin.name}
                        className={`plugin-card ${plugin.enabled ? 'enabled' : 'disabled'}`}
                      >
                        <div className="plugin-card-header">
                          <div className="plugin-info">
                            <span className="plugin-name">{plugin.name}</span>
                            <span className="plugin-version">v{plugin.version}</span>
                          </div>
                          <div className="plugin-actions">
                            <label className="toggle-switch">
                              <input
                                type="checkbox"
                                checked={plugin.enabled}
                                onChange={() => togglePlugin(plugin.name, plugin.enabled)}
                              />
                              <span className="toggle-slider"></span>
                            </label>
                          </div>
                        </div>
                        <p className="plugin-description">{plugin.description}</p>
                        <div className="plugin-hooks">
                          {plugin.hooks?.map((hook) => (
                            <span
                              key={hook}
                              className="hook-badge"
                              style={{ backgroundColor: getHookBadgeColor(hook) }}
                            >
                              {hook.replace('on_', '').replace(/_/g, ' ')}
                            </span>
                          ))}
                        </div>
                        <div className="plugin-footer">
                          <span className="plugin-author">by {plugin.author}</span>
                          <button
                            className="unregister-btn"
                            onClick={() => unregisterPlugin(plugin.name)}
                          >
                            Remove
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Available Built-in Plugins */}
              <div className="plugin-section">
                <h3>Available Built-in Plugins</h3>
                <div className="builtin-list">
                  {builtinPlugins.map((plugin) => (
                    <div
                      key={plugin.name}
                      className={`builtin-card ${isRegistered(plugin.name) ? 'registered' : ''}`}
                    >
                      <div className="builtin-info">
                        <span className="builtin-name">{plugin.name}</span>
                        <p className="builtin-desc">{plugin.description}</p>
                      </div>
                      {isRegistered(plugin.name) ? (
                        <span className="registered-badge">Active</span>
                      ) : (
                        <button
                          className="add-btn"
                          onClick={() => registerPlugin(plugin.name)}
                        >
                          Add
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
