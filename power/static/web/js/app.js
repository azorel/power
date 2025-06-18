/**
 * PALOS Web Dashboard - Main Application
 * Mobile-first responsive web application with PWA capabilities
 */

class PALOSApp {
    constructor() {
        this.currentPage = 'dashboard';
        this.isAuthenticated = false;
        this.user = null;
        this.theme = 'light';
        this.isOnline = navigator.onLine;
        this.sidebarOpen = false;
        this.notificationsOpen = false;
        
        // Initialize app
        this.init();
    }
    
    async init() {
        console.log('🚀 Initializing PALOS Web Dashboard...');
        
        try {
            // Show loading screen
            this.showLoadingScreen();
            
            // Initialize theme
            this.initTheme();
            
            // Setup event listeners
            this.setupEventListeners();
            
            // Initialize offline detection
            this.initOfflineDetection();
            
            // Check authentication status
            await this.checkAuthStatus();
            
            if (this.isAuthenticated) {
                // User is authenticated, show app
                await this.showApp();
            } else {
                // Show login modal
                this.showLoginModal();
            }
            
            // Hide loading screen
            this.hideLoadingScreen();
            
            console.log('✅ PALOS Web Dashboard initialized successfully');
            
        } catch (error) {
            console.error('❌ Failed to initialize PALOS:', error);
            this.showError('Failed to initialize application. Please refresh the page.');
            this.hideLoadingScreen();
        }
    }
    
    // Authentication Methods
    async checkAuthStatus() {
        const token = localStorage.getItem('palos_access_token');
        if (!token) {
            this.isAuthenticated = false;
            return;
        }
        
        try {
            // Validate token with backend
            const response = await API.get('/auth/validate', {
                headers: { Authorization: `Bearer ${token}` }
            });
            
            if (response.success) {
                this.isAuthenticated = true;
                this.user = response.data.user;
                this.updateUserDisplay();
            } else {
                this.logout();
            }
        } catch (error) {
            console.error('Token validation failed:', error);
            this.logout();
        }
    }
    
    async login(credentials) {
        try {
            const response = await API.post('/auth/login', credentials);
            
            if (response.success) {
                const { access_token, refresh_token, user } = response.data;
                
                // Store tokens
                localStorage.setItem('palos_access_token', access_token);
                localStorage.setItem('palos_refresh_token', refresh_token);
                
                // Update app state
                this.isAuthenticated = true;
                this.user = user;
                
                // Hide login modal and show app
                this.hideLoginModal();
                await this.showApp();
                
                this.showToast('Welcome back!', 'success');
            } else {
                throw new Error(response.message || 'Login failed');
            }
        } catch (error) {
            console.error('Login error:', error);
            this.showToast(error.message || 'Login failed. Please try again.', 'error');
            throw error;
        }
    }
    
    logout() {
        // Clear tokens
        localStorage.removeItem('palos_access_token');
        localStorage.removeItem('palos_refresh_token');
        
        // Reset app state
        this.isAuthenticated = false;
        this.user = null;
        
        // Close WebSocket connection
        if (window.websocketManager) {
            window.websocketManager.disconnect();
        }
        
        // Hide app and show login
        this.hideApp();
        this.showLoginModal();
        
        this.showToast('You have been signed out', 'info');
    }
    
    // UI State Management
    async showApp() {
        document.getElementById('app').style.display = 'block';
        
        // Update user display
        this.updateUserDisplay();
        
        // Initialize WebSocket connection
        if (window.WebSocketManager) {
            const token = localStorage.getItem('palos_access_token');
            window.websocketManager = new WebSocketManager(token);
            await window.websocketManager.connect();
        }
        
        // Load initial data
        await this.loadDashboardData();
        
        // Initialize page managers
        this.initPageManagers();
        
        // Navigate to initial page
        this.navigateToPage(this.currentPage);
    }
    
    hideApp() {
        document.getElementById('app').style.display = 'none';
    }
    
    showLoginModal() {
        const modal = document.getElementById('auth-modal');
        modal.style.display = 'flex';
        modal.classList.add('fade-in');
        
        // Focus username field
        setTimeout(() => {
            document.getElementById('username').focus();
        }, 100);
    }
    
    hideLoginModal() {
        const modal = document.getElementById('auth-modal');
        modal.classList.add('fade-out');
        setTimeout(() => {
            modal.style.display = 'none';
            modal.classList.remove('fade-in', 'fade-out');
        }, 300);
    }
    
    showLoadingScreen() {
        document.getElementById('loading-screen').style.display = 'flex';
    }
    
    hideLoadingScreen() {
        const loadingScreen = document.getElementById('loading-screen');
        loadingScreen.classList.add('fade-out');
        setTimeout(() => {
            loadingScreen.style.display = 'none';
        }, 300);
    }
    
    // Navigation
    navigateToPage(pageId) {
        // Hide all pages
        document.querySelectorAll('.page').forEach(page => {
            page.classList.remove('active');
        });
        
        // Show target page
        const targetPage = document.getElementById(`${pageId}-page`);
        if (targetPage) {
            targetPage.classList.add('active');
            this.currentPage = pageId;
            
            // Update navigation states
            this.updateNavigationState(pageId);
            
            // Load page data if needed
            this.loadPageData(pageId);
        }
    }
    
    updateNavigationState(pageId) {
        // Update sidebar navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelectorAll(`[data-page="${pageId}"]`).forEach(link => {
            link.closest('.nav-item')?.classList.add('active');
        });
        
        // Update bottom navigation
        document.querySelectorAll('.bottom-nav-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelectorAll(`.bottom-nav-item[data-page="${pageId}"]`).forEach(item => {
            item.classList.add('active');
        });
    }
    
    async loadPageData(pageId) {
        try {
            switch (pageId) {
                case 'dashboard':
                    await this.loadDashboardData();
                    break;
                case 'calendar':
                    if (window.calendarManager) {
                        await window.calendarManager.loadCalendarData();
                    }
                    break;
                case 'tasks':
                    if (window.tasksManager) {
                        await window.tasksManager.loadTasks();
                    }
                    break;
                case 'health':
                    if (window.healthManager) {
                        await window.healthManager.loadHealthData();
                    }
                    break;
                case 'finance':
                    if (window.financeManager) {
                        await window.financeManager.loadFinanceData();
                    }
                    break;
                case 'social':
                    if (window.socialManager) {
                        await window.socialManager.loadSocialData();
                    }
                    break;
                case 'agents':
                    if (window.agentsManager) {
                        window.agentsManager.onPageShow();
                    }
                    break;
            }
        } catch (error) {
            console.error(`Failed to load ${pageId} data:`, error);
            this.showToast(`Failed to load ${pageId} data`, 'error');
        }
    }
    
    // Dashboard Data
    async loadDashboardData() {
        try {
            const [summaryResponse, statsResponse, actionsResponse] = await Promise.all([
                API.get('/dashboard/summary'),
                API.get('/dashboard/stats'),
                API.get('/dashboard/quick-actions')
            ]);
            
            if (summaryResponse.success) {
                this.updateDashboardSummary(summaryResponse.data);
            }
            
            if (statsResponse.success) {
                this.updateDashboardStats(statsResponse.data);
            }
            
            if (actionsResponse.success) {
                this.updateQuickActions(actionsResponse.data);
            }
            
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
            this.showToast('Failed to load dashboard data', 'error');
        }
    }
    
    updateDashboardSummary(data) {
        // Update stat cards with real data
        const totalTasks = document.getElementById('total-tasks');
        const completedTasks = document.getElementById('tasks-completed');
        const upcomingEvents = document.getElementById('upcoming-events');
        const healthScore = document.getElementById('health-score');
        const netWorth = document.getElementById('net-worth');
        
        if (totalTasks) totalTasks.textContent = data.total_tasks || '0';
        if (completedTasks) completedTasks.textContent = `${data.completed_tasks || 0} completed`;
        if (upcomingEvents) upcomingEvents.textContent = data.upcoming_events || '0';
        if (healthScore) healthScore.textContent = data.health_score ? data.health_score.toFixed(1) : '--';
        if (netWorth) netWorth.textContent = data.net_worth ? `$${(data.net_worth / 1000).toFixed(1)}k` : '$0';
    }
    
    updateDashboardStats(stats) {
        // Update individual stat sections
        if (stats.tasks) {
            const totalTasks = document.getElementById('total-tasks');
            const tasksCompleted = document.getElementById('tasks-completed');
            
            if (totalTasks) totalTasks.textContent = stats.tasks.total;
            if (tasksCompleted) tasksCompleted.textContent = `${stats.tasks.completed} completed`;
        }
        
        if (stats.health && stats.health.health_score) {
            const healthScore = document.getElementById('health-score');
            const healthTrend = document.getElementById('health-trend');
            
            if (healthScore) healthScore.textContent = stats.health.health_score.toFixed(1);
            if (healthTrend) healthTrend.textContent = 'Good';
        }
        
        if (stats.financial) {
            const netWorth = document.getElementById('net-worth');
            const netWorthChange = document.getElementById('net-worth-change');
            
            if (netWorth) {
                const worth = stats.financial.net_worth || 0;
                netWorth.textContent = `$${(worth / 1000).toFixed(1)}k`;
            }
            
            if (netWorthChange) {
                const monthlyChange = (stats.financial.monthly_income || 0) - (stats.financial.monthly_expenses || 0);
                netWorthChange.textContent = `$${monthlyChange >= 0 ? '+' : ''}${monthlyChange.toFixed(0)} this month`;
                netWorthChange.className = `stat-change ${monthlyChange >= 0 ? 'positive' : 'negative'}`;
            }
        }
    }
    
    updateQuickActions(actions) {
        const container = document.getElementById('quick-actions');
        if (!container) return;
        
        container.innerHTML = actions.map(action => `
            <a href="#" class="quick-action" data-action="${action.id}">
                <span class="icon ${action.icon}"></span>
                <h3>${action.title}</h3>
                <p>${action.description}</p>
            </a>
        `).join('');
    }
    
    // Theme Management
    initTheme() {
        // Get saved theme or detect system preference
        const savedTheme = localStorage.getItem('palos_theme');
        if (savedTheme) {
            this.theme = savedTheme;
        } else {
            this.theme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        }
        
        this.applyTheme(this.theme);
        
        // Listen for system theme changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!localStorage.getItem('palos_theme')) {
                this.theme = e.matches ? 'dark' : 'light';
                this.applyTheme(this.theme);
            }
        });
    }
    
    applyTheme(theme) {
        document.body.setAttribute('data-theme', theme);
        this.theme = theme;
        
        // Update theme toggle icon
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            const icon = themeToggle.querySelector('.icon');
            if (icon) {
                icon.className = theme === 'dark' ? 'icon icon-moon' : 'icon icon-sun';
            }
        }
        
        // Update meta theme-color for mobile
        const themeColorMeta = document.querySelector('meta[name="theme-color"]');
        if (themeColorMeta) {
            themeColorMeta.content = theme === 'dark' ? '#0F0F0F' : '#4F46E5';
        }
    }
    
    toggleTheme() {
        const newTheme = this.theme === 'light' ? 'dark' : 'light';
        this.applyTheme(newTheme);
        localStorage.setItem('palos_theme', newTheme);
    }
    
    // Offline Detection
    initOfflineDetection() {
        const offlineIndicator = document.getElementById('offline-indicator');
        
        const updateOnlineStatus = () => {
            this.isOnline = navigator.onLine;
            if (offlineIndicator) {
                offlineIndicator.style.display = this.isOnline ? 'none' : 'flex';
            }
            
            if (!this.isOnline) {
                this.showToast('You are now offline. Some features may be limited.', 'warning');
            } else {
                this.showToast('You are back online!', 'success');
            }
        };
        
        window.addEventListener('online', updateOnlineStatus);
        window.addEventListener('offline', updateOnlineStatus);
        
        // Initial check
        updateOnlineStatus();
    }
    
    // Event Listeners
    setupEventListeners() {
        // Login form
        const loginForm = document.getElementById('login-form');
        if (loginForm) {
            loginForm.addEventListener('submit', this.handleLogin.bind(this));
        }
        
        // Theme toggle
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', this.toggleTheme.bind(this));
        }
        
        // Menu toggle (mobile)
        const menuToggle = document.getElementById('menu-toggle');
        if (menuToggle) {
            menuToggle.addEventListener('click', this.toggleSidebar.bind(this));
        }
        
        // User menu dropdown
        const userBtn = document.getElementById('user-btn');
        if (userBtn) {
            userBtn.addEventListener('click', this.toggleUserDropdown.bind(this));
        }
        
        // Logout
        const logoutLink = document.getElementById('logout-link');
        if (logoutLink) {
            logoutLink.addEventListener('click', (e) => {
                e.preventDefault();
                this.logout();
            });
        }
        
        // Navigation links
        document.addEventListener('click', (e) => {
            const navLink = e.target.closest('[data-page]');
            if (navLink) {
                e.preventDefault();
                const pageId = navLink.getAttribute('data-page');
                this.navigateToPage(pageId);
                
                // Close sidebar on mobile after navigation
                if (window.innerWidth <= 768) {
                    this.closeSidebar();
                }
            }
        });
        
        // Quick actions
        document.addEventListener('click', (e) => {
            const quickAction = e.target.closest('[data-action]');
            if (quickAction) {
                e.preventDefault();
                const actionId = quickAction.getAttribute('data-action');
                this.handleQuickAction(actionId);
            }
        });
        
        // Notifications toggle
        const notificationsBtn = document.getElementById('notifications-btn');
        if (notificationsBtn) {
            notificationsBtn.addEventListener('click', this.toggleNotifications.bind(this));
        }
        
        // Close notifications
        const closeNotifications = document.getElementById('close-notifications');
        if (closeNotifications) {
            closeNotifications.addEventListener('click', this.closeNotifications.bind(this));
        }
        
        // Dashboard refresh
        const refreshDashboard = document.getElementById('refresh-dashboard');
        if (refreshDashboard) {
            refreshDashboard.addEventListener('click', () => {
                this.loadDashboardData();
            });
        }
        
        // Close dropdowns when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.user-menu')) {
                this.closeUserDropdown();
            }
            if (!e.target.closest('.notifications-panel') && !e.target.closest('#notifications-btn')) {
                this.closeNotifications();
            }
        });
        
        // Sidebar overlay close
        document.addEventListener('click', (e) => {
            if (this.sidebarOpen && !e.target.closest('.sidebar') && !e.target.closest('#menu-toggle')) {
                this.closeSidebar();
            }
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', this.handleKeyboardShortcuts.bind(this));
        
        // Window resize
        window.addEventListener('resize', this.handleResize.bind(this));
    }
    
    async handleLogin(e) {
        e.preventDefault();
        
        const loginBtn = document.getElementById('login-btn');
        const btnText = loginBtn.querySelector('.btn-text');
        const btnSpinner = loginBtn.querySelector('.btn-spinner');
        
        // Show loading state
        btnText.style.display = 'none';
        btnSpinner.style.display = 'inline-block';
        loginBtn.disabled = true;
        
        try {
            const formData = new FormData(e.target);
            const credentials = {
                username: formData.get('username'),
                password: formData.get('password'),
                remember_me: formData.get('remember_me') === 'on'
            };
            
            await this.login(credentials);
            
        } catch (error) {
            // Error handling is done in login method
        } finally {
            // Reset button state
            btnText.style.display = 'inline';
            btnSpinner.style.display = 'none';
            loginBtn.disabled = false;
        }
    }
    
    handleQuickAction(actionId) {
        switch (actionId) {
            case 'add_task':
                this.navigateToPage('tasks');
                // Trigger add task modal if available
                if (window.tasksManager && window.tasksManager.showAddTaskModal) {
                    setTimeout(() => window.tasksManager.showAddTaskModal(), 300);
                }
                break;
            case 'add_event':
                this.navigateToPage('calendar');
                // Trigger add event modal if available
                if (window.calendarManager && window.calendarManager.showAddEventModal) {
                    setTimeout(() => window.calendarManager.showAddEventModal(), 300);
                }
                break;
            case 'log_health':
                this.navigateToPage('health');
                break;
            case 'add_transaction':
                this.navigateToPage('finance');
                break;
            case 'social_post':
                this.navigateToPage('social');
                break;
            default:
                console.log('Quick action not implemented:', actionId);
        }
    }
    
    handleKeyboardShortcuts(e) {
        // Ctrl/Cmd + K for quick search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            // Implement quick search modal
            console.log('Quick search shortcut');
        }
        
        // Escape to close modals/panels
        if (e.key === 'Escape') {
            this.closeUserDropdown();
            this.closeNotifications();
            if (window.innerWidth <= 768) {
                this.closeSidebar();
            }
        }
        
        // Number keys for quick navigation
        if (e.altKey && /^[1-7]$/.test(e.key)) {
            e.preventDefault();
            const pages = ['dashboard', 'calendar', 'tasks', 'health', 'finance', 'social', 'agents'];
            const pageIndex = parseInt(e.key) - 1;
            if (pages[pageIndex]) {
                this.navigateToPage(pages[pageIndex]);
            }
        }
    }
    
    handleResize() {
        // Close sidebar on desktop
        if (window.innerWidth > 768) {
            this.closeSidebar();
        }
    }
    
    // UI Helper Methods
    toggleSidebar() {
        this.sidebarOpen = !this.sidebarOpen;
        const sidebar = document.getElementById('sidebar');
        if (sidebar) {
            sidebar.classList.toggle('active', this.sidebarOpen);
        }
    }
    
    closeSidebar() {
        this.sidebarOpen = false;
        const sidebar = document.getElementById('sidebar');
        if (sidebar) {
            sidebar.classList.remove('active');
        }
    }
    
    toggleUserDropdown() {
        const dropdown = document.getElementById('user-dropdown');
        if (dropdown) {
            dropdown.classList.toggle('active');
        }
    }
    
    closeUserDropdown() {
        const dropdown = document.getElementById('user-dropdown');
        if (dropdown) {
            dropdown.classList.remove('active');
        }
    }
    
    toggleNotifications() {
        this.notificationsOpen = !this.notificationsOpen;
        const panel = document.querySelector('.notifications-panel');
        if (panel) {
            panel.classList.toggle('active', this.notificationsOpen);
        }
        
        if (this.notificationsOpen) {
            this.loadNotifications();
        }
    }
    
    closeNotifications() {
        this.notificationsOpen = false;
        const panel = document.querySelector('.notifications-panel');
        if (panel) {
            panel.classList.remove('active');
        }
    }
    
    async loadNotifications() {
        try {
            const response = await API.get('/dashboard/notifications');
            if (response.success) {
                this.updateNotificationsPanel(response.data);
            }
        } catch (error) {
            console.error('Failed to load notifications:', error);
        }
    }
    
    updateNotificationsPanel(notifications) {
        const list = document.getElementById('notifications-list');
        if (!list) return;
        
        if (notifications.length === 0) {
            list.innerHTML = '<p class="text-center text-secondary">No notifications</p>';
            return;
        }
        
        list.innerHTML = notifications.map(notification => `
            <div class="notification-item ${notification.read ? '' : 'unread'}">
                <div class="notification-icon ${notification.type}">
                    <span class="icon icon-${notification.type}"></span>
                </div>
                <div class="notification-content">
                    <div class="notification-title">${notification.title}</div>
                    <div class="notification-message">${notification.message}</div>
                    <div class="notification-time">${this.formatRelativeTime(notification.created_at)}</div>
                </div>
            </div>
        `).join('');
        
        // Update notification badge
        const unreadCount = notifications.filter(n => !n.read).length;
        this.updateNotificationBadge(unreadCount);
    }
    
    updateNotificationBadge(count) {
        const badge = document.getElementById('notification-count');
        if (badge) {
            if (count > 0) {
                badge.textContent = count > 99 ? '99+' : count.toString();
                badge.style.display = 'inline-block';
            } else {
                badge.style.display = 'none';
            }
        }
    }
    
    updateUserDisplay() {
        if (!this.user) return;
        
        const userAvatar = document.getElementById('user-avatar');
        const userName = document.getElementById('user-name');
        
        if (userAvatar) {
            userAvatar.textContent = (this.user.first_name || this.user.username || 'U').charAt(0).toUpperCase();
        }
        
        if (userName) {
            userName.textContent = this.user.first_name || this.user.username || 'User';
        }
    }
    
    initPageManagers() {
        // Initialize page-specific managers
        if (window.DashboardManager) {
            window.dashboardManager = new DashboardManager();
        }
        if (window.CalendarManager) {
            window.calendarManager = new CalendarManager();
        }
        if (window.TasksManager) {
            window.tasksManager = new TasksManager();
        }
        if (window.HealthManager) {
            window.healthManager = new HealthManager();
        }
        if (window.FinanceManager) {
            window.financeManager = new FinanceManager();
        }
        if (window.SocialManager) {
            window.socialManager = new SocialManager();
        }
        if (window.AgentsManager) {
            window.agentsManager = new AgentsManager();
        }
    }
    
    // Utility Methods
    showToast(message, type = 'info', duration = 5000) {
        if (window.showToast) {
            window.showToast(message, type, duration);
        } else {
            console.log(`Toast [${type}]: ${message}`);
        }
    }
    
    showError(message) {
        this.showToast(message, 'error');
    }
    
    formatRelativeTime(timestamp) {
        if (window.formatRelativeTime) {
            return window.formatRelativeTime(timestamp);
        }
        return new Date(timestamp).toLocaleDateString();
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new PALOSApp();
});

// Export for other modules
window.PALOSApp = PALOSApp;