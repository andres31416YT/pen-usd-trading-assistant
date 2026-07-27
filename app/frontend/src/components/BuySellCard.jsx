import React, { useState } from 'react';

function BuySellCard({ side, label, onExecute, disabled, optimal, price, confidence, recommendation, availableBalance }) {
  const [inputAmount, setInputAmount] = useState('');
  const [error, setError] = useState('');

  const isSell = side === 'sell';
  const amountUnit = isSell ? 'USD' : 'PEN';
  const balanceUnit = isSell ? 'USD' : 'PEN';

  const handleExecute = () => {
    const val = parseFloat(inputAmount);
    if (!isNaN(val) && val > 0) {
      if (availableBalance !== undefined && val > availableBalance) {
        setError(`Cantidad excede el saldo disponible (${availableBalance.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })})`);
        return;
      }
      onExecute(val);
      setInputAmount('');
      setError('');
    }
  };

  const isRecommended = optimal && recommendation === side;
  const cardClass = `buysell-card ${side}${disabled ? ' disabled' : ''}${isRecommended ? ' recommended' : ''}`;

  const confidenceColor = confidence >= 0.7 ? '#4ade80' : confidence >= 0.5 ? '#facc15' : '#f87171';

  return (
    <div className={cardClass}>
      <div className="card-label">
        {label}
        {isRecommended && (
          <span className="recommendation-badge" style={{ backgroundColor: confidenceColor }}>
            Modelo: {recommendation === 'buy' ? 'Compra' : 'Venta'}
          </span>
        )}
      </div>
      {isRecommended && confidence !== null && confidence !== undefined && (
        <div className="confidence-bar-container">
          <div className="confidence-bar" style={{ width: `${confidence * 100}%`, backgroundColor: confidenceColor }} />
          <span className="confidence-text" style={{ color: confidenceColor }}>
            {Math.round(confidence * 100)}% confianza
          </span>
        </div>
      )}
      <div className="amount-row">
        <input
          className="amount-input"
          type="text"
          value={inputAmount}
          onChange={(e) => { setInputAmount(e.target.value.replace(/[^0-9.]/g, "")); setError(''); }}
          placeholder="0.00"
          inputMode="numeric"
          disabled={disabled}
        />
        <span className="amount-unit">{amountUnit}</span>
      </div>
      {availableBalance !== undefined && (
        <div style={{ fontSize: '0.7rem', color: '#8892b0', marginBottom: '0.25rem', textAlign: 'center' }}>
          Disponible: {availableBalance.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} {balanceUnit}
        </div>
      )}
      {price && (
        <div style={{ fontSize: '0.75rem', color: '#8892b0', marginBottom: '0.5rem', textAlign: 'center' }}>
          Precio ref: {price.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} USD/PEN
        </div>
      )}
      {error && (
        <div style={{ fontSize: '0.75rem', color: '#ef4444', marginBottom: '0.5rem', textAlign: 'center' }}>
          {error}
        </div>
      )}
      <button
        className={`action-btn ${side === 'buy' ? 'buy-btn' : 'sell-btn'}`}
        onClick={handleExecute}
        disabled={disabled}
      >
        {disabled ? (label === 'Comprar' ? 'Sin señal de compra' : 'Sin señal de venta') : ` ${label}`}
      </button>
    </div>
  );
}

export default BuySellCard;