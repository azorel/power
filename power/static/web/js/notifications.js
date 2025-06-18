/**
 * PALOS Web Dashboard - Notifications Manager
 * Handles real-time notifications, toasts, and notification panel
 */

class NotificationManager {
    constructor() {
        this.notifications = new Map();
        this.unreadCount = 0;
        this.isOpen = false;
        this.maxToasts = 5;
        this.defaultDuration = 5000; // 5 seconds
        
        this.init();
    }
    
    init() {
        console.log('🔔 Initializing Notification Manager...');
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Setup WebSocket handlers
        this.setupWebSocketHandlers();
        
        // Initialize notification panel
        this.initializePanel();
        
        console.log('✅ Notification Manager initialized');
    }
    
    setupEventListeners() {
        // Notifications button
        const notificationsBtn = document.getElementById('notifications-btn');
        if (notificationsBtn) {
            notificationsBtn.addEventListener('click', () => this.togglePanel());
        }
        
        // Close notifications panel
        const closeBtn = document.getElementById('close-notifications');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.closePanel());
        }
        
        // Click outside to close
        document.addEventListener('click', (e) => {
            const panel = document.getElementById('notifications-panel');
            const btn = document.getElementById('notifications-btn');
            
            if (this.isOpen && panel && !panel.contains(e.target) && !btn.contains(e.target)) {
                this.closePanel();
            }
        });
        
        // Mark as read when clicked
        document.addEventListener('click', (e) => {
            if (e.target.closest('.notification-item:not(.read)')) {
                const notificationId = e.target.closest('.notification-item').dataset.notificationId;
                this.markAsRead(notificationId);
            }
        });
    }
    
    setupWebSocketHandlers() {
        if (window.websocketManager) {
            window.websocketManager.subscribe('notification', (data) => {
                this.handleIncomingNotification(data);
            });
            
            window.websocketManager.subscribe('agent_notification', (data) => {
                this.handleAgentNotification(data);
            });
            
            window.websocketManager.subscribe('system_notification', (data) => {
                this.handleSystemNotification(data);
            });
        }
    }
    
    initializePanel() {
        // Load existing notifications
        this.loadNotifications();
    }
    
    async loadNotifications() {
        try {
            // In a real implementation, this would fetch from API
            // For now, we'll start with empty state
            this.renderNotifications();
        } catch (error) {
            console.error('Error loading notifications:', error);
        }
    }
    
    show(notification) {
        const id = this.generateId();
        const notificationData = {
            id: id,
            title: notification.title || 'Notification',
            message: notification.message || '',
            type: notification.type || 'info', // info, success, warning, error
            timestamp: new Date(),
            read: false,
            persistent: notification.persistent || false,
            actions: notification.actions || []
        };
        
        // Add to notifications map
        this.notifications.set(id, notificationData);
        
        // Update unread count
        this.unreadCount++;
        this.updateBadge();
        
        // Show toast if not persistent
        if (!notificationData.persistent) {
            this.showToast(notificationData);
        }
        
        // Update notification panel
        this.renderNotifications();
        
        return id;
    }
    
    showSuccess(message, title = 'Success') {
        return this.show({
            title: title,
            message: message,
            type: 'success'
        });
    }
    
    showError(message, title = 'Error') {
        return this.show({
            title: title,
            message: message,
            type: 'error',
            persistent: true
        });
    }
    
    showWarning(message, title = 'Warning') {
        return this.show({
            title: title,
            message: message,
            type: 'warning'
        });
    }
    
    showInfo(message, title = 'Info') {
        return this.show({
            title: title,
            message: message,
            type: 'info'
        });
    }
    
    showToast(notification) {
        const toast = this.createToastElement(notification);
        const container = document.getElementById('toast-container');
        
        if (container) {
            // Limit number of toasts
            const existingToasts = container.querySelectorAll('.toast');
            if (existingToasts.length >= this.maxToasts) {
                existingToasts[0].remove();
            }
            
            container.appendChild(toast);
            
            // Animate in
            setTimeout(() => {
                toast.classList.add('show');
            }, 100);
            
            // Auto dismiss if not persistent
            if (!notification.persistent) {
                setTimeout(() => {
                    this.dismissToast(toast);
                }, this.defaultDuration);
            }
        }
    }
    
    createToastElement(notification) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${notification.type}`;
        toast.dataset.notificationId = notification.id;
        
        const iconMap = {
            success: 'check-circle',
            error: 'alert-circle',
            warning: 'alert-triangle',
            info: 'info'
        };
        
        toast.innerHTML = `
            <div class="toast-content">
                <div class="toast-icon">
                    <span class="icon icon-${iconMap[notification.type]}"></span>
                </div>
                <div class="toast-body">
                    <div class="toast-title">${notification.title}</div>
                    <div class="toast-message">${notification.message}</div>
                </div>
                <button class="toast-close">
                    <span class="icon icon-close"></span>
                </button>
            </div>
            <div class="toast-progress"></div>
        `;
        
        // Setup close button
        toast.querySelector('.toast-close').addEventListener('click', () => {
            this.dismissToast(toast);
        });
        
        // Setup progress bar for auto-dismiss
        if (!notification.persistent) {
            const progress = toast.querySelector('.toast-progress');
            progress.style.animationDuration = `${this.defaultDuration}ms`;
        }
        
        return toast;
    }
    
    dismissToast(toast) {
        toast.classList.add('dismissing');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }
    
    togglePanel() {
        if (this.isOpen) {
            this.closePanel();
        } else {
            this.openPanel();
        }
    }
    
    openPanel() {
        const panel = document.getElementById('notifications-panel');
        if (panel) {
            panel.classList.add('open');
            this.isOpen = true;
            
            // Mark visible notifications as read
            this.markVisibleAsRead();
        }
    }
    
    closePanel() {
        const panel = document.getElementById('notifications-panel');
        if (panel) {
            panel.classList.remove('open');
            this.isOpen = false;
        }
    }
    
    renderNotifications() {
        const notificationsList = document.getElementById('notifications-list');
        if (!notificationsList) return;
        
        // Sort notifications by timestamp (newest first)
        const sortedNotifications = Array.from(this.notifications.values())
            .sort((a, b) => b.timestamp - a.timestamp);
        
        if (sortedNotifications.length === 0) {
            notificationsList.innerHTML = `
                <div class="notifications-empty">
                    <span class="icon icon-bell"></span>
                    <p>No notifications</p>
                </div>
            `;
            return;
        }
        
        notificationsList.innerHTML = sortedNotifications
            .map(notification => this.createNotificationElement(notification))
            .join('');
    }
    
    createNotificationElement(notification) {
        const timeAgo = this.formatTimeAgo(notification.timestamp);
        const readClass = notification.read ? 'read' : 'unread';
        
        return `
            <div class="notification-item ${readClass}" data-notification-id="${notification.id}">
                <div class="notification-icon">
                    <span class="icon icon-${this.getNotificationIcon(notification.type)}"></span>
                </div>
                <div class="notification-content">
                    <div class="notification-header">
                        <span class="notification-title">${notification.title}</span>
                        <span class="notification-time">${timeAgo}</span>
                    </div>
                    <div class="notification-body">
                        <p>${notification.message}</p>
                    </div>
                    ${notification.actions.length > 0 ? this.renderNotificationActions(notification.actions) : ''}
                </div>
                <button class="notification-dismiss" data-notification-id="${notification.id}">
                    <span class="icon icon-close"></span>
                </button>
            </div>
        `;
    }
    
    renderNotificationActions(actions) {
        return `
            <div class="notification-actions">
                ${actions.map(action => `
                    <button class="btn btn-sm ${action.style || 'btn-ghost'}" 
                            onclick="${action.handler}">
                        ${action.label}
                    </button>
                `).join('')}
            </div>
        `;
    }
    
    getNotificationIcon(type) {
        const iconMap = {
            success: 'check-circle',
            error: 'alert-circle',
            warning: 'alert-triangle',
            info: 'info',
            agent: 'robot',
            system: 'settings'
        };
        return iconMap[type] || 'bell';
    }
    
    formatTimeAgo(timestamp) {
        const now = new Date();
        const diff = now - timestamp;
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);
        
        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        if (days < 7) return `${days}d ago`;
        return timestamp.toLocaleDateString();
    }
    
    markAsRead(notificationId) {
        const notification = this.notifications.get(notificationId);
        if (notification && !notification.read) {
            notification.read = true;
            this.unreadCount = Math.max(0, this.unreadCount - 1);
            this.updateBadge();
            this.renderNotifications();
        }
    }
    
    markVisibleAsRead() {
        // Mark all unread notifications as read when panel is opened
        let markedCount = 0;
        this.notifications.forEach(notification => {
            if (!notification.read) {
                notification.read = true;
                markedCount++;
            }
        });
        
        if (markedCount > 0) {
            this.unreadCount = Math.max(0, this.unreadCount - markedCount);
            this.updateBadge();
            this.renderNotifications();
        }
    }
    
    dismiss(notificationId) {
        this.notifications.delete(notificationId);
        this.renderNotifications();
        
        // Also dismiss any related toast
        const toast = document.querySelector(`[data-notification-id="${notificationId}"]`);
        if (toast) {
            this.dismissToast(toast);
        }
    }
    
    updateBadge() {
        const badge = document.getElementById('notification-count');
        if (badge) {
            if (this.unreadCount > 0) {
                badge.textContent = this.unreadCount > 99 ? '99+' : this.unreadCount;
                badge.style.display = 'flex';
            } else {
                badge.style.display = 'none';
            }
        }
    }
    
    clear() {
        this.notifications.clear();
        this.unreadCount = 0;
        this.updateBadge();
        this.renderNotifications();
        
        // Clear all toasts
        const container = document.getElementById('toast-container');
        if (container) {
            container.innerHTML = '';
        }
    }
    
    generateId() {
        return 'notification_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    // WebSocket event handlers
    handleIncomingNotification(data) {
        this.show({
            title: data.title,
            message: data.message,
            type: data.type || 'info',
            persistent: data.persistent || false,
            actions: data.actions || []
        });
    }
    
    handleAgentNotification(data) {
        this.show({
            title: `Agent: ${data.agent_name}`,
            message: data.message,
            type: 'agent',
            actions: data.actions || []
        });
    }
    
    handleSystemNotification(data) {
        this.show({
            title: 'System Notification',
            message: data.message,
            type: 'system',
            persistent: data.level === 'error'
        });
    }
    
    // Public API methods
    showAgentUpdate(agentName, message) {
        return this.show({
            title: `${agentName}`,
            message: message,
            type: 'agent'
        });
    }
    
    showTaskComplete(agentName, taskDescription) {
        return this.show({
            title: 'Task Completed',
            message: `${agentName} has completed: ${taskDescription}`,
            type: 'success',
            actions: [
                {
                    label: 'View Details',
                    style: 'btn-primary',
                    handler: `window.agentsManager?.showAgentDetail('${agentName}')`
                }
            ]
        });
    }
    
    showCollaborationUpdate(agents, activity) {
        return this.show({
            title: 'Agent Collaboration',
            message: `${agents.join(', ')} are collaborating on: ${activity}`,
            type: 'info'
        });
    }
    
    showSystemStatus(status, message) {
        const type = status === 'healthy' ? 'success' : status === 'warning' ? 'warning' : 'error';
        return this.show({
            title: 'System Status',
            message: message,
            type: type,
            persistent: type === 'error'
        });
    }
}

// Initialize notification manager when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.notifications = new NotificationManager();
});

// Setup dismiss handlers
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('notification-dismiss') || 
        e.target.closest('.notification-dismiss')) {
        const button = e.target.closest('.notification-dismiss');
        const notificationId = button.dataset.notificationId;
        if (window.notifications && notificationId) {
            window.notifications.dismiss(notificationId);
        }
    }
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NotificationManager;
}