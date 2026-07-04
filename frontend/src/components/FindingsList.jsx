import React, { useState } from 'react';

const severityConfig = {
  info: { color: 'bg-surface-100 text-surface-600', dot: 'bg-surface-400' },
  low: { color: 'bg-sage-50 text-sage-700', dot: 'bg-sage-400' },
  medium: { color: 'bg-amber-50 text-amber-700', dot: 'bg-amber-400' },
  high: { color: 'bg-rose-50 text-rose-700', dot: 'bg-rose-400' },
};

export default function FindingsList({ findings }) {
  const [expandedIdx, setExpandedIdx] = useState(null);

  if (!findings || findings.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-surface-200 p-5">
        <h3 className="text-sm font-semibold text-surface-700 mb-3">Findings</h3>
        <p className="text-xs text-surface-400">No significant findings detected.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-surface-200 p-5">
      <h3 className="text-sm font-semibold text-surface-700 mb-3">
        Findings ({findings.length})
      </h3>
      <div className="space-y-2">
        {findings.map((finding, i) => {
          const severity = severityConfig[finding.severity] || severityConfig.info;
          const isExpanded = expandedIdx === i;

          return (
            <div
              key={i}
              className="border border-surface-100 rounded-lg overflow-hidden"
            >
              <button
                onClick={() => setExpandedIdx(isExpanded ? null : i)}
                className="w-full px-4 py-3 flex items-center gap-3 text-left hover:bg-surface-50/50 transition-colors"
              >
                <div className={`w-2 h-2 rounded-full ${severity.dot} shrink-0`} />
                <span className="text-xs font-medium text-surface-700 flex-1 truncate">
                  {typeof finding.message === 'string' ? finding.message : String(finding.message)}
                </span>
                <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${severity.color} shrink-0`}>
                  {finding.severity}
                </span>
                <svg
                  className={`w-3.5 h-3.5 text-surface-400 transition-transform duration-200 shrink-0 ${isExpanded ? 'rotate-180' : ''}`}
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              {isExpanded && finding.details && (
                <div className="px-4 pb-3 border-t border-surface-50">
                  <p className="text-xs text-surface-500 mt-2 leading-relaxed">
                    {finding.details}
                  </p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
