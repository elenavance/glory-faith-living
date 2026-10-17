"""Core views, health endpoint, and PWA resources."""
import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

def home(request):
    return render(request, "home.html", {"app_name": "GLORY", "tagline": "Faith, renewed every day"})

@require_GET
def health(request):
    return JsonResponse({"status": "ok", "app": "glory-faith-living"})

@require_GET
def manifest(request):
    data = {
        "id": "/", "name": "GLORY — Faith & Living", "short_name": "GLORY",
        "description": "A daily Christian companion for Scripture, prayer, and life.",
        "start_url": "/", "scope": "/", "display": "standalone",
        "background_color": "#0a1020", "theme_color": "#0a1020",
        "orientation": "portrait-primary",
        "icons": [{"src": "/static/images/glory-mark.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "any maskable"}],
        "categories": ["lifestyle", "education"],
        "lang": "en"
    }
    return HttpResponse(json.dumps(data), content_type="application/manifest+json")

@require_GET
@never_cache
def service_worker(request):
    js = """
const CACHE = 'glory-shell-v1';
const CORE = ['/', '/offline/', '/manifest.webmanifest', '/static/css/glory.css', '/static/js/glory.js'];
self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(CORE)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key !== CACHE).map(key => caches.delete(key)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET' || new URL(req.url).origin !== self.location.origin) return;
  if (req.mode === 'navigate') {
    event.respondWith(fetch(req).then(response => {
      if (response.ok) caches.open(CACHE).then(cache => cache.put(req, response.clone()));
      return response;
    }).catch(async () => (await caches.match(req)) || (await caches.match('/offline/'))));
    return;
  }
  event.respondWith(caches.match(req).then(cached => cached || fetch(req).then(response => {
    if (response.ok) caches.open(CACHE).then(cache => cache.put(req, response.clone()));
    return response;
  })));
});
"""
    return HttpResponse(js, content_type="application/javascript")
