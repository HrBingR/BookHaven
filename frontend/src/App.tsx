// src/App.tsx
import React, { useState, useEffect } from 'react';
import {BrowserRouter as Router, Route, Routes, Navigate} from 'react-router-dom';
import { jwtDecode } from 'jwt-decode';
import Sidebar from './components/Sidebar';
import Home from './components/Home';
import Authors from './components/Authors';
import AuthorPage from './components/AuthorPage';
import Reader from "./components/Reader.tsx";
import Login from './components/Login.tsx';
import OTP from './components/Otp.tsx';
import '@fortawesome/fontawesome-free/css/all.min.css';
import { useConfig } from './context/ConfigProvider';

interface DecodedToken {
  token_type: string;
  user_is_admin: boolean;
  user_id: number;
  exp?: number;
}

interface DecodedCFToken {
  token_type: string;
  user_is_admin: boolean;
  user_id: number;
  iss: string;
  exp?: number;
}

const App: React.FC = () => {
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(false);
  const [isAdmin, setIsAdmin] = useState<boolean>(false);
  const { CF_ACCESS_AUTH } = useConfig();

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const decoded: DecodedToken = jwtDecode(token);
        if (decoded.token_type === 'login') {
          setIsLoggedIn(true);
        }
        if (decoded.user_is_admin) {
          setIsAdmin(true)
        }
      } catch (err) {
        console.error('Invalid token or decoding error:', err);
        setIsLoggedIn(false);
      }
    }
  }, []);

  const handleLogin = (token: string) => {
    try {
      const decoded: DecodedToken = jwtDecode(token);

      if (decoded.token_type === 'login') {
        localStorage.setItem('token', token);
        setIsLoggedIn(true);
      } else if (decoded.token_type === 'totp') {
        localStorage.setItem('token', token);
        setIsLoggedIn(false);
      } else {
        throw new Error('Unknown token type.');
      }
    } catch (error) {
      console.error('Failed to process token:', error);
      alert('Invalid login attempt. Please try again.');
      setIsLoggedIn(false);
    }
  };

  const handleLogout = () => {
    const token = localStorage.getItem('token');
    if (!token) {
      // No token found, just do your standard logout flow
      setIsLoggedIn(false);
      return;
    }
    console.log(CF_ACCESS_AUTH)
    if (CF_ACCESS_AUTH) {
      const cf_auth_token_decoded: DecodedCFToken = jwtDecode(token);
      console.log(cf_auth_token_decoded)
      const baseUrl = cf_auth_token_decoded.iss.endsWith('/') ? cf_auth_token_decoded.iss.slice(0, -1) : cf_auth_token_decoded.iss;
      const logoutUrl = `${baseUrl}/cdn-cgi/access/logout`;
      console.log(`redirecting to: ${logoutUrl}`)
      window.location.href = logoutUrl
      // localStorage.removeItem('token');
      // setIsLoggedIn(false);
    } else {
      localStorage.removeItem('token');
      setIsLoggedIn(false);
      // window.location.reload(); // Optional: reload to reset state
    }
  };

  const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const token = localStorage.getItem('token');
    if (!token) {
      return <Navigate to="/login" replace />;
    }

    try {
      const decoded: DecodedToken = jwtDecode(token);
      if (decoded.token_type !== 'login') {
        return <Navigate to="/otp" replace />;
      }
      return <>{children}</>;
    } catch (err) {
      console.error('Token validation failed:', err);
      return <Navigate to="/login" replace />;
    }
  };

  return (
      <Router>
        <div className="d-flex">
          <Sidebar isLoggedIn={isLoggedIn} isAdmin={isAdmin} onLogout={handleLogout} />
          <div className="flex-grow-1 d-flex flex-column">
            <Routes>
              <Route path="/" element={<ProtectedRoute><Home isLoggedIn={isLoggedIn} /></ProtectedRoute>} />
              <Route path="/authors" element={<ProtectedRoute><Authors /></ProtectedRoute>} />
              <Route path="/authors/:authorName" element={<ProtectedRoute><AuthorPage isLoggedIn={isLoggedIn} /></ProtectedRoute>} />
              <Route path="/read/:identifier" element={<ProtectedRoute><Reader /></ProtectedRoute>} />
              <Route path="/login" element={<Login onLogin={handleLogin}/>} />
              <Route path="/otp" element={<OTP />} />
            </Routes>
          </div>
        </div>
      </Router>
  );
};

export default App;