/**
 * PALOS Web Dashboard - Service Worker
 * Provides offline capabilities and caching for PWA functionality
 */

const CACHE_NAME = 'palos-v1.0.0';
const STATIC_CACHE_NAME = 'palos-static-v1.0.0';
const DYNAMIC_CACHE_NAME = 'palos-dynamic-v1.0.0';
const API_CACHE_NAME = 'palos-api-v1.0.0';

// Files to cache for offline use
const STATIC_FILES = [
    '/static/web/',
    '/static/web/index.html',
    '/static/web/manifest.json',
    '/static/web/css/styles.css',
    '/static/web/css/mobile.css',
    '/static/web/css/themes.css',
    '/static/web/js/app.js',
    '/static/web/js/api.js',
    '/static/web/js/websocket.js',
    '/static/web/js/utils.js',
    '/static/web/js/auth.js',
    '/static/web/js/dashboard.js',
    '/static/web/js/calendar.js',
    '/static/web/js/tasks.js',
    '/static/web/js/health.js',
    '/static/web/js/finance.js',
    '/static/web/js/social.js',
    '/static/web/js/agents.js',
    '/static/web/js/notifications.js'
];

// API endpoints to cache
const CACHEABLE_API_PATTERNS = [
    /\/api\/dashboard\/summary/,
    /\/api\/dashboard\/stats/,
    /\/api\/dashboard\/quick-actions/,
    /\/api\/auth\/validate/
];

// API endpoints that should never be cached
const UNCACHEABLE_API_PATTERNS = [
    /\/api\/auth\/login/,
    /\/api\/auth\/logout/,
    /\/api\/auth\/refresh/,
    /\/ws\//
];

// Maximum age for cached API responses (in milliseconds)
const API_CACHE_MAX_AGE = 5 * 60 * 1000; // 5 minutes
const STATIC_CACHE_MAX_AGE = 24 * 60 * 60 * 1000; // 24 hours

// Install event - cache static files
self.addEventListener('install', event => {
    console.log('🔧 Service Worker installing...');
    
    event.waitUntil(
        Promise.all([
            caches.open(STATIC_CACHE_NAME).then(cache => {
                console.log('📦 Caching static files...');
                return cache.addAll(STATIC_FILES);
            }),
            caches.open(API_CACHE_NAME),
            caches.open(DYNAMIC_CACHE_NAME)
        ])
        .then(() => {
            console.log('✅ Service Worker installed successfully');
            return self.skipWaiting();
        })
        .catch(error => {
            console.error('❌ Service Worker installation failed:', error);
        })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
    console.log('🚀 Service Worker activating...');
    
    event.waitUntil(
        caches.keys()
        .then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    // Delete old caches
                    if (cacheName !== STATIC_CACHE_NAME && 
                        cacheName !== DYNAMIC_CACHE_NAME && 
                        cacheName !== API_CACHE_NAME) {
                        console.log('🗑️ Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
        .then(() => {
            console.log('✅ Service Worker activated successfully');
            return self.clients.claim();
        })
    );
});

// Fetch event - handle network requests
self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Skip non-GET requests and chrome-extension requests
    if (request.method !== 'GET' || url.protocol === 'chrome-extension:') {
        return;
    }
    
    // Handle different types of requests
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(handleApiRequest(request));
    } else if (url.pathname.startsWith('/static/web/')) {
        event.respondWith(handleStaticRequest(request));
    } else if (url.pathname === '/' || url.pathname === '/static/web/' || url.pathname === '/static/web/index.html') {
        event.respondWith(handleAppShellRequest(request));
    } else {
        event.respondWith(handleDynamicRequest(request));
    }
});

// Handle API requests with cache-first strategy for specific endpoints
async function handleApiRequest(request) {
    const url = new URL(request.url);
    
    // Check if this API endpoint should not be cached
    if (UNCACHEABLE_API_PATTERNS.some(pattern => pattern.test(url.pathname))) {
        return handleNetworkOnly(request);
    }
    
    // Check if this API endpoint is cacheable
    const isCacheable = CACHEABLE_API_PATTERNS.some(pattern => pattern.test(url.pathname));
    
    if (isCacheable) {
        return handleCacheFirstWithExpiry(request, API_CACHE_NAME, API_CACHE_MAX_AGE);
    } else {
        return handleNetworkFirstWithCache(request, API_CACHE_NAME);
    }
}

// Handle static files with cache-first strategy
async function handleStaticRequest(request) {
    return handleCacheFirst(request, STATIC_CACHE_NAME);
}

// Handle app shell (main HTML) with network-first strategy
async function handleAppShellRequest(request) {
    try {
        // Try network first for the latest version
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            // Update cache with latest version
            const cache = await caches.open(STATIC_CACHE_NAME);
            cache.put(request, networkResponse.clone());
            return networkResponse;
        } else {
            throw new Error('Network response not ok');
        }
    } catch (error) {
        // Fall back to cache
        const cachedResponse = await caches.match('/static/web/index.html');
        if (cachedResponse) {
            return cachedResponse;
        } else {
            return new Response('App offline', { status: 503 });
        }
    }
}

// Handle dynamic content with network-first strategy
async function handleDynamicRequest(request) {
    return handleNetworkFirstWithCache(request, DYNAMIC_CACHE_NAME);
}

// Cache strategies
async function handleCacheFirst(request, cacheName) {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
        return cachedResponse;
    }
    
    try {
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            const cache = await caches.open(cacheName);
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    } catch (error) {
        console.error('Network and cache miss for:', request.url);
        return new Response('Offline', { status: 503 });
    }
}

async function handleCacheFirstWithExpiry(request, cacheName, maxAge) {
    const cache = await caches.open(cacheName);
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
        const cachedDate = new Date(cachedResponse.headers.get('sw-cache-date') || 0);
        const isExpired = Date.now() - cachedDate.getTime() > maxAge;
        
        if (!isExpired) {
            return cachedResponse;
        }
    }
    
    try {
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            // Add cache date header
            const responseToCache = new Response(networkResponse.body, {
                status: networkResponse.status,
                statusText: networkResponse.statusText,
                headers: {
                    ...Object.fromEntries(networkResponse.headers.entries()),
                    'sw-cache-date': new Date().toISOString()
                }
            });
            
            cache.put(request, responseToCache.clone());
            return responseToCache;
        } else {
            return cachedResponse || networkResponse;
        }
    } catch (error) {
        return cachedResponse || new Response('Offline', { status: 503 });
    }
}

async function handleNetworkFirstWithCache(request, cacheName) {
    try {
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            const cache = await caches.open(cacheName);
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    } catch (error) {
        const cachedResponse = await caches.match(request);
        return cachedResponse || new Response('Offline', { status: 503 });
    }
}

async function handleNetworkOnly(request) {
    try {
        return await fetch(request);
    } catch (error) {
        return new Response('Network error', { status: 503 });
    }
}

// Background sync for queued API requests
self.addEventListener('sync', event => {
    console.log('🔄 Background sync triggered:', event.tag);
    
    if (event.tag === 'background-sync-api-requests') {
        event.waitUntil(syncQueuedRequests());
    }
});

async function syncQueuedRequests() {
    try {
        // Get queued requests from IndexedDB or localStorage
        const clients = await self.clients.matchAll();
        
        clients.forEach(client => {
            client.postMessage({
                type: 'sync-queued-requests'
            });
        });
        
        console.log('✅ Background sync completed');
    } catch (error) {
        console.error('❌ Background sync failed:', error);
    }
}

// Push notification handling
self.addEventListener('push', event => {
    console.log('📱 Push notification received');
    
    if (!event.data) {
        return;
    }
    
    try {
        const data = event.data.json();
        const options = {
            body: data.body || 'You have a new notification',
            icon: '/static/web/icons/icon-192x192.png',
            badge: '/static/web/icons/icon-72x72.png',
            vibrate: [100, 50, 100],
            data: data.data || {},
            actions: [
                {
                    action: 'view',
                    title: 'View',
                    icon: '/static/web/icons/action-view.png'
                },
                {
                    action: 'dismiss',
                    title: 'Dismiss',
                    icon: '/static/web/icons/action-dismiss.png'
                }
            ]
        };
        
        event.waitUntil(
            self.registration.showNotification(data.title || 'PALOS', options)
        );
    } catch (error) {
        console.error('Failed to show push notification:', error);
    }
});

// Notification click handling
self.addEventListener('notificationclick', event => {
    console.log('🔔 Notification clicked:', event.notification.tag);
    
    event.notification.close();
    
    if (event.action === 'dismiss') {
        return;
    }
    
    const urlToOpen = event.notification.data?.url || '/static/web/index.html';
    
    event.waitUntil(
        self.clients.matchAll({
            type: 'window',
            includeUncontrolled: true
        })
        .then(clients => {
            // Check if app is already open
            for (const client of clients) {
                if (client.url.includes('/static/web/') && 'focus' in client) {
                    client.postMessage({
                        type: 'notification-click',
                        data: event.notification.data
                    });
                    return client.focus();
                }
            }
            
            // Open new window if app is not open
            if (self.clients.openWindow) {
                return self.clients.openWindow(urlToOpen);
            }
        })
    );
});

// Message handling from clients
self.addEventListener('message', event => {
    console.log('💬 Message received from client:', event.data);
    
    if (event.data && event.data.type === 'skip-waiting') {
        self.skipWaiting();
    } else if (event.data && event.data.type === 'cache-update') {
        // Force update specific cache
        handleCacheUpdate(event.data.url);
    } else if (event.data && event.data.type === 'clear-cache') {
        // Clear all caches
        handleClearCache();
    }
});

async function handleCacheUpdate(url) {
    try {
        const cache = await caches.open(DYNAMIC_CACHE_NAME);
        await cache.delete(url);
        console.log('🔄 Cache updated for:', url);
    } catch (error) {
        console.error('Failed to update cache:', error);
    }
}

async function handleClearCache() {
    try {
        const cacheNames = await caches.keys();
        await Promise.all(
            cacheNames.map(cacheName => caches.delete(cacheName))
        );
        console.log('🗑️ All caches cleared');
    } catch (error) {
        console.error('Failed to clear caches:', error);
    }
}

// Periodic background fetch (experimental)
self.addEventListener('periodicsync', event => {
    console.log('⏰ Periodic sync triggered:', event.tag);
    
    if (event.tag === 'background-data-sync') {
        event.waitUntil(performBackgroundDataSync());
    }
});

async function performBackgroundDataSync() {
    try {
        // Sync critical data in the background
        const criticalEndpoints = [
            '/api/dashboard/summary',
            '/api/dashboard/notifications'
        ];
        
        const cache = await caches.open(API_CACHE_NAME);
        
        for (const endpoint of criticalEndpoints) {
            try {
                const response = await fetch(endpoint);
                if (response.ok) {
                    await cache.put(endpoint, response.clone());
                }
            } catch (error) {
                console.warn('Failed to sync endpoint:', endpoint, error);
            }
        }
        
        console.log('✅ Background data sync completed');
    } catch (error) {
        console.error('❌ Background data sync failed:', error);
    }
}

// Cleanup old cache entries periodically
setInterval(async () => {
    try {
        const cacheNames = [API_CACHE_NAME, DYNAMIC_CACHE_NAME];
        
        for (const cacheName of cacheNames) {
            const cache = await caches.open(cacheName);
            const requests = await cache.keys();
            
            // Limit cache size to 50 entries per cache
            if (requests.length > 50) {
                const requestsToDelete = requests.slice(0, requests.length - 50);
                await Promise.all(
                    requestsToDelete.map(request => cache.delete(request))
                );
                console.log(`🧹 Cleaned up ${requestsToDelete.length} old cache entries from ${cacheName}`);
            }
        }
    } catch (error) {
        console.error('Cache cleanup failed:', error);
    }
}, 60 * 60 * 1000); // Run every hour

console.log('🎯 PALOS Service Worker loaded successfully');