import csv
import logging

from config_ui.models import PassportCategories, PassportSignals

from main.settings import BASE_DIR


logger = logging.getLogger(__name__)


def load_pasp_config():
    data_dir = BASE_DIR.joinpath("config_ui", "init_data", "pdata")

    categories = {}
    categories_path = data_dir.joinpath("pdata_category.csv")
    with open(categories_path, mode='r', encoding='windows-1251') as file:
        reader = csv.DictReader(file, delimiter=";")

        for row in reader:
            try:
                cat = PassportCategories(
                    code=row.get("code"),
                    name=row.get("name"),
                    order=row.get("sort"))
                cat.save()
            except Exception as ex:
                logger.error(f"Не удалось сохранить категорию паспорта {row}. {ex}")
            else:
                categories[cat.code] = cat

    signals_path = data_dir.joinpath("pdata_sugnals.csv")
    with open(signals_path, mode='r', encoding='windows-1251') as file:
        reader = csv.DictReader(file, delimiter=";")

        for row in reader:
            category = categories.get(row.get("pdata_category"))
            try:
                sgn = PassportSignals(
                    code=row.get("code"),
                    pdata_category=category,
                    order=row.get("sort"))
                sgn.save()
            except Exception as ex:
                logger.error(f"Не удалось сохранить сигнал паспорта {row}. {ex}")


def rollback_pasp_config():
    try:
        PassportSignals.objects.all().delete()
        PassportCategories.objects.all().delete()
    except Exception as ex:
        logger.error(
            f"Не удалось очистить таблицы {PassportSignals.Meta.db_table}, "
            f"{PassportCategories.Meta.db_table}. {ex}")
