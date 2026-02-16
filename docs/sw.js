const CACHE = 'life-dashboard-v1';
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(['./', 'index.html'])));
  self.skipWaiting();
});
self.addEventListener('fetch', e => {
  e.respondWith(
    fetch(e.request).then(r => {
      const rc = r.clone();
      caches.open(CACHE).then(c => c.put(e.request, rc));
      return r;
    }).catch(() => caches.match(e.request))
  );
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))));
});
