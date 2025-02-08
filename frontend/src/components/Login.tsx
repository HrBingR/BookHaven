import React, { useState, useEffect } from 'react';
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
    const { UI_BASE_COLOR, CF_ACCESS_AUTH, OIDC_ENABLED } = useConfig();

    useEffect(() => {
        const params = new URLSearchParams(window.location.search);

        // If there's a token param, handle it
        const tokenFromUrl = params.get('token');
        if (tokenFromUrl) {
            onLogin(tokenFromUrl);
            // Possibly navigate away if you want to hide the Login modal
            navigate('/');
        }

        // If there's an error param, display it
        const errorFromUrl = params.get('error');
        if (errorFromUrl) {
            setError(errorFromUrl);
        }
    }, [onLogin, navigate, setError]);


    const autoLogin = async () => {
        try {
            setError(null);
            // For example, call an endpoint that returns a Cloudflare-style token
            // or do any logic required to skip manual login
            const response = await apiClient.post('/login', {});
            const token = response.data.token;
            onLogin(token);
            // Then navigate just like normal
            navigate('/');
        } catch (err: any) {
            setError('Auto-login failed');
        }
    };

    useEffect(() => {
        if (CF_ACCESS_AUTH) {
            autoLogin();
        }
    }, [CF_ACCESS_AUTH]);

    const handleOidc = async () => {
        try {
            setError(null);
            window.location.replace('/login/oidc')
        } catch (err: any) {
            setError('OIDC-login failed');
        }
    };

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        try {
            setError(null); // Reset errors
            const response = await apiClient.post('/login', { username, password });

            const token = response.data.token;
            onLogin(token);
            const decoded: DecodedToken = jwtDecode(token);

            localStorage.setItem('token', token);

            if (decoded.token_type === 'login') {
                const redirectTo = localStorage.getItem('redirect') || '/';
                localStorage.removeItem('redirect');
                navigate(redirectTo);
            } else if (decoded.token_type === 'totp') {
                navigate('/otp');
            }
        } catch (err: any) {
            const errorMessage = err.message || 'Unhandled error occurred. Please try again.';
            setError(errorMessage);

            setTimeout(() => {
                setError(null);
                setUsername('');
                setPassword('');
            }, 3000);
        }
    };

    return (
        <>
            { !CF_ACCESS_AUTH && (
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
                            {OIDC_ENABLED && (
                                <Button variant={UI_BASE_COLOR} className="w-100" onClick={handleOidc} style={{ marginTop: 10 }}>
                                    OIDC Login
                                </Button>
                            )}
                        </Form>
                    </Modal.Body>
                </Modal>
            )}
        </>
    );
};

export default Login;