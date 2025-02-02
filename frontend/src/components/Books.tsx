// src/components/Books.tsx
import React from 'react';
import BookCard from './BookCard';
import { Row, Col } from 'react-bootstrap';
import { Book } from '../types';

interface BooksProps {
  books: Book[];
  refreshBooks: () => void;
  isLoggedIn: boolean;
}

const Books: React.FC<BooksProps> = ({ books, refreshBooks, isLoggedIn }) => {
  return (
      <Row className="mt-4">
        {books.map((book) => (
            <Col
                key={book.id}
                sm={6}
                md={4}
                lg={3}
                xl={3}
                xxl={2}
                className="mb-4 card-column"
            >
              <BookCard book={book} refreshBooks={refreshBooks} isLoggedIn={isLoggedIn} />
            </Col>
        ))}
        {/* Add placeholders if the number of books is less than the grid capacity */}
        {books.length < 3 &&
            Array.from({ length: 7 - books.length }, (_, index) => (
                <Col
                    key={`placeholder-${index}`}
                    sm={12}
                    md={6}
                    lg={4}
                    xl={3}
                    xxl={2}
                    className="mb-4 placeholder-col card-column"
                >
                  <div className="placeholder-div"></div>
                </Col>
            ))}
      </Row>
  );
};

export default Books;