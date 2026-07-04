import React, { useState } from 'react';
import UploadForm from '../components/UploadForm';
import ResultsView from '../components/ResultsView';
import LoadingSpinner from '../components/LoadingSpinner';
import { analyzeDocument } from '../api/client';

export default function HomePage() {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [analyzingFile, setAnalyzingFile] = useState(null);

  const handleAnalysisStart = async (file, deep = false) => {
    setIsAnalyzing(true);
    setAnalyzingFile(file);
    setError(null);
    setResult(null);

    try {
      const analysisResult = await analyzeDocument(file, deep);
      setResult(analysisResult);
    } catch (err) {
      setError(err.message || 'Analysis failed. Please try again.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleReset = () => {
    setResult(null);
    setError(null);
    setAnalyzingFile(null);
  };

  return (
    <div className="min-h-screen bg-surface-100">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-surface-200 sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img src="/logo.svg" alt="Logo" className="w-9 h-9" />
            <div>
              <h1 className="text-lg font-semibold text-surface-900">Temptation Detection</h1>
              <p className="text-xs text-surface-500">Document Forensics</p>
            </div>
          </div>
          {result && (
            <button
              onClick={handleReset}
              className="px-4 py-2 bg-surface-100 hover:bg-surface-200 text-surface-700 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              New Scan
            </button>
          )}
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-6xl mx-auto px-6 py-10">
        {!isAnalyzing && !result && (
          <div className="space-y-10">
            {/* Hero */}
            <div className="text-center mb-8">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-sage-50 border border-sage-200 rounded-full text-sage-600 text-xs font-medium mb-5">
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
                </svg>
                Rule-Based Forensic Analysis
              </div>
              <h2 className="text-3xl font-bold text-surface-900 mb-3">
                Detect Document Tampering
              </h2>
              <p className="text-surface-600 max-w-xl mx-auto text-base">
                Upload a document to analyze it using forensic techniques.
                Get explainable results with visual heatmaps.
              </p>
            </div>

            {/* Upload form */}
            <UploadForm onAnalysisStart={handleAnalysisStart} isAnalyzing={isAnalyzing} />

            {/* Features */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              {[
                {
                  icon: (
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5m.75-9l3-3 2.148 2.148A12.061 12.061 0 0116.5 7.605" />
                    </svg>
                  ),
                  title: '5 Forensic Techniques',
                  desc: 'ELA, noise analysis, metadata, JPEG ghost, and OCR consistency',
                },
                {
                  icon: (
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                  ),
                  title: 'Visual Heatmaps',
                  desc: 'Color-coded overlays showing which regions triggered each signal',
                },
                {
                  icon: (
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
                    </svg>
                  ),
                  title: 'Explainable Results',
                  desc: 'Fully interpretable scores — know why each flag was raised',
                },
              ].map((feature, i) => (
                <div key={i} className="bg-white rounded-xl p-5 border border-surface-200 card-hover">
                  <div className="w-10 h-10 rounded-lg bg-sage-50 flex items-center justify-center text-sage-600 mb-3">
                    {feature.icon}
                  </div>
                  <h3 className="text-sm font-semibold text-surface-800 mb-1">{feature.title}</h3>
                  <p className="text-xs text-surface-500 leading-relaxed">{feature.desc}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {isAnalyzing && <LoadingSpinner filename={analyzingFile?.name} />}

        {error && !isAnalyzing && (
          <div className="max-w-md mx-auto text-center py-16">
            <div className="w-16 h-16 rounded-full bg-rose-50 flex items-center justify-center mx-auto mb-5">
              <svg className="w-8 h-8 text-rose-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-surface-800 mb-2">Analysis Failed</h3>
            <p className="text-sm text-surface-500 mb-6">{error}</p>
            <button
              onClick={handleReset}
              className="px-5 py-2.5 bg-sage-600 hover:bg-sage-700 text-white rounded-lg text-sm font-medium transition-colors"
            >
              Try Again
            </button>
          </div>
        )}

        {result && !isAnalyzing && <ResultsView result={result} />}
      </main>

      {/* Footer */}
      <footer className="border-t border-surface-200 bg-white/50 mt-12">
        <div className="max-w-6xl mx-auto px-6 py-5 flex items-center justify-between">
          <p className="text-xs text-surface-400">Temptation Detection System v1.0</p>
          <p className="text-xs text-surface-400">Rule-Based Document Forensics</p>
        </div>
      </footer>
    </div>
  );
}
