"""Example PythonAnywhere WSGI configuration for GLORY.

Copy this code into the WSGI configuration file from your PythonAnywhere Web tab.
Replace YOUR_USERNAME and the project path with the actual path shown in your account.
Do not commit private secrets into this file.
"""
import os
import sys

project_home = "/home/YOUR_USERNAME/glory-faith-living"
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Optional: load the project's private .env file if you uploaded one securely.
from dotenv import load_dotenv
load_dotenv(os.path.join(project_home, ".env"))

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
