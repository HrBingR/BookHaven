// src/App.tsx
import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Home from './components/Home';
import Authors from './components/Authors';
import AuthorPage from './components/AuthorPage';
import Reader from "./components/Reader.tsx";
import 'bootstrap/dist/css/bootstrap.min.css';
import '@fortawesome/fontawesome-free/css/all.min.css';

const App: React.FC = () => {
  return (
    <Router>
      <div className="d-flex">
        <Sidebar />
        <div className="flex-grow-1 d-flex flex-column">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/authors" element={<Authors />} /> {/* Add the Authors route */}
            <Route path="/authors/:authorName" element={<AuthorPage />} />
            <Route path="/read/:identifier" element={<Reader />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
};

export default App;
