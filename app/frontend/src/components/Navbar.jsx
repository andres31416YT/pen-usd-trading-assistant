import React from 'react';
import { Link } from 'react-router-dom';
import { authAPI } from '../services/auth';

function Navbar({ user, onLogout }) {
  const hasToken = localStorage.getItem('token') !== null;

  const handleLogout = async () => {
    try {
      await authAPI.logout();
    } catch {
      // ignore
    }
    onLogout();
  };

  return (
    <nav className="navbar">
      <Link to="/" className="navbar-brand">
        PEN/USD Assistant
      </Link>
      <div className="navbar-links">
        {hasToken ? (
          <>
            <span className="user-info">
              <strong>{user?.username || 'Usuario'}</strong>
            </span>
            <button className="btn btn-secondary" onClick={handleLogout}>
              Cerrar sesión
            </button>
          </>
        ) : (
          <>
            <Link to="/login">Iniciar sesión</Link>
            <Link to="/register">Registrarse</Link>
          </>
        )}
      </div>
    </nav>
  );
}

export default Navbar;