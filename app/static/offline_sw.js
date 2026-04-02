// CACHE_NAME is dynamically injected by the server based on offline_scoreboard.html
// mtime — so it auto-bumps on every deployment without manual version changes.
const CACHE_NAME = 'ea-offline-v115'; // replaced at serve-time by scoreboard.py

// Only cache static assets. The scoreboard HTML is intentionally excluded —
// it must always be fetched fresh from the server (server sends no-store headers).
const PRECACHE_URLS = [
  '/scoreboard/manifest.webmanifest',
  '/static/ea-icon.svg'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(PRECACHE_URLS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Data API — network-first, fall back to cache for true offline use.
  if (url.pathname.startsWith('/scoreboard/offline-data')) {
    event.respondWith(
      fetch(event.request).catch(() => caches.match(event.request))
    );
    return;
  }

  // Navigation (page loads) — always network-first, NEVER cache the response.
  // The server sends Cache-Control: no-store on the HTML. We honour that here
  // because the SW Cache API bypasses HTTP cache headers if we call cache.put().
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).catch(() => caches.match('/scoreboard/offline'))
    );
    return;
  }

  // Static assets — cache-first, update cache on miss.
  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) return cached;
      return fetch(event.request)
        .then((response) => {
          if (response.ok) {
            const copy = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
          }
          return response;
        })
        .catch(() => cached);
    })
  );
});
