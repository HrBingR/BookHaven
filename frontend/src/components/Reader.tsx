import React, { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { ReactReader } from "react-reader";
import apiClient from '../utilities/apiClient';
import "./All.css";

const Reader: React.FC = () => {
    const { identifier } = useParams<{ identifier: string }>();
    const [epubUrl, setEpubUrl] = useState<string>(""); // URL of the ePub file
    const [location, setLocation] = useState<string | null>(null); // Reading progress
    const [fontSize, setFontSize] = useState<number>(16); // Font size (default: 16px)
    const renditionRef = useRef<any>(null); // Reference for react-reader's Rendition

    useEffect(() => {
        const fetchBookDetails = async () => {
            try {
                const bookResponse = await apiClient.get(`/api/books/${identifier}`);
                const streamResponse = await apiClient.get(`/stream/${identifier}`);
                const { progress } = bookResponse.data;
                const { url } = streamResponse.data;
                console.log(url);

                setEpubUrl(url); // Set the stream URL
                if (progress) setLocation(progress); // Restore reading progress
            } catch (err) {
                console.error("Error occurred while fetching book details:", err);
            }
        };

        fetchBookDetails();
    }, [identifier]);

    const saveProgress = async (cfi: string) => {
        try {
            await apiClient.put(`/api/books/${identifier}/progress_state`, { progress: cfi });
        } catch (err) {
            console.error("Error saving reading progress:", err);
        }
    };

    const onLocationChange = (cfi: string) => {
        setLocation(cfi); // Update progress locally
        saveProgress(cfi); // Save progress to API
    };

    const increaseFontSize = () => {
        setFontSize((prevFontSize) => {
            const newFontSize = prevFontSize + 2; // Increment font size
            updateFontSize(newFontSize);
            return newFontSize;
        });
    };

    const decreaseFontSize = () => {
        setFontSize((prevFontSize) => {
            const newFontSize = prevFontSize > 10 ? prevFontSize - 2 : prevFontSize; // Decrement font size, min 10px
            updateFontSize(newFontSize);
            return newFontSize;
        });
    };

    const updateFontSize = (size: number) => {
        if (renditionRef.current) {
            renditionRef.current.themes.fontSize(`${size}px`); // Update font size in the rendition
        }
    };

    return (
        <div className="reader-container">
            {/* Font Size Controls */}
            <div className="reader-content">
                <div className="reader-font-controls">
                    <button onClick={increaseFontSize}>+</button>
                    <button onClick={decreaseFontSize}>-</button>
                </div>
                {epubUrl && (
                    <ReactReader
                        url={epubUrl}
                        location={location}
                        locationChanged={onLocationChange}
                        getRendition={(rendition) => {
                            renditionRef.current = rendition;
                            // Set up default font size when the book is loaded
                            renditionRef.current.themes.default({
                                body: {
                                    overflow: "hidden",
                                },
                            });
                            updateFontSize(fontSize); // Apply the current font size
                            renditionRef.current.flow("scrolled"); // Enable scrolling flow
                        }}
                    />
                )}
            </div>
        </div>
    );
};

export default Reader;