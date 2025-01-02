// src/components/BookCard.tsx
import React from 'react';
import { Card, Button } from 'react-bootstrap';
import './BookCard.css'; // Import the CSS file

interface Book {
  id: number;
  title: string;
  authors: string[];
  series: string;
  seriesindex: number;
  coverUrl: string;
  relative_path: string;
}

interface BookCardProps {
  book: Book;
}

const BookCard: React.FC<BookCardProps> = ({ book }) => {
  const formatSeriesIndex = (index: number): string | null => {
    if (index === 0.0) return null;
    if (Number.isInteger(index)) return index.toString();
    return index.toString();
  };

  return (
    <Card className="card-container">
      {/* Cover Image */}
      <Card.Img
        variant="top"
        src={book.coverUrl}
        alt={book.title}
        className="book-cover"
      />

      {/* Card Content */}
      <Card.Body>
        <Card.Title>{book.title}</Card.Title>
        <Card.Text>By {book.authors.join(', ')}</Card.Text>
        {book.series && book.seriesindex !== 0.0 && (
          <Card.Text>
            Book {formatSeriesIndex(book.seriesindex)} of the {book.series} series
          </Card.Text>
        )}
      </Card.Body>

      {/* Footer Button */}
      <div className="card-footer">
        <Button variant="primary" href={`/download/${book.relative_path}`}>
          Download
        </Button>
      </div>
    </Card>
  );
};

export default BookCard;