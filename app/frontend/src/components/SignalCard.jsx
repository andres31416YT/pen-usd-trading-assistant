import React from 'react';

function SignalCard({ signal }) {
  const direction = signal.direction?.toLowerCase() || 'neutral';
  const time = new Date(signal.created_at).toLocaleString('es-ES');

  return (
    <div className={`signal-card ${direction}`}>
      <div className="signal-header">
        <span className="signal-pair">{signal.pair}</span>
        <span className="signal-time">{time}</span>
      </div>
      <div className="signal-details">
        <div>
          Dirección: <span>{signal.direction}</span>
        </div>
        <div>
          Confianza: <span>{signal.confidence}%</span>
        </div>
        <div>
          Precio actual: <span>{signal.current_price}</span>
        </div>
        <div>
          Precio objetivo: <span>{signal.target_price}</span>
        </div>
      </div>
    </div>
  );
}

export default SignalCard;