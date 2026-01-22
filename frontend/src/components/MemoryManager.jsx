import { useState, useEffect } from 'react';
import './MemoryManager.css';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8001';

const MEMORY_TYPES = ['fact', 'preference', 'decision', 'insight', 'relationship'];

export default function MemoryManager({ isOpen, onClose }) {
  const [memories, setMemories] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState({ type: '', search: '' });
  const [editingMemory, setEditingMemory] = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newMemory, setNewMemory] = useState({
    content: '',
    memory_type: 'insight',
    tags: '',
    importance: 0.5
  });

  useEffect(() => {
    if (isOpen) {
      loadMemories();
      loadStats();
    }
  }, [isOpen]);

  const loadMemories = async () => {
    setLoading(true);
    try {
      let url = `${API_BASE}/api/memories?limit=100`;
      if (filter.type) url += `&memory_type=${filter.type}`;

      const response = await fetch(url);
      if (response.ok) {
        const data = await response.json();
        setMemories(data.memories);
      }
    } catch (error) {
      console.error('Failed to load memories:', error);
    }
    setLoading(false);
  };

  const loadStats = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/memories/stats`);
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const handleSearch = async () => {
    if (!filter.search.trim()) {
      loadMemories();
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(
        `${API_BASE}/api/memories/search?query=${encodeURIComponent(filter.search)}&limit=50`
      );
      if (response.ok) {
        const data = await response.json();
        setMemories(data.memories);
      }
    } catch (error) {
      console.error('Failed to search memories:', error);
    }
    setLoading(false);
  };

  const handleAddMemory = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/memories`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: newMemory.content,
          memory_type: newMemory.memory_type,
          tags: newMemory.tags.split(',').map(t => t.trim()).filter(t => t),
          importance: newMemory.importance
        })
      });
      if (response.ok) {
        setShowAddForm(false);
        setNewMemory({ content: '', memory_type: 'insight', tags: '', importance: 0.5 });
        loadMemories();
        loadStats();
      }
    } catch (error) {
      console.error('Failed to add memory:', error);
    }
  };

  const handleUpdateMemory = async (memoryId) => {
    try {
      const response = await fetch(`${API_BASE}/api/memories/${memoryId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: editingMemory.content,
          memory_type: editingMemory.type,
          importance: editingMemory.importance
        })
      });
      if (response.ok) {
        setEditingMemory(null);
        loadMemories();
      }
    } catch (error) {
      console.error('Failed to update memory:', error);
    }
  };

  const handleDeleteMemory = async (memoryId) => {
    if (!confirm('Delete this memory?')) return;

    try {
      const response = await fetch(`${API_BASE}/api/memories/${memoryId}`, {
        method: 'DELETE'
      });
      if (response.ok) {
        loadMemories();
        loadStats();
      }
    } catch (error) {
      console.error('Failed to delete memory:', error);
    }
  };

  const formatDate = (isoString) => {
    return new Date(isoString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const getTypeColor = (type) => {
    const colors = {
      fact: '#4a90e2',
      preference: '#22c55e',
      decision: '#f59e0b',
      insight: '#a855f7',
      relationship: '#ec4899'
    };
    return colors[type] || '#6b7280';
  };

  if (!isOpen) return null;

  return (
    <div className="memory-overlay" onClick={onClose}>
      <div className="memory-manager" onClick={(e) => e.stopPropagation()}>
        <div className="memory-header">
          <h2>Council Memory Bank</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        {/* Stats Section */}
        {stats && (
          <div className="memory-stats">
            <div className="stat-item">
              <span className="stat-value">{stats.total_memories}</span>
              <span className="stat-label">Total Memories</span>
            </div>
            {Object.entries(stats.by_type || {}).map(([type, count]) => (
              <div
                key={type}
                className="stat-item type-stat"
                style={{ borderColor: getTypeColor(type) }}
              >
                <span className="stat-value">{count}</span>
                <span className="stat-label">{type}</span>
              </div>
            ))}
          </div>
        )}

        {/* Controls */}
        <div className="memory-controls">
          <div className="search-row">
            <input
              type="text"
              placeholder="Search memories..."
              value={filter.search}
              onChange={(e) => setFilter({ ...filter, search: e.target.value })}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            />
            <button onClick={handleSearch}>Search</button>
          </div>
          <div className="filter-row">
            <select
              value={filter.type}
              onChange={(e) => {
                setFilter({ ...filter, type: e.target.value });
                setTimeout(loadMemories, 0);
              }}
            >
              <option value="">All Types</option>
              {MEMORY_TYPES.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
            <button className="add-btn" onClick={() => setShowAddForm(true)}>
              + Add Memory
            </button>
          </div>
        </div>

        {/* Add Memory Form */}
        {showAddForm && (
          <div className="add-memory-form">
            <h3>Add New Memory</h3>
            <textarea
              placeholder="Memory content..."
              value={newMemory.content}
              onChange={(e) => setNewMemory({ ...newMemory, content: e.target.value })}
            />
            <div className="form-row">
              <select
                value={newMemory.memory_type}
                onChange={(e) => setNewMemory({ ...newMemory, memory_type: e.target.value })}
              >
                {MEMORY_TYPES.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
              <input
                type="text"
                placeholder="Tags (comma-separated)"
                value={newMemory.tags}
                onChange={(e) => setNewMemory({ ...newMemory, tags: e.target.value })}
              />
            </div>
            <div className="form-row">
              <label>
                Importance: {newMemory.importance.toFixed(1)}
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={newMemory.importance}
                  onChange={(e) => setNewMemory({ ...newMemory, importance: parseFloat(e.target.value) })}
                />
              </label>
            </div>
            <div className="form-actions">
              <button onClick={() => setShowAddForm(false)}>Cancel</button>
              <button
                className="primary"
                onClick={handleAddMemory}
                disabled={!newMemory.content.trim()}
              >
                Save Memory
              </button>
            </div>
          </div>
        )}

        {/* Memory List */}
        <div className="memory-list">
          {loading ? (
            <div className="loading">Loading memories...</div>
          ) : memories.length === 0 ? (
            <div className="empty-state">
              <p>No memories found</p>
              <p className="hint">Memories are automatically extracted from council discussions, or you can add them manually.</p>
            </div>
          ) : (
            memories.map((memory) => (
              <div key={memory.id} className="memory-card">
                {editingMemory?.id === memory.id ? (
                  <div className="editing-form">
                    <textarea
                      value={editingMemory.content}
                      onChange={(e) => setEditingMemory({ ...editingMemory, content: e.target.value })}
                    />
                    <div className="edit-actions">
                      <button onClick={() => setEditingMemory(null)}>Cancel</button>
                      <button className="primary" onClick={() => handleUpdateMemory(memory.id)}>Save</button>
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="memory-top">
                      <span
                        className="memory-type"
                        style={{ backgroundColor: getTypeColor(memory.type) }}
                      >
                        {memory.type}
                      </span>
                      <span className="memory-date">{formatDate(memory.created_at)}</span>
                    </div>
                    <p className="memory-content">{memory.content}</p>
                    {memory.tags?.length > 0 && (
                      <div className="memory-tags">
                        {memory.tags.map((tag, i) => (
                          <span key={i} className="tag">{tag}</span>
                        ))}
                      </div>
                    )}
                    <div className="memory-footer">
                      <span className="importance">
                        Importance: {(memory.importance * 100).toFixed(0)}%
                      </span>
                      {memory.access_count > 0 && (
                        <span className="access-count">
                          Accessed {memory.access_count}x
                        </span>
                      )}
                      <div className="memory-actions">
                        <button onClick={() => setEditingMemory(memory)}>Edit</button>
                        <button className="delete" onClick={() => handleDeleteMemory(memory.id)}>
                          Delete
                        </button>
                      </div>
                    </div>
                  </>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
