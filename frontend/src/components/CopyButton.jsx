import { useState } from 'react';
import { useToastStore } from '../stores/toastStore';
import './CopyButton.css';

export default function CopyButton({ text, label = 'Copy' }) {
  const [copied, setCopied] = useState(false);
  const toast = useToastStore();

  const handleCopy = async (e) => {
    e.stopPropagation();
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      toast.success('Copied to clipboard');
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
      toast.error('Failed to copy to clipboard');
    }
  };

  return (
    <button
      className={`copy-btn ${copied ? 'copied' : ''}`}
      onClick={handleCopy}
      title={copied ? 'Copied!' : label}
    >
      {copied ? (
        <span className="copy-icon">&#x2713;</span>
      ) : (
        <span className="copy-icon">&#x2398;</span>
      )}
      <span className="copy-label">{copied ? 'Copied' : label}</span>
    </button>
  );
}
