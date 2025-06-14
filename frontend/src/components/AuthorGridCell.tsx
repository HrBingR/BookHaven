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
    // Calculate expanded height based on CSS grid layout
    const calculateExpandedHeight = () => {
        if (!hasAuthors || authors.length === 0) return 160;

        // Estimate authors per row based on typical button width and container width
        // This is an approximation since we can't easily get the actual container width
        // Typical author button: ~120px width + gaps
        // Assume container width varies: small screens ~300px, medium ~600px, large ~900px+

        // Use a responsive approach - assume fewer authors per row for smaller calculations
        const minAuthorsPerRow = 2; // Conservative estimate for smaller screens
        const maxAuthorsPerRow = 7; // Estimate for larger screens

        // Use a middle ground that works reasonably well across screen sizes
        const estimatedAuthorsPerRow = Math.max(minAuthorsPerRow, Math.min(maxAuthorsPerRow, Math.floor(authors.length / 2) || minAuthorsPerRow));

        const estimatedRows = Math.ceil(authors.length / estimatedAuthorsPerRow);

        // Base height + height per row of authors
        const baseHeight = 85; // Height of the letter button and padding
        const authorRowHeight = 45; // Height of each row of author buttons (button + gap)

        return Math.max(150, baseHeight + (estimatedRows * authorRowHeight));
    };

    const expandedHeight = calculateExpandedHeight();
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