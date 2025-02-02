// src/components/SearchBar.tsx
import React, { useState } from 'react';
import { Form, FormControl, Button, ButtonGroup, InputGroup, Alert } from 'react-bootstrap';
import './All.css'; // Import the CSS file
import { useConfig } from '../context/ConfigProvider';
import apiClient from "../utilities/apiClient.ts";

interface SearchBarProps {
    onSearch: (term: string) => void;
    favoritesActive: boolean;
    finishedActive: boolean;
    unFinishedActive: boolean;
    onFavoritesToggle: () => void;
    onFinishedToggle: () => void;
    onUnfinishedToggle: () => void;
    isLoggedIn: boolean; // Determine if filter buttons should be shown
}

const SearchBar: React.FC<SearchBarProps> = ({
                                                 onSearch,
                                                 favoritesActive,
                                                 finishedActive,
                                                 unFinishedActive,
                                                 onFavoritesToggle,
                                                 onFinishedToggle,
                                                 onUnfinishedToggle,
                                                 isLoggedIn }) => {
    const [searchTerm, setSearchTerm] = useState<string>('');
    const [showAlert, setShowAlert] = useState(false);
    const [alertMessage, setAlertMessage] = useState('');
    const { UI_BASE_COLOR } = useConfig();

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSearch(searchTerm);
    };
    const handleScan = async () => {
        try{
            await apiClient.post('/scan-library', {});
            setAlertMessage("Scanning Library...");
            setShowAlert(true);
            await new Promise(resolve => setTimeout(resolve, 2000));
            window.location.reload();
            setShowAlert(false);
            setAlertMessage('');
        } catch (err: any) {
            alert(err.message);
        }
    }

    return (
        <Form onSubmit={handleSubmit}>
            {/* Search bar row */}
            <div className="search-bar-container">
                <InputGroup>
                    <FormControl
                        type="text"
                        placeholder="Search for books, authors, or series..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="search-bar"
                    />
                    <Button variant={UI_BASE_COLOR} type="submit" className="search-button">
                        Search
                    </Button>
                    <Button
                        variant={UI_BASE_COLOR}
                        className="search-button"
                        onClick={() => {
                            handleScan();
                        }}
                    >
                        Scan Library
                    </Button>
                </InputGroup>
            </div>

            {/* Filter chips row */}
            {isLoggedIn && (
                <div className="chips-container mt-2">
                    <ButtonGroup>
                        <Button
                            variant={favoritesActive ? UI_BASE_COLOR : `outline-${UI_BASE_COLOR}`}
                            onClick={onFavoritesToggle}
                        >
                            Favorites
                        </Button>
                        <Button
                            variant={finishedActive ? UI_BASE_COLOR : `outline-${UI_BASE_COLOR}`}
                            onClick={onFinishedToggle}
                        >
                            Finished
                        </Button>
                        <Button
                            variant={unFinishedActive ? UI_BASE_COLOR : `outline-${UI_BASE_COLOR}`}
                            onClick={onUnfinishedToggle}
                        >
                            Unfinished
                        </Button>
                    </ButtonGroup>
                    {showAlert && <Alert variant="success" onClose={() => setShowAlert(false)} dismissible>{alertMessage}</Alert>}
                </div>
            )}
        </Form>
    );
};

export default SearchBar;