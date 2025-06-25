// src/components/Home.tsx
import React, { useState, useEffect, useRef, useCallback } from 'react';
import apiClient from '../utilities/apiClient';
import SearchBar from './SearchBar';
import Books from './Books';
import { Container } from 'react-bootstrap';
import { Book } from '../types';

const CHUNK_SIZE = 18;
const MAX_WINDOW_SIZE = 54;
const PULL_THRESHOLD = 100; // How far user needs to "pull" to trigger load

const Home: React.FC<{ isLoggedIn: boolean }> = ({ isLoggedIn }) => {
  const [books, setBooks] = useState<Book[]>([]);
  const [offset, setOffset] = useState<number>(0);
  const [topOffset, setTopOffset] = useState<number>(0);
  const [hasMore, setHasMore] = useState<boolean>(true);
  const [hasMoreAbove, setHasMoreAbove] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [loadingAbove, setLoadingAbove] = useState<boolean>(false);
  const [pullDistance, setPullDistance] = useState<number>(0);
  const [lastTopLoadTime, setLastTopLoadTime] = useState<number>(0);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [favoritesQueried, setFavoritesQueried] = useState<boolean>(false);
  const [finishedQueried, setFinishedQueried] = useState<boolean>(false);
  const [unfinishedQueried, setUnfinishedQueried] = useState<boolean>(false);

  const observerRef = useRef<IntersectionObserver | null>(null);
  const triggerRef = useRef<HTMLDivElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

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
    console.log('fetchAndAppendBooks - current state:', { offset, topOffset, hasMoreAbove });

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

      // Update offsets
      const newOffset = offset + CHUNK_SIZE;
      setOffset(newOffset);

      // Update topOffset when we slice books from the top
      setTopOffset(prevTopOffset => {
        const newTopOffset = (books.length + newBooks.length > MAX_WINDOW_SIZE)
            ? prevTopOffset + CHUNK_SIZE
            : prevTopOffset;
        console.log('Updated topOffset from', prevTopOffset, 'to', newTopOffset);
        return newTopOffset;
      });

      // Enable loading above once we have some books loaded and topOffset > 0
      if (!hasMoreAbove && (topOffset > 0 || (books.length + newBooks.length > MAX_WINDOW_SIZE))) {
        console.log('Enabling hasMoreAbove');
        setHasMoreAbove(true);
      }
    } finally {
      setLoading(false);
    }
  }, [loading, hasMore, offset, topOffset, hasMoreAbove, books.length, searchTerm]);

  const fetchAndPrependBooks = useCallback(async () => {
    console.log('fetchAndPrepend called with:', { loadingAbove, hasMoreAbove, topOffset });

    // Debounce: prevent rapid successive calls
    const now = Date.now();
    if (now - lastTopLoadTime < 1000) {
      console.log('Debouncing top load');
      return;
    }

    if (loadingAbove || !hasMoreAbove) {
      console.log('Reached fetchAndPrepend, but loading or no more above');
      return;
    }

    const newTopOffset = Math.max(0, topOffset - CHUNK_SIZE);
    console.log('Attempting to load from offset:', newTopOffset, 'current topOffset:', topOffset);

    if (newTopOffset >= topOffset) {
      console.log('Cannot load - newTopOffset >= topOffset');
      setHasMoreAbove(false);
      return;
    }

    setLoadingAbove(true);
    setLastTopLoadTime(now);
    setPullDistance(0);

    try {
      const newBooks = await fetchBooks(newTopOffset, CHUNK_SIZE);
      console.log('Fetched books for prepend:', newBooks.length);

      if (newBooks.length === 0) {
        setHasMoreAbove(false);
        return;
      }

      setBooks((prevBooks) => {
        const existingBookIds = new Set(prevBooks.map((book) => book.id));
        const uniqueNewBooks = newBooks.filter((book) => !existingBookIds.has(book.id));
        console.log('Unique new books to prepend:', uniqueNewBooks.length);

        const updatedBooks = [...uniqueNewBooks, ...prevBooks];
        return updatedBooks.length > MAX_WINDOW_SIZE
            ? updatedBooks.slice(0, -CHUNK_SIZE)
            : updatedBooks;
      });

      setTopOffset(newTopOffset);
      console.log('Updated topOffset to:', newTopOffset);

      if (newTopOffset === 0) {
        setHasMoreAbove(false);
      }
    } finally {
      setLoadingAbove(false);
    }
  }, [loadingAbove, hasMoreAbove, topOffset, lastTopLoadTime, searchTerm]);

  // Handle pull-to-load scroll behavior
  useEffect(() => {
    let startY = 0;
    let isAtTop = false;

    const handleTouchStart = (e: TouchEvent) => {
      startY = e.touches[0].clientY;
      isAtTop = window.scrollY === 0;
    };

    const handleTouchMove = (e: TouchEvent) => {
      if (!isAtTop || !hasMoreAbove || loadingAbove) return;

      const currentY = e.touches[0].clientY;
      const deltaY = currentY - startY;

      if (deltaY > 0 && window.scrollY === 0) {
        // User is pulling down from the top
        setPullDistance(Math.min(deltaY, PULL_THRESHOLD + 50));

        // Prevent default scrolling when pulling
        if (deltaY > 10) {
          e.preventDefault();
        }
      }
    };

    const handleTouchEnd = () => {
      if (pullDistance >= PULL_THRESHOLD && hasMoreAbove && !loadingAbove) {
        fetchAndPrependBooks();
      }
      setPullDistance(0);
    };

    // For desktop: use scroll events
    const handleScroll = () => {
      if (window.scrollY === 0) {
        // User is at the very top
        isAtTop = true;
      } else {
        isAtTop = false;
        setPullDistance(0);
      }
    };

    // For desktop: simulate pull with mouse wheel when at top
    const handleWheel = (e: WheelEvent) => {
      if (window.scrollY === 0 && e.deltaY < 0 && hasMoreAbove && !loadingAbove) {
        // User is scrolling up while at the top
        e.preventDefault();

        const newPullDistance = Math.min(pullDistance + Math.abs(e.deltaY), PULL_THRESHOLD + 50);
        setPullDistance(newPullDistance);

        if (newPullDistance >= PULL_THRESHOLD) {
          fetchAndPrependBooks();
        }
      }
    };

    // Add event listeners
    document.addEventListener('touchstart', handleTouchStart, { passive: true });
    document.addEventListener('touchmove', handleTouchMove, { passive: false });
    document.addEventListener('touchend', handleTouchEnd, { passive: true });
    document.addEventListener('scroll', handleScroll, { passive: true });
    document.addEventListener('wheel', handleWheel, { passive: false });

    return () => {
      document.removeEventListener('touchstart', handleTouchStart);
      document.removeEventListener('touchmove', handleTouchMove);
      document.removeEventListener('touchend', handleTouchEnd);
      document.removeEventListener('scroll', handleScroll);
      document.removeEventListener('wheel', handleWheel);
    };
  }, [pullDistance, hasMoreAbove, loadingAbove, fetchAndPrependBooks]);

  const refreshBooks = () => {
    setOffset(0);
    setTopOffset(0);
    setHasMore(true);
    setHasMoreAbove(false);
    setBooks([]);
    setPullDistance(0);
  };

  useEffect(() => {
    setOffset(0);
    setTopOffset(0);
    setHasMore(true);
    setHasMoreAbove(false);
    setBooks([]);
    setPullDistance(0);
  }, [searchTerm]);

  // Bottom observer
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
      <Container fluid className="p-4" ref={containerRef}>
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
              refreshBooks={refreshBooks}
              isLoggedIn={isLoggedIn}
          />

          {hasMoreAbove && (
              <div className="text-center mt-2 mb-3" style={{ fontSize: '14px', color: '#666' }}>
                <p>Scroll up or pull down to load previous books</p>
              </div>
          )}

          {loadingAbove && (
              <div className="text-center mt-4">
                <p>Loading previous books...</p>
              </div>
          )}

          <Books books={books} refreshBooks={refreshBooks} isLoggedIn={isLoggedIn} />

          {loading && (
              <div className="text-center mt-4">
                <p>Loading...</p>
              </div>
          )}

          {/* Bottom loading trigger */}
          <div ref={triggerRef} style={{ height: '1px' }} />

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