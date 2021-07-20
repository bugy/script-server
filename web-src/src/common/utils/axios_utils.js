import axios from 'axios'

export const axiosInstance = axios.create({
    xsrfCookieName: '_xsrf',
    xsrfHeaderName: 'X-XSRFToken',
    withCredentials: true,
    headers: {'X-Requested-With': 'XMLHttpRequest'}
});

