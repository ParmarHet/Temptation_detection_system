import React from 'react';
import { Radar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
} from 'chart.js';

ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip);

export default function TechniqueRadar({ techniques }) {
  if (!techniques || techniques.length === 0) return null;

  const labels = techniques.map((t) => t.name);
  const scores = techniques.map((t) => t.score);

  const data = {
    labels,
    datasets: [
      {
        data: scores,
        backgroundColor: 'rgba(90, 138, 90, 0.15)',
        borderColor: 'rgba(90, 138, 90, 0.8)',
        borderWidth: 2,
        pointBackgroundColor: 'rgba(90, 138, 90, 1)',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 5,
        pointHoverRadius: 7,
        fill: true,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: '#2d2520',
        titleFont: { size: 12 },
        bodyFont: { size: 11 },
        padding: 10,
        cornerRadius: 8,
        callbacks: {
          label: (ctx) => `Score: ${ctx.raw}`,
        },
      },
    },
    scales: {
      r: {
        beginAtZero: true,
        max: 100,
        ticks: {
          stepSize: 25,
          font: { size: 10 },
          color: '#a89d8e',
          backdropColor: 'transparent',
        },
        grid: {
          color: '#e4ddd3',
        },
        angleLines: {
          color: '#e4ddd3',
        },
        pointLabels: {
          font: { size: 11, weight: '500' },
          color: '#6b5f50',
        },
      },
    },
  };

  return (
    <div>
      <h3 className="text-sm font-semibold text-surface-700 mb-3">Technique Scores</h3>
      <div className="max-w-md mx-auto">
        <Radar data={data} options={options} />
      </div>
    </div>
  );
}
