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
    const [view, setView] = useState<'main' | 'change-password' | 'mfa-setup' | 'link-oidc' | 'unlink-oidc'>('main');
    const [oldPassword, setOldPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);
    const [otp, setOtp] = useState('');
    const [provisioningUrl, setProvisioningUrl] = useState('');
    const [mfaSecret, setMfaSecret] = useState('');
    const [isMfaEnabled, setIsMfaEnabled] = useState(false);
    const [isOidcEnabled, setIsOidcEnabled] = useState(false);
    const { UI_BASE_COLOR, OIDC_ENABLED } = useConfig();

    const mfaStatus = async () => {
        try {
            const response = await apiClient.get('/api/user/get-mfa-status');
            const { message } = response.data;
            setIsMfaEnabled(message === "true");
        } catch (err: any) {
            console.error('Error fetching MFA status:', err);
        }
    };
    const oidcStatus = async() => {
        try {
            const response = await apiClient.get('/api/user/get-oidc-status');
            const { message } = response.data;
            setIsOidcEnabled(message === "true");
        } catch (err: any) {
            console.error('Error fetching OIDC status:', err);
        }
    };

    useEffect(() => {
            mfaStatus();
            oidcStatus();
        },
        []);

    // Go back to the main menu
    const handleCancel = () => {
        setView('main');
        setError(null);
    };

    // Handle change password submission
    const handlePasswordChange = async () => {
        setError(null);
        try {
            await apiClient.patch('/api/user/change-password', {
                old_password: oldPassword,
                new_password: newPassword,
            });
            alert('Your password has been changed successfully!');
            onClose();
            setView("main");
        } catch (err: any) {
            setError(err.message);
        }
    };

    // Handle enabling MFA
    const handleEnableMFA = async () => {
        setError(null);
        try {
            const response = await apiClient.post('/api/user/enable-mfa', {});
            const { totp_provisioning_url, mfa_secret } = response.data;
            setProvisioningUrl(totp_provisioning_url);
            setMfaSecret(mfa_secret);
            setView('mfa-setup');
        } catch (err: any) {
            setError(err.message);
        }
    };

    const handleDisableMFA = async () => {
        setError(null);
        try {
            const response = await apiClient.delete('/api/user/disable-mfa', {});
            const { message } = response.data;
            alert(message || "MFA Successfully Disabled")
            onClose()
            setView("main");
        } catch (err: any) {
            setError(err.message || "Failed to disable MFA. Please try again.");
        }
    };

    const handleUnlinkOidc = async () => {
        try {
            await apiClient.patch(`/api/user/unlink-oidc`, {
                new_password: newPassword
            });
            setSuccessMessage("Unlinked from OIDC successfully.")
            onClose();
            setView("main");
        } catch (err: any) {
            setError(err.message || "Failed to unlink from OIDC.")
        }
    };

    const handleLinkOidc = async () => {
        try {
            setError(null);
            window.location.replace('/login/link-oidc')
        } catch (err: any) {
            setError('OIDC-login failed');
        }
    };

    // Handle OTP submission
    const handleValidateOtp = async () => {
        setError(null);
        try {
            await apiClient.post('/validate-otp', { otp });
            alert('MFA setup completed successfully!');
            onClose();
            setView("main");
        } catch (err: any) {
            setError(err.message);
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
                        {OIDC_ENABLED && (
                            <>
                                {isOidcEnabled && (
                                    <Button
                                        variant={UI_BASE_COLOR}
                                        className="mb-3 w-100"
                                        onClick={() => setView('unlink-oidc')}
                                    >
                                        Unlink OIDC
                                    </Button>
                                )}
                                {!isOidcEnabled && (
                                    <Button
                                        variant={`outline-${UI_BASE_COLOR}`}
                                        className="mb-3 w-100"
                                        onClick={handleLinkOidc}
                                    >
                                        Link OIDC
                                    </Button>
                                )}
                            </>
                        )}
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
                            <Button variant={UI_BASE_COLOR} onClick={handlePasswordChange} className="w-100">
                                Submit
                            </Button>
                            <Button variant="secondary" onClick={handleCancel} className="w-100 mt-2">
                                Cancel
                            </Button>
                        </Form>
                    </div>
                );
            case "unlink-oidc":
                return (
                    <div className="p-3">
                        <h4>Unlink account from OIDC</h4>
                        <p
                            style={{ color: "red" }}
                        >
                            Warning: Local password and MFA will be reset when unlinking OIDC.
                        </p>
                        <Form>
                            <Form.Group className="mb-3">
                                <Form.Label>New Local Password</Form.Label>
                                <Form.Control
                                    type="password"
                                    placeholder="Enter new local password"
                                    value={newPassword}
                                    onChange={(e) => setNewPassword(e.target.value)}
                                />
                            </Form.Group>
                            <Button variant={UI_BASE_COLOR} onClick={handleUnlinkOidc} className="w-100">
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
            <Modal.Header closeButton>
                <Modal.Title>Account Settings</Modal.Title>
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

export default AccountModal;