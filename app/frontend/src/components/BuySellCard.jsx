import React, { useState } from 'react';

function BuySellCard({ side, label, onExecute, disabled, optimal, price }) {
  const [inputAmount, setInputAmount] = useState('');

  const handleExecute = () => {
    const val = parseFloat(inputAmount);
    if (!isNaN(val) && val > 0) {
      onExecute(val);
      setInputAmount('');
    }
  };

  const cardClass = `buysell-card ${side}${disabled ? ' disabled' : ''}`;

  return (
    <div className={cardClass}>
      <div className="card-label">{label}</div>
      {optimal && !disabled && (
        <div className="optimal-badge">Modelo optimo detectado</div>
      )}
      <div className="amount-row">
        <input
          className="amount-input"
          type="number"
          value={inputAmount}
          onChange={(e) => setInputAmount(e.target.value)}
          placeholder="0.00"
          step="0.01"
          min="0"
          disabled={disabled}
        />
        <span className="amount-unit">PEN</span>
      </div>
      {price && (
        <div style={{ fontSize: '0.75rem', color: '#8892b0', marginBottom: '0.5rem', textAlign: 'center' }}>
          Precio ref: {price.toFixed(4)} USD/PEN
        </div>
      )}
      <button
        className={`action-btn ${side === 'buy' ? 'buy-btn' : 'sell-btn'}`}
        onClick={handleExecute}
        disabled={disabled}
      >
        {disabled ? 'Deshabilitado' : ` ${label}`}
      </button>
    </div>
  );
}

export default BuySellCard;