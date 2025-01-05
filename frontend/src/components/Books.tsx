// src/components/Books.tsx
import React from 'react';
import BookCard from './BookCard';
import { Row, Col } from 'react-bootstrap';
import { Book } from '../types';

interface BooksProps {
  books: Book[];
  refreshBooks: () => void;
}

const Books: React.FC<BooksProps> = ({ books, refreshBooks }) => {
  return (
      <Row className="mt-4">
        {books.map((book) => (
            <Col
                key={book.id}
                sm={12} /* Full width on small devices */
                md={6} /* Half width on medium devices */
                lg={books.length <= 3 ? 2 : 2} /* Adjust for larger layouts */
                className="mb-4"
            >
              <BookCard book={book} refreshBooks={refreshBooks} />
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
                    className="mb-4 placeholder-col"
                >
                  <div className="placeholder-div"></div>
                </Col>
            ))}
      </Row>
  );
};

export default Books;