/* On Record — service worker.
   NETWORK-FIRST for the document, the data, the feed and the calendar, so a
   fresh nightly build is served the instant the device is online; the cache is
   only ever the OFFLINE FALLBACK, never the default served copy. Each nightly
   build changes BUILD, which changes the cache name and this file byte-for-byte,
   so the browser always detects an update and every older cache is purged — no
   stale copy can linger (the trap that must never recur). There is no push and
   no notification code here: the site cannot send notifications. */
<<<<<<< HEAD
const BUILD = "20260811035627-c470a255";
=======
const BUILD = "20260807043339-4e9af4d6";
>>>>>>> 6ec19ed (The opening finally says what the site is — the copy was never the defect, the order was)
const CACHE = "onrecord-" + BUILD;
const SHELL = ["./", "./index.html", "./reuse.html", "./manifest.webmanifest",
  "./data/perday-seville.json", "./data/impact.json",   // site-data is inlined into index.html; only these are fetched at runtime
  "./og/icon-192.png", "./og/icon-512.png", "./og/icon-512-maskable.png"];

self.addEventListener("install", function (e) {
  e.waitUntil(caches.open(CACHE).then(function (c) {
    return Promise.all(SHELL.map(function (u) {
      return fetch(u, { cache: "no-cache" }).then(function (r) { if (r && r.ok) return c.put(u, r); }).catch(function () {});
    }));
  }));
  self.skipWaiting();
});

self.addEventListener("activate", function (e) {
  e.waitUntil((async function () {
    var keys = await caches.keys();
    await Promise.all(keys.filter(function (k) { return k !== CACHE; }).map(function (k) { return caches.delete(k); }));
    await self.clients.claim();
  })());
});

function isFresh(u) {
  return u.pathname === "/" || u.pathname.endsWith("/") || u.pathname.endsWith("/index.html") ||
    u.pathname.endsWith(".json") || u.pathname.endsWith("feed.xml") || u.pathname.endsWith("on-record.ics");
}
function isNav(req, u) {
  return req.mode === "navigate" || u.pathname.endsWith("/index.html") || u.pathname.endsWith("/") || u.pathname === "/";
}
async function tell(type) {
  var cs = await self.clients.matchAll();
  cs.forEach(function (c) { try { c.postMessage({ type: type, built: BUILD }); } catch (e) {} });
}

self.addEventListener("fetch", function (e) {
  var req = e.request, u = new URL(req.url);
  if (req.method !== "GET" || u.origin !== location.origin) return;
  if (isFresh(u)) {
    e.respondWith((async function () {
      try {
        var net = await fetch(req, { cache: "no-cache" });       // never let the HTTP cache interpose stale bytes
        if (net && net.ok) {                                   // only a good response may become the offline fallback — never a 4xx/5xx or captive-portal page
          var c = await caches.open(CACHE); c.put(req, net.clone());
          if (isNav(req, u)) tell("fresh");
        }
        return net;
      } catch (err) {
        var hit = await caches.match(req);                     // offline fallback only
        if (hit) { if (isNav(req, u)) tell("fromcache"); return hit; }
        var idx = await caches.match("./index.html");
        return idx || Response.error();
      }
    })());
    return;
  }
  // everything else (icons) — cache-first, safe because BUILD busts the whole cache on any rebuild
  e.respondWith(caches.match(req).then(function (h) { return h || fetch(req); }));
});
