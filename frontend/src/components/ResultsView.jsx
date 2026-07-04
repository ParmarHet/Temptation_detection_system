import React from 'react';
import ScoreGauge from './ScoreGauge';
import TechniqueRadar from './TechniqueRadar';
import TechniqueBarChart from './TechniqueBarChart';
import ImageComparison from './ImageComparison';
import TechniqueCard from './TechniqueCard';
import FindingsList from './FindingsList';

export default function ResultsView({ result }) {
  if (!result) return null;

  const analysis_id = result.analysis_id || '';
  const overall_score = result.overall_score || 0;
  const verdict = result.verdict || 'UNKNOWN';
  const techniques = result.techniques || [];
  const findings = result.findings || [];
  const image_url = result.image_url || null;
  const heatmap_urls = result.heatmap_urls || {};
  const format = result.format || '';
  const filename = result.filename || '';

  const primaryHeatmap = heatmap_urls.fused || heatmap_urls.ela;

  const hasHeatmaps = Object.keys(heatmap_urls).length > 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-surface-900">Analysis Results</h2>
          <p className="text-sm text-surface-500 mt-0.5">
            {filename}{format ? ` \u2022 ${format.toUpperCase()}` : ''}
          </p>
        </div>
        {analysis_id && (
          <div className="text-xs text-surface-400 font-mono">
            ID: {analysis_id.slice(0, 8)}
          </div>
        )}
      </div>

      {/* Score + Radar row */}
      <div className="bg-white rounded-xl border border-surface-200 p-6">
        <div className="flex flex-col md:flex-row items-center gap-8">
          <div className="shrink-0">
            <ScoreGauge score={overall_score} verdict={verdict} />
          </div>
          <div className="flex-1 w-full min-w-0">
            <TechniqueRadar techniques={techniques} />
          </div>
        </div>
      </div>

      {/* Bar chart */}
      {techniques.length > 0 && (
        <TechniqueBarChart techniques={techniques} />
      )}

      {/* Image comparison slider */}
      {image_url && primaryHeatmap && (
        <ImageComparison
          originalUrl={image_url}
          heatmapUrl={primaryHeatmap}
          technique="Fused Heatmap"
        />
      )}

      {/* Per-technique heatmaps */}
      {hasHeatmaps && (
        <div>
          <h3 className="text-sm font-semibold text-surface-700 mb-3">Per-Technique Heatmaps</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(heatmap_urls)
              .filter(([key]) => key !== 'fused')
              .map(([technique, url]) => (
                <div key={technique} className="bg-white rounded-xl border border-surface-200 p-4">
                  <p className="text-xs font-medium text-surface-600 mb-2 capitalize">
                    {technique.replace(/_/g, ' ')}
                  </p>
                  <img
                    src={url}
                    alt={`${technique} heatmap`}
                    className="w-full rounded-lg border border-surface-100"
                  />
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Technique details */}
      {techniques.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-surface-700 mb-3">Technique Details</h3>
          <div className="space-y-3">
            {techniques.map((t, i) => (
              <TechniqueCard key={i} technique={t} />
            ))}
          </div>
        </div>
      )}

      {/* Findings */}
      <FindingsList findings={findings} />
    </div>
  );
}
