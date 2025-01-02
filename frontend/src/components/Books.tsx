// src/components/Books.tsx
import React from 'react';
import BookCard from './BookCard';
import { Row, Col, Pagination } from 'react-bootstrap';

interface Book {
  id: number;
  title: string;
  authors: string[];
  series: string;
  seriesindex: number;
  coverUrl: string;
  relative_path: string;
}

interface BooksProps {
  books: Book[];
  onPageChange: (page: number) => void;
  currentPage: number;
}

const Books: React.FC<BooksProps> = ({ books, onPageChange, currentPage }) => {
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
                    <Col key={book.id} sm={2} md={2} lg={2} className="mb-4">
                      <BookCard book={book}/>
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