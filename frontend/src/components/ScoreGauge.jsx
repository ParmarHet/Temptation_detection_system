import React, { useEffect, useState } from 'react';

export default function ScoreGauge({ score, verdict }) {
  const [animatedScore, setAnimatedScore] = useState(0);

  useEffect(() => {
    const timer = setTimeout(() => setAnimatedScore(score), 100);
    return () => clearTimeout(timer);
  }, [score]);

  const circumference = 2 * Math.PI * 45;
  const progress = (animatedScore / 100) * circumference;

  const getColor = () => {
    if (score <= 30) return '#5a8a5a'; // sage-500
    if (score <= 60) return '#f4a832'; // amber-400
    return '#f43f3f'; // rose-500
  };

  const getVerdictLabel = () => {
    switch (verdict) {
      case 'CLEAN': return 'Likely Authentic';
      case 'SUSPICIOUS': return 'Suspicious';
      case 'TAMPERED': return 'Likely Tampered';
      default: return 'Unknown';
    }
  };

  const getVerdictColor = () => {
    switch (verdict) {
      case 'CLEAN': return 'text-sage-600 bg-sage-50';
      case 'SUSPICIOUS': return 'text-amber-600 bg-amber-50';
      case 'TAMPERED': return 'text-rose-600 bg-rose-50';
      default: return 'text-surface-500 bg-surface-100';
    }
  };

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-44 h-44">
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
          {/* Background track */}
          <circle
            cx="50"
            cy="50"
            r="45"
            fill="none"
            stroke="#e4ddd3"
            strokeWidth="6"
          />
          {/* Progress arc */}
          <circle
            cx="50"
            cy="50"
            r="45"
            fill="none"
            stroke={getColor()}
            strokeWidth="6"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={circumference - progress}
            style={{ transition: 'stroke-dashoffset 1s ease-out' }}
          />
        </svg>
        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-bold text-surface-900">
            {Math.round(animatedScore)}
          </span>
          <span className="text-xs text-surface-400 mt-0.5">/ 100</span>
        </div>
      </div>
      <div className={`mt-3 px-3 py-1 rounded-full text-xs font-medium ${getVerdictColor()}`}>
        {getVerdictLabel()}
      </div>
    </div>
  );
}
