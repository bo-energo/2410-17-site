import csv
import json
from pathlib import Path


# Служебный скрипт для получения списка необходимых для диагностики сигналов
folder = "NoGIT\\Init_data"
file_name = "Сигналы для работы диагностики Затонской ТЭЦ.csv"
input_path = f"{folder}\\{file_name}"
output_path = Path.cwd().joinpath("main", "laser", "diag_signals.py")
"laser\\diag_signals.py"
with open(input_path, mode='r', encoding="cp1251") as input_f:
    reader = csv.DictReader(input_f, delimiter=";")
    sgns = {
        row.get("code"): row.get("name")
        for row in reader}

    data = json.dumps(sgns, ensure_ascii=False)
    with open(output_path, "w", encoding="utf-8") as output_f:
        output_f.write("sgn_needed_for_diag = {\n")
        for key, value in sgns.items():
            if key:
                output_f.write(f'    "{key}": "{value}",\n')
        output_f.write("}")
