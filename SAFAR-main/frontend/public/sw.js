const CACHE = "safar-v1";
const ASSETS = ["/", "/index.html", "/data/polar.geojson"];
self.addEventListener("install", event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(ASSETS)));
});
self.addEventListener("fetch", event => {
  event.respondWith(
    caches.match(event.request).then(cached => cached || fetch(event.request).catch(() => caches.match("/")))
  );
});
