import React, { useState } from 'react';

const techniqueIcons = {
  'Error Level Analysis': (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5m.75-9l3-3 2.148 2.148A12.061 12.061 0 0116.5 7.605" />
    </svg>
  ),
  'Noise/Residual Analysis': (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
    </svg>
  ),
  'Copy-Move Detection': (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 17.25v3.375c0 .621-.504 1.125-1.125 1.125h-9.75a1.125 1.125 0 01-1.125-1.125V7.875c0-.621.504-1.125 1.125-1.125H6.75a9.06 9.06 0 011.5.124m7.5 10.376h3.375c.621 0 1.125-.504 1.125-1.125V11.25c0-4.46-3.243-8.161-7.5-8.876a9.06 9.06 0 00-1.5-.124H9.375c-.621 0-1.125.504-1.125 1.125v3.5m7.5 10.375H9.375a1.125 1.125 0 01-1.125-1.125v-9.25m12 6.625v-1.875a3.375 3.375 0 00-3.375-3.375h-1.5a1.125 1.125 0 01-1.125-1.125v-1.5a3.375 3.375 0 00-3.375-3.375H9.75" />
    </svg>
  ),
  'Metadata Consistency': (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5" />
    </svg>
  ),
  'JPEG Ghost Detection': (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
    </svg>
  ),
  'OCR Consistency': (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
    </svg>
  ),
};

export default function TechniqueCard({ technique }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const { name, score, details } = technique;

  const getStatusColor = () => {
    if (score <= 30) return 'bg-sage-50 text-sage-700 border-sage-200';
    if (score <= 60) return 'bg-amber-50 text-amber-700 border-amber-200';
    return 'bg-rose-50 text-rose-700 border-rose-200';
  };

  const getScoreColor = () => {
    if (score <= 30) return 'text-sage-600';
    if (score <= 60) return 'text-amber-600';
    return 'text-rose-600';
  };

  return (
    <div className="bg-white rounded-xl border border-surface-200 overflow-hidden card-hover">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-5 py-4 flex items-center gap-4 text-left hover:bg-surface-50/50 transition-colors"
      >
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${getStatusColor()} border`}>
          {techniqueIcons[name] || (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" />
            </svg>
          )}
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-semibold text-surface-800">{name}</h4>
          <p className="text-xs text-surface-400 mt-0.5 truncate">
            {details?.summary || 'Forensic analysis'}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className={`text-lg font-bold font-mono ${getScoreColor()}`}>
            {score.toFixed(1)}
          </span>
          <svg
            className={`w-4 h-4 text-surface-400 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {isExpanded && details && (
        <div className="px-5 pb-5 border-t border-surface-100">
          <div className="pt-4 space-y-3">
            {details.flags && details.flags.length > 0 && (
              <div>
                <h5 className="text-xs font-semibold text-surface-600 mb-2 uppercase tracking-wide">Flags</h5>
                <div className="space-y-1.5">
                  {details.flags.map((flag, i) => (
                    <div key={i} className="flex items-start gap-2 text-xs text-surface-600">
                      <span className="text-amber-500 mt-0.5">•</span>
                      <span>{typeof flag === 'string' ? flag : flag?.detail || flag?.message || String(flag)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {details.metrics && Object.keys(details.metrics).length > 0 && (
              <div>
                <h5 className="text-xs font-semibold text-surface-600 mb-2 uppercase tracking-wide">Metrics</h5>
                <div className="grid grid-cols-2 gap-2">
                  {Object.entries(details.metrics).map(([key, value]) => (
                    <div key={key} className="bg-surface-50 rounded-lg px-3 py-2">
                      <span className="text-xs text-surface-400 block">{key}</span>
                      <span className="text-xs font-mono font-medium text-surface-700">
                        {typeof value === 'number' ? value.toFixed(3) : String(value)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
