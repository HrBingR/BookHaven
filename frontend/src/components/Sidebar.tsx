// src/components/Sidebar.tsx
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

const Sidebar: React.FC = () => {
  const [isOpen, setIsOpen] = useState(true); // State to track sidebar toggle
  const [isMobileView, setIsMobileView] = useState(false); // State to handle mobile vs desktop view

  // Monitor viewport changes and determine if we're in a mobile view
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 780) {
        setIsMobileView(true);
        setIsOpen(false); // Close sidebar by default in mobile view
      } else {
        setIsMobileView(false);
        setIsOpen(true); // Ensure it's open by default in desktop view
      }
    };

    handleResize(); // Run on initial render
    window.addEventListener('resize', handleResize); // Attach event listener
    return () => window.removeEventListener('resize', handleResize); // Cleanup listener
  }, []);

  const toggleSidebar = () => {
    setIsOpen(!isOpen);
  };

  return (
    <>
      {/* Sidebar */}
      <div
        className={`sidebar bg-light border-right ${isMobileView ? (isOpen ? 'open' : 'closed') : ''}`}
        style={{
          width: isMobileView && !isOpen ? '0' : '200px', // Collapse on mobile when closed
          minHeight: '100vh',
          overflow: isMobileView && !isOpen ? 'hidden' : 'visible', // Manage overflow in mobile view
          position: isMobileView ? 'fixed' : 'relative', // Absolute overlay for mobile, inline for desktop
          transition: 'width 0.3s ease, left 0.3s ease', // Smooth animations for opening/closing
          zIndex: isMobileView ? 999 : 'auto', // Layered above content on mobile
        }}
      >
        <div className="sidebar-heading p-3">ePub Library</div>
        <div className="list-group list-group-flush">
          <Link to="/" className="list-group-item list-group-item-action bg-light"
          onClick={toggleSidebar}>
            <i className="fas fa-home me-2"></i> Home
          </Link>
          <Link to="/authors" className="list-group-item list-group-item-action bg-light"
          onClick={toggleSidebar}>
            <i className="fas fa-users me-2"></i> Authors
          </Link>
        </div>
      </div>

      {/* Toggle Button (Only appears in mobile view) */}
      {isMobileView && (
        <button
          className="toggle-sidebar-btn"
          onClick={toggleSidebar}
          style={{
            position: 'fixed',
            top: '10px',
            left: isOpen ? '210px' : '10px', // Adjust dynamic positioning
            zIndex: 1000, // Ensure it's above other elements
            background: 'rgba(0, 0, 0, 0.8)',
            color: '#fff',
            border: 'none',
            padding: '8px 12px',
            cursor: 'pointer',
            borderRadius: '4px',
          }}
        >
          {isOpen ? 'Close' : 'Menu'}
        </button>
      )}
    </>
  );
};

export default Sidebar;