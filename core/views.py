"""Core pages, account flows, private journal actions, and PWA resources."""
import json

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from .models import FaithReflection, PrayerJournalEntry

User = get_user_model()

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, label=_("Email"))

    class Meta(UserCreationForm.Meta):
        fields = ("username", "email")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user

def home(request):
    return render(request, "home.html", {"app_name": "GLORY", "tagline": _("Faith, renewed every day")})

def sign_up(request):
    if request.user.is_authenticated:
        return redirect("journey")
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, _("Welcome to GLORY. Your private faith journey begins here."))
        return redirect("journey")
    return render(request, "accounts/signup.html", {"form": form})

@login_required
def journey(request):
    reflections = FaithReflection.objects.filter(user=request.user)
    prayers = PrayerJournalEntry.objects.filter(user=request.user)
    reflections_page = Paginator(reflections, 20).get_page(request.GET.get("r_page"))
    prayers_page = Paginator(prayers, 20).get_page(request.GET.get("p_page"))
    return render(request, "journey.html", {
        "reflections": reflections_page,
        "prayers": prayers_page,
    })

@require_POST
def guidance(request):
    """Offer a small, curated Scripture reflection without storing the user's question."""
    question = request.POST.get("question", "").strip()
    if not question:
        return JsonResponse({"error": _("Write a question first so we can find a helpful reflection.")}, status=400)
    if len(question) > 700:
        return JsonResponse({"error": _("Please keep your question to 700 characters or fewer.")}, status=400)

    normalized = question.casefold()
    topics = [
        (("anxious", "anxiety", "worry", "worried", "fear", "afraid", "stress", "panic", "cemas", "khawatir", "takut", "stres", "panik", "gelisah"),
         "Philippians 4:6–7", "Be careful for nothing; but in every thing by prayer and supplication with thanksgiving let your requests be made known unto God.",
         _("You do not have to solve everything at once. Name what is weighing on you, take one slow breath, and consider one small next step you can take today. If this is overwhelming or persistent, reach out to someone you trust or a qualified professional.")),
        (("grief", "grieving", "death", "died", "loss", "mourning", "heartbroken", "duka", "berduka", "meninggal", "kehilangan", "sedih", "patah hati"),
         "Psalm 34:18", "The LORD is nigh unto them that are of a broken heart; and saveth such as be of a contrite spirit.",
         _("Grief does not need to be rushed or hidden. Give yourself permission to mourn, accept practical care, and remember that asking for help is not a failure of faith.")),
        (("relationship", "marriage", "partner", "boyfriend", "girlfriend", "love", "dating", "family", "hubungan", "pernikahan", "pasangan", "pacar", "cinta", "keluarga"),
         "1 Corinthians 13:4", "Charity suffereth long, and is kind; charity envieth not; charity vaunteth not itself, is not puffed up.",
         _("Love includes kindness, patience, honesty, and respect. Reflect on what a caring next step could look like while keeping healthy boundaries and your safety in view.")),
        (("work", "career", "purpose", "job", "calling", "future", "direction", "pekerjaan", "karier", "karir", "panggilan", "masa depan", "tujuan"),
         "Colossians 3:23", "And whatsoever ye do, do it heartily, as to the Lord, and not unto men;",
         _("You may not see the whole path yet. Focus on the next faithful, practical action, seek wise counsel, and allow room for your plans to develop.")),
        (("money", "debt", "finance", "financial", "bills", "poor", "wealth", "uang", "hutang", "keuangan", "tagihan", "miskin", "kaya", "finansial"),
         "Proverbs 3:5", "Trust in the LORD with all thine heart; and lean not unto thine own understanding.",
         _("Faith can support patience and wise stewardship, but it does not promise a particular financial outcome. Review the facts, avoid rushed decisions, and seek qualified financial advice when needed.")),
        (("forgive", "forgiveness", "resent", "anger", "betray", "betrayed", "maaf", "memaafkan", "marah", "dendam", "dikhianati", "sakit hati"),
         "Ephesians 4:32", "And be ye kind one to another, tenderhearted, forgiving one another, even as God for Christ's sake hath forgiven you.",
         _("Forgiveness can be a process, not an instant feeling. It does not mean excusing harm, removing boundaries, or returning to an unsafe situation.")),
        (("lonely", "loneliness", "alone", "isolated", "friendless", "kesepian", "sendiri", "terisolasi", "sepi", "tidak punya teman"),
         "Deuteronomy 31:8", "And the LORD, he it is that doth go before thee; he will be with thee, he will not fail thee, neither forsake thee.",
         _("Feeling alone can be painful, even for a person of faith. Consider reaching out to one trusted person or a supportive faith community; connection can begin with a small message.")),
    ]
    selected = next((item for item in topics if any(word in normalized for word in item[0])), None)
    if selected is None:
        selected = ("", "James 1:5", "If any of you lack wisdom, let him ask of God, that giveth to all men liberally, and upbraideth not; and it shall be given him.",
                    _("Bring your question honestly to prayer, consider what is within your control, and seek the perspective of a wise and trusted person. You do not need to decide everything today."))
    return JsonResponse({
        "reference": selected[1],
        "passage": selected[2],
        "reflection": selected[3],
        "note": _("A Scripture-based reflection for consideration, not a personal prophecy or a substitute for pastoral or professional support."),
        "stored": False,
    })

@login_required
@require_POST
def save_reflection(request):
    title = request.POST.get("title", "").strip()[:120]
    body = request.POST.get("body", "").strip()
    scripture_reference = request.POST.get("scripture_reference", "").strip()[:120]
    if not body:
        messages.error(request, _("Write a reflection before saving."))
    elif len(body) > 4000:
        messages.error(request, _("Your reflection must be 4,000 characters or fewer."))
    else:
        FaithReflection.objects.create(
            user=request.user, title=title, body=body,
            scripture_reference=scripture_reference,
        )
        messages.success(request, _("Your reflection has been saved privately."))
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
        messages.error(request, _("Write a prayer or note before saving."))
    elif len(body) > 4000:
        messages.error(request, _("Your entry must be 4,000 characters or fewer."))
    else:
        PrayerJournalEntry.objects.create(
            user=request.user, title=title, body=body, entry_type=entry_type,
            is_answered=(entry_type == PrayerJournalEntry.EntryType.ANSWERED),
        )
        messages.success(request, _("Your entry has been saved privately."))
    return redirect("journey")

@login_required
@require_POST
def delete_journal_entry(request, kind, entry_id):
    """Delete only an entry owned by the currently signed-in user."""
    model = FaithReflection if kind == "reflection" else PrayerJournalEntry if kind == "prayer" else None
    if model is None:
        messages.error(request, _("That journal entry type is not available."))
        return redirect("journey")
    deleted, _ = model.objects.filter(user=request.user, pk=entry_id).delete()
    if deleted:
        messages.success(request, _("Your journal entry has been deleted."))
    else:
        messages.error(request, _("That entry was not found in your private journal."))
    return redirect("journey")

@login_required
@require_POST
def delete_account(request):
    """【entity-Play Store¦canonical_name=Play Store】 requirement: user can delete their account + all private data."""
    confirm = request.POST.get("confirm", "")
    if confirm != "DELETE":
        messages.error(request, _("Type DELETE to confirm account deletion."))
        return redirect("journey")
    user = request.user
    user.delete()
    messages.success(request, _("Your account and all private journal entries have been deleted."))
    return redirect("home")

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
        "icons": [
            {"src": "/static/images/glory-mark.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "any maskable"},
            {"src": "/static/images/glory-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": "/static/images/glory-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
        ],
        "categories": ["lifestyle", "education"],
        "lang": "en"
    }
    return HttpResponse(json.dumps(data), content_type="application/manifest+json")

@require_GET
@never_cache
def service_worker(request):
    js = """
const CACHE = 'glory-shell-v3';
const CORE = ['/', '/offline/', '/manifest.webmanifest', '/static/css/glory.css', '/static/js/glory.js'];
const PRIVATE_PREFIXES = ['/accounts/', '/my-journey/', '/admin/'];
function isPrivate(url) {
  const path = new URL(url).pathname;
  return PRIVATE_PREFIXES.some(p => path.startsWith(p));
}
self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(CORE)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key !== CACHE).map(key => caches.delete(key)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET' || new URL(req.url).origin !== self.location.origin) return;
  if (isPrivate(req.url)) return;
  if (req.mode === 'navigate') {
    event.respondWith(fetch(req).then(response => {
      if (response.ok) {
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
