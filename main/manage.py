#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

from check_db_connect import check_db_connect


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    if len(sys.argv) > 1 and sys.argv[1] in ("runserver", "migrate"):
        check_db_connect()
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
