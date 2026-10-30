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



@require_POST
def guidance(request):
    """Offer a small, curated Scripture reflection without storing the user's question."""
    question = request.POST.get("question", "").strip()
    if not question:
        return JsonResponse({"error": "Write a question first so we can find a helpful reflection."}, status=400)
    if len(question) > 700:
        return JsonResponse({"error": "Please keep your question to 700 characters or fewer."}, status=400)

    normalized = question.casefold()
    topics = [
        (("anxious", "anxiety", "worry", "worried", "fear", "afraid", "stress", "panic"),
         "Philippians 4:6–7", "Be careful for nothing; but in every thing by prayer and supplication with thanksgiving let your requests be made known unto God.",
         "You do not have to solve everything at once. Name what is weighing on you, take one slow breath, and consider one small next step you can take today. If this is overwhelming or persistent, reach out to someone you trust or a qualified professional."),
        (("grief", "grieving", "death", "died", "loss", "mourning", "heartbroken"),
         "Psalm 34:18", "The LORD is nigh unto them that are of a broken heart; and saveth such as be of a contrite spirit.",
         "Grief does not need to be rushed or hidden. Give yourself permission to mourn, accept practical care, and remember that asking for help is not a failure of faith."),
        (("relationship", "marriage", "partner", "boyfriend", "girlfriend", "love", "dating", "family"),
         "1 Corinthians 13:4", "Charity suffereth long, and is kind; charity envieth not; charity vaunteth not itself, is not puffed up.",
         "Love includes kindness, patience, honesty, and respect. Reflect on what a caring next step could look like while keeping healthy boundaries and your safety in view."),
        (("work", "career", "purpose", "job", "calling", "future", "direction"),
         "Colossians 3:23", "And whatsoever ye do, do it heartily, as to the Lord, and not unto men;",
         "You may not see the whole path yet. Focus on the next faithful, practical action, seek wise counsel, and allow room for your plans to develop."),
        (("money", "debt", "finance", "financial", "bills", "poor", "wealth"),
         "Proverbs 3:5", "Trust in the LORD with all thine heart; and lean not unto thine own understanding.",
         "Faith can support patience and wise stewardship, but it does not promise a particular financial outcome. Review the facts, avoid rushed decisions, and seek qualified financial advice when needed."),
        (("forgive", "forgiveness", "resent", "anger", "betray", "betrayed"),
         "Ephesians 4:32", "And be ye kind one to another, tenderhearted, forgiving one another, even as God for Christ's sake hath forgiven you.",
         "Forgiveness can be a process, not an instant feeling. It does not mean excusing harm, removing boundaries, or returning to an unsafe situation."),
        (("lonely", "loneliness", "alone", "isolated", "friendless"),
         "Deuteronomy 31:8", "And the LORD, he it is that doth go before thee; he will be with thee, he will not fail thee, neither forsake thee.",
         "Feeling alone can be painful, even for a person of faith. Consider reaching out to one trusted person or a supportive faith community; connection can begin with a small message."),
    ]
    selected = next((item for item in topics if any(word in normalized for word in item[0])), None)
    if selected is None:
        selected = ("", "James 1:5", "If any of you lack wisdom, let him ask of God, that giveth to all men liberally, and upbraideth not; and it shall be given him.",
                    "Bring your question honestly to prayer, consider what is within your control, and seek the perspective of a wise and trusted person. You do not need to decide everything today.")
    return JsonResponse({
        "reference": selected[1],
        "passage": selected[2],
        "reflection": selected[3],
        "note": "A Scripture-based reflection for consideration, not a personal prophecy or a substitute for pastoral or professional support.",
        "stored": False,
    })


@require_POST
def prepare_reflection_save(request):
    """Save an explicitly selected guidance result or hold it for guest signup."""
    reference = request.POST.get("scripture_reference", "").strip()[:120]
    passage = request.POST.get("passage", "").strip()
    reflection = request.POST.get("reflection", "").strip()
    body = f"{passage}\n\n{reflection}"
    if not reference or not passage or not reflection or len(body) > 4000:
        return JsonResponse({"error": "This reflection could not be saved. Please try again."}, status=400)

    title = f"Scripture reflection: {reference}"[:120]
    if request.user.is_authenticated:
        FaithReflection.objects.create(
            user=request.user,
            title=title,
            body=body,
            scripture_reference=reference,
        )
        return JsonResponse({"ok": True, "saved": True})

    request.session["pending_guidance_reflection"] = {
        "title": title,
        "body": body,
        "scripture_reference": reference,
    }
    request.session.set_expiry(3600)
    return JsonResponse({"ok": True, "saved": False, "signup_url": "/accounts/signup/"})


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
