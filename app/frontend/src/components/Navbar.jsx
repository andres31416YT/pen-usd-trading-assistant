import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { authAPI } from '../services/auth';

function Navbar({ user, onLogout }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef(null);
  const hasToken = localStorage.getItem('token') !== null;

  // Close menu when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setMenuOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Close menu on window resize to desktop
  useEffect(() => {
    function handleResize() {
      if (window.innerWidth > 768 && menuOpen) {
        setMenuOpen(false);
      }
    }
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [menuOpen]);

  // Prevent body scroll when mobile menu is open
  useEffect(() => {
    if (menuOpen && window.innerWidth <= 768) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [menuOpen]);

  const handleLogout = async () => {
    try {
      await authAPI.logout();
    } catch {
      // ignore
    }
    onLogout();
    setMenuOpen(false);
  };

  const toggleMenu = () => {
    setMenuOpen((prev) => !prev);
  };

  return (
    <nav className="navbar" ref={menuRef} aria-label="Navegación principal">
      <Link to="/" className="navbar-brand" onClick={() => setMenuOpen(false)}>
        PEN/USD Assistant
      </Link>

      {/* Hamburger toggle button */}
      <button
        className={`menu-toggle${menuOpen ? ' active' : ''}`}
        onClick={toggleMenu}
        aria-label={menuOpen ? 'Cerrar menú' : 'Abrir menú'}
        aria-expanded={menuOpen}
        type="button"
      >
        <span></span>
        <span></span>
        <span></span>
      </button>

      {/* Navigation links */}
      <div className={`navbar-links${menuOpen ? ' open' : ''}`} role="menubar">
        {hasToken ? (
          <>
            <span className="user-info" role="menuitem">
              <strong>{user?.username || 'Usuario'}</strong>
            </span>
            <button
              className="btn btn-secondary"
              onClick={handleLogout}
              role="menuitem"
              type="button"
            >
              Cerrar sesión
            </button>
          </>
        ) : (
          <>
            <Link to="/login" role="menuitem" onClick={() => setMenuOpen(false)}>
              Iniciar sesión
            </Link>
            <Link to="/register" role="menuitem" onClick={() => setMenuOpen(false)}>
              Registrarse
            </Link>
          </>
        )}
      </div>
    </nav>
  );
}

export default Navbar;
