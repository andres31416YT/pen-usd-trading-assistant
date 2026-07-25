import React from 'react';

function PredictionDisplay({ prediction }) {
  const direction = prediction.direction?.toLowerCase() || 'neutral';
  const confidence = prediction.confidence ?? 0;

  return (
    <div className="card prediction-display">
      <h3>Predicción PEN/USD</h3>
      <div className={`prediction-value ${direction}`}>
        {direction === 'bullish' ? '↑ Alcista' : direction === 'bearish' ? '↓ Bajista' : '→ Neutral'}
      </div>
      <p className="prediction-confidence">
        Confianza: {confidence}%
      </p>
      {prediction.price_target && (
        <p style={{ marginTop: '0.5rem', color: '#8892b0' }}>
          Precio objetivo: <strong>{prediction.price_target}</strong>
        </p>
      )}
      {prediction.model_version && (
        <p style={{ marginTop: '0.3rem', fontSize: '0.8rem', color: '#8892b0' }}>
          Modelo: {prediction.model_version}
        </p>
      )}
    </div>
  );
}

export default PredictionDisplay;