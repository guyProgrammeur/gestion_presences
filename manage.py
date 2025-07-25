#!/usr/bin/env python
import os
import sys

# Redirige vers GTK3 embarqué
if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
gtk_path = os.path.join(base_dir, "gtk3", "bin")
os.environ["PATH"] = gtk_path + os.pathsep + os.environ["PATH"]


if sys.platform == "win32":
    os.add_dll_directory(gtk_path)  # Nécessaire pour Python 3.8+

"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_presences.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
