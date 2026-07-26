import React, { useState } from 'react';

function BankSelector({ banks, selectedBank, onSelectBank }) {
  const [searchTerm, setSearchTerm] = useState('');

  const filtered = banks.filter((b) =>
    b.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="bank-overlay" onClick={(e) => e.stopPropagation()}>
      <div className="bank-overlay-header">
        <input
          type="text"
          className="bank-search"
          placeholder="Buscar banco..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      <div
        className={`bank-option no-bank-option ${!selectedBank ? 'selected' : ''}`}
        onClick={() => onSelectBank(null)}
      >
        <span className="bank-option-name">Sin banco</span>
        <span className="bank-option-dot" />
      </div>

      {filtered.map((bank) => (
        <div
          key={bank.id}
          className={`bank-option ${selectedBank?.id === bank.id ? 'selected' : ''}`}
          onClick={() => onSelectBank(bank)}
        >
          <span className="bank-option-name">{bank.name}</span>
          <span className="bank-option-spread">{bank.spread_multiplier.toFixed(4)}</span>
        </div>
      ))}

      {filtered.length === 0 && (
        <div className="bank-empty">
          No se encontraron bancos
        </div>
      )}
    </div>
  );
}

export default BankSelector;
