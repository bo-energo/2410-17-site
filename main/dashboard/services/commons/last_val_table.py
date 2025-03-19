class LastValTable:
    """Класс таблицы сигналов на странице последних значений"""
    def __init__(self, code: str, api_label: str, plot_tab_code: str):
        self._code = code
        self._api_label = api_label
        self._name = api_label
        self._plot_tab_code = plot_tab_code


last_val_tables = {
    "gases": LastValTable("gases", "lastValTableGases", "gases"),
    "v_gases": LastValTable("v_gases", "lastValTableVGases", "gases"),
    "power": LastValTable("power", "lastValTablePower", "power"),
    "humidity": LastValTable("humidity", "lastValTableHumidity", "humidity"),
    "temperature": LastValTable("temperature", "lastValTableTemp", "temperature"),
    "bushing": LastValTable("bushing", "lastValTableBushing", "bushing"),
}
