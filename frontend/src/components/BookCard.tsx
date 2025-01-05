// src/components/BookCard.tsx
import React, {useState} from 'react';
import { Card, Button, Modal, Form, Alert } from 'react-bootstrap';
import axios from 'axios';
import './All.css'; // Import the CSS file
import { Book } from '../types';

interface BookCardProps {
  book: Book;
  refreshBooks: () => void;
}

let debounceTimer: number;
const debounce = (cb: Function, delay: number = 300) => {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => cb(), delay);
};

const BookCard: React.FC<BookCardProps> = ({ book, refreshBooks }) => {
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(false); // To control the spinner state
  const [error, setError] = useState<string | null>(null); // Capture save errors
  const [newTitle, setNewTitle] = useState(book.title);
  const [newAuthors, setNewAuthors] = useState(book.authors.join(', '));
  const [newSeries, setNewSeries] = useState(book.series || '');
  const [newSeriesIndex, setNewSeriesIndex] = useState(book.seriesindex || 0);
  const [newCover, setNewCover] = useState<File | null>(null);

  const handleSave = () => {
  // Clear any previous error
  setError(null);

  // Prepare save logic
  const saveRequest = async () => {
    const formData = new FormData();
    formData.append('identifier', book.identifier);
    formData.append('title', newTitle);
    formData.append('authors', newAuthors);
    formData.append('series', newSeries);
    formData.append('seriesindex', newSeriesIndex.toString());
    if (newCover) {
      formData.append('coverImage', newCover);
    }

    setLoading(true); // Show spinner

    // Retry and error handling logic remains the same
    try {
      await axios.post('/api/books/edit', formData);
      setShowModal(false);
      setLoading(false);
      refreshBooks(); // Refresh the book list
    } catch (err) {
      console.error('Error updating book metadata:', err);
      setError('Failed to save. Retrying...');
      setTimeout(saveRequest, 2000); // Retry after 2 seconds
    }
  };

  // Wrap the save logic in debounce
  debounce(saveRequest, 500); // Debounce for 500ms (you can adjust this delay as needed)
};

  return (
    <Card className="card-container">
      <a href={`/read/${book.identifier}`}>
        <Card.Img
            variant="top"
            src={book.coverUrl}
            alt={book.title}
            className="book-cover"
        />
      </a>
      <Card.Body>
        <Card.Title>{book.title}</Card.Title>
        <Card.Text>By {book.authors.join(', ')}</Card.Text>
        {book.series && book.seriesindex !== 0.0 && (
          <Card.Text>
            Book {book.seriesindex} of the {book.series} series
          </Card.Text>
        )}
      </Card.Body>
      <div className="card-footer">
        {/* Read Button */}
        <Button
            variant="primary"
            href={`/read/${book.identifier}`}
            className="me-2 read-button"
        >
          <i className="fas fa-book"></i>
        </Button>

        {/* Download Button */}
        <Button
            variant="primary"
            href={`/download/${book.identifier}`}
            className="me-2 download-button"
        >
          <i className="fas fa-download"></i>
        </Button>

        {/* Edit Button */}
        <Button
            variant="outline-secondary"
            className="me-2 edit-button"
            onClick={() => setShowModal(true)}
        >
          <i className="fas fa-pencil-alt"></i>
        </Button>
      </div>

      {/* Edit Metadata Modal */}
      <Modal show={showModal} onHide={() => setShowModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Edit Metadata</Modal.Title>
        </Modal.Header>
        <Modal.Body>
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
                onChange={(e) => setNewSeriesIndex(parseFloat(e.target.value))}
              />
            </Form.Group>
            <Form.Group controlId="formCoverImage" className="mb-3">
              <Form.Label>Cover Image</Form.Label>
              <Form.Control
                type="file"
                accept="image/*"
                onChange={(e) => {
                    const target = e.target as HTMLInputElement;
                    setNewCover(target.files ? target.files[0] : null)
                }}
              />
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
            {error && (
              <Alert variant="danger" className="w-100 text-center">
                {error}
              </Alert>
            )}
          <Button variant="secondary" onClick={() => setShowModal(false)}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleSave} disabled={loading}>
              {loading ? (
                  <>
                      <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                      Saving...
                  </>
              ) : (
            'Save'
                  )}
          </Button>
        </Modal.Footer>
      </Modal>
    </Card>
  );
};

export default BookCard;