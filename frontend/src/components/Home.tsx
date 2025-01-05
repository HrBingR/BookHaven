// src/components/Home.tsx
import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import SearchBar from './SearchBar';
import Books from './Books';
import { Container } from 'react-bootstrap';
import { Book } from '../types';

const CHUNK_SIZE = 18; // Number of books to fetch per request
const MAX_WINDOW_SIZE = 54; // Maximum number of books to keep in memory (sliding window)

const groupAndSortBooks = (books: Book[]): Book[] => {
  const sortedBooks = [...books];

  sortedBooks.sort((a, b) => {
    // Step 1: Compare by the first author alphabetically
    const authorComparison = a.authors[0].localeCompare(b.authors[0]);
    if (authorComparison !== 0) return authorComparison;

    // Step 2: Compare by series name alphabetically (if both are in a series)
    if (a.series && b.series) {
      const seriesComparison = a.series.localeCompare(b.series);
      if (seriesComparison !== 0) return seriesComparison;
    }

    // Step 3: If either book is not in a series, sort books not in a series after those in a series
    if (!a.series && b.series) {
      return 1;
    } else if (a.series && !b.series) {
      return -1;
    }

    // Step 4: If both are in the same series, compare by series index (ascending)
    if (a.series && b.series && a.series === b.series) {
      return (a.seriesindex || 0) - (b.seriesindex || 0);
    }

    // Step 5: If neither is in a series, or series/index comparison is equal, compare by title alphabetically
    return a.title.localeCompare(b.title);
  });

  return sortedBooks;
};

const Home: React.FC = () => {
  const [books, setBooks] = useState<Book[]>([]); // Current list of books
  const [offset, setOffset] = useState<number>(0); // Offset for fetching the next books
  const [hasMore, setHasMore] = useState<boolean>(true); // Tracks whether more books are available
  const [loading, setLoading] = useState<boolean>(false); // Tracks if books are being loaded
  const [searchTerm, setSearchTerm] = useState<string>(''); // Tracks the search query

  const observerRef = useRef<IntersectionObserver | null>(null); // Reference to IntersectionObserver
  const triggerRef = useRef<HTMLDivElement | null>(null); // Reference to #scroll-trigger

  const fetchBooks = async (offset: number, limit: number): Promise<Book[]> => {
    try {
      const response = await axios.get('/api/books', {
        params: { query: searchTerm, offset, limit },
      });
      const groupedBooks = groupAndSortBooks(response.data.books);
      return groupedBooks || [];
    } catch (error) {
      console.error('Error fetching books:', error);
      return [];
    }
  };

  const fetchAndAppendBooks = useCallback(async () => {
    if (loading || !hasMore) return;

    setLoading(true);

    try {
      const newBooks = await fetchBooks(offset, CHUNK_SIZE);

      if (newBooks.length === 0) {
        setHasMore(false);
        return;
      }

      setBooks((prevBooks) => {
        const existingBookIds = new Set(prevBooks.map((book) => book.id));
        const uniqueNewBooks = newBooks.filter((book) => !existingBookIds.has(book.id));

        const updatedBooks = [...prevBooks, ...uniqueNewBooks];
        return updatedBooks.length > MAX_WINDOW_SIZE
            ? updatedBooks.slice(CHUNK_SIZE) // Trim old books beyond the limit
            : updatedBooks;
      });

      setOffset((prevOffset) => prevOffset + CHUNK_SIZE);
    } finally {
      setLoading(false);
    }
  }, [loading, hasMore, offset, searchTerm]);
  const refreshBooks = () => {
     setOffset(0); // Reset offset
     setHasMore(true); // Allow loading more books
     setBooks([]); // Clear current books and trigger re-fetch
   };

  useEffect(() => {
    setOffset(0); // Reset offset when search term changes
    setHasMore(true); // Allow loading more books
    setBooks([]); // Clear current books
  }, [searchTerm]);

  useEffect(() => {
    const observerCallback: IntersectionObserverCallback = (entries) => {
      if (entries[0].isIntersecting && hasMore) {
        fetchAndAppendBooks();
      }
    };

    observerRef.current = new IntersectionObserver(observerCallback, {
      root: null,
      rootMargin: '20px',
      threshold: 0,
    });

    if (triggerRef.current) {
      observerRef.current.observe(triggerRef.current);
    }

    return () => {
      if (observerRef.current) observerRef.current.disconnect();
    };
  }, [fetchAndAppendBooks, hasMore]);

  const handleSearch = (term: string) => {
    setSearchTerm(term);
  };

  return (
      <Container fluid className="p-4">
        <div className="wrapper-div">
          <SearchBar onSearch={handleSearch} />
          <Books books={books} refreshBooks={refreshBooks} />
          {loading && (
              <div className="text-center mt-4">
                <p>Loading...</p>
              </div>
          )}
          <div ref={triggerRef} id="scroll-trigger" style={{ height: '1px' }} />
          {!hasMore && !loading && (
              <div className="text-center mt-4">
                <p>No more books to load.</p>
              </div>
          )}
        </div>
      </Container>
  );
};

export default Home;