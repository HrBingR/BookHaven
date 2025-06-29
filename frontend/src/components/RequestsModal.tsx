import React, { useEffect, useState } from 'react';
import { Modal, Button, Table, Alert, Form } from 'react-bootstrap';
import { CSSTransition, SwitchTransition } from 'react-transition-group';
import apiClient from '../utilities/apiClient';
import { UserRole } from '../utilities/roleUtils';
import { useConfig } from '../context/ConfigProvider';

type RequestsModalProps = {
    onClose: () => void;
    show: boolean;
    userRole: UserRole;
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

// Type for request data from the API
interface BookRequest {
    id: number;
    user_id: number;
    username: string;
    date: string;
    title: string;
    authors: string;
    series: string;
    seriesindex: number;
    link: string;
}

interface RequestsResponse {
    requests: BookRequest[];
    total_requests: number;
    fetched_offset: number;
    next_offset: number;
    remaining_requests: number;
}

const RequestsModal: React.FC<RequestsModalProps> = ({ onClose, show, userRole }) => {
    const [view, setView] = useState<'main' | 'new-request'>('main');
    const [requests, setRequests] = useState<BookRequest[]>([]);
    const [currentPage, setCurrentPage] = useState(0);
    const [totalRequests, setTotalRequests] = useState(0);
    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    // Form state for new request
    const [newTitle, setNewTitle] = useState('');
    const [newAuthors, setNewAuthors] = useState('');
    const [newSeries, setNewSeries] = useState('');
    const [newSeriesIndex, setNewSeriesIndex] = useState<number>(0);
    const [newLink, setNewLink] = useState('');

    const requestsPerPage = 20;
    const totalPages = Math.ceil(totalRequests / requestsPerPage);
    const isAdminOrEditor = userRole === 'admin' || userRole === 'editor';
    const { UI_BASE_COLOR } = useConfig();

    useEffect(() => {
        if (show) {
            void fetchRequests();
        }
    }, [show, currentPage]);

    // Helper function to extract error message from API responses
    const getErrorMessage = (err: unknown, fallbackMessage: string): string => {
        const apiError = err as ApiError;
        return apiError.response?.data?.error || apiError.message || fallbackMessage;
    };

    const fetchRequests = async () => {
        setLoading(true);
        setError(null);
        try {
            const offset = currentPage * requestsPerPage;
            const response = await apiClient.get<RequestsResponse>('/api/books/requests', {
                params: {
                    offset,
                    limit: requestsPerPage,
                    sort_by: 'date',
                    sort_order: 'desc'
                }
            });
            setRequests(response.data.requests);
            setTotalRequests(response.data.total_requests);
        } catch (err: unknown) {
            setError(getErrorMessage(err, 'Failed to fetch requests.'));
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteRequest = async (requestId: number) => {
        try {
            await apiClient.delete(`/api/books/requests/${requestId}`);
            setSuccessMessage('Request processed successfully.');
            void fetchRequests(); // Refresh the list
        } catch (err: unknown) {
            setError(getErrorMessage(err, 'Failed to process request.'));
        }
    };

    const handleSubmitNewRequest = async () => {
        // Validate required fields
        if (!newTitle.trim() || !newAuthors.trim()) {
            setError('Title and Authors are required fields.');
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const requestData = {
                title: newTitle.trim(),
                authors: newAuthors.trim(),
                series: newSeries.trim() || undefined,
                seriesindex: newSeriesIndex || undefined,
                link: newLink.trim() || undefined
            };

            await apiClient.post('/api/books/requests', requestData);
            setSuccessMessage('Book request submitted successfully!');

            // Reset form
            setNewTitle('');
            setNewAuthors('');
            setNewSeries('');
            setNewSeriesIndex(0);
            setNewLink('');

            // Return to main view after 1500ms
            setTimeout(() => {
                setView('main');
                setSuccessMessage(null);
                void fetchRequests(); // Refresh the list
            }, 1500);

        } catch (err: unknown) {
            setError(getErrorMessage(err, 'Failed to submit book request.'));
        } finally {
            setLoading(false);
        }
    };

    const handleClose = () => {
        setView('main');
        setError(null);
        setSuccessMessage(null);
        setCurrentPage(0);
        // Reset form state
        setNewTitle('');
        setNewAuthors('');
        setNewSeries('');
        setNewSeriesIndex(0);
        setNewLink('');
        onClose();
    };

    const handleCancel = () => {
        setView('main');
        setError(null);
        setSuccessMessage(null);
        // Reset form state
        setNewTitle('');
        setNewAuthors('');
        setNewSeries('');
        setNewSeriesIndex(0);
        setNewLink('');
    };

    const handleNextPage = () => {
        if (currentPage < totalPages - 1) {
            setCurrentPage(currentPage + 1);
        }
    };

    const handlePreviousPage = () => {
        if (currentPage > 0) {
            setCurrentPage(currentPage - 1);
        }
    };

    const truncateLink = (link: string, maxLength: number = 50): string => {
        if (link.length <= maxLength) return link;
        return link.substring(0, maxLength) + '...';
    };

    const copyToClipboard = async (text: string) => {
        try {
            await navigator.clipboard.writeText(text);
            setSuccessMessage('Link copied to clipboard!');
            setTimeout(() => setSuccessMessage(null), 2000);
        } catch (err) {
            console.error('Failed to copy link to clipboard:', err);
            setError('Failed to copy link to clipboard.');
        }
    };

    const formatDate = (dateString: string): string => {
        try {
            return new Date(dateString).toLocaleDateString();
        } catch {
            return dateString;
        }
    };

    const renderMainView = () => (
        <>
            {loading ? (
                <div className="text-center">
                    <p>Loading requests...</p>
                </div>
            ) : (
                <>
                    <Table striped bordered hover>
                        <thead>
                            <tr>
                                <th>Request Date</th>
                                <th>Title</th>
                                <th>Authors</th>
                                <th>Series</th>
                                <th>Series #</th>
                                <th>Link</th>
                                {isAdminOrEditor && <th>Username</th>}
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {requests.map((request: BookRequest) => (
                                <tr key={request.id}>
                                    <td>{formatDate(request.date)}</td>
                                    <td>{request.title}</td>
                                    <td>{request.authors}</td>
                                    <td>{request.series || '-'}</td>
                                    <td>{request.seriesindex || '-'}</td>
                                    <td>
                                        {request.link ? (
                                            <span
                                                title={request.link}
                                                onClick={() => copyToClipboard(request.link)}
                                                style={{
                                                    cursor: 'pointer',
                                                    textDecoration: 'underline',
                                                    color: '#007bff'
                                                }}
                                            >
                                                {truncateLink(request.link)}
                                            </span>
                                        ) : (
                                            '-'
                                        )}
                                    </td>
                                    {isAdminOrEditor && <td>{request.username}</td>}
                                    <td>
                                        <Button
                                            variant={isAdminOrEditor ? "success" : "danger"}
                                            size="sm"
                                            onClick={() => handleDeleteRequest(request.id)}
                                        >
                                            {isAdminOrEditor ? "Resolve" : "Delete"}
                                        </Button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </Table>

                    {requests.length === 0 && !loading && (
                        <div className="text-center">
                            <p>No requests found.</p>
                        </div>
                    )}

                    {totalPages > 1 && (
                        <div className="d-flex justify-content-between align-items-center mt-3">
                            <Button
                                variant="secondary"
                                onClick={handlePreviousPage}
                                disabled={currentPage === 0}
                            >
                                Previous
                            </Button>
                            <span>
                                Page {currentPage + 1} of {totalPages} ({totalRequests} total requests)
                            </span>
                            <Button
                                variant="secondary"
                                onClick={handleNextPage}
                                disabled={currentPage >= totalPages - 1}
                            >
                                Next
                            </Button>
                        </div>
                    )}

                    <div className="mt-3">
                        <Button
                            variant={UI_BASE_COLOR}
                            onClick={() => setView('new-request')}
                        >
                            New Book Request
                        </Button>
                    </div>
                </>
            )}
        </>
    );

    const renderNewRequestView = () => (
        <div className="p-3">
            <h5>New Book Request</h5>
            <Form>
                <Form.Group controlId="formTitle" className="mb-3">
                    <Form.Label>Title *</Form.Label>
                    <Form.Control
                        type="text"
                        value={newTitle}
                        onChange={(e) => setNewTitle(e.target.value)}
                        placeholder="Enter book title"
                        required
                    />
                </Form.Group>

                <Form.Group controlId="formAuthors" className="mb-3">
                    <Form.Label>Author(s) *</Form.Label>
                    <Form.Control
                        type="text"
                        value={newAuthors}
                        onChange={(e) => setNewAuthors(e.target.value)}
                        placeholder="Enter author(s)"
                        required
                    />
                </Form.Group>

                <Form.Group controlId="formSeries" className="mb-3">
                    <Form.Label>Series</Form.Label>
                    <Form.Control
                        type="text"
                        value={newSeries}
                        onChange={(e) => setNewSeries(e.target.value)}
                        placeholder="Enter series name (optional)"
                    />
                </Form.Group>

                <Form.Group controlId="formSeriesIndex" className="mb-3">
                    <Form.Label>Series Index</Form.Label>
                    <Form.Control
                        type="number"
                        step="0.1"
                        value={newSeriesIndex}
                        onChange={(e) => setNewSeriesIndex(parseFloat(e.target.value) || 0)}
                        placeholder="Enter series index (optional)"
                    />
                </Form.Group>

                <Form.Group controlId="formLink" className="mb-3">
                    <Form.Label>Book Link</Form.Label>
                    <Form.Control
                        type="url"
                        value={newLink}
                        onChange={(e) => setNewLink(e.target.value)}
                        placeholder="Enter book link (optional)"
                    />
                </Form.Group>
            </Form>

            <div className="d-flex gap-2 mt-3">
                <Button
                    variant={UI_BASE_COLOR}
                    onClick={handleSubmitNewRequest}
                    disabled={loading}
                    className="flex-grow-1"
                >
                    {loading ? (
                        <>
                            <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                            Submitting...
                        </>
                    ) : (
                        'Submit Request'
                    )}
                </Button>
                <Button variant="secondary" onClick={handleCancel}>
                    Cancel
                </Button>
            </div>
        </div>
    );

    return (
        <Modal show={show} onHide={handleClose} centered dialogClassName="modal-90w">
            <Modal.Header closeButton>
                <Modal.Title>Book Requests</Modal.Title>
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
                        <div>
                            {view === 'main' ? renderMainView() : renderNewRequestView()}
                        </div>
                    </CSSTransition>
                </SwitchTransition>
            </Modal.Body>
        </Modal>
    );
};

export default RequestsModal;
