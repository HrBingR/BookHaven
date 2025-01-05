// src/components/Books.tsx
import React from 'react';
import BookCard from './BookCard';
import { Row, Col, Pagination } from 'react-bootstrap';
import { Book } from '../types';

interface BooksProps {
  books: Book[];
  onPageChange: (page: number) => void;
  currentPage: number;
  refreshBooks: () => void; // Add the new prop
}

const Books: React.FC<BooksProps> = ({ books, onPageChange, currentPage, refreshBooks }) => {
  const totalPages = Math.ceil(books.length / 8); // Adjust according to total number of books

  const handlePageClick = (page: number) => {
    onPageChange(page);
  };

  const paginationItems = [];
  for (let number = 1; number <= totalPages; number++) {
    paginationItems.push(
        <Pagination.Item key={number} active={number === currentPage} onClick={() => handlePageClick(number)}>
          {number}
        </Pagination.Item>
    );
  }

  return (
      <>
        {books.length === 0 ? (
            <p>No Books Found.</p>
        ) : (
            <>
                    <Row className="mt-4">
                        {books.map((book) => (
                            <Col
                                key={book.id}
                                sm={12} /* Full width on small devices */
                                md={6} /* Half width when <= 2 books */
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
              <Pagination>{paginationItems}</Pagination>
            </>
        )}
      </>
  );
}
export default Books;