import React, { useRef, useState } from 'react';
import '../styles/EvidenceDropzone.css';
import { UploadCloud } from 'lucide-react';

export default function EvidenceDropzone({ onFilesSelected, isUploading, progress }) {
  const [isDragOver, setIsDragOver] = useState(false);
  const inputRef = useRef(null);

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onFilesSelected(e.dataTransfer.files);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };
  
  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      onFilesSelected(e.target.files);
    }
  };

  return (
    <div 
      className={`evidence-dropzone ${isDragOver ? 'drag-over' : ''} ${isUploading ? 'uploading' : ''}`}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onClick={() => !isUploading && inputRef.current?.click()}
      onKeyDown={(e) => {
        if (!isUploading && (e.key === 'Enter' || e.key === ' ')) {
          e.preventDefault();
          inputRef.current?.click();
        }
      }}
      tabIndex={0}
      role="button"
      aria-label="Upload evidence files"
    >
      <input 
        type="file" 
        ref={inputRef} 
        onChange={handleChange} 
        style={{ display: 'none' }} 
        multiple
      />
      
      {isUploading ? (
        <div className="upload-state">
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${progress * 100}%` }}></div>
          </div>
          <p>Uploading... {Math.round(progress * 100)}%</p>
        </div>
      ) : (
        <div className="dropzone-content">
          <UploadCloud size={32} />
          <p>Drag and drop files here, or click to browse</p>
        </div>
      )}
    </div>
  );
}
