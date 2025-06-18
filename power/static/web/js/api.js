/**
 * PALOS Web Dashboard - API Client
 * Handles all communication with the FastAPI backend
 */

class APIClient {
    constructor() {
        this.baseURL = this.getBaseURL();
        this.defaultHeaders = {
            'Content-Type': 'application/json',
        };
        this.requestQueue = [];
        this.isOnline = navigator.onLine;
        
        // Initialize offline detection
        this.initOfflineDetection();
    }
    
    getBaseURL() {
        // Auto-detect base URL based on current location
        const protocol = window.location.protocol;
        const hostname = window.location.hostname;
        const port = window.location.port || (protocol === 'https:' ? '443' : '80');
        
        // Use same port as current page, or default to 8000 for development
        const apiPort = port === '80' || port === '443' ? port : '8000';
        
        return `${protocol}//${hostname}:${apiPort}/api`;
    }
    
    initOfflineDetection() {
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.processRequestQueue();
        });
        
        window.addEventListener('offline', () => {
            this.isOnline = false;
        });
    }
    
    getAuthHeaders() {
        const token = localStorage.getItem('palos_access_token');
        if (token) {
            return {
                ...this.defaultHeaders,
                Authorization: `Bearer ${token}`
            };
        }
        return this.defaultHeaders;
    }
    
    async request(method, endpoint, data = null, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const headers = {
            ...this.getAuthHeaders(),
            ...options.headers
        };
        
        const config = {
            method: method.toUpperCase(),
            headers,
            ...options
        };
        
        if (data && ['POST', 'PUT', 'PATCH'].includes(config.method)) {
            config.body = JSON.stringify(data);
        }
        
        // If offline, queue the request (for non-critical operations)
        if (!this.isOnline && !options.skipOfflineQueue) {
            return this.queueRequest(config, url);
        }
        
        try {
            const response = await fetch(url, config);
            return await this.handleResponse(response);
        } catch (error) {
            return this.handleError(error, config, url);
        }
    }
    
    async handleResponse(response) {
        let data;
        
        // Handle different content types
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            data = await response.json();
        } else {
            data = await response.text();
        }
        
        if (response.ok) {
            return {
                success: true,
                data: data.data || data,
                message: data.message,
                status: response.status
            };
        } else {
            // Handle specific HTTP errors
            if (response.status === 401) {
                this.handleUnauthorized();
            }
            
            throw new Error(data.error || data.detail || `HTTP ${response.status}: ${response.statusText}`);
        }
    }
    
    handleError(error, config, url) {
        console.error('API Request failed:', error);
        
        // Network error - might be offline
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            if (!this.isOnline) {
                return this.queueRequest(config, url);
            }
        }
        
        return {
            success: false,
            error: error.message,
            status: 0
        };
    }
    
    handleUnauthorized() {
        console.warn('Authentication failed - clearing tokens');
        localStorage.removeItem('palos_access_token');
        localStorage.removeItem('palos_refresh_token');
        
        // Notify app to show login
        if (window.app && window.app.logout) {
            window.app.logout();
        } else {
            window.location.reload();
        }
    }
    
    queueRequest(config, url) {
        console.log('Queueing request for when online:', url);
        
        const queuedRequest = {
            config,
            url,
            timestamp: Date.now(),
            id: Math.random().toString(36).substr(2, 9)
        };
        
        this.requestQueue.push(queuedRequest);
        
        // Store in localStorage for persistence
        this.saveRequestQueue();
        
        return {
            success: false,
            error: 'Request queued - you are offline',
            queued: true,
            queueId: queuedRequest.id
        };
    }
    
    async processRequestQueue() {
        console.log('Processing queued requests...');
        
        const queue = [...this.requestQueue];
        this.requestQueue = [];
        
        for (const queuedRequest of queue) {
            try {
                const response = await fetch(queuedRequest.url, queuedRequest.config);
                await this.handleResponse(response);
                console.log('Processed queued request:', queuedRequest.url);
            } catch (error) {
                console.error('Failed to process queued request:', error);
                // Re-queue if still failing
                this.requestQueue.push(queuedRequest);
            }
        }
        
        this.saveRequestQueue();
    }
    
    saveRequestQueue() {
        try {
            localStorage.setItem('palos_request_queue', JSON.stringify(this.requestQueue));
        } catch (error) {
            console.error('Failed to save request queue:', error);
        }
    }
    
    loadRequestQueue() {
        try {
            const saved = localStorage.getItem('palos_request_queue');
            if (saved) {
                this.requestQueue = JSON.parse(saved);
            }
        } catch (error) {
            console.error('Failed to load request queue:', error);
            this.requestQueue = [];
        }
    }
    
    // HTTP Methods
    async get(endpoint, options = {}) {
        return this.request('GET', endpoint, null, options);
    }
    
    async post(endpoint, data, options = {}) {
        return this.request('POST', endpoint, data, options);
    }
    
    async put(endpoint, data, options = {}) {
        return this.request('PUT', endpoint, data, options);
    }
    
    async patch(endpoint, data, options = {}) {
        return this.request('PATCH', endpoint, data, options);
    }
    
    async delete(endpoint, options = {}) {
        return this.request('DELETE', endpoint, null, options);
    }
    
    // Authentication specific methods
    async login(credentials) {
        return this.post('/auth/login', credentials, { skipOfflineQueue: true });
    }
    
    async logout() {
        return this.post('/auth/logout', {}, { skipOfflineQueue: true });
    }
    
    async refreshToken() {
        const refreshToken = localStorage.getItem('palos_refresh_token');
        if (!refreshToken) {
            throw new Error('No refresh token available');
        }
        
        return this.post('/auth/refresh', { refresh_token: refreshToken }, { skipOfflineQueue: true });
    }
    
    // File upload method
    async uploadFile(endpoint, file, additionalData = {}) {
        const formData = new FormData();
        formData.append('file', file);
        
        // Add additional form data
        Object.keys(additionalData).forEach(key => {
            formData.append(key, additionalData[key]);
        });
        
        const headers = { ...this.getAuthHeaders() };
        delete headers['Content-Type']; // Let browser set it for multipart
        
        return this.request('POST', endpoint, null, {
            headers,
            body: formData
        });
    }
    
    // Dashboard API methods
    async getDashboardSummary() {
        return this.get('/dashboard/summary');
    }
    
    async getDashboardStats() {
        return this.get('/dashboard/stats');
    }
    
    async getQuickActions() {
        return this.get('/dashboard/quick-actions');
    }
    
    async getNotifications(limit = 20) {
        return this.get(`/dashboard/notifications?limit=${limit}`);
    }
    
    // Calendar API methods
    async getCalendarEvents(startDate, endDate) {
        const params = new URLSearchParams();
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);
        
        return this.get(`/calendar/events?${params.toString()}`);
    }
    
    async createCalendarEvent(eventData) {
        return this.post('/calendar/events', eventData);
    }
    
    async updateCalendarEvent(eventId, eventData) {
        return this.put(`/calendar/events/${eventId}`, eventData);
    }
    
    async deleteCalendarEvent(eventId) {
        return this.delete(`/calendar/events/${eventId}`);
    }
    
    // Tasks API methods
    async getTasks(filter = {}) {
        const params = new URLSearchParams();
        Object.keys(filter).forEach(key => {
            if (filter[key] !== undefined && filter[key] !== null) {
                params.append(key, filter[key]);
            }
        });
        
        return this.get(`/tasks?${params.toString()}`);
    }
    
    async createTask(taskData) {
        return this.post('/tasks', taskData);
    }
    
    async updateTask(taskId, taskData) {
        return this.put(`/tasks/${taskId}`, taskData);
    }
    
    async deleteTask(taskId) {
        return this.delete(`/tasks/${taskId}`);
    }
    
    // Health API methods
    async getHealthMetrics(metricType = null, days = 30) {
        const params = new URLSearchParams();
        if (metricType) params.append('metric_type', metricType);
        params.append('days', days.toString());
        
        return this.get(`/health/metrics?${params.toString()}`);
    }
    
    async createHealthMetric(metricData) {
        return this.post('/health/metrics', metricData);
    }
    
    async getHealthSummary() {
        return this.get('/health/summary');
    }
    
    // Finance API methods
    async getFinancialSummary() {
        return this.get('/finance/summary');
    }
    
    async getTransactions(filter = {}) {
        const params = new URLSearchParams();
        Object.keys(filter).forEach(key => {
            if (filter[key] !== undefined && filter[key] !== null) {
                params.append(key, filter[key]);
            }
        });
        
        return this.get(`/finance/transactions?${params.toString()}`);
    }
    
    async createTransaction(transactionData) {
        return this.post('/finance/transactions', transactionData);
    }
    
    async getAccounts() {
        return this.get('/finance/accounts');
    }
    
    // Social Media API methods
    async getSocialAccounts() {
        return this.get('/social/accounts');
    }
    
    async getSocialPosts(platform = null, limit = 20) {
        const params = new URLSearchParams();
        if (platform) params.append('platform', platform);
        params.append('limit', limit.toString());
        
        return this.get(`/social/posts?${params.toString()}`);
    }
    
    async createSocialPost(postData) {
        return this.post('/social/posts', postData);
    }
    
    async getSocialSummary() {
        return this.get('/social/summary');
    }
    
    // Agents API methods
    async getAgents() {
        return this.get('/agents');
    }
    
    async getAgentStatus(agentId) {
        return this.get(`/agents/${agentId}/status`);
    }
    
    async updateAgentConfig(agentId, config) {
        return this.put(`/agents/${agentId}/config`, config);
    }
    
    async startAgent(agentId) {
        return this.post(`/agents/${agentId}/start`);
    }
    
    async stopAgent(agentId) {
        return this.post(`/agents/${agentId}/stop`);
    }
    
    // Cache management
    clearCache() {
        // Clear any cached API responses
        if ('caches' in window) {
            caches.delete('palos-api-cache');
        }
        
        // Clear queued requests
        this.requestQueue = [];
        localStorage.removeItem('palos_request_queue');
    }
    
    // Rate limiting helpers
    async withRetry(apiCall, maxRetries = 3, delay = 1000) {
        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                const result = await apiCall();
                if (result.success) {
                    return result;
                }
                
                // If not successful but not a network error, don't retry
                if (result.status >= 400 && result.status < 500) {
                    return result;
                }
                
                throw new Error(result.error || 'API call failed');
            } catch (error) {
                if (attempt === maxRetries) {
                    throw error;
                }
                
                console.warn(`API call attempt ${attempt} failed, retrying in ${delay}ms...`, error);
                await this.sleep(delay * attempt); // Exponential backoff
            }
        }
    }
    
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Create global API instance
window.API = new APIClient();

// Load any queued requests on startup
document.addEventListener('DOMContentLoaded', () => {
    window.API.loadRequestQueue();
});

// Export for other modules
window.APIClient = APIClient;