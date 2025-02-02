// src/components/BookCard.tsx
import React, {useState} from 'react';
import { Card, Button, ButtonGroup, DropdownButton, Modal, Form, Alert } from 'react-bootstrap';
import apiClient from '../utilities/apiClient';
import './All.css';
import { Book } from '../types';
import { useConfig } from '../context/ConfigProvider';

interface BookCardProps {
  book: Book;
  refreshBooks: () => void;
  isLoggedIn: boolean;
}

let debounceTimer: number;
const debounce = (cb: Function, delay: number = 300) => {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => cb(), delay);
};

const BookCard: React.FC<BookCardProps> = ({ book, refreshBooks, isLoggedIn }) => {
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [newTitle, setNewTitle] = useState(book.title);
  const [newAuthors, setNewAuthors] = useState(book.authors.join(', '));
  const [newSeries, setNewSeries] = useState(book.series || '');
  const [newSeriesIndex, setNewSeriesIndex] = useState(book.seriesindex || 0);
  const [newCover, setNewCover] = useState<File | null>(null);
  const [isFavorite, setIsFavorite] = useState(book.marked_favorite);
  const [isFinished, setIsFinished] = useState(book.is_finished);
  const { UI_BASE_COLOR } = useConfig();

  const handleSave = () => {
    setError(null);

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

      setLoading(true);

      try {
        await apiClient.post('/api/books/edit', formData);
        setShowModal(false);
        setLoading(false);
        refreshBooks();
      } catch (err) {
        console.error('Error updating book metadata:', err);
        setError('Failed to save. Retrying...');
        setTimeout(saveRequest, 2000);
      }
    };

    debounce(saveRequest, 500);
  };

  const handleToggleFavorite = async () => {
    if (!isLoggedIn) return;

    const newFavoriteState = !isFavorite;
    setIsFavorite(newFavoriteState);

    try {
      const response = await apiClient.put(`/api/books/${book.identifier}/progress_state`, {
        favorite: newFavoriteState,
      });

      if (response.status !== 200) {
        setIsFavorite(!newFavoriteState);
        console.error('Failed to toggle favorite state.');
      }
    } catch (error) {
      console.error('Error toggling favorite:', error);
      setIsFavorite(!newFavoriteState);
    }
  };

  const handleToggleFinished = async () => {
    if (!isLoggedIn) return;

    const newFinishedState = !isFinished;
    setIsFinished(newFinishedState);

    try {
      const response = await apiClient.put(`/api/books/${book.identifier}/progress_state`, {
        is_finished: newFinishedState,
      });

      if (response.status !== 200) {
        setIsFinished(!newFinishedState);
        console.error('Failed to toggle finished state.');
      }
    } catch (error) {
      console.error('Error toggling finished:', error);
      setIsFinished(!newFinishedState);
    }
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
          <ButtonGroup>
            <Button
                variant={UI_BASE_COLOR}
                href={`/read/${book.identifier}`}
                className="read-button"
            >
              <i className="fas fa-book"></i>
            </Button>

            <Button
                variant={UI_BASE_COLOR}
                href={`/download/${book.identifier}`}
                className="download-button"
            >
              <i className="fas fa-download"></i>
            </Button>
            <DropdownButton as={ButtonGroup} title=" " id="bg-nested-dropdown" variant={UI_BASE_COLOR}>
              <ButtonGroup>
                <Button
                    variant={isFavorite ? UI_BASE_COLOR : `outline-${UI_BASE_COLOR}`}
                    onClick={handleToggleFavorite}
                    className="favorite-button"
                    disabled={!isLoggedIn}
                >
                  <i className="fas fa-star"></i>
                </Button>
                <Button
                    variant={isFinished ? UI_BASE_COLOR : `outline-${UI_BASE_COLOR}`}
                    onClick={handleToggleFinished}
                    className="finished-button"
                    disabled={!isLoggedIn}
                >
                  <i className="fas fa-check"></i>
                </Button>
                <Button
                    variant={UI_BASE_COLOR}
                    className="edit-button"
                    disabled={!isLoggedIn}
                    onClick={() => setShowModal(true)}
                >
                  <i className="fas fa-pencil-alt"></i>
                </Button>
              </ButtonGroup>
            </DropdownButton>
          </ButtonGroup>
        </div>

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
            <Button variant={UI_BASE_COLOR} onClick={handleSave} disabled={loading}>
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