/**
 * API Service - Axios Singleton Pattern
 *
 * Centralized HTTP client configuration with interceptors for
 * authentication, error handling, and request/response transformation.
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';

class APIService {
  private static instance: APIService;
  private axiosInstance: AxiosInstance;
  private baseURL: string;

  private constructor() {
    this.baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    this.axiosInstance = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  /**
   * Get singleton instance of APIService
   */
  public static getInstance(): APIService {
    if (!APIService.instance) {
      APIService.instance = new APIService();
    }
    return APIService.instance;
  }

  /**
   * Setup request and response interceptors
   */
  private setupInterceptors(): void {
    // Request interceptor - Add auth token
    this.axiosInstance.interceptors.request.use(
      (config) => {
        // Get token from localStorage
        const token = typeof window !== 'undefined'
          ? localStorage.getItem('auth_token')
          : null;

        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor - Handle errors globally
    this.axiosInstance.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response) {
          // Server responded with error status
          const status = error.response.status;

          switch (status) {
            case 401:
              // Unauthorized - clear token and redirect to login
              if (typeof window !== 'undefined') {
                localStorage.removeItem('auth_token');
                window.location.href = '/login';
              }
              break;

            case 403:
              // Forbidden
              console.error('Access forbidden:', error.response.data);
              break;

            case 404:
              console.error('Resource not found:', error.response.data);
              break;

            case 500:
              console.error('Server error:', error.response.data);
              break;

            default:
              console.error('API Error:', error.response.data);
          }
        } else if (error.request) {
          // Request made but no response received
          console.error('Network error - no response received');
        } else {
          // Error in request configuration
          console.error('Request configuration error:', error.message);
        }

        return Promise.reject(error);
      }
    );
  }

  /**
   * GET request
   */
  public async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.axiosInstance.get(url, config);
    return response.data;
  }

  /**
   * POST request
   */
  public async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.axiosInstance.post(url, data, config);
    return response.data;
  }

  /**
   * PUT request
   */
  public async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.axiosInstance.put(url, data, config);
    return response.data;
  }

  /**
   * PATCH request
   */
  public async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.axiosInstance.patch(url, data, config);
    return response.data;
  }

  /**
   * DELETE request
   */
  public async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.axiosInstance.delete(url, config);
    return response.data;
  }

  /**
   * Set authentication token
   */
  public setAuthToken(token: string): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', token);
    }
  }

  /**
   * Clear authentication token
   */
  public clearAuthToken(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
    }
  }

  /**
   * Get current base URL
   */
  public getBaseURL(): string {
    return this.baseURL;
  }
}

// Export singleton instance
export const api = APIService.getInstance();
export default api;
