// src/context/ConfigProvider.tsx
import React, { createContext, useContext, useEffect, useState } from 'react';
import { fetchApiConfig } from '../utilities/fetchApiConfig'; // Import your helper

// Define the Config interface
export interface ConfigContextType {
    UI_BASE_COLOR: string;
}

// Create Context
const ConfigContext = createContext<ConfigContextType | null>(null);

// Provider Component
export const ConfigProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [config, setConfig] = useState<ConfigContextType | null>(null);

    // Fetch configuration during initialization
    useEffect(() => {
        const loadConfig = async () => {
            try {
                const runtimeConfig = await fetchApiConfig();
                setConfig(runtimeConfig); // Cache the config in state
            } catch (error) {
                console.error('Failed to load configuration:', error);
            }
        };
        loadConfig();
    }, []);

    // Render loading state until config is loaded
    if (!config) {
        return <div>Loading configuration...</div>;
    }

    return (
        <ConfigContext.Provider value={config}>{children}</ConfigContext.Provider>
    );
};

// Hook to access the configuration
export const useConfig = () => {
    const context = useContext(ConfigContext);
    if (!context) {
        throw new Error('useConfig must be used within a ConfigProvider');
    }
    return context;
};