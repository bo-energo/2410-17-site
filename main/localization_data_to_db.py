import django
import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'main.settings'
django.setup()

from main.settings import BASE_DIR
from localization.services.importing.use_cases import import_all_data


if __name__ == "__main__":
    import_all_data(BASE_DIR.joinpath("localization", "init_data", "localization_data.xlsx"))
