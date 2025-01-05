// AuthorGridCell.tsx
import React from 'react';
import { Link } from 'react-router-dom';
import { useSpring, animated } from '@react-spring/web';
import './All.css';

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
        config: { tension: 1000, friction: 40 },
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
                    <div className="authors-grid">
                        {authors.map((author, index) => (
                            <Link
                                key={index}
                                className="author-item link-button"
                                to={`/authors/${author.replace(/\s+/g, '-').toLowerCase()}`} // Convert author name into a URL-safe string
                            >
                                {author}
                            </Link>
                        ))}
                    </div>
                ) : (
                    <div className="no-authors">No authors available</div>
                )}
            </div>
        </animated.div>
    );
};

export default AuthorGridCell;