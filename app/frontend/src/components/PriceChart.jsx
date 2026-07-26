import React, { useState, useRef, useCallback } from 'react';

function PriceChart({ data }) {
  const [hoverIndex, setHoverIndex] = useState(null);
  const [mouseX, setMouseX] = useState(0);
  const chartRef = useRef(null);

  if (!data || data.length === 0) {
    return (
      <svg className="chart-svg" viewBox="0 0 400 120" preserveAspectRatio="none">
        <text x="200" y="60" textAnchor="middle" fill="#8892b0" fontSize="9">
          Sin datos de precio
        </text>
      </svg>
    );
  }

  const width = 410;
  const height = 120;
  const padding = 10;
  const rightAxisX = width - 22;

  const values = data.map((d) => d.price);
  const minVal = Math.min(...values);
  const maxVal = Math.max(...values);
  const range = maxVal - minVal || 1;

  const chartWidth = rightAxisX - padding;

  const points = data.map((d, i) => {
    const x = padding + (i / Math.max(data.length - 1, 1)) * chartWidth;
    const y = height - padding - ((d.price - minVal) / range) * (height - 2 * padding);
    return { x, y, value: d.price };
  });

  const linePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x},${p.y}`).join(' ');

  const areaPath = `${linePath} L${points[points.length - 1].x},${height - padding} L${points[0].x},${height - padding} Z`;

  const gridLines = [0, 0.25, 0.5, 0.75, 1].map((fraction) => {
    const y = padding + fraction * (height - 2 * padding);
    return <line key={fraction} x1={padding} y1={y} x2={rightAxisX} y2={y} className="chart-grid" />;
  });

  const priceLabels = [0, 0.25, 0.5, 0.75, 1].map((fraction) => {
    const price = maxVal - fraction * range;
    const y = padding + fraction * (height - 2 * padding);
    const label = price.toFixed(3);
    return (
      <text key={fraction} x={rightAxisX + 2} y={y + 3} textAnchor="start" className="chart-price-text">
        {label}
      </text>
    );
  });

  const xLabels = data.length > 1
    ? [0, Math.floor(data.length / 2), data.length - 1].map((i) => {
        const p = points[i];
        const date = new Date(data[i].date);
        const label = `${date.getDate()}/${date.getMonth() + 1}`;
        return <text key={i} x={p.x} y={height - 1} textAnchor="middle" className="chart-text">{label}</text>;
      })
    : [];

  const isUp = data.length >= 2 && data[data.length - 1].price >= data[0].price;
  const lineColor = isUp ? '#00d4aa' : '#ef4444';

  const handleMouseMove = useCallback((e) => {
    if (!chartRef.current) return;
    const rect = chartRef.current.getBoundingClientRect();
    const svgWidth = rect.width;
    const svgHeight = rect.height;
    const relativeX = ((e.clientX - rect.left) / svgWidth) * width;

    if (relativeX < padding || relativeX > rightAxisX || data.length < 2) {
      setHoverIndex(null);
      return;
    }

    const fraction = (relativeX - padding) / chartWidth;
    const index = Math.round(fraction * (data.length - 1));
    const clampedIndex = Math.max(0, Math.min(index, data.length - 1));
    setHoverIndex(clampedIndex);
    setMouseX(e.clientX - rect.left);
  }, [data.length, padding, rightAxisX, chartWidth, width]);

  const handleMouseLeave = useCallback(() => {
    setHoverIndex(null);
  }, []);

  const hoverPoint = hoverIndex !== null ? points[hoverIndex] : null;
  const hoverData = hoverIndex !== null ? data[hoverIndex] : null;

  const formatDate = (dateStr) => {
    const d = new Date(dateStr);
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hours = String(d.getHours()).padStart(2, '0');
    const minutes = String(d.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day} ${hours}:${minutes}`;
  };

  return (
    <div className="chart-container" ref={chartRef}>
      <svg
        className="chart-svg"
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="none"
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
      >
        <defs>
          <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={lineColor} stopOpacity="0.3" />
            <stop offset="100%" stopColor={lineColor} stopOpacity="0" />
          </linearGradient>
        </defs>
        {gridLines}
        <path d={areaPath} fill="url(#priceGradient)" className="chart-area" />
        <path d={linePath} className="chart-line" style={{ stroke: lineColor }} />
        {hoverPoint && (
          <line x1={hoverPoint.x} y1={padding} x2={hoverPoint.x} y2={height - padding} stroke="#e0e0e0" strokeWidth="1" strokeDasharray="3,3" />
        )}
        {points.length > 0 && (
          <circle
            cx={points[points.length - 1].x}
            cy={points[points.length - 1].y}
            r={hoverIndex !== null && hoverIndex === points.length - 1 ? "5" : "3"}
            fill={lineColor}
            style={{ transition: 'r 0.1s ease' }}
          />
        )}
        {hoverPoint && (
          <circle cx={hoverPoint.x} cy={hoverPoint.y} r="5" fill={lineColor} stroke="#0a0f1a" strokeWidth="2" />
        )}
        <line x1={rightAxisX} y1={padding} x2={rightAxisX} y2={height - padding} stroke="#334155" strokeWidth="1" />
        {priceLabels}
        {xLabels}
      </svg>
      {hoverData && (
        <div
          className="chart-tooltip"
          style={{
            left: `${Math.min(mouseX, 380)}px`,
            top: `${(hoverPoint.y / height) * 100}%`,
          }}
        >
          <div className="tooltip-date">{formatDate(hoverData.date)}</div>
          <div className="tooltip-price">S/. {hoverData.price.toFixed(3)}</div>
        </div>
      )}
    </div>
  );
}

export default PriceChart;
