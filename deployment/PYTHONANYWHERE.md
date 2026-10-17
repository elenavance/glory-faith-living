# PythonAnywhere deployment checklist for GLORY

This guide is for the GLORY project only. Do not point NOOR or Spiritual Wisdom at this project.

## 1. Upload the project

Download the ZIP for the approved GLORY branch from GitHub, upload it through the PythonAnywhere Files tab, and extract it into a dedicated directory such as:

    /home/YOUR_USERNAME/glory-faith-living

Replace YOUR_USERNAME with your actual PythonAnywhere username.

## 2. Create the virtual environment

From a PythonAnywhere Bash console:

    cd /home/YOUR_USERNAME/glory-faith-living
    python3.12 -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    pip install -r requirements.txt

Use the Python version selected for the web app if Python 3.12 is not available in your account.

## 3. Configure private settings

Create a private .env file in the project directory (do not upload it to GitHub). Set:

    DEBUG=False
    SECRET_KEY=PASTE_A_LONG_RANDOM_SECRET_HERE
    ALLOWED_HOSTS=YOUR_USERNAME.pythonanywhere.com
    CSRF_TRUSTED_ORIGINS=https://YOUR_USERNAME.pythonanywhere.com
    TIME_ZONE=Asia/Jakarta

Replace the example hostname with your real PythonAnywhere hostname. Do not use the development secret from settings.py in production.

## 4. Prepare the database and static files

With the virtual environment active:

    python manage.py check
    python manage.py migrate
    python manage.py collectstatic --noinput
    python manage.py test

The default database is SQLite. Keep db.sqlite3 in a persistent project directory, back it up, and do not place it in a temporary directory.

## 5. Configure the web app

- Create a PythonAnywhere web app using the matching Python version.
- Set its virtualenv path to /home/YOUR_USERNAME/glory-faith-living/.venv.
- Open the WSGI configuration file from the Web tab.
- Copy the contents of pythonanywhere_wsgi.example.py into that WSGI file and replace YOUR_USERNAME and project_home.
- Configure the static URL /static/ to point to /home/YOUR_USERNAME/glory-faith-living/staticfiles/.
- Save and reload the web app.

## 6. Verify before sharing

Check these paths in the live site:

- / — homepage loads on desktop and mobile.
- /health/ — returns JSON with status ok.
- /accounts/signup/ — account creation works.
- /accounts/login/ — sign-in works.
- /my-journey/ — private journal requires sign-in.
- Save a reflection and prayer, refresh, and confirm they persist.
- Sign in as another test user and confirm the first user's journal is not visible.
- Test the Ask section and the optional prayer audio preference.

Do not call the app production-ready until these checks pass on the deployed site.
