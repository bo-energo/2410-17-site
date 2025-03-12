import csv
import json
from pathlib import Path


# Служебный скрипт для получения списка необходимых для диагностики сигналов
folder = "c:\\Users\\Skiff\\Downloads"
file_name = "Сигналы для работы диагностики Затонской ТЭЦ - Лист1.csv"
input_path = f"{folder}\\{file_name}"
output_path = Path.cwd().joinpath("main", "laser", "diag_signals.py")
"laser\\diag_signals.py"
with open(input_path, mode='r', encoding="utf-8") as input_f:
    reader = csv.DictReader(input_f)
    sgns = {
        row.get("code"): row.get("name")
        for row in reader}

    data = json.dumps(sgns, ensure_ascii=False)
    with open(output_path, "w", encoding="utf-8") as output_f:
        output_f.write("sgn_needed_for_diag = ")
        output_f.write(data)
