// src/components/SearchBar.tsx
import React, { useState } from 'react';
import { Form, FormControl, Button, ButtonGroup, InputGroup, Alert } from 'react-bootstrap';
import './All.css'; // Import the CSS file
import { useConfig } from '../context/ConfigProvider';
import apiClient from "../utilities/apiClient.ts";
import UploadModal from './UploadModal';

interface SearchBarProps {
    onSearch: (term: string) => void;
    favoritesActive: boolean;
    finishedActive: boolean;
    unFinishedActive: boolean;
    onFavoritesToggle: () => void;
    onFinishedToggle: () => void;
    onUnfinishedToggle: () => void;
    isLoggedIn: boolean;
    refreshBooks?: () => void;
}

const SearchBar: React.FC<SearchBarProps> = ({
                                                 onSearch,
                                                 favoritesActive,
                                                 finishedActive,
                                                 unFinishedActive,
                                                 onFavoritesToggle,
                                                 onFinishedToggle,
                                                 onUnfinishedToggle,
                                                 isLoggedIn,
                                                 refreshBooks }) => {
    const [searchTerm, setSearchTerm] = useState<string>('');
    const [showAlert, setShowAlert] = useState(false);
    const [alertMessage, setAlertMessage] = useState('');
    const [showUploadModal, setShowUploadModal] = useState(false);
    const { UI_BASE_COLOR } = useConfig();
    const { UPLOADS_ENABLED } = useConfig();

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSearch(searchTerm);
    };
    
    const handleScan = async () => {
        try {
            // 1) Trigger the scan and get the task ID
            const response = await apiClient.post('/scan-library', {});
            const taskId = response.data.task_id;

            // 2) Show a "scanning" message
            setAlertMessage("Scanning Library...");
            setShowAlert(true);

            // 3) Poll for completion
            let isCompleted = false;
            while (!isCompleted) {
                const statusResp = await apiClient.get(`/scan-status/${taskId}`);
                const taskState = statusResp.data.state;
                if (taskState === "SUCCESS" || taskState === "FAILURE") {
                    isCompleted = true;
                } else {
                    // Wait a bit before checking again
                    await new Promise(resolve => setTimeout(resolve, 1000));
                }
            }

            // 4) Show success message (or handle failure)
            setAlertMessage("Library scan complete! Please refresh to see results.");
            // At this point you can reload or just let users stay on the page
        } catch (err: any) {
            alert(err.message);
        }
    };

    return (
        <>
            <Form onSubmit={handleSubmit}>
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
                        {isLoggedIn && UPLOADS_ENABLED && (
                            <Button
                                variant={UI_BASE_COLOR}
                                className="search-button"
                                onClick={() => setShowUploadModal(true)}
                            >
                                Upload
                            </Button>
                        )}
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
                            {showAlert && <Alert variant="success" onClose={() => setShowAlert(false)} dismissible>{alertMessage}</Alert>}
                        </ButtonGroup>
                    </div>
                )}
            </Form>

            <UploadModal 
                show={showUploadModal} 
                onClose={() => setShowUploadModal(false)}
                refreshBooks={refreshBooks}
            />
        </>
    );
};

export default SearchBar;