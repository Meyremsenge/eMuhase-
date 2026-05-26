/**
 * eMuhasebe Pro — Service Worker
 *
 * Strateji:
 *   - Statik dosyalar (CSS/JS/font/img): cache-first, ağdan güncelle (stale-while-revalidate)
 *   - Sayfalar (HTML): network-first, çevrim dışıysa cache'ten fallback
 *   - API ve Firebase istekleri: HİÇBİR ZAMAN cache'lenmez (her zaman güncel olmalı)
 */

const VERSION = 'v1.0.1';
const STATIC_CACHE  = `emuhasebe-static-${VERSION}`;
const RUNTIME_CACHE = `emuhasebe-runtime-${VERSION}`;

const PRECACHE = [
    '/',
    '/static/css/style.css',
    '/static/css/dashboard.css',
    '/static/js/db.js',
    '/static/js/ai-engine.js',
    '/static/manifest.json',
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then(cache => cache.addAll(PRECACHE).catch(() => null))
            .then(() => self.skipWaiting())
    );
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys()
            .then(keys => Promise.all(
                keys
                    .filter(k => k !== STATIC_CACHE && k !== RUNTIME_CACHE)
                    .map(k => caches.delete(k))
            ))
            .then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', (event) => {
    const req = event.request;
    const url = new URL(req.url);

    // Sadece GET cache'lenir
    if (req.method !== 'GET') return;

    // API ve Firebase: cache yok
    if (url.pathname.startsWith('/api/') ||
        url.hostname.includes('firebaseio.com') ||
        url.hostname.includes('firebasedatabase.app') ||
        url.hostname.includes('googleapis.com')) {
        return; // default browser handling
    }

    // HTML navigasyonu → network-first
    if (req.mode === 'navigate' || (req.headers.get('accept') || '').includes('text/html')) {
        event.respondWith(
            fetch(req)
                .then(resp => {
                    if (resp.ok) {
                        const copy = resp.clone();
                        caches.open(RUNTIME_CACHE).then(c => c.put(req, copy));
                    }
                    return resp;
                })
                .catch(() => caches.match(req).then(c => c || caches.match('/')))
        );
        return;
    }

    // Statik kaynaklar → stale-while-revalidate
    event.respondWith(
        caches.match(req).then(cached => {
            const fetchPromise = fetch(req)
                .then(resp => {
                    if (resp.ok && resp.type !== 'opaque') {
                        const copy = resp.clone();
                        caches.open(STATIC_CACHE).then(c => c.put(req, copy));
                    }
                    return resp;
                })
                .catch(() => cached);
            return cached || fetchPromise;
        })
    );
});
