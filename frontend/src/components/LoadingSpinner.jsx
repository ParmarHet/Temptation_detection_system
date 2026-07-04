import React from 'react';

export default function LoadingSpinner({ filename }) {
  return (
    <div className="max-w-md mx-auto text-center py-20">
      <div className="relative inline-block mb-6">
        {/* Outer ring */}
        <div className="w-20 h-20 rounded-full border-4 border-surface-200" />
        {/* Spinning arc */}
        <div className="absolute inset-0 w-20 h-20 rounded-full border-4 border-transparent border-t-sage-500 animate-spin" />
        {/* Center dot */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-3 h-3 rounded-full bg-sage-500" />
        </div>
      </div>

      <h3 className="text-lg font-semibold text-surface-800 mb-2">
        Analyzing Document
      </h3>
      <p className="text-sm text-surface-500 mb-1">
        Running forensic techniques...
      </p>
      {filename && (
        <p className="text-xs text-surface-400 mt-3 truncate max-w-xs mx-auto">
          {filename}
        </p>
      )}

      <div className="mt-8 space-y-3 text-left max-w-xs mx-auto">
        {[
          'Error Level Analysis',
          'Noise residual analysis',
          'Metadata extraction',
          'JPEG ghost detection',
          'OCR consistency check',
        ].map((step, i) => (
          <div key={i} className="flex items-center gap-3 text-xs text-surface-500">
            <div className="w-1.5 h-1.5 rounded-full bg-sage-400 animate-pulse" style={{ animationDelay: `${i * 300}ms` }} />
            {step}
          </div>
        ))}
      </div>
    </div>
  );
}
