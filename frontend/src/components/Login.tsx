import React, { useState } from 'react';
import { Button, Form, Modal } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import apiClient from '../utilities/apiClient';
import { jwtDecode } from 'jwt-decode';
import { useConfig } from '../context/ConfigProvider';

interface DecodedToken {
    token_type: string;
    exp: number;
}

const Login: React.FC<{ onLogin: (token: string) => void }> = ({ onLogin }) => {
    const [username, setUsername] = useState<string>('');
    const [password, setPassword] = useState<string>('');
    const [error, setError] = useState<string | null>(null);
    const navigate = useNavigate();
    const { UI_BASE_COLOR } = useConfig();

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        try {
            setError(null); // Reset errors
            const response = await apiClient.post('/login', { username, password });

            const token = response.data.token; // Assume token is returned as "token"
            onLogin(token);
            const decoded: DecodedToken = jwtDecode(token);

            // Save the token (e.g., to localStorage)
            localStorage.setItem('token', token);

            if (decoded.token_type === 'login') {
                // If login is successful, redirect to the last page or home
                const redirectTo = localStorage.getItem('redirect') || '/';
                localStorage.removeItem('redirect');
                navigate(redirectTo);
            } else if (decoded.token_type === 'totp') {
                // Redirect to the OTP flow
                navigate('/otp');
            }
        } catch (err: any) {
            const errorMessage = err.response?.data?.message || 'Incorrect username or password. Please try again.';
            setError(errorMessage);

            // Clear error and reset form inputs after 1.5 seconds
            setTimeout(() => {
                setError(null); // Clear error
                setUsername(''); // Reset username input
                setPassword(''); // Reset password input
            }, 1500);
        }
    };

    return (
        <Modal show={true} centered>
            <Modal.Header>
                <Modal.Title>Login</Modal.Title>
            </Modal.Header>
            <Modal.Body>
                <Form onSubmit={handleSubmit}>
                    <Form.Group className="mb-3">
                        <Form.Label>Username</Form.Label>
                        <Form.Control
                            type="text"
                            placeholder="Enter username"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                        />
                    </Form.Group>
                    <Form.Group className="mb-3">
                        <Form.Label>Password</Form.Label>
                        <Form.Control
                            type="password"
                            placeholder="Enter password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                        />
                    </Form.Group>
                    {error && <div className="text-danger mb-3">{error}</div>}
                    <Button variant={UI_BASE_COLOR} type="submit" className="w-100">
                        Submit
                    </Button>
                </Form>
            </Modal.Body>
        </Modal>
    );
};

export default Login;