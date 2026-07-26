import React, { useState, useEffect, useCallback } from 'react';
import { tradingAPI, bankAPI, accountAPI } from '../services/api';
import BankSelector from '../components/BankSelector';
import BalanceChart from '../components/BalanceChart';
import PriceChart from '../components/PriceChart';
import BuySellCard from '../components/BuySellCard';
import OrderHistory from '../components/OrderHistory';
import PnLDisplay from '../components/PnLDisplay';

function Dashboard({ user }) {
  const [banks, setBanks] = useState([]);
  const [selectedBank, setSelectedBank] = useState(null);
  const [balance, setBalance] = useState(null);
  const [balanceHistory, setBalanceHistory] = useState([]);
  const [currentPrice, setCurrentPrice] = useState(null);
  const [priceHistory, setPriceHistory] = useState([]);
  const [optimalTrade, setOptimalTrade] = useState(null);
  const [orders, setOrders] = useState([]);
  const [pnl, setPnl] = useState({ value: 0, percent: 0 });
  const [timeframe, setTimeframe] = useState('1W');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [bankOverlayOpen, setBankOverlayOpen] = useState(false);
  const [bankChecked, setBankChecked] = useState(false);
  const [balanceVisible, setBalanceVisible] = useState(true);

  const fetchData = useCallback(async () => {
    setError('');
    try {
      const [banksRes, balanceRes, historyRes, predRes, ordersRes] = await Promise.all([
        bankAPI.listBanks(),
        accountAPI.getBalance(),
        accountAPI.getBalanceHistory(30),
        tradingAPI.getPrediction(),
        accountAPI.getOrders(),
      ]);
      setBanks(banksRes);
      setBalance(balanceRes);
      setBalanceHistory(historyRes);
      setOrders(ordersRes);

      if (predRes) {
        setCurrentPrice(predRes.price_target || 0);
        const dir = predRes.direction || 'neutral';
        const conf = predRes.confidence || 0;
        const isOptimal = conf >= 0.6 && dir !== 'neutral';
        setOptimalTrade({
          recommendation: dir,
          confidence: conf,
          is_optimal: isOptimal,
          price_target: predRes.price_target,
        });
      }

      const initBal = balanceRes?.initial_balance || 10000;
      const curBal = balanceRes?.balance || initBal;
      const totalPnl = curBal - initBal;
      const pnlPercent = initBal > 0 ? (totalPnl / initBal) * 100 : 0;
      setPnl({ value: totalPnl, percent: pnlPercent });
    } catch (err) {
      setError('Error al cargar datos');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [fetchData]);

  useEffect(() => {
    const now = Date.now();
    const prices = [];
    for (let i = 61; i >= 0; i--) {
      const d = new Date(now - i * 3600000);
      const price = 3.70 + Math.sin(i * 0.1) * 0.05 + (Math.random() - 0.5) * 0.02;
      prices.push({
        date: d.toISOString().split('T')[0] + ' ' + d.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' }),
        price: parseFloat(price.toFixed(4)),
      });
    }
    setPriceHistory(prices);
  }, []);

  const handleSelectBank = (bank) => {
    setSelectedBank(bank);
    setBankChecked(false);
    setBankOverlayOpen(false);
  };

  const handleToggleBank = () => {
    setBankChecked((prev) => !prev);
  };

  const handleCreateOrder = async (side, amount) => {
    if (!selectedBank || !amount || parseFloat(amount) <= 0) return;
    try {
      const res = await accountAPI.createOrder({
        pair: 'PEN/USD',
        side,
        amount: parseFloat(amount),
        price: currentPrice || 3.76,
        bank_id: selectedBank.id,
      });
      setOrders((prev) => [res, ...prev]);
      fetchData();
    } catch {
      setError('Error al crear orden');
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <p>Cargando dashboard...</p>
      </div>
    );
  }

  return (
    <div>
      <div className="dashboard-top-row">
        <div className="balance-card">
          <div className="balance-card-header">
            <span className="section-header">Saldo de cuenta</span>
            <button
              className="btn-toggle-visibility"
              onClick={() => setBalanceVisible(!balanceVisible)}
              title={balanceVisible ? 'Ocultar saldo' : 'Mostrar saldo'}
            >
              {balanceVisible ? '👁' : '🙈'}
            </button>
          </div>
          <div className="balance-row">
            <span className="section-value">
              {balanceVisible
                ? (balance ? balance.balance.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '---')
                : '**.***,**'}
            </span>
            <span className="balance-currency">{balance ? balance.currency : ''}</span>
          </div>
        </div>

        <div className="balance-chart-card" style={{ position: 'relative' }}>
          <div className="chart-header">
            <span className="chart-title">Balance</span>
            <span className="chart-value">
              {balanceVisible
                ? (balance ? `$${balance.balance.toLocaleString('es-ES', { minimumFractionDigits: 2 })}` : '---')
                : '**.***,**'}
            </span>
            <button
              className="btn btn-sm btn-secondary"
              onClick={() => setBankOverlayOpen(!bankOverlayOpen)}
              style={{ marginLeft: 'auto', fontSize: '0.75rem' }}
            >
              Banco
            </button>
            {bankOverlayOpen && (
              <div style={{ position: 'absolute', top: '100%', right: 0, zIndex: 100 }}>
                <BankSelector
                  banks={banks}
                  selectedBank={selectedBank}
                  bankChecked={bankChecked}
                  onSelectBank={handleSelectBank}
                  onToggleBank={handleToggleBank}
                  onClose={() => setBankOverlayOpen(false)}
                />
              </div>
            )}
          </div>
          {selectedBank && (
            <div style={{ fontSize: '0.75rem', color: '#8892b0', marginBottom: '0.5rem' }}>
              Banco: {selectedBank.name} | Spread: {selectedBank.spread_multiplier.toFixed(10)}{' '}
              {bankChecked ? '✓ Activo' : ''}
            </div>
          )}
          <BalanceChart data={balanceHistory} />
        </div>
      </div>

      {error && <div className="alert-banner error">{error}</div>}

      <div className="dashboard-middle">
        <div className="pair-header">
          <span className="pair-name">PEN/USD</span>
          <span className="pair-subtitle">Peruvian Sol / US Dollar</span>
        </div>

        <div className="price-chart-card">
          <div className="chart-header">
            <span className="current-price">
              {currentPrice
                ? currentPrice.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
                : '---'}
            </span>
            <span className={`price-change ${pnl.value >= 0 ? 'positive' : 'negative'}`}>
              {pnl.value >= 0 ? '+' : ''}
              {pnl.value.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} USD
            </span>
          </div>
          <PriceChart data={priceHistory} />
          <div className="timeframe-selector">
            {['1D', '1W', '1M', '3M', '1Y', '5Y', 'Todo'].map((tf) => (
              <button
                key={tf}
                className={`timeframe-btn ${timeframe === tf ? 'active' : ''}`}
                onClick={() => setTimeframe(tf)}
              >
                {tf}
              </button>
            ))}
          </div>
        </div>

        <PnLDisplay pnl={pnl} />

        <div className="buysell-section">
          <BuySellCard
            side="buy"
            label="Comprar"
            onExecute={(amount) => handleCreateOrder('buy', amount)}
            disabled={!optimalTrade || !optimalTrade.is_optimal}
            optimal={optimalTrade && optimalTrade.is_optimal && optimalTrade.recommendation === 'buy'}
            price={currentPrice}
          />
          <BuySellCard
            side="sell"
            label="Vender"
            onExecute={(amount) => handleCreateOrder('sell', amount)}
            disabled={!optimalTrade || !optimalTrade.is_optimal}
            optimal={optimalTrade && optimalTrade.is_optimal && optimalTrade.recommendation === 'sell'}
            price={currentPrice}
          />
        </div>

        <OrderHistory orders={orders} />
      </div>
    </div>
  );
}

export default Dashboard;