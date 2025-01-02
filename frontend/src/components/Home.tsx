// src/components/Home.tsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import SearchBar from './SearchBar';
import Books from './Books';
import { Container } from 'react-bootstrap';

interface Book {
  id: number;
  title: string;
  authors: string[];
  series: string;
  seriesindex: number;
  coverUrl: string;
  relative_path: string;
}

const Home: React.FC = () => {
  const [books, setBooks] = useState<Book[]>([]);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [currentPage, setCurrentPage] = useState<number>(1);
  const booksPerPage = 8;
//  const [totalBooks, setTotalBooks] = useState<number>(0);
//  const [totalPages, setTotalPages] = useState<number>(1);

  useEffect(() => {
    fetchBooks();
  }, [searchTerm, currentPage]);

  const fetchBooks = async () => {
    try {
      const response = await axios.get('/api/books', {
        params: { query: searchTerm, page: currentPage, limit: booksPerPage },
      });
      setBooks(response.data.books);
//      setTotalBooks(response.data.total_books); // Store total books count
//      setTotalPages(response.data.total_pages); // Store total pages
    } catch (error) {
      console.error('Error fetching books:', error);
    }
  };

  const handleSearch = (term: string) => {
    setSearchTerm(term);
    setCurrentPage(1); // Reset to first page on new search
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  return (
    <Container fluid className="p-4">
      <SearchBar onSearch={handleSearch} />
      <Books books={books} onPageChange={handlePageChange} currentPage={currentPage} />
    </Container>
  );
};

export default Home;