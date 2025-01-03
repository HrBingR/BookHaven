// src/components/Home.tsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import SearchBar from './SearchBar';
import Books from './Books';
import { Container } from 'react-bootstrap';
import { Book } from '../types';

const groupAndSortBooks = (books: Book[]): Book[] => {
  // Copy the array to avoid mutating the original data
  const sortedBooks = [...books];

  // Sort by author, then series, then series index
  sortedBooks.sort((a, b) => {
    // First, compare authors (case-insensitive)
    const authorComparison = a.authors[0].localeCompare(b.authors[0]);
    if (authorComparison !== 0) return authorComparison;

    // If authors are the same, compare by series (null values last)
    if (a.series && b.series) {
      const seriesComparison = a.series.localeCompare(b.series);
      if (seriesComparison !== 0) return seriesComparison;
    } else if (a.series) {
      return -1; // a has a series, b doesn't -> a comes first
    } else if (b.series) {
      return 1; // b has a series, a doesn't -> b comes first
    }

    // If series are the same (or both null), sort by series index (numerical order)
    return (a.seriesindex || 0) - (b.seriesindex || 0);
  });

  return sortedBooks;
};

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
      const processedBooks = groupAndSortBooks(response.data.books);
      setBooks(processedBooks);
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
      <Books
        books={books}
        onPageChange={handlePageChange}
        currentPage={currentPage}
        refreshBooks={fetchBooks} // Pass fetchBooks as a prop
      />
    </Container>
  );
};

export default Home;