import React, { useState, useEffect } from 'react';
import { useParams, Link, LinkProps } from 'react-router-dom';
import apiClient from '../utilities/apiClient';
import { Container, Row, Col, ButtonProps } from 'react-bootstrap';
import BookCard from './BookCard';
import { Book } from '../types';
import './All.css';

// Extend ButtonProps to include React Router "to" Prop
type ButtonLinkProps = ButtonProps & LinkProps;

// Fix Link for react-bootstrap compatibility
const RouterLink = React.forwardRef<HTMLAnchorElement, ButtonLinkProps>(({ to, ...rest }, ref) => (
    <Link ref={ref} to={to} {...rest} />
));
RouterLink.displayName = 'RouterLink';

const groupAndSortBySeries = (books: Book[]) => {
    const grouped: { [key: string]: Book[] } = {};

    books.forEach((book) => {
        const seriesName = book.series || "Standalone"; // Group standalone books separately
        if (!grouped[seriesName]) {
            grouped[seriesName] = [];
        }
        grouped[seriesName].push(book);
    });

    // Sort books within each group by series index
    for (const series in grouped) {
        grouped[series].sort((a, b) => (a.seriesindex || 0) - (b.seriesindex || 0));
    }

    return grouped;
};

const kebabToTitleCase = (str: string | undefined): string => {
    if (!str) return ""; // Handle undefined input
    return str
        .split('-') // Split into words based on the hyphen
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1)) // Capitalize first letter of each word
        .join(' '); // Join them back with a space
};

const AuthorPage: React.FC<{ isLoggedIn: boolean }> = ({isLoggedIn}) => {
    const { authorName } = useParams<{ authorName: string }>(); // Get the author name from the route
    const [booksBySeries, setBooksBySeries] = useState<{ [key: string]: Book[] }>({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchAuthorBooks = async () => {
            setLoading(true);
            setError(null);

            try {
                const response = await apiClient.get(`/api/authors/${authorName}`);
                const groupedBooks = groupAndSortBySeries(response.data.books);
                setBooksBySeries(groupedBooks);
            } catch (err) {
                console.error('Error fetching author books:', err);
                setError('Failed to load books for this author.');
            } finally {
                setLoading(false);
            }
        };

        fetchAuthorBooks();
    }, [authorName]);

    if (loading) {
        return <p className="text-center">Loading books...</p>;
    }

    if (error) {
        return <p className="text-danger text-center">{error}</p>;
    }

    return (
        <Container fluid className="p-4 wrapper-div">
            {/* Header */}
            <div className="header-container">
                <div className="spacer"></div>
                <h2 className="text-center title">{kebabToTitleCase(authorName)}</h2>
                <Link to="/authors" className="btn btn-secondary back-button">
                    Back to Authors
                </Link>
            </div>
            <hr className="authors-divider"/>

            {/* Books by Series */}
            {Object.entries(booksBySeries).map(([seriesName, books]) => (
                <div key={seriesName} className="mb-4">
                    {/* Series Title */}
                    <div className="series-title">
                        {seriesName !== "Standalone" ? seriesName : "Standalone Titles"}
                    </div>

                    {/* Book Grid */}
                    <Row className="mt-4">
                        {books.map((book) => (
                            <Col
                                key={book.id}
                                sm={12} /* Full width on small devices */
                                md={6} /* Half width when <= 2 books */
                                lg={books.length <= 3 ? 2 : 2} /* Adjust for larger layouts */
                                className="mb-4"
                            >
                                <BookCard book={book} refreshBooks={() => {}} isLoggedIn={isLoggedIn} />
                            </Col>
                        ))}
                        {/* Add placeholders if the number of books is less than the grid capacity */}
                        {books.length < 3 &&
                            Array.from({ length: 7 - books.length }, (_, index) => (
                                <Col
                                    key={`placeholder-${index}`}
                                    sm={12}
                                    md={6}
                                    lg={4}
                                    className="mb-4 placeholder-col"
                                >
                                    <div className="placeholder-div"></div>
                                </Col>
                            ))}
                    </Row>
                </div>
            ))}
        </Container>
    );
};

export default AuthorPage;