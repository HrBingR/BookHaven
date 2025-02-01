// src/components/Sidebar.tsx
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Button } from 'react-bootstrap';
import AccountModal from './AccountModal';
import AdminModal from './AdminModal';

const Sidebar: React.FC<{ isLoggedIn: boolean, isAdmin: boolean, onLogout: () => void }> = ({ isLoggedIn, isAdmin, onLogout }) => {
    const [isOpen, setIsOpen] = useState(true); // State to track sidebar toggle
    const [isMobileView, setIsMobileView] = useState(false); // State to handle mobile vs desktop view
    const [showAccountModal, setShowAccountModal] = useState(false); // State to show/hide account modal
    const [showAdminModal, setShowAdminModal] = useState(false);

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
    }, [])

    const toggleSidebar = () => {
        setIsOpen(!isOpen);
    };

    return (
        <>
            {/* Sidebar */}
            <div
                className={`sidebar bg-light border-right ${isMobileView ? (isOpen ? 'open' : 'closed') : ''}`}
                style={{
                    // width: isMobileView && !isOpen ? '0' : '19vw', // Collapse on mobile when closed
                    minHeight: '100vh',
                    overflow: isMobileView && !isOpen ? 'hidden' : 'visible', // Manage overflow in mobile view
                    // position: isMobileView ? 'fixed' : 'relative', // Absolute overlay for mobile, inline for desktop
                    transition: 'width 0.3s ease, left 0.3s ease', // Smooth animations for opening/closing
                    zIndex: isMobileView ? 999 : 'auto', // Layered above content on mobile
                }}
            >
                <div className="sidebar-heading p-3">BookHaven</div>
                <div className="list-group list-group-flush">
                    <Link to="/" className="list-group-item list-group-item-action bg-light"
                          onClick={toggleSidebar}>
                        <i className="fas fa-home me-2"></i> Home
                    </Link>
                    <Link to="/authors" className="list-group-item list-group-item-action bg-light"
                          onClick={toggleSidebar}>
                        <i className="fas fa-users me-2"></i> Authors
                    </Link>
                    {isLoggedIn && (
                        <>
                            <button
                                className="list-group-item list-group-item-action bg-light border-0"
                                onClick={() => setShowAccountModal(true)} // Show the Account Modal
                                style={{
                                    textAlign: 'left',
                                    background: 'none',
                                    outline: 'none',
                                    cursor: 'pointer',
                                }}
                            >
                                <i className="fas fa-gear me-2"></i> Account
                            </button>
                            {isAdmin && (
                                <button
                                    className="list-group-item list-group-item-action bg-light border-0"
                                    onClick={() => setShowAdminModal(true)}
                                    style={{
                                        textAlign: 'left',
                                        background: 'none',
                                        outline: 'none',
                                        cursor: 'pointer',
                                    }}
                                >
                                    <i className="fas fa-user-shield me-2"></i> Admin
                                </button>
                            )}
                        </>
                    )}
                </div>
                {/* Logout Button */}
                {isLoggedIn && (
                    <div
                        className="d-flex justify-content-center align-items-center p-3 mt-auto"
                        style={{
                            position: 'absolute',
                            top: '90vh',
                            width: '100%'
                        }}
                    >
                        <Button
                            onClick={onLogout}
                            variant="danger"
                            className="w-75"
                        >
                            Log Out
                        </Button>

                    </div> )}
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
            {/* Account Modal */}
            {isLoggedIn && (
                <AccountModal onClose={() => setShowAccountModal(false)} show={showAccountModal} />
            )}
            {isLoggedIn && isAdmin && (
                <AdminModal onClose={() => setShowAdminModal(false)} show={showAdminModal} />
            )}
        </>
    );
};

export default Sidebar;