import React, { useState } from 'react';
import { Button, Form, Alert, Modal } from 'react-bootstrap';
import apiClient from '../utilities/apiClient';
import { useConfig } from '../context/ConfigProvider';
import { CSSTransition, SwitchTransition } from 'react-transition-group';

type UploadModalProps = {
    onClose: () => void;
    show: boolean;
    refreshBooks?: () => void;
};

type UploadedBookMetadata = {
    identifier: string;
    title: string;
    authors: string[];
    series: string;
    seriesindex: number;
    relative_path: string;
    coverImageData: string | null;
    coverMediaType: string | null;
    hasCover: boolean;
};

const UploadModal: React.FC<UploadModalProps> = ({ onClose, show, refreshBooks }) => {
    const [view, setView] = useState<'upload' | 'edit'>('upload');
    const [file, setFile] = useState<File | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [saved, setSaved] = useState(false);
    const [bookMetadata, setBookMetadata] = useState<UploadedBookMetadata | null>(null);

    // Form fields for editing
    const [newTitle, setNewTitle] = useState('');
    const [newAuthors, setNewAuthors] = useState('');
    const [newSeries, setNewSeries] = useState('');
    const [newSeriesIndex, setNewSeriesIndex] = useState(0);
    const [newCover, setNewCover] = useState<File | null>(null);

    const { UI_BASE_COLOR } = useConfig();

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const selectedFile = e.target.files?.[0];
        if (selectedFile) {
            // Frontend validation for .epub files
            if (!selectedFile.name.toLowerCase().endsWith('.epub')) {
                setError('Only .epub files are allowed');
                setFile(null);
                return;
            }
            setError(null);
            setFile(selectedFile);
        }
    };

    const handleUpload = async () => {
        if (!file) {
            setError('Please select a file');
            return;
        }

        setLoading(true);
        setError(null);

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await apiClient.post('/api/books/upload', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });

            if (response.status === 200) {
                const metadata = response.data.book_metadata[0];
                setBookMetadata(metadata);

                // Pre-populate form fields
                setNewTitle(metadata.title);
                setNewAuthors(metadata.authors.join(', '));
                setNewSeries(metadata.series || '');
                setNewSeriesIndex(metadata.seriesindex || 0);

                setView('edit');
                setSuccessMessage('File uploaded successfully! Please review and edit the metadata below.');
            }
        } catch (err: any) {
            if (err.response?.data?.error) {
                setError(err.response.data.error);
            } else {
                setError('Failed to upload file. Please try again.');
                console.log(err)
            }
        } finally {
            setLoading(false);
        }
    };

    const handleSaveMetadata = async () => {
        if (!bookMetadata) {
            setError('No book metadata available');
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const formData = new FormData();
            formData.append('identifier', bookMetadata.identifier);
            formData.append('title', newTitle);
            formData.append('authors', newAuthors);
            formData.append('series', newSeries);
            formData.append('seriesindex', newSeriesIndex.toString());
            formData.append('relative_path', bookMetadata.relative_path);

            if (newCover) {
                formData.append('coverImage', newCover);
            }

            const response = await apiClient.post('/api/books/add', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });

        if (response.status === 200) {
            setSaved(true);
            setSuccessMessage('Book metadata saved successfully!');

            // Refresh the books list if callback provided
            if (refreshBooks) {
                refreshBooks();
            }

            // Close modal after a brief delay to show success message
            setTimeout(() => {
                handleClose();
            }, 1500);
        }


        } catch (err: any) {
            if (err.response?.data?.error) {
                setError(err.response.data.error);
            } else {
                setError('Failed to save metadata. Please try again.');
            }
        } finally {
            setLoading(false);
        }
    };

    const handleClose = () => {
        // Reset all state
        setView('upload');
        setFile(null);
        setError(null);
        setSuccessMessage(null);
        setLoading(false);
        setSaved(false);
        onClose();
    };

    const handleEditClose = async () => {
        // Reset all state
        setView('upload');
        setFile(null);
        setError(null);
        setSuccessMessage(null);
        setLoading(false);
        if (bookMetadata) {
            try {
                await apiClient.delete(`/api/books/upload/cancel/${encodeURIComponent(bookMetadata.relative_path)}`);
            } catch (err: unknown) {
                console.error('Failed to cancel upload:', err);
            }
        }
        setBookMetadata(null);
        setNewTitle('');
        setNewAuthors('');
        setNewSeries('');
        setNewSeriesIndex(0);
        setNewCover(null);
        onClose();
    };

    const renderUploadView = () => (
        <div className="p-3">
            <h5>Upload ePub File</h5>
            <Form>
                <Form.Group className="mb-3">
                    <Form.Label>Select ePub File</Form.Label>
                    <Form.Control
                        type="file"
                        accept=".epub"
                        onChange={handleFileChange}
                    />
                    {file && (
                        <Form.Text className="text-muted">
                            Selected: {file.name}
                        </Form.Text>
                    )}
                </Form.Group>
                <div className="d-flex gap-2">
                    <Button
                        variant={UI_BASE_COLOR}
                        onClick={handleUpload}
                        disabled={!file || loading}
                        className="flex-grow-1"
                    >
                        {loading ? (
                            <>
                                <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                                Uploading...
                            </>
                        ) : (
                            'Next'
                        )}
                    </Button>
                    <Button variant="secondary" onClick={handleClose}>
                        Cancel
                    </Button>
                </div>
            </Form>
        </div>
    );

    const renderEditView = () => (
        <div className="p-3">
            <h5>Edit Book Metadata</h5>
            <div className="row">
                <div className="col-md-8">
                    <Form>
                        <Form.Group controlId="formTitle" className="mb-3">
                            <Form.Label>Title</Form.Label>
                            <Form.Control
                                type="text"
                                value={newTitle}
                                onChange={(e) => setNewTitle(e.target.value)}
                            />
                        </Form.Group>
                        <Form.Group controlId="formAuthors" className="mb-3">
                            <Form.Label>Authors</Form.Label>
                            <Form.Control
                                type="text"
                                value={newAuthors}
                                onChange={(e) => setNewAuthors(e.target.value)}
                                placeholder="Comma-separated authors"
                            />
                        </Form.Group>
                        <Form.Group controlId="formSeries" className="mb-3">
                            <Form.Label>Series</Form.Label>
                            <Form.Control
                                type="text"
                                value={newSeries}
                                onChange={(e) => setNewSeries(e.target.value)}
                            />
                        </Form.Group>
                        <Form.Group controlId="formSeriesIndex" className="mb-3">
                            <Form.Label>Series Index</Form.Label>
                            <Form.Control
                                type="number"
                                value={newSeriesIndex}
                                onChange={(e) => setNewSeriesIndex(parseFloat(e.target.value) || 0)}
                            />
                        </Form.Group>
                    {/* Only show cover upload option if the book has an existing cover */}
                    {bookMetadata?.hasCover && (
                        <Form.Group controlId="formCoverImage" className="mb-3">
                            <Form.Label>Replace Cover Image (Optional)</Form.Label>
                            <Form.Control
                                type="file"
                                accept="image/*"
                                onChange={(e) => {
                                    const target = e.target as HTMLInputElement;
                                    setNewCover(target.files ? target.files[0] : null);
                                }}
                            />
                            <Form.Text className="text-muted">
                                Only replacement of existing covers is supported
                            </Form.Text>
                        </Form.Group>
                    )}
                    </Form>
                </div>
                <div className="col-md-4">
                {bookMetadata?.hasCover && bookMetadata.coverImageData && (
                    <div className="text-center">
                        <img
                            src={`data:${bookMetadata.coverMediaType};base64,${bookMetadata.coverImageData}`}
                            alt="Book Cover"
                            className="img-fluid"
                            style={{ maxHeight: '300px', objectFit: 'contain' }}
                        />
                        <p className="text-muted mt-2">Current Cover</p>
                    </div>
                )}
                {!bookMetadata?.hasCover && (
                    <div className="text-center">
                        <div
                            className="d-flex align-items-center justify-content-center bg-light"
                            style={{ height: '300px', border: '2px dashed #ccc' }}
                        >
                            <p className="text-muted">No cover image available</p>
                        </div>
                    </div>
                )}
            </div>
            </div>
            <div className="d-flex gap-2 mt-3">
                <Button
                    variant={UI_BASE_COLOR}
                    onClick={handleSaveMetadata}
                    disabled={loading || saved}
                    className="flex-grow-1"
                >
                    {loading ? (
                        <>
                            <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                            Saving...
                        </>
                    ) : (
                        'Save'
                    )}
                </Button>
                <Button variant="secondary" onClick={handleEditClose}>
                    Cancel
                </Button>
            </div>
        </div>
    );

    const getModalSize = () => {
        return view === 'upload' ? undefined : 'lg'; // Small for upload, large for edit
    };

    return (
        <Modal show={show} onHide={view === 'upload' ? handleClose : handleEditClose} centered size={getModalSize()}>
            <Modal.Header closeButton>
                <Modal.Title>
                    {view === 'upload' ? 'Upload Book' : 'Edit Book Metadata'}
                </Modal.Title>
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
                            {view === 'upload' ? renderUploadView() : renderEditView()}
                        </div>
                    </CSSTransition>
                </SwitchTransition>
            </Modal.Body>
        </Modal>
    );
};

export default UploadModal;