/**
 * PALOS Web Dashboard - WebSocket Client
 * Handles real-time communication with the FastAPI backend
 */

class WebSocketManager {
    constructor(token) {
        this.token = token;
        this.websocket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.heartbeatInterval = null;
        this.listeners = new Map();
        
        // Get WebSocket URL
        this.wsURL = this.getWebSocketURL();
    }
    
    getWebSocketURL() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const hostname = window.location.hostname;
        const port = window.location.port || (window.location.protocol === 'https:' ? '443' : '80');
        
        // Use same port as current page, or default to 8000 for development
        const wsPort = port === '80' || port === '443' ? port : '8000';
        
        return `${protocol}//${hostname}:${wsPort}/ws/connect?token=${this.token}`;
    }
    
    async connect() {
        if (this.isConnected || !this.token) {
            return;
        }
        
        try {
            console.log('🔌 Connecting to WebSocket...');
            
            this.websocket = new WebSocket(this.wsURL);
            
            this.websocket.onopen = this.handleOpen.bind(this);
            this.websocket.onmessage = this.handleMessage.bind(this);
            this.websocket.onclose = this.handleClose.bind(this);
            this.websocket.onerror = this.handleError.bind(this);
            
        } catch (error) {
            console.error('❌ Failed to create WebSocket connection:', error);
            this.handleReconnect();
        }
    }
    
    handleOpen(event) {
        console.log('✅ WebSocket connected successfully');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        
        // Start heartbeat
        this.startHeartbeat();
        
        // Notify listeners
        this.emit('connected', { event });
        
        // Show connection status
        if (window.app && window.app.showToast) {
            window.app.showToast('Real-time updates connected', 'success', 3000);
        }
    }
    
    handleMessage(event) {
        try {
            const message = JSON.parse(event.data);
            console.log('📨 WebSocket message received:', message);
            
            // Handle different message types
            switch (message.type) {
                case 'notification':
                    this.handleNotification(message);
                    break;
                case 'update':
                    this.handleUpdate(message);
                    break;
                case 'heartbeat':
                    this.handleHeartbeat(message);
                    break;
                case 'error':
                    this.handleServerError(message);
                    break;
                default:
                    this.emit('message', message);
            }
            
        } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
        }
    }
    
    handleClose(event) {
        console.log('🔌 WebSocket connection closed:', event.code, event.reason);
        this.isConnected = false;
        
        // Stop heartbeat
        this.stopHeartbeat();
        
        // Notify listeners
        this.emit('disconnected', { event });
        
        // Attempt to reconnect if not a clean close
        if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.handleReconnect();
        } else if (event.code === 1008) {
            // Authentication failed
            console.warn('WebSocket authentication failed');
            if (window.app && window.app.logout) {
                window.app.logout();
            }
        }
    }
    
    handleError(error) {
        console.error('❌ WebSocket error:', error);
        this.emit('error', { error });
    }
    
    handleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            if (window.app && window.app.showToast) {
                window.app.showToast('Real-time connection failed. Please refresh the page.', 'error');
            }
            return;
        }
        
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1); // Exponential backoff
        
        console.log(`⏳ Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        
        setTimeout(() => {
            this.connect();
        }, delay);
    }
    
    handleNotification(message) {
        console.log('🔔 Notification received:', message.payload);
        
        // Update notification badge
        if (window.app && window.app.updateNotificationBadge) {
            // Fetch updated notification count
            this.fetchNotificationCount();
        }
        
        // Show toast notification
        if (message.payload && message.payload.title) {
            const { title, message: text, type = 'info' } = message.payload;
            if (window.app && window.app.showToast) {
                window.app.showToast(`${title}: ${text}`, type);
            }
        }
        
        // Emit to specific listeners
        this.emit('notification', message.payload);
    }
    
    handleUpdate(message) {
        console.log('🔄 Update received:', message.payload);
        
        const { type, data } = message.payload;
        
        switch (type) {
            case 'dashboard':
                this.handleDashboardUpdate(data);
                break;
            case 'tasks':
                this.handleTasksUpdate(data);
                break;
            case 'calendar':
                this.handleCalendarUpdate(data);
                break;
            case 'health':
                this.handleHealthUpdate(data);
                break;
            case 'finance':
                this.handleFinanceUpdate(data);
                break;
            case 'social':
                this.handleSocialUpdate(data);
                break;
            case 'agents':
                this.handleAgentsUpdate(data);
                break;
            default:
                this.emit('update', message.payload);
        }
    }
    
    handleDashboardUpdate(data) {
        // Update dashboard stats in real-time
        if (window.app && window.app.currentPage === 'dashboard') {
            if (data.stats) {
                window.app.updateDashboardStats(data.stats);
            }
        }
        
        this.emit('dashboard-update', data);
    }
    
    handleTasksUpdate(data) {
        // Refresh tasks list
        if (window.tasksManager && window.tasksManager.refreshTasks) {
            window.tasksManager.refreshTasks();
        }
        
        this.emit('tasks-update', data);
    }
    
    handleCalendarUpdate(data) {
        // Refresh calendar
        if (window.calendarManager && window.calendarManager.refreshCalendar) {
            window.calendarManager.refreshCalendar();
        }
        
        this.emit('calendar-update', data);
    }
    
    handleHealthUpdate(data) {
        // Refresh health metrics
        if (window.healthManager && window.healthManager.refreshHealth) {
            window.healthManager.refreshHealth();
        }
        
        this.emit('health-update', data);
    }
    
    handleFinanceUpdate(data) {
        // Refresh financial data
        if (window.financeManager && window.financeManager.refreshFinance) {
            window.financeManager.refreshFinance();
        }
        
        this.emit('finance-update', data);
    }
    
    handleSocialUpdate(data) {
        // Refresh social media data
        if (window.socialManager && window.socialManager.refreshSocial) {
            window.socialManager.refreshSocial();
        }
        
        this.emit('social-update', data);
    }
    
    handleAgentsUpdate(data) {
        // Refresh agents status
        if (window.agentsManager && window.agentsManager.refreshAgents) {
            window.agentsManager.refreshAgents();
        }
        
        this.emit('agents-update', data);
    }
    
    handleHeartbeat(message) {
        // Respond to heartbeat
        this.send({
            type: 'heartbeat_response',
            timestamp: Date.now()
        });
    }
    
    handleServerError(message) {
        console.error('Server error received:', message.payload);
        
        if (window.app && window.app.showToast) {
            window.app.showToast(message.payload.error || 'Server error occurred', 'error');
        }
        
        this.emit('server-error', message.payload);
    }
    
    send(message) {
        if (this.isConnected && this.websocket) {
            try {
                this.websocket.send(JSON.stringify(message));
                console.log('📤 WebSocket message sent:', message);
            } catch (error) {
                console.error('Failed to send WebSocket message:', error);
            }
        } else {
            console.warn('Cannot send message - WebSocket not connected');
        }
    }
    
    startHeartbeat() {
        this.heartbeatInterval = setInterval(() => {
            this.send({
                type: 'heartbeat',
                timestamp: Date.now()
            });
        }, 30000); // Send heartbeat every 30 seconds
    }
    
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }
    
    async fetchNotificationCount() {
        try {
            const response = await window.API.getNotifications(1);
            if (response.success && response.data) {
                const unreadCount = response.data.filter(n => !n.read).length;
                if (window.app && window.app.updateNotificationBadge) {
                    window.app.updateNotificationBadge(unreadCount);
                }
            }
        } catch (error) {
            console.error('Failed to fetch notification count:', error);
        }
    }
    
    // Event listener management
    on(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
    }
    
    off(event, callback) {
        if (this.listeners.has(event)) {
            const callbacks = this.listeners.get(event);
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
        }
    }
    
    emit(event, data) {
        if (this.listeners.has(event)) {
            this.listeners.get(event).forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in WebSocket event listener for ${event}:`, error);
                }
            });
        }
    }
    
    // Broadcast message to other connected clients (admin only)
    broadcast(message, targetUserId = null) {
        this.send({
            type: 'broadcast',
            payload: message,
            target_user_id: targetUserId
        });
    }
    
    // Subscribe to specific update types
    subscribe(updateType) {
        this.send({
            type: 'subscribe',
            payload: { update_type: updateType }
        });
    }
    
    unsubscribe(updateType) {
        this.send({
            type: 'unsubscribe',
            payload: { update_type: updateType }
        });
    }
    
    disconnect() {
        if (this.websocket) {
            console.log('🔌 Disconnecting WebSocket...');
            this.stopHeartbeat();
            this.websocket.close(1000, 'Client disconnect');
            this.websocket = null;
            this.isConnected = false;
        }
    }
    
    // Connection status
    getConnectionStatus() {
        return {
            connected: this.isConnected,
            reconnectAttempts: this.reconnectAttempts,
            maxReconnectAttempts: this.maxReconnectAttempts
        };
    }
    
    // Update token (for token refresh scenarios)
    updateToken(newToken) {
        this.token = newToken;
        this.wsURL = this.getWebSocketURL();
        
        // Reconnect with new token if currently connected
        if (this.isConnected) {
            this.disconnect();
            setTimeout(() => this.connect(), 1000);
        }
    }
}

// Helper function to create connection status indicator
function createConnectionIndicator() {
    const indicator = document.createElement('div');
    indicator.id = 'ws-status-indicator';
    indicator.style.cssText = `
        position: fixed;
        top: 70px;
        right: 20px;
        padding: 8px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 500;
        z-index: 1000;
        display: none;
        align-items: center;
        gap: 6px;
        transition: all 0.3s ease;
    `;
    
    document.body.appendChild(indicator);
    
    return {
        show: (message, type = 'info') => {
            const colors = {
                info: 'background: #3B82F6; color: white;',
                success: 'background: #10B981; color: white;',
                warning: 'background: #F59E0B; color: white;',
                error: 'background: #EF4444; color: white;'
            };
            
            indicator.style.cssText += colors[type];
            indicator.innerHTML = `
                <span style="width: 8px; height: 8px; border-radius: 50%; background: currentColor; display: inline-block;"></span>
                ${message}
            `;
            indicator.style.display = 'flex';
            
            setTimeout(() => {
                indicator.style.display = 'none';
            }, 3000);
        },
        
        hide: () => {
            indicator.style.display = 'none';
        }
    };
}

// Export for other modules
window.WebSocketManager = WebSocketManager;