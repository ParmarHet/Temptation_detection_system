import React from 'react';

export default function TechniqueBarChart({ techniques }) {
  const getBarColor = (score) => {
    if (score <= 30) return 'bg-sage-500';
    if (score <= 60) return 'bg-amber-400';
    return 'bg-rose-500';
  };

  const getBarBg = (score) => {
    if (score <= 30) return 'bg-sage-100';
    if (score <= 60) return 'bg-amber-100';
    return 'bg-rose-100';
  };

  return (
    <div className="bg-white rounded-xl border border-surface-200 p-5">
      <h3 className="text-sm font-semibold text-surface-700 mb-4">Score Breakdown</h3>
      <div className="space-y-3">
        {techniques.map((t, i) => (
          <div key={i}>
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-medium text-surface-600">{t.name}</span>
              <span className="text-xs font-mono text-surface-500">{t.score.toFixed(1)}</span>
            </div>
            <div className={`h-2 rounded-full ${getBarBg(t.score)}`}>
              <div
                className={`h-full rounded-full ${getBarColor(t.score)} transition-all duration-700`}
                style={{ width: `${Math.min(t.score, 100)}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
