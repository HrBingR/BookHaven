import { ConfigContextType } from '../context/ConfigProvider';

export const fetchApiConfig = async (): Promise<ConfigContextType> => {
    const response = await fetch('/api/react-init');
    if (!response.ok) {
        throw new Error(`Failed to fetch configuration: ${response.statusText}`);
    }
    const data = await response.json();

    if (!data.UI_BASE_COLOR) {
        throw new Error('Missing required configuration property: UI_BASE_COLOR');
    }

    return data;
};