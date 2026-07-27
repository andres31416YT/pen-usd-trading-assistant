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

  useEffect(() => {
    if (banks.length > 0 && !selectedBank) {
      const defaultBank = banks.find((b) => b.name === "Sin banco") || banks[0];
      setSelectedBank(defaultBank);
      setBankChecked(true);
    }
  }, [banks, selectedBank]);
  const [balance, setBalance] = useState(null);
  const [solBalance, setSolBalance] = useState(null);
  const [balanceHistory, setBalanceHistory] = useState([]);
  const [currentPrice, setCurrentPrice] = useState(null);
  const [priceHistory, setPriceHistory] = useState([]);
  const [priceHistoryLoading, setPriceHistoryLoading] = useState(true);
  const [optimalTrade, setOptimalTrade] = useState(null);
  const [orders, setOrders] = useState([]);
  const [pnl, setPnl] = useState({ value: 0, percent: 0 });
  const [timeframe, setTimeframe] = useState('1M');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [bankOverlayOpen, setBankOverlayOpen] = useState(false);
  const [bankChecked, setBankChecked] = useState(false);
  const [balanceVisible, setBalanceVisible] = useState(true);
  const [solBalanceVisible, setSolBalanceVisible] = useState(true);

  const EyeOpenIcon = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );

  const EyeClosedIcon = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
      <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
      <path d="M14.12 14.12a3 3 0 1 1-4.24-4.24" />
      <line x1="1" y1="1" x2="23" y2="23" />
    </svg>
  );

  const fetchData = useCallback(async () => {
    setError('');
    const currentSpread = selectedBank?.spread_multiplier ?? 1;
    try {
      const [banksRes, balanceRes, historyRes, predRes, ordersRes, solBalanceRes] = await Promise.all([
        bankAPI.listBanks(),
        accountAPI.getBalance(),
        accountAPI.getBalanceHistory(30),
        tradingAPI.getPrediction({ spread_multiplier: currentSpread }),
        accountAPI.getOrders(),
        accountAPI.getSolBalance(),
      ]);
      setBanks(banksRes);
      setBalance(balanceRes);
      setSolBalance(solBalanceRes);
      setBalanceHistory(historyRes);
      setOrders(ordersRes);

      if (predRes) {
        setCurrentPrice(predRes.current_price || predRes.price_target || null);
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
  }, [selectedBank]);

  const timeframeToDays = {
    '1D': 1,
    '1W': 7,
    '1M': 30,
    '3M': 90,
    '1Y': 365,
    '5Y': 1825,
    'Todo': 3650,
  };

  const fetchPriceHistory = useCallback(async () => {
    setPriceHistoryLoading(true);
    setError('');
    try {
      const res = await tradingAPI.getPriceHistory({ pair: 'PEN/USD', timeframe });
      const data = (res?.data || []).map((item) => ({
        date: item.date,
        price: parseFloat(item.price),
      }));
      setPriceHistory(data);
    } catch (err) {
      setError('Error al cargar historial de precios');
      setPriceHistory([]);
    } finally {
      setPriceHistoryLoading(false);
    }
  }, [timeframe]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [fetchData]);

  useEffect(() => {
    fetchPriceHistory();
  }, [fetchPriceHistory]);

  const spreadMultiplier = selectedBank?.spread_multiplier ?? 1;
  const adjustedPriceHistory = priceHistory.map((d) => ({
    ...d,
    price: d.price * spreadMultiplier,
  }));
  const adjustedCurrentPrice = currentPrice ? currentPrice * spreadMultiplier : null;

  const handleSelectBank = (bank) => {
    setSelectedBank(bank);
    setBankChecked(bank !== null);
    setBankOverlayOpen(false);
    fetchPriceHistory();
  };

  const handleCreateOrder = async (side, amount) => {
    if (!selectedBank || !amount || parseFloat(amount) <= 0) return;
    try {
      const res = await accountAPI.createOrder({
        pair: 'PEN/USD',
        side,
        amount: parseFloat(amount),
        price: adjustedCurrentPrice || currentPrice || 3.76,
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

  const buyRecommended = optimalTrade && optimalTrade.recommendation === 'buy';
  const sellRecommended = optimalTrade && optimalTrade.recommendation === 'sell';

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
              {balanceVisible ? <EyeOpenIcon /> : <EyeClosedIcon />}
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
            <div style={{ position: 'relative', display: 'inlineFlex', marginLeft: 'auto' }}>
              <button
                className="btn btn-sm btn-secondary"
                onClick={() => setBankOverlayOpen(!bankOverlayOpen)}
                style={{ fontSize: '0.75rem' }}
              >
                Banco
              </button>
              {bankOverlayOpen && (
                <BankSelector
                  banks={banks}
                  selectedBank={selectedBank}
                  onSelectBank={handleSelectBank}
                />
              )}
            </div>
          </div>
          {selectedBank && (
            <div style={{ fontSize: '0.75rem', color: '#8892b0', marginBottom: '0.5rem' }}>
              Banco: {selectedBank.name} | Spread: {selectedBank.spread_multiplier.toFixed(10)}{' '}
              {bankChecked ? '✓ Activo' : ''}
            </div>
          )}
          <BalanceChart data={balanceHistory} />
        </div>

        <div className="balance-card sol-balance-card">
          <div className="balance-card-header">
            <span className="section-header">Saldo en Soles</span>
            <button
              className="btn-toggle-visibility"
              onClick={() => setSolBalanceVisible(!solBalanceVisible)}
              title={solBalanceVisible ? 'Ocultar saldo' : 'Mostrar saldo'}
            >
              {solBalanceVisible ? <EyeOpenIcon /> : <EyeClosedIcon />}
            </button>
          </div>
          <div className="balance-row">
            <span className="section-value sol-value">
              {solBalanceVisible
                ? (solBalance
                    ? solBalance.balance.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
                    : '---')
                : '**.***,**'}
            </span>
            <span className="balance-currency">{solBalance ? solBalance.currency : ''}</span>
          </div>
          <div className="balance-row sol-usd-row">
            <span className="balance-label">Equivalente USD</span>
            <span className="section-value sol-usd-value">
              {solBalanceVisible && solBalance
                ? `$${solBalance.usd_balance.toLocaleString('es-ES', { minimumFractionDigits: 2 })}`
                : '---'}
            </span>
          </div>
        </div>
      </div>

      {error && <div className="alert-banner error">{error}</div>}

      <div className="dashboard-middle">
        <div className="pair-header">
          <span className="pair-name">USD/PEN</span>
          <span className="pair-subtitle">US Dollar / Peruvian Sol</span>
        </div>

        <div className="price-chart-card">
          <div className="chart-header">
          <span className="current-price">
                {adjustedCurrentPrice
                  ? `S/. ${adjustedCurrentPrice.toLocaleString('es-ES', { minimumFractionDigits: 3, maximumFractionDigits: 3 })}`
                  : '---'}
              </span>
            {priceHistory && priceHistory.length >= 2 && (() => {
                const start = priceHistory[0].price;
                const end = priceHistory[priceHistory.length - 1].price;
                const change = start !== 0 ? ((end - start) / start) * 100 : 0;
                return (
                  <span className={`price-change ${change >= 0 ? 'positive' : 'negative'}`}>
                    {change >= 0 ? '+' : ''}
                    {change.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}%
                  </span>
                );
              })()}
          </div>
          <PriceChart data={adjustedPriceHistory} />
          <div className="timeframe-selector">
            {['1D', '5D', '1M', '1Y', '5Y', 'Max'].map((tf) => (
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
            disabled={!buyRecommended}
            optimal={buyRecommended}
            confidence={optimalTrade ? optimalTrade.confidence : null}
            recommendation={optimalTrade ? optimalTrade.recommendation : null}
            price={adjustedCurrentPrice}
          />
          <BuySellCard
            side="sell"
            label="Vender"
            onExecute={(amount) => handleCreateOrder('sell', amount)}
            disabled={!sellRecommended}
            optimal={sellRecommended}
            confidence={optimalTrade ? optimalTrade.confidence : null}
            recommendation={optimalTrade ? optimalTrade.recommendation : null}
            price={adjustedCurrentPrice}
          />
        </div>

        <OrderHistory orders={orders} />
      </div>
    </div>
  );
}

export default Dashboard;