/* درب الثراء — عامل الخدمة: يعمل بلا إنترنت بعد أول فتح */
const VER = "darb-city-of-opportunity-v3";
const SHELL = [
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./styles/identity.css",
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
  "./art/identity/goods-sheet.png"
];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(VER).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys()
    .then(ks => Promise.all(ks.filter(k => k !== VER).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return;           // STUN وغيره خارج النطاق: لا نتدخل
  if (req.mode === "navigate") {                        // الصفحة: الشبكة أولاً ليصل التحديث، وإلا النسخة المحفوظة
    e.respondWith(fetch(req).then(r => {
      const copy = r.clone(); caches.open(VER).then(c => c.put("./index.html", copy)); return r;
    }).catch(() => caches.match("./index.html")));
    return;
  }
  e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(r => {
    if (r.ok) { const copy = r.clone(); caches.open(VER).then(c => c.put(req, copy)); }
    return r;
  })));
});
