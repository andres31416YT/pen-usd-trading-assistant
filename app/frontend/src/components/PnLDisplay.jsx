import React from 'react';

function PnLDisplay({ pnl }) {
  const isPositive = pnl.value >= 0;

  return (
    <div className="pnl-card">
      <div>
        <div className="pnl-label">Ganancia/Pérdida</div>
        <div className={`pnl-value ${isPositive ? 'positive' : 'negative'}`}>
          {isPositive ? '+' : ''}{pnl.value.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} USD
        </div>
      </div>
      <div style={{ textAlign: 'right' }}>
        <div className="pnl-label">Variación</div>
        <div className={`pnl-percent ${isPositive ? 'positive' : 'negative'}`}>
          {isPositive ? '+' : ''}{pnl.percent.toFixed(2)}%
        </div>
      </div>
    </div>
  );
}

export default PnLDisplay;