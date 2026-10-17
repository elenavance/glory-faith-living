# GLORY — Faith & Living

A premium, mobile-first Christian companion for Scripture, prayer, biblical wisdom, and everyday faith.

## Product vision

Help people grow closer to God through Scripture, prayer, reflection, and practical biblical wisdom. The product welcomes Christians across denominations while distinguishing shared Christian content from tradition-specific practices.

## Experience

- **Daily Word:** Scripture, context, reflection, and practical application.
- **Prayer & Devotion:** a quiet prayer experience plus a personal prayer, gratitude, and answered-prayer journal.
- **Biblical Wisdom:** reflections for relationships, family, work, finances, hardship, forgiveness, and growth.
- **Ask for Guidance:** a clearly labelled preview for Scripture-informed reflection; personalized AI guidance is not connected yet.
- **My Faith Journey:** private account, saved reflections with optional Scripture references, and a personal prayer journal.
- **PWA:** installable web app shell with offline fallback.
- **Language preference:** English, Bahasa Indonesia, and Chinese language choices are shown; complete translated content is a later phase.
- **Reminder preferences:** optional device-level preferences. Reliable scheduled delivery is not implemented yet.

## Visual direction

- Luxurious, heavenly, God-centered art direction.
- Midnight navy, antique gold, warm ivory, divine-light photography.
- Elegant serif typography, atmospheric visuals, restrained motion.
- Mobile-first layouts. Core content stays visible when animations or external assets fail.

## Privacy and safety

- Reflections and prayer entries require authentication and are stored against the signed-in user.
- The journal page only queries the current user's records.
- Use HTTPS in production and keep the secret key private.
- The app does not replace clergy, medical care, therapy, or financial professionals.
- Notifications, audio, and reminders must remain explicit and user-controlled.
- Scripture translations and media must be properly sourced/licensed before broad public release.

## Technology

- Django 5.2
- SQLite for local development and simple initial hosting; PostgreSQL-compatible configuration is available through the database URL.
- WhiteNoise for static assets.
- PWA manifest and service worker.

## Local development (Windows PowerShell)

Use Python 3.12 and run these commands from the project folder:

    py -3.12 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    Copy-Item .env.example .env

For local HTTP testing, set DEBUG=True in .env so development cookies work over localhost. Keep DEBUG=False in production and replace the development secret with a long random value.

    python manage.py migrate
    python manage.py check
    python manage.py test
    python manage.py runserver

Open http://127.0.0.1:8000/. Create an account through Sign in / Profile to test the private faith journal.

## PythonAnywhere deployment preparation

1. Upload the project folder or the branch ZIP to your PythonAnywhere account.
2. Create a Python 3.12 virtual environment and install requirements.txt.
3. Set production environment variables: DEBUG=False, a unique SECRET_KEY, and the correct ALLOWED_HOSTS / CSRF_TRUSTED_ORIGINS.
4. Run python manage.py migrate and python manage.py collectstatic --noinput.
5. Point the web app's WSGI configuration at config.wsgi:application using the actual project path on your account.
6. Configure static files to serve the collected staticfiles directory, reload the web app, then verify /health/, signup/login, and saving private journal entries.

Keep the database file on persistent project storage and back it up regularly if SQLite is used. Do not upload a real .env, passwords, or private user data into GitHub.

See [deployment/PYTHONANYWHERE.md](deployment/PYTHONANYWHERE.md) for the full hosting checklist and [deployment/pythonanywhere_wsgi.example.py](deployment/pythonanywhere_wsgi.example.py) for the WSGI example.

## CI checks

GitHub Actions runs Django system checks, verifies migrations are up to date, and executes automated tests on the Phase 2 branch and on pull requests targeting main.

## Current stage

Phase 2: account flows and private faith journal are implemented on the phase-2-faith-features development branch. Full translations, scheduled notifications, personalized AI guidance, and final hosting setup remain future tasks.
