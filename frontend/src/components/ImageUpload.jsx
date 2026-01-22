import { useState, useRef } from 'react';
import './ImageUpload.css';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8001';

export default function ImageUpload({ onImagesChange, disabled }) {
  const [images, setImages] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  const handleFileSelect = async (event) => {
    const files = Array.from(event.target.files);
    if (files.length === 0) return;

    // Validate file count
    if (images.length + files.length > 4) {
      setError('Maximum 4 images allowed');
      return;
    }

    setUploading(true);
    setError('');

    const newImages = [];

    for (const file of files) {
      // Validate file type
      if (!file.type.startsWith('image/')) {
        setError(`${file.name} is not an image`);
        continue;
      }

      // Validate file size (10MB max)
      if (file.size > 10 * 1024 * 1024) {
        setError(`${file.name} is too large (max 10MB)`);
        continue;
      }

      try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE}/api/images/upload`, {
          method: 'POST',
          body: formData
        });

        if (response.ok) {
          const data = await response.json();

          // Get thumbnail
          const thumbResponse = await fetch(`${API_BASE}/api/images/${data.id}/thumbnail`);
          const thumbData = await thumbResponse.json();

          newImages.push({
            id: data.id,
            filename: data.filename,
            size: data.size_bytes,
            dataUrl: thumbData.data_url
          });
        } else {
          const errorData = await response.json();
          setError(errorData.detail || 'Upload failed');
        }
      } catch (err) {
        console.error('Upload error:', err);
        setError('Failed to upload image');
      }
    }

    if (newImages.length > 0) {
      const updatedImages = [...images, ...newImages];
      setImages(updatedImages);
      onImagesChange(updatedImages.map(img => img.id));
    }

    setUploading(false);

    // Clear the input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleRemoveImage = async (imageId) => {
    try {
      await fetch(`${API_BASE}/api/images/${imageId}`, {
        method: 'DELETE'
      });
    } catch (err) {
      console.error('Delete error:', err);
    }

    const updatedImages = images.filter(img => img.id !== imageId);
    setImages(updatedImages);
    onImagesChange(updatedImages.map(img => img.id));
  };

  const clearAll = async () => {
    for (const img of images) {
      try {
        await fetch(`${API_BASE}/api/images/${img.id}`, {
          method: 'DELETE'
        });
      } catch (err) {
        console.error('Delete error:', err);
      }
    }
    setImages([]);
    onImagesChange([]);
  };

  const formatSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="image-upload">
      {/* Image previews */}
      {images.length > 0 && (
        <div className="image-previews">
          {images.map((image) => (
            <div key={image.id} className="image-preview">
              <img src={image.dataUrl} alt={image.filename} />
              <div className="image-info">
                <span className="filename">{image.filename}</span>
                <span className="size">{formatSize(image.size)}</span>
              </div>
              <button
                className="remove-btn"
                onClick={() => handleRemoveImage(image.id)}
                disabled={disabled}
                title="Remove image"
              >
                ×
              </button>
            </div>
          ))}
          {images.length > 1 && (
            <button className="clear-all-btn" onClick={clearAll} disabled={disabled}>
              Clear all
            </button>
          )}
        </div>
      )}

      {/* Error message */}
      {error && <div className="upload-error">{error}</div>}

      {/* Upload button */}
      {images.length < 4 && (
        <div className="upload-controls">
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/gif,image/webp"
            multiple
            onChange={handleFileSelect}
            disabled={disabled || uploading}
            style={{ display: 'none' }}
            id="image-upload-input"
          />
          <label
            htmlFor="image-upload-input"
            className={`upload-btn ${disabled || uploading ? 'disabled' : ''}`}
          >
            {uploading ? (
              <span className="uploading">Uploading...</span>
            ) : (
              <>
                <span className="upload-icon">📷</span>
                <span className="upload-text">Add Image</span>
              </>
            )}
          </label>
          {images.length === 0 && (
            <span className="upload-hint">Attach images for vision-capable models</span>
          )}
        </div>
      )}
    </div>
  );
}
