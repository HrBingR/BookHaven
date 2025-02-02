import axios from 'axios';

const apiClient = axios.create({
    baseURL: `${window.location.origin}`,
    withCredentials: true,
});

apiClient.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response) {
            const status = error.response.status;
            const data = error.response.data;

            if (status === 401) {
                localStorage.removeItem('token');
                const redirectUrl = window.location.pathname;
                window.location.href = `/login?redirect=${encodeURIComponent(redirectUrl)}`;
            }

            return Promise.reject({
                status,
                data,
                message: data?.error || error.message,
            });
        }

        return Promise.reject({
            status: null,
            data: null,
            message: error.message || 'An unexpected error occurred',
        });
    }
);

export default apiClient;