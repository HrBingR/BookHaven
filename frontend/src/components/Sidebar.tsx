// src/components/Sidebar.tsx
import React from 'react';
import { Link } from 'react-router-dom';

const Sidebar: React.FC = () => {
  return (
    <div className="bg-light border-right" style={{ width: '200px', minHeight: '100vh' }}>
      <div className="sidebar-heading p-3">ePub Library</div>
      <div className="list-group list-group-flush">
        <Link to="/" className="list-group-item list-group-item-action bg-light">
          <i className="fas fa-home me-2"></i> Home
        </Link>
        <Link to="/authors" className="list-group-item list-group-item-action bg-light">
          <i className="fas fa-users me-2"></i> Authors {/* Add Authors link here */}
        </Link>
      </div>
    </div>
  );
};

export default Sidebar;