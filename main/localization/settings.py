import os
from dotenv import load_dotenv


load_dotenv()

# Язык, используемый в панели администратора для названий экземпляров
# сигналов, категорий и единиц измерения.
# Используется при локализации указанных выше сущностей.
ADMIN_VALUE_LANG = os.getenv("ADMIN_VALUE_LANG", "ru")
