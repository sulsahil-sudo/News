const CACHE = "news-v1";
self.addEventListener("install", function(e) { self.skipWaiting(); });
self.addEventListener("activate", function(e) { e.waitUntil(clients.claim()); });
self.addEventListener("fetch", function(e) {
  var url = new URL(e.request.url);
  if(url.pathname.indexOf("news.json") !== -1){
    e.respondWith(fetch(e.request).then(function(r){
      var copy = r.clone();
      caches.open(CACHE).then(function(c){ c.put(e.request, copy); });
      return r;
    }).catch(function(){ return caches.match(e.request); }));
    return;
  }
  e.respondWith(caches.match(e.request).then(function(r){ return r || fetch(e.request); }));
});
