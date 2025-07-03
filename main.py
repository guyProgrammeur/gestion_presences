import os
import sys
from django.conf import settings
from django.core.management import execute_from_command_line

print("Mon application démarre...")

if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_presences.settings")
settings.TEMPLATES[0]['DIRS'] = [os.path.join(BASE_DIR, 'templates')]
settings.STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

if __name__ == "__main__":
    execute_from_command_line([
        'manage.py',
        'runserver',
        '127.0.0.1:8000',
        '--noreload'  # 🛑 important !
    ])
    print("L'application est prête à être exécutée.")
    print("Accédez à 'http://127.0.0.1:8000' pour voir l'application.")
    print("Pour arrêter l'application, utilisez Ctrl+C dans le terminal.")
    print("Merci d'utiliser notre application de gestion des présences !")
# Note: This script is designed to be run in a Django environment.
# Ensure that Django is properly installed and configured before running this script.
