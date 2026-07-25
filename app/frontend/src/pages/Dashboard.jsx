import React, { useState, useEffect } from 'react';
import { authAPI, tradingAPI } from '../services/api';
import SignalCard from '../components/SignalCard';
import PredictionDisplay from '../components/PredictionDisplay';

function Dashboard({ user }) {
  const [signals, setSignals] = useState([]);
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('signals');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [signalsRes, predRes] = await Promise.all([
          tradingAPI.getSignals(),
          tradingAPI.getPrediction(),
        ]);
        setSignals(signalsRes.data);
        setPrediction(predRes.data);
      } catch (err) {
        setError('Error al cargar datos');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleRefresh = async () => {
    setLoading(true);
    setError('');
    try {
      const [signalsRes, predRes] = await Promise.all([
        tradingAPI.getSignals(),
        tradingAPI.getPrediction(),
      ]);
      setSignals(signalsRes.data);
      setPrediction(predRes.data);
    } catch {
      setError('Error al actualizar datos');
    } finally {
      setLoading(false);
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
      <h1 style={{ marginBottom: '0.5rem' }}>Dashboard</h1>
      <p style={{ color: '#8892b0', marginBottom: '1rem' }}>
        Bienvenido, <strong>{user.username}</strong>
      </p>

      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem' }}>
        <button
          className={`btn ${activeTab === 'signals' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveTab('signals')}
        >
          Señales
        </button>
        <button
          className={`btn ${activeTab === 'prediction' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveTab('prediction')}
        >
          Predicción
        </button>
        <button className="btn btn-secondary" onClick={handleRefresh}>
          Actualizar
        </button>
      </div>

      {error && <div className="alert-banner error">{error}</div>}

      {activeTab === 'signals' && (
        <div>
          {signals.length === 0 ? (
            <div className="card">
              <p>No hay señales disponibles.</p>
            </div>
          ) : (
            signals.map((signal) => (
              <SignalCard key={signal.id} signal={signal} />
            ))
          )}
        </div>
      )}

      {activeTab === 'prediction' && prediction && (
        <PredictionDisplay prediction={prediction} />
      )}
    </div>
  );
}

export default Dashboard;