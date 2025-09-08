# #!/usr/bin/env python
# """Django's command-line utility for administrative tasks."""
# import os
# import sys
#
#
# def main():
#     """Run administrative tasks."""
#     os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_core.settings')
#     try:
#         from django.core.management import execute_from_command_line
#     except ImportError as exc:
#         raise ImportError(
#             "Couldn't import Django. Are you sure it's installed and "
#             "available on your PYTHONPATH environment variable? Did you "
#             "forget to activate a virtual environment?"
#         ) from exc
#     execute_from_command_line(sys.argv)
#
#
# if __name__ == '__main__':
#     main()


#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    # Read environment variable DJANGO_ENV to decide settings
    env = os.getenv('DJANGO_ENV', 'development').lower()

    if env == 'production':
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_core.settings.production')
    else:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_core.settings.development')

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
