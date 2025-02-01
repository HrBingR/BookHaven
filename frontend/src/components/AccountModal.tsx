import React, {useEffect, useState} from 'react';
import { Button, Form, Alert, Modal } from 'react-bootstrap';
import apiClient from '../utilities/apiClient';
import {QRCodeSVG} from 'qrcode.react';
import { useConfig } from '../context/ConfigProvider';
import { CSSTransition, SwitchTransition } from 'react-transition-group';

type AccountModalProps = {
    onClose: () => void;
    show: boolean;
};

const AccountModal: React.FC<AccountModalProps> = ({ onClose, show }) => {
    const [view, setView] = useState<'main' | 'change-password' | 'mfa-setup'>('main');
    const [oldPassword, setOldPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [passwordError, setPasswordError] = useState<string | null>(null);
    const [mfaError, setMfaError] = useState<string | null>(null);
    const [otp, setOtp] = useState('');
    const [provisioningUrl, setProvisioningUrl] = useState('');
    const [mfaSecret, setMfaSecret] = useState('');
    const [isMfaEnabled, setIsMfaEnabled] = useState(false);
    const { UI_BASE_COLOR } = useConfig();

    const mfaStatus = async () => {
        try {
            const response = await apiClient.get('/api/user/get-mfa-status');
            const { message } = response.data;
            setIsMfaEnabled(message === "true"); // Convert to boolean here
        } catch (err: any) {
            console.error('Error fetching MFA status:', err);
        }
    };

    useEffect(() => {
            mfaStatus();
        },
        []);

    // Go back to the main menu
    const handleCancel = () => {
        setView('main');
        setPasswordError(null);
        setMfaError(null);
    };

    // Handle change password submission
    const handlePasswordChange = async () => {
        setPasswordError(null); // Reset errors
        try {
            await apiClient.patch('/api/user/change-password', {
                old_password: oldPassword,
                new_password: newPassword,
            });
            alert('Your password has been changed successfully!');
            onClose(); // Close the modal
            setView("main");
        } catch (err: any) {
            setPasswordError(err.message); // Set inline error
        }
    };

    // Handle enabling MFA
    const handleEnableMFA = async () => {
        setMfaError(null); // Reset errors
        try {
            const response = await apiClient.post('/api/user/enable-mfa', {});
            const { totp_provisioning_url, mfa_secret } = response.data;
            setProvisioningUrl(totp_provisioning_url);
            setMfaSecret(mfa_secret);
            setView('mfa-setup'); // Move to MFA setup flow
        } catch (err: any) {
            setMfaError(err.message); // Set inline error
        }
    };

    const handleDisableMFA = async () => {
        setMfaError(null);
        try {
            const response = await apiClient.delete('/api/user/disable-mfa', {});
            const { message } = response.data;
            alert(message || "MFA Successfully Disabled")
            onClose()
            setView("main");
        } catch (err: any) {
            setMfaError(err.message || "Failed to disable MFA. Please try again.");
        }
    };

    // Handle OTP submission
    const handleValidateOtp = async () => {
        setMfaError(null); // Reset errors
        try {
            await apiClient.post('/validate-otp', { otp });
            alert('MFA setup completed successfully!');
            onClose(); // Close the modal
            setView("main");
        } catch (err: any) {
            setMfaError(err.message); // Set inline error
        }
    }

    const handleClose = () => {
        setView("main");
        onClose();
    }

    function renderView() {
        switch (view) {
            case "main":
                return (
                    <div className="p-3">
                        <h4>Account Settings</h4>
                        <Button
                            variant={UI_BASE_COLOR}
                            className="mb-3 w-100"
                            onClick={() => setView('change-password')}
                        >
                            Change Password
                        </Button>
                        {!isMfaEnabled && (
                            <Button
                                variant={`outline-${UI_BASE_COLOR}`}
                                className="mb-3 w-100"
                                onClick={handleEnableMFA}
                            >
                                Enable MFA
                            </Button>
                        )}
                        {isMfaEnabled && (
                            <Button
                                variant={UI_BASE_COLOR}
                                className="mb-3 w-100"
                                onClick={handleDisableMFA}
                            >
                                Disable MFA
                            </Button>
                        )}
                        {mfaError && <Alert variant="danger">{mfaError}</Alert>}
                        <Button variant="secondary" className="w-100" onClick={onClose}>
                            Close
                        </Button>
                    </div>
                );
            case "change-password":
                return (
                    <div className="p-3">
                        <h4>Change Password</h4>
                        <Form>
                            <Form.Group className="mb-3">
                                <Form.Label>Current Password</Form.Label>
                                <Form.Control
                                    type="password"
                                    placeholder="Enter Current Password"
                                    value={oldPassword}
                                    onChange={(e) => setOldPassword(e.target.value)}
                                />
                            </Form.Group>
                            <Form.Group className="mb-3">
                                <Form.Label>New Password</Form.Label>
                                <Form.Control
                                    type="password"
                                    placeholder="Enter New Password"
                                    value={newPassword}
                                    onChange={(e) => setNewPassword(e.target.value)}
                                />
                            </Form.Group>
                            {passwordError && <Alert variant="danger">{passwordError}</Alert>}
                            <Button variant={UI_BASE_COLOR} onClick={handlePasswordChange} className="w-100">
                                Submit
                            </Button>
                            <Button variant="secondary" onClick={handleCancel} className="w-100 mt-2">
                                Cancel
                            </Button>
                        </Form>
                    </div>
                );
            case "mfa-setup":
                return (
                    <div className="p-3">
                        <h4>Enable MFA</h4>
                        <p>Scan the QR code below with your TOTP app:</p>
                        <div className="d-flex justify-content-center mb-3">
                            <QRCodeSVG value={provisioningUrl} size={200} />
                        </div>
                        <p className="text-center">
                            <strong>Manual Entry Code:</strong> {mfaSecret}
                        </p>
                        <Form>
                            <Form.Group className="mb-3">
                                <Form.Label>Enter Current OTP</Form.Label>
                                <Form.Control
                                    type="text"
                                    placeholder="Enter OTP"
                                    value={otp}
                                    onChange={(e) => setOtp(e.target.value)}
                                />
                            </Form.Group>
                            {mfaError && <Alert variant="danger">{mfaError}</Alert>}
                            <Button variant={UI_BASE_COLOR} onClick={handleValidateOtp} className="w-100">
                                Submit
                            </Button>
                            <Button variant="secondary" onClick={handleCancel} className="w-100 mt-2">
                                Cancel
                            </Button>
                        </Form>
                    </div>
                )
        }
    }

    return (
        <Modal show={show} onHide={handleClose} centered>
            <Modal.Body>
                <SwitchTransition mode="out-in">
                    <CSSTransition
                        key={view}          // Re-renders child when 'view' changes
                        timeout={100}       // Adjust as desired
                        classNames="fade"   // Matches our fade CSS class
                        unmountOnExit
                    >
                        {/* This is the single “child” to animate in/out */}
                        <div>{renderView()}</div>
                    </CSSTransition>
                </SwitchTransition>
            </Modal.Body>
        </Modal>
    );

};

export default AccountModal;