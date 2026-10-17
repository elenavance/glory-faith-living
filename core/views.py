"""Core pages, account flows, private journal actions, and PWA resources."""
import json

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from .models import FaithReflection, PrayerJournalEntry


def home(request):
    return render(request, "home.html", {"app_name": "GLORY", "tagline": "Faith, renewed every day"})


def sign_up(request):
    if request.user.is_authenticated:
        return redirect("journey")
    form = UserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Welcome to GLORY. Your private faith journey begins here.")
        return redirect("journey")
    return render(request, "accounts/signup.html", {"form": form})


@login_required
def journey(request):
    return render(request, "journey.html", {
        "reflections": FaithReflection.objects.filter(user=request.user),
        "prayers": PrayerJournalEntry.objects.filter(user=request.user),
    })


@login_required
@require_POST
def save_reflection(request):
    title = request.POST.get("title", "").strip()[:120]
    body = request.POST.get("body", "").strip()
    scripture_reference = request.POST.get("scripture_reference", "").strip()[:120]
    if not body:
        messages.error(request, "Write a reflection before saving.")
    elif len(body) > 4000:
        messages.error(request, "Your reflection must be 4,000 characters or fewer.")
    else:
        FaithReflection.objects.create(
            user=request.user, title=title, body=body,
            scripture_reference=scripture_reference,
        )
        messages.success(request, "Your reflection has been saved privately.")
    return redirect("journey")


@login_required
@require_POST
def save_prayer(request):
    title = request.POST.get("title", "").strip()[:120]
    body = request.POST.get("body", "").strip()
    entry_type = request.POST.get("entry_type", PrayerJournalEntry.EntryType.PRAYER)
    valid_types = {choice[0] for choice in PrayerJournalEntry.EntryType.choices}
    if entry_type not in valid_types:
        entry_type = PrayerJournalEntry.EntryType.PRAYER
    if not body:
        messages.error(request, "Write a prayer or note before saving.")
    elif len(body) > 4000:
        messages.error(request, "Your entry must be 4,000 characters or fewer.")
    else:
        PrayerJournalEntry.objects.create(
            user=request.user, title=title, body=body, entry_type=entry_type,
            is_answered=(entry_type == PrayerJournalEntry.EntryType.ANSWERED),
        )
        messages.success(request, "Your entry has been saved privately.")
    return redirect("journey")



@login_required
@require_POST
def delete_journal_entry(request, kind, entry_id):
    """Delete only an entry owned by the currently signed-in user."""
    model = FaithReflection if kind == "reflection" else PrayerJournalEntry if kind == "prayer" else None
    if model is None:
        messages.error(request, "That journal entry type is not available.")
        return redirect("journey")
    deleted, _ = model.objects.filter(user=request.user, pk=entry_id).delete()
    if deleted:
        messages.success(request, "Your journal entry has been deleted.")
    else:
        messages.error(request, "That entry was not found in your private journal.")
    return redirect("journey")


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
const CACHE = 'glory-shell-v2';
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
      if (response.ok && !new URL(req.url).pathname.startsWith('/accounts/') && !new URL(req.url).pathname.startsWith('/my-journey/')) {
        caches.open(CACHE).then(cache => cache.put(req, response.clone()));
      }
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
