// src/components/Home.tsx
import React, { useState, useEffect, useRef, useCallback } from 'react';
import apiClient from '../utilities/apiClient';
import SearchBar from './SearchBar';
import Books from './Books';
import { Container } from 'react-bootstrap';
import { Book } from '../types';

const CHUNK_SIZE = 18;
const MAX_WINDOW_SIZE = 54;

const Home: React.FC<{ isLoggedIn: boolean }> = ({ isLoggedIn }) => {
  const [books, setBooks] = useState<Book[]>([]);
  const [offset, setOffset] = useState<number>(0);
  const [hasMore, setHasMore] = useState<boolean>(true);
  const [loading, setLoading] = useState<boolean>(false);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [favoritesQueried, setFavoritesQueried] = useState<boolean>(false);
  const [finishedQueried, setFinishedQueried] = useState<boolean>(false);
  const [unfinishedQueried, setUnfinishedQueried] = useState<boolean>(false);

  const observerRef = useRef<IntersectionObserver | null>(null);
  const triggerRef = useRef<HTMLDivElement | null>(null);

  const fetchBooks = async (offset: number, limit: number): Promise<Book[]> => {
    try {
      const response = await apiClient.get('/api/books', {
        params: {
          query: searchTerm,
          offset,
          limit,
          favorites: favoritesQueried,
          finished: finishedQueried,
          unfinished: unfinishedQueried,
        },
      });
      console.log('API Response:', response);
      if (!response.data || !Array.isArray(response.data.books)) {
        console.error('Invalid API response:', response.data);
        return [];
      }
      const fetchedBooks = response.data.books;
      return fetchedBooks || [];
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
            ? updatedBooks.slice(CHUNK_SIZE)
            : updatedBooks;
      });

      setOffset((prevOffset) => prevOffset + CHUNK_SIZE);
    } finally {
      setLoading(false);
    }
  }, [loading, hasMore, offset, searchTerm]);
  const refreshBooks = () => {
    setOffset(0);
    setHasMore(true);
    setBooks([]);
  };

  useEffect(() => {
    setOffset(0);
    setHasMore(true);
    setBooks([]);
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
          <SearchBar
              onSearch={handleSearch}
              favoritesActive={favoritesQueried}
              finishedActive={finishedQueried}
              unFinishedActive={unfinishedQueried}
              onFavoritesToggle={() => {
                setFavoritesQueried((prev) => !prev);
                refreshBooks();
              }}
              onFinishedToggle={() => {
                setFinishedQueried((prev) => !prev);
                setUnfinishedQueried(false)
                refreshBooks();
              }}
              onUnfinishedToggle={() => {
                setUnfinishedQueried((prev) => !prev);
                setFinishedQueried(false)
                refreshBooks();
              }}
              isLoggedIn={isLoggedIn}
          />
          <Books books={books} refreshBooks={refreshBooks} isLoggedIn={isLoggedIn} />
          {loading && (
              <div className="text-center mt-4">
                <p>Loading...</p>
              </div>
          )}
          <div ref={triggerRef} id="scroll-trigger" style={{ height: '1px' }} />
          {!hasMore && !loading && (
              <div className="text-center mt-4">
                {finishedQueried || favoritesQueried ? (
                    <p>No books found with the selected filter.</p>
                ) : (
                    <p>No more books to load.</p>
                )}
              </div>
          )}
        </div>
      </Container>
  );
};

export default Home;