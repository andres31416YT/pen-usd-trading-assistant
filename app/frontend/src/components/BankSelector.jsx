import React, { useState } from 'react';

function BankSelector({ banks, selectedBank, bankChecked, onSelectBank, onToggleBank, onClose }) {
  const [searchTerm, setSearchTerm] = useState('');

  const filtered = banks.filter((b) =>
    b.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="bank-overlay" onClick={(e) => e.stopPropagation()}>
      <div style={{ padding: '0.4rem 0.8rem', borderBottom: '1px solid #1e293b' }}>
        <input
          type="text"
          placeholder="Buscar banco..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          style={{
            width: '100%',
            padding: '0.4rem 0.6rem',
            background: '#1e293b',
            border: '1px solid #334155',
            borderRadius: '6px',
            color: '#e0e0e0',
            fontSize: '0.8rem',
            fontFamily: 'inherit',
          }}
        />
      </div>
      {filtered.map((bank) => (
        <div
          key={bank.id}
          className={`bank-option ${selectedBank?.id === bank.id ? 'selected' : ''}`}
          onClick={() => onSelectBank(bank)}
        >
          <span>{bank.name}</span>
          <span className={`spread-check ${bankChecked ? 'active' : ''}`}>
            {bankChecked ? '✓' : '○'} {bank.spread_multiplier.toFixed(10)}
          </span>
        </div>
      ))}
      {filtered.length === 0 && (
        <div style={{ padding: '0.5rem', textAlign: 'center', color: '#8892b0', fontSize: '0.8rem' }}>
          No se encontraron bancos
        </div>
      )}
      <div
        style={{
          padding: '0.4rem 0.8rem',
          borderTop: '1px solid #1e293b',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <span style={{ fontSize: '0.75rem', color: '#8892b0' }}>
          {selectedBank ? selectedBank.name : 'Sin banco seleccionado'}
        </span>
        <button
          className="btn btn-sm"
          style={{
            background: bankChecked ? '#00d4aa' : '#1e293b',
            color: bankChecked ? '#0a0e17' : '#e0e0e0',
            fontSize: '0.7rem',
            padding: '0.2rem 0.5rem',
          }}
          onClick={(e) => {
            e.stopPropagation();
            onToggleBank();
          }}
        >
          {bankChecked ? 'Desactivar' : 'Activar'} Spread
        </button>
      </div>
    </div>
  );
}

export default BankSelector;