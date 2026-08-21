const CACHE_NAME = 'rpi-lightning-pwa-v1';

// App shell resources to pre-cache
const PRECACHE_ASSETS = [
  '/',
  '/index.html',
  '/manifest.webmanifest',
  '/favicon.svg',
  '/pwa-icon.svg'
];

// Install Event - Pre-cache App Shell
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[Service Worker] Pre-caching App Shell');
      return cache.addAll(PRECACHE_ASSETS);
    }).then(() => self.skipWaiting())
  );
});

// Activate Event - Clean Up Old Caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          if (cache !== CACHE_NAME) {
            console.log('[Service Worker] Deleting old cache:', cache);
            return caches.delete(cache);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch Event - Network First for API GET, Cache First for Static Assets, Offline Interception for POST
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Ignore WebSockets or external non-http schemas
  if (!url.protocol.startsWith('http')) return;

  // Handle API GET Requests (Network First, Cache Fallback)
  if (url.pathname.startsWith('/api/') && request.method === 'GET') {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response && response.status === 200) {
            const responseClone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, responseClone));
          }
          return response;
        })
        .catch(async () => {
          console.log('[Service Worker] API offline, checking cache for:', url.pathname);
          const cachedResponse = await caches.match(request);
          if (cachedResponse) {
            return cachedResponse;
          }
          return new Response(
            JSON.stringify({ error: 'Offline mode', offline: true }),
            { headers: { 'Content-Type': 'application/json' }, status: 503 }
          );
        })
    );
    return;
  }

  // Handle API POST Requests (Try Network; if offline, return queued signal so Client App enqueues action)
  if (url.pathname.startsWith('/api/') && request.method === 'POST') {
    event.respondWith(
      fetch(request.clone()).catch(() => {
        console.log('[Service Worker] POST offline, intercepted:', url.pathname);
        return new Response(
          JSON.stringify({
            success: true,
            offlineQueued: true,
            message: 'Server connection offline. Action saved locally and will sync when connection returns.'
          }),
          { headers: { 'Content-Type': 'application/json' }, status: 202 }
        );
      })
    );
    return;
  }

  // Static Assets & App Shell (Stale-While-Revalidate / Network-First with Cache Fallback)
  event.respondWith(
    caches.match(request).then((cachedResponse) => {
      const fetchPromise = fetch(request)
        .then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200 && networkResponse.type === 'basic') {
            const responseClone = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, responseClone));
          }
          return networkResponse;
        })
        .catch(() => cachedResponse);

      return cachedResponse || fetchPromise;
    })
  );
});
