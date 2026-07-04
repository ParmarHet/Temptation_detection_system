import React, { useState, useRef, useCallback, useEffect } from 'react';

export default function ImageComparison({ originalUrl, heatmapUrl, technique }) {
  const [sliderPos, setSliderPos] = useState(50);
  const containerRef = useRef(null);
  const isDragging = useRef(false);

  const handleMouseMove = useCallback((e) => {
    if (!isDragging.current || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    setSliderPos(Math.max(0, Math.min(100, x)));
  }, []);

  const handleMouseUp = useCallback(() => {
    isDragging.current = false;
  }, []);

  useEffect(() => {
    document.addEventListener('mouseup', handleMouseUp);
    document.addEventListener('mousemove', handleMouseMove);
    return () => {
      document.removeEventListener('mouseup', handleMouseUp);
      document.removeEventListener('mousemove', handleMouseMove);
    };
  }, [handleMouseUp, handleMouseMove]);

  return (
    <div className="bg-white rounded-xl border border-surface-200 p-5">
      <h3 className="text-sm font-semibold text-surface-700 mb-3">
        {technique || 'Image Comparison'}
      </h3>
      <div
        ref={containerRef}
        className="relative w-full aspect-[4/3] rounded-lg overflow-hidden cursor-ew-resize select-none bg-surface-100"
        onMouseDown={() => { isDragging.current = true; }}
      >
        <img
          src={originalUrl}
          alt="Original"
          className="absolute inset-0 w-full h-full object-contain"
        />
        <div
          className="absolute inset-0 overflow-hidden"
          style={{ clipPath: `inset(0 0 0 ${sliderPos}%)` }}
        >
          <img
            src={heatmapUrl}
            alt="Heatmap overlay"
            className="absolute inset-0 w-full h-full object-contain"
          />
        </div>
        <div
          className="absolute top-0 bottom-0 w-0.5 bg-white shadow-md z-10"
          style={{ left: `${sliderPos}%` }}
        >
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-white shadow-lg flex items-center justify-center">
            <svg className="w-4 h-4 text-surface-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M8 9l4-4 4 4m0 6l-4 4-4-4" />
            </svg>
          </div>
        </div>
        <div className="absolute top-3 left-3 px-2 py-1 bg-white/90 rounded text-xs font-medium text-surface-600 shadow-sm z-10">
          Original
        </div>
        <div className="absolute top-3 right-3 px-2 py-1 bg-white/90 rounded text-xs font-medium text-surface-600 shadow-sm z-10">
          Heatmap
        </div>
      </div>
    </div>
  );
}
