import axios, { type AxiosInstance, type AxiosResponse } from 'axios';
import type { ApiResponse, ApiError } from '../types';

// Create axios instance with default config
const api: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token refresh and errors
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(
            `${import.meta.env.VITE_API_URL || 'http://localhost:8000/api'}/auth/token/refresh/`,
            { refresh: refreshToken }
          );

          const { access } = response.data;
          localStorage.setItem('access_token', access);

          // Retry the original request with new token
          originalRequest.headers.Authorization = `Bearer ${access}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
      }
    }

    // Handle other errors
    if (error.response) {
      const apiError: ApiError = {
        message: error.response.data?.message || error.response.data?.detail || 'An error occurred',
        errors: error.response.data?.errors,
        status: error.response.status,
      };
      return Promise.reject(apiError);
    }

    return Promise.reject(error);
  }
);

// API methods
export const apiClient = {
  get: <T>(url: string, params?: any): Promise<AxiosResponse<T>> => {
    return api.get(url, { params });
  },

  post: <T>(url: string, data?: any): Promise<AxiosResponse<T>> => {
    return api.post(url, data);
  },

  put: <T>(url: string, data?: any): Promise<AxiosResponse<T>> => {
    return api.put(url, data);
  },

  patch: <T>(url: string, data?: any): Promise<AxiosResponse<T>> => {
    return api.patch(url, data);
  },

  delete: <T>(url: string): Promise<AxiosResponse<T>> => {
    return api.delete(url);
  },
};

// Auth API
export const authApi = {
  login: (credentials: { username: string; password: string }) => {
    return api.post('/auth/login/', credentials);
  },

  register: (userData: any) => {
    return api.post('/auth/register/', userData);
  },

  logout: () => {
    return api.post('/auth/logout/');
  },

  refreshToken: (refreshToken: string) => {
    return api.post('/auth/token/refresh/', { refresh: refreshToken });
  },

  getProfile: () => {
    return api.get('/auth/profile/');
  },
};

// Members API
export const membersApi = {
  getMembers: (params?: any) => {
    return api.get('/members/', { params });
  },

  getMember: (id: number) => {
    return api.get(`/members/${id}/`);
  },

  createMember: (memberData: any) => {
    return api.post('/members/', memberData);
  },

  updateMember: (id: number, memberData: any) => {
    return api.put(`/members/${id}/`, memberData);
  },

  deleteMember: (id: number) => {
    return api.delete(`/members/${id}/`);
  },
};

// Groups API
export const groupsApi = {
  getGroups: (params?: any) => {
    return api.get('/groups/', { params });
  },

  getGroup: (id: number) => {
    return api.get(`/groups/${id}/`);
  },

  createGroup: (groupData: any) => {
    return api.post('/groups/', groupData);
  },

  updateGroup: (id: number, groupData: any) => {
    return api.put(`/groups/${id}/`, groupData);
  },

  deleteGroup: (id: number) => {
    return api.delete(`/groups/${id}/`);
  },
};

// Loans API
export const loansApi = {
  getLoans: (params?: any) => {
    return api.get('/loans/', { params });
  },

  getLoan: (id: number) => {
    return api.get(`/loans/${id}/`);
  },

  createLoan: (loanData: any) => {
    return api.post('/loans/', loanData);
  },

  updateLoan: (id: number, loanData: any) => {
    return api.put(`/loans/${id}/`, loanData);
  },

  disburseLoan: (id: number, disbursementData: any) => {
    return api.post(`/loans/${id}/disburse/`, disbursementData);
  },
};

// Transactions API
export const transactionsApi = {
  getTransactions: (params?: any) => {
    return api.get('/transactions/', { params });
  },

  createCashIn: (transactionData: any) => {
    return api.post('/transactions/cash-in/', transactionData);
  },

  createCashOut: (transactionData: any) => {
    return api.post('/transactions/cash-out/', transactionData);
  },
};

// Dividends API
export const dividendsApi = {
  getDividendPeriods: () => {
    return api.get('/dividends/periods/');
  },

  getDividendPeriod: (id: number) => {
    return api.get(`/dividends/periods/${id}/`);
  },

  calculateDividends: (periodId: number) => {
    return api.post(`/dividends/periods/${periodId}/calculate/`);
  },

  getMemberDividends: (periodId: number) => {
    return api.get(`/dividends/periods/${periodId}/members/`);
  },

  toggleFieldOfficerVisibility: (dividendId: number, visible: boolean) => {
    return api.patch(`/dividends/members/${dividendId}/field-officer-visibility/`, { visible });
  },

  toggleMemberVisibility: (dividendId: number, visible: boolean) => {
    return api.patch(`/dividends/members/${dividendId}/member-visibility/`, { visible });
  },
};

// Dashboard API
export const dashboardApi = {
  getOverview: () => {
    return api.get('/dashboard/overview/');
  },

  getLoanOverview: () => {
    return api.get('/dashboard/loan-overview/');
  },

  getSavingsOverview: () => {
    return api.get('/dashboard/savings-overview/');
  },
};

export default api;
