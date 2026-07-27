import React from 'react';

function BalanceChart({ data }) {
  if (!data || data.length === 0) {
    return (
      <svg className="chart-svg" viewBox="0 0 400 120" preserveAspectRatio="none">
        <text x="200" y="60" textAnchor="middle" fill="#8892b0" fontSize="11">
          Sin datos
        </text>
      </svg>
    );
  }

  const width = 400;
  const height = 120;
  const padding = 10;

  const values = data.map((d) => d.usd_balance);
  const minVal = Math.min(...values);
  const maxVal = Math.max(...values);
  const range = maxVal - minVal || 1;

  const points = data.map((d, i) => {
    const x = padding + (i / Math.max(data.length - 1, 1)) * (width - 2 * padding);
    const y = height - padding - ((d.usd_balance - minVal) / range) * (height - 2 * padding);
    return { x, y, value: d.usd_balance };
  });

  const linePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x},${p.y}`).join(' ');

  const areaPath = `${linePath} L${points[points.length - 1].x},${height - padding} L${points[0].x},${height - padding} Z`;

  const gridLines = [0, 0.25, 0.5, 0.75, 1].map((fraction) => {
    const y = padding + fraction * (height - 2 * padding);
    return <line key={fraction} x1={padding} y1={y} x2={width - padding} y2={y} className="chart-grid" />;
  });

  const xLabels = data.length > 1
    ? [0, Math.floor(data.length / 2), data.length - 1].map((i) => {
        const p = points[i];
        const date = new Date(data[i].date);
        const label = `${date.getDate()}/${date.getMonth() + 1}`;
        return <text key={i} x={p.x} y={height - 1} textAnchor="middle" className="chart-text">{label}</text>;
      })
    : [];

  return (
    <svg className="chart-svg" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
      <defs>
        <linearGradient id="balanceGradient" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#00d4aa" stopOpacity="0.3" />
          <stop offset="100%" stopColor="#00d4aa" stopOpacity="0" />
        </linearGradient>
      </defs>
      {gridLines}
      <path d={areaPath} fill="url(#balanceGradient)" className="chart-area" />
      <path d={linePath} className="chart-line" />
      {points.length > 0 && (
        <circle cx={points[points.length - 1].x} cy={points[points.length - 1].y} r="3" fill="#00d4aa" />
      )}
      {xLabels}
    </svg>
  );
}

export default BalanceChart;