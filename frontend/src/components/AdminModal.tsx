import React, { useEffect, useState } from 'react';
import { Modal, Button, Table, Alert } from 'react-bootstrap';
import apiClient from '../utilities/apiClient';
import {CSSTransition, SwitchTransition} from "react-transition-group";
import {useConfig} from "../context/ConfigProvider.tsx";

type AdminModalProps = {
    onClose: () => void;
    show: boolean;
};

const AdminModal: React.FC<AdminModalProps> = ({ onClose, show }) => {
    const [view, setView] = useState<'main' | 'change-email' | 'reset-password' | 'unlink-oidc' | 'register'>('main');
    const [users, setUsers] = useState([]);
    const [selectedUserId, setSelectedUserId] = useState<number | null>(null); // ID of the user being acted upon
    const [email, setEmail] = useState('');
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [adminStatus, setAdminStatus] = useState<boolean | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);
    const { UI_BASE_COLOR } = useConfig();

    useEffect(() => {
        fetchAllUsers();
    }, []);

    const fetchAllUsers = async () => {
        try {
            const response = await apiClient.get('/api/admin/users');
            setUsers(response.data);
        } catch (err: any) {
            setError(err.message || 'Failed to fetch users.');
        }
    };

    const handleResetPassword = async () => {
        if (!selectedUserId) return;

        try {
            await apiClient.post(`/api/admin/users/${selectedUserId}/reset-password`, {
                new_password: password,
            });
            setSuccessMessage('Password reset successfully.');
            setView('main');
        } catch (err: any) {
            setError(err.message || 'Failed to reset password.');
        }
    };

    const handleMfaReset = async () => {
        if (!selectedUserId) return;
        try {
            await apiClient.post(`/api/admin/users/${selectedUserId}/reset-mfa`, {});
            setSuccessMessage('MFA reset successfully.');
            fetchAllUsers();
        } catch (err: any) {
            setError(err.message || 'Failed to reset MFA.');
        }
    }

    const handleChangeEmail = async () => {
        if (!selectedUserId) return;

        try {
            await apiClient.patch(`/api/admin/users/${selectedUserId}/change-email`, {
                new_email: email,
            });
            setSuccessMessage('Email changed successfully.');
            setView('main');
        } catch (err: any) {
            setError(err.message || 'Failed to change email.');
        }
    };

    const handleAdminStatus = async () => {
        if (!selectedUserId) return;
        try {
            await apiClient.patch(`/api/admin/users/${selectedUserId}/admin-status`, {
                is_admin: adminStatus,
            });
            setSuccessMessage('Admin status updated successfully');
            fetchAllUsers();
        } catch (err: any) {
            setError(err.message || "Failed to update admin status.");
        }
    }

    const handleRegisterUser = async () => {
        try {
            await apiClient.post('/api/admin/users/register', {
                username: username,
                email: email,
                password: password,
            });
            setSuccessMessage('User registered successfully.');
            fetchAllUsers();
            setView('main');
        } catch (err: any) {
            setError(err.message || 'Failed to register user.');
        }
    };

    const handleDeleteUser = async () => {
        if (!selectedUserId) return;
        try {
            await apiClient.delete(`/api/admin/users/${selectedUserId}/delete`, {});
            setSuccessMessage('User deleted successfully.')
            fetchAllUsers();
        } catch (err: any) {
            setError(err.message || "Failed to delete user.");
        }
    }

    const handleUnlinkOidc = async () => {
        if (!selectedUserId) return;
        try {
            await apiClient.patch(`/api/admin/users/${selectedUserId}/unlink-oidc`, {
                new_password:password
            });
            setSuccessMessage("User unlinked from OIDC successfully.")
            fetchAllUsers();
        } catch (err: any) {
            setError(err.message || "Failed to unlink user from OIDC.")
        }
    }

    const handleCancel = () => {
        setView('main');
        setError(null);
        setSuccessMessage(null);
        setEmail('');
        setPassword('');
    };

    const handleClose = () => {
        setView("main");
        setError(null);
        setSuccessMessage(null);
        setEmail('');
        setPassword('');
        onClose();
    }

    function renderView() {
        switch (view) {
            case "main":
                return (
                    <div>
                        <p
                            style={{ color: "grey" }}
                        >
                            Note: Only partial account management is available for OIDC users.
                        </p>
                        <Table striped bordered hover>
                            <thead>
                            <tr>
                                <th>UID</th>
                                <th>Created At</th>
                                <th>Last Login</th>
                                <th>Auth Type</th>
                                <th>Username</th>
                                <th>Email</th>
                                <th>Admin Status</th>
                                <th>Reset Password</th>
                                <th>Reset MFA</th>
                                <th>Delete User</th>
                            </tr>
                            </thead>
                            <tbody>
                            {users.map((user: any) => (
                                <tr key={user.id}>
                                    <td>{user.id}</td>
                                    <td>{user.created_at}</td>
                                    <td>{user.last_login}</td>
                                    <td>
                                        <Button
                                            variant={UI_BASE_COLOR}
                                            size="sm"
                                            onClick={() => {
                                                setSelectedUserId(user.id);
                                                setView('unlink-oidc')
                                            }}
                                            disabled={user.auth_type === 'local'}
                                        >
                                            {user.auth_type}
                                        </Button>
                                    </td>
                                    <td>{user.username}</td>
                                    <td>
                                        <Button
                                            variant={UI_BASE_COLOR}
                                            size="sm"
                                            onClick={() => {
                                                setSelectedUserId(user.id);
                                                setEmail(user.email);
                                                setView('change-email');
                                            }}
                                            disabled={user.auth_type === 'oidc'}
                                        >
                                            {user.email}
                                        </Button>
                                    </td>
                                    <td>
                                        <Button
                                            variant={UI_BASE_COLOR}
                                            size="sm"
                                            onClick={() => {
                                                setSelectedUserId(user.id);
                                                setAdminStatus(!user.is_admin);
                                                handleAdminStatus();
                                            }}
                                        >
                                            {user.is_admin ? 'Admin' : 'User'}
                                        </Button>
                                    </td>
                                    <td>
                                        <Button
                                            variant={UI_BASE_COLOR}
                                            size="sm"
                                            onClick={() => {
                                                setSelectedUserId(user.id);
                                                setView('reset-password');
                                            }}
                                            disabled={user.auth_type === 'oidc'}
                                        >
                                            Reset
                                        </Button>
                                    </td>
                                    <td>
                                        <Button
                                            variant={UI_BASE_COLOR}
                                            size="sm"
                                            onClick={() => {
                                                setSelectedUserId(user.id);
                                                handleMfaReset();
                                            }}
                                            disabled={user.auth_type === 'oidc'}
                                        >
                                            Reset
                                        </Button>
                                    </td>
                                    <td>
                                        <Button
                                            variant="danger"
                                            size="sm"
                                            onClick={() => {
                                                setSelectedUserId(user.id);
                                                handleDeleteUser();
                                            }}
                                        >
                                            Delete
                                        </Button>
                                    </td>
                                </tr>
                            ))}
                            </tbody>
                        </Table>
                        <Button
                            variant={UI_BASE_COLOR}
                            className="mt-3"
                            onClick={() => setView('register')}
                        >
                            Register New User
                        </Button>
                    </div>
                );
            case "change-email":
                return (
                    <div>
                        <h5>Change Email</h5>
                        <input
                            type="email"
                            placeholder="Enter new email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="form-control"
                        />
                        <div className="mt-3">
                            <Button variant={UI_BASE_COLOR} onClick={handleChangeEmail}>
                                Submit
                            </Button>{' '}
                            <Button variant="secondary" onClick={handleCancel}>
                                Cancel
                            </Button>
                        </div>
                    </div>
                );
            case "reset-password":
                return (
                    <div>
                        <h5>Reset Password</h5>
                        <input
                            type="password"
                            placeholder="Enter new password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="form-control"
                        />
                        <div className="mt-3">
                            <Button variant={UI_BASE_COLOR} onClick={handleResetPassword}>
                                Submit
                            </Button>{' '}
                            <Button variant="secondary" onClick={handleCancel}>
                                Cancel
                            </Button>
                        </div>
                    </div>
                );
            case "unlink-oidc":
                return (
                    <div>
                        <h5>Unlink account from OIDC</h5>
                        <p
                            style={{ color: "red" }}
                        >
                            Warning: Local password and MFA will be reset when unlinking OIDC.
                        </p>
                        <input
                            type="password"
                            placeholder="Enter new local password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="form-control"
                        />
                        <div className="mt-3">
                            <Button variant={UI_BASE_COLOR} onClick={handleUnlinkOidc}>
                                Submit
                            </Button>{' '}
                            <Button variant="secondary" onClick={handleCancel}>
                                Cancel
                            </Button>
                        </div>
                    </div>
                );
            case "register":
                return (
                    <div>
                        <h5>Register New User</h5>
                        <input
                            type="email"
                            placeholder="Email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="form-control mb-2"
                        />
                        <input
                            type="text"
                            placeholder="Username"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            className="form-control mb-2"
                        />
                        <input
                            type="password"
                            placeholder="Password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="form-control mb-2"
                        />
                        <div>
                            <Button variant={UI_BASE_COLOR} onClick={handleRegisterUser}>
                                Register
                            </Button>{' '}
                            <Button variant="secondary" onClick={handleCancel}>
                                Cancel
                            </Button>
                        </div>
                    </div>
                );
        }
    }

    return (
        <Modal show={show} onHide={handleClose} centered dialogClassName="modal-90w">
            <Modal.Header closeButton>
                <Modal.Title>User Management</Modal.Title>
            </Modal.Header>
            <Modal.Body>
                {error && <Alert variant="danger">{error}</Alert>}
                {successMessage && <Alert variant="success">{successMessage}</Alert>}
                <SwitchTransition mode="out-in">
                    <CSSTransition
                        key={view}
                        timeout={100}
                        classNames="fade"
                        unmountOnExit
                    >
                        <div>{renderView()}</div>
                    </CSSTransition>
                </SwitchTransition>
            </Modal.Body>
        </Modal>
    );
};

export default AdminModal;