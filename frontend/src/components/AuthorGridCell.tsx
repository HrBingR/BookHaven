// AuthorGridCell.tsx
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useSpring, animated } from '@react-spring/web';
import { Button } from 'react-bootstrap';
import './All.css';
import { useConfig } from '../context/ConfigProvider';

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

    const navigate = useNavigate();
    const { UI_BASE_COLOR } = useConfig();

    return (
        <animated.div className={`grid-cell ${isExpanded ? 'expanded' : ''}`} style={styles}>
            <Button
                variant={UI_BASE_COLOR}
                className={`letter-button ${hasAuthors ? '' : 'disabled'}`}
                onClick={() => hasAuthors && toggleLetter(letter)}
                disabled={!hasAuthors}
            >
                {letter}
            </Button>

            <div className="authors-list">
                {hasAuthors ? (
                    <div className="authors-grid">
                        {authors.map((author, index) => (
                            <Button
                                variant={UI_BASE_COLOR}
                                key={index}
                                className="author-item link-button"
                                onClick={() => navigate(`/authors/${author.replace(/\s+/g, '-').toLowerCase()}`)} // Navigate to the target URL
                            >
                                {author}
                            </Button>
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