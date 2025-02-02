import React, { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { ReactReader } from "react-reader";
import apiClient from '../utilities/apiClient';
import "./All.css";

const Reader: React.FC = () => {
    const { identifier } = useParams<{ identifier: string }>();
    const [epubUrl, setEpubUrl] = useState<string>("");
    const [location, setLocation] = useState<string | null>(null);
    const [fontSize, setFontSize] = useState<number>(16);
    const renditionRef = useRef<any>(null);

    useEffect(() => {
        const fetchBookDetails = async () => {
            try {
                const bookResponse = await apiClient.get(`/api/books/${identifier}`);
                const streamResponse = await apiClient.get(`/stream/${identifier}`);
                const { progress } = bookResponse.data;
                const { url } = streamResponse.data;
                console.log(url);

                setEpubUrl(url);
                if (progress) setLocation(progress);
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
        setLocation(cfi);
        saveProgress(cfi);
    };

    const increaseFontSize = () => {
        setFontSize((prevFontSize) => {
            const newFontSize = prevFontSize + 2;
            updateFontSize(newFontSize);
            return newFontSize;
        });
    };

    const decreaseFontSize = () => {
        setFontSize((prevFontSize) => {
            const newFontSize = prevFontSize > 10 ? prevFontSize - 2 : prevFontSize;
            updateFontSize(newFontSize);
            return newFontSize;
        });
    };

    const updateFontSize = (size: number) => {
        if (renditionRef.current) {
            renditionRef.current.themes.fontSize(`${size}px`);
        }
    };

    return (
        <div className="reader-container">
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
                            renditionRef.current.themes.default({
                                body: {
                                    overflow: "hidden",
                                },
                            });
                            updateFontSize(fontSize);
                            renditionRef.current.flow("scrolled");
                        }}
                    />
                )}
            </div>
        </div>
    );
};

export default Reader;