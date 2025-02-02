// src/components/Sidebar.tsx
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Button } from 'react-bootstrap';
import AccountModal from './AccountModal';
import AdminModal from './AdminModal';
import {useConfig} from "../context/ConfigProvider.tsx";

const Sidebar: React.FC<{ isLoggedIn: boolean, isAdmin: boolean, onLogout: () => void }> = ({ isLoggedIn, isAdmin, onLogout }) => {
    const [isOpen, setIsOpen] = useState(true);
    const [isMobileView, setIsMobileView] = useState(false);
    const [showAccountModal, setShowAccountModal] = useState(false);
    const [showAdminModal, setShowAdminModal] = useState(false);
    const { UI_BASE_COLOR } = useConfig();

    useEffect(() => {
        const handleResize = () => {
            if (window.innerWidth < 780) {
                setIsMobileView(true);
                setIsOpen(false);
            } else {
                setIsMobileView(false);
                setIsOpen(true);
            }
        };
        handleResize();
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
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
                    minHeight: '100vh',
                    overflow: isMobileView && !isOpen ? 'hidden' : 'visible',
                    transition: 'width 0.3s ease, left 0.3s ease',
                    zIndex: isMobileView ? 999 : 'auto',
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
                                onClick={() => setShowAccountModal(true)}
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
            {isMobileView && (
                <Button
                    variant={UI_BASE_COLOR}
                    className="toggle-sidebar-btn"
                    onClick={toggleSidebar}
                    style={{
                        position: 'fixed',
                        top: '10px',
                        left: isOpen ? '210px' : '10px',
                        zIndex: 1000,
                        background: 'rgba(0, 0, 0, 0.8)',
                        color: '#fff',
                        border: 'none',
                        padding: '8px 12px',
                        cursor: 'pointer',
                        borderRadius: '4px',
                    }}
                >
                    {isOpen ? 'Close' : 'Menu'}
                </Button>
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