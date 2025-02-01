import axios from 'axios';

// Create an Axios instance
const apiClient = axios.create({
    baseURL: `${window.location.origin}`, // Backend base URL
    withCredentials: true, // Enable cookies if needed (e.g., for CSRF tokens)
});

// Add a request interceptor to include the token
apiClient.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token'); // Replace with your token storage logic
        if (token) {
            config.headers.Authorization = `Bearer ${token}`; // Attach token to Authorization header
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Add a response interceptor to handle errors
// Add a response interceptor to handle errors
apiClient.interceptors.response.use(
    (response) => response, // Pass through successful responses
    (error) => {
        if (error.response) {
            // Handle specific error scenarios
            const status = error.response.status;
            const data = error.response.data;

            // Automatically handle unauthorized errors (401)
            if (status === 401) {
                localStorage.removeItem('token'); // Clear invalid token
                const redirectUrl = window.location.pathname;
                window.location.href = `/login?redirect=${encodeURIComponent(redirectUrl)}`;
            }

            // Return a consistent error format for other cases
            return Promise.reject({
                status,
                data, // The JSON error body
                message: data?.error || error.message, // Extract meaningful error message
            });
        }

        // Handle cases where the server is unreachable or other Axios issues
        return Promise.reject({
            status: null,
            data: null,
            message: error.message || 'An unexpected error occurred',
        });
    }
);

export default apiClient;