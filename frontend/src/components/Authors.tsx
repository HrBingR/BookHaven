// Authors.tsx
import React, { useState, useEffect } from 'react';
import apiClient from '../utilities/apiClient';
import { Button } from 'react-bootstrap';
import './All.css';
import AuthorGridCell from './AuthorGridCell';
import { useConfig } from '../context/ConfigProvider';

const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');

interface AuthorsData {
  [key: string]: string[];
}

const Authors: React.FC = () => {
  const [authorsData, setAuthorsData] = useState<AuthorsData>(
    alphabet.reduce((acc, letter) => {
      acc[letter] = [];
      return acc;
    }, {} as AuthorsData)
  );
  const [expandedLetters, setExpandedLetters] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const { UI_BASE_COLOR } = useConfig();

  useEffect(() => {
    const fetchAuthors = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await apiClient.get('/api/authors');
        const authors: string[] = response.data.authors;

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

const expandAll = () => {
  const lettersWithAuthors = new Set(
    alphabet.filter((letter) => authorsData[letter]?.length > 0)
  );
  setExpandedLetters(lettersWithAuthors);
};

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
        <Button className="btn btn-primary me-2" onClick={expandAll} variant={UI_BASE_COLOR}>
          Expand All
        </Button>
        <Button className="btn btn-secondary collapse-button" onClick={collapseAll} variant={UI_BASE_COLOR}>
          Collapse All
        </Button>
      </div>

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