import React from 'react';

function OrderHistory({ orders }) {
  const formatDate = (iso) => {
    if (!iso) return '---';
    const d = new Date(iso);
    return d.toLocaleString('es-ES', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="order-history">
      <h3>Historial de órdenes</h3>
      {orders.length === 0 ? (
        <div className="order-empty">No hay órdenes registradas</div>
      ) : (
        orders.map((order) => (
          <div key={order.id} className="order-item">
            <span className={`order-side ${order.side}`}>{order.side.toUpperCase()}</span>
            <div className="order-details">
              <span className="order-amount">{order.amount} {order.side === 'buy' ? 'PEN' : 'USD'}</span>
              <span className="order-price">@ {order.price.toFixed(4)} USD</span>
            </div>
            <span className="order-time">{formatDate(order.created_at)}</span>
          </div>
        ))
      )}
    </div>
  );
}

export default OrderHistory;