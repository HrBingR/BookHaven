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

const OTP: React.FC = () => {
    const [otp, setOtp] = useState<string>('');
    const [error, setError] = useState<string | null>(null);
    const navigate = useNavigate();
    const { UI_BASE_COLOR } = useConfig();

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        try {
            setError(null); // Reset errors
            const response = await apiClient.post('/login/check-otp', { otp });

            const token = response.data.token; // Assume token is returned as "token"
            const decoded: DecodedToken = jwtDecode(token);

            if (decoded.token_type === 'login') {
                // Save token and navigate to redirected page or home
                localStorage.setItem('token', token);
                const redirectTo = localStorage.getItem('redirect') || '/';
                localStorage.removeItem('redirect');
                navigate(redirectTo);
                window.location.reload();
            } else {
                throw new Error('Unexpected token type.');
            }
        } catch (err: any) {
            setError(err.response?.data?.message || 'Invalid OTP provided.');
        }
    };

    return (
        <Modal show={true} centered>
            <Modal.Header>
                <Modal.Title>Verify OTP</Modal.Title>
            </Modal.Header>
            <Modal.Body>
                <Form onSubmit={handleSubmit}>
                    <Form.Group className="mb-3">
                        <Form.Label>OTP</Form.Label>
                        <Form.Control
                            type="text"
                            placeholder="Enter OTP"
                            value={otp}
                            onChange={(e) => setOtp(e.target.value)}
                        />
                    </Form.Group>
                    {error && <div className="text-danger mb-3">{error}</div>}
                    <Button variant={UI_BASE_COLOR} type="submit" className="w-100">
                        Verify OTP
                    </Button>
                </Form>
            </Modal.Body>
        </Modal>
    );
};

export default OTP;