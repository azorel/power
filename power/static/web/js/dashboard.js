/**
 * PALOS Web Dashboard - Dashboard Manager
 * Handles the main dashboard functionality and real-time updates
 */

class DashboardManager {
    constructor() {
        this.refreshInterval = null;
        this.autoRefreshEnabled = true;
        this.refreshRate = 30000; // 30 seconds
        this.lastUpdate = null;
        this.widgets = new Map();
        this.isVisible = false;
        
        this.init();
    }
    
    init() {
        console.log('🏠 Initializing Dashboard Manager...');
        
        // Setup dashboard widgets
        this.setupWidgets();
        
        // Setup auto-refresh
        this.setupAutoRefresh();
        
        // Setup real-time updates
        this.setupRealTimeUpdates();
        
        // Setup visibility handling
        this.setupVisibilityHandling();
        
        // Setup event listeners
        this.setupEventListeners();
        
        console.log('✅ Dashboard Manager initialized');
    }
    
    setupWidgets() {
        // Register dashboard widgets
        this.widgets.set('stats', new StatsWidget());
        this.widgets.set('quick-actions', new QuickActionsWidget());
        this.widgets.set('recent-activity', new RecentActivityWidget());
        this.widgets.set('notifications', new NotificationsWidget());
        
        // Initialize all widgets
        this.widgets.forEach((widget, id) => {
            widget.init();
        });
    }
    
    setupAutoRefresh() {
        if (this.autoRefreshEnabled) {
            this.refreshInterval = setInterval(() => {
                if (this.isVisible && document.visibilityState === 'visible') {
                    this.refreshDashboard();
                }
            }, this.refreshRate);
        }
    }
    
    setupRealTimeUpdates() {
        // Listen for WebSocket updates
        if (window.websocketManager) {
            window.websocketManager.on('dashboard-update', (data) => {
                this.handleRealTimeUpdate(data);
            });
            
            window.websocketManager.on('notification', (data) => {
                this.handleNotificationUpdate(data);
            });
        }
    }
    
    setupVisibilityHandling() {
        // Page visibility API
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible' && this.isVisible) {
                // Refresh when page becomes visible
                this.refreshDashboard();
            }
        });
        
        // Intersection Observer for dashboard visibility
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.target.id === 'dashboard-page') {
                    this.isVisible = entry.isIntersecting;
                    if (this.isVisible) {
                        this.refreshDashboard();
                    }
                }
            });
        });
        
        const dashboardPage = document.getElementById('dashboard-page');
        if (dashboardPage) {
            observer.observe(dashboardPage);
        }
    }
    
    setupEventListeners() {
        // Refresh button
        const refreshBtn = document.getElementById('refresh-dashboard');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refreshDashboard(true);
            });
        }
        
        // Auto-refresh toggle
        const autoRefreshToggle = document.getElementById('auto-refresh-toggle');
        if (autoRefreshToggle) {
            autoRefreshToggle.addEventListener('change', (e) => {
                this.toggleAutoRefresh(e.target.checked);
            });
        }
        
        // Widget settings
        document.addEventListener('click', (e) => {
            if (e.target.closest('[data-widget-setting]')) {
                const widget = e.target.closest('[data-widget]');
                const setting = e.target.getAttribute('data-widget-setting');
                this.handleWidgetSetting(widget, setting);
            }
        });
    }
    
    async refreshDashboard(forceRefresh = false) {
        console.log('🔄 Refreshing dashboard...');
        
        try {
            // Show loading indicator
            this.showLoadingIndicator();
            
            // Refresh all widgets
            const refreshPromises = Array.from(this.widgets.values()).map(widget => 
                widget.refresh(forceRefresh)
            );
            
            await Promise.all(refreshPromises);
            
            this.lastUpdate = new Date();
            this.updateLastRefreshTime();
            
            console.log('✅ Dashboard refreshed successfully');
            
        } catch (error) {
            console.error('❌ Dashboard refresh failed:', error);
            this.showError('Failed to refresh dashboard');
        } finally {
            this.hideLoadingIndicator();
        }
    }
    
    handleRealTimeUpdate(data) {
        console.log('📊 Real-time dashboard update received:', data);
        
        // Update specific widgets based on data type
        if (data.stats) {
            const statsWidget = this.widgets.get('stats');
            if (statsWidget) {
                statsWidget.updateData(data.stats);
            }
        }
        
        if (data.activity) {
            const activityWidget = this.widgets.get('recent-activity');
            if (activityWidget) {
                activityWidget.addActivity(data.activity);
            }
        }
        
        // Show update notification
        this.showUpdateNotification();
    }
    
    handleNotificationUpdate(data) {
        console.log('🔔 Dashboard notification update:', data);
        
        const notificationsWidget = this.widgets.get('notifications');
        if (notificationsWidget) {
            notificationsWidget.addNotification(data);
        }
        
        // Update notification badge
        this.updateNotificationBadge();
    }
    
    showLoadingIndicator() {
        const indicator = document.querySelector('.dashboard-loading');
        if (indicator) {
            indicator.style.display = 'block';
        }
        
        // Add loading class to refresh button
        const refreshBtn = document.getElementById('refresh-dashboard');
        if (refreshBtn) {
            refreshBtn.classList.add('loading');
            refreshBtn.disabled = true;
        }
    }
    
    hideLoadingIndicator() {
        const indicator = document.querySelector('.dashboard-loading');
        if (indicator) {
            indicator.style.display = 'none';
        }
        
        // Remove loading class from refresh button
        const refreshBtn = document.getElementById('refresh-dashboard');
        if (refreshBtn) {
            refreshBtn.classList.remove('loading');
            refreshBtn.disabled = false;
        }
    }
    
    showUpdateNotification() {
        const notification = document.createElement('div');
        notification.className = 'dashboard-update-notification';
        notification.innerHTML = `
            <span class="icon">🔄</span>
            <span>Dashboard updated</span>
        `;
        
        const dashboard = document.getElementById('dashboard-page');
        if (dashboard) {
            dashboard.appendChild(notification);
            
            setTimeout(() => {
                notification.classList.add('show');
            }, 100);
            
            setTimeout(() => {
                notification.classList.remove('show');
                setTimeout(() => notification.remove(), 300);
            }, 2000);
        }
    }
    
    updateLastRefreshTime() {
        const timeElement = document.querySelector('.last-refresh-time');
        if (timeElement && this.lastUpdate) {
            timeElement.textContent = `Last updated: ${formatTime(this.lastUpdate)}`;
        }
    }
    
    updateNotificationBadge() {
        // This will be handled by the main app notification system
        if (window.app && window.app.updateNotificationBadge) {
            // Trigger badge update
            setTimeout(() => {
                API.get('/dashboard/notifications?limit=1').then(response => {
                    if (response.success) {
                        const unreadCount = response.data.filter(n => !n.read).length;
                        window.app.updateNotificationBadge(unreadCount);
                    }
                });
            }, 500);
        }
    }
    
    toggleAutoRefresh(enabled) {
        this.autoRefreshEnabled = enabled;
        
        if (enabled) {
            this.setupAutoRefresh();
        } else {
            if (this.refreshInterval) {
                clearInterval(this.refreshInterval);
                this.refreshInterval = null;
            }
        }
        
        // Save preference
        localStorage.setItem('palos_dashboard_auto_refresh', enabled.toString());
    }
    
    handleWidgetSetting(widget, setting) {
        const widgetId = widget.getAttribute('data-widget');
        const widgetInstance = this.widgets.get(widgetId);
        
        if (widgetInstance && widgetInstance.handleSetting) {
            widgetInstance.handleSetting(setting);
        }
    }
    
    showError(message) {
        if (window.showToast) {
            window.showToast(message, 'error');
        }
    }
    
    destroy() {
        // Clean up intervals
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        
        // Destroy all widgets
        this.widgets.forEach(widget => {
            if (widget.destroy) {
                widget.destroy();
            }
        });
        
        console.log('🗑️ Dashboard Manager destroyed');
    }
}

// Base Widget Class
class BaseWidget {
    constructor(id, element) {
        this.id = id;
        this.element = element;
        this.data = null;
        this.lastUpdate = null;
        this.isLoading = false;
    }
    
    init() {
        console.log(`📊 Initializing widget: ${this.id}`);
    }
    
    async refresh(forceRefresh = false) {
        if (this.isLoading && !forceRefresh) return;
        
        this.isLoading = true;
        this.showLoading();
        
        try {
            const data = await this.fetchData();
            this.updateData(data);
            this.lastUpdate = new Date();
        } catch (error) {
            this.showError(error.message);
        } finally {
            this.isLoading = false;
            this.hideLoading();
        }
    }
    
    async fetchData() {
        throw new Error('fetchData must be implemented by subclass');
    }
    
    updateData(data) {
        this.data = data;
        this.render();
    }
    
    render() {
        throw new Error('render must be implemented by subclass');
    }
    
    showLoading() {
        if (this.element) {
            this.element.classList.add('loading');
        }
    }
    
    hideLoading() {
        if (this.element) {
            this.element.classList.remove('loading');
        }
    }
    
    showError(message) {
        console.error(`Widget ${this.id} error:`, message);
        
        if (this.element) {
            this.element.innerHTML = `
                <div class="widget-error">
                    <span class="icon">⚠️</span>
                    <span>Failed to load data</span>
                </div>
            `;
        }
    }
}

// Stats Widget
class StatsWidget extends BaseWidget {
    constructor() {
        super('stats', document.querySelector('.stats-grid'));
    }
    
    async fetchData() {
        try {
            // Fetch dashboard stats and agent monitoring data
            const [dashboardResponse, agentResponse] = await Promise.all([
                API.getDashboardStats(),
                API.get('/api/agents/monitoring/status')
            ]);
            
            if (!dashboardResponse.success) {
                throw new Error(dashboardResponse.error || 'Failed to fetch dashboard stats');
            }
            
            const data = dashboardResponse.data;
            
            // Add agent monitoring data if available
            if (agentResponse.success) {
                data.agents = agentResponse.data;
            }
            
            return data;
        } catch (error) {
            console.error('Error fetching dashboard data:', error);
            throw error;
        }
    }
    
    render() {
        if (!this.data || !this.element) return;
        
        // Update task stats
        this.updateStatCard('total-tasks', this.data.tasks?.total || 0);
        this.updateStatCard('tasks-completed', `${this.data.tasks?.completed || 0} completed`);
        
        // Update health stats
        if (this.data.health?.health_score) {
            this.updateStatCard('health-score', this.data.health.health_score.toFixed(1));
            this.updateStatCard('health-trend', 'Good');
        }
        
        // Update financial stats
        if (this.data.financial) {
            const netWorth = this.data.financial.net_worth || 0;
            this.updateStatCard('net-worth', formatCurrency(netWorth));
            
            const monthlyChange = (this.data.financial.monthly_income || 0) - (this.data.financial.monthly_expenses || 0);
            this.updateStatCard('net-worth-change', `${monthlyChange >= 0 ? '+' : ''}${formatCurrency(monthlyChange)} this month`);
        }
        
        // Update agent stats
        if (this.data.agents) {
            this.updateStatCard('total-agents', this.data.agents.total_agents || 0);
            this.updateStatCard('active-agents', `${this.data.agents.active_agents || 0} active`);
        }
        
        // Update social stats
        if (this.data.social) {
            // These would be shown in additional stat cards if present
        }
    }
    
    updateStatCard(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value;
        }
    }
}

// Quick Actions Widget
class QuickActionsWidget extends BaseWidget {
    constructor() {
        super('quick-actions', document.getElementById('quick-actions'));
    }
    
    async fetchData() {
        const response = await API.getQuickActions();
        if (!response.success) {
            throw new Error(response.error || 'Failed to fetch quick actions');
        }
        return response.data;
    }
    
    render() {
        if (!this.data || !this.element) return;
        
        this.element.innerHTML = this.data.map(action => `
            <a href="#" class="quick-action" data-action="${action.id}">
                <span class="icon icon-${action.icon}"></span>
                <h3>${action.title}</h3>
                <p>${action.description}</p>
            </a>
        `).join('');
    }
}

// Recent Activity Widget
class RecentActivityWidget extends BaseWidget {
    constructor() {
        super('recent-activity', document.getElementById('activity-feed'));
        this.maxItems = 10;
    }
    
    async fetchData() {
        // This would typically come from the dashboard summary
        const response = await API.getDashboardSummary();
        if (!response.success) {
            throw new Error(response.error || 'Failed to fetch activity');
        }
        return response.data.recent_activity || [];
    }
    
    render() {
        if (!this.data || !this.element) return;
        
        if (this.data.length === 0) {
            this.element.innerHTML = `
                <div class="activity-item">
                    <div class="activity-icon info">
                        <span class="icon">ℹ️</span>
                    </div>
                    <div class="activity-content">
                        <div class="activity-title">Welcome to PALOS!</div>
                        <div class="activity-description">Start by adding some tasks or events</div>
                        <div class="activity-time">Just now</div>
                    </div>
                </div>
            `;
            return;
        }
        
        this.element.innerHTML = this.data.slice(0, this.maxItems).map(activity => `
            <div class="activity-item">
                <div class="activity-icon ${activity.type || 'info'}">
                    <span class="icon">${this.getActivityIcon(activity.type)}</span>
                </div>
                <div class="activity-content">
                    <div class="activity-title">${activity.title}</div>
                    <div class="activity-description">${activity.description}</div>
                    <div class="activity-time">${formatRelativeTime(activity.timestamp)}</div>
                </div>
            </div>
        `).join('');
    }
    
    getActivityIcon(type) {
        const iconMap = {
            task: '✅',
            calendar: '📅',
            health: '❤️',
            finance: '💰',
            social: '📱',
            agent: '🤖'
        };
        return iconMap[type] || 'ℹ️';
    }
    
    addActivity(activity) {
        if (!this.data) this.data = [];
        
        this.data.unshift(activity);
        
        // Keep only recent items
        if (this.data.length > this.maxItems) {
            this.data = this.data.slice(0, this.maxItems);
        }
        
        this.render();
    }
}

// Notifications Widget
class NotificationsWidget extends BaseWidget {
    constructor() {
        super('notifications', null); // No specific element, uses notification system
        this.notifications = [];
    }
    
    async fetchData() {
        const response = await API.getNotifications(5);
        if (!response.success) {
            throw new Error(response.error || 'Failed to fetch notifications');
        }
        return response.data;
    }
    
    render() {
        // This widget doesn't render to a specific element
        // It manages the notification system
        this.updateNotificationBadge();
    }
    
    addNotification(notification) {
        this.notifications.unshift(notification);
        
        // Keep only recent notifications
        if (this.notifications.length > 20) {
            this.notifications = this.notifications.slice(0, 20);
        }
        
        this.updateNotificationBadge();
    }
    
    updateNotificationBadge() {
        const unreadCount = this.notifications.filter(n => !n.read).length;
        
        if (window.app && window.app.updateNotificationBadge) {
            window.app.updateNotificationBadge(unreadCount);
        }
    }
}

// Export for use in other modules
window.DashboardManager = DashboardManager;