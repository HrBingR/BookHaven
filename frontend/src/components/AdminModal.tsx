import React, { useEffect, useState } from 'react';
import { Modal, Button, Table, Alert, DropdownButton, Dropdown } from 'react-bootstrap';
import apiClient from '../utilities/apiClient';
import {CSSTransition, SwitchTransition} from "react-transition-group";
import {useConfig} from "../context/ConfigProvider.tsx";
import { UserRole } from '../utilities/roleUtils';

type AdminModalProps = {
    onClose: () => void;
    show: boolean;
};

// Type for API error responses
interface ApiError {
    response?: {
        data?: {
            error?: string;
        };
    };
    message?: string;
}

// Type for user data from the API - FIXED to match actual API response
interface User {
    id: number;
    created_at: string;
    last_login: string;
    auth_type: 'local' | 'oidc';
    username: string;
    email: string;
    role: UserRole;  // Changed from user_role to role to match API
}

const AdminModal: React.FC<AdminModalProps> = ({ onClose, show }) => {
    const [view, setView] = useState<'main' | 'change-email' | 'reset-password' | 'unlink-oidc' | 'register'>('main');
    const [users, setUsers] = useState<User[]>([]);
    const [selectedUserId, setSelectedUserId] = useState<number | null>(null); // ID of the user being acted upon
    const [email, setEmail] = useState('');
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const { UI_BASE_COLOR, OIDC_ENABLED, CF_ACCESS_AUTH } = useConfig();

    const availableRoles: UserRole[] = ['user', 'editor', 'admin'];
    
    useEffect(() => {
        if (show) {
            void fetchAllUsers();
        }
    }, [show]);

    // Helper function to extract error message from API responses
    const getErrorMessage = (err: unknown, fallbackMessage: string): string => {
        const apiError = err as ApiError;
        return apiError.response?.data?.error || apiError.message || fallbackMessage;
    };

    const fetchAllUsers = async () => {
        setLoading(true);
        try {
            const response = await apiClient.get('/api/admin/users');
            console.log('Users API response:', response.data); // Debug log
            setUsers(response.data);
        } catch (err: unknown) {
            setError(getErrorMessage(err, 'Failed to fetch users.'));
        } finally {
            setLoading(false);
        }
    };

    const handleResetPassword = async () => {
        if (!selectedUserId || CF_ACCESS_AUTH) return;

        try {
            await apiClient.post(`/api/admin/users/${selectedUserId}/reset-password`, {
                new_password: password,
            });
            setSuccessMessage('Password reset successfully.');
            setView('main');
        } catch (err: unknown) {
            setError(getErrorMessage(err, 'Failed to reset password.'));
        }
    };

    const handleMfaReset = async () => {
        if (!selectedUserId || CF_ACCESS_AUTH) return;
        try {
            await apiClient.post(`/api/admin/users/${selectedUserId}/reset-mfa`, {});
            setSuccessMessage('MFA reset successfully.');
            await fetchAllUsers();
        } catch (err: unknown) {
            setError(getErrorMessage(err, 'Failed to reset MFA.'));
        }
    }

    const handleChangeEmail = async () => {
        if (!selectedUserId || CF_ACCESS_AUTH) return;

        try {
            await apiClient.patch(`/api/admin/users/${selectedUserId}/change-email`, {
                new_email: email,
            });
            setSuccessMessage('Email changed successfully.');
            setView('main');
        } catch (err: unknown) {
            setError(getErrorMessage(err, 'Failed to change email.'));
        }
    };

    // FIXED: Accept userId as parameter instead of relying on selectedUserId state
    const handleUserRole = async (userId: number, newRole: UserRole) => {
        try {
            await apiClient.patch(`/api/admin/users/${userId}/role`, {
                role: newRole,
            });
            setSuccessMessage('User role updated successfully');
            await fetchAllUsers();
        } catch (err: unknown) {
            setError(getErrorMessage(err, "Failed to update user role."));
        }
    }

    const handleRegisterUser = async () => {
        if (CF_ACCESS_AUTH) return;
        try {
            await apiClient.post('/api/admin/users/register', {
                username: username,
                email: email,
                password: password,
            });
            setSuccessMessage('User registered successfully.');
            await fetchAllUsers();
            setView('main');
        } catch (err: unknown) {
            setError(getErrorMessage(err, 'Failed to register user.'));
        }
    };

    const handleDeleteUser = async () => {
        if (!selectedUserId) return;
        try {
            await apiClient.delete(`/api/admin/users/${selectedUserId}/delete`, {});
            setSuccessMessage('User deleted successfully.')
            await fetchAllUsers();
        } catch (err: unknown) {
            setError(getErrorMessage(err, "Failed to delete user."));
        }
    }

    const handleUnlinkOidc = async () => {
        if (!selectedUserId) return;
        try {
            await apiClient.patch(`/api/admin/users/${selectedUserId}/unlink-oidc`, {
                new_password:password
            });
            setSuccessMessage("User unlinked from OIDC successfully.")
            await fetchAllUsers();
        } catch (err: unknown) {
            setError(getErrorMessage(err, "Failed to unlink user from OIDC."));
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

    // Helper function to get user's current role with safety check - FIXED
    const getUserRole = (user: User): UserRole => {
        return user.role || 'user'; // Changed from user.user_role to user.role
    };

    // Helper function to capitalize role names for display with safety check
    const capitalizeRole = (role: UserRole | undefined): string => {
        if (!role) return 'User'; // Fallback if role is undefined
        return role.charAt(0).toUpperCase() + role.slice(1);
    };

    function renderView() {
        switch (view) {
            case "main":
                return (
                    <div>
                        <p style={{ color: "grey" }}>
                            Note: Only partial account management is available for OIDC users.
                        </p>
                        
                        {loading ? (
                            <div className="text-center">
                                <p>Loading users...</p>
                            </div>
                        ) : (
                            <Table striped bordered hover>
                                <thead>
                                <tr>
                                    <th>UID</th>
                                    <th>Created At</th>
                                    <th>Last Login</th>
                                    { OIDC_ENABLED && ( <th>Auth Type</th> )}
                                    <th>Username</th>
                                    <th>Email</th>
                                    <th>Role</th>
                                    <th>Reset Password</th>
                                    <th>Reset MFA</th>
                                    <th>Delete User</th>
                                </tr>
                                </thead>
                                <tbody>
                                {users.map((user: User) => {
                                    const currentUserRole = getUserRole(user);
                                    console.log('Rendering user:', user.username, 'with role:', currentUserRole); // Debug log
                                    
                                    return (
                                        <tr key={user.id}>
                                            <td>{user.id}</td>
                                            <td>{user.created_at}</td>
                                            <td>{user.last_login}</td>
                                            { OIDC_ENABLED && (
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
                                            )}
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
                                                    disabled={user.auth_type === 'oidc' || CF_ACCESS_AUTH}
                                                >
                                                    {user.email}
                                                </Button>
                                            </td>
                                            <td>
                                                <DropdownButton
                                                    as="div"
                                                    variant={UI_BASE_COLOR}
                                                    size="sm"
                                                    title={capitalizeRole(currentUserRole)}
                                                    onSelect={(selectedRole) => {
                                                        void handleUserRole(user.id, selectedRole as UserRole);
                                                    }}
                                                >
                                                    {availableRoles.map((role) => (
                                                        <Dropdown.Item 
                                                            key={role} 
                                                            eventKey={role}
                                                            active={currentUserRole === role}
                                                        >
                                                            {capitalizeRole(role)}
                                                        </Dropdown.Item>
                                                    ))}
                                                </DropdownButton>
                                            </td>
                                            <td>
                                                <Button
                                                    variant={UI_BASE_COLOR}
                                                    size="sm"
                                                    onClick={() => {
                                                        setSelectedUserId(user.id);
                                                        setView('reset-password');
                                                    }}
                                                    disabled={user.auth_type === 'oidc' || CF_ACCESS_AUTH}
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
                                                        void handleMfaReset();
                                                    }}
                                                    disabled={user.auth_type === 'oidc' || CF_ACCESS_AUTH}
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
                                                        void handleDeleteUser();
                                                    }}
                                                >
                                                    Delete
                                                </Button>
                                            </td>
                                        </tr>
                                    );
                                })}
                                </tbody>
                            </Table>
                        )}
                        
                        <Button
                            variant={UI_BASE_COLOR}
                            className="mt-3"
                            onClick={() => setView('register')}
                            disabled={CF_ACCESS_AUTH}
                        >
                            {CF_ACCESS_AUTH ? "Registration Managed via Cloudflare" : "Register New User"}
                        </Button>
                    </div>
                );
            case "change-email":
                if (CF_ACCESS_AUTH) {
                    return (
                        <div className="text-center">
                            <h5>Email Management Disabled</h5>
                            <p>Email changes are managed through Cloudflare Access.</p>
                            <Button variant="secondary" onClick={handleCancel}>
                                Back
                            </Button>
                        </div>
                    );
                }
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
                            <Button variant={UI_BASE_COLOR} onClick={() => void handleChangeEmail()}>
                                Submit
                            </Button>{' '}
                            <Button variant="secondary" onClick={handleCancel}>
                                Cancel
                            </Button>
                        </div>
                    </div>
                );
            case "reset-password":
                if (CF_ACCESS_AUTH) {
                    return (
                        <div className="text-center">
                            <h5>Password Management Disabled</h5>
                            <p>Password resets are managed through Cloudflare Access.</p>
                            <Button variant="secondary" onClick={handleCancel}>
                                Back
                            </Button>
                        </div>
                    );
                }
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
                            <Button variant={UI_BASE_COLOR} onClick={() => void handleResetPassword()}>
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
                        <p style={{ color: "red" }}>
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
                            <Button variant={UI_BASE_COLOR} onClick={() => void handleUnlinkOidc()}>
                                Submit
                            </Button>{' '}
                            <Button variant="secondary" onClick={handleCancel}>
                                Cancel
                            </Button>
                        </div>
                    </div>
                );
            case "register":
                if (CF_ACCESS_AUTH) {
                    return (
                        <div className="text-center">
                            <h5>Registration Disabled</h5>
                            <p>User registration is managed through Cloudflare Access.</p>
                            <Button variant="secondary" onClick={handleCancel}>
                                Back
                            </Button>
                        </div>
                    );
                }
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
                            <Button variant={UI_BASE_COLOR} onClick={() => void handleRegisterUser()}>
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