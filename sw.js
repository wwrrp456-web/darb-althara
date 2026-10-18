/* درب الثراء — عامل الخدمة: يعمل بلا إنترنت بعد أول فتح */
const VER = "darb-light-illustrated-v10";
const SHELL = [
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./styles/identity.css?v=10",
  "./styles/tabletop.css?v=10",
  "./styles/illustrated.css?v=10",
  "./scripts/identity.js",
  "./art/identity/icons-sheet.png",
  "./art/identity/cards-sheet.png",
  "./art/identity/reactions-sheet.png",
  "./scripts/tabletop.js?v=10",
  "./scripts/board-camera.js?v=10",
  "./fonts/Tajawal-Regular.ttf",
  "./fonts/Tajawal-Bold.ttf",
  "./icons/brand-mark.svg",
  "./icons/game-icons.svg",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./icons/maskable-512.png",
  "./icons/apple-touch-icon.png",
  "./icons/favicon-64.png",
  "./art/identity/clear.svg",
  "./art/identity/world-sheet.png",
  "./art/identity/characters-sheet.png",
  "./art/identity/goods-sheet.png",
  "./art/identity/pawns-sheet.png",
  "./art/identity/tabletop-park.png",
  "./art/identity/tabletop-city.png"
];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(VER).then(c => c.addAll(SHELL.map(url => new Request(url, {cache: "reload"})))).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys()
    .then(ks => Promise.all(ks.filter(k => k !== VER).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET" || new URL(req.url).origin !== location.origin) return;
  e.respondWith((async () => {
    // Use this release's cache only, including while an older worker is retiring.
    const cache = await caches.open(VER);
    if (req.mode === "navigate") {
      try {
        const response = await fetch(req);
        if (response.ok) e.waitUntil(cache.put("./index.html", response.clone()));
        return response;
      } catch (_) {
        return await cache.match("./index.html") || Response.error();
      }
    }
    const hit = await cache.match(req);
    if (hit) return hit;
    const response = await fetch(req);
    if (response.ok) e.waitUntil(cache.put(req, response.clone()));
    return response;
  })());
});
