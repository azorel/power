/**
 * PALOS Web Dashboard - Utility Functions
 * Common utility functions used throughout the application
 */

// Toast notification system
function showToast(message, type = 'info', duration = 5000) {
    const container = document.getElementById('toast-container');
    if (!container) {
        console.warn('Toast container not found');
        return;
    }
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const iconMap = {
        success: '✓',
        error: '✕',
        warning: '⚠',
        info: 'ℹ'
    };
    
    toast.innerHTML = `
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-weight: bold;">${iconMap[type] || 'ℹ'}</span>
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" style="margin-left: auto; background: none; border: none; cursor: pointer; opacity: 0.7;">✕</button>
        </div>
    `;
    
    container.appendChild(toast);
    
    // Auto-remove after duration
    setTimeout(() => {
        if (toast.parentElement) {
            toast.style.animation = 'slideOutRight 0.3s ease-out forwards';
            setTimeout(() => toast.remove(), 300);
        }
    }, duration);
    
    return toast;
}

// Date and time utilities
function formatDate(date, options = {}) {
    if (!date) return '';
    
    const d = new Date(date);
    const defaultOptions = {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    };
    
    return d.toLocaleDateString('en-US', { ...defaultOptions, ...options });
}

function formatTime(date, options = {}) {
    if (!date) return '';
    
    const d = new Date(date);
    const defaultOptions = {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
    };
    
    return d.toLocaleTimeString('en-US', { ...defaultOptions, ...options });
}

function formatDateTime(date, options = {}) {
    if (!date) return '';
    
    const d = new Date(date);
    const defaultOptions = {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
    };
    
    return d.toLocaleString('en-US', { ...defaultOptions, ...options });
}

function formatRelativeTime(date) {
    if (!date) return '';
    
    const now = new Date();
    const target = new Date(date);
    const diffMs = now - target;
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffSecs < 60) {
        return 'Just now';
    } else if (diffMins < 60) {
        return `${diffMins}m ago`;
    } else if (diffHours < 24) {
        return `${diffHours}h ago`;
    } else if (diffDays < 7) {
        return `${diffDays}d ago`;
    } else {
        return formatDate(date);
    }
}

function isToday(date) {
    const today = new Date();
    const target = new Date(date);
    
    return today.getDate() === target.getDate() &&
           today.getMonth() === target.getMonth() &&
           today.getFullYear() === target.getFullYear();
}

function isTomorrow(date) {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const target = new Date(date);
    
    return tomorrow.getDate() === target.getDate() &&
           tomorrow.getMonth() === target.getMonth() &&
           tomorrow.getFullYear() === target.getFullYear();
}

function getDaysInMonth(year, month) {
    return new Date(year, month + 1, 0).getDate();
}

function getFirstDayOfMonth(year, month) {
    return new Date(year, month, 1).getDay();
}

// Number formatting utilities
function formatCurrency(amount, currency = 'USD', options = {}) {
    const defaultOptions = {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    };
    
    return new Intl.NumberFormat('en-US', { ...defaultOptions, ...options }).format(amount);
}

function formatNumber(number, options = {}) {
    const defaultOptions = {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    };
    
    return new Intl.NumberFormat('en-US', { ...defaultOptions, ...options }).format(number);
}

function formatPercentage(value, options = {}) {
    const defaultOptions = {
        style: 'percent',
        minimumFractionDigits: 0,
        maximumFractionDigits: 1
    };
    
    return new Intl.NumberFormat('en-US', { ...defaultOptions, ...options }).format(value / 100);
}

function abbreviateNumber(number) {
    if (number < 1000) return number.toString();
    if (number < 1000000) return (number / 1000).toFixed(1) + 'K';
    if (number < 1000000000) return (number / 1000000).toFixed(1) + 'M';
    return (number / 1000000000).toFixed(1) + 'B';
}

// String utilities
function truncateString(str, length = 50, suffix = '...') {
    if (!str || str.length <= length) return str || '';
    return str.substring(0, length - suffix.length) + suffix;
}

function capitalizeFirstLetter(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function slugify(str) {
    return str
        .toLowerCase()
        .trim()
        .replace(/[^\w\s-]/g, '')
        .replace(/[\s_-]+/g, '-')
        .replace(/^-+|-+$/g, '');
}

function generateId(prefix = '') {
    const timestamp = Date.now().toString(36);
    const random = Math.random().toString(36).substr(2, 5);
    return prefix ? `${prefix}-${timestamp}-${random}` : `${timestamp}-${random}`;
}

// Validation utilities
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function isValidURL(url) {
    try {
        new URL(url);
        return true;
    } catch {
        return false;
    }
}

function isValidPhoneNumber(phone) {
    const phoneRegex = /^\+?[\d\s\-\(\)]{10,}$/;
    return phoneRegex.test(phone);
}

function validateForm(formData, rules) {
    const errors = {};
    
    Object.keys(rules).forEach(field => {
        const value = formData[field];
        const rule = rules[field];
        
        if (rule.required && (!value || value.trim() === '')) {
            errors[field] = `${capitalizeFirstLetter(field)} is required`;
            return;
        }
        
        if (value && rule.minLength && value.length < rule.minLength) {
            errors[field] = `${capitalizeFirstLetter(field)} must be at least ${rule.minLength} characters`;
            return;
        }
        
        if (value && rule.maxLength && value.length > rule.maxLength) {
            errors[field] = `${capitalizeFirstLetter(field)} must be no more than ${rule.maxLength} characters`;
            return;
        }
        
        if (value && rule.pattern && !rule.pattern.test(value)) {
            errors[field] = rule.message || `${capitalizeFirstLetter(field)} format is invalid`;
            return;
        }
        
        if (value && rule.email && !isValidEmail(value)) {
            errors[field] = 'Please enter a valid email address';
            return;
        }
        
        if (value && rule.url && !isValidURL(value)) {
            errors[field] = 'Please enter a valid URL';
            return;
        }
    });
    
    return errors;
}

// DOM utilities
function createElement(tag, attributes = {}, children = []) {
    const element = document.createElement(tag);
    
    Object.keys(attributes).forEach(key => {
        if (key === 'className' || key === 'class') {
            element.className = attributes[key];
        } else if (key === 'innerHTML') {
            element.innerHTML = attributes[key];
        } else if (key === 'textContent') {
            element.textContent = attributes[key];
        } else {
            element.setAttribute(key, attributes[key]);
        }
    });
    
    children.forEach(child => {
        if (typeof child === 'string') {
            element.appendChild(document.createTextNode(child));
        } else if (child instanceof HTMLElement) {
            element.appendChild(child);
        }
    });
    
    return element;
}

function removeElement(selector) {
    const element = typeof selector === 'string' ? document.querySelector(selector) : selector;
    if (element && element.parentNode) {
        element.parentNode.removeChild(element);
    }
}

function toggleClass(element, className, force) {
    if (typeof element === 'string') {
        element = document.querySelector(element);
    }
    if (element) {
        return element.classList.toggle(className, force);
    }
    return false;
}

function hasClass(element, className) {
    if (typeof element === 'string') {
        element = document.querySelector(element);
    }
    return element ? element.classList.contains(className) : false;
}

// Event utilities
function debounce(func, wait, immediate = false) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            timeout = null;
            if (!immediate) func(...args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func(...args);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function executedFunction(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

function once(func) {
    let called = false;
    return function executedFunction(...args) {
        if (!called) {
            called = true;
            return func.apply(this, args);
        }
    };
}

// Local storage utilities
function setLocalStorage(key, value, expirationDays = null) {
    try {
        const item = {
            value: value,
            timestamp: Date.now(),
            expiration: expirationDays ? Date.now() + (expirationDays * 24 * 60 * 60 * 1000) : null
        };
        localStorage.setItem(key, JSON.stringify(item));
        return true;
    } catch (error) {
        console.error('Failed to save to localStorage:', error);
        return false;
    }
}

function getLocalStorage(key, defaultValue = null) {
    try {
        const itemStr = localStorage.getItem(key);
        if (!itemStr) return defaultValue;
        
        const item = JSON.parse(itemStr);
        
        // Check expiration
        if (item.expiration && Date.now() > item.expiration) {
            localStorage.removeItem(key);
            return defaultValue;
        }
        
        return item.value;
    } catch (error) {
        console.error('Failed to read from localStorage:', error);
        return defaultValue;
    }
}

function removeLocalStorage(key) {
    try {
        localStorage.removeItem(key);
        return true;
    } catch (error) {
        console.error('Failed to remove from localStorage:', error);
        return false;
    }
}

function clearExpiredLocalStorage() {
    try {
        const keys = Object.keys(localStorage);
        keys.forEach(key => {
            try {
                const itemStr = localStorage.getItem(key);
                if (itemStr) {
                    const item = JSON.parse(itemStr);
                    if (item.expiration && Date.now() > item.expiration) {
                        localStorage.removeItem(key);
                    }
                }
            } catch {
                // Skip invalid items
            }
        });
    } catch (error) {
        console.error('Failed to clear expired localStorage items:', error);
    }
}

// Color utilities
function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
    } : null;
}

function rgbToHex(r, g, b) {
    return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
}

function adjustBrightness(hex, percent) {
    const rgb = hexToRgb(hex);
    if (!rgb) return hex;
    
    const factor = percent / 100;
    const r = Math.min(255, Math.max(0, Math.round(rgb.r + (255 - rgb.r) * factor)));
    const g = Math.min(255, Math.max(0, Math.round(rgb.g + (255 - rgb.g) * factor)));
    const b = Math.min(255, Math.max(0, Math.round(rgb.b + (255 - rgb.b) * factor)));
    
    return rgbToHex(r, g, b);
}

// Device detection utilities
function isMobile() {
    return window.innerWidth <= 768 || /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

function isTablet() {
    return window.innerWidth > 768 && window.innerWidth <= 1024;
}

function isDesktop() {
    return window.innerWidth > 1024;
}

function isTouchDevice() {
    return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
}

function getDeviceType() {
    if (isMobile()) return 'mobile';
    if (isTablet()) return 'tablet';
    return 'desktop';
}

// Copy to clipboard utility
async function copyToClipboard(text) {
    try {
        if (navigator.clipboard && window.isSecureContext) {
            await navigator.clipboard.writeText(text);
            return true;
        } else {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            textArea.style.top = '-999999px';
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            
            const success = document.execCommand('copy');
            document.body.removeChild(textArea);
            return success;
        }
    } catch (error) {
        console.error('Failed to copy to clipboard:', error);
        return false;
    }
}

// File utilities
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function getFileExtension(filename) {
    return filename.slice((filename.lastIndexOf('.') - 1 >>> 0) + 2);
}

function isImageFile(filename) {
    const imageExtensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'];
    const extension = getFileExtension(filename).toLowerCase();
    return imageExtensions.includes(extension);
}

// Export all utilities to global scope
window.utils = {
    showToast,
    formatDate,
    formatTime,
    formatDateTime,
    formatRelativeTime,
    isToday,
    isTomorrow,
    getDaysInMonth,
    getFirstDayOfMonth,
    formatCurrency,
    formatNumber,
    formatPercentage,
    abbreviateNumber,
    truncateString,
    capitalizeFirstLetter,
    slugify,
    generateId,
    isValidEmail,
    isValidURL,
    isValidPhoneNumber,
    validateForm,
    createElement,
    removeElement,
    toggleClass,
    hasClass,
    debounce,
    throttle,
    once,
    setLocalStorage,
    getLocalStorage,
    removeLocalStorage,
    clearExpiredLocalStorage,
    hexToRgb,
    rgbToHex,
    adjustBrightness,
    isMobile,
    isTablet,
    isDesktop,
    isTouchDevice,
    getDeviceType,
    copyToClipboard,
    formatFileSize,
    getFileExtension,
    isImageFile
};

// Also export individual functions to global scope for convenience
Object.assign(window, window.utils);

// Clean up expired localStorage items on load
document.addEventListener('DOMContentLoaded', () => {
    clearExpiredLocalStorage();
});