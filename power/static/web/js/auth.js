/**
 * PALOS Web Dashboard - Authentication Manager
 * Handles user authentication, session management, and security
 */

class AuthenticationManager {
    constructor() {
        this.isAuthenticated = false;
        this.user = null;
        this.tokenRefreshInterval = null;
        this.sessionCheckInterval = null;
        this.loginAttempts = 0;
        this.maxLoginAttempts = 5;
        this.lockoutDuration = 15 * 60 * 1000; // 15 minutes
        
        this.init();
    }
    
    init() {
        // Check if user is locked out
        this.checkLockoutStatus();
        
        // Start session monitoring
        this.startSessionMonitoring();
        
        // Setup token refresh
        this.setupTokenRefresh();
        
        // Listen for storage changes (multi-tab support)
        this.setupStorageListener();
    }
    
    checkLockoutStatus() {
        const lockoutEnd = localStorage.getItem('palos_lockout_end');
        if (lockoutEnd) {
            const lockoutEndTime = new Date(lockoutEnd);
            if (Date.now() < lockoutEndTime.getTime()) {
                const remainingTime = Math.ceil((lockoutEndTime.getTime() - Date.now()) / 1000 / 60);
                throw new Error(`Account locked. Try again in ${remainingTime} minutes.`);
            } else {
                // Lockout expired, clear it
                localStorage.removeItem('palos_lockout_end');
                localStorage.removeItem('palos_login_attempts');
                this.loginAttempts = 0;
            }
        }
        
        // Get current login attempts
        this.loginAttempts = parseInt(localStorage.getItem('palos_login_attempts') || '0');
    }
    
    async validateCredentials(username, password) {
        // Basic validation
        if (!username || !password) {
            throw new Error('Username and password are required');
        }
        
        if (username.length < 3) {
            throw new Error('Username must be at least 3 characters');
        }
        
        if (password.length < 6) {
            throw new Error('Password must be at least 6 characters');
        }
        
        // Check lockout status
        if (this.loginAttempts >= this.maxLoginAttempts) {
            const lockoutEnd = new Date(Date.now() + this.lockoutDuration);
            localStorage.setItem('palos_lockout_end', lockoutEnd.toISOString());
            throw new Error(`Too many failed attempts. Account locked for ${this.lockoutDuration / 60000} minutes.`);
        }
        
        return true;
    }
    
    async login(credentials) {
        try {
            // Validate credentials format
            await this.validateCredentials(credentials.username, credentials.password);
            
            // Attempt login with API
            const response = await API.login(credentials);
            
            if (response.success) {
                const { access_token, refresh_token, user, expires_in } = response.data;
                
                // Store tokens securely
                this.storeTokens(access_token, refresh_token, expires_in);
                
                // Update auth state
                this.isAuthenticated = true;
                this.user = user;
                
                // Reset login attempts
                this.loginAttempts = 0;
                localStorage.removeItem('palos_login_attempts');
                localStorage.removeItem('palos_lockout_end');
                
                // Store user data
                this.storeUserData(user);
                
                // Setup token refresh
                this.setupTokenRefresh();
                
                // Log successful login
                this.logSecurityEvent('login_success', {
                    username: credentials.username,
                    timestamp: new Date().toISOString(),
                    userAgent: navigator.userAgent,
                    ip: await this.getClientIP()
                });
                
                return response;
            } else {
                throw new Error(response.error || 'Login failed');
            }
        } catch (error) {
            // Increment login attempts
            this.loginAttempts++;
            localStorage.setItem('palos_login_attempts', this.loginAttempts.toString());
            
            // Log failed login attempt
            this.logSecurityEvent('login_failed', {
                username: credentials.username,
                attempt: this.loginAttempts,
                error: error.message,
                timestamp: new Date().toISOString(),
                userAgent: navigator.userAgent,
                ip: await this.getClientIP()
            });
            
            throw error;
        }
    }
    
    async logout() {
        try {
            // Notify server about logout
            await API.logout();
        } catch (error) {
            console.warn('Server logout notification failed:', error);
        }
        
        // Clear tokens and user data
        this.clearAuthData();
        
        // Update auth state
        this.isAuthenticated = false;
        this.user = null;
        
        // Stop token refresh
        if (this.tokenRefreshInterval) {
            clearInterval(this.tokenRefreshInterval);
            this.tokenRefreshInterval = null;
        }
        
        // Stop session monitoring
        if (this.sessionCheckInterval) {
            clearInterval(this.sessionCheckInterval);
            this.sessionCheckInterval = null;
        }
        
        // Log logout
        this.logSecurityEvent('logout', {
            timestamp: new Date().toISOString()
        });
        
        // Disconnect WebSocket
        if (window.websocketManager) {
            window.websocketManager.disconnect();
        }
    }
    
    storeTokens(accessToken, refreshToken, expiresIn) {
        const expirationTime = Date.now() + (expiresIn * 1000);
        
        localStorage.setItem('palos_access_token', accessToken);
        localStorage.setItem('palos_refresh_token', refreshToken);
        localStorage.setItem('palos_token_expiration', expirationTime.toString());
    }
    
    storeUserData(user) {
        localStorage.setItem('palos_user_data', JSON.stringify({
            ...user,
            lastLogin: new Date().toISOString()
        }));
    }
    
    clearAuthData() {
        const keysToRemove = [
            'palos_access_token',
            'palos_refresh_token',
            'palos_token_expiration',
            'palos_user_data',
            'palos_session_data'
        ];
        
        keysToRemove.forEach(key => {
            localStorage.removeItem(key);
        });
    }
    
    async refreshToken() {
        try {
            const refreshToken = localStorage.getItem('palos_refresh_token');
            if (!refreshToken) {
                throw new Error('No refresh token available');
            }
            
            const response = await API.refreshToken();
            
            if (response.success) {
                const { access_token, refresh_token, expires_in } = response.data;
                this.storeTokens(access_token, refresh_token, expires_in);
                
                // Update WebSocket connection with new token
                if (window.websocketManager) {
                    window.websocketManager.updateToken(access_token);
                }
                
                console.log('✅ Token refreshed successfully');
                return true;
            } else {
                throw new Error(response.error || 'Token refresh failed');
            }
        } catch (error) {
            console.error('❌ Token refresh failed:', error);
            
            // If refresh fails, logout user
            this.logout();
            
            if (window.app && window.app.showLoginModal) {
                window.app.showLoginModal();
                window.app.showToast('Session expired. Please sign in again.', 'warning');
            }
            
            return false;
        }
    }
    
    setupTokenRefresh() {
        // Clear existing interval
        if (this.tokenRefreshInterval) {
            clearInterval(this.tokenRefreshInterval);
        }
        
        const expirationTime = parseInt(localStorage.getItem('palos_token_expiration') || '0');
        if (expirationTime === 0) return;
        
        const timeUntilExpiration = expirationTime - Date.now();
        const refreshTime = Math.max(timeUntilExpiration - (5 * 60 * 1000), 60 * 1000); // Refresh 5 minutes before expiry, or in 1 minute if already close
        
        this.tokenRefreshInterval = setTimeout(() => {
            this.refreshToken();
            
            // Setup next refresh
            this.setupTokenRefresh();
        }, refreshTime);
        
        console.log(`🔄 Token refresh scheduled in ${Math.round(refreshTime / 1000 / 60)} minutes`);
    }
    
    startSessionMonitoring() {
        // Check session validity every 5 minutes
        this.sessionCheckInterval = setInterval(async () => {
            if (this.isAuthenticated) {
                await this.validateSession();
            }
        }, 5 * 60 * 1000);
        
        // Monitor user activity
        this.setupActivityMonitoring();
    }
    
    async validateSession() {
        try {
            const response = await API.get('/auth/validate');
            if (!response.success) {
                throw new Error('Session validation failed');
            }
        } catch (error) {
            console.warn('Session validation failed:', error);
            this.logout();
        }
    }
    
    setupActivityMonitoring() {
        let lastActivity = Date.now();
        const maxInactivity = 30 * 60 * 1000; // 30 minutes
        
        const activityEvents = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];
        
        const updateActivity = () => {
            lastActivity = Date.now();
            localStorage.setItem('palos_last_activity', lastActivity.toString());
        };
        
        activityEvents.forEach(event => {
            document.addEventListener(event, updateActivity, true);
        });
        
        // Check for inactivity
        const inactivityCheck = setInterval(() => {
            const timeSinceActivity = Date.now() - lastActivity;
            
            if (timeSinceActivity > maxInactivity && this.isAuthenticated) {
                console.log('User inactive for too long, logging out');
                this.logout();
                
                if (window.app && window.app.showToast) {
                    window.app.showToast('Logged out due to inactivity', 'warning');
                }
                
                clearInterval(inactivityCheck);
            }
        }, 60 * 1000); // Check every minute
    }
    
    setupStorageListener() {
        // Listen for changes in other tabs
        window.addEventListener('storage', (e) => {
            if (e.key === 'palos_access_token') {
                if (e.newValue === null && this.isAuthenticated) {
                    // Token was removed in another tab, logout this tab too
                    this.logout();
                    if (window.app && window.app.showLoginModal) {
                        window.app.showLoginModal();
                        window.app.showToast('Logged out from another tab', 'info');
                    }
                } else if (e.newValue && !this.isAuthenticated) {
                    // User logged in from another tab, reload this tab
                    window.location.reload();
                }
            }
        });
    }
    
    async getClientIP() {
        try {
            // This is a simple way to get client IP, in production you might want to use a dedicated service
            const response = await fetch('https://api.ipify.org?format=json');
            const data = await response.json();
            return data.ip;
        } catch (error) {
            return 'unknown';
        }
    }
    
    logSecurityEvent(eventType, data) {
        const securityLog = JSON.parse(localStorage.getItem('palos_security_log') || '[]');
        
        securityLog.push({
            type: eventType,
            data: data,
            timestamp: new Date().toISOString()
        });
        
        // Keep only last 100 events
        if (securityLog.length > 100) {
            securityLog.splice(0, securityLog.length - 100);
        }
        
        localStorage.setItem('palos_security_log', JSON.stringify(securityLog));
        
        // Send critical events to server
        if (['login_failed', 'suspicious_activity'].includes(eventType)) {
            this.reportSecurityEvent(eventType, data);
        }
    }
    
    async reportSecurityEvent(eventType, data) {
        try {
            await API.post('/auth/security-event', {
                type: eventType,
                data: data
            });
        } catch (error) {
            console.warn('Failed to report security event:', error);
        }
    }
    
    // Password strength checker
    checkPasswordStrength(password) {
        const checks = {
            length: password.length >= 8,
            lowercase: /[a-z]/.test(password),
            uppercase: /[A-Z]/.test(password),
            numbers: /\d/.test(password),
            symbols: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)
        };
        
        const passedChecks = Object.values(checks).filter(Boolean).length;
        
        let strength = 'weak';
        if (passedChecks >= 5) strength = 'very-strong';
        else if (passedChecks >= 4) strength = 'strong';
        else if (passedChecks >= 3) strength = 'medium';
        
        return {
            strength,
            score: passedChecks,
            checks,
            suggestions: this.getPasswordSuggestions(checks)
        };
    }
    
    getPasswordSuggestions(checks) {
        const suggestions = [];
        
        if (!checks.length) suggestions.push('Use at least 8 characters');
        if (!checks.lowercase) suggestions.push('Add lowercase letters');
        if (!checks.uppercase) suggestions.push('Add uppercase letters');
        if (!checks.numbers) suggestions.push('Add numbers');
        if (!checks.symbols) suggestions.push('Add special characters');
        
        return suggestions;
    }
    
    // Two-factor authentication helpers
    async enableTwoFactor() {
        try {
            const response = await API.post('/auth/2fa/enable');
            return response;
        } catch (error) {
            throw new Error('Failed to enable two-factor authentication');
        }
    }
    
    async verifyTwoFactor(code) {
        try {
            const response = await API.post('/auth/2fa/verify', { code });
            return response.success;
        } catch (error) {
            throw new Error('Invalid two-factor authentication code');
        }
    }
    
    // Biometric authentication (if supported)
    async isBiometricSupported() {
        if (window.PublicKeyCredential && 
            PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable) {
            return await PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable();
        }
        return false;
    }
    
    async registerBiometric() {
        if (!await this.isBiometricSupported()) {
            throw new Error('Biometric authentication not supported on this device');
        }
        
        try {
            // Get challenge from server
            const challengeResponse = await API.post('/auth/biometric/challenge');
            if (!challengeResponse.success) {
                throw new Error('Failed to get biometric challenge');
            }
            
            const credential = await navigator.credentials.create({
                publicKey: challengeResponse.data.publicKeyOptions
            });
            
            // Register credential with server
            const registrationResponse = await API.post('/auth/biometric/register', {
                credential: {
                    id: credential.id,
                    rawId: Array.from(new Uint8Array(credential.rawId)),
                    response: {
                        clientDataJSON: Array.from(new Uint8Array(credential.response.clientDataJSON)),
                        attestationObject: Array.from(new Uint8Array(credential.response.attestationObject))
                    }
                }
            });
            
            return registrationResponse.success;
        } catch (error) {
            console.error('Biometric registration failed:', error);
            throw new Error('Failed to register biometric authentication');
        }
    }
    
    async authenticateWithBiometric() {
        if (!await this.isBiometricSupported()) {
            throw new Error('Biometric authentication not supported on this device');
        }
        
        try {
            // Get assertion challenge from server
            const challengeResponse = await API.post('/auth/biometric/assertion-challenge');
            if (!challengeResponse.success) {
                throw new Error('Failed to get biometric challenge');
            }
            
            const assertion = await navigator.credentials.get({
                publicKey: challengeResponse.data.publicKeyOptions
            });
            
            // Verify assertion with server
            const verificationResponse = await API.post('/auth/biometric/verify', {
                assertion: {
                    id: assertion.id,
                    rawId: Array.from(new Uint8Array(assertion.rawId)),
                    response: {
                        clientDataJSON: Array.from(new Uint8Array(assertion.response.clientDataJSON)),
                        authenticatorData: Array.from(new Uint8Array(assertion.response.authenticatorData)),
                        signature: Array.from(new Uint8Array(assertion.response.signature))
                    }
                }
            });
            
            if (verificationResponse.success) {
                // Store tokens and update auth state
                const { access_token, refresh_token, user, expires_in } = verificationResponse.data;
                this.storeTokens(access_token, refresh_token, expires_in);
                this.isAuthenticated = true;
                this.user = user;
                this.storeUserData(user);
                this.setupTokenRefresh();
                
                return verificationResponse;
            } else {
                throw new Error('Biometric verification failed');
            }
        } catch (error) {
            console.error('Biometric authentication failed:', error);
            throw new Error('Biometric authentication failed');
        }
    }
    
    // Get current auth state
    getAuthState() {
        return {
            isAuthenticated: this.isAuthenticated,
            user: this.user,
            tokenExpiration: parseInt(localStorage.getItem('palos_token_expiration') || '0'),
            lastActivity: parseInt(localStorage.getItem('palos_last_activity') || '0'),
            loginAttempts: this.loginAttempts
        };
    }
}

// Export for use in other modules
window.AuthenticationManager = AuthenticationManager;