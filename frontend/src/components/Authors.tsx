// Authors.tsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './Authors.Grid.css'; // Grid styles
import './Authors.General.css';
import './Authors.Responsive.css';
import './Authors.Buttons.css';
import AuthorGridCell from './AuthorGridCell'; // Import the new component

const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');

interface AuthorsData {
  [key: string]: string[];
}

const Authors: React.FC = () => {
  const [authorsData, setAuthorsData] = useState<AuthorsData>(
    alphabet.reduce((acc, letter) => {
      acc[letter] = []; // Empty array for default
      return acc;
    }, {} as AuthorsData)
  );
  const [expandedLetters, setExpandedLetters] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch authors from the API
  useEffect(() => {
    const fetchAuthors = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await axios.get('/api/authors'); // Assume this fetches authors
        const authors: string[] = response.data.authors;

        // Group authors by the first letter
        const groupedAuthors: AuthorsData = alphabet.reduce((acc, letter) => {
          acc[letter] = [];
          return acc;
        }, {} as AuthorsData);

        authors.forEach((author) => {
          const firstLetter = author[0].toUpperCase();
          if (groupedAuthors[firstLetter]) {
            groupedAuthors[firstLetter].push(author);
          }
        });

        setAuthorsData(groupedAuthors);
      } catch (err) {
        console.error('Error fetching authors:', err);
        setError('Failed to load authors list. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchAuthors();
  }, []);

  // Toggle letter expansion
  const toggleLetter = (letter: string) => {
    setExpandedLetters((prev) => {
      const updated = new Set(prev);
      if (updated.has(letter)) {
        updated.delete(letter);
      } else {
        updated.add(letter);
      }
      return updated;
    });
  };

  // Expand all letters
// Expand only letters that have authors
const expandAll = () => {
  const lettersWithAuthors = new Set(
    alphabet.filter((letter) => authorsData[letter]?.length > 0)
  );
  setExpandedLetters(lettersWithAuthors);
};

  // Collapse all letters
  const collapseAll = () => {
    setExpandedLetters(new Set());
  };

  console.group(`Authors render: ${new Date().toISOString()}`);
  console.log('Alphabet:', alphabet);
  console.log('Authors Data:', authorsData);
  console.log('Expanded Letters:', [...expandedLetters]);
  console.groupEnd();

  if (loading) {
    return <div className="text-center mt-4">Loading authors...</div>;
  }

  if (error) {
    return <div className="text-danger text-center mt-4">{error}</div>;
  }

  return (
    <div className="authors-container p-4">
      <h1 className="page-heading">Books by Author</h1>
      <hr className="authors-divider" /> {/* Separator line */}
      <div className="expand-controls mb-4">
        <button className="btn btn-primary me-2" onClick={expandAll}>
          Expand All
        </button>
        <button className="btn btn-secondary" onClick={collapseAll}>
          Collapse All
        </button>
      </div>

      {/* Authors Grid */}
      <div className="grid">
        {alphabet.map((letter) => {
          const hasAuthors = authorsData[letter]?.length > 0;
          const isExpanded = expandedLetters.has(letter);
          const authors = authorsData[letter] || [];

          return (
            <AuthorGridCell
              key={letter}
              letter={letter}
              hasAuthors={hasAuthors}
              isExpanded={isExpanded}
              toggleLetter={toggleLetter}
              authors={authors}
            />
          );
        })}
      </div>
    </div>
  );
};

export default Authors;