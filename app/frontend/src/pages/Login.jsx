import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authAPI } from '../services/auth';

function Login({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const data = await authAPI.login(username, password);
      onLogin(data.access_token, data.user);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al iniciar sesión');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="form-container">
      <h2>Iniciar sesión</h2>
      {error && <div className="alert-banner error">{error}</div>}
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Usuario</label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            minLength={3}
          />
        </div>
        <div className="form-group">
          <label>Contraseña</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={6}
          />
        </div>
        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? 'Entrando...' : 'Entrar'}
        </button>
      </form>
      <p style={{ textAlign: 'center', marginTop: '1rem', fontSize: '0.9rem' }}>
        ¿No tienes cuenta? <Link to="/register">Regístrate</Link>
      </p>
    </div>
  );
}

export default Login;