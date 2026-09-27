import React, { useState, useRef } from 'react';

interface FileUploaderProps {
  onAnalyze: (file: File) => void;
  disabled: boolean;
}

export const FileUploader: React.FC<FileUploaderProps> = ({ onAnalyze, disabled }) => {
  const [file, setFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (selectedFile: File | null) => {
    if (selectedFile) {
      setFile(selectedFile);
    }
  };

  const handleDragOver = (e: React.DragEvent) => e.preventDefault();
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="card" style={{ maxWidth: '600px', margin: '0 auto', textAlign: 'center' }}>
      <div
        className="upload-box"
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        style={{ padding: '3rem', border: '2px dashed var(--color-border)', borderRadius: 'var(--radius-md)', marginBottom: '1rem' }}
      >
        <p style={{ fontSize: '1.1rem', color: 'var(--color-text)', marginBottom: '0.5rem' }}>
          {file ? file.name : "Drag and drop your specification document here"}
        </p>
        <input
          type="file"
          ref={fileInputRef}
          onChange={(e) => e.target.files && handleFileChange(e.target.files[0])}
          accept=".pdf,.docx,.txt"
          style={{ display: 'none' }}
        />
        <button
          className="btn-secondary"
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled}
        >
          {file ? "Change File" : "Browse Files"}
        </button>
      </div>

      <button
        className="btn-primary"
        onClick={() => file && onAnalyze(file)}
        disabled={disabled || !file}
        style={{ width: '100%', padding: '1rem', fontSize: '1rem', fontWeight: '600' }}
      >
        {disabled ? "Processing..." : "Analyze Document"}
      </button>
    </div>
  );
};
