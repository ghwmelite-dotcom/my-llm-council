import { useState } from 'react';
import { api } from '../api';
import './ExportButton.css';

/**
 * ExportButton - Dropdown for exporting conversations
 */
export default function ExportButton({ conversationId, disabled }) {
  const [isOpen, setIsOpen] = useState(false);
  const [exporting, setExporting] = useState(false);

  const downloadBlob = (blob, filename) => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleExport = async (format) => {
    if (!conversationId || exporting) return;

    setExporting(true);
    setIsOpen(false);

    try {
      if (format === 'markdown') {
        const { blob, filename } = await api.exportMarkdown(conversationId);
        downloadBlob(blob, filename);
      } else if (format === 'html') {
        const { blob, filename } = await api.exportHtml(conversationId);
        downloadBlob(blob, filename);
      } else if (format === 'pdf') {
        // Export HTML and open in new tab for printing
        const { blob } = await api.exportHtml(conversationId);
        const url = URL.createObjectURL(blob);
        const printWindow = window.open(url, '_blank');
        if (printWindow) {
          printWindow.onload = () => {
            printWindow.print();
          };
        }
      }
    } catch (error) {
      console.error('Export failed:', error);
      alert('Failed to export conversation');
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="export-button-container">
      <button
        className={`export-button ${isOpen ? 'open' : ''}`}
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled || exporting}
        title="Export conversation"
      >
        {exporting ? (
          <span className="export-icon spinning">⏳</span>
        ) : (
          <span className="export-icon">📥</span>
        )}
        <span className="export-label">Export</span>
        <span className="dropdown-arrow">▼</span>
      </button>

      {isOpen && (
        <div className="export-dropdown">
          <button
            className="export-option"
            onClick={() => handleExport('markdown')}
          >
            <span className="option-icon">📝</span>
            <span className="option-label">Markdown (.md)</span>
          </button>
          <button
            className="export-option"
            onClick={() => handleExport('html')}
          >
            <span className="option-icon">🌐</span>
            <span className="option-label">HTML</span>
          </button>
          <button
            className="export-option"
            onClick={() => handleExport('pdf')}
          >
            <span className="option-icon">📄</span>
            <span className="option-label">Print / PDF</span>
          </button>
        </div>
      )}
    </div>
  );
}
