import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authAPI } from '../services/auth';

function Navbar({ user, onLogout }) {
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await authAPI.logout();
    } catch {
      // ignore
    }
    localStorage.removeItem('token');
    onLogout();
    navigate('/login');
  };

  return (
    <nav className="navbar">
      <Link to="/" className="navbar-brand">
        PEN/USD Assistant
      </Link>
      <div className="navbar-links">
        {user ? (
          <>
            <span className="user-info">
              <strong>{user.username}</strong>
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