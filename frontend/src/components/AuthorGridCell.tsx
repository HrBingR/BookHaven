// AuthorGridCell.tsx
import React from 'react';
import { useSpring, animated } from '@react-spring/web';
import './Authors.Grid.css'; // Grid styles
import './Authors.General.css';
import './Authors.Responsive.css';
import './Authors.Buttons.css';

interface AuthorGridCellProps {
  letter: string;
  hasAuthors: boolean;
  isExpanded: boolean;
  toggleLetter: (letter: string) => void;
  authors: string[];
}

const AuthorGridCell: React.FC<AuthorGridCellProps> = ({
  letter,
  hasAuthors,
  isExpanded,
  toggleLetter,
  authors,
}) => {
  const expandedHeight = Math.max(150, 50 + authors.length * 30); // Base height + 30px per author, minimum 150px
  const collapsedHeight = 85; // Fixed height when collapsed
  const styles = useSpring({
    height: isExpanded ? `${expandedHeight}px` : `${collapsedHeight}px`,
    transform: isExpanded ? 'scale(1.02)' : 'scale(1)',
    config: { tension: 200, friction: 20 },
  });

  return (
    <animated.div className={`grid-cell ${isExpanded ? 'expanded' : ''}`} style={styles}>
      <button
        className={`letter-button ${hasAuthors ? 'active' : 'disabled'}`}
        onClick={() => hasAuthors && toggleLetter(letter)}
        disabled={!hasAuthors}
      >
        {letter}
      </button>

      <div className="authors-list">
        {hasAuthors ? (
          authors.map((author, index) => (
            <div key={index} className="author-item">
              {author}
            </div>
          ))
        ) : (
          <div className="no-authors">No authors available</div>
        )}
      </div>
    </animated.div>
  );
};

export default AuthorGridCell;