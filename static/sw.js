self.addEventListener('install', event => {
    event.waitUntil(
        caches.open('product-cache').then(cache => {
            return cache.addAll([
                '/',
                '/static/styles.css',
                '/static/manifest.json'
            ]);
        })
    );
});

self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request).then(response => {
            return response || fetch(event.request);
        })
    );
});
