import React, { useState, useRef } from 'react';

export default function UploadForm({ onAnalysisStart, isAnalyzing }) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [deepAnalysis, setDeepAnalysis] = useState(false);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleSubmit = () => {
    if (selectedFile && !isAnalyzing) {
      onAnalysisStart(selectedFile, deepAnalysis);
    }
  };

  const formatSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div className="max-w-lg mx-auto">
      {/* Drop zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !selectedFile && fileInputRef.current?.click()}
        className={`
          relative rounded-xl border-2 border-dashed p-10 text-center cursor-pointer
          transition-all duration-200
          ${isDragging
            ? 'border-sage-400 bg-sage-50'
            : selectedFile
              ? 'border-sage-300 bg-white'
              : 'border-surface-300 bg-white hover:border-sage-300 hover:bg-sage-50/30'
          }
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".jpg,.jpeg,.png,.pdf"
          onChange={handleFileSelect}
          className="hidden"
        />

        {!selectedFile ? (
          <div className="space-y-4">
            <div className="w-14 h-14 rounded-full bg-surface-100 flex items-center justify-center mx-auto">
              <svg className="w-7 h-7 text-surface-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
              </svg>
            </div>
            <div>
              <p className="text-sm font-medium text-surface-700">
                Drop your document here
              </p>
              <p className="text-xs text-surface-400 mt-1">
                or click to browse
              </p>
            </div>
            <p className="text-xs text-surface-400">
              JPG, PNG, or PDF
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="w-12 h-12 rounded-lg bg-sage-50 flex items-center justify-center mx-auto">
              <svg className="w-6 h-6 text-sage-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
              </svg>
            </div>
            <div>
              <p className="text-sm font-medium text-surface-800 truncate max-w-xs mx-auto">
                {selectedFile.name}
              </p>
              <p className="text-xs text-surface-400 mt-0.5">
                {formatSize(selectedFile.size)}
              </p>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setSelectedFile(null);
              }}
              className="text-xs text-surface-500 hover:text-surface-700 underline"
            >
              Choose different file
            </button>
          </div>
        )}
      </div>

      {/* Options */}
      <div className="mt-4 flex items-center gap-3 px-1">
        <label className="flex items-center gap-2 cursor-pointer group">
          <div className="relative">
            <input
              type="checkbox"
              checked={deepAnalysis}
              onChange={(e) => setDeepAnalysis(e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-9 h-5 bg-surface-300 rounded-full peer peer-checked:bg-sage-500 transition-colors" />
            <div className="absolute left-0.5 top-0.5 w-4 h-4 bg-white rounded-full shadow-sm transform peer-checked:translate-x-4 transition-transform" />
          </div>
          <span className="text-xs text-surface-600 group-hover:text-surface-800 transition-colors">
            Include copy-move detection (slower)
          </span>
        </label>
      </div>

      {/* Analyze button */}
      <button
        onClick={handleSubmit}
        disabled={!selectedFile || isAnalyzing}
        className={`
          mt-5 w-full py-3 rounded-xl text-sm font-semibold transition-all duration-200
          ${!selectedFile || isAnalyzing
            ? 'bg-surface-200 text-surface-400 cursor-not-allowed'
            : 'bg-sage-600 hover:bg-sage-700 text-white shadow-sm hover:shadow-md active:scale-[0.98]'
          }
        `}
      >
        {isAnalyzing ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            Analyzing...
          </span>
        ) : (
          'Analyze Document'
        )}
      </button>
    </div>
  );
}
