import React, { useState } from 'react';

interface FileUploaderProps {
  onAnalyze: (file: File) => void;
  disabled: boolean;
}

export const FileUploader: React.FC<FileUploaderProps> = ({ onAnalyze, disabled }) => {
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const handleFileChange = (selectedFile: File | null) => {
    if (selectedFile) {
      setFile(selectedFile);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => setIsDragging(false);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="card w-full max-w-lg mx-auto p-6 text-center shadow-sm">
      <div
        className={`upload-box p-12 border-2 border-dashed rounded-lg mb-4 transition-colors ${
          isDragging ? 'border-primary bg-primary-light' : 'border-gray-300'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <div className="mb-4">
          <span className="text-4xl">📄</span>
        </div>
        <p className="text-lg font-medium text-gray-700 mb-2">
          {file ? file.name : "Drag and drop your specification document"}
        </p>
        <p className="text-sm text-gray-500 mb-6">
          PDF, DOCX, or TXT supported (Max 20MB)
        </p>
        <input
          type="file"
          ref={fileInputRef}
          onChange={(e) => e.target.files && handleFileChange(e.target.files[0])}
          accept=".pdf,.docx,.txt"
          className="hidden"
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
        className="btn-primary w-full py-4 text-base font-semibold"
        onClick={() => file && onAnalyze(file)}
        disabled={disabled || !file}
      >
        {disabled ? "Processing..." : "Analyze Document"}
      </button>
    </div>
  );
};
